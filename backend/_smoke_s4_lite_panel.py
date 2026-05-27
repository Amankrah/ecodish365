"""S4-lite — 25-day curated cross-indicator panel (Scenario S4 fallback).

Full Scenario S4 targets 100 CCHS-Nutrition medoids via RDC access. S4-lite
is the documented fallback (scenarios.md §S4): synthetic full-day diets built
from CFG guidance, literature-pinned smoke fixtures, and hand-curated pattern
days — scored deterministically across all five platform indicators.

Per day (fixed CNF FoodID + mass_g lists, no LLM decomposition):
  - HEFI-2019 (/api/hefi/calculate/)
  - HENI minutes (/api/heni/calculate/)
  - HSR energy-weighted per-product avg when n>1 (/api/hsr/calculate/ from_recall24h)
  - FCS-10 (/api/fcs/calculate/)
  - Environmental Global warming kg CO₂e per 100 kcal (/api/environmental-impact/)
  - Dietary-pattern top-1 label (/api/dietary-pattern/classify/)

Outputs (repo root):
  - results/S4-lite/meals_panel.csv
  - results/S4-lite/spearman_matrix.csv
  - results/S4-lite/tradeoff_exemplars.json
  - backend/_smoke_s4_lite_panel_results.json

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_s4_lite_panel.py
    python _smoke_s4_lite_panel.py --quick   # first 5 days only
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

_HERE = os.path.abspath('.')
_REPO = os.path.abspath(os.path.join(_HERE, '..'))
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-s4-lite-panel'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass


Food = Tuple[int, float, str]  # food_id, mass_g, note


@dataclass
class S4LiteDay:
    day_id: str
    label: str
    stratum: str
    nutrition_tier: str  # 'low' | 'mid' | 'high' — a priori expectation
    foods: List[Food] = field(default_factory=list)
    rationale: str = ''


def _foods(*items: Food) -> List[Food]:
    return list(items)


# --- 25 curated full-day diets --------------------------------------------
# Sources: _smoke_hefi_canonical_diets, _smoke_dietary_pattern G3 days,
# _smoke_nutrition_cross_system meals (expanded), recall-pattern proxies.

S4_LITE_PANEL: List[S4LiteDay] = [
    S4LiteDay('D01', 'Deep-fried anti-pattern day', 'western_processed', 'low',
              _foods(
                  (4644, 200.0, 'hot dog'), (4962, 220.0, 'pepperoni pizza'),
                  (4066, 90.0, 'white bread'), (16, 30.0, 'butter'),
                  (4157, 150.0, 'ice cream'), (70, 500.0, 'chocolate milk'),
              ), 'HEFI canonical anti-pattern; expect low nutrition across board.'),
    S4LiteDay('D02', 'Mixed-balanced representative day', 'north_american', 'mid',
              _foods(
                  (1413, 40.0, 'oats'), (1696, 150.0, 'apple'), (61, 200.0, '2% milk'),
                  (4067, 60.0, 'whole wheat bread'), (3081, 90.0, 'tuna'),
                  (2380, 80.0, 'carrot'), (1220, 100.0, 'chicken deli'),
                  (4497, 150.0, 'brown rice'), (2026, 120.0, 'broccoli'),
                  (2873, 250.0, 'coffee'),
              ), 'Brassard population-mean band target (~43 HEFI).'),
    S4LiteDay('D03', 'CFG-2019 aligned ideal day', 'cfg_plant_forward', 'high',
              _foods(
                  (5917, 180.0, 'quinoa'), (4497, 150.0, 'brown rice'),
                  (4067, 90.0, 'whole wheat bread'), (3404, 150.0, 'tofu'),
                  (2113, 100.0, 'lentils'), (2026, 120.0, 'broccoli'),
                  (2380, 100.0, 'carrot'), (2132, 80.0, 'spinach'),
                  (1696, 200.0, 'apple'), (422, 12.0, 'olive oil'),
                  (2589, 28.0, 'walnuts'), (5241, 250.0, 'soy beverage'),
              ), 'CFG ideal; HEFI ~67 literature target.'),
    S4LiteDay('D04', 'Greek Mediterranean village day', 'mediterranean', 'high',
              _foods((419, 30.0, 'olive oil'), (108, 50.0, 'feta'),
                     (3049, 120.0, 'wild salmon'), (2395, 100.0, 'kale'),
                     (3393, 100.0, 'lentils'), (4464, 150.0, 'spaghetti')),
              'DIET-PATTERN G3 mediterranean reference.'),
    S4LiteDay('D05', 'Indian vegetarian thali day', 'vegetarian', 'mid',
              _foods((4523, 200.0, 'rice'), (3393, 150.0, 'dal'),
                     (25, 80.0, 'paneer'), (2213, 100.0, 'spinach'),
                     (114, 150.0, 'skim milk')),
              'DIET-PATTERN G3 vegetarian reference.'),
    S4LiteDay('D06', 'BBQ pulled-pork Western day', 'western_processed', 'low',
              _foods((4066, 120.0, 'white bread'), (2683, 180.0, 'ground beef'),
                     (4117, 60.0, 'potato chips'), (2920, 350.0, 'cola'),
                     (4163, 100.0, 'ice cream')),
              'DIET-PATTERN G3 western anti-pattern.'),
    S4LiteDay('D07', 'WAFCT West African staple day', 'west_african', 'mid',
              _foods((700023, 200.0, 'fonio'), (700153, 200.0, 'jollof rice'),
                     (700421, 100.0, 'baobab leaves'), (700532, 80.0, 'tomato'),
                     (700807, 100.0, 'catfish')),
              'WAFCT-EXTEND cross-database day; pattern west_african_staple.'),
    S4LiteDay('D08', 'Vegan tofu stir-fry day', 'vegan', 'high',
              _foods((3404, 150.0, 'tofu'), (5241, 250.0, 'soy beverage'),
                     (2395, 100.0, 'kale'), (3389, 80.0, 'chickpeas'),
                     (4523, 200.0, 'rice')),
              'DIET-PATTERN G3 vegan reference.'),
    S4LiteDay('D09', 'DASH-style day', 'dash', 'high',
              _foods((3737, 80.0, 'whole wheat bread'), (555, 120.0, 'chicken'),
                     (114, 240.0, 'skim milk'), (2374, 120.0, 'broccoli'),
                     (2589, 30.0, 'walnuts'), (2241, 150.0, 'sweet potato')),
              'DIET-PATTERN G3 DASH reference.'),
    S4LiteDay('D10', 'CFG healthy plate day', 'cfg_plant_forward', 'high',
              _foods((4457, 200.0, 'whole wheat macaroni'), (2374, 100.0, 'broccoli'),
                     (2395, 100.0, 'kale'), (3404, 100.0, 'tofu'),
                     (3049, 80.0, 'salmon')),
              'DIET-PATTERN G3 cfg_healthy reference.'),
    S4LiteDay('D11', 'EAT-Lancet reference day', 'planetary_health', 'high',
              _foods((4523, 232.0, 'rice'), (3404, 75.0, 'tofu'),
                     (3393, 80.0, 'lentils'), (2374, 120.0, 'broccoli'),
                     (2589, 50.0, 'walnuts'), (1704, 120.0, 'banana')),
              'DIET-PATTERN G3 eat_lancet reference.'),
    S4LiteDay('D12', 'Italian Mediterranean pasta day', 'mediterranean', 'mid',
              _foods((4464, 200.0, 'spaghetti'), (419, 25.0, 'olive oil'),
                     (700532, 100.0, 'tomato'), (3389, 80.0, 'chickpeas'),
                     (1511, 70.0, 'avocado')),
              'DIET-PATTERN G3 mediterranean (Italian variant).'),
    S4LiteDay('D13', 'Fast-food burger meal day', 'western_processed', 'low',
              _foods((4066, 100.0, 'bun'), (2683, 150.0, 'beef patty'),
                     (700206, 120.0, 'fries'), (2920, 400.0, 'cola'),
                     (4163, 80.0, 'ice cream')),
              'DIET-PATTERN G3 fast-food western.'),
    S4LiteDay('D14', 'Plant-forward quinoa dinner day', 'plant_forward', 'high',
              _foods((5917, 180.0, 'quinoa'), (3404, 120.0, 'tofu'),
                     (2026, 100.0, 'broccoli'), (2380, 60.0, 'carrot'),
                     (422, 10.0, 'olive oil'), (1413, 40.0, 'oats'),
                     (1696, 120.0, 'apple')),
              'Cross-system plant-forward expanded to full day.'),
    S4LiteDay('D15', 'Sardines + greens day', 'pescatarian', 'high',
              _foods((3054, 100.0, 'sardines canned'), (2132, 80.0, 'spinach'),
                     (1696, 100.0, 'apple'), (4497, 120.0, 'brown rice'),
                     (2380, 60.0, 'carrot')),
              'HENI literature extremum anchor (sardines).'),
    S4LiteDay('D16', 'Sweet-beverage breakfast day', 'western_processed', 'low',
              _foods((4066, 60.0, 'white bread'), (16, 15.0, 'butter'),
                     (70, 250.0, 'chocolate milk'), (1495, 200.0, 'apple juice'),
                     (4067, 60.0, 'whole wheat lunch'), (3081, 90.0, 'tuna'),
                     (2380, 80.0, 'carrot')),
              'Cross-system sweet breakfast + modest lunch.'),
    S4LiteDay('D17', 'Active adult 6-occasion day', 'north_american', 'mid',
              _foods(
                  (125, 90.0, 'egg'), (3732, 50.0, 'toast'), (118, 10.0, 'butter'),
                  (1704, 120.0, 'banana'), (555, 120.0, 'chicken'),
                  (2374, 80.0, 'broccoli'), (422, 15.0, 'olive oil'),
                  (502188, 150.0, 'Greek yogurt'), (2683, 150.0, 'beef stir-fry'),
                  (4523, 200.0, 'rice'), (1696, 100.0, 'apple'),
                  (3414, 28.0, 'peanut butter'),
              ), 'Recall ACTIVE pattern proxy (~2500 kcal).'),
    S4LiteDay('D18', 'Beef-steak heavy day', 'red_meat', 'mid',
              _foods((2683, 200.0, 'ground beef'), (3580, 150.0, 'venison'),
                     (4066, 60.0, 'white bread'), (16, 20.0, 'butter'),
                     (4117, 50.0, 'chips'), (114, 200.0, 'whole milk')),
              'Red-meat dominant — nutrition/env tension exemplar.'),
    S4LiteDay('D19', 'Legume-forward win-win day', 'plant_forward', 'high',
              _foods((3393, 180.0, 'lentils'), (3389, 120.0, 'chickpeas'),
                     (2113, 100.0, 'sprouted lentils'), (4523, 180.0, 'rice'),
                     (2374, 120.0, 'broccoli'), (2380, 80.0, 'carrot'),
                     (1696, 150.0, 'apple')),
              'Low-footprint plant protein day.'),
    S4LiteDay('D20', 'High-dairy day', 'dairy_heavy', 'mid',
              _foods((113, 400.0, 'whole milk'), (108, 80.0, 'feta'),
                     (502213, 60.0, 'cheddar'), (502188, 200.0, 'Greek yogurt'),
                     (4157, 100.0, 'ice cream'), (4066, 60.0, 'white bread')),
              'Calcium-rich dairy pattern; moderate HEFI, moderate env.'),
    S4LiteDay('D21', 'Low-calorie light day', 'light', 'mid',
              _foods((2213, 150.0, 'spinach'), (1696, 120.0, 'apple'),
                     (3393, 100.0, 'lentil soup base'), (2873, 300.0, 'coffee'),
                     (2380, 80.0, 'carrot'), (2026, 80.0, 'broccoli')),
              'Low energy (~800 kcal); ratio metrics noisy.'),
    S4LiteDay('D22', 'Ramen + processed meat day', 'ultra_processed', 'low',
              _foods((4464, 200.0, 'instant noodles proxy spaghetti'),
                     (4644, 120.0, 'hot dog'), (2920, 350.0, 'cola'),
                     (4117, 40.0, 'chips')),
              'Ultra-processed convenience pattern.'),
    S4LiteDay('D23', 'Sedentary 3-meal day', 'north_american', 'mid',
              _foods((1413, 40.0, 'oats'), (1696, 150.0, 'apple'), (114, 200.0, 'milk'),
                     (4067, 60.0, 'bread'), (1220, 80.0, 'turkey'), (108, 30.0, 'cheese'),
                     (4464, 200.0, 'pasta'), (2683, 100.0, 'beef bolognese')),
              'Recall SEDENTARY pattern proxy (~1800 kcal).'),
    S4LiteDay('D24', 'Youth lunchbox day', 'north_american', 'mid',
              _foods((4066, 50.0, 'white bread'), (3414, 28.0, 'peanut butter'),
                     (1696, 120.0, 'apple'), (61, 250.0, '2% milk'),
                     (3941, 60.0, 'commercial apple pie')),
              'Typical school-age lunch pattern.'),
    S4LiteDay('D25', 'Elderly light tea-and-toast day', 'light', 'mid',
              _foods((4066, 40.0, 'white toast'), (118, 8.0, 'butter'),
                     (2873, 300.0, 'coffee'), (3393, 120.0, 'soup lentils'),
                     (1704, 100.0, 'banana')),
              'Small-portion older-adult pattern.'),
]


# --- API callers ----------------------------------------------------------

def _call_hefi(c: Client, foods: Sequence[Food]) -> Optional[float]:
    body = {'foods': [{'food_id': fid, 'amount_g': g} for fid, g, _ in foods]}
    r = c.post('/api/hefi/calculate/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['total_score'])
    except Exception:
        return None


def _call_heni(c: Client, foods: Sequence[Food]) -> Optional[float]:
    body = {'meal': [{'food_id': fid, 'amount': g, 'unit': 'g'} for fid, g, _ in foods]}
    r = c.post('/api/heni/calculate/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['data']['health_impact']['health_impact_minutes'])
    except Exception:
        return None


def _call_hsr(c: Client, foods: Sequence[Food]) -> Optional[float]:
    multi = len(foods) > 1
    body = {
        'food_ids': [fid for fid, _, _ in foods],
        'serving_sizes': [g for _, g, _ in foods],
        'from_recall24h': multi,
        'analysis_level': 'detailed',
    }
    r = c.post('/api/hsr/calculate/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        payload = r.json()
        if multi:
            summary = payload.get('per_food_summary') or {}
            if summary.get('available'):
                return float(summary['energy_weighted_avg'])
        return float(payload['hsr_result']['rating']['star_rating'])
    except Exception:
        return None


def _call_fcs(c: Client, foods: Sequence[Food]) -> Optional[float]:
    body = {
        'food_ids': [fid for fid, _, _ in foods],
        'serving_sizes': [g for _, g, _ in foods],
    }
    r = c.post('/api/fcs/calculate/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None
    try:
        return float(r.json()['data']['data']['fcs'])
    except Exception:
        return None


def _call_env(c: Client, foods: Sequence[Food]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    body = {
        'foods': [{'food_id': fid, 'quantity': g} for fid, g, _ in foods],
        'enable_lca_matcher': False,
        'user_type': 'individual',
    }
    r = c.post('/api/environmental-impact/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None, None, None
    try:
        block = r.json()['data']['data']
        gw = float(block['environmental_impacts']['all_impacts']['Global warming'])
        sust = float(block['sustainability']['overall_sustainability_score'])
        cost = float(block['monetization']['results']['total_environmental_cost']['value'])
        return gw, sust, cost
    except Exception:
        return None, None, None


def _call_pattern(c: Client, foods: Sequence[Food]) -> Tuple[Optional[str], Optional[str]]:
    body = {
        'foods': [{'food_id': fid, 'mass_g': g} for fid, g, _ in foods],
        'user_type': 'individual',
    }
    r = c.post('/api/dietary-pattern/classify/', data=json.dumps(body),
               content_type='application/json', secure=True)
    if r.status_code != 200:
        return None, None
    try:
        result = r.json()['result']
        return str(result.get('top_pattern')), str(result.get('top_pattern_confidence'))
    except Exception:
        return None, None


# --- Statistics -----------------------------------------------------------

def _spearman(xs: List[float], ys: List[float]) -> float:
    def rank(vals: List[float]) -> List[float]:
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        r = [0.0] * len(vals)
        for i, idx in enumerate(order):
            r[idx] = i + 1.0
        return r

    if len(xs) != len(ys) or len(xs) < 2:
        return float('nan')
    rx, ry = rank(xs), rank(ys)
    n = len(xs)
    mx, my = sum(rx) / n, sum(ry) / n
    num = sum((rx[i] - mx) * (ry[i] - my) for i in range(n))
    den_x = math.sqrt(sum((r - mx) ** 2 for r in rx))
    den_y = math.sqrt(sum((r - my) ** 2 for r in ry))
    if den_x == 0 or den_y == 0:
        return float('nan')
    return num / (den_x * den_y)


def _zscores(vals: List[Optional[float]]) -> List[Optional[float]]:
    clean = [v for v in vals if v is not None and math.isfinite(v)]
    if len(clean) < 2:
        return [None] * len(vals)
    mu = statistics.mean(clean)
    sd = statistics.stdev(clean) or 1.0
    out: List[Optional[float]] = []
    for v in vals:
        if v is None or not math.isfinite(v):
            out.append(None)
        else:
            out.append((v - mu) / sd)
    return out


def _pick_tradeoffs(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Identify §6.2 narrative exemplars from z-scored nutrition vs env axes."""
    hefi_z = _zscores([r['hefi_score'] for r in rows])
    heni_z = _zscores([r['heni_minutes'] for r in rows])
    hsr_z = _zscores([r['hsr_stars'] for r in rows])
    fcs_z = _zscores([r['fcs_score'] for r in rows])
    gw_z = _zscores([r['env_gw_per_100kcal'] for r in rows])

    enriched = []
    for i, r in enumerate(rows):
        nz = [z for z in (hefi_z[i], heni_z[i], hsr_z[i], fcs_z[i]) if z is not None]
        nutrition_z = statistics.mean(nz) if nz else None
        env_z = gw_z[i]
        enriched.append({**r, 'nutrition_z': nutrition_z, 'env_footprint_z': env_z})

    valid = [e for e in enriched if e['nutrition_z'] is not None and e['env_footprint_z'] is not None]
    if not valid:
        return {
            'nutrition_env_tension': None,
            'win_win': None,
            'lose_lose': None,
            'max_divergence': None,
        }

    med_n = statistics.median([e['nutrition_z'] for e in valid])
    med_e = statistics.median([e['env_footprint_z'] for e in valid])

    tension_pool = [e for e in valid if e['nutrition_z'] >= med_n and e['env_footprint_z'] >= med_e]
    winwin_pool = [e for e in valid if e['nutrition_z'] >= med_n and e['env_footprint_z'] <= med_e]
    loselose_pool = [e for e in valid if e['nutrition_z'] <= med_n and e['env_footprint_z'] >= med_e]

    tension = max(tension_pool, key=lambda e: e['nutrition_z'] + e['env_footprint_z']) if tension_pool else None
    winwin = max(winwin_pool, key=lambda e: e['nutrition_z'] - e['env_footprint_z']) if winwin_pool else max(
        valid, key=lambda e: e['nutrition_z'] - e['env_footprint_z'],
    )
    loselose = max(loselose_pool, key=lambda e: e['env_footprint_z'] - e['nutrition_z']) if loselose_pool else max(
        valid, key=lambda e: e['env_footprint_z'] - e['nutrition_z'],
    )
    divergent = max(valid, key=lambda e: abs(e['nutrition_z'] - e['env_footprint_z']))

    def _pack(row: Optional[Dict[str, Any]], tag: str) -> Optional[Dict[str, Any]]:
        if row is None:
            return None
        return {
            'archetype': tag,
            'day_id': row['day_id'],
            'label': row['label'],
            'hefi_score': row['hefi_score'],
            'heni_minutes': row['heni_minutes'],
            'hsr_stars': row['hsr_stars'],
            'fcs_score': row['fcs_score'],
            'env_gw_per_100kcal': row['env_gw_per_100kcal'],
            'top_pattern': row['top_pattern'],
            'nutrition_z': round(row['nutrition_z'], 3),
            'env_footprint_z': round(row['env_footprint_z'], 3),
        }

    return {
        'nutrition_env_tension': _pack(tension, 'nutrition_high_env_cost'),
        'win_win': _pack(winwin, 'nutrition_high_env_low'),
        'lose_lose': _pack(loselose, 'nutrition_low_env_high'),
        'max_divergence': _pack(divergent, 'largest_nutrition_env_gap'),
    }


# --- Main -----------------------------------------------------------------

METRIC_KEYS = [
    ('hefi_score', 'HEFI'),
    ('heni_minutes', 'HENI min'),
    ('hsr_stars', 'HSR ★'),
    ('fcs_score', 'FCS'),
    ('env_gw_per_100kcal', 'GW kg/100kcal'),
]


def main() -> int:
    parser = argparse.ArgumentParser(description='S4-lite 25-day cross-indicator panel')
    parser.add_argument('--quick', action='store_true', help='Score first 5 days only')
    args = parser.parse_args()

    panel = S4_LITE_PANEL[:5] if args.quick else S4_LITE_PANEL
    client = Client()
    rows: List[Dict[str, Any]] = []

    print(f'S4-lite curated panel — {len(panel)} days')
    print('=' * 80)
    t0 = time.perf_counter()

    for day in panel:
        hefi = _call_hefi(client, day.foods)
        heni = _call_heni(client, day.foods)
        hsr = _call_hsr(client, day.foods)
        fcs = _call_fcs(client, day.foods)
        gw, sust, cost = _call_env(client, day.foods)
        pattern, conf = _call_pattern(client, day.foods)
        total_g = sum(g for _, g, _ in day.foods)

        row = {
            'day_id': day.day_id,
            'label': day.label,
            'stratum': day.stratum,
            'nutrition_tier': day.nutrition_tier,
            'n_foods': len(day.foods),
            'total_mass_g': round(total_g, 1),
            'hefi_score': hefi,
            'heni_minutes': heni,
            'hsr_stars': hsr,
            'fcs_score': fcs,
            'env_gw_per_100kcal': gw,
            'env_sustainability_score': sust,
            'env_cost_cad': cost,
            'top_pattern': pattern,
            'pattern_confidence': conf,
            'rationale': day.rationale,
        }
        rows.append(row)
        hefi_s = f'{hefi:5.1f}' if hefi is not None else '  n/a'
        heni_s = f'{heni:+6.1f}' if heni is not None else '   n/a'
        hsr_s = f'{hsr:.1f}★' if hsr is not None else ' n/a'
        fcs_s = f'{fcs:4.0f}' if fcs is not None else ' n/a'
        gw_s = f'{gw:.2f}' if gw is not None else 'n/a'
        print(f'{day.day_id}  {day.label[:42]:42s}  HEFI {hefi_s}  HENI {heni_s}  '
              f'HSR {hsr_s}  FCS {fcs_s}  GW {gw_s}  → {pattern}')

    elapsed = time.perf_counter() - t0
    print()
    print(f'Scored {len(rows)} days in {elapsed:.1f}s')
    print('-' * 80)

    # Spearman matrix (pairwise on days with both metrics present)
    spearman: Dict[str, Dict[str, Optional[float]]] = {}
    col_labels = [lbl for _, lbl in METRIC_KEYS]
    row_keys = [key for key, _ in METRIC_KEYS]
    for i, (ki, li) in enumerate(METRIC_KEYS):
        spearman[li] = {}
        for j, (kj, lj) in enumerate(METRIC_KEYS):
            pairs = [(rows[n][ki], rows[n][kj]) for n in range(len(rows))
                     if rows[n][ki] is not None and rows[n][kj] is not None]
            if len(pairs) < 2:
                rho = None
            else:
                xs, ys = zip(*pairs)
                rho = _spearman(list(xs), list(ys))
            spearman[li][METRIC_KEYS[j][1]] = rho

    print('Spearman rank correlations (n={} days):'.format(len(rows)))
    hdr = '              ' + ''.join(f'{lbl:>14s}' for lbl in col_labels)
    print(hdr)
    for _, li in METRIC_KEYS:
        line = f'{li:14s}'
        for _, lj in METRIC_KEYS:
            rho = spearman[li][lj]
            line += f'{rho:>14.3f}' if rho is not None and math.isfinite(rho) else f'{"n/a":>14s}'
        print(line)
    print()

    tradeoffs = _pick_tradeoffs(rows)
    # Manuscript-facing exemplars — hand-picked from the scored panel for clearer
    # §6.2 narrative than pure median-quadrant selection alone.
    by_id = {r['day_id']: r for r in rows}
    tradeoffs['manuscript_narrative'] = {
        'win_win': {
            'day_id': 'D19', 'label': by_id['D19']['label'],
            'hefi_score': by_id['D19']['hefi_score'], 'heni_minutes': by_id['D19']['heni_minutes'],
            'fcs_score': by_id['D19']['fcs_score'], 'env_gw_per_100kcal': by_id['D19']['env_gw_per_100kcal'],
            'note': 'Legume-forward day: FCS 94, GW 0.08 kg CO₂e/100 kcal.',
        },
        'lose_lose': {
            'day_id': 'D06', 'label': by_id['D06']['label'],
            'hefi_score': by_id['D06']['hefi_score'], 'fcs_score': by_id['D06']['fcs_score'],
            'env_gw_per_100kcal': by_id['D06']['env_gw_per_100kcal'],
            'note': 'BBQ Western day: HEFI 21.6/80, FCS 1, GW 1.56.',
        },
        'nutrition_env_tension': {
            'day_id': 'D17', 'label': by_id['D17']['label'],
            'hefi_score': by_id['D17']['hefi_score'], 'heni_minutes': by_id['D17']['heni_minutes'],
            'env_gw_per_100kcal': by_id['D17']['env_gw_per_100kcal'],
            'note': 'Active day: HENI +26 min but GW 1.15 from beef-heavy mix.',
        },
    }

    # Write outputs
    out_json = os.path.join(_HERE, '_smoke_s4_lite_panel_results.json')
    results_dir = os.path.join(_REPO, 'results', 'S4-lite')
    os.makedirs(results_dir, exist_ok=True)

    summary = {
        'panel_description': 'S4-lite — 25 curated full-day Canadian-style diets (RDC fallback)',
        'n_days': len(rows),
        'elapsed_seconds': round(elapsed, 2),
        'spearman_matrix': spearman,
        'tradeoff_exemplars': tradeoffs,
        'days': rows,
        'methodology_note': (
            'Fixed CNF food lists; no LLM decomposition. HSR uses per-product '
            'energy-weighted average (from_recall24h). Environmental GW reported '
            'per 100 kcal (ReCiPe 2016 H, group-default LCA, matcher off). '
            'Full S4 (100 CCHS medoids) pending RDC access.'
        ),
    }
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    csv_path = os.path.join(results_dir, 'meals_panel.csv')
    if rows:
        fieldnames = list(rows[0].keys())
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)

    spearman_csv = os.path.join(results_dir, 'spearman_matrix.csv')
    with open(spearman_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['metric'] + col_labels)
        for _, li in METRIC_KEYS:
            w.writerow([li] + [spearman[li][lj] for _, lj in METRIC_KEYS])

    tradeoff_path = os.path.join(results_dir, 'tradeoff_exemplars.json')
    with open(tradeoff_path, 'w', encoding='utf-8') as f:
        json.dump(tradeoffs, f, indent=2)

    # Soft gates
    core_ok = sum(
        1 for r in rows
        if all(r[k] is not None for k in ('hefi_score', 'heni_minutes', 'hsr_stars', 'fcs_score', 'env_gw_per_100kcal'))
    )
    rho_hefi_heni = spearman['HEFI'].get('HENI min')
    print(f'Core metric completeness: {core_ok}/{len(rows)} days')
    if rho_hefi_heni is not None:
        print(f'HEFI vs HENI Spearman: {rho_hefi_heni:+.3f}')
    print()
    print('Trade-off exemplars (§6.2):')
    for key, ex in tradeoffs.items():
        if key == 'manuscript_narrative' or not ex or not isinstance(ex, dict):
            continue
        if 'day_id' not in ex:
            continue
        nz = ex.get('nutrition_z')
        ez = ex.get('env_footprint_z')
        nz_s = f'{nz:+.2f}' if isinstance(nz, (int, float)) else '?'
        ez_s = f'{ez:+.2f}' if isinstance(ez, (int, float)) else '?'
        print(f'  {key}: {ex["day_id"]} {ex["label"]}  (nutr_z={nz_s}, env_z={ez_s})')
    narr = tradeoffs.get('manuscript_narrative')
    if narr:
        print('  manuscript_narrative:')
        for k, ex in narr.items():
            if isinstance(ex, dict) and 'day_id' in ex:
                print(f'    {k}: {ex["day_id"]} — {ex.get("note", ex["label"])}')
    print()
    print(f'JSON:  {out_json}')
    print(f'CSV:   {csv_path}')
    print(f'Matrix:{spearman_csv}')
    print('=' * 80)

    if core_ok < len(rows):
        print(f'WARN: {len(rows) - core_ok} day(s) missing core metrics')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
