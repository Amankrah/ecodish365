from typing import Dict, List, Any, Optional
import logging
from django.core.exceptions import ValidationError

# Import your existing calculation systems
try:
    # Environmental Impact Model
    from environmental_impact_model.src.meal import Meal as EnvironmentalMeal
    from environmental_impact_model.src.food import Food as EnvironmentalFood
    
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
    from hsr_calculator.hsr.calculators.hsr_calculator import HSRCalculator, HSRConfig
    
    # HENI Calculator  
    from heni_calculator.heni.database.cnf_integrator import create_heni_cnf_integrator
    from heni_calculator.heni.models.ingredient import Ingredient
    from heni_calculator.heni.calculator.heni_calculator import HENICalculator
    
    CALCULATORS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import calculation modules: {e}")
    CALCULATORS_AVAILABLE = False

from api.food_id_finder import load_food_data, search_food

logger = logging.getLogger(__name__)


class MealCalculationService:
    """Service to integrate meal models with existing health and environmental calculators"""
    
    def __init__(self):
        self.food_df = load_food_data()
        if self.food_df is None:
            logger.error("Failed to load food data")
            raise ValidationError("Food database not available")
    
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
            
            for item in food_items:
                food_id = item['food_id']
                quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                
                # Get food data
                food_row = self.food_df[self.food_df['FoodID'] == food_id].iloc[0]
                
                # Calculate nutrient amounts (nutrients are typically per 100g)
                factor = quantity_g / 100.0
                
                # Add up all nutrients - you'll need to map your actual nutrient columns
                nutrient_columns = [col for col in self.food_df.columns 
                                  if col not in ['FoodID', 'FoodDescription', 'FoodDescription_processed', 
                                               'food_category', 'preparation_method']]
                
                for nutrient_col in nutrient_columns:
                    nutrient_value = food_row.get(nutrient_col, 0) or 0
                    if isinstance(nutrient_value, (int, float)):
                        total_nutrients[nutrient_col] = total_nutrients.get(nutrient_col, 0) + (nutrient_value * factor)
            
            return total_nutrients
            
        except Exception as e:
            logger.error(f"Error calculating nutritional profile: {str(e)}")
            return {}
    
    def calculate_total_calories(self, food_items: List[Dict[str, Any]]) -> float:
        """Calculate total calories from food items"""
        try:
            total_calories = 0
            for item in food_items:
                food_id = item['food_id']
                quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                
                # Get food data and calculate calories
                food_row = self.food_df[self.food_df['FoodID'] == food_id].iloc[0]
                
                # Try different possible calorie column names
                calorie_fields = ['ENERGY (KILOCALORIES)', 'ENERGY', 'KILOCALORIES', 'KCAL']
                calories_per_100g = 0
                
                for field in calorie_fields:
                    if field in food_row and food_row[field]:
                        calories_per_100g = float(food_row[field])
                        break
                
                total_calories += (calories_per_100g * quantity_g / 100.0)
            
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
            # Calculate FCS (Food Choice Score)
            try:
                food_item = FCSFoodItem("Meal Analysis")
                integrator = create_fcs_integrator()
                analyzer = FoodAnalyzer(integrator)
                
                # Add foods to the food item based on food_items
                for item in food_items:
                    food_id = item['food_id']
                    quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                    # This needs to be adapted based on actual FCS API
                
                fcs_score = analyzer.calculate_fcs(50.0)  # Base score - adapt as needed
                scores['fcs_score'] = fcs_score
            except Exception as e:
                logger.error(f"FCS calculation error: {e}")
            
            # Calculate HEFI (Healthy Eating Food Index)
            try:
                from django.conf import settings
                integrator = HEFICNFIntegrator(settings.CNF_FOLDER)
                
                # Create HEFI inputs from food items
                food_ids = [item['food_id'] for item in food_items]
                quantities = [self._convert_to_grams(item['quantity'], item['unit']) for item in food_items]
                
                hefi_inputs = HEFIInputs(food_ids=food_ids, quantities=quantities)
                hefi_score = compute_hefi(hefi_inputs, integrator)
                scores['hefi_score'] = hefi_score.total_score if hefi_score else None
            except Exception as e:
                logger.error(f"HEFI calculation error: {e}")
            
            # Calculate HENI (Health and Nutrition Index)
            try:
                integrator = create_heni_cnf_integrator()
                calculator = HENICalculator(integrator)
                
                # Convert food items to ingredients
                ingredients = []
                for item in food_items:
                    food_id = item['food_id']
                    quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                    ingredient = Ingredient(food_id=food_id, quantity_grams=quantity_g)
                    ingredients.append(ingredient)
                
                heni_result = calculator.calculate_heni(ingredients)
                scores['heni_score'] = heni_result.net_daly_total if heni_result else None
            except Exception as e:
                logger.error(f"HENI calculation error: {e}")
            
            # Calculate HSR (Health Star Rating)
            try:
                calculator = HSRCalculator(HSRConfig())
                
                # Create HSR foods from food items
                hsr_foods = []
                for item in food_items:
                    food_id = item['food_id']
                    quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                    food_row = self.food_df[self.food_df['FoodID'] == food_id].iloc[0]
                    
                    hsr_food = HSRFood(
                        food_id=food_id,
                        name=food_row['FoodDescription'],
                        quantity_grams=quantity_g
                    )
                    hsr_foods.append(hsr_food)
                
                hsr_meal = HSRMeal(hsr_foods)
                hsr_result = calculator.calculate_meal_hsr(hsr_meal)
                scores['hsr_score'] = hsr_result.overall_hsr_rating if hsr_result else None
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
                'sustainability_rating': 'Unknown'
            }
        
        try:
            # Create environmental foods
            env_foods = []
            for item in food_items:
                food_id = item['food_id']
                quantity_g = self._convert_to_grams(item['quantity'], item['unit'])
                
                # Get food info
                food_row = self.food_df[self.food_df['FoodID'] == food_id].iloc[0]
                food_name = food_row['FoodDescription']
                
                # Create environmental food object
                env_food = EnvironmentalFood(
                    food_id=food_id,
                    food_name=food_name,
                    quantity=quantity_g,
                    food_group=food_row.get('food_category', 'other')
                )
                env_foods.append(env_food)
            
            # Create environmental meal
            env_meal = EnvironmentalMeal(env_foods)
            
            # Calculate impacts
            environmental_impact = env_meal.calculate_environmental_impact()
            sustainability_score = env_meal.get_sustainability_score()
            
            return {
                'environmental_impacts': environmental_impact,
                'sustainability_score': sustainability_score.get('overall_sustainability_score', 50) if isinstance(sustainability_score, dict) else 50,
                'sustainability_rating': sustainability_score.get('sustainability_rating', 'Unknown') if isinstance(sustainability_score, dict) else 'Unknown'
            }
            
        except Exception as e:
            logger.error(f"Error calculating environmental impact: {str(e)}")
            return {
                'environmental_impacts': {},
                'sustainability_score': 50,
                'sustainability_rating': 'Unknown'
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