"""HEFI-2019 canonical-diet smoke (Brassard et al. 2022 reference targets).

Three CNF-constructed 1-day diets are scored via POST /api/hefi/calculate/
and gated against directional targets. Per `tranquil-coalescing-acorn.md`
Phase 2 + the 2026-05-23 re-scoping note, the gates are directional rather
than literature-pinned-mean reproduction (Brassard's 43.1/80 is a
population-level usual-intake aggregate from CCHS 24-h recalls, not a
1-day diet score; reproducing it from a single synthesised meal would be
methodologically incoherent).

Gates:
  (A) Mixed-balanced 1-day diet     → 35 <= HEFI <= 55   (centred on population p25-p75)
  (B) CFG-2019-aligned ideal diet   → HEFI >= 55         (one-sided; CFG diets score ~67)
  (C) Deep-fried anti-pattern diet  → HEFI <= 30         (one-sided; below population p10)

The directional rank (C) < (A) < (B) is the load-bearing assertion: it
validates the HEFI pipeline ranks diets by dietary-guideline alignment.

Run from `backend/`:
    python _smoke_hefi_canonical_diets.py
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Tuple

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-hefi-canonical-diets'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402


@dataclass
class DietPanel:
    label: str
    rationale: str
    # Each entry: (food_id, amount_g, note)
    foods: List[Tuple[int, float, str]] = field(default_factory=list)
    # Directional gate: (lower_inclusive, upper_inclusive) — use math.inf for one-sided
    target_low: float = 0.0
    target_high: float = 80.0
    target_description: str = ''


# Diet (B) CFG-2019 ideal: half plate V&F, whole grains, plant protein, water.
# Mass roughly tuned to ~1700 kcal so the per-100-kcal normalisations land
# in published ranges.
DIET_CFG_IDEAL = DietPanel(
    label='CFG-2019 aligned ideal diet',
    rationale='Plant-forward, whole-grain, low-sodium pattern aligned to Canada\'s '
              'Food Guide 2019 plate. Expected to score in p90+ range (Brassard 2022 '
              'reports CFG-recipe-based 3-day diets at 67.1/80).',
    foods=[
        # Whole grains
        (5917, 180.0, 'Grains, quinoa, cooked'),
        (4497, 150.0, 'Grains, rice, brown, long-grain, cooked'),
        (4067, 90.0,  'Bread, whole wheat, commercial (3 slices)'),
        # Plant protein
        (3404, 150.0, 'Tofu, regular, firm — primary plant protein'),
        (2113, 100.0, 'Lentils, sprouted, raw'),
        # Vegetables (each contributes to half-plate V&F)
        (2026, 120.0, 'Broccoli, frozen, boiled'),
        (2380, 100.0, 'Carrot, raw'),
        (2132, 80.0,  'New Zealand spinach, raw'),
        # Fruits
        (1696, 200.0, 'Apple, raw, with skin (1 medium-large)'),
        # Healthy fats
        (422, 12.0,  'Vegetable oil, olive (~1 tbsp)'),
        (2589, 28.0, 'Nuts, walnuts, black, dried (~1 oz)'),
        # Beverages: plant milk (no SSB, water for the rest is HEFI-zero)
        (5241, 250.0, 'Plant-based beverage, soy, unenriched'),
    ],
    target_low=55.0, target_high=80.0,
    target_description='one-sided: HEFI >= 55/80 (CFG-recipe-based diets ~67)',
)

# Diet (C) deep-fried anti-pattern: high sodium, high sat fat, no V&F, no whole
# grains, no plant protein, sweetened beverages. Should score in p10 or lower.
DIET_ANTIPATTERN = DietPanel(
    label='Deep-fried fast-food anti-pattern',
    rationale='High-sodium / high-sat-fat / low-V&F / no-whole-grain pattern. '
              'Expected to score in p10 or lower (Brassard 2022 p10 = 27/80).',
    foods=[
        # Processed meats + fast food
        (4644, 200.0, 'Fast foods, hot dog, plain (1.3 hot dogs)'),
        (4962, 220.0, 'Pizza, pepperoni, frozen, cooked (2 slices)'),
        (1185, 100.0, 'Wiener (frankfurter), beef'),
        # Refined grain
        (4066, 90.0,  'Bread, white, commercial (3 slices)'),
        # High-sat-fat / discretionary
        (16, 30.0,   'Butter, whipped'),
        (4157, 150.0, 'Ice cream, vanilla, rich, 16% M.F.'),
        # Sweetened beverage (chocolate milk 2% as cola proxy — same sugar load)
        (70, 500.0, 'Milk, fluid, chocolate, partly skimmed, 2% M.F. (SSB proxy — '
                    'cola not directly indexable in this CNF revision)'),
    ],
    target_low=0.0, target_high=30.0,
    target_description='one-sided: HEFI <= 30/80 (below population p10)',
)

# Diet (A) mixed-balanced: typical North American 1-day intake mixing some
# whole grains + protein + some V&F + some discretionary. Aims for the
# population-mean band (Brassard 2022 mean 43.1; p25-p75 ~ 35-50).
DIET_MIXED = DietPanel(
    label='Mixed-balanced 1-day diet (representative)',
    rationale='Realistic North American 1-day intake: oatmeal + fruit + milk; '
              'tuna sandwich + carrot; chicken + rice + broccoli; coffee. '
              'Population-mean band (Brassard mean 43.1, p25-p75 ~ 35-50).',
    foods=[
        # Breakfast
        (1413, 40.0,  'Cereal, hot, oats, instant: regular, dry'),
        (1696, 150.0, 'Apple, raw, with skin'),
        (61, 200.0, 'Milk, fluid, partly skimmed, 2% M.F.'),
        # Lunch
        (4067, 60.0,  'Bread, whole wheat, commercial (2 slices)'),
        (3081, 90.0,  'Fish, tuna, light, canned in water, drained, salted'),
        (2380, 80.0,  'Carrot, raw'),
        # Dinner
        (1220, 100.0, 'Deli-meat, chicken breast, cooked, extra lean'),
        (4497, 150.0, 'Grains, rice, brown, long-grain, cooked'),
        (2026, 120.0, 'Broccoli, frozen, boiled'),
        # Snack/beverage
        (2873, 250.0, 'Coffee, brewed (with tap water)'),
    ],
    target_low=35.0, target_high=55.0,
    target_description='Brassard 2022 p25-p75 band (population mean 43.1/80)',
)


PANELS = [DIET_ANTIPATTERN, DIET_MIXED, DIET_CFG_IDEAL]


def _build_body(panel: DietPanel) -> dict:
    return {'foods': [{'food_id': fid, 'amount_g': g}
                       for fid, g, _ in panel.foods]}


def _call_hefi(client: Client, panel: DietPanel) -> tuple[Optional[float], Optional[dict], Optional[str]]:
    body = _build_body(panel)
    r = client.post('/api/hefi/calculate/', data=json.dumps(body),
                    content_type='application/json', secure=True)
    if r.status_code != 200:
        return None, None, f'HTTP {r.status_code}: {r.content[:300]!r}'
    try:
        p = r.json()
        d = p['data']
        total = float(d['total_score'])
        diag = {
            'percentage': float(d['percentage']),
            'components': {k: (v if isinstance(v, (int, float)) else v.get('score', v))
                            for k, v in d['components'].items()},
            'ratios': dict(d['ratios']),
            'inputs': dict(d['inputs']),
        }
        return total, diag, None
    except Exception as exc:
        return None, None, f'parse error: {exc!r}'


def main() -> int:
    client = Client()
    results = []
    print('HEFI-2019 canonical-diet smoke (Brassard et al. 2022 directional gates)')
    print('=' * 76)
    print()

    scores = []
    for panel in PANELS:
        total, diag, err = _call_hefi(client, panel)
        if err is not None:
            print(f'[ERROR] {panel.label}')
            print(f'        {err}')
            print()
            results.append({**asdict(panel), 'total_score': None, 'verdict': 'ERROR', 'error': err})
            continue

        within = panel.target_low <= total <= panel.target_high
        verdict = 'PASS' if within else 'FAIL'
        scores.append((panel.label, total))

        print(f'[{verdict:>4}] {panel.label}')
        print(f'        rationale: {panel.rationale}')
        print(f'        target   : {panel.target_description}  '
              f'[gate {panel.target_low:.0f}-{panel.target_high:.0f}/80]')
        print(f'        actual   : {total:.1f}/80  ({diag["percentage"]:.1f}%)')
        # Component scorecard
        comp_str = ', '.join(f'{k.split("_", 1)[-1]}={v}' for k, v in diag['components'].items())
        print(f'        components: {comp_str}')
        print()
        results.append({**asdict(panel),
                        'total_score': total,
                        'within_gate': within,
                        'verdict': verdict,
                        'diagnostics': diag})

    # Directional-rank assertion
    print('-' * 76)
    print('Directional-rank check (Anti-pattern < Mixed-balanced < CFG-ideal):')
    rank_pass = (
        len(scores) == 3 and
        scores[0][1] < scores[1][1] < scores[2][1]
    )
    if rank_pass:
        print(f'   PASS  rank: {scores[0][0][:30]}={scores[0][1]:.1f} < '
              f'{scores[1][0][:30]}={scores[1][1]:.1f} < {scores[2][0][:30]}={scores[2][1]:.1f}')
    else:
        print(f'   FAIL  scores out of expected order:')
        for label, score in scores:
            print(f'         {score:5.1f}  {label}')
    print()

    n_pass = sum(1 for r in results if r.get('verdict') == 'PASS')
    n_total = len(results)
    print('=' * 76)
    print(f'Summary: PASS={n_pass}/{n_total}  rank_check={"PASS" if rank_pass else "FAIL"}')

    out_path = os.path.join(_HERE, '_smoke_hefi_canonical_diets_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump({
            'panel_description': 'HEFI-2019 canonical-diets smoke (Brassard 2022 directional gates)',
            'gate_policy': 'directional (CFG-ideal >= 55, mixed 35-55, anti-pattern <= 30) + rank order',
            'summary': {
                'n_pass': n_pass, 'n_total': n_total,
                'directional_rank_pass': rank_pass,
            },
            'diets': results,
        }, f, indent=2)
    print(f'Results JSON: {out_path}')
    return 0 if (n_pass == n_total and rank_pass) else 1


if __name__ == '__main__':
    sys.exit(main())
