"""Cohort upload parsers (PLATFORM-CODE-1.b, 2026-06-26).

Two ingest paths, both returning the same `Recall` shape that the cohort
orchestrator expects:

  - `parse_generic_csv(text)` — header-driven CSV with flexible column
    aliases. The internal canonical schema is
    `respondent_id, day_id, occasion, food_id, mass_g`; we accept
    common SAS / NHANES / spreadsheet variants (`SEQN`, `grams`, etc.)
    so a researcher doesn't have to rename columns.

  - `parse_nhanes_xpt(xpt_bytes)` — SAS XPT for the NHANES Day-1
    individual food file (`DR1IFF_J.xpt`) or Day-2 (`DR2IFF_J.xpt`).
    Maps each line's FNDDS food code (DR1IFDCD) to a CNF FoodID via the
    existing [cnf_to_fndds_bridge.json](backend/heni_calculator/data/cnf_to_fndds_bridge.json),
    then groups by SEQN to yield one Recall per respondent. Rows with
    no FNDDS→CNF bridge are dropped and counted in the validation report,
    NOT silently merged.

Both return `(recalls, ValidationReport)` so the caller can show the
researcher a preview + a count of dropped/unknown rows before they
commit to running cohort scoring (which is the expensive step).

This module performs NO scoring. It's a pure parse + map + validate
layer that sits in front of `cohort_orchestrator.score_cohort`.
"""
from __future__ import annotations

import csv
import io
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from api.services.cohort_orchestrator import Recall

logger = logging.getLogger(__name__)


_BRIDGE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / 'heni_calculator' / 'data' / 'cnf_to_fndds_bridge.json'
)

# NHANES 2017-2018 DR1_030Z (meal occasion) numeric codes → English bucket.
# Mirrors `_OCCASION_BUCKET` in `etl/build_nhanes_2017_meal_pool.py:61-68`.
# Per https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DR1IFF_J.htm value labels.
_NHANES_OCCASION = {
    1.0: 'breakfast', 10.0: 'breakfast',
    2.0: 'lunch', 3.0: 'lunch', 11.0: 'lunch', 12.0: 'lunch',
    4.0: 'dinner', 5.0: 'dinner', 14.0: 'dinner',
    6.0: 'snack', 7.0: 'snack', 13.0: 'snack',
    15.0: 'snack', 16.0: 'snack', 17.0: 'snack',
    18.0: 'snack', 19.0: 'snack',
}

# Column-name aliases for the generic CSV path. Lowercased before matching.
_ALIASES = {
    'respondent_id': ('respondent_id', 'subject_id', 'seqn', 'participant_id', 'person_id', 'id'),
    'day_id':        ('day_id', 'day', 'day_n', 'day_num', 'recall_day', 'recallday'),
    'occasion':      ('occasion', 'meal', 'meal_name', 'meal_type', 'meal_occasion'),
    'food_id':       ('food_id', 'cnf_id', 'cnfid', 'foodid', 'fndds_code', 'ciqual_code', 'fdc_id'),
    'mass_g':        ('mass_g', 'mass', 'grams', 'amount_g', 'amount', 'gram', 'weight_g'),
}

_bridge_lock = Lock()
_fndds_to_cnf_cache: Optional[Dict[int, int]] = None


# ---------- Validation report ----------------------------------------------

@dataclass
class ValidationReport:
    n_rows_read:        int = 0
    n_rows_dropped:     int = 0
    n_recalls_built:    int = 0
    n_respondents:      int = 0
    drop_reasons:       Dict[str, int] = field(default_factory=dict)
    unknown_food_ids:   List[int] = field(default_factory=list)   # first 50 only
    sample_bad_rows:    List[Dict[str, Any]] = field(default_factory=list)  # first 10 only
    fndds_unmatched:    int = 0
    fndds_matched:      int = 0
    headers_detected:   List[str] = field(default_factory=list)

    def add_drop(self, reason: str) -> None:
        self.drop_reasons[reason] = self.drop_reasons.get(reason, 0) + 1
        self.n_rows_dropped += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            'n_rows_read':       self.n_rows_read,
            'n_rows_dropped':    self.n_rows_dropped,
            'n_recalls_built':   self.n_recalls_built,
            'n_respondents':     self.n_respondents,
            'drop_reasons':      dict(self.drop_reasons),
            'unknown_food_ids':  self.unknown_food_ids[:50],
            'sample_bad_rows':   self.sample_bad_rows[:10],
            'fndds_matched':     self.fndds_matched,
            'fndds_unmatched':   self.fndds_unmatched,
            'headers_detected':  self.headers_detected,
        }


# ---------- Bridge loader --------------------------------------------------

def _load_fndds_to_cnf_bridge() -> Dict[int, int]:
    """Invert the CNF→FNDDS bridge to FNDDS code → CNF FoodID. Cached.
    Logic mirrors `_invert_bridge` in `build_nhanes_2017_meal_pool.py:96-135`
    so the parser produces the same matches as the manuscript ETL."""
    global _fndds_to_cnf_cache
    if _fndds_to_cnf_cache is not None:
        return _fndds_to_cnf_cache
    with _bridge_lock:
        if _fndds_to_cnf_cache is not None:
            return _fndds_to_cnf_cache
        if not _BRIDGE_PATH.exists():
            logger.warning('CNF→FNDDS bridge missing at %s; NHANES ingest disabled.', _BRIDGE_PATH)
            _fndds_to_cnf_cache = {}
            return _fndds_to_cnf_cache
        with _BRIDGE_PATH.open('r', encoding='utf-8') as fh:
            raw = json.load(fh)
        forward = raw.get('bridges', {})
        inverted: Dict[int, Tuple[int, float]] = {}
        for cnf_id_str, entry in forward.items():
            try:
                cnf_id = int(cnf_id_str)
                food_code = int(entry['food_code'])
                conf = float(entry.get('confidence', 0.0))
            except (TypeError, ValueError, KeyError):
                continue
            # Loadable CNF range: stock CNF + WAFCT (FDC + CIQUAL use other prefixes
            # that are not in the bridge anyway).
            if not (1 <= cnf_id <= 7021 or cnf_id >= 700000):
                continue
            existing = inverted.get(food_code)
            if existing is None or conf > existing[1]:
                inverted[food_code] = (cnf_id, conf)
        _fndds_to_cnf_cache = {fc: cid for fc, (cid, _c) in inverted.items()}
        logger.info('cohort_ingest: FNDDS→CNF bridge loaded, %d codes mapped.',
                    len(_fndds_to_cnf_cache))
    return _fndds_to_cnf_cache


# ---------- Generic CSV ----------------------------------------------------

def _normalize_header(h: str) -> Optional[str]:
    """Map a raw header to one of {respondent_id, day_id, occasion, food_id, mass_g}.
    Returns None if not recognized."""
    lo = h.strip().lower().lstrip('﻿')
    for canonical, aliases in _ALIASES.items():
        if lo in aliases:
            return canonical
    return None


def parse_generic_csv(text: str) -> Tuple[List[Recall], ValidationReport]:
    report = ValidationReport()
    if not text or not text.strip():
        report.add_drop('empty_input')
        return [], report

    reader = csv.reader(io.StringIO(text))
    try:
        raw_headers = next(reader)
    except StopIteration:
        report.add_drop('no_header_row')
        return [], report
    report.headers_detected = list(raw_headers)

    # Build a position → canonical-name map.
    canon_at: Dict[int, str] = {}
    for i, h in enumerate(raw_headers):
        c = _normalize_header(h)
        if c is not None:
            canon_at[i] = c
    if 'food_id' not in canon_at.values() or 'mass_g' not in canon_at.values():
        report.add_drop('missing_required_columns_food_id_or_mass_g')
        return [], report
    has_respondent = 'respondent_id' in canon_at.values()
    has_day = 'day_id' in canon_at.values()

    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    grouped_order: List[Tuple[str, str]] = []

    for row in reader:
        report.n_rows_read += 1
        rec: Dict[str, Any] = {}
        for i, val in enumerate(row):
            c = canon_at.get(i)
            if c is not None:
                rec[c] = val
        try:
            fid = int(float(rec.get('food_id') or 0))
            mass = float(rec.get('mass_g') or 0)
        except (TypeError, ValueError):
            if len(report.sample_bad_rows) < 10:
                report.sample_bad_rows.append({'row': rec, 'reason': 'parse_error_food_id_or_mass_g'})
            report.add_drop('parse_error_food_id_or_mass_g')
            continue
        if fid <= 0 or mass <= 0:
            if len(report.sample_bad_rows) < 10:
                report.sample_bad_rows.append({'row': rec, 'reason': 'food_id_or_mass_g_nonpositive'})
            report.add_drop('food_id_or_mass_g_nonpositive')
            continue
        rid = str(rec.get('respondent_id') or 'subject_unknown') if has_respondent else 'subject_all'
        did = str(rec.get('day_id') or 'day_1') if has_day else 'day_1'
        key = (rid, did)
        if key not in grouped:
            grouped[key] = []
            grouped_order.append(key)
        entry: Dict[str, Any] = {'food_id': fid, 'mass_g': mass}
        occ = rec.get('occasion')
        if occ:
            entry['occasion'] = str(occ).strip().lower()
        grouped[key].append(entry)

    recalls: List[Recall] = []
    respondents = set()
    for rid, did in grouped_order:
        foods = grouped[(rid, did)]
        if not foods:
            continue
        recalls.append(Recall(respondent_id=rid, day_id=did, foods=foods))
        respondents.add(rid)
    report.n_recalls_built = len(recalls)
    report.n_respondents = len(respondents)
    return recalls, report


# ---------- NHANES XPT ----------------------------------------------------

def parse_nhanes_xpt(
    xpt_bytes: bytes,
    day_id_label: str = 'day_1',
) -> Tuple[List[Recall], ValidationReport]:
    """Parse an NHANES `DR*IFF_*.xpt` Day-1 / Day-2 individual food file
    into per-respondent Recalls. FNDDS food codes are mapped to CNF FoodIDs
    via the same bridge the manuscript ETL uses."""
    report = ValidationReport()
    if not xpt_bytes:
        report.add_drop('empty_input')
        return [], report

    # pandas is the cleanest XPT reader we already depend on.
    import pandas as pd
    try:
        dr = pd.read_sas(io.BytesIO(xpt_bytes), format='xport')
    except Exception as exc:  # noqa: BLE001
        report.add_drop(f'xpt_parse_error:{type(exc).__name__}')
        if len(report.sample_bad_rows) < 1:
            report.sample_bad_rows.append({'reason': f'xpt_parse_error: {exc}'})
        return [], report

    # Required NHANES columns. Day-2 file uses DR2* prefixes — accept either.
    cols = set(dr.columns)
    if 'SEQN' not in cols:
        report.add_drop('missing_SEQN_column')
        return [], report
    fdcd = 'DR1IFDCD' if 'DR1IFDCD' in cols else ('DR2IFDCD' if 'DR2IFDCD' in cols else None)
    grms = 'DR1IGRMS' if 'DR1IGRMS' in cols else ('DR2IGRMS' if 'DR2IGRMS' in cols else None)
    occc = 'DR1_030Z' if 'DR1_030Z' in cols else ('DR2_030Z' if 'DR2_030Z' in cols else None)
    if not fdcd or not grms:
        report.add_drop('missing_required_NHANES_columns_DR_IFDCD_or_DR_IGRMS')
        report.headers_detected = list(map(str, dr.columns))
        return [], report
    report.headers_detected = [c for c in (fdcd, grms, occc, 'SEQN') if c]

    fndds_to_cnf = _load_fndds_to_cnf_bridge()
    report.n_rows_read = len(dr)

    grouped: Dict[str, List[Dict[str, Any]]] = {}
    grouped_order: List[str] = []
    unknown_codes_seen: set = set()

    # Iterate rows. NHANES files are ~100k rows so this stays well under a
    # second on the reference machine; using pandas vectorisation is overkill
    # here and would make the validation report harder to populate.
    for _, row in dr.iterrows():
        try:
            seqn = int(row['SEQN'])
        except (TypeError, ValueError):
            report.add_drop('bad_SEQN')
            continue
        try:
            code = int(row[fdcd])
        except (TypeError, ValueError):
            report.add_drop('bad_food_code')
            continue
        try:
            mass = float(row[grms])
        except (TypeError, ValueError):
            mass = 0.0
        if mass <= 0:
            report.add_drop('mass_nonpositive')
            continue
        cnf_id = fndds_to_cnf.get(code)
        if cnf_id is None:
            report.fndds_unmatched += 1
            if code not in unknown_codes_seen and len(report.unknown_food_ids) < 50:
                report.unknown_food_ids.append(code)
                unknown_codes_seen.add(code)
            report.add_drop('fndds_unmatched')
            continue
        report.fndds_matched += 1
        rid = f'NHANES_{seqn}'
        if rid not in grouped:
            grouped[rid] = []
            grouped_order.append(rid)
        entry: Dict[str, Any] = {'food_id': int(cnf_id), 'mass_g': mass}
        if occc:
            try:
                occ_code = float(row[occc])
            except (TypeError, ValueError):
                occ_code = None
            occ_label = _NHANES_OCCASION.get(occ_code) if occ_code is not None else None
            if occ_label:
                entry['occasion'] = occ_label
        grouped[rid].append(entry)

    recalls: List[Recall] = []
    for rid in grouped_order:
        foods = grouped[rid]
        if foods:
            recalls.append(Recall(respondent_id=rid, day_id=day_id_label, foods=foods))
    report.n_recalls_built = len(recalls)
    report.n_respondents = len(recalls)   # 1 day per SEQN per file
    return recalls, report


# ---------- Validation -----------------------------------------------------

def validate_recalls(recalls: List[Recall]) -> ValidationReport:
    """Post-parse validation — useful when the caller built recalls some
    other way (e.g. pasted JSON in the UI's developer field) and wants the
    same QC the parsers run."""
    report = ValidationReport()
    respondents = set()
    for r in recalls:
        report.n_rows_read += len(r.foods)
        if not r.foods:
            report.add_drop('recall_with_no_foods')
            continue
        for f in r.foods:
            fid = f.get('food_id')
            mass = f.get('mass_g')
            if not isinstance(fid, int) or fid <= 0:
                report.add_drop('food_id_nonpositive')
                continue
            if not isinstance(mass, (int, float)) or mass <= 0:
                report.add_drop('mass_nonpositive')
                continue
        respondents.add(r.respondent_id)
    report.n_recalls_built = len(recalls)
    report.n_respondents = len(respondents)
    return report


# ---------- Format dispatch ----------------------------------------------

def parse_upload(
    file_bytes: bytes,
    filename: str = '',
    format_hint: str = 'auto',
) -> Tuple[List[Recall], ValidationReport, str]:
    """Single entry point for the upload endpoint. Returns
    `(recalls, report, format_detected)`.

    Detection rules:
      - `format_hint='generic_csv'`         → parse_generic_csv
      - `format_hint='nhanes_dr1iff'/'..2'` → parse_nhanes_xpt
      - 'auto': sniff by extension first, then by content shape.
    """
    fmt = format_hint.lower().strip()
    name_lo = filename.lower()
    if fmt == 'auto':
        if name_lo.endswith('.xpt'):
            fmt = 'nhanes_dr1iff' if 'dr1' in name_lo or 'dr2' not in name_lo else 'nhanes_dr2iff'
        elif name_lo.endswith('.csv') or name_lo.endswith('.txt'):
            fmt = 'generic_csv'
        else:
            # Content sniff: NHANES XPT files start with the literal
            # "HEADER RECORD" SAS xport magic. CSV starts printable.
            head = file_bytes[:128] if file_bytes else b''
            if b'HEADER RECORD' in head or b'SAS' in head[:80]:
                fmt = 'nhanes_dr1iff'
            else:
                fmt = 'generic_csv'

    if fmt in ('nhanes_dr1iff', 'nhanes_dr2iff'):
        recalls, report = parse_nhanes_xpt(
            file_bytes,
            day_id_label='day_2' if fmt == 'nhanes_dr2iff' else 'day_1',
        )
        return recalls, report, fmt
    # default: generic CSV
    try:
        text = file_bytes.decode('utf-8-sig', errors='replace')
    except Exception:  # noqa: BLE001
        text = file_bytes.decode('latin-1', errors='replace')
    recalls, report = parse_generic_csv(text)
    return recalls, report, 'generic_csv'
