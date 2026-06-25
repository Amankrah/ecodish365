"""FDC → CNF nutrient bridge exploration probe (FDC-INGEST, 2026-06-25).

Walks the three on-disk FDC datasets (Foundation, SR Legacy, FNDDS) and
prints:

  1. nutrient.csv inventory per dataset (id, nutrient_nbr, name, unit)
  2. which FDC nutrients bridge to a CNF NutrientID via integer-cast(nutrient_nbr)
  3. which FDC nutrients DON'T bridge (and how many food_nutrient rows we'd
     drop in v1 if we ingest only the bridged subset)
  4. unit-mismatch flags (CNF unit vs FDC unit_name for bridged pairs)

Run:

    cd backend && python _explore_fdc_nutrient_bridge.py

Output writes both stdout summary and a JSON artefact at
`backend/_explore_fdc_nutrient_bridge_results.json` for later reference.
"""
from __future__ import annotations

import csv
import json
import os
from collections import defaultdict, Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parent

FDC_FOUNDATION = BACKEND / 'raw_fdc_foundation' / 'FoodData_Central_foundation_food_csv_2026-04-30'
FDC_SR_LEGACY  = BACKEND / 'raw_fdc_sr_legacy'  / 'FoodData_Central_sr_legacy_food_csv_2018-04'
FDC_FNDDS      = BACKEND / 'raw_fndds'          / 'FoodData_Central_survey_food_csv_2024-10-31'
CNF_NUTRIENT_NAME = BACKEND / 'raw_cnf' / 'NUTRIENT_NAME.csv'

# Unit aliases: FDC unit_name → CNF NutrientUnit. CNF uses long forms
# ("Gram", "kilocalorie") where FDC uses short codes ("G", "KCAL"). This
# map only contains the unit codes we expect to see for bridged nutrients;
# unbridged FDC-only codes (PH, SP_GR, UMOL_TE, MG_GAE, MCG_RE) will simply
# show up in the unit-mismatch report and don't matter because those
# nutrients won't be bridged anyway.
FDC_UNIT_TO_CNF_UNIT = {
    'G':      'Gram',
    'MG':     'Milligram',
    'UG':     'Microgram',
    'KCAL':   'kilocalorie',
    'KJ':     'kilojoule',
    'IU':     'IU',
    'MCG_RE': 'Microgram',     # vitamin A activity RE
    'MG_ATE': 'Milligram',     # vitamin E activity ATE
}


def _read_csv(path: Path) -> list[dict]:
    """Read a CSV into a list of dicts (assumes UTF-8 with double-quoted strings)."""
    with path.open('r', encoding='utf-8', newline='') as fh:
        reader = csv.DictReader(fh)
        return list(reader)


def _load_cnf_nutrient_lookup() -> dict[int, dict]:
    """Return {NutrientID: {Name, Unit, Tagname}} from CNF."""
    out = {}
    # CNF CSV is ISO-8859-1.
    with CNF_NUTRIENT_NAME.open('r', encoding='ISO-8859-1', newline='') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                nid = int(row['NutrientID'])
            except (ValueError, TypeError):
                continue
            out[nid] = {
                'name':    row.get('NutrientName', ''),
                'unit':    row.get('NutrientUnit', ''),
                'tagname': row.get('Tagname', ''),
            }
    return out


def _load_fdc_nutrients(dataset_dir: Path) -> list[dict]:
    """Load nutrient.csv from a single FDC dataset."""
    return _read_csv(dataset_dir / 'nutrient.csv')


def _load_fdc_used_nutrient_ids(dataset_dir: Path) -> Counter[int]:
    """Count how many food_nutrient rows reference each nutrient_id.

    Streams through food_nutrient.csv (can be large) and tallies
    nutrient_id values.
    """
    out: Counter[int] = Counter()
    with (dataset_dir / 'food_nutrient.csv').open('r', encoding='utf-8', newline='') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                nid = int(row['nutrient_id'])
            except (ValueError, TypeError):
                continue
            out[nid] += 1
    return out


def _parse_nutrient_nbr(nbr_str: str) -> tuple[int | None, float | None]:
    """Return (integer_part, raw_float). Integer part is the candidate
    CNF NutrientID when nbr is integer-valued."""
    nbr_str = (nbr_str or '').strip()
    if not nbr_str:
        return None, None
    try:
        f = float(nbr_str)
    except ValueError:
        return None, None
    i = int(f)
    if abs(f - i) < 1e-9:
        return i, f
    return None, f  # subcategory variant (e.g., 269.3, 293.1, 338.1)


def explore() -> dict:
    cnf = _load_cnf_nutrient_lookup()
    cnf_ids = set(cnf.keys())

    datasets = {
        'foundation': FDC_FOUNDATION,
        'sr_legacy':  FDC_SR_LEGACY,
        'fndds':      FDC_FNDDS,
    }

    summary: dict = {
        'cnf_nutrient_count': len(cnf),
        'datasets': {},
    }

    # Are the three FDC nutrient.csv files identical?
    nutrient_signatures = {}
    for name, ddir in datasets.items():
        nuts = _load_fdc_nutrients(ddir)
        sig = sorted((n['id'], n['nutrient_nbr'], n['name'], n['unit_name']) for n in nuts)
        nutrient_signatures[name] = (len(nuts), sig)

    all_identical = (
        nutrient_signatures['foundation'][1]
        == nutrient_signatures['sr_legacy'][1]
        == nutrient_signatures['fndds'][1]
    )
    summary['nutrient_csv_identical_across_datasets'] = all_identical
    summary['nutrient_csv_counts'] = {k: v[0] for k, v in nutrient_signatures.items()}

    # Build the canonical bridge from Foundation (since all three are
    # claimed identical above; we'll cross-check during ingest).
    fdc_nutrients = _load_fdc_nutrients(FDC_FOUNDATION)

    bridged: dict[int, dict] = {}            # FDC id → bridge info
    unbridged_fdc_only: list[dict] = []      # nutrient_nbr is empty or not in CNF
    unbridged_subcategory: list[dict] = []   # nutrient_nbr is non-integer (e.g. 269.3)
    unit_mismatches: list[dict] = []

    for n in fdc_nutrients:
        try:
            fdc_id = int(n['id'])
        except (ValueError, TypeError):
            continue
        int_nbr, float_nbr = _parse_nutrient_nbr(n.get('nutrient_nbr', ''))
        name = n.get('name', '')
        unit = n.get('unit_name', '')

        if int_nbr is None:
            if float_nbr is None:
                unbridged_fdc_only.append({
                    'fdc_id': fdc_id, 'name': name, 'unit': unit,
                    'reason': 'empty_nutrient_nbr',
                })
            else:
                unbridged_subcategory.append({
                    'fdc_id': fdc_id, 'name': name, 'unit': unit,
                    'nutrient_nbr': float_nbr,
                    'reason': 'non_integer_subcategory',
                })
            continue

        if int_nbr not in cnf_ids:
            unbridged_fdc_only.append({
                'fdc_id': fdc_id, 'name': name, 'unit': unit,
                'nutrient_nbr': int_nbr,
                'reason': 'no_cnf_match',
            })
            continue

        # Bridged. Check unit alignment.
        cnf_row = cnf[int_nbr]
        cnf_unit = cnf_row['unit']
        expected_cnf_unit = FDC_UNIT_TO_CNF_UNIT.get(unit, unit)
        unit_ok = (cnf_unit == expected_cnf_unit) or (cnf_unit.lower() == unit.lower())
        if not unit_ok:
            unit_mismatches.append({
                'fdc_id': fdc_id, 'name': name, 'fdc_unit': unit,
                'cnf_nutrient_id': int_nbr, 'cnf_name': cnf_row['name'],
                'cnf_unit': cnf_unit,
            })
        bridged[fdc_id] = {
            'fdc_name': name,
            'fdc_unit': unit,
            'cnf_nutrient_id': int_nbr,
            'cnf_name': cnf_row['name'],
            'cnf_unit': cnf_unit,
            'unit_ok': unit_ok,
        }

    summary['bridge'] = {
        'bridged_count': len(bridged),
        'unbridged_fdc_only_count': len(unbridged_fdc_only),
        'unbridged_subcategory_count': len(unbridged_subcategory),
        'unit_mismatch_count': len(unit_mismatches),
        'unbridged_fdc_only_sample': unbridged_fdc_only[:30],
        'unbridged_subcategory_sample': unbridged_subcategory[:30],
        'unit_mismatches_sample': unit_mismatches[:30],
    }

    # FNDDS food_nutrient.csv uses nutrient_nbr (e.g. 208, 301) as its
    # `nutrient_id`, NOT the FDC id (1001-2069). Foundation and SR Legacy
    # use the FDC id. Build a second resolver keyed by nutrient_nbr so
    # FNDDS lookups still work.
    fdc_id_to_name = {int(n['id']): n['name'] for n in fdc_nutrients}
    nbr_to_cnf_nutrient_id = {}  # nutrient_nbr (int) -> CNF NutrientID
    nbr_to_name = {}             # nutrient_nbr (int) -> FDC name (for display)
    for n in fdc_nutrients:
        int_nbr, _ = _parse_nutrient_nbr(n.get('nutrient_nbr', ''))
        if int_nbr is None:
            continue
        nbr_to_name[int_nbr] = n.get('name', '')
        if int_nbr in cnf_ids:
            nbr_to_cnf_nutrient_id[int_nbr] = int_nbr  # identity

    # Coverage: of all food_nutrient.csv rows, how many reference a
    # bridged nutrient vs an unbridged one? FNDDS uses nutrient_nbr as
    # the FK; Foundation + SR Legacy use the FDC id.
    for name, ddir in datasets.items():
        used = _load_fdc_used_nutrient_ids(ddir)
        used_total = sum(used.values())
        is_fndds = (name == 'fndds')
        if is_fndds:
            # FNDDS path: nutrient_id IS already nutrient_nbr.
            def bridged_lookup(k):
                return k in nbr_to_cnf_nutrient_id
            name_lookup = lambda k: nbr_to_name.get(k, '?')
            key_label = 'nutrient_nbr'
        else:
            def bridged_lookup(k):
                return k in bridged
            name_lookup = lambda k: fdc_id_to_name.get(k, '?')
            key_label = 'fdc_id'

        bridged_rows = sum(c for k, c in used.items() if bridged_lookup(k))
        unbridged_rows = used_total - bridged_rows
        unbridged_top = sorted(
            ((k, c) for k, c in used.items() if not bridged_lookup(k)),
            key=lambda x: -x[1],
        )[:15]
        top_unbridged_hydrated = [
            {key_label: k, 'rows': c, 'name': name_lookup(k)}
            for k, c in unbridged_top
        ]
        summary['datasets'][name] = {
            'fk_system':                 key_label,
            'total_food_nutrient_rows':  used_total,
            'bridged_rows':              bridged_rows,
            'unbridged_rows':            unbridged_rows,
            'bridged_pct':               round(100.0 * bridged_rows / max(used_total, 1), 2),
            'distinct_nutrient_ids_used':       len(used),
            'distinct_bridged_ids_used': sum(1 for k in used if bridged_lookup(k)),
            'top_unbridged_by_row_count':       top_unbridged_hydrated,
        }

    return summary


def main() -> None:
    s = explore()
    out_path = BACKEND / '_explore_fdc_nutrient_bridge_results.json'
    out_path.write_text(json.dumps(s, indent=2, ensure_ascii=False))
    print('=' * 78)
    print('FDC -> CNF Nutrient Bridge Exploration')
    print('=' * 78)
    print(f"CNF total NutrientID count:                       {s['cnf_nutrient_count']}")
    print(f"FDC nutrient.csv identical across 3 datasets:      {s['nutrient_csv_identical_across_datasets']}")
    print(f"FDC nutrient.csv counts:                          {s['nutrient_csv_counts']}")
    print()
    b = s['bridge']
    print(f"Bridged (FDC id -> CNF NutrientID via nutrient_nbr): {b['bridged_count']}")
    print(f"Unbridged: subcategory (non-integer nutrient_nbr):  {b['unbridged_subcategory_count']}")
    print(f"Unbridged: FDC-only / empty / no CNF match:         {b['unbridged_fdc_only_count']}")
    print(f"Unit mismatches among bridged:                     {b['unit_mismatch_count']}")
    print()
    print('Per-dataset food_nutrient row coverage:')
    print('-' * 78)
    print(f"{'dataset':<12} {'total_rows':>12} {'bridged_rows':>14} {'pct':>7} {'distinct_used':>14}")
    for name, d in s['datasets'].items():
        print(
            f"{name:<12} {d['total_food_nutrient_rows']:>12,} "
            f"{d['bridged_rows']:>14,} {d['bridged_pct']:>6}% "
            f"{d['distinct_nutrient_ids_used']:>14}"
        )
    print()
    print('Top 15 unbridged nutrients by row count (per dataset):')
    print('-' * 78)
    for name, d in s['datasets'].items():
        print(f"\n  [{name}]")
        for row in d['top_unbridged_by_row_count']:
            print(f"    fdc_id={row['fdc_id']:>5}  rows={row['rows']:>7,}  {row['name']}")
    print()
    print(f"Full report written to {out_path}")


if __name__ == '__main__':
    main()
