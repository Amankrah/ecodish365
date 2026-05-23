"""
HENI orchestration: CNF + risk-factor extraction in Python; **DALY / μDALY math in** ``rust_core.heni``.

Use this module from Django views and meal services instead of duplicating integrator wiring.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .calculator.heni_calculator import HENICalculator
from .database.cnf_integrator import HENICNFIntegrator, create_heni_cnf_integrator
from .models.ingredient import Ingredient

_heni_integrator: Optional[HENICNFIntegrator] = None


def _default_cnf_dir() -> str:
    try:
        from django.conf import settings

        if getattr(settings, "configured", False):
            return str(settings.CNF_FOLDER)
    except Exception:
        pass
    import os

    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, "raw_cnf")


def get_cnf_integrator() -> HENICNFIntegrator:
    """Process-wide HENI CNF integrator (same CNF folder as Django ``CNF_FOLDER`` when configured)."""
    global _heni_integrator
    if _heni_integrator is None:
        _heni_integrator = create_heni_cnf_integrator(_default_cnf_dir())
    return _heni_integrator


def resolve_llm_api_key(explicit: Optional[str] = None) -> str:
    if explicit:
        return explicit
    try:
        from django.conf import settings

        if getattr(settings, "configured", False):
            v = getattr(settings, "OPENAI_API_KEY", None)
            if v:
                return str(v)
    except Exception:
        pass
    import os
    return os.environ.get("OPENAI_API_KEY", "")


def calculate_meal_heni_response(
    ingredients: List[Ingredient],
    *,
    llm_api_key: Optional[str] = None,
    age_group: str = "adult_male",
    cnf_integrator: Optional[HENICNFIntegrator] = None,
) -> Dict[str, Any]:
    """
    Public API-shaped dict (``heni_scores``, ``meal_composition``, …).

    Scoring runs in ``rust_core.heni`` via :class:`HENICalculator`.
    """
    integrator = (
        cnf_integrator
        or (ingredients[0].cnf_integrator if ingredients else None)
        or get_cnf_integrator()
    )
    calc = HENICalculator(integrator, resolve_llm_api_key(llm_api_key), age_group=age_group)
    return calc.calculate_meal_heni(ingredients)


def meal_api_rows_to_ingredients(
    meal_data: List[Dict[str, Any]],
    *,
    integrator: Optional[HENICNFIntegrator] = None,
) -> List[Ingredient]:
    """API rows: ``food_id``, ``amount``, ``unit`` (same as ``/api/heni/calculate/``)."""
    integ = integrator or get_cnf_integrator()
    return [
        Ingredient(
            food_id=int(item["food_id"]),
            amount=float(item["amount"]),
            unit=str(item.get("unit", "g")),
            cnf_integrator=integ,
        )
        for item in meal_data
    ]


def ingredients_from_meal_food_items(
    food_items: List[Dict[str, Any]],
    grams_from_item: Callable[[Dict[str, Any]], float],
    *,
    integrator: Optional[HENICNFIntegrator] = None,
) -> List[Ingredient]:
    """Meal model rows: ``food_id``, ``quantity``, ``unit`` → pass a gram resolver (e.g. ``_convert_to_grams``)."""
    integ = integrator or get_cnf_integrator()
    return [
        Ingredient(
            food_id=int(item["food_id"]),
            amount=float(grams_from_item(item)),
            unit="g",
            cnf_integrator=integ,
        )
        for item in food_items
    ]
