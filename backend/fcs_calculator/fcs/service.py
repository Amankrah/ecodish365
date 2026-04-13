"""FCS pipeline for Django and scripts: CNF → ``FoodItem`` → ``rust_core.fcs``."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fcs.analyzers.food_analyzer import FoodAnalyzer
from fcs.models.food_item import FoodItem
from fcs.utils.cnf_data_integrator import EnhancedCNFDataIntegrator, create_cnf_integrator

_integrator: Optional[EnhancedCNFDataIntegrator] = None
_analyzer = FoodAnalyzer()


def _cnf_dir_for_runtime() -> Optional[str]:
    try:
        from django.conf import settings

        if getattr(settings, "configured", False):
            return str(settings.CNF_FOLDER)
    except Exception:
        pass
    return None


def get_cnf_integrator() -> EnhancedCNFDataIntegrator:
    """One integrator per process; inner CNF pipeline is already a singleton."""
    global _integrator
    if _integrator is None:
        _integrator = create_cnf_integrator(_cnf_dir_for_runtime())
    return _integrator


def extract_and_score(food_ids: List[int], display_name: str) -> Tuple[FoodItem, Dict[str, Any]]:
    food_item = FoodItem(display_name)
    get_cnf_integrator().extract_nutrients_enhanced(food_ids, food_item)
    summary = _analyzer.analyze_food_item(food_item)
    return food_item, summary


def score_food_item(food_item: FoodItem) -> Dict[str, Any]:
    return _analyzer.analyze_food_item(food_item)


def per_domain_attribute_breakdown(food_item: FoodItem) -> Dict[str, Dict[str, Any]]:
    """Non-zero attributes only; per-attribute scores via Rust."""
    breakdown: Dict[str, Dict[str, Any]] = {}
    for domain, attributes in food_item.attributes.items():
        domain_scores: Dict[str, Any] = {}
        for attribute, value in attributes.items():
            if value <= 0:
                continue
            try:
                attribute_type = FoodAnalyzer.get_attribute_type(attribute)
                score = FoodAnalyzer.score_attribute(value, attribute, attribute_type)
                domain_scores[attribute] = {
                    "value": round(float(value), 3),
                    "score": round(float(score), 2),
                    "type": attribute_type.name,
                }
            except ValueError:
                continue
        if domain_scores:
            breakdown[domain] = domain_scores
    return breakdown


def domain_mean_scores(food_item: FoodItem) -> Dict[str, float]:
    """Simple mean of per-attribute scores per domain (comparison endpoint)."""
    raw: Dict[str, List[float]] = {domain: [] for domain in food_item.attributes.keys()}
    for domain, attributes in food_item.attributes.items():
        for attribute, value in attributes.items():
            try:
                attribute_type = FoodAnalyzer.get_attribute_type(attribute)
                score = FoodAnalyzer.score_attribute(value, attribute, attribute_type)
                raw[domain].append(float(score))
            except ValueError:
                continue
    out: Dict[str, float] = {}
    for domain, scores in raw.items():
        out[domain] = round(sum(scores) / len(scores), 2) if scores else 0.0
    return out


def cnf_food_description(integrator: EnhancedCNFDataIntegrator, food_id: int) -> str:
    try:
        df = integrator.cnf_pipeline.food_name_df
        row = df[df["FoodID"] == food_id]
        if not row.empty:
            return str(row["FoodDescription"].iloc[0])
    except Exception:
        pass
    return f"Food ID {food_id}"
