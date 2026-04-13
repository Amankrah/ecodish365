"""Scientific meal categorization via ``rust_core``."""

from typing import Any, Dict, List, Tuple
from dataclasses import dataclass

from ..models.food import Food
from ..models.category import Category
from ..providers.threshold_provider import rust_hsr_backend


@dataclass
class ScientificCategorizationResult:
    """Result of scientific categorization analysis"""

    recommended_category: Category
    confidence: float
    reasoning: List[str]
    nutritional_rationale: str
    alternative_categories: List[Tuple[Category, float, str]]
    scientific_factors: Dict[str, Any]


class MealCategorizer:
    """Delegates to Rust ``determine_scientific_category_meal``."""

    @classmethod
    def determine_scientific_category(
        cls, foods: List[Food]
    ) -> ScientificCategorizationResult:
        rust = rust_hsr_backend()
        d = rust.determine_scientific_category_meal(foods)
        alternatives = [
            (Category(x[0]), float(x[1]), str(x[2]))
            for x in d["alternative_categories"]
        ]
        return ScientificCategorizationResult(
            recommended_category=Category(d["recommended_category"]),
            confidence=float(d["confidence"]),
            reasoning=list(d["reasoning"]),
            nutritional_rationale=str(d["nutritional_rationale"]),
            alternative_categories=alternatives,
            scientific_factors=dict(d["scientific_factors"]),
        )
