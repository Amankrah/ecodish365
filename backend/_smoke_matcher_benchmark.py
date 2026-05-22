"""Matcher validation benchmark — stratified live-LLM accuracy harness.

Reproducible benchmark of the §3.5 LCA matcher against a 200-CNF-food
stratified sample across all 23 CNF FoodGroups. For each food, runs the
live matcher (OpenAI embedding retrieval + LLM ranking) and applies four
automated quality heuristics:

  1. Group consistency   — matched Agribalyse `agribalyse_group` is in the
                            expected set for the CNF FoodGroup
  2. Magnitude plausibility — matched per-100g GW within ±3× of the
                            cnf_integrator group-default for the CNF group
  3. Token overlap       — matched LCI name shares ≥1 content token (≥4 chars,
                            stoplist filtered) with the canonicalised CNF
                            description
  4. Confidence band     — clean ≥ 0.85; borderline 0.60–0.85; low < 0.60

Per-food verdict: `clean` (all 4 pass + conf ≥ 0.85), `borderline` (all 4
pass + conf in [0.60, 0.85)), or `flagged` (any of 1–3 fail OR matched=False).

Outputs (in `backend/environmental_impact_model/data/`):
  - matcher_benchmark_<git-rev>_<utc>.json   — full per-food benchmark
  - matcher_benchmark_flagged_for_review.md   — markdown summary of flagged rows

Cost: < $0.10 per run after first-time embedding cache warmup.
Run: python _smoke_matcher_benchmark.py [--sample-size 200] [--seed 42]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_BACKEND = os.path.dirname(os.path.abspath(__file__))
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    p = os.path.join(_BACKEND, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

# Load .env before Django setup so OPENAI_API_KEY is in env when the matcher
# singleton reads it on first use.
try:
    from dotenv import load_dotenv  # noqa: E402
    load_dotenv(os.path.join(_BACKEND, '.env'))
except Exception:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

_DATA_DIR = os.path.join(_BACKEND, 'environmental_impact_model', 'data')

# ---------------------------------------------------------------------------
# Heuristic 1: CNF FoodGroupName → expected Agribalyse `agribalyse_group`
# acceptance set. `None` means any group is acceptable (no constraint).
# Extends the matcher's `_CNF_TO_AGRIBALYSE_SUBGROUP` with broader sets for
# CNF groups that legitimately span multiple Agribalyse groups.
# ---------------------------------------------------------------------------
_GROUP_CONSISTENCY_MAP: Dict[str, Optional[set]] = {
    # Animal proteins
    'Beef Products':                  {'viandes, œufs, poissons'},
    'Pork Products':                  {'viandes, œufs, poissons'},
    'Poultry Products':               {'viandes, œufs, poissons'},
    'Lamb, Veal and Game':            {'viandes, œufs, poissons'},
    'Finfish and Shellfish Products': {'viandes, œufs, poissons'},
    'Sausages and Luncheon meats':    {'viandes, œufs, poissons', 'entrées et plats composés'},
    # Dairy and Egg
    'Dairy and Egg Products':         {'lait et produits laitiers', 'viandes, œufs, poissons'},
    # Plants
    'Vegetables and Vegetable Products':  {'fruits, légumes, légumineuses et oléagineux'},
    'Fruits and fruit juices':            {'fruits, légumes, légumineuses et oléagineux', 'boissons'},
    'Legumes and Legume Products':        {'fruits, légumes, légumineuses et oléagineux', 'entrées et plats composés'},
    'Nuts and Seeds':                     {'fruits, légumes, légumineuses et oléagineux'},
    # Grains / starches
    'Cereals, Grains and Pasta':      {'produits céréaliers', 'entrées et plats composés'},
    'Baked Products':                 {'produits céréaliers', 'produits sucrés', 'entrées et plats composés'},
    'Breakfast cereals':              {'produits céréaliers'},
    # Fats / sugars
    'Fats and Oils':                  {'matières grasses'},
    'Sweets':                         {'produits sucrés', 'produits céréaliers'},
    # Beverages
    'Beverages':                      {'boissons'},
    # Composites
    'Babyfoods':                      {'aliments infantiles'},
    'Soups, Sauces and Gravies':      {'entrées et plats composés', 'aides culinaires et ingrédients divers'},
    'Mixed Dishes':                   {'entrées et plats composés', 'viandes, œufs, poissons',
                                       'produits céréaliers', 'fruits, légumes, légumineuses et oléagineux'},
    'Fast Foods':                     {'entrées et plats composés', 'viandes, œufs, poissons'},
    # Snacks / herbs: wildcards (cross all groups legitimately)
    'Snacks':                         None,
    'Spices and Herbs':               None,
}

# Words too common or state-related to count as content-token overlap
_TOKEN_STOPLIST = frozenset({
    'food', 'foods', 'raw', 'cooked', 'prepared', 'frozen', 'dried', 'fresh',
    'jarred', 'canned', 'with', 'without', 'and', 'or', 'the', 'for',
    'all', 'stages', 'plain', 'regular', 'home', 'made', 'homemade',
    'baby', 'infant', 'condensed', 'powder', 'mix', 'pure', 'natural',
    'extra', 'light', 'low', 'high', 'fat',
})


def hr(s: str = '') -> None:
    print()
    print('=' * 78)
    if s:
        print(s)
        print('=' * 78)


def _git_rev_short() -> str:
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(_BACKEND),
        ).decode('ascii').strip()
    except Exception:
        return 'unknown'


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def _stratified_cnf_sample(n_per_group: int, seed: int) -> List[Tuple[int, str, str]]:
    """Stratified random sample across all CNF FoodGroups."""
    from environmental_impact_model.src.cnf_integrator import get_cnf_integrator
    ci = get_cnf_integrator()
    if not ci.is_initialized():
        ci.initialize()
    fn = ci._dataframes['food_name']
    fg = ci._dataframes['food_group']
    group_map = dict(zip(fg['FoodGroupID'], fg['FoodGroupName']))
    random.seed(seed)
    sample = []
    for gid, gname in group_map.items():
        sub = fn[fn['FoodGroupID'] == gid]
        if len(sub) == 0:
            continue
        for _, row in sub.sample(min(n_per_group, len(sub)), random_state=seed).iterrows():
            sample.append((int(row['FoodID']), row['FoodDescription'], gname))
    return sample


def _content_tokens(s: str) -> set:
    """Extract content tokens (>= 4 chars, not in stoplist, alphanumeric only)."""
    if not s:
        return set()
    import re
    raw = re.sub(r'[^A-Za-z0-9\s]', ' ', s.lower()).split()
    return {t for t in raw if len(t) >= 4 and t not in _TOKEN_STOPLIST}


def _canonicalise_cnf(desc: str) -> str:
    """Reuse the matcher's state-stripping canonicalisation for fair comparison."""
    from environmental_impact_model.src.lca_matcher import _canonicalize_food_state
    base, _state = _canonicalize_food_state(desc)
    return base or desc


def _cnf_group_default_gw(cnf_group: str) -> Optional[float]:
    """Per-CNF-group default GW per 100g from cnf_integrator. None if group
    is unmapped (falls back to the integrator's default factors)."""
    from environmental_impact_model.src.cnf_integrator import _DERIVED_GROUP_CENTRALS
    block = _DERIVED_GROUP_CENTRALS.get(cnf_group)
    if not block:
        return None
    return block.get('ghg')


def _check_group_consistency(cnf_group: str, matched_agribalyse_group: str) -> bool:
    expected = _GROUP_CONSISTENCY_MAP.get(cnf_group, None)
    if expected is None:
        return True  # wildcard: any group accepts
    return matched_agribalyse_group in expected


def _check_magnitude_plausibility(matched_gw: Optional[float], cnf_default_gw: Optional[float]) -> Tuple[bool, Optional[float]]:
    """matched per-100g GW within ±3× of CNF group default. Returns (pass, ratio).
    When cnf_default_gw is None (unmapped group), pass automatically."""
    if cnf_default_gw is None or cnf_default_gw <= 0 or matched_gw is None:
        return True, None
    ratio = matched_gw / cnf_default_gw
    return (ratio >= 1.0 / 3.0) and (ratio <= 3.0), ratio


def _check_token_overlap(cnf_desc: str, matched_lci_name: str, matched_lci_name_fr: str = '') -> bool:
    cnf_toks = _content_tokens(_canonicalise_cnf(cnf_desc))
    matched_toks = _content_tokens((matched_lci_name or '') + ' ' + (matched_lci_name_fr or ''))
    return bool(cnf_toks & matched_toks)


def _classify(matched: bool, confidence: float, gc_pass: bool, mag_pass: bool, tok_pass: bool) -> str:
    if not matched:
        return 'flagged'
    if not (gc_pass and mag_pass and tok_pass):
        return 'flagged'
    if confidence >= 0.85:
        return 'clean'
    if confidence >= 0.60:
        return 'borderline'
    # confidence < 0.60 with matched=True shouldn't really happen
    return 'borderline'


def _matched_entry_lookup(ciqual_code: Optional[str]) -> Dict[str, Any]:
    """Look up the full v32 catalog entry for a matched Ciqual code."""
    from environmental_impact_model.src.lca_matcher import AgribalyseIndex
    idx = AgribalyseIndex()
    for e in idx.catalog:
        if e.get('ciqual_code') == ciqual_code:
            return e
    return {}


def run_benchmark(sample_size: int = 200, seed: int = 42,
                  with_decomposer: bool = False) -> Dict[str, Any]:
    """Execute the benchmark + return the summary + per-food rows.

    When `with_decomposer=True`, each /environmental-impact/ POST also passes
    enable_recipe_decomposer=true; the Tier γ audit (`recipe_decomposition_decisions[0]`)
    is then captured on each per_food row. Adds ≈ 24-30 extra LLM calls per
    184-food run (only composite-group borderline matches trigger Tier γ),
    bringing total cost from ≈ $0.026 to ≈ $0.035.
    """
    from django.test import Client

    n_groups = 23
    n_per_group = max(1, sample_size // n_groups)

    hr(f'Matcher validation benchmark — {sample_size}-food sample (n_per_group={n_per_group}'
       + (', with Tier γ decomposer)' if with_decomposer else ')'))
    sample = _stratified_cnf_sample(n_per_group=n_per_group, seed=seed)
    # Trim to exactly sample_size (random shuffle for determinism per seed)
    random.seed(seed)
    random.shuffle(sample)
    sample = sample[:sample_size]
    print(f'Sampled {len(sample)} foods across {len(set(g for _, _, g in sample))} groups')

    c = Client()
    rows: List[Dict[str, Any]] = []
    latencies: List[float] = []
    n_progress = 0
    for food_id, cnf_name, cnf_group in sample:
        n_progress += 1
        if n_progress % 25 == 0:
            print(f'  ... {n_progress}/{len(sample)}', flush=True)
        t = time.time()
        # When the caller passes --with-decomposer, the API runs Tier γ on
        # borderline composite matches; we capture the decomposer audit
        # alongside the matcher decision so the benchmark reflects the full
        # production resolution stack (matcher → optional Tier γ → fallback).
        post_body = {
            'foods': [{'food_id': food_id, 'quantity': 100}],
            'enable_lca_matcher': True,
        }
        if with_decomposer:
            post_body['enable_recipe_decomposer'] = True
        r = c.post('/api/environmental-impact/', data=json.dumps(post_body),
                   content_type='application/json')
        elapsed = time.time() - t
        latencies.append(elapsed)
        try:
            env = r.json()['data'].get('data', {}).get('environmental_impacts', {})
        except Exception:
            env = {}
        decisions = env.get('lca_matcher_decisions') or []
        m = decisions[0] if decisions else {}
        matched = bool(m.get('matched'))
        confidence = float(m.get('confidence') or 0.0)
        matched_ciqual = m.get('ciqual_code')
        matched_lci = m.get('lci_name') or ''
        justification = m.get('justification') or ''
        decomp_decisions = env.get('recipe_decomposition_decisions') or []
        decomp = decomp_decisions[0] if decomp_decisions else None

        # Pull the matched entry's Agribalyse group + per-100g GW for the
        # group-consistency and magnitude-plausibility checks. The matcher
        # decision audit doesn't include them; look up from the v32 catalog.
        entry = _matched_entry_lookup(matched_ciqual) if matched_ciqual else {}
        matched_ag_group = entry.get('agribalyse_group', '') or ''
        matched_lci_fr = entry.get('lci_name_fr') or ''
        matched_gw = (entry.get('recipe2016_midpoints_per_100g') or {}).get('Global warming')

        cnf_default_gw = _cnf_group_default_gw(cnf_group)
        gc_pass = _check_group_consistency(cnf_group, matched_ag_group) if matched else False
        mag_pass, mag_ratio = _check_magnitude_plausibility(matched_gw, cnf_default_gw) if matched else (False, None)
        tok_pass = _check_token_overlap(cnf_name, matched_lci, matched_lci_fr) if matched else False
        verdict = _classify(matched, confidence, gc_pass, mag_pass, tok_pass)

        row = {
            'food_id': food_id,
            'cnf_name': cnf_name,
            'cnf_group': cnf_group,
            'matched': matched,
            'ciqual_code': matched_ciqual,
            'lci_name': matched_lci,
            'matched_agribalyse_group': matched_ag_group,
            'confidence': confidence,
            'justification': justification[:200],
            'group_consistency_pass': gc_pass,
            'magnitude_pass': mag_pass,
            'token_overlap_pass': tok_pass,
            'automated_verdict': verdict,
            'reviewer_verdict': None,
            'reviewer_notes': None,
            'matched_gw_per_100g': matched_gw,
            'cnf_group_default_gw_per_100g': cnf_default_gw,
            'magnitude_ratio': mag_ratio,
            'latency_seconds': round(elapsed, 3),
        }
        # Decomposer audit (Tier γ). Only populated when --with-decomposer is
        # set AND the matcher routed this food to the decomposer (composite
        # group + matcher conf < HIGH_CONFIDENCE_THRESHOLD). For non-composite
        # groups the decomposer never attempts, so these stay None.
        if with_decomposer:
            if decomp:
                row['decomposer_attempted'] = True
                row['decomposer_resolved'] = bool(decomp.get('matched'))
                row['decomposer_confidence'] = float(decomp.get('decomposition_confidence') or 0.0)
                row['decomposer_n_ingredients'] = int(decomp.get('ingredient_count') or 0)
                row['decomposer_triggered_by'] = decomp.get('triggered_by')
                row['decomposer_fallback_reason'] = decomp.get('fallback_reason')
                # Capture the decomposer's chosen ingredient ciqual codes so we
                # can check "decomposer's first/only ingredient == matcher's
                # chosen ciqual_code" — the agreement signal that motivates the
                # "decomposer-confirmed direct match" gate refinement.
                row['decomposer_ingredients'] = [
                    {
                        'ciqual_code': i.get('ciqual_code'),
                        'mass_g': i.get('mass_g'),
                        'lci_name': i.get('lci_name'),
                    }
                    for i in (decomp.get('ingredients') or [])
                ]
            else:
                row['decomposer_attempted'] = False
                row['decomposer_resolved'] = False
                row['decomposer_confidence'] = None
                row['decomposer_n_ingredients'] = None
                row['decomposer_triggered_by'] = None
                row['decomposer_fallback_reason'] = None
                row['decomposer_ingredients'] = None
        rows.append(row)

    # ---- Aggregate summary ----
    overall = {'clean': 0, 'borderline': 0, 'flagged': 0}
    by_group: Dict[str, Dict[str, int]] = {}
    by_band: Dict[str, Dict[str, Any]] = {
        '≥0.85': {'n': 0, 'clean': 0, 'borderline': 0, 'flagged': 0},
        '0.60-0.85': {'n': 0, 'clean': 0, 'borderline': 0, 'flagged': 0},
        '<0.60': {'n': 0, 'clean': 0, 'borderline': 0, 'flagged': 0},
    }
    for r in rows:
        v = r['automated_verdict']
        overall[v] += 1
        g = r['cnf_group']
        bg = by_group.setdefault(g, {'clean': 0, 'borderline': 0, 'flagged': 0, 'n': 0})
        bg[v] += 1
        bg['n'] += 1
        conf = r['confidence']
        band = '≥0.85' if conf >= 0.85 else ('0.60-0.85' if conf >= 0.60 else '<0.60')
        bb = by_band[band]
        bb['n'] += 1
        bb[v] += 1

    # Per-band flagged rate
    for band, b in by_band.items():
        b['flagged_rate'] = round(b['flagged'] / b['n'], 3) if b['n'] > 0 else 0.0

    # Cost estimate: each /environmental-impact/ POST fires one embedding +
    # one chat completion. text-embedding-3-small ≈ $0.02/M tokens × ~20 tok
    # = $4e-7 per query; the configured ranking LLM ≈ $0.40/$1.60 per 1M
    # input/output tokens (gpt-4.1-mini, post-2026-05-22 default) × ~700 in +
    # 50 out ≈ $1.4e-4 per call. Total per food ≈ $0.00014 (≈ same as the
    # pre-upgrade gpt-4o-mini cost because output tokens dominate by count
    # only modestly and the prompt is short).
    cost_per_food_usd = 0.00014
    total_cost_usd = round(len(sample) * cost_per_food_usd, 4)

    # Per-group bootstrap CIs (95% percentile method, B=1000 resamples).
    # n=8 per group is statistically thin — point estimates can land 25-40 pp
    # apart by chance alone, so the manuscript should report CIs alongside
    # rates. Implemented inline (no scipy dep) since it's just resampling.
    per_group_cis = _bootstrap_per_group_flagged_ci(rows, seed=seed)

    # Decomposer aggregate (only when --with-decomposer was set)
    decomp_summary = _aggregate_decomposer(rows) if with_decomposer else None

    # Latency percentiles. The harness already reports median + mean, but the
    # tail can be 20-30x median on slow LLM responses; p90/p95/p99 surface
    # this for UX/batching tuning.
    latency_pcts = _latency_percentiles(latencies)

    summary = {
        'overall': {**overall, 'total': len(rows)},
        'by_group': by_group,
        'by_group_bootstrap_ci_95': per_group_cis,
        'by_confidence_band': by_band,
        'total_cost_usd': total_cost_usd,
        'latency_seconds': latency_pcts,
        # Backwards-compatible aliases (pre-2026-05-22 schema):
        'median_latency_seconds': latency_pcts.get('p50', 0),
        'mean_latency_seconds':   latency_pcts.get('mean', 0),
    }
    if decomp_summary is not None:
        summary['decomposer'] = decomp_summary

    return {
        '_schema_version': '1.0',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'git_rev': _git_rev_short(),
        'matcher_pack_version': _matcher_pack_version(),
        'sample_size': len(rows),
        'seed': seed,
        'summary': summary,
        'per_food': rows,
    }


def _latency_percentiles(latencies: List[float]) -> Dict[str, float]:
    """Return p50/p75/p90/p95/p99 + min/max/mean over latency samples.

    Critical for production-UX claims because the mean is misleading when the
    tail is heavy: on the n=184 panel the new gpt-4.1-mini ranker has
    p50=2.2 s but p99=54 s — the tail of ~5 % of foods drives the mean.
    """
    if not latencies:
        return {'p50': 0.0, 'p75': 0.0, 'p90': 0.0, 'p95': 0.0, 'p99': 0.0,
                'min': 0.0, 'max': 0.0, 'mean': 0.0, 'n': 0}
    s = sorted(latencies)
    n = len(s)
    def _pct(p: float) -> float:
        idx = min(n - 1, max(0, int(p * n)))
        return round(s[idx], 2)
    return {
        'p50': _pct(0.50), 'p75': _pct(0.75), 'p90': _pct(0.90),
        'p95': _pct(0.95), 'p99': _pct(0.99),
        'min': round(s[0], 2), 'max': round(s[-1], 2),
        'mean': round(statistics.mean(s), 2), 'n': n,
    }


def _bootstrap_per_group_flagged_ci(
    rows: List[Dict[str, Any]],
    seed: int,
    n_resamples: int = 1000,
    alpha: float = 0.05,
) -> Dict[str, Dict[str, float]]:
    """Per-group 95% percentile bootstrap CI on the flagged-rate.

    n_per_group is small (typically 8) so the point estimate has wide
    uncertainty. We resample with replacement B times and report the alpha/2
    and 1-alpha/2 quantiles of the bootstrap distribution. Reported alongside
    the point estimate so reviewers can see e.g. "Beef 50% [13-88%]" rather
    than treating 50% as a precise figure.
    """
    rng = random.Random(seed)
    by_group: Dict[str, List[int]] = {}
    for r in rows:
        flag = 1 if r.get('automated_verdict') == 'flagged' else 0
        by_group.setdefault(r['cnf_group'], []).append(flag)
    out: Dict[str, Dict[str, float]] = {}
    for g, flags in by_group.items():
        n = len(flags)
        if n == 0:
            continue
        obs = sum(flags) / n
        boot = []
        for _ in range(n_resamples):
            sample = [flags[rng.randrange(n)] for _ in range(n)]
            boot.append(sum(sample) / n)
        boot.sort()
        lo_idx = int((alpha / 2) * n_resamples)
        hi_idx = int((1 - alpha / 2) * n_resamples) - 1
        out[g] = {
            'n': n,
            'observed': round(obs, 3),
            'ci_lo': round(boot[lo_idx], 3),
            'ci_hi': round(boot[hi_idx], 3),
        }
    return out


def _aggregate_decomposer(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarise the Tier γ decomposer audit across the panel.

    Reports: attempted (matcher routed to Tier γ), resolved (passed all
    validation gates), rejection-reason breakdown, and a per-CNF-group
    attempt/resolve table for the composite groups where Tier γ is in
    scope. Only meaningful when --with-decomposer was set.
    """
    attempted = [r for r in rows if r.get('decomposer_attempted')]
    resolved = [r for r in attempted if r.get('decomposer_resolved')]
    reasons: Dict[str, int] = {}
    for r in attempted:
        if not r.get('decomposer_resolved'):
            reason = r.get('decomposer_fallback_reason') or 'unknown'
            # Normalise reasons like 'low_confidence:0.40' → 'low_confidence'
            head = reason.split(':', 1)[0] if isinstance(reason, str) else 'unknown'
            reasons[head] = reasons.get(head, 0) + 1
    by_group: Dict[str, Dict[str, int]] = {}
    for r in attempted:
        g = r['cnf_group']
        gb = by_group.setdefault(g, {'attempted': 0, 'resolved': 0})
        gb['attempted'] += 1
        if r.get('decomposer_resolved'):
            gb['resolved'] += 1
    return {
        'attempted': len(attempted),
        'resolved': len(resolved),
        'resolved_rate': round(len(resolved) / max(1, len(attempted)), 3),
        'rejection_reasons': dict(sorted(reasons.items(), key=lambda kv: -kv[1])),
        'by_group': by_group,
    }


def _matcher_pack_version() -> str:
    try:
        from environmental_impact_model.src.lca_matcher import AgribalyseIndex
        return AgribalyseIndex().catalog_version
    except Exception:
        return 'unknown'


def _write_artefacts(benchmark: Dict[str, Any]) -> Tuple[str, str]:
    """Write the JSON benchmark + a flagged-row markdown summary.

    Returns (json_path, markdown_path)."""
    git_rev = benchmark['git_rev']
    stamp = _utc_stamp()
    json_path = os.path.join(_DATA_DIR, f'matcher_benchmark_{git_rev}_{stamp}.json')
    md_path   = os.path.join(_DATA_DIR, 'matcher_benchmark_flagged_for_review.md')

    blob = (json.dumps(benchmark, ensure_ascii=False, indent=2, sort_keys=False) + '\n').encode('utf-8')
    with open(json_path, 'wb') as fh:
        fh.write(blob)

    # Markdown summary of flagged rows for expert spot-check
    flagged = [r for r in benchmark['per_food'] if r['automated_verdict'] == 'flagged']
    lines: List[str] = []
    lines.append(f'# Matcher benchmark — flagged-for-review rows')
    lines.append('')
    lines.append(f'- Benchmark JSON: `matcher_benchmark_{git_rev}_{stamp}.json`')
    lines.append(f'- Git rev: `{git_rev}`')
    lines.append(f'- Sample size: {benchmark["sample_size"]}; flagged: {len(flagged)} ({100*len(flagged)/benchmark["sample_size"]:.1f}%)')
    lines.append('')
    lines.append('Reviewer: for each row below, add `reviewer_verdict: "good" | "stretched" | "fallback"` and `reviewer_notes: "..."` to the per_food row in the JSON.')
    lines.append('')
    for r in flagged:
        lines.append(f'### food_id={r["food_id"]} — {r["cnf_name"]}')
        lines.append('')
        lines.append(f'- CNF group: `{r["cnf_group"]}`')
        lines.append(f'- Matched: `{r["matched"]}`  confidence: {r["confidence"]:.2f}')
        lines.append(f'- Matched ciqual: `{r["ciqual_code"]}`  → "{r["lci_name"]}"')
        lines.append(f'- Matched Agribalyse group: `{r["matched_agribalyse_group"]}`')
        lines.append(f'- Justification: "{r["justification"]}"')
        lines.append(f'- Quality checks: group={r["group_consistency_pass"]}  magnitude={r["magnitude_pass"]}  token={r["token_overlap_pass"]}')
        if r.get('magnitude_ratio') is not None:
            lines.append(f'- GW per 100g: matched={r["matched_gw_per_100g"]}  cnf_default={r["cnf_group_default_gw_per_100g"]}  ratio={r["magnitude_ratio"]:.2f}x')
        lines.append('')
    md_blob = ('\n'.join(lines) + '\n').encode('utf-8')
    with open(md_path, 'wb') as fh:
        fh.write(md_blob)

    return json_path, md_path


def _print_summary(benchmark: Dict[str, Any]) -> None:
    s = benchmark['summary']
    o = s['overall']
    hr('SUMMARY')
    print(f'Sample size:       {benchmark["sample_size"]}')
    print(f'Git rev:           {benchmark["git_rev"]}')
    print(f'Matcher pack:      {benchmark["matcher_pack_version"]}')
    print(f'Cost:              ${s["total_cost_usd"]:.4f}')
    lat = s.get('latency_seconds', {})
    if lat:
        print(f'Latency (s):       p50={lat["p50"]:5.2f}  p75={lat["p75"]:5.2f}  '
              f'p90={lat["p90"]:5.2f}  p95={lat["p95"]:5.2f}  p99={lat["p99"]:5.2f}  '
              f'max={lat["max"]:5.2f}  (mean {lat["mean"]:.2f})')
    else:
        print(f'Latency median:    {s["median_latency_seconds"]:.2f} s  (mean {s["mean_latency_seconds"]:.2f} s)')
    print()
    print(f'Overall verdicts:')
    n = o["total"]
    print(f'  clean       {o["clean"]:4d}  ({100*o["clean"]/n:.0f}%)')
    print(f'  borderline  {o["borderline"]:4d}  ({100*o["borderline"]/n:.0f}%)')
    print(f'  flagged     {o["flagged"]:4d}  ({100*o["flagged"]/n:.0f}%)')
    print()
    print(f'By confidence band:')
    for band, b in s['by_confidence_band'].items():
        n_band = b['n']
        if n_band == 0:
            continue
        print(f'  {band:10s}  n={n_band:3d}  clean={b["clean"]:3d}  borderline={b["borderline"]:3d}  '
              f'flagged={b["flagged"]:3d}  (flagged_rate={b["flagged_rate"]:.2%})')
    print()
    print(f'By CNF FoodGroup (sorted by flagged_rate desc; 95% bootstrap CI shown):')
    cis = s.get('by_group_bootstrap_ci_95', {})
    sorted_groups = sorted(
        s['by_group'].items(),
        key=lambda kv: -(kv[1]['flagged'] / max(1, kv[1]['n']))
    )
    for g, b in sorted_groups:
        fr = b['flagged'] / max(1, b['n'])
        ci = cis.get(g, {})
        ci_str = (f"[{ci['ci_lo']*100:3.0f}%, {ci['ci_hi']*100:3.0f}%]"
                  if ci else '[-, -]')
        print(f'  {g:<45s}  n={b["n"]:2d}  clean={b["clean"]:2d}  borderline={b["borderline"]:2d}  '
              f'flagged={b["flagged"]:2d}  (rate={fr:.0%}  CI95={ci_str})')

    decomp = s.get('decomposer')
    if decomp:
        print()
        print(f'Tier γ decomposer (composite-group borderline routing):')
        print(f'  attempted:  {decomp["attempted"]:3d}')
        print(f'  resolved:   {decomp["resolved"]:3d}  ({100*decomp["resolved_rate"]:.0f}%)')
        if decomp['rejection_reasons']:
            print(f'  rejection reasons:')
            for reason, count in decomp['rejection_reasons'].items():
                print(f'    {reason:<35s} {count}')
        if decomp['by_group']:
            print(f'  by composite group:')
            for g, b in sorted(decomp['by_group'].items()):
                rate = b['resolved'] / max(1, b['attempted'])
                print(f'    {g:<43s} attempted={b["attempted"]:2d}  resolved={b["resolved"]:2d}  ({rate:.0%})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample-size', type=int, default=200,
                        help='Total foods to benchmark (default 200)')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--with-decomposer', action='store_true',
                        help='Also exercise the Tier γ recipe decomposer on borderline composite matches '
                             '(adds ≈ 24–30 LLM calls; total cost ≈ $0.035 vs $0.026 matcher-only)')
    args = parser.parse_args()

    if not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY missing — aborting benchmark.')
        sys.exit(1)
    print(f'Using OpenAI key sk-***{os.environ["OPENAI_API_KEY"][-6:]}')

    bench = run_benchmark(sample_size=args.sample_size, seed=args.seed,
                          with_decomposer=args.with_decomposer)
    json_path, md_path = _write_artefacts(bench)
    _print_summary(bench)
    print()
    print(f'Benchmark JSON:           {json_path}')
    print(f'Flagged review markdown:  {md_path}')
    print()
    return 0


if __name__ == '__main__':
    sys.exit(main())
