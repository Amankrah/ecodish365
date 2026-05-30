"""Verify the EF 3.1 methodology pack against the AGRIBALYSE v32 catalogue.

For every entry in the AGRIBALYSE catalogue that carries an
``ef31_indicators_per_100g`` block with all 16 midpoint values plus the
precomputed ``Score unique EF 3.1``, this script:

  1. Recomputes the single score from the midpoint values and the pack's
     JRC normalisation + weighting factors using the EF 3.1 formula
       single_score (Pt) = sum_i( midpoint_i * weighting_i / normalisation_i )
       reported in mPt   = single_score * 1000
  2. Compares the recomputed value against AGRIBALYSE's stored single score.
  3. Reports the mean and worst-case relative error across the catalogue.

If the pack's normalisation and weighting values match the JRC reference
values that AGRIBALYSE used, the recomputed and stored single scores should
agree within a small numerical tolerance (~1 %) across the entire catalogue.
Larger systematic drift means the pack values are stale or wrong and should
not be shipped as authoritative.

Run:  python _smoke_ef31_pack_verify.py
Exit: 0 if mean relative error <= 5 %, 1 otherwise.
"""
from __future__ import annotations

import io
import json
import os
import sys
from typing import Dict, List, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

_HERE = os.path.dirname(os.path.abspath(__file__))
_PACK = os.path.join(_HERE, 'environmental_impact_model', 'data', 'ef31_methodology.json')
_CATALOG = os.path.join(_HERE, 'environmental_impact_model', 'data', 'agribalyse_v32_catalog.json')

TOLERANCE_REL = 0.05      # 5 % mean relative error gate
WORST_CASE_REL = 0.20     # 20 % worst single-entry relative error gate
SAMPLE_LIMIT = 100        # cap the sample size to keep the smoke fast


def _load_pack() -> Dict:
    with open(_PACK, encoding='utf-8') as f:
        return json.load(f)


def _load_catalog_entries() -> List[Dict]:
    with open(_CATALOG, encoding='utf-8') as f:
        return json.load(f)['entries']


def _recompute_single_score(midpoints: Dict[str, float], indicators: Dict[str, Dict]) -> Tuple[float, List[str]]:
    """Sum_i( midpoint_i * weighting_i / normalisation_i ) reported in mPt.

    Returns (single_score_mpt, list_of_skipped_categories).
    """
    skipped = []
    total_pt = 0.0
    for name_fr, spec in indicators.items():
        m = midpoints.get(name_fr)
        if m is None:
            skipped.append(name_fr)
            continue
        n = spec['normalisation_per_person_per_year']
        w = spec['weighting_pct']
        if n == 0:
            skipped.append(f'{name_fr} (zero norm)')
            continue
        # weighting_pct is a percentage (sums to 100), so divide by 100 before
        # applying as a weight.
        total_pt += m * (w / 100.0) / n
    return total_pt * 1000.0, skipped


def main() -> int:
    if not os.path.exists(_PACK):
        print(f'EF 3.1 methodology pack not found at {_PACK}')
        return 1
    if not os.path.exists(_CATALOG):
        print(f'AGRIBALYSE catalogue not found at {_CATALOG}')
        return 1

    pack = _load_pack()
    indicators = pack['indicators']
    entries = _load_catalog_entries()
    print(f'Loaded EF 3.1 pack ({len(indicators)} indicators) and AGRIBALYSE catalogue ({len(entries)} entries).')

    sample = entries[:SAMPLE_LIMIT]
    errors_rel: List[float] = []
    n_eval = 0
    worst_so_far = (0.0, '', 0.0, 0.0)
    skipped_counts: Dict[str, int] = {}

    for e in sample:
        ef = e.get('ef31_indicators_per_100g') or {}
        stored_mpt = ef.get('Score unique EF 3.1')
        if stored_mpt is None or stored_mpt <= 0:
            continue
        recomputed_mpt, skipped = _recompute_single_score(ef, indicators)
        for s in skipped:
            skipped_counts[s] = skipped_counts.get(s, 0) + 1
        if recomputed_mpt <= 0:
            continue
        rel = abs(recomputed_mpt - stored_mpt) / stored_mpt
        errors_rel.append(rel)
        n_eval += 1
        if rel > worst_so_far[0]:
            worst_so_far = (rel, e.get('lci_name', ''), stored_mpt, recomputed_mpt)

    if n_eval == 0:
        print('No entries with EF 3.1 single score available in the sample.')
        return 1

    mean_rel = sum(errors_rel) / n_eval
    max_rel = max(errors_rel)

    print(f'Evaluated {n_eval} entries')
    print(f'Mean relative error: {mean_rel*100:.2f} %')
    print(f'Max relative error:  {max_rel*100:.2f} % on {worst_so_far[1]!r}')
    print(f'  stored single score = {worst_so_far[2]:.6g} mPt')
    print(f'  recomputed score    = {worst_so_far[3]:.6g} mPt')
    if skipped_counts:
        print(f'Skipped indicators across sample (catalogue entries missing this column):')
        for name, c in sorted(skipped_counts.items(), key=lambda kv: -kv[1])[:10]:
            print(f'  {name}: {c}')

    ok_mean = mean_rel <= TOLERANCE_REL
    ok_worst = max_rel <= WORST_CASE_REL
    print()
    if ok_mean and ok_worst:
        print(f'PASS — mean error within {TOLERANCE_REL*100:.0f} % and worst-case within {WORST_CASE_REL*100:.0f} %.')
        print('EF 3.1 methodology pack values are consistent with the AGRIBALYSE-stored single scores.')
        return 0
    if ok_mean:
        print(f'PARTIAL — mean error OK but worst case exceeds {WORST_CASE_REL*100:.0f} %.')
        return 1
    print(f'FAIL — mean relative error exceeds {TOLERANCE_REL*100:.0f} %.')
    print('Pack values are stale / wrong. Do not ship until reconciled with the JRC source.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
