"""Lab Test — Evaluate the LLM-augmented prep-state tagger against the GT.

Runs the tagger's output (``api/data/cnf_prep_state.json``) against the
ground-truth panel and reports:

  - For each GT probe, look up ``prep_state_of(expected_food_ids[0])``.
  - Compare against the GT's asserted ``expected_thermal_state`` and
    ``expected_preservation_state`` using the same asymmetric equivalence
    semantics as the matcher probe.
  - Report accuracy overall + by category + by tagger source (regex vs
    LLM vs llm_overrode_regex).

The GT pre-check already validates the REGEX extractor against the GT
(60/60 pass). This eval validates the LLM-augmented tagger — the comparison
shows whether the LLM is adding value (resolving 'unknown' to a confident
specific state) or noise (overriding the regex with worse guesses).

Pass criteria for shipping the tagger:
  - >= 95% both_acc against the GT (matching the lab plan's bar).
  - LLM-overrode-regex switches should be CORRECT more often than they
    are wrong (net positive vs the regex-only baseline).
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, List

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
os.environ.setdefault('DJANGO_SECRET_KEY', 'lab-tagger-eval')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from api.cnf_cache import get_api_cnf_pipeline  # noqa: E402
from api.services.cnf_prep_state import prep_state_of  # noqa: E402
from api.services.prep_state_extract import (  # noqa: E402
    extract_prep_state,
    thermal_states_equivalent,
    preservation_states_equivalent,
)

GROUNDTRUTH_PATH = os.path.join(_HERE, '_lab_prep_state_groundtruth.json')


def _hydrate_descriptions(food_ids: List[int]) -> Dict[int, str]:
    pipe = get_api_cnf_pipeline()
    fn = pipe.food_name_df
    sub = fn[fn['FoodID'].isin(food_ids)][['FoodID', 'FoodDescription']]
    return {int(r['FoodID']): str(r['FoodDescription']) for _, r in sub.iterrows()}


def main() -> int:
    with open(GROUNDTRUTH_PATH, encoding='utf-8') as f:
        gt = json.load(f)
    probes = gt['probes']
    all_fids = [p['expected_food_ids'][0] for p in probes if p['expected_food_ids']]
    desc_by_fid = _hydrate_descriptions(all_fids)

    results: List[Dict[str, Any]] = []
    n_pass = n_fail = n_unlabeled = 0
    for p in probes:
        if not p['expected_food_ids']:
            continue
        fid = p['expected_food_ids'][0]
        desc = desc_by_fid.get(fid, '')
        tag = prep_state_of(fid)
        if tag is None:
            n_unlabeled += 1
            results.append({
                'label': p['label'],
                'food_id': fid,
                'category': p['category'],
                'expected': (p['expected_thermal_state'], p['expected_preservation_state']),
                'tagged': None,
                'source': 'unlabeled',
                'thermal_correct': False,
                'preservation_correct': False,
                'both_correct': False,
                'description': desc,
            })
            continue
        t_ok = thermal_states_equivalent(tag.thermal_state, p['expected_thermal_state'])
        p_ok = preservation_states_equivalent(tag.preservation_state, p['expected_preservation_state'])
        both = t_ok and p_ok
        if both:
            n_pass += 1
        else:
            n_fail += 1
        results.append({
            'label': p['label'],
            'food_id': fid,
            'category': p['category'],
            'expected': (p['expected_thermal_state'], p['expected_preservation_state']),
            'tagged': (tag.thermal_state, tag.preservation_state),
            'source': tag.source,
            'confidence': tag.confidence,
            'rationale': tag.rationale,
            'thermal_correct': t_ok,
            'preservation_correct': p_ok,
            'both_correct': both,
            'description': desc,
        })

    n_eval = n_pass + n_fail
    print('=' * 100)
    print(f'PREP-STATE TAGGER EVAL — {len(probes)} GT probes, {n_eval} evaluated, '
          f'{n_unlabeled} unlabeled')
    print('=' * 100)
    if n_eval > 0:
        print(f'OVERALL  both_acc={n_pass / n_eval * 100:5.1f}%  (PASS {n_pass}/{n_eval})')
    print('-' * 100)
    # By tagger source
    src_counter = Counter(r['source'] for r in results if r['tagged'] is not None)
    print('By tagger source:')
    for src, n in src_counter.items():
        rows = [r for r in results if r['source'] == src]
        n_correct = sum(1 for r in rows if r['both_correct'])
        print(f'  {src:<22} n={n:<3}  correct={n_correct}/{n}  ({n_correct/n*100:.1f}%)')

    # By GT category
    print('By GT category:')
    cats = sorted({r['category'] for r in results})
    for cat in cats:
        rows = [r for r in results if r['category'] == cat]
        n = len(rows)
        n_correct = sum(1 for r in rows if r['both_correct'])
        print(f'  {cat:<22} n={n:<3}  correct={n_correct}/{n}  ({n_correct/n*100:.1f}%)')

    print('-' * 100)
    print('Disagreements (tagger picked something different than GT asserted):')
    for r in results:
        if r['tagged'] is None or r['both_correct']:
            continue
        print(f'  {r["label"]:<32}  fid={r["food_id"]:<6}  '
              f'src={r["source"]:<22}  '
              f'tagged={r["tagged"]} exp={r["expected"]}  '
              f'desc={r["description"][:48]!r}  '
              f'why={r.get("rationale","")[:60]!r}')

    # Compare to regex-only baseline (from the GT pre-check pattern).
    n_regex_pass = 0
    n_tagger_better = 0
    n_tagger_worse = 0
    for r in results:
        if r['tagged'] is None:
            continue
        rps = extract_prep_state(r['description'])
        t_ok = thermal_states_equivalent(rps.thermal_state, r['expected'][0])
        p_ok = preservation_states_equivalent(rps.preservation_state, r['expected'][1])
        regex_both = t_ok and p_ok
        if regex_both:
            n_regex_pass += 1
        if r['both_correct'] and not regex_both:
            n_tagger_better += 1
        if regex_both and not r['both_correct']:
            n_tagger_worse += 1
    print('-' * 100)
    print(f'Regex-only baseline against same probes: {n_regex_pass}/{n_eval} '
          f'({n_regex_pass / n_eval * 100:.1f}%)')
    print(f'Tagger improved vs regex on {n_tagger_better} probes; '
          f'regressed on {n_tagger_worse}; net {n_tagger_better - n_tagger_worse}')
    return 0 if n_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
