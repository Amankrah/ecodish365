from typing import Dict, List, Any, Optional
import logging
from django.conf import settings
from django.core.exceptions import ValidationError

try:
    from environmental_impact_model.src.meal import Meal as EnvironmentalMeal
    from environmental_impact_model.src.food import Food as EnvironmentalFood
    from environmental_impact_model.src.monetization import Monetization
    from environmental_impact_model.src.data_loader import DataLoader as EnvDataLoader
    from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment
    from environmental_impact_model.src.cnf_integrator import get_cnf_integrator as get_env_cnf_integrator

    from fcs_calculator.fcs.service import extract_and_score

    from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator
    from hefi_calculator.hefi.models import HEFIInputs
    from hefi_calculator.hefi.algorithm import compute_hefi

    from hsr_calculator.hsr.models.food import Food as HSRFood
    from hsr_calculator.hsr.models.meal import Meal as HSRMeal
    from hsr_calculator.hsr.models.category import Category
    from hsr_calculator.hsr.calculators.hsr_calculator import HSRCalculator, HSRConfig
    from hsr_calculator.hsr.providers.threshold_provider import ThresholdProvider
    from hsr_calculator.hsr.calculators.fvnl_calculator import calculate_fvnl_content

    from heni_calculator.heni.service import (
        calculate_meal_heni_response,
        get_cnf_integrator as get_heni_cnf_integrator,
        ingredients_from_meal_food_items,
        resolve_llm_api_key,
    )

    CALCULATORS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import calculation modules: {e}")
    CALCULATORS_AVAILABLE = False

from api.food_id_finder import load_food_data, search_food
from api.cnf_cache import get_api_cnf_pipeline, get_dish_cnf_pipeline
from dish_cnf_db_pipeline.cnf_pipeline import CNFDataPipeline

logger = logging.getLogger(__name__)

# Module-level HEFI integrator — lightweight (shared pipeline), only built once.
_hefi_integrator = None


def _get_hefi_integrator() -> 'HEFICNFIntegrator':
    global _hefi_integrator
    if _hefi_integrator is None:
        _hefi_integrator = HEFICNFIntegrator(settings.CNF_FOLDER)
    return _hefi_integrator


class MealCalculationService:
    """Service integrating meal models with HSR, HEFI, HENI, FCS, and
    environmental-impact calculators.

    All CNF data access goes through the shared pipelines in
    ``api.cnf_cache``. The pre-indexed ``nutrients_by_food`` dict
    on the api pipeline replaces per-food ``get_food_details`` calls
    for nutrient lookups, and the Rust-backed HEFI/HSR scoring runs
    through the same ``rust_core`` bindings the standalone API views use.
    """

    def __init__(self):
        self.food_df = load_food_data()
        if self.food_df is None:
            logger.error("Failed to load food data")
            raise ValidationError("Food database not available")

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_food_items(self, food_items: List[Dict[str, Any]]) -> bool:
        required_fields = ['food_id', 'quantity', 'unit']
        for item in food_items:
            if not all(field in item for field in required_fields):
                raise ValidationError(f"Food item missing required fields: {required_fields}")
            if self.food_df[self.food_df['FoodID'] == item['food_id']].empty:
                raise ValidationError(f"Food ID {item['food_id']} not found in database")
        return True

    # ------------------------------------------------------------------
    # Nutritional profile — single pass using pre-indexed nutrients
    # ------------------------------------------------------------------

    def calculate_nutritional_profile(self, food_items: List[Dict[str, Any]]) -> Dict[str, float]:
        api_pipe = get_api_cnf_pipeline()
        nutrients_index = api_pipe.nutrients_by_food
        total: Dict[str, float] = {}
        for item in food_items:
            food_id = int(item['food_id'])
            factor = self._convert_to_grams(item['quantity'], item['unit']) / 100.0
            food_nutrients = nutrients_index.get(food_id, {})
            for name, value in food_nutrients.items():
                if value > 0:
                    total[name] = total.get(name, 0.0) + value * factor
        return total

    def calculate_total_calories(self, food_items: List[Dict[str, Any]]) -> float:
        api_pipe = get_api_cnf_pipeline()
        nutrients_index = api_pipe.nutrients_by_food
        total = 0.0
        for item in food_items:
            food_id = int(item['food_id'])
            factor = self._convert_to_grams(item['quantity'], item['unit']) / 100.0
            kcal = nutrients_index.get(food_id, {}).get('ENERGY (KILOCALORIES)', 0.0)
            total += kcal * factor
        return total

    # ------------------------------------------------------------------
    # Health scores (FCS, HEFI, HENI, HSR)
    # ------------------------------------------------------------------

    def calculate_health_scores(self, food_items: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
        scores: Dict[str, Optional[float]] = {
            'fcs_score': None,
            'hefi_score': None,
            'heni_score': None,
            'heni_total_score': None,
            'hsr_score': None,
        }
        if not CALCULATORS_AVAILABLE:
            return scores

        # --- FCS ---
        try:
            food_ids = [int(item['food_id']) for item in food_items]
            amounts_g = [
                float(self._convert_to_grams(item['quantity'], item['unit']))
                for item in food_items
            ]
            _, fcs_result = extract_and_score(food_ids, "Meal Analysis", amounts_g=amounts_g)
            scores['fcs_score'] = fcs_result.get('fcs')
        except Exception as e:
            logger.error("FCS calculation error: %s", e)

        # --- HEFI (Rust-backed via rust_core.hefi) ---
        try:
            integrator = _get_hefi_integrator()
            food_data = [
                (int(item['food_id']), float(self._convert_to_grams(item['quantity'], item['unit'])))
                for item in food_items
            ]
            agg = integrator.aggregate_inputs(food_data)
            hefi_result = compute_hefi(HEFIInputs(**agg))
            scores['hefi_score'] = hefi_result.total_score
        except Exception as e:
            logger.error("HEFI calculation error: %s", e)

        # --- HENI (rust_core.heni via heni_calculator service) ---
        try:
            heni_integrator = get_heni_cnf_integrator()
            ingredients = ingredients_from_meal_food_items(
                food_items,
                lambda it: float(self._convert_to_grams(it["quantity"], it["unit"])),
                integrator=heni_integrator,
            )
            comprehensive = calculate_meal_heni_response(
                ingredients,
                llm_api_key=resolve_llm_api_key(),
                cnf_integrator=heni_integrator,
            )
            heni_scores = comprehensive.get("heni_scores", {})
            scores["heni_score"] = heni_scores.get("total_heni_score")
            scores["heni_total_score"] = heni_scores.get("heni_per_100_kcal")
        except Exception as e:
            logger.error("HENI calculation error: %s", e)

        # --- HSR (Rust-backed via rust_core.hsr) ---
        try:
            hsr_foods: List[HSRFood] = []
            for item in food_items:
                food_id = int(item['food_id'])
                serving_size = float(self._convert_to_grams(item['quantity'], item['unit']))
                hsr_foods.append(self._build_hsr_food(food_id, serving_size))

            primary_food = hsr_foods[0] if hsr_foods else None
            if primary_food:
                meal_category = ThresholdProvider.get_category_from_food(
                    primary_food.food_name,
                    getattr(primary_food, 'food_group_id', 0),
                )
            else:
                meal_category = Category.FOOD

            meal = HSRMeal(foods=hsr_foods)
            meal.category = meal_category
            config = HSRConfig(
                use_scientific_thresholds=False,
                differentiate_sugar_sources=False,
                apply_satiety_adjustments=False,
                use_unified_energy_approach=False,
                consider_processing_level=False,
                include_confidence_metrics=True,
                detailed_explanations=False,
            )
            calculator = HSRCalculator(meal, config)
            result = calculator.calculate_hsr()
            scores['hsr_score'] = result.star_rating if result else None
        except Exception as e:
            logger.error("HSR calculation error: %s", e)

        return scores

    # ------------------------------------------------------------------
    # Environmental impact — direct call, no RequestFactory hack
    # ------------------------------------------------------------------

    def calculate_environmental_impact(self, food_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        empty = {
            'environmental_impacts': {},
            'sustainability_score': 50,
            'sustainability_rating': 'Unknown',
            'environmental_cost_total_cad': 0.0,
            'environmental_cost_per_100g_cad': 0.0,
            'environmental_cost_per_calorie_cad': 0.0,
            'carbon_footprint': 0.0,
            'water_use': 0.0,
            'land_use': 0.0,
        }
        if not CALCULATORS_AVAILABLE:
            return empty

        try:
            data_loader = EnvDataLoader()
            foods = [
                EnvironmentalFood(
                    food_id=int(item['food_id']),
                    quantity=float(self._convert_to_grams(item['quantity'], item['unit'])),
                    data_loader=data_loader,
                )
                for item in food_items
            ]
            env_meal = EnvironmentalMeal(foods)

            environmental_impact = env_meal.calculate_environmental_impact()
            sustainability_score = env_meal.get_sustainability_score()
            total_calories = env_meal.calculate_total_calories()

            try:
                monetization = Monetization(environmental_impact, data_loader)
                total_cost = monetization.get_total_monetized_impact()
                cost_per_calorie = monetization.calculate_cost_per_calorie(total_calories)
            except Exception as e:
                logger.error("Monetization error: %s", e)
                total_cost = 0.0
                cost_per_calorie = 0.0

            carbon_fp = environmental_impact.get('Global warming', 0.0)
            water_use = environmental_impact.get('Water consumption', 0.0)
            land_use = environmental_impact.get('Land use', 0.0)

            env_impacts = dict(environmental_impact)
            env_impacts['Water use'] = water_use
            env_impacts['_monetized_total_cad'] = total_cost
            env_impacts['_monetized_per_calorie_cad'] = cost_per_calorie

            sus = sustainability_score if isinstance(sustainability_score, dict) else {}
            return {
                'environmental_impacts': env_impacts,
                'sustainability_score': sus.get('overall_sustainability_score', 50),
                'sustainability_rating': sus.get('sustainability_rating', 'Unknown'),
                'environmental_cost_total_cad': total_cost,
                'environmental_cost_per_100g_cad': 0.0,
                'environmental_cost_per_calorie_cad': cost_per_calorie,
                'carbon_footprint': carbon_fp,
                'water_use': water_use,
                'land_use': land_use,
            }
        except Exception as e:
            logger.error("Environmental impact calculation error: %s", e)
            return empty

    # ------------------------------------------------------------------
    # Orchestrator — single entry point for the full meal analysis
    # ------------------------------------------------------------------

    def calculate_all_scores(self, food_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.validate_food_items(food_items)

        nutritional_profile = self.calculate_nutritional_profile(food_items)
        total_calories = nutritional_profile.get('ENERGY (KILOCALORIES)', 0.0)
        total_weight = sum(
            self._convert_to_grams(item['quantity'], item['unit']) for item in food_items
        )

        health_scores = self.calculate_health_scores(food_items)
        environmental_data = self.calculate_environmental_impact(food_items)

        return {
            'nutritional_profile': nutritional_profile,
            'total_calories': total_calories,
            'total_weight_grams': total_weight,
            'health_scores': health_scores,
            'environmental_data': environmental_data,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _convert_to_grams(quantity: float, unit: str) -> float:
        unit = unit.lower().strip()
        factors = {
            'g': 1, 'gram': 1, 'grams': 1,
            'kg': 1000, 'kilogram': 1000, 'kilograms': 1000,
            'lb': 453.592, 'pound': 453.592, 'pounds': 453.592,
            'oz': 28.3495, 'ounce': 28.3495, 'ounces': 28.3495,
            'ml': 1, 'milliliter': 1, 'milliliters': 1,
            'l': 1000, 'liter': 1000, 'liters': 1000,
            'cup': 240, 'cups': 240,
            'tbsp': 15, 'tablespoon': 15, 'tablespoons': 15,
            'tsp': 5, 'teaspoon': 5, 'teaspoons': 5,
        }
        return quantity * factors.get(unit, 1)

    def _get_cnf_pipeline(self) -> CNFDataPipeline:
        return get_dish_cnf_pipeline()

    def _build_hsr_food(self, food_id: int, serving_size: float) -> 'HSRFood':
        food_details = self._get_cnf_pipeline().get_food_details(food_id)
        if not food_details:
            raise ValidationError(f"Food with ID {food_id} not found in CNF database")

        nutrients: Dict[str, float] = {}
        for nutrient in food_details.get('NutrientValues', []):
            nutrients[nutrient['NutrientName']] = nutrient['NutrientValue']

        fvnl_percent = calculate_fvnl_content(food_id)
        food_group_id = food_details['FoodGroupID']

        return HSRFood(
            food_id=food_id,
            food_name=food_details['FoodDescription'],
            serving_size=serving_size,
            nutrients=nutrients,
            fvnl_percent=fvnl_percent,
            food_group_id=food_group_id,
        )


class MealRecommendationService:
    """Service for meal recommendations based on user preferences and health goals."""

    def __init__(self):
        self.calculation_service = MealCalculationService()

    def get_recommendations_for_user(self, user, meal_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        from .models import Meal

        queryset = Meal.objects.filter(is_public=True)
        if meal_type:
            queryset = queryset.filter(meal_type=meal_type)

        if user.is_authenticated:
            if user.allergies:
                for allergy in user.allergies:
                    queryset = queryset.exclude(tags__contains=allergy)
            if user.dietary_preferences:
                for preference in user.dietary_preferences:
                    queryset = queryset.filter(tags__contains=preference)

        meals = queryset.order_by('-likes_count', '-sustainability_score', '-created_at')[:limit]
        recommendations = [
            {
                'meal': meal,
                'match_score': self._calculate_match_score(meal, user),
                'reasons': self._get_recommendation_reasons(meal, user),
            }
            for meal in meals
        ]
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        return recommendations

    @staticmethod
    def _calculate_match_score(meal, user) -> float:
        if not user.is_authenticated:
            return 50.0

        score = 50.0
        if user.health_goals:
            if 'weight_loss' in user.health_goals and meal.total_calories and meal.total_calories < 400:
                score += 10
            if 'sustainability' in user.health_goals and meal.sustainability_score and meal.sustainability_score > 70:
                score += 15
            if 'muscle_gain' in user.health_goals:
                score += 5

        if user.dietary_preferences:
            matching = set(user.dietary_preferences) & set(meal.tags)
            score += len(matching) * 5

        if user.allergies:
            conflicts = set(user.allergies) & set(meal.tags)
            score -= len(conflicts) * 20

        if user.daily_calorie_target and meal.total_calories:
            diff = abs(meal.total_calories - user.daily_calorie_target / 3)
            if diff < 100:
                score += 10
            elif diff > 300:
                score -= 5

        return max(0.0, min(100.0, score))

    @staticmethod
    def _get_recommendation_reasons(meal, user) -> List[str]:
        reasons = []
        if meal.sustainability_score and meal.sustainability_score > 80:
            reasons.append("Highly sustainable choice")
        if meal.get_health_score_average() and meal.get_health_score_average() > 75:
            reasons.append("Excellent nutritional profile")
        if user.is_authenticated and user.dietary_preferences:
            matching = set(user.dietary_preferences) & set(meal.tags)
            if matching:
                reasons.append(f"Matches your {', '.join(matching)} preference")
        if meal.difficulty_level == 'easy':
            reasons.append("Quick and easy to prepare")
        if meal.likes_count > 50:
            reasons.append("Popular among community")
        return reasons
