"""Process-wide singleton loader for FPID ingredient-level pattern equivalents.

FPID (USDA Food Patterns Ingredient Database, FPID_1718.xls) holds cup/oz pattern
equivalents keyed on the USDA SR ingredient code, not on the finished-food FNDDS
food_code that FPED uses. To go from a finished FNDDS food to its ingredient-
level FPID rows, this loader joins through FNDDS input_food.csv:

    food_code  ->  fdc_id (via survey_fndds_food.csv)
    fdc_id     ->  [sr_code, gram_weight, ...] rows (via input_food.csv)
    sr_code    ->  FPID row of cup/oz pattern equivalents

This is an integration-surface stub. No consumer is wired in yet; the loader
exists so a future ingredient-decomposition feature has a stable API to land on
without re-deriving the join from scratch.

Raw inputs (relocated 2026-05-27 to backend/raw_*):
    backend/raw_fpid/FPID_1718.xls
    backend/raw_fndds/FoodData_Central_survey_food_csv_2024-10-31/{survey_fndds_food,input_food}.csv

Values in FPID's pattern columns are per 100 g of the SR ingredient — the same
convention as FPED. Use the published cup-eq -> grams constants in
`etl.build_cnf_heni_composition` if you need to convert to risk-factor masses.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

_THIS_DIR = Path(__file__).resolve().parent
# Walk up: heni_calculator/heni/data -> heni_calculator/heni -> heni_calculator -> backend
_BACKEND_ROOT = _THIS_DIR.parents[2]
_FPID_PATH = _BACKEND_ROOT / 'raw_fpid' / 'FPID_1718.xls'
_FNDDS_DIR = _BACKEND_ROOT / 'raw_fndds' / 'FoodData_Central_survey_food_csv_2024-10-31'
_SURVEY_FNDDS_PATH = _FNDDS_DIR / 'survey_fndds_food.csv'
_INPUT_FOOD_PATH = _FNDDS_DIR / 'input_food.csv'


@dataclass(frozen=True)
class FpidIngredient:
    """One ingredient of a finished FNDDS food, with its FPID pattern equivalents.

    Attributes
    ----------
    sr_code
        USDA SR (Standard Reference) ingredient code that joins to FPID.CODE.
    sr_description
        Human-readable ingredient name as recorded in FNDDS input_food.csv.
    seq_num
        Position of this ingredient in the parent FNDDS food's recipe.
    gram_weight
        Mass of this ingredient (grams) contributed to the parent food's recipe.
    pattern_equivalents
        Raw FPID pattern columns (e.g. ``'F_TOTAL (cup eq.)'``, ``'PF_MEAT (oz. eq.)'``).
        Values are per 100 g of the ingredient. Multiply by ``gram_weight / 100``
        to get the absolute contribution to the parent food.
    """
    sr_code: int
    sr_description: str
    seq_num: int
    gram_weight: float
    pattern_equivalents: Dict[str, float] = field(default_factory=dict)


_lock = threading.Lock()
_food_code_to_fdc_id: Optional[Dict[int, int]] = None
_input_food_by_fdc: Optional[Dict[int, List[Dict]]] = None
_fpid_by_code: Optional[Dict[int, Dict[str, float]]] = None


def _load_food_code_to_fdc_id() -> Dict[int, int]:
    """{food_code -> fdc_id} for the FNDDS survey foods bundle."""
    if not _SURVEY_FNDDS_PATH.exists():
        logger.warning('survey_fndds_food.csv missing at %s; FPID loader will return None for every lookup',
                       _SURVEY_FNDDS_PATH)
        return {}
    df = pd.read_csv(_SURVEY_FNDDS_PATH,
                     dtype={'fdc_id': 'int64', 'food_code': 'int64'},
                     usecols=['fdc_id', 'food_code'])
    out: Dict[int, int] = {int(r.food_code): int(r.fdc_id) for r in df.itertuples()}
    logger.info('FPID loader: indexed %d FNDDS food_code -> fdc_id pairs', len(out))
    return out


def _load_input_food_by_fdc() -> Dict[int, List[Dict]]:
    """{fdc_id -> [{sr_code, sr_description, seq_num, gram_weight}, ...]} for
    every FNDDS finished food's ingredients (those with a non-null sr_code).

    Rows with a null sr_code reference another FNDDS food via fdc_of_input_food
    (recipe-within-a-recipe). They are skipped here — recursive expansion is
    a future enhancement.
    """
    if not _INPUT_FOOD_PATH.exists():
        logger.warning('input_food.csv missing at %s; FPID loader will return None for every lookup',
                       _INPUT_FOOD_PATH)
        return {}
    df = pd.read_csv(_INPUT_FOOD_PATH,
                     dtype={'fdc_id': 'int64', 'seq_num': 'Int64',
                            'gram_weight': 'float64'},
                     usecols=['fdc_id', 'seq_num', 'sr_code', 'sr_description', 'gram_weight'])
    df = df[df['sr_code'].notna()].copy()
    df['sr_code'] = df['sr_code'].astype('int64')
    out: Dict[int, List[Dict]] = {}
    for r in df.itertuples():
        rows = out.setdefault(int(r.fdc_id), [])
        rows.append({
            'sr_code': int(r.sr_code),
            'sr_description': str(r.sr_description) if r.sr_description == r.sr_description else '',
            'seq_num': int(r.seq_num) if r.seq_num == r.seq_num else 0,
            'gram_weight': float(r.gram_weight) if r.gram_weight == r.gram_weight else 0.0,
        })
    for rows in out.values():
        rows.sort(key=lambda x: x['seq_num'])
    logger.info('FPID loader: indexed %d FNDDS fdc_id -> ingredient lists (%d ingredient rows)',
                len(out), int(df.shape[0]))
    return out


def _load_fpid_by_code() -> Dict[int, Dict[str, float]]:
    """{sr_code -> {pattern_column: value_per_100g}} for every FPID row."""
    if not _FPID_PATH.exists():
        logger.warning('FPID_1718.xls missing at %s; FPID loader will return empty rows',
                       _FPID_PATH)
        return {}
    df = pd.read_excel(_FPID_PATH, sheet_name='FPID_1718', header=0)
    df['CODE'] = df['CODE'].astype('int64')
    # Pattern columns are everything except CODE + DESCRIPTION. Coerce to float
    # so downstream code never gets a numpy scalar that fails equality checks.
    pattern_cols = [c for c in df.columns if c not in ('CODE', 'DESCRIPTION')]
    out: Dict[int, Dict[str, float]] = {}
    for _, row in df.iterrows():
        code = int(row['CODE'])
        out[code] = {c: float(row[c]) if pd.notna(row[c]) else 0.0
                     for c in pattern_cols}
    logger.info('FPID loader: indexed %d FPID rows across %d pattern columns',
                len(out), len(pattern_cols))
    return out


def _ensure_loaded() -> None:
    """Populate all three lookups under the lock; idempotent."""
    global _food_code_to_fdc_id, _input_food_by_fdc, _fpid_by_code
    if (_food_code_to_fdc_id is not None
            and _input_food_by_fdc is not None
            and _fpid_by_code is not None):
        return
    with _lock:
        if _food_code_to_fdc_id is None:
            _food_code_to_fdc_id = _load_food_code_to_fdc_id()
        if _input_food_by_fdc is None:
            _input_food_by_fdc = _load_input_food_by_fdc()
        if _fpid_by_code is None:
            _fpid_by_code = _load_fpid_by_code()


def get_fpid_ingredients_by_fdc_id(fdc_id: int) -> Optional[List[FpidIngredient]]:
    """Ingredient-level FPID rows for a finished FNDDS food, by fdc_id.

    Returns
    -------
    None
        If the fdc_id has no input_food rows (rare: malformed FNDDS entries,
        or finished foods whose ingredients are all recipe-within-a-recipe
        references rather than SR ingredients).
    list[FpidIngredient]
        One ``FpidIngredient`` per direct SR ingredient. Ingredients whose
        sr_code is missing from FPID get an empty ``pattern_equivalents`` dict
        — they are still returned so the caller sees the full ingredient list
        and can decide what to do with the gap.
    """
    _ensure_loaded()
    assert _input_food_by_fdc is not None
    assert _fpid_by_code is not None
    rows = _input_food_by_fdc.get(int(fdc_id))
    if not rows:
        return None
    out: List[FpidIngredient] = []
    for r in rows:
        sr = int(r['sr_code'])
        out.append(FpidIngredient(
            sr_code=sr,
            sr_description=r['sr_description'],
            seq_num=r['seq_num'],
            gram_weight=r['gram_weight'],
            pattern_equivalents=_fpid_by_code.get(sr, {}),
        ))
    return out


def get_fpid_ingredients_for_fndds(food_code: int) -> Optional[List[FpidIngredient]]:
    """Same as ``get_fpid_ingredients_by_fdc_id`` but keyed on the 8-digit FNDDS
    ``food_code`` instead of ``fdc_id`` — convenient when the caller is
    starting from the FPED side of the bridge (which exposes ``food_code``).
    """
    _ensure_loaded()
    assert _food_code_to_fdc_id is not None
    fdc_id = _food_code_to_fdc_id.get(int(food_code))
    if fdc_id is None:
        return None
    return get_fpid_ingredients_by_fdc_id(fdc_id)


def reset_for_test() -> None:
    """Reset the singleton caches (test-helper; not for production use)."""
    global _food_code_to_fdc_id, _input_food_by_fdc, _fpid_by_code
    with _lock:
        _food_code_to_fdc_id = None
        _input_food_by_fdc = None
        _fpid_by_code = None
