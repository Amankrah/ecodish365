"""
HENI DALY step: **all** μDALY aggregation, normalization, and disease breakdown run in ``rust_core.heni.compute_heni``.

This module only marshals Python dicts into :class:`HENIResult`.
"""

from dataclasses import dataclass
from typing import Dict, List

try:
    from rust_core import heni as _rust_heni
except ImportError as exc:
    raise ImportError(
        "HENI DALY core requires the rust_core native module. Build and install with:\n"
        "  cd backend/rust_core && maturin develop"
    ) from exc


@dataclass
class DALYComponents:
    """Components of DALY calculation: YLL + YLD (retained for API compatibility)."""

    yll: float
    yld: float
    total_daly: float

    def __post_init__(self):
        self.total_daly = self.yll + self.yld


@dataclass
class HENIResult:
    """Comprehensive HENI calculation result."""

    total_heni_score: float
    heni_per_100_kcal: float
    heni_per_100_grams: float
    heni_per_serving: float
    food_group_contributions: Dict[str, float]
    nutrient_contributions: Dict[str, float]
    disease_burden_breakdown: Dict[str, float]
    risk_factor_amounts: Dict[str, float]
    effective_range_warnings: List[str]
    health_impact_minutes: float
    health_impact_description: str


def _py_dict_to_float_map(d: Dict[str, float]) -> Dict[str, float]:
    return {str(k): float(v) for k, v in d.items()}


class DALYCalculator:
    """HENI methodology; delegates scoring to Rust."""

    def __init__(self, age_group: str = "adult_male", gender_adjustment: bool = True):
        self.age_group = age_group
        self.gender_adjustment = gender_adjustment

    def calculate_heni_score(
        self,
        risk_factor_amounts: Dict[str, float],
        total_energy_kcal: float,
        total_weight_grams: float,
        serving_size_grams: float = 100.0,
    ) -> HENIResult:
        out = _rust_heni.compute_heni(
            _py_dict_to_float_map(risk_factor_amounts),
            float(total_energy_kcal),
            float(total_weight_grams),
            float(serving_size_grams),
            str(self.age_group),
            bool(self.gender_adjustment),
        )
        return HENIResult(
            total_heni_score=float(out["total_heni_score"]),
            heni_per_100_kcal=float(out["heni_per_100_kcal"]),
            heni_per_100_grams=float(out["heni_per_100_grams"]),
            heni_per_serving=float(out["heni_per_serving"]),
            food_group_contributions={k: float(v) for k, v in out["food_group_contributions"].items()},
            nutrient_contributions={k: float(v) for k, v in out["nutrient_contributions"].items()},
            disease_burden_breakdown={k: float(v) for k, v in out["disease_burden_breakdown"].items()},
            risk_factor_amounts=risk_factor_amounts,
            effective_range_warnings=list(out["effective_range_warnings"]),
            health_impact_minutes=float(out["health_impact_minutes"]),
            health_impact_description=str(out["health_impact_description"]),
        )
