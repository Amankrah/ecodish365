from typing import Dict, List, Any, Optional
import logging
from django.core.exceptions import ValidationError

# Import your existing calculation systems
try:
    # Environmental Impact Model
    from environmental_impact_model.src.meal import Meal as EnvironmentalMeal
    from environmental_impact_model.src.food import Food as EnvironmentalFood
    from environmental_impact_model.src.monetization import Monetization
    from environmental_impact_model.src.data_loader import DataLoader as EnvDataLoader
    
    # FCS Calculator
    from fcs_calculator.fcs.models.food_item import FoodItem as FCSFoodItem
    from fcs_calculator.fcs.analyzers.food_analyzer import FoodAnalyzer
    from fcs_calculator.fcs.utils.cnf_data_integrator import create_cnf_integrator as create_fcs_integrator
    
    # HEFI Calculator
    from hefi_calculator.hefi.cnf_integrator import HEFICNFIntegrator
    from hefi_calculator.hefi.models import HEFIInputs
    from hefi_calculator.hefi.algorithm import compute_hefi
    
    # HSR Calculator
    from hsr_calculator.hsr.models.food import Food as HSRFood
    from hsr_calculator.hsr.models.meal import Meal as HSRMeal
    from hsr_calculator.hsr.models.category import Category
    from hsr_calculator.hsr.calculators.hsr_calculator import HSRCalculator, HSRConfig
    from hsr_calculator.hsr.providers.threshold_provider import ThresholdProvider
    from hsr_calculator.hsr.calculators.fvnl_calculator import calculate_fvnl_content
    
    # HENI Calculator  
    from heni_calculator.heni.database.cnf_integrator import create_heni_cnf_integrator
    from heni_calculator.heni.models.ingredient import Ingredient
    from heni_calculator.heni.calculator.heni_calculator import HENICalculator
    
    CALCULATORS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import calculation modules: {e}")
    CALCULATORS_AVAILABLE = False

from api.food_id_finder import load_food_data, search_food
from django.conf import settings
from dish_cnf_db_pipeline.cnf_pipeline import CNFDataPipeline

logger = logging.getLogger(__name__)


class MealCalculationService:
    """Service to integrate meal models with existing health and environmental calculators"""
    
    def __init__(self):
        self.food_df = load_food_data()
        if self.food_df is None:
            logger.error("Failed to load food data")
            raise ValidationError("Food database not available")
        # Lazy-init CNF pipeline for HSR and other model integrations
        self._cnf_pipeline = None
    
    def validate_food_items(self, food_items: List[Dict[str, Any]]) -> bool:
        """Validate that all food items exist and have proper format"""
        required_fields = ['food_id', 'quantity', 'unit']
        
        for item in food_items:
            # Check required fields
            if not all(field in item for field in required_fields):
                raise ValidationError(f"Food item missing required fields: {required_fields}")
            
            # Validate food_id exists in database
            if not self.food_df[self.food_df['FoodID'] == item['food_id']].empty:
                continue
            else:
                raise ValidationError(f"Food ID {item['food_id']} not found in database")
        
        return True
    
    def calculate_nutritional_profile(self, food_items: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate comprehensive nutritional profile from food items"""
        try:
            total_nutrients = {}
            cnf_pipeline = self._get_cnf_pipeline()
            
            for item in food_items:
                food_id = int(item['food_id'])
                quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                
                # Get comprehensive food data including nutrients
                food_details = cnf_pipeline.get_food_details(food_id)
                if not food_details:
                    logger.warning(f"Food ID {food_id} not found in CNF database")
                    continue
                
                # Calculate nutrient amounts (CNF data is per 100g)
                factor = quantity_g / 100.0
                
                # Process nutrient values
                nutrient_values = food_details.get('NutrientValues', [])
                for nutrient in nutrient_values:
                    nutrient_name = nutrient.get('NutrientName', '')
                    nutrient_value = nutrient.get('NutrientValue', 0)
                    
                    if nutrient_name and nutrient_value is not None:
                        try:
                            nutrient_value = float(nutrient_value)
                            if nutrient_value > 0:  # Only include positive values
                                scaled_value = nutrient_value * factor
                                total_nutrients[nutrient_name] = total_nutrients.get(nutrient_name, 0) + scaled_value
                        except (ValueError, TypeError):
                            continue
            
            logger.info(f"Calculated {len(total_nutrients)} nutrients from CNF pipeline")
            return total_nutrients
            
        except Exception as e:
            logger.error(f"Error calculating nutritional profile: {str(e)}")
            return {}
    
    def calculate_total_calories(self, food_items: List[Dict[str, Any]]) -> float:
        """Calculate total calories from food items"""
        try:
            total_calories = 0
            cnf_pipeline = self._get_cnf_pipeline()
            
            for item in food_items:
                food_id = int(item['food_id'])
                quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                
                # Get comprehensive food data including nutrients
                food_details = cnf_pipeline.get_food_details(food_id)
                if not food_details:
                    logger.warning(f"Food ID {food_id} not found for calorie calculation")
                    continue
                
                # Find energy/calorie nutrient
                calories_per_100g = 0
                found_nutrient = None
                
                nutrient_values = food_details.get('NutrientValues', [])
                calorie_names = ['ENERGY (KILOCALORIES)', 'ENERGY', 'KILOCALORIES', 'KCAL', 'Energy (kcal)', 'energy', 'kcal']
                
                for nutrient in nutrient_values:
                    nutrient_name = nutrient.get('NutrientName', '')
                    nutrient_value = nutrient.get('NutrientValue', 0)
                    
                    if any(calorie_name.lower() in nutrient_name.lower() for calorie_name in calorie_names):
                        try:
                            calories_per_100g = float(nutrient_value)
                            if calories_per_100g > 0:
                                found_nutrient = nutrient_name
                                break
                        except (ValueError, TypeError):
                            continue
                
                item_calories = (calories_per_100g * quantity_g / 100.0)
                total_calories += item_calories
                
                logger.debug(f"Food {food_id}: {quantity_g}g, {calories_per_100g} kcal/100g (nutrient: {found_nutrient}), total: {item_calories} kcal")
            
            logger.info(f"Total calories calculated: {total_calories}")
            return total_calories
            
        except Exception as e:
            logger.error(f"Error calculating calories: {str(e)}")
            return 0.0
    
    def calculate_health_scores(self, food_items: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
        """Calculate all health scores using existing calculators"""
        scores = {
            'fcs_score': None,
            'hefi_score': None,
            'heni_score': None,
            'hsr_score': None
        }
        
        if not CALCULATORS_AVAILABLE:
            logger.warning("Calculators not available, returning None scores")
            return scores
        
        try:
            # Calculate FCS (Food Compass Score) using working FCS view logic
            try:
                # Build combined FoodItem for the meal
                food_item = FCSFoodItem("Meal Analysis")
                food_ids = [int(item['food_id']) for item in food_items]

                # Use enhanced CNF integrator to populate attributes
                cnf_integrator = create_fcs_integrator()
                cnf_integrator.extract_nutrients_enhanced(food_ids, food_item)

                # Analyze and extract FCS
                analyzer = FoodAnalyzer()
                fcs_result = analyzer.analyze_food_item(food_item)
                scores['fcs_score'] = fcs_result.get('fcs')
            except Exception as e:
                logger.error(f"FCS calculation error: {e}")
            
            # Calculate HEFI (Healthy Eating Food Index) using working HEFI flow
            try:
                integrator = HEFICNFIntegrator(settings.CNF_FOLDER)
                # Build (food_id, amount_g) pairs
                food_data = [
                    (int(item['food_id']), float(self._convert_to_grams(item['quantity'], item['unit'])))
                    for item in food_items
                ]
                agg = integrator.aggregate_inputs(food_data)
                hefi_inputs = HEFIInputs(**agg)
                hefi_result = compute_hefi(hefi_inputs)
                scores['hefi_score'] = hefi_result.total_score if hefi_result else None
            except Exception as e:
                logger.error(f"HEFI calculation error: {e}")
            
            # Calculate HENI (Health and Nutrition Index) using standalone HENI endpoint
            try:
                from django.test import Client
                import json
                
                # Prepare meal data for HENI API
                meal_data = []
                for item in food_items:
                    food_id = int(item['food_id'])
                    quantity_g = float(self._convert_to_grams(item['quantity'], item['unit']))
                    meal_data.append({
                        'food_id': food_id,
                        'amount': quantity_g,
                        'unit': 'g'
                    })
                
                # Use Django test client to call internal HENI API
                client = Client()
                response = client.post(
                    '/api/heni/calculate/',
                    data=json.dumps({'meal': meal_data}),
                    content_type='application/json'
                )
                
                if response.status_code == 200:
                    heni_result = response.json()
                    if heni_result.get('success'):
                        comprehensive_result = heni_result.get('data', {})
                        heni_scores = comprehensive_result.get('heni_scores', {})
                        scores['heni_score'] = heni_scores.get('total_heni_score')  # For minutes calculation
                        scores['heni_total_score'] = heni_scores.get('heni_per_100_kcal')  # For μDALY/100kcal display
                    else:
                        logger.warning(f"HENI API returned error: {heni_result}")
                else:
                    logger.warning(f"HENI API call failed with status {response.status_code}")
            except Exception as e:
                logger.error(f"HENI calculation error: {e}")
            
            # Calculate HSR (Health Star Rating) using consolidated logic
            try:
                # Build HSR foods using CNF pipeline-backed data (per hsr_views_consolidated)
                hsr_foods: List[HSRFood] = []
                for item in food_items:
                    food_id = int(item['food_id'])
                    serving_size = float(self._convert_to_grams(item['quantity'], item['unit']))
                    hsr_foods.append(self._build_hsr_food(food_id, serving_size))

                # Determine HSR category from the primary food
                primary_food = hsr_foods[0] if hsr_foods else None
                if primary_food:
                    meal_category = ThresholdProvider.get_category_from_food(
                        primary_food.food_name,
                        getattr(primary_food, 'food_group_id', 0)
                    )
                else:
                    meal_category = Category.FOOD

                # Create meal and calculator with standard config
                meal = HSRMeal(foods=hsr_foods)
                meal.category = meal_category
                config = HSRConfig(
                    use_scientific_thresholds=False,
                    differentiate_sugar_sources=False,
                    apply_satiety_adjustments=False,
                    use_unified_energy_approach=False,
                    consider_processing_level=False,
                    include_confidence_metrics=True,
                    detailed_explanations=False
                )
                calculator = HSRCalculator(meal, config)
                result = calculator.calculate_hsr()
                scores['hsr_score'] = result.star_rating if result else None
            except Exception as e:
                logger.error(f"HSR calculation error: {e}")
                
        except Exception as e:
            logger.error(f"Error calculating health scores: {str(e)}")
        
        return scores
    
    def calculate_environmental_impact(self, food_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate environmental impact using existing environmental model"""
        if not CALCULATORS_AVAILABLE:
            logger.warning("Environmental calculators not available, returning default values")
            return {
                'environmental_impacts': {},
                'sustainability_score': 50,
                'sustainability_rating': 'Unknown',
                'environmental_cost_total_cad': 0.0,
                'environmental_cost_per_100g_cad': 0.0,
                'environmental_cost_per_calorie_cad': 0.0
            }
        
        try:
            # Create environmental foods
            env_foods = []
            data_loader = EnvDataLoader()
            for item in food_items:
                food_id = item['food_id']
                quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                
                # Create environmental food object
                env_food = EnvironmentalFood(food_id=food_id, quantity=quantity_g, data_loader=data_loader)
                env_foods.append(env_food)
            
            # Create environmental meal
            env_meal = EnvironmentalMeal(env_foods)
            
            # Calculate impacts
            environmental_impact = env_meal.calculate_environmental_impact()
            sustainability_score = env_meal.get_sustainability_score()

            # Monetize environmental impacts (environmental cost)
            try:
                data_loader = EnvDataLoader()
                monetization = Monetization(environmental_impact, data_loader)
                total_cost = monetization.get_total_monetized_impact()
                cost_per_100g = monetization.calculate_cost_per_100g(env_meal.get_total_weight())
                cost_per_calorie = monetization.calculate_cost_per_calorie(env_meal.calculate_total_calories())
            except Exception as e:
                logger.error(f"Monetization error: {e}")
                total_cost = 0.0
                cost_per_100g = 0.0
                cost_per_calorie = 0.0

            return {
                'environmental_impacts': environmental_impact,
                'sustainability_score': sustainability_score.get('overall_sustainability_score', 50) if isinstance(sustainability_score, dict) else 50,
                'sustainability_rating': sustainability_score.get('sustainability_rating', 'Unknown') if isinstance(sustainability_score, dict) else 'Unknown',
                'environmental_cost_total_cad': total_cost,
                'environmental_cost_per_100g_cad': cost_per_100g,
                'environmental_cost_per_calorie_cad': cost_per_calorie
            }
            
        except Exception as e:
            logger.error(f"Error calculating environmental impact: {str(e)}")
            return {
                'environmental_impacts': {},
                'sustainability_score': 50,
                'sustainability_rating': 'Unknown',
                'environmental_cost_total_cad': 0.0,
                'environmental_cost_per_100g_cad': 0.0,
                'environmental_cost_per_calorie_cad': 0.0
            }
    
    def calculate_all_scores(self, food_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate all scores and metrics for a meal"""
        try:
            self.validate_food_items(food_items)
            
            # Calculate basic nutritional data
            nutritional_profile = self.calculate_nutritional_profile(food_items)
            total_calories = self.calculate_total_calories(food_items)
            total_weight = sum(self._convert_to_grams(item['quantity'], item['unit']) for item in food_items)
            
            # Calculate health scores
            health_scores = self.calculate_health_scores(food_items)
            
            # Calculate environmental impact
            environmental_data = self.calculate_environmental_impact(food_items)
            
            return {
                'nutritional_profile': nutritional_profile,
                'total_calories': total_calories,
                'total_weight_grams': total_weight,
                'health_scores': health_scores,
                'environmental_data': environmental_data
            }
            
        except Exception as e:
            logger.error(f"Error calculating meal scores: {str(e)}")
            raise ValidationError(f"Failed to calculate meal scores: {str(e)}")
    
    def _convert_to_grams(self, quantity: float, unit: str) -> float:
        """Convert different units to grams"""
        unit = unit.lower().strip()
        
        conversion_factors = {
            'g': 1,
            'gram': 1,
            'grams': 1,
            'kg': 1000,
            'kilogram': 1000,
            'kilograms': 1000,
            'lb': 453.592,
            'pound': 453.592,
            'pounds': 453.592,
            'oz': 28.3495,
            'ounce': 28.3495,
            'ounces': 28.3495,
            'ml': 1,  # Assuming 1ml = 1g for liquids (approximation)
            'milliliter': 1,
            'milliliters': 1,
            'l': 1000,
            'liter': 1000,
            'liters': 1000,
            'cup': 240,  # Approximate
            'cups': 240,
            'tbsp': 15,
            'tablespoon': 15,
            'tablespoons': 15,
            'tsp': 5,
            'teaspoon': 5,
            'teaspoons': 5,
        }
        
        factor = conversion_factors.get(unit, 1)
        return quantity * factor

    def _get_cnf_pipeline(self) -> CNFDataPipeline:
        """Get or initialize the CNF data pipeline (singleton within this service)."""
        if self._cnf_pipeline is None:
            self._cnf_pipeline = CNFDataPipeline(settings.CNF_FOLDER)
        return self._cnf_pipeline

    def _build_hsr_food(self, food_id: int, serving_size: float) -> 'HSRFood':
        """Construct an HSRFood using CNF data (aligns with hsr_views_consolidated logic)."""
        food_details = self._get_cnf_pipeline().get_food_details(food_id)
        if not food_details:
            raise ValidationError(f"Food with ID {food_id} not found in CNF database")

        # Extract nutrients
        nutrients: Dict[str, float] = {}
        for nutrient in food_details.get('NutrientValues', []):
            nutrients[nutrient['NutrientName']] = nutrient['NutrientValue']

        # FVNL percent and food group
        fvnl_percent = calculate_fvnl_content(food_id)
        food_group_id = food_details['FoodGroupID']

        return HSRFood(
            food_id=food_id,
            food_name=food_details['FoodDescription'],
            serving_size=serving_size,
            nutrients=nutrients,
            fvnl_percent=fvnl_percent,
            food_group_id=food_group_id
        )
    
    def _prepare_meal_data_for_calculators(self, food_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare meal data in the format expected by your existing calculators"""
        # This will depend on the specific format your calculators expect
        # You'll need to adapt this based on your actual calculator interfaces
        
        foods = []
        for item in food_items:
            food_id = item['food_id']
            quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
            
            food_row = self.food_df[self.food_df['FoodID'] == food_id].iloc[0]
            
            food_data = {
                'food_id': food_id,
                'food_name': food_row['FoodDescription'],
                'quantity': quantity_g,
                'food_group': food_row.get('food_category', 'other'),
                'preparation_method': food_row.get('preparation_method', 'unspecified')
            }
            foods.append(food_data)
        
        return {
            'foods': foods,
            'total_weight': sum(food['quantity'] for food in foods)
        }


class MealRecommendationService:
    """Service for meal recommendations based on user preferences and health goals"""
    
    def __init__(self):
        self.calculation_service = MealCalculationService()
    
    def get_recommendations_for_user(self, user, meal_type: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get personalized meal recommendations for a user"""
        from .models import Meal
        
        # Base queryset for public meals
        queryset = Meal.objects.filter(is_public=True)
        
        if meal_type:
            queryset = queryset.filter(meal_type=meal_type)
        
        # Filter based on user preferences
        if user.is_authenticated:
            # Exclude meals with user's allergies
            if user.allergies:
                for allergy in user.allergies:
                    queryset = queryset.exclude(tags__contains=allergy)
            
            # Prefer meals matching dietary preferences
            if user.dietary_preferences:
                for preference in user.dietary_preferences:
                    queryset = queryset.filter(tags__contains=preference)
        
        # Order by relevance (you can customize this logic)
        meals = queryset.order_by('-likes_count', '-sustainability_score', '-created_at')[:limit]
        
        recommendations = []
        for meal in meals:
            recommendations.append({
                'meal': meal,
                'match_score': self._calculate_match_score(meal, user),
                'reasons': self._get_recommendation_reasons(meal, user)
            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations
    
    def _calculate_match_score(self, meal, user) -> float:
        """Calculate how well a meal matches user preferences"""
        if not user.is_authenticated:
            return 50.0
        
        score = 50.0  # Base score
        
        # Health goals alignment
        if user.health_goals:
            if 'weight_loss' in user.health_goals and meal.total_calories and meal.total_calories < 400:
                score += 10
            if 'sustainability' in user.health_goals and meal.sustainability_score and meal.sustainability_score > 70:
                score += 15
            if 'muscle_gain' in user.health_goals:
                # Check if meal is high in protein (you'd need to implement this)
                score += 5
        
        # Dietary preferences match
        if user.dietary_preferences:
            matching_prefs = set(user.dietary_preferences) & set(meal.tags)
            score += len(matching_prefs) * 5
        
        # Avoid allergens (penalty for allergens)
        if user.allergies:
            conflicting_allergens = set(user.allergies) & set(meal.tags)
            score -= len(conflicting_allergens) * 20
        
        # Calorie target alignment
        if user.daily_calorie_target and meal.total_calories:
            target_per_meal = user.daily_calorie_target / 3  # Rough estimate
            calorie_diff = abs(meal.total_calories - target_per_meal)
            if calorie_diff < 100:
                score += 10
            elif calorie_diff > 300:
                score -= 5
        
        return max(0, min(100, score))
    
    def _get_recommendation_reasons(self, meal, user) -> List[str]:
        """Get reasons why this meal is recommended"""
        reasons = []
        
        if meal.sustainability_score and meal.sustainability_score > 80:
            reasons.append("Highly sustainable choice")
        
        if meal.get_health_score_average() and meal.get_health_score_average() > 75:
            reasons.append("Excellent nutritional profile")
        
        if user.is_authenticated and user.dietary_preferences:
            matching_prefs = set(user.dietary_preferences) & set(meal.tags)
            if matching_prefs:
                reasons.append(f"Matches your {', '.join(matching_prefs)} preference")
        
        if meal.difficulty_level == 'easy':
            reasons.append("Quick and easy to prepare")
        
        if meal.likes_count > 50:
            reasons.append("Popular among community")
        
        return reasons