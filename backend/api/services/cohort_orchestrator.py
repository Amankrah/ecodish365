"""Cohort orchestrator — score N recalls across all 6 lenses in parallel.

PLATFORM-CODE-1.b (2026-06-26). Powers the `/api/research/cohort/`
endpoint. Each recall (`{respondent_id, day_id, foods: [...]}`) is
dispatched in parallel via `django.test.Client` to every selected lens
calculator's existing API endpoint — reusing the proven adapter pattern
from [`_smoke_s4_lite_panel.py`](backend/_smoke_s4_lite_panel.py:225) so
no scoring logic is duplicated. The orchestrator collects the headline
score per (recall × lens), aggregates into per-respondent records plus
cohort distribution stats, and returns one structured payload.

Why `django.test.Client` instead of HTTP requests or direct function
calls: (1) it executes the full DRF middleware stack in-process — no
TCP, no auth surprises, no rate-limit headers — so it's both faster and
safer than `requests.post('http://localhost:8000/...')`; (2) it
preserves each calculator's audience-aware response shape verbatim,
which keeps the cohort orchestrator agnostic of every lens's internals.

Parallelism is bounded by `ThreadPoolExecutor(max_workers=...)` —
default 4 — sized for the platform's single-Django-process deployment.
The full default cohort run (200 recalls × 7 lenses = 1,400 jobs) takes
~30-60 s on the reference machine.
"""
from __future__ import annotations

import json
import logging
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from django.test import Client

logger = logging.getLogger(__name__)


# ---------- Public types --------------------------------------------------

LensName = str   # 'hefi' | 'heni' | 'hsr' | 'fcs' | 'env' | 'dietary_pattern' | 'fped'

ALL_LENSES: Tuple[LensName, ...] = (
    'hefi', 'heni', 'hsr', 'fcs', 'env', 'dietary_pattern', 'fped',
)


@dataclass
class Recall:
    """One day of food intake for one respondent."""
    respondent_id: str
    day_id: str
    foods: List[Dict[str, Any]]   # [{food_id, mass_g, occasion?}]

    def key(self) -> str:
        return f'{self.respondent_id}::{self.day_id}'


@dataclass
class RecallScores:
    """Headline scores for one recall across all requested lenses.
    Missing lenses (calculator failure / unknown food) report None."""
    respondent_id:           str
    day_id:                  str
    n_foods:                 int
    total_mass_g:            float
    hefi_total_score:        Optional[float] = None
    heni_minutes:            Optional[float] = None
    hsr_stars:               Optional[float] = None
    fcs_score:               Optional[float] = None
    env_gw_per_100kcal:      Optional[float] = None
    env_sustainability:      Optional[float] = None
    env_monetized_cost:      Optional[float] = None
    pattern_top:             Optional[str] = None
    pattern_confidence:      Optional[str] = None
    fped_unmatched_pct:      Optional[float] = None   # coverage flag from FPED
    errors:                  List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            'respondent_id':       self.respondent_id,
            'day_id':              self.day_id,
            'n_foods':             self.n_foods,
            'total_mass_g':        round(self.total_mass_g, 2),
            'hefi_total_score':    None if self.hefi_total_score is None else round(self.hefi_total_score, 2),
            'heni_minutes':        None if self.heni_minutes is None else round(self.heni_minutes, 2),
            'hsr_stars':           None if self.hsr_stars is None else round(self.hsr_stars, 2),
            'fcs_score':           None if self.fcs_score is None else round(self.fcs_score, 2),
            'env_gw_per_100kcal':  None if self.env_gw_per_100kcal is None else round(self.env_gw_per_100kcal, 4),
            'env_sustainability':  None if self.env_sustainability is None else round(self.env_sustainability, 2),
            'env_monetized_cost':  None if self.env_monetized_cost is None else round(self.env_monetized_cost, 4),
            'pattern_top':         self.pattern_top,
            'pattern_confidence':  self.pattern_confidence,
            'fped_unmatched_pct':  None if self.fped_unmatched_pct is None else round(self.fped_unmatched_pct, 1),
        }
        if self.errors:
            d['errors'] = self.errors
        return d


@dataclass
class LensDistribution:
    """Distribution stats for one numeric lens across the cohort."""
    lens:           str
    metric:         str
    unit:           str
    n:              int
    n_missing:      int
    median:         Optional[float] = None
    q1:             Optional[float] = None
    q3:             Optional[float] = None
    mean:           Optional[float] = None
    sd:             Optional[float] = None
    min_:           Optional[float] = None
    max_:           Optional[float] = None
    histogram:      List[Dict[str, Any]] = field(default_factory=list)
    pct_meets_target: Optional[float] = None   # populated when a published cap/floor exists

    def to_dict(self) -> Dict[str, Any]:
        def r(v: Optional[float], nd: int = 4) -> Optional[float]:
            return None if v is None else round(float(v), nd)
        return {
            'lens':               self.lens,
            'metric':             self.metric,
            'unit':               self.unit,
            'n':                  self.n,
            'n_missing':          self.n_missing,
            'median':             r(self.median),
            'q1':                 r(self.q1),
            'q3':                 r(self.q3),
            'mean':               r(self.mean),
            'sd':                 r(self.sd),
            'min':                r(self.min_),
            'max':                r(self.max_),
            'pct_meets_target':   r(self.pct_meets_target, 1),
            'histogram':          self.histogram,
        }


# ---------- Per-lens adapters --------------------------------------------
# Adapted from _smoke_s4_lite_panel.py:225-320. The body shapes match each
# calculator's existing API view — no scoring logic is reimplemented here.

def _call_hefi(c: Client, foods: List[Dict[str, Any]]) -> Optional[float]:
    body = {'foods': [{'food_id': f['food_id'], 'amount_g': f['mass_g']} for f in foods]}
    r = c.post('/api/hefi/calculate/', data=json.dumps(body), content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['total_score'])
    except Exception:  # noqa: BLE001
        return None


def _call_heni(c: Client, foods: List[Dict[str, Any]]) -> Optional[float]:
    body = {'meal': [{'food_id': f['food_id'], 'amount': f['mass_g'], 'unit': 'g'} for f in foods]}
    r = c.post('/api/heni/calculate/', data=json.dumps(body), content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['data']['health_impact']['health_impact_minutes'])
    except Exception:  # noqa: BLE001
        return None


def _call_hsr(c: Client, foods: List[Dict[str, Any]]) -> Optional[float]:
    multi = len(foods) > 1
    body = {
        'food_ids':       [f['food_id'] for f in foods],
        'serving_sizes':  [f['mass_g']  for f in foods],
        'from_recall24h': multi,
        'analysis_level': 'detailed',
    }
    r = c.post('/api/hsr/calculate/', data=json.dumps(body), content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        payload = r.json()
        if multi:
            summary = payload.get('per_food_summary') or {}
            if summary.get('available'):
                return float(summary['energy_weighted_avg'])
        return float(payload['hsr_result']['rating']['star_rating'])
    except Exception:  # noqa: BLE001
        return None


def _call_fcs(c: Client, foods: List[Dict[str, Any]]) -> Optional[float]:
    body = {
        'food_ids':      [f['food_id'] for f in foods],
        'serving_sizes': [f['mass_g']  for f in foods],
    }
    r = c.post('/api/fcs/calculate/', data=json.dumps(body), content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['data']['fcs'])
    except Exception:  # noqa: BLE001
        return None


def _call_env(c: Client, foods: List[Dict[str, Any]]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    body = {
        'foods':              [{'food_id': f['food_id'], 'quantity': f['mass_g']} for f in foods],
        'enable_lca_matcher': False,
        'user_type':          'researcher',
    }
    r = c.post('/api/environmental-impact/', data=json.dumps(body), content_type='application/json', secure=True)
    if r.status_code != 200:
        return None, None, None
    try:
        block = r.json()['data']['data']
        gw   = float(block['environmental_impacts']['all_impacts']['Global warming'])
        sust = float(block['sustainability']['overall_sustainability_score'])
        cost = float(block['monetization']['results']['total_environmental_cost']['value'])
        return gw, sust, cost
    except Exception:  # noqa: BLE001
        return None, None, None


def _call_pattern(c: Client, foods: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    body = {
        'foods':     [{'food_id': f['food_id'], 'mass_g': f['mass_g']} for f in foods],
        'user_type': 'researcher',
    }
    r = c.post('/api/dietary-pattern/classify/', data=json.dumps(body), content_type='application/json', secure=True)
    if r.status_code != 200:
        return None, None
    try:
        result = r.json()['result']
        return str(result.get('top_pattern')), str(result.get('top_pattern_confidence'))
    except Exception:  # noqa: BLE001
        return None, None


def _call_fped_coverage(c: Client, foods: List[Dict[str, Any]]) -> Optional[float]:
    """Single-recall FPED coverage flag — % of meal mass with NO bridged
    FPED profile. Surfaces the per-recall data-quality signal in the cohort
    distribution panel."""
    body = {'recalls': [[{'food_id': f['food_id'], 'mass_g': f['mass_g']} for f in foods]]}
    r = c.post('/api/fped/cohort/', data=json.dumps(body), content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        cov = r.json()['result']['coverage']
        # mean_coverage_pct_by_mass is 0-100 where 100 = fully bridged.
        mean_cov = float(cov.get('mean_coverage_pct_by_mass', 0.0))
        return round(100.0 - mean_cov, 2)
    except Exception:  # noqa: BLE001
        return None


# ---------- Per-recall fan-out --------------------------------------------

def _score_one_recall(client: Client, recall: Recall, lenses: List[LensName]) -> RecallScores:
    """Score one recall across all requested lenses. Errors per-lens are
    collected so a partial run still yields useful data."""
    scores = RecallScores(
        respondent_id=recall.respondent_id,
        day_id=recall.day_id,
        n_foods=len(recall.foods),
        total_mass_g=sum(float(f.get('mass_g', 0.0)) for f in recall.foods),
    )
    if 'hefi' in lenses:
        try:
            scores.hefi_total_score = _call_hefi(client, recall.foods)
        except Exception as exc:  # noqa: BLE001
            scores.errors.append(f'hefi: {exc}')
    if 'heni' in lenses:
        try:
            scores.heni_minutes = _call_heni(client, recall.foods)
        except Exception as exc:  # noqa: BLE001
            scores.errors.append(f'heni: {exc}')
    if 'hsr' in lenses:
        try:
            scores.hsr_stars = _call_hsr(client, recall.foods)
        except Exception as exc:  # noqa: BLE001
            scores.errors.append(f'hsr: {exc}')
    if 'fcs' in lenses:
        try:
            scores.fcs_score = _call_fcs(client, recall.foods)
        except Exception as exc:  # noqa: BLE001
            scores.errors.append(f'fcs: {exc}')
    if 'env' in lenses:
        try:
            gw, sust, cost = _call_env(client, recall.foods)
            scores.env_gw_per_100kcal = gw
            scores.env_sustainability = sust
            scores.env_monetized_cost = cost
        except Exception as exc:  # noqa: BLE001
            scores.errors.append(f'env: {exc}')
    if 'dietary_pattern' in lenses:
        try:
            top, conf = _call_pattern(client, recall.foods)
            scores.pattern_top = top
            scores.pattern_confidence = conf
        except Exception as exc:  # noqa: BLE001
            scores.errors.append(f'dietary_pattern: {exc}')
    if 'fped' in lenses:
        try:
            scores.fped_unmatched_pct = _call_fped_coverage(client, recall.foods)
        except Exception as exc:  # noqa: BLE001
            scores.errors.append(f'fped: {exc}')
    return scores


# ---------- Distribution stats -------------------------------------------

def _histogram(values: List[float], n_bins: int = 10) -> List[Dict[str, Any]]:
    """Equal-width histogram for a list of numeric values. Returns a list of
    `{bin_min, bin_max, count}` rows. Empty list if values is empty or
    constant (range == 0). Histograms are intended for the UI; the
    `n_bins` default keeps the payload small."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    if lo == hi:
        return [{'bin_min': lo, 'bin_max': hi, 'count': len(values)}]
    width = (hi - lo) / n_bins
    bins: List[Dict[str, Any]] = []
    for i in range(n_bins):
        b_lo = lo + i * width
        b_hi = lo + (i + 1) * width
        count = sum(1 for v in values if (b_lo <= v < b_hi)) if i < n_bins - 1 else sum(1 for v in values if b_lo <= v <= b_hi)
        bins.append({'bin_min': round(b_lo, 4), 'bin_max': round(b_hi, 4), 'count': count})
    return bins


def _percentile(sorted_vals: List[float], p: float) -> float:
    """Linear-interpolation percentile. `p` in [0, 100]."""
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_vals) - 1)
    if f == c:
        return sorted_vals[f]
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def _distribution_from_values(
    lens: str, metric: str, unit: str, values: List[Optional[float]],
    pct_meets_target_fn: Optional[Callable[[float], bool]] = None,
    n_bins: int = 10,
) -> LensDistribution:
    finite = [float(v) for v in values if v is not None]
    n_missing = len(values) - len(finite)
    if not finite:
        return LensDistribution(lens=lens, metric=metric, unit=unit, n=0, n_missing=n_missing)
    sorted_v = sorted(finite)
    pct_meets = None
    if pct_meets_target_fn is not None:
        pct_meets = 100.0 * sum(1 for v in finite if pct_meets_target_fn(v)) / len(finite)
    return LensDistribution(
        lens=lens, metric=metric, unit=unit, n=len(finite), n_missing=n_missing,
        median=_percentile(sorted_v, 50),
        q1=_percentile(sorted_v, 25),
        q3=_percentile(sorted_v, 75),
        mean=statistics.fmean(finite),
        sd=(statistics.stdev(finite) if len(finite) >= 2 else 0.0),
        min_=sorted_v[0],
        max_=sorted_v[-1],
        histogram=_histogram(finite, n_bins=n_bins),
        pct_meets_target=pct_meets,
    )


# ---------- Public entry point -------------------------------------------

def score_cohort(
    recalls: List[Recall],
    lenses: Optional[List[LensName]] = None,
    parallelism: int = 4,
) -> Dict[str, Any]:
    """Score every recall across every requested lens. Returns a structured
    payload mirroring the meta + per_respondent + distribution_by_lens +
    coverage + provenance contract documented in the plan."""
    if not recalls:
        return {
            'meta': {'n_recalls': 0, 'n_respondents': 0, 'lenses_run': list(lenses or ALL_LENSES), 'runtime_s': 0.0},
            'per_respondent': [],
            'distribution_by_lens': {},
            'coverage': {'n_recalls_with_errors': 0},
            'provenance': _provenance_block(),
        }
    lenses_run = list(lenses) if lenses else list(ALL_LENSES)
    invalid = [l for l in lenses_run if l not in ALL_LENSES]
    if invalid:
        raise ValueError(f'Unknown lenses requested: {invalid!r}')

    t0 = time.perf_counter()
    client = Client()   # django.test.Client is reusable across threads at this scope
    per_respondent: List[RecallScores] = [None] * len(recalls)   # type: ignore[list-item]

    with ThreadPoolExecutor(max_workers=parallelism) as pool:
        futures = {
            pool.submit(_score_one_recall, client, r, lenses_run): i
            for i, r in enumerate(recalls)
        }
        for fut in as_completed(futures):
            idx = futures[fut]
            try:
                per_respondent[idx] = fut.result()
            except Exception as exc:  # noqa: BLE001
                logger.exception('Cohort recall scoring failed at idx=%s', idx)
                per_respondent[idx] = RecallScores(
                    respondent_id=recalls[idx].respondent_id,
                    day_id=recalls[idx].day_id,
                    n_foods=len(recalls[idx].foods),
                    total_mass_g=sum(float(f.get('mass_g', 0.0)) for f in recalls[idx].foods),
                    errors=[f'fatal: {exc}'],
                )

    runtime_s = time.perf_counter() - t0

    # ---- Distribution stats per lens ----
    distribution_by_lens: Dict[str, Any] = {}
    if 'hefi' in lenses_run:
        distribution_by_lens['hefi'] = _distribution_from_values(
            'hefi', 'total_score', '0-80',
            [s.hefi_total_score for s in per_respondent],
            pct_meets_target_fn=lambda v: v >= 60,  # Brassard 2022 "good" threshold
        ).to_dict()
    if 'heni' in lenses_run:
        distribution_by_lens['heni'] = _distribution_from_values(
            'heni', 'minutes_healthy_life', 'min',
            [s.heni_minutes for s in per_respondent],
            pct_meets_target_fn=lambda v: v >= 0,   # net positive
        ).to_dict()
    if 'hsr' in lenses_run:
        distribution_by_lens['hsr'] = _distribution_from_values(
            'hsr', 'stars', '0.5-5.0',
            [s.hsr_stars for s in per_respondent],
            pct_meets_target_fn=lambda v: v >= 3.5,  # HSRAC "above average"
        ).to_dict()
    if 'fcs' in lenses_run:
        distribution_by_lens['fcs'] = _distribution_from_values(
            'fcs', 'food_compass_score', '1-100',
            [s.fcs_score for s in per_respondent],
            pct_meets_target_fn=lambda v: v >= 70,   # Mozaffarian 2021 "encourage"
        ).to_dict()
    if 'env' in lenses_run:
        distribution_by_lens['env_gw'] = _distribution_from_values(
            'env', 'global_warming_per_100kcal', 'kg CO2e / 100 kcal',
            [s.env_gw_per_100kcal for s in per_respondent],
            pct_meets_target_fn=lambda v: v <= 0.3,  # informal "low" threshold
        ).to_dict()
        distribution_by_lens['env_sustainability'] = _distribution_from_values(
            'env', 'sustainability', '0-100',
            [s.env_sustainability for s in per_respondent],
        ).to_dict()
        distribution_by_lens['env_cost'] = _distribution_from_values(
            'env', 'monetized_cost', 'USD / 100 kcal',
            [s.env_monetized_cost for s in per_respondent],
        ).to_dict()
    if 'fped' in lenses_run:
        distribution_by_lens['fped_coverage'] = _distribution_from_values(
            'fped', 'unmatched_pct_by_mass', '%',
            [s.fped_unmatched_pct for s in per_respondent],
            pct_meets_target_fn=lambda v: v <= 10.0,  # < 10 % unmatched = good
        ).to_dict()
    if 'dietary_pattern' in lenses_run:
        pattern_counts: Dict[str, int] = {}
        for s in per_respondent:
            key = s.pattern_top or 'unknown'
            pattern_counts[key] = pattern_counts.get(key, 0) + 1
        n_with = sum(1 for s in per_respondent if s.pattern_top)
        distribution_by_lens['dietary_pattern'] = {
            'lens':         'dietary_pattern',
            'metric':       'top_pattern_distribution',
            'unit':         'count by pattern',
            'n':            n_with,
            'n_missing':    len(per_respondent) - n_with,
            'pattern_counts': pattern_counts,
        }

    n_errors = sum(1 for s in per_respondent if s and s.errors)
    distinct_respondents = len({s.respondent_id for s in per_respondent if s})
    coverage = {
        'n_recalls_total':       len(per_respondent),
        'n_recalls_with_errors': n_errors,
        'n_distinct_respondents': distinct_respondents,
    }

    return {
        'meta': {
            'n_recalls':     len(per_respondent),
            'n_respondents': distinct_respondents,
            'lenses_run':    lenses_run,
            'parallelism':   parallelism,
            'runtime_s':     round(runtime_s, 2),
        },
        'per_respondent':        [s.to_dict() for s in per_respondent if s],
        'distribution_by_lens':  distribution_by_lens,
        'coverage':              coverage,
        'provenance':            _provenance_block(),
    }


def _provenance_block() -> Dict[str, Any]:
    return {
        'cohort_endpoint_version': '1.0',
        'lens_versions': {
            'hefi':            'Brassard 2022 / HEFI-2019 (APNM)',
            'heni':            'Stylianou 2021 (Nature Food) + Stylianou SI Table 1 DRFs',
            'hsr':             'HSRAC v9 (2023 Implementation Guide)',
            'fcs':             'Mozaffarian 2021 (Nature Food) Food Compass',
            'env':             'ReCiPe 2016 H + P&N 2018 + M&H 2011/2012 (3-category v1 trim)',
            'dietary_pattern': 'Trichopoulou 2003 / Sacks 2001 / Orlich 2013 / Willett 2019',
            'fped':            'FPED 1718 (USDA Food Patterns Equivalents Database)',
        },
        'platform_substrate': 'CNF + WAFCT + FDC + CIQUAL (24,125 foods)',
    }
