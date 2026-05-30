"""Lab Test — Preparation-state matcher accuracy (Phase 1 baseline).

Measures how often ``CNFMatcher.match()`` resolves a free-text query to a CNF
FoodID with the CORRECT preparation state (thermal axis + preservation axis).
This is the headline metric the prep-state lab is built around: the matcher's
current ignorance of prep state is the root cause of decomposer + substitution
errors documented in the lab plan.

Pattern mirrors ``_lab_test_hsr_v9_overrides_snapshot.py``:
  capture  -> hits the live matcher for every probe in the ground-truth panel,
              writes a JSON baseline + a console scorecard
  verify   -> re-runs the same panel and reports drift vs the baseline; used
              after any matcher / corpus / tagger change to confirm we
              improved the targeted probes WITHOUT collateral regression

Scoring (per probe):
  food_id_correct          : top-1 FoodID is in expected_food_ids
  thermal_state_correct    : extract_prep_state(top-1 desc).thermal matches GT
                             (loose equivalence — any cooked verb counts when
                             GT says 'cooked')
  preservation_correct     : same for preservation axis
  prep_state_both_correct  : both axes match

The probe deliberately does NOT change any production code. Reading this file's
output is how we decide whether the lab plan's hard-filter strategy is worth
the engineering cost vs the soft-hint strategy alone.

Cost: ~$0.25 per run at gpt-4.1-mini rates (49 probes x 1 embedding + 1 rank).
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_HERE, '.env'))
except Exception:
    pass

os.environ.setdefault('DJANGO_SECRET_KEY', 'lab-prep-state-matcher')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from api.services.cnf_matcher import get_default_matcher  # noqa: E402
from api.services.prep_state_extract import (  # noqa: E402
    extract_prep_state,
    thermal_states_equivalent,
    preservation_states_equivalent,
)
from api.services.prep_state_nutrient_delta import (  # noqa: E402
    compute_nutrient_delta,
    summarise_distortion,
)


GROUNDTRUTH_PATH = os.path.join(_HERE, '_lab_prep_state_groundtruth.json')
BASELINE_PATH = os.path.join(_HERE, '_lab_test_prep_state_matcher_baseline.json')


@dataclass
class ProbeOutcome:
    label: str
    query: str
    category: str
    expected_food_ids: List[int]
    expected_thermal_state: str
    expected_preservation_state: str
    # Matcher output
    matched_food_id: Optional[int]
    matched_food_description: str
    matched_confidence: float
    used_ai_ranking: bool
    fallback_reason: Optional[str]
    # Derived prep-state from matched description (regex extractor)
    extracted_thermal_state: str
    extracted_preservation_state: str
    extractor_confidence: float
    # Verdict bits
    food_id_correct: bool
    thermal_state_correct: bool
    preservation_correct: bool
    prep_state_both_correct: bool
    # Nutrient distortion vs the first expected FoodID (per-100 g). None if either food
    # has no nutrient data or matched_food_id equals expected_food_ids[0].
    nutrient_delta: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _run_one(matcher, probe: Dict[str, Any]) -> ProbeOutcome:
    expected_thermal = probe['expected_thermal_state']
    expected_preservation = probe['expected_preservation_state']
    expected_ids = list(probe['expected_food_ids'])

    try:
        result = matcher.match(probe['query'])
    except Exception as exc:  # noqa: BLE001
        return ProbeOutcome(
            label=probe['label'],
            query=probe['query'],
            category=probe['category'],
            expected_food_ids=expected_ids,
            expected_thermal_state=expected_thermal,
            expected_preservation_state=expected_preservation,
            matched_food_id=None,
            matched_food_description='',
            matched_confidence=0.0,
            used_ai_ranking=False,
            fallback_reason='exception',
            extracted_thermal_state='unknown',
            extracted_preservation_state='unknown',
            extractor_confidence=0.0,
            food_id_correct=False,
            thermal_state_correct=False,
            preservation_correct=False,
            prep_state_both_correct=False,
            error=f'{type(exc).__name__}: {exc!r}'[:300],
        )

    desc = result.food_description or ''
    extracted = extract_prep_state(desc)
    food_id_correct = (result.food_id in expected_ids) if expected_ids else False
    thermal_ok = thermal_states_equivalent(extracted.thermal_state, expected_thermal)
    preservation_ok = preservation_states_equivalent(
        extracted.preservation_state, expected_preservation,
    )
    both_ok = thermal_ok and preservation_ok

    # Nutrient distortion vs the FIRST acceptable expected FoodID — only
    # meaningful when the matcher returned a different ID. None when same.
    nutrient_delta_dict: Optional[Dict[str, Any]] = None
    if (expected_ids and result.food_id is not None
            and result.food_id != expected_ids[0]):
        try:
            nd = compute_nutrient_delta(expected_ids[0], int(result.food_id))
            if nd is not None:
                nutrient_delta_dict = nd.as_dict()
        except Exception:  # noqa: BLE001
            nutrient_delta_dict = None

    return ProbeOutcome(
        label=probe['label'],
        query=probe['query'],
        category=probe['category'],
        expected_food_ids=expected_ids,
        expected_thermal_state=expected_thermal,
        expected_preservation_state=expected_preservation,
        matched_food_id=result.food_id,
        matched_food_description=desc,
        matched_confidence=round(result.confidence, 3),
        used_ai_ranking=result.used_ai_ranking,
        fallback_reason=result.fallback_reason,
        extracted_thermal_state=extracted.thermal_state,
        extracted_preservation_state=extracted.preservation_state,
        extractor_confidence=extracted.confidence,
        food_id_correct=food_id_correct,
        thermal_state_correct=thermal_ok,
        preservation_correct=preservation_ok,
        prep_state_both_correct=both_ok,
        nutrient_delta=nutrient_delta_dict,
        error=None,
    )


def _summarise(outcomes: List[ProbeOutcome]) -> Dict[str, Any]:
    n = len(outcomes)
    if n == 0:
        return {}
    food_id_acc = sum(o.food_id_correct for o in outcomes) / n
    thermal_acc = sum(o.thermal_state_correct for o in outcomes) / n
    pres_acc = sum(o.preservation_correct for o in outcomes) / n
    both_acc = sum(o.prep_state_both_correct for o in outcomes) / n

    by_category: Dict[str, Dict[str, Any]] = {}
    cats = Counter(o.category for o in outcomes)
    for cat in cats:
        cat_rows = [o for o in outcomes if o.category == cat]
        cn = len(cat_rows)
        by_category[cat] = {
            'n': cn,
            'food_id_acc': round(sum(o.food_id_correct for o in cat_rows) / cn, 3),
            'thermal_acc': round(sum(o.thermal_state_correct for o in cat_rows) / cn, 3),
            'preservation_acc': round(sum(o.preservation_correct for o in cat_rows) / cn, 3),
            'both_acc': round(sum(o.prep_state_both_correct for o in cat_rows) / cn, 3),
        }

    # Confusion: among probes where thermal axis is asserted (not 'unknown'),
    # what does the matcher actually return?
    confusion = Counter()
    for o in outcomes:
        if o.expected_thermal_state != 'unknown':
            confusion[(o.expected_thermal_state, o.extracted_thermal_state)] += 1
    confusion_list = sorted(
        ({'expected': k[0], 'got': k[1], 'count': v}
         for k, v in confusion.items()),
        key=lambda r: -r['count'],
    )

    # Nutrient distortion aggregate — only across probes where the matcher
    # returned a DIFFERENT food_id than expected_food_ids[0] AND we got a
    # nutrient_delta record back. Mean absolute Δ and Δ% per nutrient.
    distortion = _summarise_nutrient_distortion(outcomes)

    return {
        'n': n,
        'overall': {
            'food_id_acc': round(food_id_acc, 3),
            'thermal_acc': round(thermal_acc, 3),
            'preservation_acc': round(pres_acc, 3),
            'both_acc': round(both_acc, 3),
        },
        'by_category': by_category,
        'thermal_confusion': confusion_list,
        'nutrient_distortion': distortion,
    }


def _summarise_nutrient_distortion(outcomes: List[ProbeOutcome]) -> Dict[str, Any]:
    """Aggregate absolute / percent distortion across all probes that returned
    a nutrient_delta record."""
    rows = [o.nutrient_delta for o in outcomes if o.nutrient_delta is not None]
    if not rows:
        return {'n': 0}
    keys = ('kcal', 'sodium_mg', 'vitamin_c_mg', 'sat_fat_g', 'fibre_g')
    out: Dict[str, Any] = {'n': len(rows)}
    for k in keys:
        abs_sum, abs_count = 0.0, 0
        pct_sum, pct_count = 0.0, 0
        for r in rows:
            point = r.get(k) or {}
            d_abs = point.get('delta_abs')
            d_pct = point.get('delta_pct')
            if d_abs is not None:
                abs_sum += abs(d_abs)
                abs_count += 1
            if d_pct is not None:
                pct_sum += abs(d_pct)
                pct_count += 1
        out[k] = {
            'mean_abs_delta': round(abs_sum / abs_count, 2) if abs_count else None,
            'mean_abs_pct_delta': round(pct_sum / pct_count * 100, 1) if pct_count else None,
            'n_abs': abs_count,
            'n_pct': pct_count,
        }
    return out


def _print_scorecard(outcomes: List[ProbeOutcome], summary: Dict[str, Any]) -> None:
    print('=' * 100)
    print(f'PREP-STATE MATCHER LAB — {summary["n"]} probes')
    print('=' * 100)
    ov = summary['overall']
    print(f'OVERALL  food_id={ov["food_id_acc"]*100:5.1f}%   '
          f'thermal={ov["thermal_acc"]*100:5.1f}%   '
          f'preservation={ov["preservation_acc"]*100:5.1f}%   '
          f'both={ov["both_acc"]*100:5.1f}%')
    print('-' * 100)
    print('By category:')
    for cat, s in summary['by_category'].items():
        print(f'  {cat:<18} n={s["n"]:<3}  '
              f'food_id={s["food_id_acc"]*100:5.1f}%  '
              f'thermal={s["thermal_acc"]*100:5.1f}%  '
              f'preservation={s["preservation_acc"]*100:5.1f}%  '
              f'both={s["both_acc"]*100:5.1f}%')
    print('-' * 100)
    print('Thermal confusion (expected → got, asserted probes only):')
    for row in summary['thermal_confusion'][:20]:
        mark = '  ' if row['expected'] == row['got'] else 'XX'
        print(f'  {mark}  {row["expected"]:<10} -> {row["got"]:<10} x{row["count"]}')
    print('-' * 100)
    distortion = summary.get('nutrient_distortion') or {}
    if distortion.get('n'):
        print(f'Nutrient distortion vs expected_food_ids[0] '
              f'(n={distortion["n"]} mis-matched probes):')
        for k in ('kcal', 'sodium_mg', 'vitamin_c_mg', 'sat_fat_g', 'fibre_g'):
            p = distortion.get(k) or {}
            mad = p.get('mean_abs_delta')
            mpd = p.get('mean_abs_pct_delta')
            print(f'  {k:<16}  mean|Δ|={mad}  mean|Δ%|={mpd}%  '
                  f'(n_abs={p.get("n_abs")}, n_pct={p.get("n_pct")})')
        print('-' * 100)
    print('Per-probe results:')
    for o in outcomes:
        marks = ''.join([
            'F' if o.food_id_correct else 'f',
            'T' if o.thermal_state_correct else 't',
            'P' if o.preservation_correct else 'p',
        ])
        print(f'  [{marks}] {o.label:<32} q={o.query!r:<40} '
              f'→ id={o.matched_food_id} ({o.extracted_thermal_state}/{o.extracted_preservation_state})  '
              f'exp ids={o.expected_food_ids} ({o.expected_thermal_state}/{o.expected_preservation_state})')
        if o.error:
            print(f'       error: {o.error}')


def capture() -> int:
    if not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY not set. Aborting.')
        return 2
    with open(GROUNDTRUTH_PATH, encoding='utf-8') as f:
        gt = json.load(f)
    probes = gt['probes']

    matcher = get_default_matcher()
    outcomes: List[ProbeOutcome] = []
    print(f'Running {len(probes)} prep-state probes through CNFMatcher.match() ...')
    for i, probe in enumerate(probes, 1):
        out = _run_one(matcher, probe)
        outcomes.append(out)
        print(f'  [{i:>2}/{len(probes)}] {probe["label"]}  '
              f'→ id={out.matched_food_id} '
              f'({out.extracted_thermal_state}/{out.extracted_preservation_state})')

    summary = _summarise(outcomes)
    baseline_payload = {
        'groundtruth_version': gt.get('version'),
        'summary': summary,
        'per_probe': [o.as_dict() for o in outcomes],
    }
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump(baseline_payload, f, ensure_ascii=False, indent=2, sort_keys=True)
    print()
    _print_scorecard(outcomes, summary)
    print()
    print(f'Wrote {BASELINE_PATH}')
    return 0


def verify() -> int:
    """Re-run the panel and report drift vs the baseline (post-fix verification)."""
    if not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY not set. Aborting.')
        return 2
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline at {BASELINE_PATH}. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    baseline_by_label = {row['label']: row for row in baseline['per_probe']}

    with open(GROUNDTRUTH_PATH, encoding='utf-8') as f:
        gt = json.load(f)
    probes = gt['probes']

    matcher = get_default_matcher()
    outcomes: List[ProbeOutcome] = []
    drift: List[Dict[str, Any]] = []
    for probe in probes:
        out = _run_one(matcher, probe)
        outcomes.append(out)
        b = baseline_by_label.get(probe['label'], {})
        if b:
            changed = (
                out.matched_food_id != b.get('matched_food_id')
                or out.extracted_thermal_state != b.get('extracted_thermal_state')
                or out.extracted_preservation_state != b.get('extracted_preservation_state')
            )
            if changed:
                drift.append({
                    'label': out.label,
                    'baseline_food_id': b.get('matched_food_id'),
                    'current_food_id': out.matched_food_id,
                    'baseline_prep': (b.get('extracted_thermal_state'),
                                      b.get('extracted_preservation_state')),
                    'current_prep': (out.extracted_thermal_state,
                                     out.extracted_preservation_state),
                    'food_id_correct_now': out.food_id_correct,
                    'both_correct_now': out.prep_state_both_correct,
                })

    summary = _summarise(outcomes)
    _print_scorecard(outcomes, summary)
    print()
    print(f'DRIFT vs baseline: {len(drift)} probes changed')
    for d in drift:
        print(f'  {d["label"]}: id {d["baseline_food_id"]} -> {d["current_food_id"]} '
              f'  prep {d["baseline_prep"]} -> {d["current_prep"]}  '
              f'(now id_correct={d["food_id_correct_now"]} both_correct={d["both_correct_now"]})')

    base_ov = baseline['summary']['overall']
    cur_ov = summary['overall']
    delta = lambda k: (cur_ov[k] - base_ov[k]) * 100
    print()
    print('Deltas vs baseline (percentage points):')
    print(f'  food_id_acc      {base_ov["food_id_acc"]*100:5.1f}% → {cur_ov["food_id_acc"]*100:5.1f}%  ({delta("food_id_acc"):+5.1f}pp)')
    print(f'  thermal_acc      {base_ov["thermal_acc"]*100:5.1f}% → {cur_ov["thermal_acc"]*100:5.1f}%  ({delta("thermal_acc"):+5.1f}pp)')
    print(f'  preservation_acc {base_ov["preservation_acc"]*100:5.1f}% → {cur_ov["preservation_acc"]*100:5.1f}%  ({delta("preservation_acc"):+5.1f}pp)')
    print(f'  both_acc         {base_ov["both_acc"]*100:5.1f}% → {cur_ov["both_acc"]*100:5.1f}%  ({delta("both_acc"):+5.1f}pp)')
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else 'capture'
    if mode == 'capture':
        return capture()
    if mode in ('verify', 'verify_fixed'):
        return verify()
    print(f'Unknown mode: {mode!r}. Use "capture" or "verify".')
    return 2


if __name__ == '__main__':
    sys.exit(main())
