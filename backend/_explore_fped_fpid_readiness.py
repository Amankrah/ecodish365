"""FPED / FPID integration readiness harness (HENI bridge audit, 2026-05-26).

Read-only audit of the USDA Food Patterns raw inputs at backend/raw_fped,
backend/raw_fpid, and backend/raw_fndds, plus the derived bridge + composition
JSON under heni_calculator/data/, and how they connect to the CNF pipeline.

Unlike `_explore_wafct_vs_cnf_per100g.py` (nutrient-database comparison),
FPED/FPID are *food-pattern equivalent* tables used for HENI food-group
attribution — not per-nutrient composition. This harness checks:

  1. Raw file inventory (FPED_1718.xls, FPID_1718.xls, FNDDS bundle)
  2. Key-space alignment (FPED FOODCODE vs FNDDS food_code vs FPID CODE)
  3. Current CNF→FNDDS→FPED bridge coverage (smoke vs full corpus)
  4. FPID ingredient-chain feasibility via FNDDS input_food.sr_code

Outputs:
  `_explore_fped_fpid_readiness_results.json`

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _explore_fped_fpid_readiness.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass

_HERE = Path(__file__).resolve().parent  # backend/
# Raw inputs at backend/raw_* (post-2026-05-27 relocation, matches raw_cnf / raw_wafct).
_FPED = _HERE / 'raw_fped' / 'FPED_1718.xls'
_FPID = _HERE / 'raw_fpid' / 'FPID_1718.xls'
_FNDDS = _HERE / 'raw_fndds' / 'FoodData_Central_survey_food_csv_2024-10-31'
# Derived artifacts stay next to the consuming HENI module.
_DATA = _HERE / 'heni_calculator' / 'data'
_BRIDGE = _DATA / 'cnf_to_fndds_bridge.json'
_COMPOSITION = _DATA / 'cnf_heni_composition.json'
_OUT = _HERE / '_explore_fped_fpid_readiness_results.json'


def main() -> int:
    import pandas as pd

    print('FPED / FPID integration readiness audit')
    print('=' * 72)

    report: Dict[str, Any] = {
        'harness': 'FPED-FPID readiness audit (2026-05-26)',
        'data_paths': {
            'fped': str(_FPED),
            'fpid': str(_FPID),
            'fndds': str(_FNDDS),
            'bridge': str(_BRIDGE),
            'composition': str(_COMPOSITION),
        },
        'recommendations': [],
    }

    # --- Raw inventory ---------------------------------------------------
    for label, path in [('FPED', _FPED), ('FPID', _FPID)]:
        exists = path.exists()
        size_kb = round(path.stat().st_size / 1024, 1) if exists else 0
        report[f'{label.lower()}_file'] = {'exists': exists, 'size_kb': size_kb}
        print(f'\n{label}: {"OK" if exists else "MISSING"} ({size_kb} KB)')

    fndds_ok = _FNDDS.is_dir() and (_FNDDS / 'food.csv').exists()
    report['fndds_bundle'] = {'exists': fndds_ok, 'path': str(_FNDDS)}
    print(f'FNDDS bundle: {"OK" if fndds_ok else "MISSING"}')

    if not all([_FPED.exists(), _FPID.exists(), fndds_ok]):
        print('\nAbort: required files missing.')
        return 1

    fped = pd.read_excel(_FPED, sheet_name='FPED_1718')
    fpid = pd.read_excel(_FPID, sheet_name='FPID_1718')
    sf = pd.read_csv(_FNDDS / 'survey_fndds_food.csv', dtype={'food_code': 'int64'})
    inp = pd.read_csv(_FNDDS / 'input_food.csv', dtype={'sr_code': 'float64'})

    report['fped'] = {
        'rows': len(fped),
        'key_column': 'FOODCODE',
        'pattern_columns': [c for c in fped.columns if 'eq.' in c or 'eq)' in c][:8],
    }
    report['fpid'] = {
        'rows': len(fpid),
        'key_column': 'CODE',
        'pattern_columns': [c for c in fpid.columns if 'eq.' in c or 'eq)' in c][:8],
    }
    print(f'\nFPED rows: {len(fped)} (key=FOODCODE, finished-food pattern equivalents)')
    print(f'FPID rows: {len(fpid)} (key=CODE, ingredient-level pattern equivalents)')

    fndds_food_codes = set(sf['food_code'].astype(int))
    fped_codes = set(fped['FOODCODE'].astype(int))
    fpid_codes = set(fpid['CODE'].astype(int))
    sr_codes = set(inp['sr_code'].dropna().astype(int))

    fped_hit = len(fndds_food_codes & fped_codes)
    fpid_hit = len(sr_codes & fpid_codes)
    fped_fpid_overlap = len(fped_codes & fpid_codes)

    report['key_alignment'] = {
        'fndds_food_codes': len(fndds_food_codes),
        'fndds_sr_codes': len(sr_codes),
        'fped_fndds_overlap': fped_hit,
        'fped_fndds_overlap_pct': round(100 * fped_hit / max(1, len(fndds_food_codes)), 1),
        'fpid_sr_overlap': fpid_hit,
        'fpid_sr_overlap_pct': round(100 * fpid_hit / max(1, len(sr_codes)), 1),
        'fped_fpid_code_overlap': fped_fpid_overlap,
    }
    print(f'\nFNDDS food_code → FPED FOODCODE: {fped_hit}/{len(fndds_food_codes)} '
          f'({report["key_alignment"]["fped_fndds_overlap_pct"]}%)')
    print(f'FNDDS input_food sr_code → FPID CODE: {fpid_hit}/{len(sr_codes)} '
          f'({report["key_alignment"]["fpid_sr_overlap_pct"]}%)')
    print(f'FPED FOODCODE ∩ FPID CODE (direct): {fped_fpid_overlap} — different key spaces')

    # --- Current bridge / composition coverage ---------------------------
    bridge = json.loads(_BRIDGE.read_text(encoding='utf-8')) if _BRIDGE.exists() else {}
    bridges = bridge.get('bridges', {})
    comp = json.loads(_COMPOSITION.read_text(encoding='utf-8')) if _COMPOSITION.exists() else {}
    compositions = comp.get('compositions', {})

    bridged_food_codes = [int(v['food_code']) for v in bridges.values()]
    in_fped = sum(1 for fc in bridged_food_codes if fc in fped_codes)
    in_fpid = sum(1 for fc in bridged_food_codes if fc in fpid_codes)

    report['current_integration'] = {
        'fped_runtime_wired': True,
        'fped_etl': 'heni_calculator.heni.etl.build_cnf_heni_composition',
        'fped_loader': 'heni_calculator.heni.data.composition_loader',
        'fpid_runtime_wired': False,
        'cnf_bridged': len(bridges),
        'cnf_compositions': len(compositions),
        'bridged_with_fped_row': in_fped,
        'bridged_with_fpid_row': in_fpid,
        'bridge_provenance': bridge.get('_provenance', {}),
    }
    print(f'\nCurrent CNF/WAFCT→FNDDS bridge: {len(bridges)} foods')
    print(f'  → FPED composition lookup (HENI 8-bucket): {len(compositions)} entries ({in_fped} direct FPED hits)')
    print(f'  → Full 37-component FPED profiles: api/data/cnf_fped_profile.json (bridged CNF + WAFCT)')
    print(f'  → FPID: not integrated ({in_fpid} bridged foods match FPID CODE — expected 0)')

    # --- Contrast with WAFCT explore -------------------------------------
    report['contrast_with_wafct_explore'] = {
        'wafct_harness': '_explore_wafct_vs_cnf_per100g.py',
        'wafct_purpose': 'Compare per-100g NUTRIENT values between two nutrient DBs (CNF vs WAFCT)',
        'fped_fpid_purpose': 'Food-pattern cup/oz equivalents for HENI risk-factor masses — not nutrients',
        'analogous_validation': [
            'Bridge coverage audit (this harness)',
            'FPED vs legacy literal-100 attribution panel (_smoke_heni_literature_panel.py)',
            'Per-composite-food decomposition sanity (pepperoni pizza, apple pie)',
        ],
    }

    # --- Data layout (current) ----------------------------------------
    report['data_layout'] = {
        'raw_sources_at_backend_root': {
            'raw_cnf': 'Canadian Nutrient File CSVs',
            'raw_wafct': 'WAFCT_2019.xlsx',
            'raw_fndds': 'FoodData_Central_survey_food_csv_2024-10-31/ (relocated 2026-05-27)',
            'raw_fped': 'FPED_1718.xls (relocated 2026-05-27)',
            'raw_fpid': 'FPID_1718.xls (relocated 2026-05-27)',
        },
        'derived_artifacts_module_local': {
            'cnf_to_fndds_bridge.json': 'heni_calculator/data/',
            'cnf_heni_composition.json': 'heni_calculator/data/',
            'fndds_embeddings.npz': 'heni_calculator/data/',
        },
    }

    report['recommendations'] = [
        'FPED is integrated for HENI across the full CNF corpus (CNF 2026 edition). '
        'After any CNF edition refresh, re-run: build_cnf_to_fndds_bridge (auto-bridges '
        'new food codes) then build_cnf_heni_composition.',
        'FPID has a loader stub at heni_calculator.heni.data.fpid_loader but no consumer '
        'is wired in yet. It uses ingredient CODE (via FNDDS input_food.sr_code), not '
        'FOODCODE — use for ingredient-level pattern decomposition of composite foods.',
        'Do NOT compare FPED/FPID to CNF/WAFCT with the per-100g nutrient delta harness; '
        'they answer different questions (pattern equivalents vs nutrient composition).',
        'Full 37-component FPED profiles (api/data/cnf_fped_profile.json) include bridged '
        'WAFCT foods the same as CNF — inclusion is bridge-gated, not source-gated. Foods '
        'with no close US analog have no profile and are flagged in coverage notes.',
    ]

    print('\n## Recommendations')
    for i, rec in enumerate(report['recommendations'], 1):
        print(f'  {i}. {rec}')

    _OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nResults JSON: {_OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
