"""
Food group → HSR category mapping via ``rust_core`` (word-boundary rules in Rust).

FDC-MULTI-SOURCE (2026-06-26): WAFCT and FDC FoodGroupIDs are translated to
their CNF-equivalent group ID via the canonical-category bridge before
delegating to Rust, so the kernel's hard-coded `match food_group_id { 1, 4, 14 }`
and CNF-specific keyword overrides (cheese/dairy/egg/butter) keep firing on
non-CNF foods that map to the same CNF concept. CNF group IDs pass through
identity-translated. Synthetic / unknown groups fall through to the Rust
kernel's `_ => "2"` default, preserving prior behaviour.
"""

from typing import Any, Dict

from ..models.category import Category
from ..constants.food_groups import FOOD_GROUPS
from ..providers.threshold_provider import rust_hsr_backend


# CNF FVNL-eligible groups (mirrors `FVNL_GROUPS` in
# `hsr_calculator/hsr/constants/food_groups.py` and the Rust kernel's
# `FVNL_ELIGIBLE_GROUPS` at `rust_core/src/hsr/fvnl.rs`). Canonical
# categories that should be FVNL-eligible regardless of the source-native
# group ID — used by `validate_category_assignment` to suppress the
# false-positive "non-beverage group classified as beverage" warning when
# a WAFCT/FDC fruit (whose native group ID is not in {9, 14}) gets routed
# to BEVERAGE for fruit-juice keywords.
_FVNL_ELIGIBLE_CANONICALS = frozenset({
    'fruits', 'vegetables', 'nuts_seeds', 'legumes',
})


def _shim_group_id(food_group_id: int) -> int:
    """Translate any source's FoodGroupID to the CNF equivalent the Rust
    kernel expects. Identity for CNF (1-25). Returns the original ID if
    the bridge has no mapping, so synthetic IDs fall through to Rust's
    `_ => "2"` default."""
    try:
        from api.services.food_group_category import cnf_equivalent_group_id_for_group
    except Exception:  # noqa: BLE001 — bridge module optional
        return int(food_group_id)
    eq = cnf_equivalent_group_id_for_group(int(food_group_id))
    return int(eq) if eq is not None else int(food_group_id)


def _canonical_category(food_group_id: int) -> str:
    try:
        from api.services.food_group_category import canonical_category_for_group
    except Exception:  # noqa: BLE001
        return 'unknown'
    return canonical_category_for_group(int(food_group_id))


class FoodGroupMapper:
    """Food group ID + name → HSR ``Category``; Rust kernel still owns the
    word-boundary rules, Python provides the source-aware translation."""

    @classmethod
    def get_category(cls, food_group_id: int, food_name: str) -> Category:
        rust = rust_hsr_backend()
        shim = _shim_group_id(food_group_id)
        return Category(rust.food_group_category(int(shim), food_name))

    @classmethod
    def get_food_group_info(cls, food_group_id: int) -> Dict[str, str]:
        rust = rust_hsr_backend()
        shim = _shim_group_id(food_group_id)
        cat = Category(rust.food_group_category(int(shim), ""))
        # Prefer the bridge's source-aware name (handles "WAFCT — ..." /
        # "FDC — ..." prefixes); fall back to the CNF FOOD_GROUPS table
        # for ids the bridge doesn't know about.
        bridge_name: str = ""
        try:
            from api.services.food_group_category import _ensure_loaded
            by_gid, _ = _ensure_loaded()
            entry = by_gid.get(int(food_group_id))
            if entry is not None:
                bridge_name = entry.get('name', '') or ""
        except Exception:  # noqa: BLE001
            bridge_name = ""
        display_name = bridge_name or FOOD_GROUPS.get(food_group_id, "Unknown")
        return {
            "food_group_id":        food_group_id,
            "food_group_name":      display_name,
            "canonical_category":   _canonical_category(food_group_id),
            "hsr_category":         cat.value,
            "category_name":        cat.name,
        }

    @classmethod
    def validate_category_assignment(
        cls, food_group_id: int, food_name: str, calculated_category: Category
    ) -> Dict[str, Any]:
        """Lightweight validation metadata (not part of Rust core scoring).

        Canonical-category-driven (FDC-MULTI-SOURCE 2026-06-26): the
        validation is the same concept (a dairy-bucket food that comes out
        as a regular food, or a non-fruit/beverage food that comes out as
        a beverage, deserves a low-confidence note) but the test runs
        against the canonical category so WAFCT/FDC foods get the same
        validation as their CNF equivalents.
        """
        confidence = 1.0
        warnings = []
        food_name_lower = food_name.lower()

        canonical = _canonical_category(food_group_id)

        # Dairy bucket (CNF FG1 'dairy_egg_combined', WAFCT/FDC 'dairy' or
        # 'eggs') classified as a regular food — likely a powder/substitute
        # the keyword overrides didn't catch; otherwise plausibly a casein
        # / lactose-derived ingredient. Eggs proper are correctly Category 2.
        if canonical in ('dairy_egg_combined', 'dairy'):
            if calculated_category == Category.FOOD:
                if not any(
                    keyword in food_name_lower
                    for keyword in ["egg", "powder", "substitute"]
                ):
                    confidence = 0.7
                    warnings.append("Dairy product classified as regular food")

        # Beverage routing — fruits (FG9) and beverages (FG14) can correctly
        # be categorised as Category 1/1D; nothing else should be.
        if calculated_category == Category.BEVERAGE and canonical not in _FVNL_ELIGIBLE_CANONICALS and canonical != 'beverages':
            confidence = 0.8
            warnings.append("Non-beverage group classified as beverage")

        return {
            "confidence": confidence,
            "warnings": warnings,
            "validated": confidence >= 0.8,
        }
