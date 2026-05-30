"""PLANETARY-1 — EAT-Lancet 2.0 food-system boundary overlay.

Takes the meal-level ReCiPe midpoints emitted by `life_cycle_assessment` and
reports each as a percentage of the per-capita-per-day food-system boundary
from E28 Table 2 (Rockström, Thilsted, Willett et al. 2025, *Lancet* 406:1625-1700,
Table 2 p. 1640). v1 covers 3 of 9 boundaries (climate, land, water); the other
6 surface as ``available=False`` placeholders pre-wired for v2 when
TODO-CODE-LCA-2 lands the licensed AGRIBALYSE-LCI re-scored under ReCiPe CFs.

Stock-vs-flux reconciliation: E28's land boundary is a STOCK (total agricultural
area). ReCiPe `Land use` is a FLUX (m²·yr/serving). We treat the per-capita
allocation of the global stock as a comparable per-capita-per-day flux — the
standard LCA-vs-planetary-boundary reconciliation, documented as an explicit
methodology note in researcher / policy mode.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Mapping, Optional

logger = logging.getLogger(__name__)


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_PATH = os.path.join(
    _THIS_DIR, "..", "data", "eat_lancet_2025_table_2.json",
)


_CACHED_TABLE: Optional[Dict[str, Any]] = None


def _load_table() -> Dict[str, Any]:
    """Module-cached load of the published Table 2 constants."""
    global _CACHED_TABLE
    if _CACHED_TABLE is None:
        with open(_DATA_PATH, "r", encoding="utf-8") as fh:
            _CACHED_TABLE = json.load(fh)
    return _CACHED_TABLE


def get_per_capita_daily_budgets() -> Dict[str, Optional[float]]:
    """Return per-capita-per-day budgets for the 9 control variables.

    Covered (3) yield a real number; uncovered (6) yield ``None``. Useful for
    frontend reference rendering even when the matching meal value is absent.
    """
    table = _load_table()
    pop = float(table["per_capita_derivation"]["world_population"])
    days = float(table["per_capita_derivation"]["days_per_year"])
    out: Dict[str, Optional[float]] = {}
    for row in table["boundaries"]:
        if not row["available_in_v1"]:
            out[row["key"]] = None
            continue
        annual = float(row["global_boundary_per_year"])
        out[row["key"]] = annual / (pop * days)
    return out


# ReCiPe midpoint key → boundary entry key. We look up the meal's value
# under either of these two common shapes (alphabetic-case variations seen
# in tests). Lookup is forgiving — missing keys become ``None``.
_RECIPE_KEY_VARIANTS: Dict[str, str] = {
    "Global warming": "climate_change",
    "global warming": "climate_change",
    "Land use": "land_use",
    "land use": "land_use",
    "Water consumption": "water_consumption",
    "water consumption": "water_consumption",
}


def _read_meal_value(meal_impacts: Mapping[str, Any], recipe_key: str) -> Optional[float]:
    """Read a ReCiPe midpoint value from the meal-impacts dict, tolerant of
    case variations and missing keys."""
    if not isinstance(meal_impacts, Mapping):
        return None
    # First try the exact key as stored on the row.
    if recipe_key in meal_impacts:
        try:
            v = float(meal_impacts[recipe_key])
            return v if v >= 0 else None
        except (TypeError, ValueError):
            return None
    # Fall back to a case-insensitive search.
    target_lower = recipe_key.lower()
    for k, v in meal_impacts.items():
        if isinstance(k, str) and k.lower() == target_lower:
            try:
                fv = float(v)
                return fv if fv >= 0 else None
            except (TypeError, ValueError):
                return None
    return None


def compute_planetary_boundary_shares(
    meal_impacts: Mapping[str, Any],
    *,
    world_population: Optional[int] = None,
    days_per_year: Optional[int] = None,
) -> Dict[str, Any]:
    """Compute per-meal share of per-capita-per-day food-system planetary budgets.

    Args:
        meal_impacts: ReCiPe midpoints for one meal/day, keyed by ReCiPe label
            (e.g. ``{'Global warming': 0.45, 'Land use': 3.2, 'Water consumption': 0.05}``).
            Extra keys are ignored; missing keys collapse to ``available=False``.
            Caller is responsible for choosing the appropriate basis (per-serving
            for a one-meal share; per-day-total for a recall-day share).
        world_population: Override world-population denominator (default reads from JSON).
        days_per_year: Override days-per-year denominator (default 365).

    Returns:
        ``{
            'shares': [{boundary_row + meal_value + per_capita_daily_budget +
                        share_of_daily_budget_pct + status}, ...],   # 9 rows preserving table order
            'n_covered': 3,
            'n_total': 9,
            'population_assumption': 8_000_000_000,
            'days_per_year': 365,
            'citation': {...},
            'method_note': "...",
         }``

    Stable contract:
        - Every row has ``key``, ``label``, ``unit``, ``available``.
        - Available rows additionally have ``meal_value``, ``per_capita_daily_budget``,
          ``share_of_daily_budget_pct``, ``method_note``.
        - Unavailable rows additionally have ``reason``.
    """
    table = _load_table()
    pop = float(world_population or table["per_capita_derivation"]["world_population"])
    days = float(days_per_year or table["per_capita_derivation"]["days_per_year"])

    shares = []
    for row in table["boundaries"]:
        key = row["key"]
        base = {
            "key": key,
            "label": row["label"],
            "control_variable": row["control_variable"],
            "unit": row["unit"],
            "available": bool(row["available_in_v1"]),
            "global_boundary_per_year": float(row["global_boundary_per_year"]),
            "global_boundary_source": row["global_boundary_source"],
            "current_food_system_contribution": row["current_food_system_contribution"],
        }
        if not row["available_in_v1"]:
            base["reason"] = row.get("reason_unavailable",
                                     "Not in v1 ReCiPe consumed-midpoint scope.")
            shares.append(base)
            continue

        # Covered: compute the meal share.
        recipe_key = row["recipe_midpoint_key"]
        per_capita_daily = base["global_boundary_per_year"] / (pop * days)
        meal_value = _read_meal_value(meal_impacts, recipe_key)
        base["recipe_midpoint_key"] = recipe_key
        base["per_capita_daily_budget"] = per_capita_daily
        base["method_note"] = row["method_note"]
        if meal_value is None:
            base["meal_value"] = None
            base["share_of_daily_budget_pct"] = None
            base["reason"] = (
                f"Meal-impacts dict missing or invalid value for ReCiPe key "
                f"'{recipe_key}'."
            )
        else:
            base["meal_value"] = meal_value
            base["share_of_daily_budget_pct"] = (
                100.0 * meal_value / per_capita_daily if per_capita_daily > 0 else None
            )
        shares.append(base)

    n_covered = sum(1 for r in shares if r["available"])
    return {
        "shares": shares,
        "n_covered": n_covered,
        "n_total": len(shares),
        "population_assumption": int(pop),
        "days_per_year": int(days),
        "citation": table["source"],
        "method_note": table["per_capita_derivation"]["rationale"],
    }


# --- Audience-aware explanations -----------------------------------------


def _format_pct(v: Optional[float]) -> str:
    if v is None:
        return "—"
    if v >= 100.0:
        return f"{v:.0f} %"
    if v >= 10.0:
        return f"{v:.1f} %"
    return f"{v:.2f} %"


def build_planetary_explanations(
    shares: Dict[str, Any],
    user_type: str,
) -> Dict[str, str]:
    """Return the audience-aware explanation pack for the planetary overlay.

    Mirrors the pattern used by other AUDIENCE-CODE-1 explanation builders
    (hsr_explanations.py, hefi_explanations.py, etc.): a dict with
    {title, headline, message, mandatory_caveat} the frontend renders verbatim.
    """
    user_type = user_type if user_type in ("individual", "researcher", "policy") else "individual"

    # Pull headline numbers for the 3 covered boundaries.
    covered = {r["key"]: r for r in shares["shares"] if r["available"]}
    climate_pct = covered.get("climate_change", {}).get("share_of_daily_budget_pct")
    land_pct = covered.get("land_use", {}).get("share_of_daily_budget_pct")
    water_pct = covered.get("water_consumption", {}).get("share_of_daily_budget_pct")

    if user_type == "individual":
        return {
            "title": "Your share of a daily planet budget",
            "headline": (
                f"Climate {_format_pct(climate_pct)} · "
                f"Land {_format_pct(land_pct)} · "
                f"Water {_format_pct(water_pct)} "
                "of one person's fair daily share."
            ),
            "message": (
                "These percentages compare your meal or day to what one person "
                "would get if global food limits were split equally. Lower is "
                "better. Above 100% means that if everyone ate this way every "
                "day, we would exceed safe limits."
            ),
            "mandatory_caveat": (
                "Equal shares are a simple way to compare meals, not a rule "
                "about who should eat what. In reality, wealthier countries "
                "drive much of the pressure. We currently show 3 of 9 "
                "environmental categories because the rest need data we do "
                "not yet have for individual foods."
            ),
        }

    if user_type == "researcher":
        return {
            "title": "Per-capita-per-day food-system boundary share",
            "headline": (
                f"Climate {_format_pct(climate_pct)} · "
                f"Land {_format_pct(land_pct)} · "
                f"Water {_format_pct(water_pct)} "
                "of per-capita-per-day food-system boundary."
            ),
            "message": (
                "Per-capita-per-day budgets are computed as the published global food-system "
                "boundary (E28 Table 2, p. 1640) divided by world population (8 × 10⁹) and "
                "365 days. Climate: 5 Gt CO₂e/yr → 1.712 kg CO₂e/p/day. Land use: 48 × 10¹² m² "
                "stock allocated as 16.44 m²·yr/p/day. Water: 2000 km³/yr → 0.685 m³/p/day. "
                "Land is a stock in E28; we treat the per-capita allocation as a comparable "
                "flux for the m²·yr/serving values our LCA emits (standard LCA-vs-planetary-"
                "boundary reconciliation)."
            ),
            "mandatory_caveat": (
                "Coverage is 3 of 9 boundaries. Nitrogen surplus, phosphorus loss, biosphere "
                "integrity (HANPP), stratospheric ozone (N₂O), ocean acidification, and novel-"
                "entity (pesticide) pressures are not in the v1 ReCiPe consumed-midpoint scope. "
                "Wiring N₂O and eutrophication midpoints through is in scope for v2 "
                "(TODO-CODE-LCA-2). Citation: Rockström et al. 2025, Lancet 406:1625-1700, "
                "Table 2 p. 1640, doi:10.1016/S0140-6736(25)01201-2."
            ),
        }

    # policy
    return {
        "title": "Food-system boundary share for population framing",
        "headline": (
            f"Climate {_format_pct(climate_pct)} · "
            f"Land {_format_pct(land_pct)} · "
            f"Water {_format_pct(water_pct)} "
            "of per-capita-per-day food-system boundary."
        ),
        "message": (
            "Useful for procurement and dietary-guideline analysis: any meal whose climate "
            "share exceeds 100 % is a pattern incompatible with the EAT-Lancet 2.0 food-"
            "system carbon boundary at a per-capita-equal allocation. Procurement programmes "
            "can use the three covered shares (climate / land / water) as a unified planetary-"
            "pressure axis alongside HEFI / FCS nutritional adequacy."
        ),
        "mandatory_caveat": (
            "Per-capita-equal allocation is a modelling convenience, not a normative "
            "claim. EAT-Lancet 2.0 itself emphasises (Section 3, p. 1661) that the global "
            "richest 30 % drives over 70 % of food-system pressures. Country / income-bracket "
            "differentiated boundaries are an open research question this overlay does not "
            "attempt to answer. Only 3 of 9 planetary boundaries are currently scored."
        ),
    }
