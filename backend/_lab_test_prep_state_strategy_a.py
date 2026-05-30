"""Lab Test — Strategy A simulator (matcher prep-state re-rank, no production change).

Strategy A in the lab plan is: pass a prep-state hint into the matcher's LLM
re-rank prompt so it prefers candidates whose CNF description matches the
asserted prep state. This script *simulates* that without changing matcher
code — it post-processes the matcher's existing top-20 alternatives:

  1. Run ``CNFMatcher.match(query, retrieval_only=True)`` — returns top-1 +
     up to 19 alternatives sorted by cosine sim (no LLM rerank yet).
  2. Extract a regex prep-state from the QUERY ("boiled egg on salad" →
     thermal=boiled, preservation=fresh). This is what Strategy A would
     pass as a hint to the LLM in production.
  3. For each alternative + the top-1, extract prep-state from its
     description and compute a re-rank score:
        score = cosine_sim
              + 0.20 if extracted.thermal_state == query.thermal_state (and != 'unknown')
              + 0.10 if extracted.preservation_state == query.preservation_state (and != 'unknown')
        (Boost magnitudes chosen so a same-prep candidate within 0.30 cosine of
        the top can overtake; cross-prep candidates need a real semantic edge.)
  4. Top-1 after re-rank is Strategy A's pick.
  5. Compare Strategy A's pick against the baseline (LLM-reranked) pick from
     the existing matcher probe baseline.

Reports for each probe: did Strategy A switch the pick? Did the switch help
(more probes now correct on both food_id and prep_state)?

Cheaper than re-running the matcher: this probe issues only ONE retrieval-only
call per GT probe (no LLM ranking), so ~$0.10 for the full panel.
"""
from __future__ import annotations

import io
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_HERE, '.env'))
except Exception:
    pass
os.environ.setdefault('DJANGO_SECRET_KEY', 'lab-prep-state-strategy-a')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from api.services.cnf_matcher import get_default_matcher  # noqa: E402
from api.services.prep_state_extract import (  # noqa: E402
    extract_prep_state,
    thermal_states_equivalent,
    preservation_states_equivalent,
)


GROUNDTRUTH_PATH = os.path.join(_HERE, '_lab_prep_state_groundtruth.json')
BASELINE_PATH = os.path.join(_HERE, '_lab_test_prep_state_matcher_baseline.json')
OUT_PATH = os.path.join(_HERE, '_lab_test_prep_state_strategy_a_baseline.json')

# Boost magnitudes for the re-rank. Tuned so a same-prep cosine-0.65 candidate
# can overtake a cross-prep cosine-0.85 candidate (0.85 - 0.65 = 0.20 — exactly
# the thermal boost — so ties go to the cross-prep when prep gap is small).
THERMAL_BOOST = 0.20
PRESERVATION_BOOST = 0.10


@dataclass
class StrategyAOutcome:
    label: str
    query: str
    category: str
    expected_food_ids: List[int]
    expected_thermal_state: str
    expected_preservation_state: str
    query_thermal_state: str
    query_preservation_state: str
    # Baseline (LLM-reranked) pick from the existing matcher baseline JSON.
    baseline_food_id: Optional[int]
    baseline_food_description: str
    baseline_thermal: str
    baseline_preservation: str
    baseline_food_id_correct: bool
    baseline_both_correct: bool
    # Strategy A pick.
    strategy_a_food_id: Optional[int]
    strategy_a_food_description: str
    strategy_a_thermal: str
    strategy_a_preservation: str
    strategy_a_food_id_correct: bool
    strategy_a_both_correct: bool
    # Switched?
    switched: bool

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _strategy_a_pick(
    query: str, matcher,
) -> Tuple[Optional[int], str, str, str, str, str]:
    """Returns (food_id, description, thermal, preservation, query_thermal, query_preservation).

    Runs matcher in retrieval-only mode (no LLM rerank), then post-applies
    prep-state boost to the top-1 + alternatives and picks the highest scorer.
    """
    result = matcher.match(query, retrieval_only=True)
    q_ps = extract_prep_state(query)

    # Candidate set = the top match + its alternatives (all share cosine sim).
    candidates: List[Tuple[int, str, float]] = []
    if result.food_id is not None and result.food_description is not None:
        candidates.append((result.food_id, result.food_description, float(result.confidence)))
    for alt in (result.alternatives or []):
        candidates.append((alt.food_id, alt.food_description, float(alt.similarity)))

    if not candidates:
        return None, '', 'unknown', 'unknown', q_ps.thermal_state, q_ps.preservation_state

    best_score = -1.0
    best: Tuple[int, str, str, str] = (candidates[0][0], candidates[0][1], 'unknown', 'unknown')
    for fid, desc, cos in candidates:
        c_ps = extract_prep_state(desc)
        score = cos
        # Thermal boost: only when BOTH query and candidate have a specific
        # thermal state AND they're equivalent (cooked-class equivalence).
        if (q_ps.thermal_state != 'unknown'
                and c_ps.thermal_state != 'unknown'
                and thermal_states_equivalent(c_ps.thermal_state, q_ps.thermal_state)):
            score += THERMAL_BOOST
        if (q_ps.preservation_state != 'unknown'
                and c_ps.preservation_state != 'unknown'
                and preservation_states_equivalent(c_ps.preservation_state, q_ps.preservation_state)):
            score += PRESERVATION_BOOST
        if score > best_score:
            best_score = score
            best = (fid, desc, c_ps.thermal_state, c_ps.preservation_state)

    return best[0], best[1], best[2], best[3], q_ps.thermal_state, q_ps.preservation_state


def main() -> int:
    if not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY not set. Aborting.')
        return 2
    if not os.path.exists(BASELINE_PATH):
        print(f'No matcher baseline at {BASELINE_PATH}. Run the matcher probe first.')
        return 2

    with open(GROUNDTRUTH_PATH, encoding='utf-8') as f:
        gt = json.load(f)
    probes = gt['probes']
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    baseline_by_label = {row['label']: row for row in baseline['per_probe']}

    matcher = get_default_matcher()
    outcomes: List[StrategyAOutcome] = []
    n_switched = 0
    for probe in probes:
        b = baseline_by_label.get(probe['label']) or {}
        fid, desc, th, pr, q_th, q_pr = _strategy_a_pick(probe['query'], matcher)
        a_fid_correct = (fid in probe['expected_food_ids']) if probe['expected_food_ids'] else False
        a_t_ok = thermal_states_equivalent(th, probe['expected_thermal_state'])
        a_p_ok = preservation_states_equivalent(pr, probe['expected_preservation_state'])
        switched = fid != b.get('matched_food_id')
        if switched:
            n_switched += 1
        outcomes.append(StrategyAOutcome(
            label=probe['label'],
            query=probe['query'],
            category=probe['category'],
            expected_food_ids=list(probe['expected_food_ids']),
            expected_thermal_state=probe['expected_thermal_state'],
            expected_preservation_state=probe['expected_preservation_state'],
            query_thermal_state=q_th,
            query_preservation_state=q_pr,
            baseline_food_id=b.get('matched_food_id'),
            baseline_food_description=b.get('matched_food_description', ''),
            baseline_thermal=b.get('extracted_thermal_state', 'unknown'),
            baseline_preservation=b.get('extracted_preservation_state', 'unknown'),
            baseline_food_id_correct=bool(b.get('food_id_correct', False)),
            baseline_both_correct=bool(b.get('prep_state_both_correct', False)),
            strategy_a_food_id=fid,
            strategy_a_food_description=desc,
            strategy_a_thermal=th,
            strategy_a_preservation=pr,
            strategy_a_food_id_correct=a_fid_correct,
            strategy_a_both_correct=a_t_ok and a_p_ok,
            switched=switched,
        ))

    n = len(outcomes)
    b_food = sum(o.baseline_food_id_correct for o in outcomes) / n
    a_food = sum(o.strategy_a_food_id_correct for o in outcomes) / n
    b_both = sum(o.baseline_both_correct for o in outcomes) / n
    a_both = sum(o.strategy_a_both_correct for o in outcomes) / n

    helpful = sum(1 for o in outcomes if (o.strategy_a_both_correct and not o.baseline_both_correct))
    harmful = sum(1 for o in outcomes if (not o.strategy_a_both_correct and o.baseline_both_correct))

    print('=' * 100)
    print(f'STRATEGY A SIMULATOR — {n} probes')
    print('=' * 100)
    print(f'food_id_acc     baseline={b_food*100:5.1f}%   strategy_a={a_food*100:5.1f}%   '
          f'(Δ {(a_food - b_food)*100:+5.1f}pp)')
    print(f'both_acc        baseline={b_both*100:5.1f}%   strategy_a={a_both*100:5.1f}%   '
          f'(Δ {(a_both - b_both)*100:+5.1f}pp)')
    print(f'switched: {n_switched}/{n} probes  '
          f'(helpful={helpful}, harmful={harmful}, net={helpful - harmful})')
    print('-' * 100)
    print('Switches:')
    for o in outcomes:
        if not o.switched:
            continue
        b_mark = 'OK' if o.baseline_both_correct else '..'
        a_mark = 'OK' if o.strategy_a_both_correct else '..'
        verdict = '+' if (o.strategy_a_both_correct and not o.baseline_both_correct) \
                  else ('-' if (not o.strategy_a_both_correct and o.baseline_both_correct) else '=')
        print(f'  [{verdict}]  {o.label:<32}  '
              f'baseline[{b_mark}] id={o.baseline_food_id} ({o.baseline_thermal}/{o.baseline_preservation})  '
              f'-> strategy_a[{a_mark}] id={o.strategy_a_food_id} ({o.strategy_a_thermal}/{o.strategy_a_preservation})  '
              f'query=({o.query_thermal_state}/{o.query_preservation_state})')

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'n': n,
                'baseline_food_id_acc': round(b_food, 3),
                'strategy_a_food_id_acc': round(a_food, 3),
                'baseline_both_acc': round(b_both, 3),
                'strategy_a_both_acc': round(a_both, 3),
                'switched': n_switched,
                'helpful': helpful,
                'harmful': harmful,
                'net': helpful - harmful,
            },
            'thermal_boost': THERMAL_BOOST,
            'preservation_boost': PRESERVATION_BOOST,
            'per_probe': [o.as_dict() for o in outcomes],
        }, f, ensure_ascii=False, indent=2, sort_keys=True)
    print()
    print(f'Wrote {OUT_PATH}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
