"""Recipe-decomposer validation benchmark — stratified live-LLM accuracy harness.

Reproducible accuracy benchmark of the CNF recipe decomposer
(`cnf_recipe_decomposer.CNFRecipeDecomposer`) against a stratified sample of CNF
COMPOSITE foods (the dishes that actually need decomposing). For each food it decomposes
the dish at a 100 g reference and scores the result on 4 independent ground-truth lenses:

  1. Nutrient reconstruction (primary) — recompute the dish's per-100 g nutrients from the
     decomposed ingredients and compare to the dish's OWN measured CNF nutrients.
  2. FPED food-group cosine vs the dish's FPED twin (`decomposition_plausibility`).
  3. Structural gates — matched flag, mass closure, confidence, ingredient count.
  4. FNDDS authoritative-recipe comparison — food-group rollup cosine vs USDA's real
     recipe (input_food.csv), for composites bridged at >= 0.7.

Per-food verdict (reproducible heuristics):
  pass       = matched AND kcal_rel_error <= 0.20 AND macro_mean_abs_rel_error <= 0.25
               AND (fped_cosine >= 0.80 OR no twin)
  flagged    = matched=False OR kcal_rel_error > 0.40 OR macro_mean_abs_rel_error > 0.60
               OR (fped_cosine is not None AND fped_cosine < 0.60)
  borderline = anything in between
  no_truth   = the dish has no nutrient profile (excluded from pass/flag rates)

Outputs (in backend/):
  - decomposer_benchmark_<git-rev>_<utc>.json        — full per-food benchmark
  - decomposer_benchmark_flagged_for_review.md       — worst rows for human spot-check

Cost: ~$0.0003/food (gpt-4.1-mini, temp 0; embeddings cached) → < ~$0.15 for ~240 foods.
Run: python _smoke_decomposer_benchmark.py [--per-group 30] [--seed 42] [--limit N] [--workers 6]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_BACKEND, '.env'))
except Exception:
    pass

os.environ.setdefault('DJANGO_SECRET_KEY', 'decomposer-benchmark')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

# CNF composite groups that genuinely need decomposition (mirrors the environmental
# decomposer's _COMPOSITE_FOOD_GROUPS).
_COMPOSITE_GROUPS = frozenset({
    'Mixed Dishes',
    'Soups, Sauces and Gravies',
    'Fast Foods',
    'Baked Products',
    'Sweets',
    'Snacks',
    'Sausages and Luncheon meats',
    'Babyfoods',
})

_APPROX_COST_PER_FOOD_USD = 0.0003  # rough; decomposer doesn't expose token usage


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


def _stratified_composite_sample(n_per_group: int, seed: int) -> List[Tuple[int, str, str]]:
    """Stratified random sample across the CNF composite food groups."""
    from api.cnf_cache import get_api_cnf_pipeline
    pipe = get_api_cnf_pipeline()
    fn = pipe.food_name_df
    fg = pipe.food_group_df
    name_by_id = dict(zip(fg['FoodGroupID'], fg['FoodGroupName']))
    sample: List[Tuple[int, str, str]] = []
    for gid, gname in name_by_id.items():
        if gname not in _COMPOSITE_GROUPS:
            continue
        sub = fn[fn['FoodGroupID'] == gid]
        if len(sub) == 0:
            continue
        for _, row in sub.sample(min(n_per_group, len(sub)), random_state=seed).iterrows():
            sample.append((int(row['FoodID']), str(row['FoodDescription']), gname))
    return sample


def _classify(matched: bool, kcal_err: Optional[float], macro_err: Optional[float],
              fped_cos: Optional[float]) -> str:
    if not matched:
        return 'flagged'
    if kcal_err is None and macro_err is None:
        return 'no_truth'
    bad_kcal = kcal_err is not None and kcal_err > 0.40
    bad_macro = macro_err is not None and macro_err > 0.60
    bad_fped = fped_cos is not None and fped_cos < 0.60
    if bad_kcal or bad_macro or bad_fped:
        return 'flagged'
    good_kcal = kcal_err is not None and kcal_err <= 0.20
    good_macro = macro_err is not None and macro_err <= 0.25
    good_fped = fped_cos is None or fped_cos >= 0.80
    if good_kcal and good_macro and good_fped:
        return 'pass'
    return 'borderline'


def _eval_one(food_id: int, cnf_name: str, cnf_group: str,
              force_decompose: bool = False) -> Dict[str, Any]:
    from api.services.cnf_recipe_decomposer import get_default_decomposer
    from api.services.decomposition_validation import (
        nutrient_reconstruction, fndds_recipe_comparison,
    )
    from api.services.fped_aggregator import decomposition_plausibility

    t0 = time.time()
    decomposer = get_default_decomposer()
    try:
        recipe = decomposer.decompose(cnf_name, 100.0, force_decompose=force_decompose)
    except Exception as exc:  # noqa: BLE001
        return {
            'food_id': food_id, 'cnf_name': cnf_name, 'cnf_group': cnf_group,
            'matched': False, 'error': str(exc)[:200],
            'automated_verdict': 'flagged', 'latency_seconds': round(time.time() - t0, 2),
        }
    ings = [{'food_id': i.food_id, 'mass_g': i.mass_g} for i in recipe.ingredients]

    nutr = nutrient_reconstruction(food_id, ings, total_mass_g=100.0) if ings else None
    fped = decomposition_plausibility(food_id, ings) if ings else None
    fndds = fndds_recipe_comparison(food_id, ings) if ings else None

    kcal_err = nutr['kcal_rel_error'] if nutr else None
    macro_err = nutr['macro_mean_abs_rel_error'] if nutr else None
    fped_cos = fped['cosine'] if fped else None
    verdict = _classify(recipe.matched, kcal_err, macro_err, fped_cos)

    return {
        'food_id': food_id, 'cnf_name': cnf_name, 'cnf_group': cnf_group,
        'matched': recipe.matched,
        'fallback_reason': recipe.fallback_reason,
        'n_ingredients': len(ings),
        'decomposition_confidence': recipe.decomposition_confidence,
        'resolved_mass_g': round(recipe.resolved_mass_g, 1),
        'unresolved_mass_g': round(recipe.unresolved_mass_g, 1),
        # lens 1
        'kcal_rel_error': kcal_err,
        'macro_mean_abs_rel_error': macro_err,
        'panel_mean_abs_rel_error': (nutr['panel_mean_abs_rel_error'] if nutr else None),
        'resolved_mass_fraction': (nutr['resolved_mass_fraction'] if nutr else None),
        'nutrients': (nutr['nutrients'] if nutr else None),
        # lens 2
        'fped_cosine': fped_cos,
        'fped_plausible': (fped['plausible'] if fped else None),
        # lens 4
        'fndds_cosine': (fndds['fped_rollup_cosine'] if fndds else None),
        'fndds_dominant_agree': (fndds['dominant_group_agree'] if fndds else None),
        'fndds_n_ingredients': (fndds['fndds_n_ingredients'] if fndds else None),
        'automated_verdict': verdict,
        'cache_hit': recipe.cache_hit,
        'latency_seconds': round(time.time() - t0, 2),
    }


def _pct(values: List[float], p: float) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    return round(s[min(len(s) - 1, max(0, int(p * len(s))))], 3)


def _bootstrap_ci(flags: List[int], rng: random.Random, b: int = 1000, alpha: float = 0.05):
    n = len(flags)
    if n == 0:
        return None
    obs = sum(flags) / n
    boot = sorted(sum(flags[rng.randrange(n)] for _ in range(n)) / n for _ in range(b))
    return {'n': n, 'observed': round(obs, 3),
            'ci_lo': round(boot[int((alpha / 2) * b)], 3),
            'ci_hi': round(boot[int((1 - alpha / 2) * b) - 1], 3)}


def _aggregate(rows: List[Dict[str, Any]], seed: int) -> Dict[str, Any]:
    rng = random.Random(seed)
    verdicts = [r['automated_verdict'] for r in rows]
    scored = [r for r in rows if r['automated_verdict'] != 'no_truth']
    n_scored = max(1, len(scored))
    overall = {v: verdicts.count(v) for v in ('pass', 'borderline', 'flagged', 'no_truth')}
    overall['total'] = len(rows)
    overall['matched_rate'] = round(sum(1 for r in rows if r['matched']) / max(1, len(rows)), 3)
    overall['pass_rate_of_scored'] = round(verdicts.count('pass') / n_scored, 3)
    overall['flagged_rate_of_scored'] = round(verdicts.count('flagged') / n_scored, 3)
    n_catalog = sum(1 for r in rows if str(r.get('fallback_reason') or '').startswith('catalog_'))
    overall['catalog_hit_rate'] = round(n_catalog / max(1, len(rows)), 3)

    by_group: Dict[str, Dict[str, Any]] = {}
    for g in sorted(set(r['cnf_group'] for r in rows)):
        grows = [r for r in rows if r['cnf_group'] == g]
        gv = [r['automated_verdict'] for r in grows]
        flags = [1 if r['automated_verdict'] == 'flagged' else 0 for r in grows
                 if r['automated_verdict'] != 'no_truth']
        by_group[g] = {
            'n': len(grows),
            'pass': gv.count('pass'), 'borderline': gv.count('borderline'),
            'flagged': gv.count('flagged'), 'no_truth': gv.count('no_truth'),
            'matched_rate': round(sum(1 for r in grows if r['matched']) / max(1, len(grows)), 3),
            'flagged_ci_95': _bootstrap_ci(flags, rng),
        }

    def _collect(key):
        return [r[key] for r in rows if r.get(key) is not None]
    kcal = _collect('kcal_rel_error')
    macro = _collect('macro_mean_abs_rel_error')
    fped = _collect('fped_cosine')
    fndds = _collect('fndds_cosine')
    lat = _collect('latency_seconds')
    conf = _collect('decomposition_confidence')
    return {
        'overall': overall,
        'by_group': by_group,
        'distributions': {
            'kcal_rel_error': {'median': _pct(kcal, 0.5), 'p90': _pct(kcal, 0.9), 'n': len(kcal)},
            'macro_mean_abs_rel_error': {'median': _pct(macro, 0.5), 'p90': _pct(macro, 0.9), 'n': len(macro)},
            'fped_cosine': {'median': _pct(fped, 0.5), 'p10': _pct(fped, 0.1), 'n': len(fped)},
            'fndds_cosine': {'median': _pct(fndds, 0.5), 'p10': _pct(fndds, 0.1), 'n': len(fndds)},
            'decomposition_confidence': {'median': _pct(conf, 0.5), 'min': (min(conf) if conf else None),
                                         'max': (max(conf) if conf else None), 'distinct': len(set(conf))},
        },
        'latency_seconds': {'p50': _pct(lat, 0.5), 'p90': _pct(lat, 0.9),
                            'p99': _pct(lat, 0.99), 'mean': (round(statistics.mean(lat), 2) if lat else None)},
        'approx_cost_usd': round(len(rows) * _APPROX_COST_PER_FOOD_USD, 4),
    }


def run_benchmark(per_group: int, seed: int, limit: Optional[int], workers: int,
                  force_decompose: bool = False) -> Dict[str, Any]:
    sample = _stratified_composite_sample(per_group, seed)
    random.seed(seed)
    random.shuffle(sample)
    if limit:
        sample = sample[:limit]
    mode = 'force-decompose' if force_decompose else 'full-pipeline'
    print(f'Sampled {len(sample)} composite foods across '
          f'{len(set(g for _, _, g in sample))} groups (per_group={per_group}, seed={seed}, mode={mode})')

    rows: List[Dict[str, Any]] = []
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(_eval_one, fid, name, grp, force_decompose): fid
                for fid, name, grp in sample}
        for fut in as_completed(futs):
            rows.append(fut.result())
            done += 1
            if done % 20 == 0:
                print(f'  ... {done}/{len(sample)}', flush=True)
    rows.sort(key=lambda r: (r['cnf_group'], r['food_id']))
    return {
        'git_rev': _git_rev_short(),
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'seed': seed, 'per_group': per_group, 'sample_size': len(rows),
        'mode': mode, 'force_decompose': bool(force_decompose),
        'summary': _aggregate(rows, seed),
        'per_food': rows,
    }


def _write_artefacts(bench: Dict[str, Any]) -> Tuple[str, str]:
    stamp = _utc_stamp()
    suffix = '_forcedecomp' if bench.get('force_decompose') else ''
    json_path = os.path.join(_BACKEND, f'decomposer_benchmark_{bench["git_rev"]}{suffix}_{stamp}.json')
    md_path = os.path.join(_BACKEND, f'decomposer_benchmark_flagged_for_review{suffix}.md')
    with open(json_path, 'wb') as fh:
        fh.write((json.dumps(bench, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

    flagged = [r for r in bench['per_food'] if r['automated_verdict'] == 'flagged']
    flagged.sort(key=lambda r: -(r.get('kcal_rel_error') or 0))
    lines = [f'# Decomposer benchmark — flagged-for-review rows', '',
             f'- Benchmark JSON: `decomposer_benchmark_{bench["git_rev"]}_{stamp}.json`',
             f'- Sample: {bench["sample_size"]} composite foods; flagged: {len(flagged)}', '']
    for r in flagged:
        lines.append(f'### food_id={r["food_id"]} — {r["cnf_name"]}  ({r["cnf_group"]})')
        lines.append(f'- matched=`{r["matched"]}` fallback=`{r.get("fallback_reason")}` '
                     f'n_ing={r.get("n_ingredients")} conf={r.get("decomposition_confidence")}')
        lines.append(f'- kcal_err={r.get("kcal_rel_error")} macro_err={r.get("macro_mean_abs_rel_error")} '
                     f'fped_cos={r.get("fped_cosine")} fndds_cos={r.get("fndds_cosine")}')
        lines.append('')
    with open(md_path, 'wb') as fh:
        fh.write(('\n'.join(lines) + '\n').encode('utf-8'))
    return json_path, md_path


def _print_summary(bench: Dict[str, Any]) -> None:
    s = bench['summary']
    o = s['overall']
    print('\n' + '=' * 78)
    print(f'DECOMPOSER BENCHMARK — {bench["sample_size"]} composite foods '
          f'(git {bench["git_rev"]}, mode={bench.get("mode", "full-pipeline")})')
    print('=' * 78)
    print(f'matched: {o["matched_rate"]*100:.0f}%   catalog-hit: {o.get("catalog_hit_rate", 0)*100:.0f}%   '
          f'pass: {o["pass"]} / borderline: {o["borderline"]} / flagged: {o["flagged"]} '
          f'/ no_truth: {o["no_truth"]}')
    print(f'pass-rate (of scored): {o["pass_rate_of_scored"]*100:.0f}%   '
          f'flagged-rate (of scored): {o["flagged_rate_of_scored"]*100:.0f}%')
    d = s['distributions']
    print(f'kcal_rel_error  median={d["kcal_rel_error"]["median"]}  p90={d["kcal_rel_error"]["p90"]}')
    print(f'macro_err       median={d["macro_mean_abs_rel_error"]["median"]}  p90={d["macro_mean_abs_rel_error"]["p90"]}')
    print(f'fped_cosine     median={d["fped_cosine"]["median"]}  p10={d["fped_cosine"]["p10"]}  (n={d["fped_cosine"]["n"]})')
    print(f'fndds_cosine    median={d["fndds_cosine"]["median"]}  p10={d["fndds_cosine"]["p10"]}  (n={d["fndds_cosine"]["n"]})')
    print(f'confidence      median={d["decomposition_confidence"]["median"]}  distinct={d["decomposition_confidence"]["distinct"]}')
    print(f'approx cost: ${s["approx_cost_usd"]:.4f}   latency p50={s["latency_seconds"]["p50"]}s p99={s["latency_seconds"]["p99"]}s')
    print('\nBy CNF group (flagged-rate 95% CI):')
    for g, gb in sorted(s['by_group'].items(), key=lambda kv: -(kv[1]['flagged_ci_95'] or {}).get('observed', 0)):
        ci = gb['flagged_ci_95'] or {}
        print(f'  {g:32s} n={gb["n"]:3d}  pass={gb["pass"]:3d} flag={gb["flagged"]:3d}  '
              f'matched={gb["matched_rate"]*100:3.0f}%  flagged={ci.get("observed",0)*100:3.0f}% '
              f'[{ci.get("ci_lo",0)*100:.0f}-{ci.get("ci_hi",0)*100:.0f}%]')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--per-group', type=int, default=30)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--limit', type=int, default=None)
    p.add_argument('--workers', type=int, default=6)
    p.add_argument('--force-decompose', action='store_true',
                   help='Bypass catalog preference + override; measure raw decomposition quality.')
    args = p.parse_args()
    if not os.environ.get('OPENAI_API_KEY'):
        print('OPENAI_API_KEY not set; aborting.')
        return 1
    bench = run_benchmark(args.per_group, args.seed, args.limit, args.workers,
                          force_decompose=args.force_decompose)
    json_path, md_path = _write_artefacts(bench)
    _print_summary(bench)
    print(f'\nWrote {os.path.basename(json_path)} + {os.path.basename(md_path)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
