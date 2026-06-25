"""DRI compendium loader for the research deep-dive.

Reads `backend/api/data/dri_compendium.json` (built by the ETL at
`backend.api.services.etl.build_dri_compendium`) and exposes a small,
documented surface to the deep-dive endpoint and the population harness.

Three primitives:

* `get_life_stage(age_years, sex, pregnancy_status, lactation_status)`
  resolves a (age, sex, P, L) tuple to the canonical life-stage code
  used as a key in the compendium. Returns None when no life-stage cell
  is published for the supplied tuple (e.g. the child / infant cells
  that ship pending curation).
* `percent_ear`, `percent_rda`, `percent_ai`, `percent_ul`
  return the percent-of-reference for one amount, one nutrient, one
  life-stage. Each returns None when the reference is not published
  (the conservative null behaviour the EAR cut-point method already
  expects: a nutrient with no EAR cannot be assessed for adequacy by
  the cut-point method, so no value is fabricated).
* `dri_panel_for_meal(nutrient_totals, life_stage)` returns one
  `NutrientDriRow` per nutrient with all four reference flags populated,
  plus the AMDR block for macronutrients and the sodium CDRR flag.

Unit convention. The DRI cells are stored in the same unit as the CNF
nutrient registry uses for the same NutrientID. The loader does not
attempt unit conversion; if a caller passes an amount in a different
unit, the percent-of-reference will be wrong. The deep-dive endpoint
sources amounts from the shared meal nutrient aggregator, which always
returns CNF-registry units, so the convention holds.
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_PATH = Path(__file__).resolve().parent.parent / 'data' / 'dri_compendium.json'

_lock = threading.Lock()
_cache: Optional[Dict[str, Any]] = None


def _load() -> Dict[str, Any]:
    if not _PATH.exists():
        logger.warning('DRI compendium not present at %s; deep-dive %%EAR / %%RDA unavailable', _PATH)
        return {'_meta': {}, 'life_stages': {}, 'nutrients': {}}
    try:
        with open(_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001
        logger.warning('DRI compendium unreadable: %s', exc)
        return {'_meta': {}, 'life_stages': {}, 'nutrients': {}}


def _ensure() -> Dict[str, Any]:
    global _cache
    if _cache is not None:
        return _cache
    with _lock:
        if _cache is None:
            _cache = _load()
    return _cache


# Age bands used to bucket age_years into the life-stage codes.
# Tuple form: (age_low_inclusive, age_high_inclusive, sex, code)
_AGE_BANDS_NONPREG: List = [
    (0.0,   0.5,   'either', 'infants_0_6m'),
    (0.6,   1.0,   'either', 'infants_7_12m'),
    (1.0,   3.9,   'either', 'children_1_3y'),
    (4.0,   8.9,   'either', 'children_4_8y'),
    (9.0,  13.9,   'male',   'males_9_13y'),
    (14.0, 18.9,   'male',   'males_14_18y'),
    (19.0, 30.9,   'male',   'males_19_30y'),
    (31.0, 50.9,   'male',   'males_31_50y'),
    (51.0, 70.9,   'male',   'males_51_70y'),
    (71.0, 130.0,  'male',   'males_71plus'),
    (9.0,  13.9,   'female', 'females_9_13y'),
    (14.0, 18.9,   'female', 'females_14_18y'),
    (19.0, 30.9,   'female', 'females_19_30y'),
    (31.0, 50.9,   'female', 'females_31_50y'),
    (51.0, 70.9,   'female', 'females_51_70y'),
    (71.0, 130.0,  'female', 'females_71plus'),
]

_AGE_BANDS_PREG: List = [
    (14.0, 18.9, 'pregnant_14_18y'),
    (19.0, 30.9, 'pregnant_19_30y'),
    (31.0, 50.9, 'pregnant_31_50y'),
]

_AGE_BANDS_LACT: List = [
    (14.0, 18.9, 'lactating_14_18y'),
    (19.0, 30.9, 'lactating_19_30y'),
    (31.0, 50.9, 'lactating_31_50y'),
]


def get_life_stage(
    age_years: Optional[float],
    sex: Optional[str],
    pregnancy_status: Optional[str] = None,
    lactation_status: Optional[str] = None,
) -> Optional[str]:
    """Resolve (age, sex, P, L) to a canonical life-stage code.

    Returns None when the supplied tuple does not match any published
    life-stage (e.g. age unknown, or sex unknown for an adult).

    Pregnancy and lactation cells take precedence over the matching
    non-pregnant non-lactating cell (a pregnant 30-year-old female maps
    to `pregnant_19_30y`, not `females_19_30y`). The deep-dive endpoint
    surfaces both the resolved life-stage code and the (age, sex, P, L)
    inputs back to the response for transparency.
    """
    if age_years is None:
        return None
    age = float(age_years)
    sex_norm = (sex or '').strip().lower() if isinstance(sex, str) else ''
    preg = (pregnancy_status or '').strip().lower() if isinstance(pregnancy_status, str) else ''
    lact = (lactation_status or '').strip().lower() if isinstance(lactation_status, str) else ''

    preg_active = preg not in ('', 'not_pregnant', 'no', 'false', 'none')
    lact_active = lact not in ('', 'not_lactating', 'no', 'false', 'none')

    if preg_active and sex_norm == 'female':
        for lo, hi, code in _AGE_BANDS_PREG:
            if lo <= age <= hi:
                return code
    if lact_active and sex_norm == 'female':
        for lo, hi, code in _AGE_BANDS_LACT:
            if lo <= age <= hi:
                return code

    for lo, hi, band_sex, code in _AGE_BANDS_NONPREG:
        if not (lo <= age <= hi):
            continue
        if band_sex == 'either':
            return code
        if band_sex == sex_norm:
            return code
    return None


def _cell(nutrient_id: int, life_stage: str) -> Optional[Dict[str, Optional[float]]]:
    """Return the (EAR/RDA/AI/UL) cell dict for one nutrient at one
    life-stage, or None when the cell is not published."""
    comp = _ensure()
    nut = comp.get('nutrients', {}).get(str(int(nutrient_id)))
    if nut is None:
        return None
    return nut.get('cells', {}).get(life_stage)


def _ref(nutrient_id: int, life_stage: str, key: str) -> Optional[float]:
    cell = _cell(nutrient_id, life_stage)
    if not cell:
        return None
    v = cell.get(key)
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _pct(amount: Optional[float], ref: Optional[float]) -> Optional[float]:
    if amount is None or ref is None or ref <= 0:
        return None
    try:
        return float(amount) / ref * 100.0
    except (TypeError, ValueError):
        return None


def percent_ear(nutrient_id: int, amount: float, life_stage: str) -> Optional[float]:
    return _pct(amount, _ref(nutrient_id, life_stage, 'EAR'))


def percent_rda(nutrient_id: int, amount: float, life_stage: str) -> Optional[float]:
    return _pct(amount, _ref(nutrient_id, life_stage, 'RDA'))


def percent_ai(nutrient_id: int, amount: float, life_stage: str) -> Optional[float]:
    return _pct(amount, _ref(nutrient_id, life_stage, 'AI'))


def percent_ul(nutrient_id: int, amount: float, life_stage: str) -> Optional[float]:
    return _pct(amount, _ref(nutrient_id, life_stage, 'UL'))


def adequacy_flag(
    pct_ear: Optional[float],
    pct_rda: Optional[float],
    pct_ai: Optional[float],
    pct_ul: Optional[float],
) -> str:
    """Distil the four percent-of-reference flags to a single status the UI
    can colour and the manuscript can table directly.

    Categories:
      * `below_ear`            : intake below EAR, classical inadequate
      * `between_ear_rda`      : between EAR and RDA, individually sufficient
                                   probability but population proportion has
                                   non-trivial inadequacy share
      * `at_or_above_rda`      : intake at or above RDA
      * `below_ai`             : for nutrients with only AI; intake below AI
      * `at_or_above_ai`       : for nutrients with only AI; intake at or above AI
      * `at_or_above_ul`       : intake at or above UL (independent of the
                                   adequacy axis)
      * `no_reference`         : neither EAR nor AI is published
    """
    ul_breach = (pct_ul is not None and pct_ul >= 100.0)
    if pct_ear is not None:
        if pct_ear < 100.0:
            return 'below_ear_ul_breach' if ul_breach else 'below_ear'
        if pct_rda is not None and pct_rda >= 100.0:
            return 'at_or_above_rda_ul_breach' if ul_breach else 'at_or_above_rda'
        return 'between_ear_rda_ul_breach' if ul_breach else 'between_ear_rda'
    if pct_ai is not None:
        if pct_ai < 100.0:
            return 'below_ai_ul_breach' if ul_breach else 'below_ai'
        return 'at_or_above_ai_ul_breach' if ul_breach else 'at_or_above_ai'
    return 'at_or_above_ul' if ul_breach else 'no_reference'


@dataclass
class NutrientDriRow:
    nutrient_id: int
    name: str
    unit: str
    life_stage: str
    amount: float
    ear: Optional[float]
    rda: Optional[float]
    ai: Optional[float]
    ul: Optional[float]
    pct_ear: Optional[float]
    pct_rda: Optional[float]
    pct_ai: Optional[float]
    pct_ul: Optional[float]
    adequacy_flag: str
    cdrr_value: Optional[float] = None
    cdrr_flag: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        def r(v):
            return None if v is None else round(float(v), 4)
        return {
            'nutrient_id': self.nutrient_id,
            'name': self.name,
            'unit': self.unit,
            'life_stage': self.life_stage,
            'amount': r(self.amount),
            'ear': r(self.ear),
            'rda': r(self.rda),
            'ai': r(self.ai),
            'ul': r(self.ul),
            'pct_ear': r(self.pct_ear),
            'pct_rda': r(self.pct_rda),
            'pct_ai': r(self.pct_ai),
            'pct_ul': r(self.pct_ul),
            'adequacy_flag': self.adequacy_flag,
            'cdrr_value': r(self.cdrr_value),
            'cdrr_flag': self.cdrr_flag,
            'notes': self.notes,
        }


def dri_panel_for_meal(
    nutrient_amounts: Dict[int, float],
    life_stage: Optional[str],
) -> List[NutrientDriRow]:
    """Produce one DRI row per published nutrient.

    `nutrient_amounts` is `{nutrient_id: amount_in_cnf_unit}` (the meal-level
    summed value from `meal_nutrient_aggregator.aggregate_meal_nutrients`).
    `life_stage` is the canonical code from `get_life_stage(...)`. When
    `life_stage` is None, the row carries the amount but every percent
    field is None and the adequacy flag is `no_reference`.
    """
    comp = _ensure()
    nutrients_block = comp.get('nutrients', {})
    rows: List[NutrientDriRow] = []

    for nid_str, nut in nutrients_block.items():
        try:
            nid = int(nid_str)
        except (TypeError, ValueError):
            continue
        amount = float(nutrient_amounts.get(nid, 0.0) or 0.0)
        if life_stage is None:
            rows.append(NutrientDriRow(
                nutrient_id=nid, name=nut.get('name', ''),
                unit=nut.get('unit', ''),
                life_stage='unknown',
                amount=amount,
                ear=None, rda=None, ai=None, ul=None,
                pct_ear=None, pct_rda=None, pct_ai=None, pct_ul=None,
                adequacy_flag='no_reference',
                notes=['life-stage not supplied; %DRI not computed'],
            ))
            continue
        cell = nut.get('cells', {}).get(life_stage)
        if not cell:
            rows.append(NutrientDriRow(
                nutrient_id=nid, name=nut.get('name', ''),
                unit=nut.get('unit', ''),
                life_stage=life_stage,
                amount=amount,
                ear=None, rda=None, ai=None, ul=None,
                pct_ear=None, pct_rda=None, pct_ai=None, pct_ul=None,
                adequacy_flag='no_reference',
                notes=['life-stage cell pending curation'],
            ))
            continue
        ear = cell.get('EAR'); rda = cell.get('RDA')
        ai = cell.get('AI'); ul = cell.get('UL')
        pe = _pct(amount, ear); pr = _pct(amount, rda)
        pa = _pct(amount, ai); pu = _pct(amount, ul)
        flag = adequacy_flag(pe, pr, pa, pu)

        # CDRR (NASEM 2019). The block can be either:
        #   - global, with `cdrr_mg_per_day` (sodium pattern)
        #   - per-life-stage, with `by_life_stage[life_stage_code]` (potassium pattern)
        # The `direction` field disambiguates the flag semantics:
        #   - 'cap'    (sodium): intake AT/ABOVE the CDRR is risk-increasing
        #   - 'target' (K, NASEM 2019 Ch. 6): intake AT/ABOVE the CDRR is risk-reducing
        # When `direction` is missing on a legacy block, defaults to 'cap'
        # (the original sodium-only assumption).
        cdrr_block = nut.get('cdrr')
        cdrr_value = None
        cdrr_flag = None
        if cdrr_block is not None:
            direction = str(cdrr_block.get('direction') or 'cap').lower()
            by_ls = cdrr_block.get('by_life_stage') or {}
            if isinstance(by_ls, dict) and life_stage in by_ls:
                cdrr_value = float(by_ls.get(life_stage) or 0.0) or None
            else:
                cdrr_value = float(cdrr_block.get('cdrr_mg_per_day') or 0.0) or None
            if cdrr_value is not None and amount > 0:
                if direction == 'target':
                    # Higher is better (potassium): meeting target = good.
                    cdrr_flag = 'meets_cdrr_target' if amount >= cdrr_value else 'below_cdrr_target'
                else:
                    # Cap (sodium): lower is better.
                    cdrr_flag = 'above_cdrr' if amount >= cdrr_value else 'at_or_below_cdrr'

        rows.append(NutrientDriRow(
            nutrient_id=nid, name=nut.get('name', ''),
            unit=nut.get('unit', ''),
            life_stage=life_stage,
            amount=amount,
            ear=ear, rda=rda, ai=ai, ul=ul,
            pct_ear=pe, pct_rda=pr, pct_ai=pa, pct_ul=pu,
            adequacy_flag=flag,
            cdrr_value=cdrr_value, cdrr_flag=cdrr_flag,
        ))
    return rows


def get_amdr_ranges() -> Dict[str, Dict[str, float]]:
    """Return the AMDR pct-kcal block (carbohydrate, protein, fat, etc.)."""
    comp = _ensure()
    return comp.get('_meta', {}).get('amdr_block', {})


def get_compendium_meta() -> Dict[str, Any]:
    """Return the `_meta` block for the deep-dive provenance pane."""
    comp = _ensure()
    return dict(comp.get('_meta', {}))


def all_life_stages() -> Dict[str, Dict[str, Any]]:
    """Full `life_stages` registry for the UI selector."""
    comp = _ensure()
    return dict(comp.get('life_stages', {}))


def reset_for_test() -> None:
    """Drop the cached compendium so a clean reload happens on next call."""
    global _cache
    with _lock:
        _cache = None
