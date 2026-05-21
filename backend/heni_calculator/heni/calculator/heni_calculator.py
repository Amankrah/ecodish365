from typing import List, Tuple, Dict, Optional
from ..database.cnf_integrator import HENICNFIntegrator
from ..models.ingredient import Ingredient
from ..categorization.llm_categorizer import LLMFoodCategorizer
from ..core.daly_calculator import DALYCalculator, HENIResult
from ..config.heni_factors import HENI_RISK_FACTOR_KEYS

import logging

logger = logging.getLogger(__name__)

class HENICalculator:
    def __init__(self, cnf_integrator: HENICNFIntegrator, llm_api_key: str = "", age_group: str = "adult_male"):
        self.cnf_integrator = cnf_integrator
        self.heni_factor_keys = HENI_RISK_FACTOR_KEYS
        self.categorizer = LLMFoodCategorizer(cnf_integrator, llm_api_key) if llm_api_key else None
        self.daly_calculator = DALYCalculator(age_group=age_group)

    def calculate_heni(self, ingredients: List[Ingredient]) -> HENIResult:
        """Calculate comprehensive HENI score using proper DALY methodology"""
        total_energy_kcal = 0.0
        total_weight_grams = 0.0
        aggregated_risk_factors: Dict[str, float] = {}
        aggregated_carve_out_audit: List[str] = []
        aggregated_imputation_warnings: List[str] = []
        ingredient_details = []

        for ingredient in ingredients:
            logger.info(f"Processing ingredient: {ingredient.food_id}, amount: {ingredient.amount}g")

            # Calculate energy and weight contributions
            ingredient_kcal = ingredient.kcal * (float(ingredient.amount) / 100)
            total_energy_kcal += ingredient_kcal
            total_weight_grams += float(ingredient.amount)

            # Get risk factor amounts for this ingredient.
            # The extractor may attach two sentinel keys carrying audit-trail
            # metadata (carve-outs applied; TFA imputation warnings); strip them
            # here before scaling/aggregating numeric factors. See
            # `heni_calculator_methods._apply_double_counting_carve_outs`.
            risk_factors = self._extract_risk_factors_from_ingredient(ingredient)
            audit_keys = ("__audit_carve_outs__", "__imputation_warnings__")
            ingredient_audit = risk_factors.pop("__audit_carve_outs__", [])
            ingredient_imputations = risk_factors.pop("__imputation_warnings__", [])
            aggregated_carve_out_audit.extend(ingredient_audit)
            aggregated_imputation_warnings.extend(ingredient_imputations)

            # Scale risk factors by ingredient amount
            scaled_risk_factors = {}
            for factor, amount_per_100g in risk_factors.items():
                if factor in audit_keys:
                    continue  # defensive — already popped above
                if not isinstance(amount_per_100g, (int, float)):
                    logger.warning(
                        f"Non-numeric value for {factor!r} on food {ingredient.food_id}; skipping."
                    )
                    continue
                scaled_amount = (float(amount_per_100g) * float(ingredient.amount)) / 100
                scaled_risk_factors[factor] = scaled_amount

                # Aggregate across all ingredients
                if factor in aggregated_risk_factors:
                    aggregated_risk_factors[factor] += scaled_amount
                else:
                    aggregated_risk_factors[factor] = scaled_amount

            # Store ingredient details for reporting
            ingredient_details.append({
                'food_id': ingredient.food_id,
                'amount_g': ingredient.amount,
                'energy_kcal': ingredient_kcal,
                'risk_factors': scaled_risk_factors,
                'description': self.cnf_integrator.get_food_description(ingredient.food_id),
                'carve_out_audit': ingredient_audit,
                'imputation_warnings': ingredient_imputations,
            })

            logger.info(f"Ingredient kcal: {ingredient_kcal}, risk factors: {len(scaled_risk_factors)}")

        # Calculate HENI score using DALY methodology
        heni_result = self.daly_calculator.calculate_heni_score(
            risk_factor_amounts=aggregated_risk_factors,
            total_energy_kcal=total_energy_kcal,
            total_weight_grams=total_weight_grams,
            serving_size_grams=total_weight_grams
        )

        # Add ingredient details to result
        heni_result.ingredient_details = ingredient_details
        heni_result.total_energy_kcal = total_energy_kcal
        heni_result.total_weight_grams = total_weight_grams
        # Surface meal-level audit trail (additive). The HENIResult dataclass is
        # mutable, so attaching new attributes is safe.
        heni_result.carve_out_audit = aggregated_carve_out_audit
        heni_result.imputation_warnings = aggregated_imputation_warnings

        logger.info(f"Total HENI: {heni_result.total_heni_score:.2f} μDALY, Health impact: {heni_result.health_impact_minutes:.1f} minutes")

        return heni_result
    
    def _extract_risk_factors_from_ingredient(self, ingredient) -> Dict[str, float]:
        """Extract HENI risk factors from ingredient using CNF data and categorization"""
        from .heni_calculator_methods import extract_risk_factors_from_ingredient
        return extract_risk_factors_from_ingredient(self, ingredient)
    
    def calculate_meal_heni(self, ingredients: List) -> Dict:
        """Calculate HENI for a complete meal with detailed breakdown"""
        from .heni_calculator_methods import calculate_meal_heni
        return calculate_meal_heni(self, ingredients)