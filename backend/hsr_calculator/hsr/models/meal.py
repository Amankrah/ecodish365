from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import logging
from .food import Food
from .category import Category

logger = logging.getLogger(__name__)

@dataclass
class Meal:
    foods: List[Food]
    category: Optional[Category] = None  # Will be auto-determined if not provided
    
    # Enhanced categorization analysis (populated during __post_init__)
    category_analysis: Dict[str, Any] = field(default_factory=dict, init=False)
    category_confidence: float = field(default=0.0, init=False)
    category_warnings: List[str] = field(default_factory=list, init=False)
    
    # Nutritional context for validation
    nutritional_context: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self):
        # Validate foods list
        if not self.foods:
            logger.warning("Empty meal created")
            self.category = Category.FOOD
            self.category_analysis = {"reason": "empty_meal", "confidence": 0.0}
            self.category_confidence = 0.0
            self.category_warnings = ["Empty meal - defaulting to FOOD category"]
            return
        
        # Ensure all foods have valid data
        self._validate_foods()
        
        # Auto-determine category if not provided
        if self.category is None:
            self._determine_category()
        else:
            # Validate provided category
            self._validate_provided_category()
        
        # Calculate nutritional values
        self._calculate_nutritional_values()
        
        # Validate final categorization
        self._validate_final_categorization()

    def _validate_foods(self):
        """Validate that all foods have required data"""
        invalid_foods = []
        
        for i, food in enumerate(self.foods):
            if not hasattr(food, 'serving_size') or food.serving_size <= 0:
                invalid_foods.append(f"Food {i+1}: Invalid serving size")
            
            if not hasattr(food, 'nutrients') or not food.nutrients:
                invalid_foods.append(f"Food {i+1}: Missing nutrient data")
            
            if not hasattr(food, 'category') or food.category is None:
                invalid_foods.append(f"Food {i+1}: Missing category")
        
        if invalid_foods:
            self.category_warnings.extend(invalid_foods)
            logger.warning(f"Meal validation issues: {invalid_foods}")

    def _determine_category(self):
        """Auto-determine meal category from constituent foods with scientific logic"""
        # Import here to avoid circular imports
        from ..utils.meal_categorizer import MealCategorizer
        
        try:
            # Ensure all foods have categories assigned
            foods_without_categories = [food for food in self.foods if food.category is None]
            if foods_without_categories:
                self.category_warnings.append(
                    f"{len(foods_without_categories)} foods missing category assignments"
                )
                # Auto-assign categories for foods that are missing them
                self._assign_missing_food_categories(foods_without_categories)
            
            # Determine meal category with scientific logic
            categorization_result = MealCategorizer.determine_scientific_category(self.foods)
            self.category = categorization_result.recommended_category
            self.category_analysis = {
                "reason": "scientific_categorization",
                "confidence": categorization_result.confidence,
                "reasoning": categorization_result.reasoning,
                "nutritional_rationale": categorization_result.nutritional_rationale,
                "alternative_categories": categorization_result.alternative_categories,
                "scientific_factors": categorization_result.scientific_factors
            }
            self.category_confidence = categorization_result.confidence
            
            # Extract nutritional context
            self.nutritional_context = categorization_result.scientific_factors
            
            # Add any warnings from the analysis
            if hasattr(categorization_result, 'warnings'):
                self.category_warnings.extend(categorization_result.warnings)
            
            # Add note if present
            if 'note' in self.category_analysis:
                self.category_warnings.append(self.category_analysis['note'])
            
            # Log categorization for debugging
            logger.info(
                f"Meal categorized as {self.category.value}: "
                f"{self.category_analysis.get('reason', 'unknown')} "
                f"(confidence: {self.category_confidence:.2f})"
            )
            
        except Exception as e:
            logger.error(f"Error during meal categorization: {str(e)}")
            self.category = Category.FOOD
            self.category_analysis = {"reason": "error_fallback", "error": str(e)}
            self.category_confidence = 0.0
            self.category_warnings.append(f"Categorization error: {str(e)} - defaulted to FOOD")

    def _validate_provided_category(self):
        """Validate user-provided category against calculated category with scientific logic"""
        # Import here to avoid circular imports
        from ..utils.meal_categorizer import MealCategorizer
        
        try:
            # Use scientific categorization for validation
            categorization_result = MealCategorizer.determine_scientific_category(self.foods)
            
            # Create validation structure compatible with existing code
            validation = {
                'confidence': categorization_result.confidence,
                'warnings': [],
                'calculated_category': categorization_result.recommended_category.value,
                'assigned_category': self.category.value,
                'category_breakdown': categorization_result.scientific_factors,
                'analysis': {
                    'reasoning': categorization_result.reasoning,
                    'nutritional_rationale': categorization_result.nutritional_rationale,
                    'alternative_categories': categorization_result.alternative_categories
                }
            }
            
            # Add warnings if categories don't match
            if categorization_result.recommended_category != self.category:
                validation['warnings'].append(f"Calculated category {categorization_result.recommended_category.value} differs from assigned {self.category.value}")
            
            self.category_confidence = validation['confidence']
            self.category_warnings.extend(validation['warnings'])
            
            # Enhanced analysis with nutritional context
            self.category_analysis = {
                "reason": "user_provided",
                "validation": validation,
                "calculated_category": validation['calculated_category'],
                "assigned_category": validation['assigned_category'],
                "nutritional_context": validation.get('category_breakdown', {}),
                "analysis": validation.get('analysis', {})
            }
            
            # Extract nutritional context
            self.nutritional_context = validation.get('category_breakdown', {})
            
            # Add recommendations if confidence is low
            if self.category_confidence < 0.6:
                self.category_warnings.append(
                    f"Consider using {validation['calculated_category']} category instead"
                )
            
            logger.info(
                f"User-provided category {self.category.value} validated "
                f"(confidence: {self.category_confidence:.2f})"
            )
            
        except Exception as e:
            logger.error(f"Error during category validation: {str(e)}")
            self.category_warnings.append(f"Validation error: {str(e)}")
            self.category_confidence = 0.5

    def _assign_missing_food_categories(self, foods_without_categories: List[Food]):
        """Assign categories to foods that are missing them"""
        # Import here to avoid circular imports
        from ..utils.food_group_mapper import FoodGroupMapper
        
        for food in foods_without_categories:
            try:
                if hasattr(food, 'food_id') and hasattr(food, 'food_name'):
                    # Try to determine from food group
                    food_group_id = getattr(food, 'food_group_id', None)
                    if food_group_id:
                        food.category = FoodGroupMapper.get_category(
                            food_group_id, food.food_name
                        )
                        food.category_source = 'food_group_mapping'
                        food.category_confidence = 0.8
                    else:
                        # Default fallback with warning
                        food.category = Category.FOOD
                        food.category_source = 'default_fallback'
                        food.category_confidence = 0.3
                        self.category_warnings.append(
                            f"Food '{food.food_name}' defaulted to FOOD category"
                        )
                else:
                    # Minimal fallback
                    food.category = Category.FOOD
                    food.category_source = 'minimal_fallback'
                    food.category_confidence = 0.2
                    self.category_warnings.append(
                        f"Food with insufficient data defaulted to FOOD category"
                    )
                    
            except Exception as e:
                logger.error(f"Error assigning category to food: {str(e)}")
                food.category = Category.FOOD
                food.category_source = 'error_fallback'
                food.category_confidence = 0.1
                self.category_warnings.append(
                    f"Error assigning category to food: {str(e)}"
                )

    def _calculate_nutritional_values(self):
        """Calculate nutritional values with error handling"""
        try:
            self.total_weight = sum(food.serving_size for food in self.foods)
            
            if self.total_weight == 0:
                logger.warning("Meal has zero total weight")
                self.category_warnings.append("Meal has zero total weight")
                # Set all nutritional values to 0
                self._set_zero_nutritional_values()
                return
            
            # Calculate weighted nutritional values
            self.energy_kilocalories = self._calculate_weighted_sum('ENERGY (KILOCALORIES)')
            self.energy_kj = self.energy_kilocalories * 4.184  # Convert kcal to kJ
            self.protein = self._calculate_weighted_sum('PROTEIN')
            self.carbohydrate_total = self._calculate_weighted_sum('CARBOHYDRATE, TOTAL')
            self.fibre_total_dietary = self._calculate_weighted_sum('FIBRE, TOTAL DIETARY')
            self.sugars_total = self._calculate_weighted_sum('SUGARS, TOTAL')
            self.fat_total = self._calculate_weighted_sum('FAT, TOTAL')
            self.fatty_acids_saturated_total = self._calculate_weighted_sum('FATTY ACIDS, SATURATED, TOTAL')
            self.sodium = self._calculate_weighted_sum('SODIUM')
            self.calcium = self._calculate_weighted_sum('CALCIUM')
            self.fvnl_percent = self._calculate_fvnl_percent()
            
            # Validate calculated values
            self._validate_nutritional_values()
            
        except Exception as e:
            logger.error(f"Error calculating nutritional values: {str(e)}")
            self.category_warnings.append(f"Nutritional calculation error: {str(e)}")
            self._set_zero_nutritional_values()

    def _set_zero_nutritional_values(self):
        """Set all nutritional values to zero (fallback for errors)"""
        self.energy_kilocalories = 0.0
        self.energy_kj = 0.0
        self.protein = 0.0
        self.carbohydrate_total = 0.0
        self.fibre_total_dietary = 0.0
        self.sugars_total = 0.0
        self.fat_total = 0.0
        self.fatty_acids_saturated_total = 0.0
        self.sodium = 0.0
        self.calcium = 0.0
        self.fvnl_percent = 0.0

    def _validate_nutritional_values(self):
        """Validate calculated nutritional values for reasonableness"""
        warnings = []
        
        # Check for extreme values
        if self.energy_kilocalories > 2000:
            warnings.append(f"Very high energy content: {self.energy_kilocalories:.1f} kcal/100g")
        
        if self.protein > 100:
            warnings.append(f"Extremely high protein: {self.protein:.1f} g/100g")
        
        if self.fat_total > 100:
            warnings.append(f"Extremely high fat: {self.fat_total:.1f} g/100g")
        
        if self.sodium > 5000:
            warnings.append(f"Extremely high sodium: {self.sodium:.1f} mg/100g")
        
        if self.fvnl_percent > 100:
            warnings.append(f"FVNL percent exceeds 100%: {self.fvnl_percent:.1f}%")
        
        # Check for negative values
        nutritional_values = {
            'energy': self.energy_kilocalories,
            'protein': self.protein,
            'carbohydrates': self.carbohydrate_total,
            'fiber': self.fibre_total_dietary,
            'sugars': self.sugars_total,
            'fat': self.fat_total,
            'saturated_fat': self.fatty_acids_saturated_total,
            'sodium': self.sodium,
            'calcium': self.calcium,
            'fvnl_percent': self.fvnl_percent
        }
        
        for name, value in nutritional_values.items():
            if value < 0:
                warnings.append(f"Negative {name} value: {value}")
        
        if warnings:
            self.category_warnings.extend(warnings)
            logger.warning(f"Nutritional validation warnings: {warnings}")

    def _validate_final_categorization(self):
        """Validate final categorization against nutritional profile"""
        try:
            # Check if category makes sense given nutritional profile
            if self.category == Category.BEVERAGE:
                if self.protein > 10 or self.fat_total > 5:
                    self.category_warnings.append(
                        "High protein/fat content unusual for beverage category"
                    )
            
            elif self.category == Category.CHEESE:
                if self.protein < 5 or self.fat_total < 5:
                    self.category_warnings.append(
                        "Low protein/fat content unusual for cheese category"
                    )
            
            elif self.category == Category.OILS_AND_SPREADS:
                if self.fat_total < 20:
                    self.category_warnings.append(
                        "Low fat content unusual for oils/spreads category"
                    )
            
            # Check for inconsistent FVNL content
            if self.fvnl_percent > 80 and self.category not in [Category.FOOD, Category.DAIRY_FOOD]:
                self.category_warnings.append(
                    f"High FVNL content ({self.fvnl_percent:.1f}%) may indicate food category more appropriate"
                )
            
        except Exception as e:
            logger.error(f"Error in final categorization validation: {str(e)}")

    def _calculate_weighted_sum(self, nutrient_name: str) -> float:
        """Calculate weighted sum of a nutrient with error handling"""
        try:
            if self.total_weight == 0:
                return 0.0
            
            total_nutrient = 0.0
            for food in self.foods:
                nutrient_value = food.nutrients.get(nutrient_name, 0)
                if nutrient_value is None:
                    nutrient_value = 0
                total_nutrient += nutrient_value * food.serving_size / 100
            
            return total_nutrient / (self.total_weight / 100)
            
        except Exception as e:
            logger.error(f"Error calculating {nutrient_name}: {str(e)}")
            return 0.0

    def _calculate_fvnl_percent(self) -> float:
        """Calculate FVNL percentage with error handling"""
        try:
            if self.total_weight == 0:
                return 0.0
            
            fvnl_weight = 0.0
            for food in self.foods:
                fvnl_percent = getattr(food, 'fvnl_percent', 0)
                if fvnl_percent is None:
                    fvnl_percent = 0
                fvnl_weight += food.serving_size * (fvnl_percent / 100)
            
            return (fvnl_weight / self.total_weight) * 100
            
        except Exception as e:
            logger.error(f"Error calculating FVNL percent: {str(e)}")
            return 0.0

    def get_category_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of meal categorization"""
        # Calculate food category breakdown
        food_categories = {}
        for food in self.foods:
            cat = food.category.value if food.category else 'unknown'
            if cat not in food_categories:
                food_categories[cat] = {
                    'count': 0, 
                    'weight': 0.0, 
                    'foods': [],
                    'avg_confidence': 0.0
                }
            
            food_categories[cat]['count'] += 1
            food_categories[cat]['weight'] += food.serving_size
            food_categories[cat]['foods'].append({
                'id': food.food_id,
                'name': food.food_name,
                'weight': food.serving_size,
                'confidence': getattr(food, 'category_confidence', 0.0)
            })
        
        # Calculate percentages and average confidence
        for cat_data in food_categories.values():
            cat_data['weight_percent'] = (cat_data['weight'] / self.total_weight) * 100 if self.total_weight > 0 else 0
            if cat_data['foods']:
                cat_data['avg_confidence'] = sum(
                    f['confidence'] for f in cat_data['foods']
                ) / len(cat_data['foods'])
        
        return {
            'meal_category': self.category.value if self.category else 'unknown',
            'category_confidence': self.category_confidence,
            'category_analysis': self.category_analysis,
            'category_warnings': self.category_warnings,
            'nutritional_context': self.nutritional_context,
            'food_categories': food_categories,
            'total_foods': len(self.foods),
            'total_weight': self.total_weight,
            'complexity_score': self.nutritional_context.get('complexity_score', 0.0),
            'is_mixed_meal': len(food_categories) > 1,
            'validation_status': {
                'has_warnings': len(self.category_warnings) > 0,
                'confidence_level': 'high' if self.category_confidence >= 0.8 else 
                                  'medium' if self.category_confidence >= 0.6 else 'low',
                'nutritional_consistency': self._assess_nutritional_consistency()
            }
        }

    def _assess_nutritional_consistency(self) -> str:
        """Assess if nutritional profile is consistent with category"""
        try:
            if self.category == Category.BEVERAGE:
                if self.protein > 10 or self.fat_total > 5:
                    return 'inconsistent'
            elif self.category == Category.CHEESE:
                if self.protein < 5 or self.fat_total < 5:
                    return 'inconsistent'
            elif self.category == Category.OILS_AND_SPREADS:
                if self.fat_total < 20:
                    return 'inconsistent'
            
            return 'consistent'
        except:
            return 'unknown'

    def get_categorization_insights(self) -> Dict[str, Any]:
        """Get insights about the categorization process"""
        return {
            'categorization_method': self.category_analysis.get('reason', 'unknown'),
            'confidence_level': self.category_confidence,
            'primary_factors': self._identify_primary_factors(),
            'potential_alternatives': self._suggest_alternative_categories(),
            'validation_notes': self.category_warnings,
            'nutritional_alignment': self._assess_nutritional_consistency(),
            'complexity_assessment': self._assess_complexity(),
            'recommendations': self._generate_categorization_recommendations()
        }

    def _identify_primary_factors(self) -> List[str]:
        """Identify the primary factors that influenced categorization"""
        factors = []
        
        if self.category_analysis.get('reason') == 'absolute_dominance':
            factors.append(f"Single category dominates ({self.category_analysis.get('dominance_percent', 0):.1f}%)")
        elif self.category_analysis.get('reason') == 'category_specific_significance':
            factors.append(f"Category-specific significance threshold met")
        elif self.category_analysis.get('reason') == 'liquid_meal_dominance':
            factors.append("Liquid meal characteristics detected")
        elif self.category_analysis.get('reason') == 'mixed_meal_analysis':
            factors.append("Complex meal analysis applied")
        
        # Add nutritional factors
        if self.nutritional_context.get('is_high_protein'):
            factors.append("High protein content")
        if self.nutritional_context.get('is_high_fat'):
            factors.append("High fat content")
        if self.nutritional_context.get('is_liquid_dominant'):
            factors.append("Liquid-dominant composition")
        
        return factors

    def _suggest_alternative_categories(self) -> List[Dict[str, Any]]:
        """Suggest alternative categories if appropriate"""
        alternatives = []
        
        if self.category_confidence < 0.7:
            # Import here to avoid circular imports
            from ..utils.meal_categorizer import MealCategorizer
            
            try:
                # Get the full analysis to see other options
                _, analysis = MealCategorizer.determine_meal_category(self.foods)
                category_breakdown = analysis.get('nutritional_context', {}).get('category_breakdown', {})
                
                # Suggest categories with significant representation
                for cat_name, percentage in category_breakdown.items():
                    if percentage >= 25 and cat_name != self.category.value:
                        alternatives.append({
                            'category': cat_name,
                            'percentage': percentage,
                            'reason': f"Significant component ({percentage:.1f}%)"
                        })
                        
            except Exception as e:
                logger.error(f"Error suggesting alternatives: {str(e)}")
        
        return alternatives

    def _assess_complexity(self) -> Dict[str, Any]:
        """Assess meal complexity"""
        complexity_score = self.nutritional_context.get('complexity_score', 0.0)
        category_count = len(set(food.category for food in self.foods if food.category))
        
        return {
            'complexity_score': complexity_score,
            'category_count': category_count,
            'complexity_level': 'high' if complexity_score > 0.8 else 
                               'medium' if complexity_score > 0.5 else 'low',
            'is_simple_meal': category_count <= 2,
            'is_complex_meal': category_count >= 4
        }

    def _generate_categorization_recommendations(self) -> List[str]:
        """Generate recommendations for improving categorization"""
        recommendations = []
        
        if self.category_confidence < 0.6:
            recommendations.append("Consider reviewing food categorizations for accuracy")
        
        if len(self.category_warnings) > 3:
            recommendations.append("Multiple validation warnings - verify input data")
        
        if self.nutritional_context.get('complexity_score', 0) > 0.8:
            recommendations.append("Very complex meal - consider simplifying for more accurate HSR calculation")
        
        if self._assess_nutritional_consistency() == 'inconsistent':
            recommendations.append("Nutritional profile doesn't align with category - review categorization")
        
        return recommendations

    def __repr__(self):
        category_info = f"Category: {self.category.value if self.category else 'None'}"
        if self.category_confidence < 0.8:
            category_info += f" (confidence: {self.category_confidence:.1f})"
        
        warnings_info = f", Warnings: {len(self.category_warnings)}" if self.category_warnings else ""
        
        return (f"Meal({category_info}, Total Weight: {self.total_weight}g, "
                f"Energy: {self.energy_kj:.1f} kJ, SatFat: {self.fatty_acids_saturated_total:.1f} g, "
                f"Total Sugar: {self.sugars_total:.1f} g, Sodium: {self.sodium:.0f} mg, "
                f"Protein: {self.protein:.1f} g, Fiber: {self.fibre_total_dietary:.1f} g, "
                f"Calcium: {self.calcium:.0f} mg, FVNL: {self.fvnl_percent:.1f}%{warnings_info})")