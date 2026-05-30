"""NHANES 2017-2018 day-1 individual food file -> per-DAY CNF pool.

Phase 1 of Scenario S4 (NHANES proxy for the unavailable 2015 CCHS-Nutrition
RDC microdata). Loads NHANES DR1IFF_J (day-1 24-h recall, 112 683 food line
rows) and DEMO_J (9 254 respondents with age, sex, family income-to-poverty
ratio), maps every FNDDS food code in the recall to a CNF FoodID via the
existing CNF -> FNDDS bridge inverted in memory, aggregates food lines per
SEQN (full-day recall, concatenating all meal occasions) into one record
per respondent, and writes the resulting NHANES-derived DAY pool to JSON.

We aggregate to full-day records because the manuscript's Brassard 2022b
reproduction gate (national HEFI-2019 mean 43.1 / 80) is a usual-intake
DAY-LEVEL population statistic. A per-occasion panel cannot be fairly
compared to that reference, so the medoid input pool is per-day.

The output `nhanes_2017_day_pool.json` is the cluster input for the
Phase 2 stratified k-medoids sampler that selects 100 medoid days across
the (age-sex group x FIPR quintile) strata.

Run from `backend/`:
    python -m api.services.etl.build_nhanes_2017_meal_pool

Inputs:
    raw_nhanes/DR1IFF_J.xpt
    raw_nhanes/DEMO_J.xpt
    heni_calculator/data/cnf_to_fndds_bridge.json

Output:
    api/data/nhanes_2017_meal_pool.json
"""
from __future__ import annotations

import json
import logging
import os
import sys
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

_HERE = os.path.abspath(os.path.dirname(__file__))
_BACKEND = os.path.abspath(os.path.join(_HERE, '..', '..', '..'))
_RAW = os.path.join(_BACKEND, 'raw_nhanes')
_BRIDGE_PATH = os.path.join(_BACKEND, 'heni_calculator', 'data',
                            'cnf_to_fndds_bridge.json')
_OUT_PATH = os.path.join(_BACKEND, 'api', 'data',
                         'nhanes_2017_day_pool.json')


# NHANES 2017-2018 DR1_030Z meal occasion codebook (numeric value in file
# -> English collapsed bucket for S4 stratification).
# Per https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DR1IFF_J.htm value labels:
# 1 Breakfast / 10 Desayuno -> breakfast
# 2 Brunch / 3 Lunch / 11 Almuerzo / 12 Comida -> lunch
# 4 Dinner / 5 Supper / 14 Cena -> dinner
# 6 Snack / 7 Drink / 13 Merienda / 15-19 Spanish snacks/drinks -> snack
# 8 Infant feeding / 9 Don't know / 99 Other -> dropped
_OCCASION_BUCKET = {
    1.0: 'breakfast', 10.0: 'breakfast',
    2.0: 'lunch', 3.0: 'lunch', 11.0: 'lunch', 12.0: 'lunch',
    4.0: 'dinner', 5.0: 'dinner', 14.0: 'dinner',
    6.0: 'snack', 7.0: 'snack', 13.0: 'snack',
    15.0: 'snack', 16.0: 'snack', 17.0: 'snack',
    18.0: 'snack', 19.0: 'snack',
}

# FIPR quintile bins (NHANES INDFMPIR is on a 0..5 scale; CDC convention
# truncates at 5). Five equal-width bins on the truncated range.
_FIPR_BIN_EDGES = [-0.001, 1.0, 2.0, 3.0, 4.0, 5.001]
_FIPR_QUINTILE_LABELS = [1, 2, 3, 4, 5]


def _age_band(age_years: float) -> str:
    """Brassard 2022b stratification: 2-18 y / males >=19 / females >=19.
    Sex is read separately; this returns the age bucket only.
    """
    if age_years < 2 or pd.isna(age_years):
        return 'drop'
    if age_years < 19:
        return 'youth_2_18'
    return 'adult_19plus'


def _fipr_quintile(fipr: float) -> Optional[int]:
    if pd.isna(fipr):
        return None
    for i, hi in enumerate(_FIPR_BIN_EDGES[1:], start=1):
        if fipr <= hi:
            return _FIPR_QUINTILE_LABELS[i - 1]
    return _FIPR_QUINTILE_LABELS[-1]


def _invert_bridge(bridge_path: str) -> Tuple[Dict[int, int], Dict[str, int]]:
    """Invert the CNF -> FNDDS bridge into FNDDS food_code -> CNF FoodID.

    Many CNF foods may map to the same FNDDS food_code (the bridge is a
    soft mapping with confidence scores). We resolve collisions by keeping
    the CNF whose bridge confidence is highest. Returns (inverted_map,
    diagnostics_counter).
    """
    with open(bridge_path, 'r', encoding='utf-8') as f:
        bridge = json.load(f)
    forward = bridge.get('bridges', {})
    inverted: Dict[int, Tuple[int, float]] = {}
    diag = Counter()
    for cnf_id_str, entry in forward.items():
        try:
            cnf_id = int(cnf_id_str)
            food_code = int(entry['food_code'])
            confidence = float(entry.get('confidence', 0.0))
        except (TypeError, ValueError, KeyError):
            diag['parse_skip'] += 1
            continue
        # Only keep CNF IDs that are loadable by every scoring endpoint:
        # standard CNF (1 .. 7021) and WAFCT (700000+). The 500000-501999
        # range covers FNDDS-derived synthesised IDs that exist in the
        # bridge but not in the CNF integrator's food table, so swapping
        # them into a meal would produce a 404 from the API.
        if not (1 <= cnf_id <= 7021 or cnf_id >= 700000):
            diag['cnf_id_unloadable_skipped'] += 1
            continue
        existing = inverted.get(food_code)
        if existing is None or confidence > existing[1]:
            inverted[food_code] = (cnf_id, confidence)
            if existing is not None:
                diag['collision_resolved_to_higher_conf'] += 1
        else:
            diag['collision_kept_existing'] += 1
    final = {fc: cnf_id for fc, (cnf_id, _conf) in inverted.items()}
    diag['n_fndds_codes_covered'] = len(final)
    diag['n_cnf_in_bridge'] = len(forward)
    return final, diag


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s')
    logger.info('Loading CNF -> FNDDS bridge from %s', _BRIDGE_PATH)
    fndds_to_cnf, bridge_diag = _invert_bridge(_BRIDGE_PATH)
    logger.info('Inverted bridge: %s', dict(bridge_diag))

    logger.info('Reading DEMO_J.xpt')
    demo = pd.read_sas(os.path.join(_RAW, 'DEMO_J.xpt'), format='xport')
    demo = demo[['SEQN', 'RIAGENDR', 'RIDAGEYR', 'INDFMPIR']].copy()
    demo['SEQN'] = demo['SEQN'].astype(int)
    demo['sex'] = demo['RIAGENDR'].map({1.0: 'M', 2.0: 'F'})
    demo['age_band'] = demo['RIDAGEYR'].apply(_age_band)
    demo['fipr_quintile'] = demo['INDFMPIR'].apply(_fipr_quintile)
    demo_map = demo.set_index('SEQN').to_dict('index')
    logger.info('DEMO_J: %d respondents', len(demo))

    logger.info('Reading DR1IFF_J.xpt (this takes ~15 s for 112k rows)')
    dr = pd.read_sas(os.path.join(_RAW, 'DR1IFF_J.xpt'), format='xport')
    keep_cols = ['SEQN', 'DR1IFDCD', 'DR1IGRMS', 'DR1_030Z',
                 'DR1IKCAL', 'DR1IPROT', 'DR1ICARB', 'DR1ISUGR',
                 'DR1IFIBE', 'DR1ITFAT', 'DR1ISFAT', 'DR1ISODI']
    dr = dr[keep_cols].copy()
    dr['SEQN'] = dr['SEQN'].astype(int)
    dr['fndds_code'] = dr['DR1IFDCD'].fillna(0).astype(int)
    dr['mass_g'] = dr['DR1IGRMS'].astype(float)
    dr['occasion'] = dr['DR1_030Z'].map(_OCCASION_BUCKET)
    logger.info('DR1IFF_J: %d food line rows', len(dr))

    # Counters for the diagnostics block
    diag = Counter()
    diag['food_lines_total'] = len(dr)

    # Filter out non-bucketed occasions (infant feeding, refused, etc.)
    n_pre_occ = len(dr)
    dr = dr.dropna(subset=['occasion'])
    diag['food_lines_after_occasion_filter'] = len(dr)
    diag['food_lines_dropped_non_bucketed_occasion'] = n_pre_occ - len(dr)

    # Map FNDDS -> CNF. We track unmatched lines BEFORE dropping so the
    # per-meal mass-coverage filter below can reject meals where too
    # much of the recall mass is unmappable.
    n_pre_match = len(dr)
    dr['cnf_food_id'] = dr['fndds_code'].map(fndds_to_cnf)
    n_unmatched = dr['cnf_food_id'].isna().sum()
    diag['food_lines_unmatched_fndds'] = int(n_unmatched)
    diag['food_lines_matched'] = int(n_pre_match - n_unmatched)
    diag['fndds_codes_unique_in_recall'] = int(dr['fndds_code'].nunique())
    diag['fndds_codes_unmatched_unique'] = int(
        dr.loc[dr['cnf_food_id'].isna(), 'fndds_code'].nunique()
    )
    # Per-DAY mass coverage = matched mass / total recall mass (across all
    # occasions for one respondent's day-1 recall).
    dr['matched_mass'] = dr['mass_g'].where(dr['cnf_food_id'].notna(), 0.0)
    mass_coverage = dr.groupby('SEQN').apply(
        lambda g: g['matched_mass'].sum() / max(1e-9, g['mass_g'].sum()),
        include_groups=False,
    ).rename('mass_coverage').reset_index()
    dr = dr.merge(mass_coverage, on='SEQN', how='left')
    dr = dr.dropna(subset=['cnf_food_id'])
    dr['cnf_food_id'] = dr['cnf_food_id'].astype(int)

    # Aggregate to per-day records (one row per SEQN, concatenating all
    # bucketed occasions). Per-day reproduces Brassard 2022b's day-level
    # population reference and is the medoid input.
    logger.info('Aggregating to per-day records...')
    meals: List[Dict] = []
    grouped = dr.groupby('SEQN')
    for seqn, grp in grouped:
        occ = None  # per-day, no single occasion label
        demo_row = demo_map.get(seqn)
        if not demo_row:
            diag['days_dropped_no_demo'] += 1
            continue
        if demo_row['age_band'] == 'drop':
            diag['days_dropped_age_under_2'] += 1
            continue
        sex = demo_row['sex']
        if not isinstance(sex, str):
            diag['days_dropped_no_sex'] += 1
            continue
        if demo_row['age_band'] == 'adult_19plus':
            agesex = f'{"males" if sex == "M" else "females"}_19plus'
        else:
            agesex = 'youth_2_18'
        fipr_q = demo_row['fipr_quintile']
        if fipr_q is None or (isinstance(fipr_q, float) and pd.isna(fipr_q)):
            diag['days_dropped_no_fipr'] += 1
            continue
        kcal_total = float(grp['DR1IKCAL'].fillna(0).sum())
        # Day-level kcal floor: drop respondents whose full-day recall is
        # below 500 kcal (likely incomplete or invalid recalls per NHANES
        # documentation guidance).
        if kcal_total < 500.0:
            diag['days_dropped_kcal_under_500'] += 1
            continue
        mc = float(grp['mass_coverage'].iloc[0]) if 'mass_coverage' in grp.columns else 1.0
        if mc < 0.7:
            diag['days_dropped_mass_coverage_under_70'] += 1
            continue
        # Compose a meal-occasion mix descriptor for diagnostics.
        occ_counts = Counter(grp['occasion'].dropna())
        occ_mix = '+'.join(f'{o}{n}' for o, n in occ_counts.most_common())
        foods = [
            {
                'cnf_food_id': int(r['cnf_food_id']),
                'mass_g': round(float(r['mass_g']), 2),
                'fndds_food_code': int(r['fndds_code']),
            }
            for _, r in grp.iterrows()
            if r['mass_g'] and r['mass_g'] > 0.0
        ]
        if len(foods) == 0:
            diag['days_dropped_no_foods'] += 1
            continue
        meal_macros = {
            'kcal': kcal_total,
            'protein_g': float(grp['DR1IPROT'].fillna(0).sum()),
            'carb_g': float(grp['DR1ICARB'].fillna(0).sum()),
            'sugar_g': float(grp['DR1ISUGR'].fillna(0).sum()),
            'fibre_g': float(grp['DR1IFIBE'].fillna(0).sum()),
            'fat_g': float(grp['DR1ITFAT'].fillna(0).sum()),
            'sat_fat_g': float(grp['DR1ISFAT'].fillna(0).sum()),
            'sodium_mg': float(grp['DR1ISODI'].fillna(0).sum()),
        }
        meals.append({
            'day_id': f'NH-{int(seqn)}',
            'seqn': int(seqn),
            'agesex_group': agesex,
            'age_years': float(demo_row['RIDAGEYR']),
            'sex': sex,
            'fipr_quintile': int(fipr_q),
            'occasion_mix': occ_mix,
            'mass_coverage': round(mc, 3),
            'foods': foods,
            'macros_nhanes_self_reported': meal_macros,
        })
        diag['days_kept'] += 1

    logger.info('Meal pool diagnostics: %s', dict(diag))
    logger.info('Final meal pool: %d meals', len(meals))

    # Stratum cell sizes (day-level: age-sex group x FIPR quintile)
    stratum_counts = Counter(
        (m['agesex_group'], m['fipr_quintile']) for m in meals
    )
    cell_sizes_summary = sorted(stratum_counts.items(),
                                key=lambda kv: kv[1], reverse=True)
    logger.info('Stratum cells (agesex x FIPR): %s', cell_sizes_summary)

    out = {
        '_provenance': {
            'source': 'NHANES 2017-2018 What We Eat In America',
            'inputs': {
                'individual_foods': 'raw_nhanes/DR1IFF_J.xpt',
                'demographics': 'raw_nhanes/DEMO_J.xpt',
                'cnf_fndds_bridge': 'heni_calculator/data/cnf_to_fndds_bridge.json',
            },
            'occasion_bucketing_for_diagnostics': _OCCASION_BUCKET,
            'fipr_bin_edges': _FIPR_BIN_EDGES,
            'kcal_floor_per_day': 500.0,
            'unit': 'per-DAY records, each with a list of (cnf_food_id, mass_g) '
                    'foods aggregated across the respondent\'s day-1 24-h recall',
        },
        'diagnostics': dict(diag),
        'bridge_diagnostics': dict(bridge_diag),
        'stratum_cell_sizes': {
            f'{ag}|q{q}': n for (ag, q), n in cell_sizes_summary
        },
        'n_days': len(meals),
        'days': meals,
    }
    os.makedirs(os.path.dirname(_OUT_PATH), exist_ok=True)
    with open(_OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out, f, indent=2)
    logger.info('Wrote %s', _OUT_PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
