"""
FCS 2.0 analysis: CNF integration fills ``FoodItem``; scoring runs in ``rust_core.fcs``.
"""

import logging
from typing import Any, Dict, Union

from fcs.models.food_item import FoodItem
from fcs.models.enums import AttributeType, NOVACategory

logger = logging.getLogger(__name__)

try:
    from rust_core import fcs as _rust_fcs
except ImportError as exc:
    raise ImportError(
        "FCS requires the rust_core native module. Build and install with:\n"
        "  cd backend/rust_core && maturin develop"
    ) from exc


def _nova_enum_from_level(processing_level: int) -> NOVACategory:
    if processing_level == -1:
        return NOVACategory.MINIMALLY_PROCESSED
    mapping = {
        1: NOVACategory.MINIMALLY_PROCESSED,
        2: NOVACategory.PROCESSED_CULINARY_INGREDIENTS,
        3: NOVACategory.PROCESSED_FOODS,
        4: NOVACategory.ULTRA_PROCESSED_FOODS,
    }
    return mapping.get(processing_level, NOVACategory.MINIMALLY_PROCESSED)


def _floatify_attributes(attrs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Ensure nested values are plain ``float`` for PyO3 (e.g. numpy scalars)."""
    out: Dict[str, Dict[str, float]] = {}
    for domain, inner in attrs.items():
        out[domain] = {k: float(v) for k, v in inner.items()}
    return out


class FoodAnalyzer:
    """Thin façade over ``rust_core.fcs`` (parity with pre-Rust API surface)."""

    @staticmethod
    def get_attribute_type(attribute: str) -> AttributeType:
        kind = _rust_fcs.fcs_attribute_kind(attribute)
        return AttributeType[kind]

    @staticmethod
    def score_attribute(
        value: float, attribute: str, attribute_type: AttributeType
    ) -> float:
        _ = attribute_type
        return float(_rust_fcs.fcs_score_attribute(float(value), attribute))

    def analyze_food_item(self, food_item: FoodItem) -> Dict[str, Union[float, str, dict]]:
        pl = int(food_item.get_nova_processing_level())
        food_item.set_nova_category(_nova_enum_from_level(pl))

        attrs = _floatify_attributes(food_item.attributes)
        out = _rust_fcs.compute_fcs(attrs, pl)

        result: Dict[str, Union[float, str, dict]] = {
            "name": food_item.name,
            "original_score": round(float(out["original_score"]), 2),
            "fcs": float(out["fcs"]),
            "nova_category": str(out["nova_category"]),
        }
        processing_details = food_item.get_processing_details()
        if processing_details:
            result["processing_details"] = processing_details
        return result
