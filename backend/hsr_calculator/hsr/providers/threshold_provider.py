"""
Threshold Provider — HSR thresholds and point math via ``rust_core`` only.

Install: ``cd backend/rust_core && maturin develop`` (requires a virtualenv).
"""

import logging
from typing import List
from dataclasses import dataclass

from ..models.category import Category

logger = logging.getLogger(__name__)

try:
    from rust_core import hsr as _rust_hsr  # type: ignore
except ImportError as exc:
    raise ImportError(
        "HSR requires the rust_core native module. Build and install with:\n"
        "  cd backend/rust_core && maturin develop"
    ) from exc

logger.info("HSR: using rust_core backend")


def rust_hsr_backend():
    """The ``rust_core.hsr`` module (always available once this package loads)."""
    return _rust_hsr


@dataclass
class NutritionalContext:
    """Context information for threshold adjustments"""

    is_natural_sugar_dominant: bool = False
    has_added_sugars: bool = False
    satiety_index: float = 1.0
    processing_level: str = "minimally_processed"
    liquid_percentage: float = 0.0
    fiber_density: float = 0.0
    protein_quality_score: float = 1.0
    fvnl_naturalness: float = 1.0


@dataclass
class HSRThresholds:
    """HSR threshold configuration"""

    energy: List[float]
    sugar: List[float]
    saturated_fat: List[float]
    sodium: List[float]
    fvnl: List[float]
    protein: List[float]
    fiber: List[float]
    star_thresholds: List[float]


class ThresholdProvider:
    """HSR thresholds and helpers; all computation is in Rust."""

    @classmethod
    def get_thresholds(cls, category: Category) -> HSRThresholds:
        d = _rust_hsr.get_thresholds(category.value)
        return HSRThresholds(
            energy=list(d["energy"]),
            sugar=list(d["sugar"]),
            saturated_fat=list(d["saturated_fat"]),
            sodium=list(d["sodium"]),
            fvnl=list(d["fvnl"]),
            protein=list(d["protein"]),
            fiber=list(d["fiber"]),
            star_thresholds=list(d["star_thresholds"]),
        )

    @classmethod
    def get_category_from_food(cls, food_name: str, food_group_id: int) -> Category:
        """Same rules as ``FoodGroupMapper.get_category`` (Rust)."""
        from ..utils.food_group_mapper import FoodGroupMapper

        return FoodGroupMapper.get_category(food_group_id, food_name)

    @classmethod
    def calculate_hsr_points(cls, value: float, thresholds: List[float]) -> int:
        return _rust_hsr.calculate_hsr_points(float(value), [float(t) for t in thresholds])

    @classmethod
    def convert_score_to_stars(cls, final_score: int, star_thresholds: List[float]) -> float:
        return _rust_hsr.convert_score_to_stars(
            int(final_score), [float(t) for t in star_thresholds]
        )
