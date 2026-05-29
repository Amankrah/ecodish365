"""Compound-meal lab — end-to-end decomposer validation on curated free-text dishes.

The CNF benchmark (`_smoke_decomposer_benchmark.py`) samples exact CNF food *names*,
which self-match and never exercise realistic free-text dishes. This lab fills that
gap: 20 curated compound/single meals (`_decomposer_lab_scenarios.json`) run through
the FULL `decompose()` pipeline — catalog preference (short-circuit + reconstruction-
gated override) and the compound-meal gate all active — and each is scored on:

  - compound-gate detection vs the expected tag (`_is_compound_meal`);
  - survival of the `must_keep` components (e.g. the beverage in "... and a coke");
  - plausible per-100 g energy density (catches soup over/under-count);
  - which path fired (decompose / catalog_short_circuit / catalog_override) vs expected;
  - the catalog match's food_type, and a hard check that NO dish was collapsed onto a
    SINGLE-ingredient catalog food (the regression the food-type gate prevents);
  - the recipe's dish_as_ingredient_count (Stage-1 handing back dishes, not ingredients).

Verdict per scenario:
  flagged = a must_keep component was dropped, OR the dish was collapsed onto a single
            ingredient, OR the compound-gate tag disagreed (all deterministic).
  review  = energy density out of band OR the path differed from expectation (soft —
            depends on LLM proportions + catalog matching; for a human to eyeball).
  pass    = none of the above.

Outputs (in backend/):
  - decomposer_lab_<git-rev>_<utc>.json     — full per-scenario record
  - decomposer_lab_review.md                — flagged + review rows for human judgment

Cost: 20 dishes x full pipeline (decompose + per-ingredient matching) ~= a few cents.
Run: python _smoke_decomposer_lab.py [--workers 5] [--scenarios path.json]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_BACKEND, '.env'))
except Exception:
    pass

os.environ.setdefault('DJANGO_SECRET_KEY', 'decomposer-lab')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

_SCENARIOS_PATH = os.path.join(_BACKEND, '_decomposer_lab_scenarios.json')


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')


def _git_rev_short() -> str:
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL, cwd=os.path.dirname(_BACKEND),
        ).decode('ascii').strip()
    except Exception:
        return 'unknown'


def _behavior(recipe) -> str:
    """Which decompose() path produced this recipe, from its fallback_reason."""
    fr = recipe.fallback_reason or ''
    if fr.startswith('catalog_direct_match'):
        return 'catalog_short_circuit'
    if fr.startswith('catalog_override'):
        return 'catalog_override'
    return 'decompose' if recipe.matched else 'failed'


def _energy_density_kcal_100g(recipe) -> Optional[float]:
    """Mass-weighted kcal per 100 g of the dish (target mass as denominator, so any
    unresolved residual is treated as 0-kcal — matching what the scorers see)."""
    from api.cnf_cache import get_api_cnf_pipeline
    pipe = get_api_cnf_pipeline()
    denom = recipe.total_mass_g or sum(i.mass_g for i in recipe.ingredients)
    if not denom or denom <= 0:
        return None
    kcal = 0.0
    for i in recipe.ingredients:
        try:
            n = pipe.nutrients_for(int(i.food_id)) or {}
        except Exception:  # noqa: BLE001
            n = {}
        kcal += float(n.get('ENERGY (KILOCALORIES)', 0.0) or 0.0) * i.mass_g / 100.0
    return round(kcal / denom * 100.0, 1)


def _component_survives(any_of: List[str], ingredients) -> bool:
    needles = [s.lower() for s in any_of]
    for ing in ingredients:
        hay = f'{ing.food_description} {ing.food_group}'.lower()
        if any(n in hay for n in needles):
            return True
    return False


def _eval_scenario(sc: Dict[str, Any]) -> Dict[str, Any]:
    from api.services.cnf_recipe_decomposer import get_default_decomposer, _is_compound_meal

    dish = sc['dish']
    total_mass = float(sc['total_mass_g'])
    t0 = time.time()
    decomposer = get_default_decomposer()
    try:
        recipe = decomposer.decompose(dish, total_mass)  # full pipeline (no force_decompose)
    except Exception as exc:  # noqa: BLE001
        return {
            'dish': dish, 'total_mass_g': total_mass, 'error': str(exc)[:200],
            'verdict': 'flagged', 'flag_reasons': ['decompose_exception'],
            'latency_seconds': round(time.time() - t0, 2),
        }

    ings = recipe.ingredients
    compound_detected = bool(_is_compound_meal(dish))
    behavior = _behavior(recipe)
    energy = _energy_density_kcal_100g(recipe)

    # must_keep survival
    kept, dropped = [], []
    for mk in sc.get('must_keep', []):
        (kept if _component_survives(mk['any_of'], ings) else dropped).append(mk['label'])

    # collapsed-onto-single: the regression the food-type gate exists to prevent.
    is_catalog = behavior in ('catalog_short_circuit', 'catalog_override')
    collapsed_food_type = (ings[0].food_type if (is_catalog and len(ings) == 1) else None)
    collapsed_onto_single = bool(is_catalog and len(ings) == 1
                                 and ings[0].food_type == 'single')

    band = sc.get('energy_density_kcal_100g')
    energy_in_band = (band is None or energy is None
                      or (band[0] <= energy <= band[1]))

    # --- Verdict -------------------------------------------------------
    flag_reasons: List[str] = []
    review_reasons: List[str] = []
    if dropped:
        flag_reasons.append(f'must_keep_dropped:{",".join(dropped)}')
    if collapsed_onto_single:
        flag_reasons.append(
            f'collapsed_onto_single_ingredient:{ings[0].food_id}:{ings[0].food_description}')
    if compound_detected != bool(sc.get('compound', False)):
        flag_reasons.append(
            f'compound_gate_mismatch:detected={compound_detected},expected={sc.get("compound")}')
    if not recipe.matched:
        review_reasons.append(f'unmatched:{recipe.fallback_reason}')
    if not energy_in_band:
        review_reasons.append(
            f'energy_density_out_of_band:{energy}_not_in_{band}')
    if sc.get('expect_behavior') and behavior != sc['expect_behavior']:
        review_reasons.append(f'behavior:{behavior}_expected_{sc["expect_behavior"]}')

    verdict = 'flagged' if flag_reasons else ('review' if review_reasons else 'pass')

    return {
        'dish': dish,
        'total_mass_g': total_mass,
        'verdict': verdict,
        'flag_reasons': flag_reasons,
        'review_reasons': review_reasons,
        'matched': recipe.matched,
        'fallback_reason': recipe.fallback_reason,
        'behavior': behavior,
        'expect_behavior': sc.get('expect_behavior'),
        'compound_detected': compound_detected,
        'compound_expected': bool(sc.get('compound', False)),
        'n_ingredients': len(ings),
        'decomposition_confidence': recipe.decomposition_confidence,
        'resolved_mass_g': round(recipe.resolved_mass_g, 1),
        'unresolved_mass_g': round(recipe.unresolved_mass_g, 1),
        'unresolved_description': recipe.unresolved_description,
        'dish_as_ingredient_count': recipe.dish_as_ingredient_count,
        'energy_density_kcal_100g': energy,
        'energy_density_band': band,
        'energy_in_band': energy_in_band,
        'must_keep_kept': kept,
        'must_keep_dropped': dropped,
        'collapsed_onto_single': collapsed_onto_single,
        'collapsed_food_type': collapsed_food_type,
        'ingredients': [
            {'food_id': i.food_id, 'desc': i.food_description, 'group': i.food_group,
             'mass_g': round(i.mass_g, 1), 'food_type': i.food_type,
             'resolution_confidence': round(i.resolution_confidence, 3)}
            for i in ings
        ],
        'note': sc.get('note', ''),
        'cache_hit': recipe.cache_hit,
        'latency_seconds': round(time.time() - t0, 2),
    }


def run_lab(scenarios: List[Dict[str, Any]], workers: int) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_eval_scenario, sc): sc['dish'] for sc in scenarios}
        for fut in as_completed(futs):
            rows.append(fut.result())
    order = {sc['dish']: idx for idx, sc in enumerate(scenarios)}
    rows.sort(key=lambda r: order.get(r['dish'], 999))

    verdicts = [r['verdict'] for r in rows]
    summary = {
        'total': len(rows),
        'pass': verdicts.count('pass'),
        'review': verdicts.count('review'),
        'flagged': verdicts.count('flagged'),
        'matched_rate': round(sum(1 for r in rows if r.get('matched')) / max(1, len(rows)), 3),
        'compound_gate_correct': sum(
            1 for r in rows if r.get('compound_detected') == r.get('compound_expected')),
        'must_keep_all_survived': sum(1 for r in rows if not r.get('must_keep_dropped')),
        'collapsed_onto_single': sum(1 for r in rows if r.get('collapsed_onto_single')),
    }
    return {
        'git_rev': _git_rev_short(),
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'sample_size': len(rows),
        'summary': summary,
        'per_scenario': rows,
    }


def _write_artefacts(lab: Dict[str, Any]) -> str:
    stamp = _utc_stamp()
    json_path = os.path.join(_BACKEND, f'decomposer_lab_{lab["git_rev"]}_{stamp}.json')
    md_path = os.path.join(_BACKEND, 'decomposer_lab_review.md')
    with open(json_path, 'wb') as fh:
        fh.write((json.dumps(lab, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

    s = lab['summary']
    lines = [
        '# Decomposer compound-meal lab — review',
        '',
        f'- Lab JSON: `decomposer_lab_{lab["git_rev"]}_{stamp}.json`',
        f'- Scenarios: {s["total"]}  |  pass: {s["pass"]}  review: {s["review"]}  flagged: {s["flagged"]}',
        f'- compound-gate correct: {s["compound_gate_correct"]}/{s["total"]}  |  '
        f'must_keep all survived: {s["must_keep_all_survived"]}/{s["total"]}  |  '
        f'collapsed-onto-single: {s["collapsed_onto_single"]}',
        '',
    ]
    for tag in ('flagged', 'review'):
        rows = [r for r in lab['per_scenario'] if r['verdict'] == tag]
        if not rows:
            continue
        lines.append(f'## {tag.upper()} ({len(rows)})')
        lines.append('')
        for r in rows:
            lines.append(f'### {r["dish"]}  — `{r["verdict"]}`')
            reasons = (r.get('flag_reasons') or []) + (r.get('review_reasons') or [])
            lines.append(f'- reasons: {reasons}')
            lines.append(f'- behavior=`{r.get("behavior")}` (expected `{r.get("expect_behavior")}`) '
                         f'matched=`{r.get("matched")}` fallback=`{r.get("fallback_reason")}` '
                         f'conf={r.get("decomposition_confidence")}')
            lines.append(f'- energy={r.get("energy_density_kcal_100g")} kcal/100g '
                         f'(band {r.get("energy_density_band")}) in_band={r.get("energy_in_band")}')
            lines.append(f'- kept={r.get("must_keep_kept")} dropped={r.get("must_keep_dropped")} '
                         f'dish_as_ingredient={r.get("dish_as_ingredient_count")}')
            ings = ', '.join(f'{i["desc"]}({i["mass_g"]}g,{i["food_type"]})'
                             for i in r.get('ingredients', []))
            lines.append(f'- ingredients: {ings}')
            if r.get('note'):
                lines.append(f'- note: {r["note"]}')
            lines.append('')
    with open(md_path, 'wb') as fh:
        fh.write(('\n'.join(lines) + '\n').encode('utf-8'))
    return json_path


def _print_summary(lab: Dict[str, Any]) -> None:
    s = lab['summary']
    print('\n' + '=' * 78)
    print(f'DECOMPOSER COMPOUND-MEAL LAB — {s["total"]} scenarios (git {lab["git_rev"]})')
    print('=' * 78)
    print(f'pass: {s["pass"]}   review: {s["review"]}   flagged: {s["flagged"]}   '
          f'matched: {s["matched_rate"]*100:.0f}%')
    print(f'compound-gate correct: {s["compound_gate_correct"]}/{s["total"]}   '
          f'must_keep all survived: {s["must_keep_all_survived"]}/{s["total"]}   '
          f'collapsed-onto-single: {s["collapsed_onto_single"]}')
    print('-' * 78)
    for r in lab['per_scenario']:
        mark = {'pass': 'PASS', 'review': 'REVW', 'flagged': 'FLAG'}[r['verdict']]
        print(f'[{mark}] {r["dish"][:42]:42s} {r.get("behavior",""):20s} '
              f'{str(r.get("energy_density_kcal_100g","")):>7}kcal  n={r.get("n_ingredients","")}')
        for reason in (r.get('flag_reasons') or []) + (r.get('review_reasons') or []):
            print(f'        - {reason}')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--workers', type=int, default=5)
    p.add_argument('--scenarios', type=str, default=_SCENARIOS_PATH)
    args = p.parse_args()
    if not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY not set; aborting.')
        return 1
    with open(args.scenarios, encoding='utf-8') as fh:
        scenarios = json.load(fh)['scenarios']
    print(f'Running {len(scenarios)} compound-meal scenarios through the full pipeline '
          f'(workers={args.workers})...')
    lab = run_lab(scenarios, args.workers)
    json_path = _write_artefacts(lab)
    _print_summary(lab)
    print(f'\nWrote {os.path.basename(json_path)} + decomposer_lab_review.md')
    # Non-zero exit if any hard flags, so CI / the user notices regressions.
    return 1 if lab['summary']['flagged'] else 0


if __name__ == '__main__':
    sys.exit(main())
