"""CNFMatcher smoke + accuracy harness (AI-MATCH-1, 2026-05-23).

Four panels of free-text → CNF FoodID probes against
``api.services.cnf_matcher.CNFMatcher``. Bypasses the HTTP layer (no rate
limit / circuit breaker) so the matcher itself is what's measured.

  Panel A — exact-name sanity (10 queries)
    Queries that contain the canonical CNF name verbatim or with trivial
    variation. Gate: top-1 matches the expected FoodID, confidence ≥ 0.85.
    NON-NEGOTIABLE: any Panel-A failure exits non-zero.

  Panel B — synonyms / foreign-language (10 queries)
    Queries that depend on bilingual or synonym handling
    ("aubergine" / "courgette" / French "yogourt"). Gate: top-1 OR any
    alternative matches an expected FoodID set.

  Panel C — compound / descriptive (10 queries)
    Queries that combine multiple properties ("low-fat chocolate milk",
    "whole-grain bread"). Gate: top-1 matches expected FoodID set.

  Panel D — brand / fusion / recipe-style (10 queries)
    Adversarial — "Beyond Meat burger", "rotisserie chicken", "homemade
    beef stew". Gate: top-3 contains an acceptable food group keyword.

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_cnf_matcher.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional, Set

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-cnf-matcher'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()


# --- Panels ---------------------------------------------------------------

@dataclass
class QueryProbe:
    panel: str
    query: str
    # ALLOWED match outcomes — top-1 or (panel D) any top-3 match against:
    expected_food_ids: Optional[Set[int]] = None         # specific CNF FoodID(s)
    expected_group_keyword: Optional[str] = None         # OR a food_group substring (case-insensitive)
    min_confidence: float = 0.6
    # Panel D allows the match to be in any of the alternatives:
    accept_in_alternatives: bool = False
    note: str = ''


# Panel A — exact-name sanity. Each query is an exact / near-exact CNF name.
# CNF FoodIDs verified via direct probe of FOOD_NAME.csv during harness build.
PANEL_A = [
    QueryProbe('A', 'Apple, raw, with skin', {1696}, min_confidence=0.85,
               note='canonical apple FoodID'),
    QueryProbe('A', 'Bread, white, commercial',
               {4066, 4067, 4068, 4069, 4070}, min_confidence=0.85,
               note='white bread family'),
    QueryProbe('A', 'Beef stew, canned', {4964}, min_confidence=0.85,
               note='canonical canned beef stew (used in HSR audit panel)'),
    QueryProbe('A', 'Cheese, cheddar', {119}, min_confidence=0.85,
               note='canonical cheddar'),
    QueryProbe('A', 'Vegetable oil, olive', {422}, min_confidence=0.85,
               note='canonical olive oil'),
    QueryProbe('A', 'Yogourt, plain, fat-free', {502157}, min_confidence=0.85,
               note='French CNF spelling (Yogourt) of plain yogurt'),
    QueryProbe('A', 'Milk, fluid, partly skimmed, 2% M.F.', {61}, min_confidence=0.85,
               note='canonical 2% milk'),
    QueryProbe('A', 'Cheese, brie', {20}, min_confidence=0.85,
               note='canonical brie'),
    QueryProbe('A', 'Apple juice, canned or bottled, without added vitamin C',
               {1495}, min_confidence=0.85,
               note='canonical apple juice'),
    QueryProbe('A', 'Salad dressing, mayonnaise, commercial, regular', {531},
               min_confidence=0.85, note='canonical mayonnaise'),
]


# Panel B — synonyms + foreign-language. Loose match: any acceptable FoodID set.
PANEL_B = [
    QueryProbe('B', 'aubergine', expected_group_keyword='vegetable',
               min_confidence=0.6, note='British / French → eggplant'),
    QueryProbe('B', 'courgette', expected_group_keyword='vegetable',
               min_confidence=0.6, note='British / French → zucchini'),
    QueryProbe('B', 'yogourt', expected_group_keyword='dairy',
               min_confidence=0.6, note='French spelling of yogurt (no qualifier)'),
    QueryProbe('B', 'rocket leaves', expected_group_keyword='vegetable',
               min_confidence=0.5, note='British → arugula'),
    QueryProbe('B', 'cilantro', expected_group_keyword='vegetable',
               min_confidence=0.5, note='Spanish/Mexican → coriander leaves (CNF likely uses coriander)'),
    QueryProbe('B', 'bell pepper red',
               expected_group_keyword='vegetable',
               min_confidence=0.6, note='descriptor synonym for sweet pepper'),
    QueryProbe('B', 'romaine lettuce',
               expected_group_keyword='vegetable',
               min_confidence=0.6, note='variety synonym for cos lettuce'),
    QueryProbe('B', 'soya sauce',
               expected_group_keyword='soup',          # CNF puts soy sauce in soups/sauces (FG6)
               min_confidence=0.5, note='British spelling of soy sauce'),
    QueryProbe('B', 'aniseed', expected_group_keyword='spices',
               min_confidence=0.5, note='UK spelling of anise seed (spices/herbs)'),
    QueryProbe('B', 'mangetout', expected_group_keyword='vegetable',
               min_confidence=0.5, note='French → snow peas'),
]


# Panel C — compound / descriptive. Should still rank confidently.
PANEL_C = [
    QueryProbe('C', 'low-fat chocolate milk', expected_group_keyword='dairy',
               min_confidence=0.6, note='attribute + flavor + commodity'),
    QueryProbe('C', 'whole grain bread', expected_group_keyword='baked',
               min_confidence=0.6, note='attribute + commodity'),
    QueryProbe('C', 'boneless skinless chicken breast',
               expected_group_keyword='poultry',
               min_confidence=0.6, note='cuts + attribute'),
    QueryProbe('C', 'unsweetened almond milk',
               expected_group_keyword='beverage',
               min_confidence=0.5, note='plant-based beverage'),
    QueryProbe('C', 'extra virgin olive oil',
               expected_food_ids={422},
               min_confidence=0.6, note='premium olive oil — should match canonical (CNF lacks "extra virgin" tier)'),
    QueryProbe('C', 'fat-free Greek yogurt',
               expected_food_ids={502188, 502157, 502158, 502159, 502187},
               min_confidence=0.6, note='Greek / plain / fat-free yogurt family'),
    QueryProbe('C', 'whole wheat pasta cooked',
               expected_group_keyword='cereal',         # FG20 Cereals, Grains and Pasta
               min_confidence=0.5, note='cooking-state + attribute'),
    QueryProbe('C', 'plain unsweetened coffee',
               expected_group_keyword='beverage',
               min_confidence=0.5),
    QueryProbe('C', 'sparkling water',
               expected_group_keyword='beverage',
               min_confidence=0.5),
    QueryProbe('C', 'roasted almonds unsalted',
               expected_group_keyword='nuts',
               min_confidence=0.5, note='nuts + processing + attribute'),
]


# Panel D — adversarial. Top-3 contains an acceptable match.
PANEL_D = [
    QueryProbe('D', 'Beyond Meat burger', expected_group_keyword='legume',
               min_confidence=0.3, accept_in_alternatives=True,
               note='plant-based brand-name burger; closest CNF will be a legume product'),
    QueryProbe('D', 'rotisserie chicken',
               expected_group_keyword='poultry',
               min_confidence=0.4, accept_in_alternatives=True),
    QueryProbe('D', 'homemade beef stew',
               expected_food_ids={4964, 502002, 502003},
               min_confidence=0.4, accept_in_alternatives=True,
               note='matches canned beef stew or beef-stew-with-vegetables'),
    QueryProbe('D', 'spaghetti bolognese',
               expected_group_keyword='mixed',          # FG22 Mixed Dishes
               min_confidence=0.4, accept_in_alternatives=True),
    QueryProbe('D', 'chicken pad thai',
               expected_group_keyword='mixed',
               min_confidence=0.3, accept_in_alternatives=True,
               note='fusion dish; closest CNF mixed-dish'),
    QueryProbe('D', 'kale chips',
               expected_group_keyword='snack',          # FG25 Snacks (or FG11 Vegetables)
               min_confidence=0.3, accept_in_alternatives=True),
    QueryProbe('D', 'protein shake whey',
               expected_group_keyword='beverage',
               min_confidence=0.3, accept_in_alternatives=True),
    QueryProbe('D', 'buddha bowl',
               expected_group_keyword='mixed',
               min_confidence=0.2, accept_in_alternatives=True,
               note='no canonical recipe; closest fit is mixed-dish or vegetable'),
    QueryProbe('D', 'avocado toast',
               expected_group_keyword='baked',
               min_confidence=0.3, accept_in_alternatives=True),
    QueryProbe('D', 'açai bowl',
               expected_group_keyword='fruit',
               min_confidence=0.2, accept_in_alternatives=True,
               note='fruit-based; closest fit likely a berry or smoothie entry'),
]


PANELS = {'A': PANEL_A, 'B': PANEL_B, 'C': PANEL_C, 'D': PANEL_D}
GATE_PANELS = {'A'}      # non-negotiable; failure → exit 1


# --- Runner ---------------------------------------------------------------

@dataclass
class ProbeResult:
    panel: str
    query: str
    expected: str                       # human-readable summary
    observed_food_id: Optional[int]
    observed_description: Optional[str]
    observed_group: Optional[str]
    observed_confidence: float
    observed_alternatives: List[dict] = field(default_factory=list)
    passed: bool = False
    detail: str = ''
    timing_ms: float = 0.0


def _matches_food_ids(rid: Optional[int], expected: Optional[Set[int]],
                      alts: List[dict], accept_alts: bool) -> bool:
    if expected is None:
        return False
    if rid in expected:
        return True
    if accept_alts:
        return any(a.get('food_id') in expected for a in alts)
    return False


def _matches_group_keyword(rgroup: Optional[str], expected_kw: Optional[str],
                           alts: List[dict], accept_alts: bool) -> bool:
    if not expected_kw:
        return False
    needle = expected_kw.lower()
    if rgroup and needle in rgroup.lower():
        return True
    if accept_alts:
        return any(needle in (a.get('food_group') or '').lower() for a in alts)
    return False


def run_panel(matcher, probes: List[QueryProbe]) -> List[ProbeResult]:
    results = []
    for p in probes:
        t0 = time.perf_counter()
        try:
            r = matcher.match(p.query)
        except Exception as exc:  # noqa: BLE001
            results.append(ProbeResult(
                panel=p.panel, query=p.query,
                expected=str(p.expected_food_ids or p.expected_group_keyword),
                observed_food_id=None, observed_description=None,
                observed_group=None, observed_confidence=0.0,
                passed=False, detail=f'exception: {exc!r}',
                timing_ms=(time.perf_counter() - t0) * 1000,
            ))
            continue
        d = r.to_dict()
        alts = d['alternatives']
        food_id_ok = _matches_food_ids(d['food_id'], p.expected_food_ids,
                                       alts, p.accept_in_alternatives)
        group_ok = _matches_group_keyword(d['food_group'], p.expected_group_keyword,
                                          alts, p.accept_in_alternatives)
        conf_ok = d['confidence'] >= p.min_confidence
        # Pass requires: either food_id or group keyword matches, AND confidence ≥ min.
        passed = (food_id_ok or group_ok) and conf_ok
        expected_str = (f'food_ids={sorted(p.expected_food_ids)}'
                        if p.expected_food_ids
                        else f'group~={p.expected_group_keyword!r}')
        detail_parts = []
        if not (food_id_ok or group_ok):
            detail_parts.append('no expected match')
        if not conf_ok:
            detail_parts.append(f'conf {d["confidence"]:.2f} < min {p.min_confidence}')
        if not detail_parts:
            detail_parts.append(p.note or 'ok')
        results.append(ProbeResult(
            panel=p.panel, query=p.query, expected=expected_str,
            observed_food_id=d['food_id'],
            observed_description=d['food_description'],
            observed_group=d['food_group'],
            observed_confidence=d['confidence'],
            observed_alternatives=alts,
            passed=passed,
            detail='; '.join(detail_parts),
            timing_ms=d['timing_ms'],
        ))
    return results


# --- Report ---------------------------------------------------------------

def _format_panel(panel: str, results: List[ProbeResult]) -> None:
    p_count = sum(1 for r in results if r.passed)
    print(f'\nPANEL {panel}: {p_count}/{len(results)} PASS')
    print('-' * 100)
    for r in results:
        mark = '[ OK ]' if r.passed else '[FAIL]'
        print(f'  {mark}  query={r.query[:36]:<36s} -> CNF {r.observed_food_id} '
              f'conf={r.observed_confidence:.2f}  ({r.timing_ms:.0f}ms)')
        print(f'         {(r.observed_description or "")[:80]}')
        print(f'         expected={r.expected} | {r.detail[:90]}')


def main() -> int:
    print('CNFMatcher smoke + accuracy harness (4 panels x 10 queries = 40 probes)')
    print('=' * 100)
    from api.services.cnf_matcher import get_default_matcher
    matcher = get_default_matcher()
    print(f'Corpus: {len(matcher.corpus.food_ids)} foods | '
          f'LLM ranking: {"yes" if matcher.chat_json_client else "NO (degraded)"} | '
          f'corpus version: {matcher.corpus.provenance.get("build_date_utc")}')

    all_results = {}
    for panel, probes in PANELS.items():
        all_results[panel] = run_panel(matcher, probes)
        _format_panel(panel, all_results[panel])

    # Totals
    flat = [r for rs in all_results.values() for r in rs]
    total_pass = sum(1 for r in flat if r.passed)
    print()
    print('=' * 100)
    print(f'Overall: PASS={total_pass}  FAIL={len(flat) - total_pass}  TOTAL={len(flat)}')
    print()
    for panel in PANELS:
        p = sum(1 for r in all_results[panel] if r.passed)
        t = len(all_results[panel])
        gate = ' (GATE)' if panel in GATE_PANELS else ''
        print(f'  Panel {panel}: {p}/{t} PASS{gate}')

    # Persist
    out_path = os.path.join(_HERE, '_smoke_cnf_matcher_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'harness': 'CNFMatcher smoke + accuracy (AI-MATCH-1)',
            'corpus_version': matcher.corpus.provenance.get('build_date_utc'),
            'totals': {
                'pass': total_pass, 'fail': len(flat) - total_pass, 'total': len(flat),
                'per_panel': {p: {'pass': sum(1 for r in all_results[p] if r.passed),
                                  'total': len(all_results[p])}
                              for p in PANELS},
            },
            'results': [
                {
                    'panel': r.panel, 'query': r.query, 'expected': r.expected,
                    'observed_food_id': r.observed_food_id,
                    'observed_description': r.observed_description,
                    'observed_group': r.observed_group,
                    'observed_confidence': round(r.observed_confidence, 3),
                    'observed_alternatives': [
                        {'food_id': a['food_id'],
                         'description': a['food_description'][:80],
                         'similarity': a['similarity']}
                        for a in r.observed_alternatives
                    ],
                    'passed': r.passed, 'detail': r.detail,
                    'timing_ms': round(r.timing_ms, 1),
                }
                for r in flat
            ],
        }, f, indent=2)
    print()
    print(f'Results JSON: {out_path}')

    # Gate: Panel A is non-negotiable
    panel_a_failed = any(not r.passed for r in all_results['A'])
    return 1 if panel_a_failed else 0


if __name__ == '__main__':
    sys.exit(main())
