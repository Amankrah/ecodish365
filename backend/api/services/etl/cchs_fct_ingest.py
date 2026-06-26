"""CCHS Nutrition 2015 Food Consumption Table ETL (PLATFORM-CODE-1.m, 2026-06-26).

Reads Health Canada's published Food Consumption Table 2015 — 10 per-food-group
CSVs + 1 body-weight reference + 1 subgroup-list — and normalises every cell
into one long-format JSON artifact the platform loads as a singleton at
runtime via [`cchs_fct_loader.py`](backend/api/services/cchs_fct_loader.py).

Each per-group CSV row has 32 statistic columns: {All-Person, Eaters-Only}
x {per-person, per-kg-body-weight} x {Mean, P50, P90, P95} x {value, SE}.
We unpivot those 32 columns into 16 long-format rows per source row
(value + SE paired), tagged with `basis`, `denom`, `statistic`.

Suppression: Health Canada flags low-CV cells with `'E'` (CV 16.6-33.3 %,
interpret with caution), `'F'` or `'.'` (CV > 33.3 % or n_eaters too low,
suppressed). We carry that flag through to the loader so the UI never
silently fills a suppressed cell.

Compound Food-Group-Code values like `"22 - 25 and 27 - 32 and 34 - 35"`
(MEATS - OVERALL) and `"10E- 10F- 10G"` (MILK - EVAPORATED combined) are
kept as-is — they identify the published roll-up rather than a single
subgroup, and downstream code matches on the literal string.

Deterministic, no LLM. Run-once:

    cd backend
    python -m api.services.etl.cchs_fct_ingest

Inputs:
    backend/raw_cchs_fct_2015/fct2015_*.csv         (10 group + 1 body-weight)
    backend/raw_cchs_fct_2015/food-group-list-2015.csv

Output:
    backend/api/data/cchs_fct_2015.json
"""
from __future__ import annotations

import csv
import json
import logging
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

logger = logging.getLogger(__name__)


_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_RAW_DIR = _BACKEND_ROOT / 'raw_cchs_fct_2015'
_OUT_PATH = _BACKEND_ROOT / 'api' / 'data' / 'cchs_fct_2015.json'

# Per the README: "All Bureau of Nutritional Sciences (BNS) food groups are
# categorized into ten main food groups". File-name -> canonical main group label.
_GROUP_FILES: List[Tuple[str, str]] = [
    ('fct2015_grain_final.csv',     'Grain products'),
    ('fct2015_dairy_final.csv',     'Dairy products'),
    ('fct2015_fat_final.csv',       'Fats'),
    ('fct2015_meat_final.csv',      'Meats'),
    ('fct2015_meat_alt_final.csv',  'Meat alternatives'),
    ('fct2015_veg_final.csv',       'Vegetables'),
    ('fct2015_fruits_final.csv',    'Fruits'),
    ('fct2015_beverage_final.csv',  'Beverages'),
    ('fct2015_babyfood_final.csv',  'Babyfood'),
    ('fct2015_mis_final.csv',       'Miscellaneous'),
]
_BODYWEIGHT_FILE = 'fct2015_bodyweight_final.csv'
_GROUP_LIST_FILE = 'food-group-list-2015.csv'

# CCHS strata labels we accept as published. Both/Male/Female x age band.
_VALID_SEX = {'both', 'male', 'female'}
_VALID_AGE_BANDS = {
    'All ages', '1-3 Years', '4-8 Years', '9-13 Years', '14-18 Years',
    '19-30 Years', '31-50 Years', '51-70 Years', '71+ Years',
    '1-18 Years', '19+ Years',
}

# Map every published stat column suffix to (basis, denom, statistic, kind)
# where kind in {'value', 'se'}. Each source row produces 16 long rows
# (8 stats x 2 kinds).
_STAT_COL_TEMPLATE = [
    # (basis, denom, statistic)
    ('all_person',  'per_person',     'mean'),
    ('all_person',  'per_person',     'p50'),
    ('all_person',  'per_person',     'p90'),
    ('all_person',  'per_person',     'p95'),
    ('all_person',  'per_kg_bw',      'mean'),
    ('all_person',  'per_kg_bw',      'p50'),
    ('all_person',  'per_kg_bw',      'p90'),
    ('all_person',  'per_kg_bw',      'p95'),
    ('eaters_only', 'per_person',     'mean'),
    ('eaters_only', 'per_person',     'p50'),
    ('eaters_only', 'per_person',     'p90'),
    ('eaters_only', 'per_person',     'p95'),
    ('eaters_only', 'per_kg_bw',      'mean'),
    ('eaters_only', 'per_kg_bw',      'p50'),
    ('eaters_only', 'per_kg_bw',      'p90'),
    ('eaters_only', 'per_kg_bw',      'p95'),
]


def _column_key(basis: str, denom: str, statistic: str, kind: str) -> str:
    """Reconstruct the published header for a (basis, denom, statistic, kind) tuple."""
    basis_label = 'All-Person' if basis == 'all_person' else 'Eaters-Only'
    denom_label = 'g-per-person' if denom == 'per_person' else 'g-per-kg-body-weight'
    stat_label = {'mean': 'Mean', 'p50': 'P50', 'p90': 'P90', 'p95': 'P95'}[statistic]
    prefix = 'SE-' if kind == 'se' else ''
    return f'{basis_label}-Consumption-Intake-{denom_label}-{prefix}{stat_label}'


def _normalise_header(headers: Iterable[str]) -> Dict[str, int]:
    """Map cleaned header label -> column index. Strips whitespace + BOMs."""
    out: Dict[str, int] = {}
    for i, h in enumerate(headers):
        out[(h or '').strip().lstrip('﻿')] = i
    return out


def _parse_value(raw: str) -> Tuple[Optional[float], str]:
    """Parse one stat-cell value -> (number_or_None, suppression_flag).

    suppression_flag in {'none', 'E', 'F'}. The published table uses 'F' or
    '.' interchangeably for fully-suppressed cells; we collapse to 'F'.
    """
    s = (raw or '').strip()
    if s == '' or s == '.':
        return None, 'F'
    if s.upper() == 'F':
        return None, 'F'
    # An 'E' suffix flags a cautionable value (CV 16.6-33.3 %); the numeric
    # part is still published.
    if s.upper().endswith('E'):
        try:
            return float(s[:-1].strip()), 'E'
        except ValueError:
            return None, 'F'
    try:
        return float(s), 'none'
    except ValueError:
        return None, 'F'


def _parse_int(raw: str) -> Optional[int]:
    s = (raw or '').strip()
    if not s or s.upper() == 'F' or s == '.':
        return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _parse_float(raw: str) -> Optional[float]:
    s = (raw or '').strip()
    if not s or s.upper() == 'F' or s == '.':
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _normalise_sex(raw: str) -> Optional[str]:
    s = (raw or '').strip().lower()
    if s in _VALID_SEX:
        return s
    return None


def _normalise_age_band(raw: str) -> Optional[str]:
    s = (raw or '').strip()
    return s if s in _VALID_AGE_BANDS else None


def _parse_group_file(path: Path, main_group: str) -> List[Dict[str, Any]]:
    """Read one fct2015_<group>_final.csv into long-format rows."""
    rows: List[Dict[str, Any]] = []
    with path.open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.reader(fh)
        header = next(reader)
        col_idx = _normalise_header(header)

        # Required key columns
        try:
            i_name = col_idx['Food-Group-Name']
            i_code = col_idx['Food-Group-Code']
            i_sex = col_idx['Sex']
            i_age = col_idx['Age']
            i_n   = col_idx['Number-of-Respondents']
            i_pct = col_idx['Percentage-of-Eaters']
        except KeyError as exc:
            raise RuntimeError(f'{path.name}: missing required column {exc}')

        for row in reader:
            if not row or len(row) < 6:
                continue
            sex = _normalise_sex(row[i_sex])
            age = _normalise_age_band(row[i_age])
            if sex is None or age is None:
                continue
            subgroup_code = (row[i_code] or '').strip()
            subgroup_name = (row[i_name] or '').strip()
            if not subgroup_code or not subgroup_name:
                continue

            n_respondents = _parse_int(row[i_n])
            pct_eaters = _parse_float(row[i_pct])

            for basis, denom, statistic in _STAT_COL_TEMPLATE:
                col_value = _column_key(basis, denom, statistic, 'value')
                col_se    = _column_key(basis, denom, statistic, 'se')
                if col_value not in col_idx or col_se not in col_idx:
                    continue
                v_raw = row[col_idx[col_value]] if col_idx[col_value] < len(row) else ''
                se_raw = row[col_idx[col_se]]    if col_idx[col_se]    < len(row) else ''
                value, flag_v  = _parse_value(v_raw)
                se,    flag_se = _parse_value(se_raw)
                # If the value is suppressed, propagate that flag; SE
                # suppression alone (rare) downgrades the flag to caution.
                flag = flag_v if flag_v != 'none' else flag_se
                rows.append({
                    'main_group':        main_group,
                    'subgroup_code':     subgroup_code,
                    'subgroup_name':     subgroup_name,
                    'sex':               sex,
                    'age_band':          age,
                    'n_respondents':     n_respondents,
                    'pct_eaters':        pct_eaters,
                    'basis':             basis,
                    'denom':             denom,
                    'statistic':         statistic,
                    'value':             value,
                    'se':                se,
                    'suppression_flag':  flag,
                })
    logger.info('  %s: %d long rows from %d stratum rows', path.name,
                len(rows), len(rows) // len(_STAT_COL_TEMPLATE) if rows else 0)
    return rows


def _parse_bodyweight(path: Path) -> List[Dict[str, Any]]:
    """fct2015_bodyweight_final.csv -> per-(sex, age_band) body-weight rows.

    Schema: Sex, Age, Number-of-respondents, mean-bw, 95percent-Mean-LB,
    95percent-Mean-UB, median-bw, 95percent-Median-LB, 95percent-Median-UB.
    """
    out: List[Dict[str, Any]] = []
    with path.open('r', encoding='utf-8-sig', newline='') as fh:
        reader = csv.reader(fh)
        header = next(reader)
        col = _normalise_header(header)
        try:
            i_sex = col['Sex']
            i_age = col['Age']
            i_n   = col['Number-of-respondents']
            i_mean = col['mean-bw']
            i_mlb  = col['95percent-Mean-LB']
            i_mub  = col['95percent-Mean-UB']
            i_med  = col['median-bw']
            i_qlb  = col['95percent-Median-LB']
            i_qub  = col['95percent-Median-UB']
        except KeyError as exc:
            raise RuntimeError(f'{path.name}: missing column {exc}')

        for row in reader:
            if not row or len(row) < 9:
                continue
            sex = _normalise_sex(row[i_sex])
            age = _normalise_age_band(row[i_age])
            if sex is None or age is None:
                continue
            out.append({
                'sex':           sex,
                'age_band':      age,
                'n_respondents': _parse_int(row[i_n]),
                'mean_bw':       _parse_float(row[i_mean]),
                'mean_lb':       _parse_float(row[i_mlb]),
                'mean_ub':       _parse_float(row[i_mub]),
                'median_bw':     _parse_float(row[i_med]),
                'median_lb':     _parse_float(row[i_qlb]),
                'median_ub':     _parse_float(row[i_qub]),
            })
    logger.info('  %s: %d body-weight strata', path.name, len(out))
    return out


_GROUP_LIST_MAIN_HEADERS = {
    # The free-text rows that introduce each main group in food-group-list-2015.csv.
    # We treat these as section markers, not subgroups.
    'grain products', 'dairy products', 'fats', 'meats', 'meat alternatives',
    'vegetables', 'fruits', 'beverages', 'babyfood products', 'miscellaneous',
}


def _parse_group_list(path: Path) -> List[Dict[str, Any]]:
    """food-group-list-2015.csv -> subgroup metadata.

    The file alternates between main-group banner rows (no code, no
    description) and subgroup rows. Top-level codes like '1' identify a
    parent group; sub-letter codes like '1A' / '10D' / '4F' identify
    specific subgroups; compound codes like '10E- 10F- 10G' identify a
    published combined group. We keep every coded row.
    """
    import io
    out: List[Dict[str, Any]] = []
    current_main: Optional[str] = None
    # food-group-list-2015.csv ships with at least one Windows-1252 byte
    # (0xe8) — try utf-8 first, fall back to cp1252 so accented chars in
    # subgroup descriptions don't crash the run.
    try:
        text = path.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        text = path.read_text(encoding='cp1252')
    reader = csv.reader(io.StringIO(text))
    next(reader)  # skip header
    for row in reader:
        if not row:
            continue
        row = (row + [''] * 4)[:4]   # pad to 4 cols
        code = (row[0] or '').strip()
        name = (row[1] or '').strip()
        desc = (row[2] or '').strip()
        notes = (row[3] or '').strip()
        if not code and not name:
            continue
        # Main-group banner row: Health Canada sticks the main-group name
        # in the Code column with everything else blank (e.g.
        # `Grain Products,,,,` precedes the `1A`, `1B`, ... rows).
        if code.lower() in _GROUP_LIST_MAIN_HEADERS and not name and not desc:
            current_main = code
            continue
        # Coded row -> subgroup entry
        if code:
            out.append({
                'code':        code,
                'name':        name,
                'description': desc,
                'notes':       notes,
                'main_group':  current_main,
            })
    logger.info('  %s: %d coded subgroup entries', path.name, len(out))
    return out


def _summarise_subgroups(long_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """De-duplicate the (subgroup_code, subgroup_name, main_group) tuple
    across long rows. Lets the loader serve a quick subgroup index without
    scanning the long table."""
    seen: Dict[str, Dict[str, Any]] = {}
    for r in long_rows:
        code = r['subgroup_code']
        if code in seen:
            continue
        seen[code] = {
            'code':       code,
            'name':       r['subgroup_name'],
            'main_group': r['main_group'],
        }
    return list(seen.values())


def _summarise_strata(long_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Unique (sex, age_band) strata observed in the long table."""
    seen: Dict[Tuple[str, str], int] = {}
    for r in long_rows:
        key = (r['sex'], r['age_band'])
        if key not in seen:
            seen[key] = r['n_respondents'] or 0
    return [{'sex': s, 'age_band': a, 'n_respondents': n}
            for (s, a), n in seen.items()]


def build_artifact() -> Dict[str, Any]:
    """Parse every input file and return the full long-format dict."""
    if not _RAW_DIR.exists():
        raise FileNotFoundError(f'raw dir missing: {_RAW_DIR}')

    logger.info('Reading per-group consumption tables from %s', _RAW_DIR)
    long_rows: List[Dict[str, Any]] = []
    for fname, main_group in _GROUP_FILES:
        path = _RAW_DIR / fname
        if not path.exists():
            logger.warning('Missing %s; skipping main group %s', fname, main_group)
            continue
        long_rows.extend(_parse_group_file(path, main_group))

    bodyweights = _parse_bodyweight(_RAW_DIR / _BODYWEIGHT_FILE)
    subgroup_meta = _parse_group_list(_RAW_DIR / _GROUP_LIST_FILE)

    # Cross-check: every code that appears in the long table should also
    # appear in the subgroup_meta list (so the loader can resolve
    # description / notes for any cell it serves). Log gaps as warnings;
    # do not fail — Health Canada occasionally publishes a combined-code
    # row in the consumption table that is not on the subgroup-list sheet.
    code_in_long = {r['subgroup_code'] for r in long_rows}
    code_in_meta = {m['code'] for m in subgroup_meta}
    gap = sorted(code_in_long - code_in_meta)
    if gap:
        logger.warning('Codes in consumption table missing from food-group-list (%d): %s',
                       len(gap), gap[:10])

    artifact = {
        'meta': {
            'source':               'Health Canada Food Consumption Table 2015',
            'base_data':            'CCHS Nutrition 2015, Share File (Statistics Canada)',
            'weighting':            'Survey-weighted, bootstrap SEs via PROC SURVEYMEANS',
            'n_respondents_total':  19670,
            'ingestion_date':       str(date.today()),
            'platform_item_id':     'PLATFORM-CODE-1.m',
            'notes': (
                'Single-day (Day-1 24-h recall), not usual intake. Recipe groups '
                'excluded by Health Canada. Suppression flags: E = CV 16.6-33.3% '
                '(caution); F = suppressed (CV > 33.3% or n_eaters too low).'
            ),
        },
        'long_rows':      long_rows,
        'subgroups':      _summarise_subgroups(long_rows),
        'subgroup_meta':  subgroup_meta,
        'strata':         _summarise_strata(long_rows),
        'body_weights':   bodyweights,
    }
    logger.info('Built artifact: %d long rows, %d subgroups, %d strata, %d body-weight rows',
                len(long_rows), len(artifact['subgroups']),
                len(artifact['strata']), len(bodyweights))
    return artifact


def write_artifact(artifact: Dict[str, Any], out_path: Path = _OUT_PATH) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8') as fh:
        json.dump(artifact, fh, ensure_ascii=False, indent=2)
    logger.info('Wrote %s (%d KB)', out_path,
                out_path.stat().st_size // 1024)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    artifact = build_artifact()
    write_artifact(artifact)


if __name__ == '__main__':
    main()
