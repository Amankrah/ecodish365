"""
Food group → HSR category mapping via ``rust_core`` (word-boundary rules in Rust).
"""

from typing import Any, Dict

from ..models.category import Category
from ..constants.food_groups import FOOD_GROUPS
from ..providers.threshold_provider import rust_hsr_backend


class FoodGroupMapper:
    """CNF food group ID + name → ``Category``; logic is in Rust."""

    @classmethod
    def get_category(cls, food_group_id: int, food_name: str) -> Category:
        rust = rust_hsr_backend()
        return Category(rust.food_group_category(int(food_group_id), food_name))

    @classmethod
    def get_food_group_info(cls, food_group_id: int) -> Dict[str, str]:
        rust = rust_hsr_backend()
        cat = Category(rust.food_group_category(int(food_group_id), ""))
        return {
            "food_group_id": food_group_id,
            "food_group_name": FOOD_GROUPS.get(food_group_id, "Unknown"),
            "hsr_category": cat.value,
            "category_name": cat.name,
        }

    @classmethod
    def validate_category_assignment(
        cls, food_group_id: int, food_name: str, calculated_category: Category
    ) -> Dict[str, Any]:
        """Lightweight validation metadata (not part of Rust core scoring)."""
        confidence = 1.0
        warnings = []
        food_name_lower = food_name.lower()

        if food_group_id == 1:
            if calculated_category == Category.FOOD:
                if not any(
                    keyword in food_name_lower
                    for keyword in ["egg", "powder", "substitute"]
                ):
                    confidence = 0.7
                    warnings.append("Dairy product classified as regular food")

        if calculated_category == Category.BEVERAGE and food_group_id not in [9, 14]:
            confidence = 0.8
            warnings.append("Non-beverage group classified as beverage")

        return {
            "confidence": confidence,
            "warnings": warnings,
            "validated": confidence >= 0.8,
        }
