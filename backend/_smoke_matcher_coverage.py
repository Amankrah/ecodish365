"""Tier β coverage smoke — Jaccard token-overlap regression bound.

CALIBRATION CAVEAT: Jaccard token overlap is a *lower bound* on retrieval
quality, not a proxy for it. The production matcher uses OpenAI
text-embedding-3-small (semantic embedding) + LLM ranking. Semantic
retrieval handles food-state stripping ("Squash, frozen, unprepared" →
match "Squash") and cross-lingual matching ("Yogourt fruit" → "Yaourt aux
fruits") well; Jaccard cannot — it rewards literal token overlap, so
stripping state tokens REMOVES overlap opportunities even when the
canonicalisation is correct.

Use this smoke for:
  (a) NO-REGRESSION gate: median Jaccard must not collapse by > 50% from
      baseline (caught: subgroup-routing bug that nukes pool to < 50 entries).
  (b) Per-group profiling: which CNF groups have NO close v32 entries even
      under the most generous scoring — those are Tier γ recipe-decomposition
      candidates.

Do NOT use this smoke to measure the absolute value of Tier β semantic
retrieval improvements. That requires an OpenAI key + a full e2e run.

Baseline (raw CNF descriptions vs. v32 entries, full catalogue):
  median Jaccard:        0.18
  >= 0.40 (clean match):  8 / 184  ( 4%)
  0.20-0.40 (weak):      75 / 184  (41%)
  <  0.20 (poor):       101 / 184  (55%)

Tier β (with `_canonicalize_food_state` + `_agribalyse_subgroup_for_cnf`):
  median Jaccard drops slightly under the proxy (~0.16) because state tokens
  that randomly overlap with v32 ingredient names are removed. Real semantic
  retrieval gain is NOT captured by this proxy.

Usage:
  python _smoke_matcher_coverage.py             # baseline run
  python _smoke_matcher_coverage.py --canonical  # apply Tier β canonicalisation
  python _smoke_matcher_coverage.py --before-after  # both, with delta
"""
from __future__ import annotations

import argparse
import os
import random
import statistics
import sys

# Django setup for CNF integrator
_BACKEND = os.path.dirname(os.path.abspath(__file__))
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    p = os.path.join(_BACKEND, sub)
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()

from environmental_impact_model.src.cnf_integrator import get_cnf_integrator  # noqa: E402
from environmental_impact_model.src.lca_matcher import (  # noqa: E402
    AgribalyseIndex,
    _canonicalize_food_state,
    _agribalyse_subgroup_for_cnf,
)


def _tokens(s: str) -> set:
    return set(s.lower().replace(',', ' ').replace('-', ' ').split())


def _stratified_cnf_sample(n_per_group: int = 8, seed: int = 42):
    """Stratified random sample: n_per_group foods per CNF FoodGroup."""
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


def _measure_jaccard(sample, idx: AgribalyseIndex, canonicalise: bool) -> dict:
    """Return Jaccard-overlap distribution and per-group medians."""
    cat = idx.catalog
    by_group: dict[str, list[float]] = {}
    all_jac: list[float] = []
    misses = []
    for food_id, desc, gname in sample:
        # Tier β step 1: apply canonicalisation if requested.
        if canonicalise:
            base_name, _state_tag = _canonicalize_food_state(desc)
            query = base_name or desc
        else:
            query = desc
        # Tier β step 2: subgroup-routing-aware pool selection.
        agri_filter = _agribalyse_subgroup_for_cnf(gname) if canonicalise else None
        pool = [e for e in cat if (agri_filter is None or e.get('agribalyse_group') == agri_filter)]
        # Fallback to full pool if subgroup filter would yield <50 candidates
        # (matches retriever behaviour: don't starve the search).
        if len(pool) < 50:
            pool = cat
        food_toks = _tokens(query)
        best = 0.0
        best_e = None
        for e in pool:
            et = _tokens((e.get('lci_name') or '') + ' ' + (e.get('lci_name_fr') or ''))
            if not et:
                continue
            j = len(food_toks & et) / max(1, len(food_toks | et))
            if j > best:
                best, best_e = j, e
        all_jac.append(best)
        by_group.setdefault(gname, []).append(best)
        if best < 0.20:
            misses.append((desc, best, (best_e or {}).get('lci_name')))
    return {
        'jaccards': all_jac,
        'by_group': by_group,
        'misses': misses,
    }


def _print_report(label: str, m: dict) -> None:
    vals = m['jaccards']
    n = len(vals)
    print(f'\n=== {label} (n={n}) ===')
    print(f'  median:               {statistics.median(vals):.3f}')
    print(f'  >= 0.40 (clean):       {sum(1 for v in vals if v >= 0.40):3d}/{n} ({100 * sum(1 for v in vals if v >= 0.40) / n:.0f}%)')
    print(f'  0.20 - 0.40 (weak):    {sum(1 for v in vals if 0.20 <= v < 0.40):3d}/{n} ({100 * sum(1 for v in vals if 0.20 <= v < 0.40) / n:.0f}%)')
    print(f'  <  0.20 (poor):        {sum(1 for v in vals if v < 0.20):3d}/{n} ({100 * sum(1 for v in vals if v < 0.20) / n:.0f}%)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--canonical', action='store_true',
                        help='Apply Tier β canonicalisation (state-strip + subgroup routing).')
    parser.add_argument('--before-after', action='store_true',
                        help='Run both modes and print the delta.')
    parser.add_argument('--n-per-group', type=int, default=8)
    args = parser.parse_args()

    print('Loading CNF + Agribalyse v32...')
    sample = _stratified_cnf_sample(n_per_group=args.n_per_group)
    idx = AgribalyseIndex()
    print(f'Sample: {len(sample)} CNF foods across {len(set(g for _, _, g in sample))} groups')
    print(f'v32 catalog: {len(idx.catalog)} entries')

    if args.before_after:
        baseline = _measure_jaccard(sample, idx, canonicalise=False)
        tier_b   = _measure_jaccard(sample, idx, canonicalise=True)
        _print_report('BASELINE (raw description, no subgroup routing)', baseline)
        _print_report('TIER β (canonicalised + subgroup-routed)', tier_b)
        # Delta
        b_med = statistics.median(baseline['jaccards'])
        t_med = statistics.median(tier_b['jaccards'])
        print(f'\nMedian Jaccard delta:       {t_med - b_med:+.3f}  (baseline {b_med:.3f} -> tier_b {t_med:.3f})')
        # Gate
        threshold_median = 0.30
        threshold_poor_share = 0.30
        poor_share_b = sum(1 for v in baseline['jaccards'] if v < 0.20) / len(baseline['jaccards'])
        poor_share_t = sum(1 for v in tier_b['jaccards']   if v < 0.20) / len(tier_b['jaccards'])
        print(f'Poor-overlap share:         baseline {poor_share_b:.0%} -> tier_b {poor_share_t:.0%}')
        # Print best-improvement cases (where Tier β fixed the worst baseline misses)
        miss_baseline = {d: j for d, j, _ in baseline['misses']}
        improved = []
        for d, j_b in miss_baseline.items():
            # find this desc in tier_b results
            for d2, j2, _ in tier_b.get('misses', []):
                if d == d2:
                    if j2 > j_b + 0.05:
                        improved.append((d, j_b, j2))
                    break
        if improved:
            print('\nSample improvements (top 5):')
            for d, jb, jt in sorted(improved, key=lambda x: -(x[2] - x[1]))[:5]:
                print(f'  [{jb:.2f} -> {jt:.2f}] {d[:70]}')

        # No-regression gate: Jaccard median must not drop by >50% (catches
        # bugs like pool-starvation in subgroup routing). The proxy cannot
        # measure semantic-retrieval improvement; that requires an OpenAI key.
        gate_pass = (t_med >= b_med * 0.5)
        print(f'\nNo-regression gate: tier_b median ({t_med:.3f}) >= 0.5 × baseline ({b_med * 0.5:.3f})  =>  '
              f'{"PASS" if gate_pass else "FAIL — investigate canonicalisation/routing"}')
        print('NOTE: This proxy cannot measure semantic-retrieval gain. The production matcher')
        print('      uses OpenAI text-embedding-3-small which captures the canonicalisation benefit.')
        sys.exit(0 if gate_pass else 1)
    else:
        m = _measure_jaccard(sample, idx, canonicalise=args.canonical)
        _print_report('TIER β' if args.canonical else 'BASELINE', m)
        sys.exit(0)


if __name__ == '__main__':
    main()
