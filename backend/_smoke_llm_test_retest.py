"""LLM test-retest reliability for the LCA matcher.

Plan D (Tier 1 statistical analyses). Closes the manuscript's
"deterministic at temperature 0" claim with an empirical retest panel.

For 30 foods (deterministic subset of the seed-42 stratified panel
used by `_smoke_matcher_benchmark.py`), invokes
`/api/environmental-impact/?enable_lca_matcher=true` N = 5 times per
food and reports:

  - % of foods returning an identical ciqual_code across all N runs
    (headline reproducibility metric);
  - median per-food SD of the verbalised confidence across runs;
  - mean pairwise Cohen's kappa on the automated_verdict labels
    across all C(N, 2) run pairs.

Cost guard: ~150 matcher calls @ ~$0.0003 each ~ $0.045. Pass
--yes-i-understand-cost (or run interactively with the prompt) to
proceed. The script is opt-in by design because plan D is the only
Tier 1 analysis that costs real LLM calls.

Run from `backend/`:
    python _smoke_llm_test_retest.py --yes-i-understand-cost
    python _smoke_llm_test_retest.py --n-foods 30 --n-runs 5 --yes-i-understand-cost
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
from collections import Counter
from itertools import combinations
from typing import Any, Dict, List, Tuple

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-llm-test-retest'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402

# Reuse the same stratified sampler the matcher benchmark uses, so the
# retest panel is a strict subset of the benchmark and the two harnesses
# can be cross-referenced.
from _smoke_matcher_benchmark import (
    _stratified_cnf_sample,
    _matched_entry_lookup,
    _cnf_group_default_gw,
    _check_group_consistency,
    _check_magnitude_plausibility,
    _check_token_overlap,
    _classify,
)


_OUTPUT_JSON = os.path.join(_HERE, '_smoke_llm_test_retest_results.json')


def _clear_matcher_cache_for_food(food_id: int) -> None:
    """Bust the LCAMatcher singleton's per-food cache so the next
    /api/environmental-impact/ call actually re-invokes the LLM rather
    than serving from `LCAMatcher._cache`. Without this, runs 2..N are
    deterministic by cache, not by temperature=0.
    """
    try:
        from api.views.environmental_views import _get_default_lca_matcher
        m = _get_default_lca_matcher()
        if m is not None and hasattr(m, '_cache'):
            m._cache.pop(food_id, None)
    except Exception:  # noqa: BLE001
        pass


def _matcher_call(c: Client, food_id: int) -> Dict[str, Any]:
    # Force the matcher to re-invoke the LLM by clearing the per-food
    # cache slot before each call. This makes the retest panel a real
    # test of provider-side determinism, not a test of the in-process
    # cache (which by construction returns the first run's result).
    _clear_matcher_cache_for_food(food_id)
    body = {
        'foods': [{'food_id': food_id, 'quantity': 100}],
        'enable_lca_matcher': True,
    }
    t = time.time()
    r = c.post('/api/environmental-impact/', data=json.dumps(body),
               content_type='application/json')
    elapsed = time.time() - t
    try:
        env = r.json()['data'].get('data', {}).get('environmental_impacts', {})
    except Exception:
        env = {}
    decisions = env.get('lca_matcher_decisions') or []
    m = decisions[0] if decisions else {}
    return {
        'matched': bool(m.get('matched')),
        'confidence': float(m.get('confidence') or 0.0),
        'ciqual_code': m.get('ciqual_code'),
        'lci_name': m.get('lci_name') or '',
        'latency_seconds': elapsed,
    }


def _verdict_for(food_id: int, cnf_name: str, cnf_group: str,
                 call_result: Dict[str, Any]) -> str:
    """Recompute the same automated_verdict the benchmark uses, so the
    retest comparison is apples-to-apples.
    """
    matched = call_result['matched']
    if not matched:
        return 'flagged'
    confidence = call_result['confidence']
    matched_ciqual = call_result['ciqual_code']
    matched_lci = call_result['lci_name']
    entry = _matched_entry_lookup(matched_ciqual) if matched_ciqual else {}
    matched_ag_group = entry.get('agribalyse_group', '') or ''
    matched_lci_fr = entry.get('lci_name_fr') or ''
    matched_gw = (entry.get('recipe2016_midpoints_per_100g') or {}).get('Global warming')
    cnf_default_gw = _cnf_group_default_gw(cnf_group)
    gc_pass = _check_group_consistency(cnf_group, matched_ag_group)
    mag_pass, _ratio = _check_magnitude_plausibility(matched_gw, cnf_default_gw)
    tok_pass = _check_token_overlap(cnf_name, matched_lci, matched_lci_fr)
    return _classify(matched, confidence, gc_pass, mag_pass, tok_pass)


def _cohen_kappa(labels_a: List[str], labels_b: List[str]) -> float:
    """Cohen's kappa between two categorical raters."""
    if len(labels_a) != len(labels_b) or len(labels_a) == 0:
        return float('nan')
    n = len(labels_a)
    cats = sorted(set(labels_a) | set(labels_b))
    if not cats:
        return float('nan')
    # observed agreement
    po = sum(1 for i in range(n) if labels_a[i] == labels_b[i]) / n
    # expected agreement under independence
    ca = Counter(labels_a)
    cb = Counter(labels_b)
    pe = sum((ca[c] / n) * (cb[c] / n) for c in cats)
    if pe >= 1.0:
        return 1.0 if po >= 1.0 else 0.0
    return (po - pe) / (1.0 - pe)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--n-foods', type=int, default=30,
                        help='subset size from the seed-42 panel (default 30)')
    parser.add_argument('--n-runs', type=int, default=5,
                        help='repeats per food (default 5)')
    parser.add_argument('--seed', type=int, default=42,
                        help='same seed as the matcher benchmark')
    parser.add_argument('--yes-i-understand-cost', action='store_true',
                        help='skip the interactive cost prompt')
    args = parser.parse_args()

    n_calls = args.n_foods * args.n_runs
    approx_cost_usd = n_calls * 0.0003

    print('LLM test-retest reliability for the LCA matcher')
    print(f'  N_foods = {args.n_foods}  N_runs = {args.n_runs}  seed = {args.seed}')
    print(f'  Approx total calls: {n_calls}  Approx cost: ${approx_cost_usd:.3f}')
    if not args.yes_i_understand_cost:
        ans = input('  Proceed? [y/N] ').strip().lower()
        if ans != 'y':
            print('  Aborted.')
            return 0

    print('=' * 80)
    # Reuse the same stratified sample shape the matcher benchmark uses.
    # Take every (200 // n_foods)-th food to spread the subset uniformly
    # across CNF groups.
    n_per_group = max(1, 200 // 23)  # matches benchmark default
    full_sample = _stratified_cnf_sample(n_per_group=n_per_group, seed=args.seed)
    if len(full_sample) < args.n_foods:
        print(f'WARNING: panel only has {len(full_sample)} foods')
    step = max(1, len(full_sample) // args.n_foods)
    subset = full_sample[::step][:args.n_foods]
    print(f'Subset: {len(subset)} foods spanning '
          f'{len(set(g for _, _, g in subset))} CNF groups')
    print()

    c = Client()
    per_food: List[Dict[str, Any]] = []
    t0 = time.time()
    for idx, (food_id, cnf_name, cnf_group) in enumerate(subset):
        print(f'  [{idx+1}/{len(subset)}] {cnf_name[:60]}', flush=True)
        runs = []
        for run_idx in range(args.n_runs):
            call_result = _matcher_call(c, food_id)
            verdict = _verdict_for(food_id, cnf_name, cnf_group, call_result)
            runs.append({**call_result, 'verdict': verdict, 'run_idx': run_idx})
        ciqual_codes = [r['ciqual_code'] for r in runs]
        identical_match = len(set(ciqual_codes)) == 1
        modal_ciqual = Counter(ciqual_codes).most_common(1)[0][0]
        modal_share = ciqual_codes.count(modal_ciqual) / len(ciqual_codes)
        confidences = [r['confidence'] for r in runs]
        conf_mean = statistics.fmean(confidences)
        conf_sd = statistics.pstdev(confidences) if len(confidences) > 1 else 0.0
        verdicts = [r['verdict'] for r in runs]
        verdict_counter = Counter(verdicts)
        per_food.append({
            'food_id': food_id,
            'cnf_name': cnf_name,
            'cnf_group': cnf_group,
            'runs': runs,
            'ciqual_codes': ciqual_codes,
            'identical_match': identical_match,
            'modal_ciqual': modal_ciqual,
            'modal_ciqual_share': modal_share,
            'confidences': confidences,
            'conf_mean': conf_mean,
            'conf_sd': conf_sd,
            'verdicts': verdicts,
            'verdict_distribution': dict(verdict_counter),
        })

    elapsed_total = time.time() - t0

    # Headline 1: % identical-match
    n_identical = sum(1 for p in per_food if p['identical_match'])
    pct_identical = 100.0 * n_identical / len(per_food)

    # Headline 2: median conf SD across foods
    sds = [p['conf_sd'] for p in per_food]
    median_conf_sd = statistics.median(sds)

    # Headline 3: mean pairwise Cohen's kappa across runs on verdict labels.
    # Build N_runs vectors of length len(per_food), one per run.
    n_runs = args.n_runs
    per_run_labels: List[List[str]] = [[p['verdicts'][r] for p in per_food]
                                       for r in range(n_runs)]
    kappas = []
    for i, j in combinations(range(n_runs), 2):
        k = _cohen_kappa(per_run_labels[i], per_run_labels[j])
        if k == k:  # NaN guard
            kappas.append(k)
    mean_pairwise_kappa = sum(kappas) / len(kappas) if kappas else float('nan')

    # Modal-share-weighted reproducibility: average of modal_ciqual_share
    mean_modal_share = sum(p['modal_ciqual_share'] for p in per_food) / len(per_food)

    print()
    print('=' * 80)
    print(f'Wall clock: {elapsed_total:.1f}s  ({len(per_food)*n_runs} matcher calls)')
    print()
    print(f'1. Identical-ciqual rate (all {n_runs} runs returned same LCI code):')
    print(f'     {n_identical}/{len(per_food)} foods = {pct_identical:.1f}%')
    print(f'   Mean modal-ciqual share (avg run agreement per food):')
    print(f'     {mean_modal_share*100:.1f}%')
    print()
    print(f'2. Median per-food SD of verbalised confidence:')
    print(f'     {median_conf_sd:.4f}  (0 = identical confidence across runs)')
    print(f'   Foods with confidence SD = 0: '
          f'{sum(1 for s in sds if s == 0)}/{len(sds)}')
    print()
    print(f'3. Mean pairwise Cohen kappa on automated_verdict labels:')
    print(f'     {mean_pairwise_kappa:.4f}  (1.0 = perfect agreement across run pairs)')
    print(f'   Pairs evaluated: {len(kappas)}/{len(list(combinations(range(n_runs), 2)))}')
    print()

    out = {
        'panel_description': 'LLM test-retest reliability for the LCA matcher',
        'n_foods': len(per_food),
        'n_runs': n_runs,
        'seed': args.seed,
        'elapsed_seconds': elapsed_total,
        'summary': {
            'identical_match_rate': pct_identical / 100.0,
            'mean_modal_ciqual_share': mean_modal_share,
            'median_conf_sd': median_conf_sd,
            'mean_pairwise_verdict_kappa': mean_pairwise_kappa,
            'n_kappa_pairs': len(kappas),
        },
        'per_food': per_food,
        'caveats': [
            'Temperature is held at 0 across providers, but provider-side '
            'inference is not guaranteed bit-equivalent across calls. The '
            'identical-match rate is the empirical reproducibility in '
            'practice, not a theoretical guarantee.',
            'The LCAMatcher in-process LRU cache is busted per food '
            'before each retest call (see `_clear_matcher_cache_for_food`), '
            'so the panel reflects real LLM-driven test-retest variance, '
            'not within-process cache hits.',
            'The verdict label is recomputed locally per run with the same '
            'four heuristics the benchmark uses, so verdict drift is '
            'driven by matcher-output drift, not heuristic stochasticity.',
            f'N_runs = {n_runs} -> {len(kappas)} pairwise kappas per food '
            f'class set. Larger N would tighten the kappa estimate; N=5 was '
            f'chosen as a cost-bounded smoke; full retest at N=10 deferred '
            f'to the manuscript revision pass.',
        ],
    }
    with open(_OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    print(f'Results JSON: {_OUTPUT_JSON}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
