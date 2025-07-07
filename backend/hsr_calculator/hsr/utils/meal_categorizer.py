"""
Meal Categorizer - Scientifically-improved meal categorization
Incorporates nutritional science and evidence-based logic for more accurate categorization.
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from collections import Counter

from ..models.food import Food
from ..models.category import Category

logger = logging.getLogger(__name__)


@dataclass
class ScientificCategorizationResult:
    """Result of scientific categorization analysis"""
    recommended_category: Category
    confidence: float
    reasoning: List[str]
    nutritional_rationale: str
    alternative_categories: List[Tuple[Category, float, str]]
    scientific_factors: Dict[str, any]


class MealCategorizer:
    """
    Scientific meal categorizer that applies nutritional science principles
    to improve categorization accuracy and resolve category conflicts.
    """
    
    # Scientific thresholds based on nutritional impact research
    SCIENTIFIC_THRESHOLDS = {
        'liquid_dominant': 0.4,           # 40% liquid content triggers liquid analysis
        'energy_density_high': 400,      # kcal/100g - high energy density foods
        'protein_significant': 15,       # g/100g - significant protein content
        'fat_significant': 20,           # g/100g - significant fat content
        'sugar_concern': 15,             # g/100g - concerning sugar levels
        'sodium_concern': 600,           # mg/100g - concerning sodium levels
        'fiber_excellent': 6,            # g/100g - excellent fiber content
        'satiety_threshold': 1.1         # Satiety index threshold
    }
    
    # Nutritional profile templates for each category
    CATEGORY_NUTRITIONAL_PROFILES = {
        Category.BEVERAGE: {
            'expected_energy_range': (0, 200),      # kcal/100g
            'expected_protein_range': (0, 3),       # g/100g
            'expected_fat_range': (0, 1),           # g/100g
            'liquid_percentage_min': 0.8,           # Must be mostly liquid
            'processing_tolerance': 'processed'      # Can be processed
        },
        Category.DAIRY_BEVERAGE: {
            'expected_energy_range': (30, 150),
            'expected_protein_range': (2, 8),
            'expected_fat_range': (0, 6),
            'liquid_percentage_min': 0.7,
            'processing_tolerance': 'processed'
        },
        Category.FOOD: {
            'expected_energy_range': (50, 800),
            'expected_protein_range': (0, 50),
            'expected_fat_range': (0, 50),
            'liquid_percentage_max': 0.3,
            'processing_tolerance': 'any'
        },
        Category.DAIRY_FOOD: {
            'expected_energy_range': (50, 400),
            'expected_protein_range': (3, 30),
            'expected_fat_range': (0, 25),
            'liquid_percentage_max': 0.2,
            'processing_tolerance': 'processed'
        },
        Category.CHEESE: {
            'expected_energy_range': (200, 450),
            'expected_protein_range': (10, 35),
            'expected_fat_range': (15, 35),
            'liquid_percentage_max': 0.1,
            'processing_tolerance': 'processed'
        },
        Category.OILS_AND_SPREADS: {
            'expected_energy_range': (300, 900),
            'expected_protein_range': (0, 5),
            'expected_fat_range': (30, 100),
            'liquid_percentage_max': 0.2,
            'processing_tolerance': 'any'
        }
    }

    @classmethod
    def determine_scientific_category(cls, foods: List[Food]) -> ScientificCategorizationResult:
        """
        Determine meal category using scientific analysis and nutritional principles.
        
        Args:
            foods: List of Food objects with nutritional data
            
        Returns:
            ScientificCategorizationResult with detailed analysis
        """
        if not foods:
            return cls._create_fallback_result(Category.FOOD, "Empty meal")
        
        if len(foods) == 1:
            return cls._analyze_single_food(foods[0])
        
        # Perform comprehensive scientific analysis
        nutritional_analysis = cls._analyze_meal_nutrition(foods)
        category_fitness = cls._evaluate_category_fitness(nutritional_analysis)
        conflict_resolution = cls._resolve_category_conflicts(foods, category_fitness)
        
        # Select best category based on scientific evidence
        recommended_category = cls._select_scientifically_optimal_category(
            category_fitness, conflict_resolution, nutritional_analysis
        )
        
        # Calculate confidence based on multiple factors
        confidence = cls._calculate_scientific_confidence(
            recommended_category, category_fitness, nutritional_analysis
        )
        
        # Generate scientific reasoning
        reasoning = cls._generate_scientific_reasoning(
            recommended_category, nutritional_analysis, category_fitness
        )
        
        # Identify alternative categories
        alternatives = cls._identify_scientific_alternatives(
            recommended_category, category_fitness
        )
        
        return ScientificCategorizationResult(
            recommended_category=recommended_category,
            confidence=confidence,
            reasoning=reasoning,
            nutritional_rationale=cls._generate_nutritional_rationale(
                recommended_category, nutritional_analysis
            ),
            alternative_categories=alternatives,
            scientific_factors=nutritional_analysis
        )

    @classmethod
    def _analyze_meal_nutrition(cls, foods: List[Food]) -> Dict[str, any]:
        """Comprehensive nutritional analysis of the meal"""
        total_weight = sum(food.serving_size for food in foods)
        
        if total_weight == 0:
            return cls._get_empty_nutrition_analysis()
        
        # Calculate weighted nutritional values per 100g
        nutrition = {
            'energy_kcal': sum(food.nutrients.get('ENERGY (KILOCALORIES)', 0) * food.serving_size / 100 for food in foods) / (total_weight / 100),
            'protein': sum(food.nutrients.get('PROTEIN', 0) * food.serving_size / 100 for food in foods) / (total_weight / 100),
            'fat_total': sum(food.nutrients.get('FAT, TOTAL', 0) * food.serving_size / 100 for food in foods) / (total_weight / 100),
            'saturated_fat': sum(food.nutrients.get('FATTY ACIDS, SATURATED, TOTAL', 0) * food.serving_size / 100 for food in foods) / (total_weight / 100),
            'carbohydrates': sum(food.nutrients.get('CARBOHYDRATE, TOTAL', 0) * food.serving_size / 100 for food in foods) / (total_weight / 100),
            'sugars': sum(food.nutrients.get('SUGARS, TOTAL', 0) * food.serving_size / 100 for food in foods) / (total_weight / 100),
            'fiber': sum(food.nutrients.get('FIBRE, TOTAL DIETARY', 0) * food.serving_size / 100 for food in foods) / (total_weight / 100),
            'sodium': sum(food.nutrients.get('SODIUM', 0) * food.serving_size / 100 for food in foods) / (total_weight / 100),
            'total_weight': total_weight
        }
        
        # Calculate auxiliary metrics first (needed for satiety calculation)
        liquid_percentage = cls._calculate_liquid_percentage(foods)
        processing_level = cls._assess_overall_processing_level(foods)
        natural_content_score = cls._calculate_natural_content_score(foods)
        
        # Add liquid percentage to nutrition for satiety calculation
        nutrition['liquid_percentage'] = liquid_percentage
        
        # Calculate derived metrics
        nutrition.update({
            'energy_density_level': cls._categorize_energy_density(nutrition['energy_kcal']),
            'protein_level': cls._categorize_protein_content(nutrition['protein']),
            'fat_level': cls._categorize_fat_content(nutrition['fat_total']),
            'sugar_level': cls._categorize_sugar_content(nutrition['sugars']),
            'sodium_level': cls._categorize_sodium_content(nutrition['sodium']),
            'fiber_level': cls._categorize_fiber_content(nutrition['fiber']),
            'satiety_index': cls._calculate_meal_satiety_index(nutrition),
            'processing_level': processing_level,
            'natural_content_score': natural_content_score,
            'nutritional_density': cls._calculate_nutritional_density(nutrition)
        })
        
        return nutrition

    @classmethod
    def _evaluate_category_fitness(cls, nutrition: Dict[str, any]) -> Dict[Category, float]:
        """Evaluate how well the meal fits each category based on nutritional profile"""
        fitness_scores = {}
        
        for category, profile in cls.CATEGORY_NUTRITIONAL_PROFILES.items():
            score = 0.0
            max_score = 0.0
            
            # Energy fitness
            energy_min, energy_max = profile['expected_energy_range']
            if energy_min <= nutrition['energy_kcal'] <= energy_max:
                score += 20
            else:
                # Penalty for being outside range
                if nutrition['energy_kcal'] < energy_min:
                    score += max(0, 20 - (energy_min - nutrition['energy_kcal']) / 10)
                else:
                    score += max(0, 20 - (nutrition['energy_kcal'] - energy_max) / 20)
            max_score += 20
            
            # Protein fitness
            protein_min, protein_max = profile['expected_protein_range']
            if protein_min <= nutrition['protein'] <= protein_max:
                score += 15
            else:
                if nutrition['protein'] < protein_min:
                    score += max(0, 15 - (protein_min - nutrition['protein']) * 2)
                else:
                    score += max(0, 15 - (nutrition['protein'] - protein_max) / 2)
            max_score += 15
            
            # Fat fitness
            fat_min, fat_max = profile['expected_fat_range']
            if fat_min <= nutrition['fat_total'] <= fat_max:
                score += 15
            else:
                if nutrition['fat_total'] < fat_min:
                    score += max(0, 15 - (fat_min - nutrition['fat_total']) * 2)
                else:
                    score += max(0, 15 - (nutrition['fat_total'] - fat_max) / 3)
            max_score += 15
            
            # Liquid percentage fitness
            if 'liquid_percentage_min' in profile:
                if nutrition['liquid_percentage'] >= profile['liquid_percentage_min']:
                    score += 25
                else:
                    score += nutrition['liquid_percentage'] / profile['liquid_percentage_min'] * 25
            elif 'liquid_percentage_max' in profile:
                if nutrition['liquid_percentage'] <= profile['liquid_percentage_max']:
                    score += 25
                else:
                    excess = nutrition['liquid_percentage'] - profile['liquid_percentage_max']
                    score += max(0, 25 - excess * 50)
            max_score += 25
            
            # Processing level fitness
            processing_tolerance = profile.get('processing_tolerance', 'any')
            if processing_tolerance == 'any':
                score += 15
            elif processing_tolerance == 'processed' and nutrition['processing_level'] != 'ultra_processed':
                score += 15
            elif processing_tolerance == 'minimally_processed' and nutrition['processing_level'] == 'minimally_processed':
                score += 15
            elif processing_tolerance == 'processed' and nutrition['processing_level'] == 'ultra_processed':
                score += 10  # Partial credit
            max_score += 15
            
            # Special bonuses for category-specific characteristics
            if category == Category.CHEESE and nutrition['protein'] >= 15 and nutrition['fat_total'] >= 15:
                score += 10
                max_score += 10
            elif category in [Category.BEVERAGE, Category.DAIRY_BEVERAGE] and nutrition['liquid_percentage'] > 0.8:
                score += 10
                max_score += 10
            elif category == Category.OILS_AND_SPREADS and nutrition['fat_total'] > 50:
                score += 10
                max_score += 10
            
            # Normalize to 0-1 scale
            fitness_scores[category] = score / max_score if max_score > 0 else 0
        
        return fitness_scores

    @classmethod
    def _resolve_category_conflicts(cls, foods: List[Food], category_fitness: Dict[Category, float]) -> Dict[str, any]:
        """Resolve conflicts when multiple categories have similar fitness scores"""
        # Get top categories
        sorted_categories = sorted(category_fitness.items(), key=lambda x: x[1], reverse=True)
        top_category, top_score = sorted_categories[0]
        
        conflicts = []
        for category, score in sorted_categories[1:]:
            if abs(score - top_score) < 0.15:  # Within 15% is considered a conflict
                conflicts.append((category, score, abs(score - top_score)))
        
        resolution_strategy = "clear_winner"
        tie_breaker = None
        
        if conflicts:
            resolution_strategy = "conflict_resolution"
            # Apply tie-breaking rules
            tie_breaker = cls._apply_tie_breaking_rules(top_category, conflicts, foods)
        
        return {
            'has_conflicts': len(conflicts) > 0,
            'conflicts': conflicts,
            'resolution_strategy': resolution_strategy,
            'tie_breaker': tie_breaker,
            'top_category': top_category,
            'top_score': top_score
        }

    @classmethod
    def _apply_tie_breaking_rules(cls, top_category: Category, conflicts: List, foods: List[Food]) -> Dict[str, any]:
        """Apply scientific tie-breaking rules for category conflicts"""
        tie_breaker = {
            'rule_applied': None,
            'winner': top_category,
            'reasoning': "Default to highest scoring category"
        }
        
        # Rule 1: Liquid dominance
        liquid_percentage = cls._calculate_liquid_percentage(foods)
        if liquid_percentage > 0.6:
            liquid_categories = [Category.BEVERAGE, Category.DAIRY_BEVERAGE]
            for category, _, _ in conflicts:
                if category in liquid_categories:
                    tie_breaker.update({
                        'rule_applied': 'liquid_dominance',
                        'winner': category,
                        'reasoning': f'Liquid content ({liquid_percentage:.1%}) favors liquid categories'
                    })
                    break
        
        # Rule 2: Protein-fat profile for cheese/dairy
        nutrition = cls._analyze_meal_nutrition(foods)
        if nutrition['protein'] >= 15 and nutrition['fat_total'] >= 15:
            cheese_dairy_categories = [Category.CHEESE, Category.DAIRY_FOOD]
            for category, _, _ in conflicts:
                if category in cheese_dairy_categories:
                    tie_breaker.update({
                        'rule_applied': 'protein_fat_profile',
                        'winner': Category.CHEESE if category == Category.CHEESE else category,
                        'reasoning': 'High protein and fat content indicates dairy/cheese category'
                    })
                    break
        
        # Rule 3: Energy density for oils/spreads
        if nutrition['energy_kcal'] > 500 and nutrition['fat_total'] > 40:
            for category, _, _ in conflicts:
                if category == Category.OILS_AND_SPREADS:
                    tie_breaker.update({
                        'rule_applied': 'energy_density',
                        'winner': Category.OILS_AND_SPREADS,
                        'reasoning': 'Very high energy density and fat content indicates oils/spreads'
                    })
                    break
        
        # Rule 4: Default to most inclusive category (FOOD)
        if tie_breaker['rule_applied'] is None:
            for category, _, _ in conflicts:
                if category == Category.FOOD:
                    tie_breaker.update({
                        'rule_applied': 'inclusive_default',
                        'winner': Category.FOOD,
                        'reasoning': 'Default to general food category for mixed meals'
                    })
                    break
        
        return tie_breaker

    @classmethod
    def _select_scientifically_optimal_category(cls, category_fitness: Dict[Category, float], 
                                              conflict_resolution: Dict[str, any], 
                                              nutritional_analysis: Dict[str, any]) -> Category:
        """Select the scientifically optimal category based on all evidence"""
        
        if conflict_resolution['has_conflicts'] and conflict_resolution['tie_breaker']:
            return conflict_resolution['tie_breaker']['winner']
        
        # No conflicts - return highest scoring category
        return max(category_fitness.items(), key=lambda x: x[1])[0]

    @classmethod
    def _calculate_scientific_confidence(cls, recommended_category: Category, 
                                       category_fitness: Dict[Category, float], 
                                       nutritional_analysis: Dict[str, any]) -> float:
        """Calculate confidence in the scientific categorization"""
        base_confidence = category_fitness[recommended_category]
        
        # Adjust for nutritional consistency
        profile = cls.CATEGORY_NUTRITIONAL_PROFILES[recommended_category]
        consistency_bonus = 0.0
        
        # Energy consistency
        energy_min, energy_max = profile['expected_energy_range']
        if energy_min <= nutritional_analysis['energy_kcal'] <= energy_max:
            consistency_bonus += 0.1
        
        # Liquid percentage consistency
        if 'liquid_percentage_min' in profile:
            if nutritional_analysis['liquid_percentage'] >= profile['liquid_percentage_min']:
                consistency_bonus += 0.1
        elif 'liquid_percentage_max' in profile:
            if nutritional_analysis['liquid_percentage'] <= profile['liquid_percentage_max']:
                consistency_bonus += 0.1
        
        # Processing level consistency
        if profile.get('processing_tolerance') == 'any':
            consistency_bonus += 0.05
        
        # Penalty for data quality issues
        data_quality_penalty = 0.0
        if nutritional_analysis['protein'] == 0:
            data_quality_penalty += 0.05
        if nutritional_analysis['fiber'] == 0:
            data_quality_penalty += 0.03
        
        final_confidence = base_confidence + consistency_bonus - data_quality_penalty
        return max(0.1, min(1.0, final_confidence))

    @classmethod
    def _generate_scientific_reasoning(cls, recommended_category: Category, 
                                     nutritional_analysis: Dict[str, any], 
                                     category_fitness: Dict[Category, float]) -> List[str]:
        """Generate scientific reasoning for the categorization decision"""
        reasoning = []
        
        # Primary reason based on highest fitness score
        fitness_score = category_fitness[recommended_category]
        reasoning.append(f"Best nutritional profile match (fitness: {fitness_score:.2f})")
        
        # Specific nutritional factors
        nutrition = nutritional_analysis
        
        if recommended_category in [Category.BEVERAGE, Category.DAIRY_BEVERAGE]:
            reasoning.append(f"High liquid content ({nutrition['liquid_percentage']:.1%})")
            if nutrition['energy_kcal'] < 150:
                reasoning.append("Low energy density appropriate for beverages")
        
        elif recommended_category == Category.CHEESE:
            reasoning.append(f"High protein ({nutrition['protein']:.1f}g/100g) and fat ({nutrition['fat_total']:.1f}g/100g)")
            reasoning.append("Nutritional profile consistent with cheese products")
        
        elif recommended_category == Category.OILS_AND_SPREADS:
            reasoning.append(f"Very high energy density ({nutrition['energy_kcal']:.0f} kcal/100g)")
            reasoning.append(f"High fat content ({nutrition['fat_total']:.1f}g/100g)")
        
        elif recommended_category == Category.FOOD:
            reasoning.append("Balanced nutritional profile suitable for general food category")
            if nutrition['liquid_percentage'] < 0.3:
                reasoning.append("Predominantly solid food characteristics")
        
        # Add satiety and processing considerations
        if nutrition['satiety_index'] > 1.1:
            reasoning.append("High satiety index supports solid food categorization")
        
        if nutrition['processing_level'] == 'minimally_processed':
            reasoning.append("Minimally processed foods align with whole food categories")
        
        return reasoning

    @classmethod
    def _generate_nutritional_rationale(cls, recommended_category: Category, 
                                      nutritional_analysis: Dict[str, any]) -> str:
        """Generate detailed nutritional rationale for the categorization"""
        nutrition = nutritional_analysis
        
        rationale_templates = {
            Category.BEVERAGE: f"Energy density of {nutrition['energy_kcal']:.0f} kcal/100g and {nutrition['liquid_percentage']:.1%} liquid content align with beverage standards. Low protein ({nutrition['protein']:.1f}g) and fat ({nutrition['fat_total']:.1f}g) content consistent with typical beverages.",
            
            Category.DAIRY_BEVERAGE: f"Moderate energy density ({nutrition['energy_kcal']:.0f} kcal/100g) with significant liquid content ({nutrition['liquid_percentage']:.1%}) and moderate protein ({nutrition['protein']:.1f}g) typical of dairy beverages.",
            
            Category.CHEESE: f"High energy density ({nutrition['energy_kcal']:.0f} kcal/100g) with substantial protein ({nutrition['protein']:.1f}g) and fat ({nutrition['fat_total']:.1f}g) content characteristic of cheese products. Low liquid content ({nutrition['liquid_percentage']:.1%}) confirms solid dairy product classification.",
            
            Category.OILS_AND_SPREADS: f"Very high energy density ({nutrition['energy_kcal']:.0f} kcal/100g) dominated by fat content ({nutrition['fat_total']:.1f}g/100g) with minimal protein ({nutrition['protein']:.1f}g) typical of oils and spreads.",
            
            Category.FOOD: f"Balanced nutritional profile with {nutrition['energy_kcal']:.0f} kcal/100g energy density, {nutrition['protein']:.1f}g protein, and {nutrition['fat_total']:.1f}g fat. Predominantly solid composition ({nutrition['liquid_percentage']:.1%} liquid) suitable for general food category.",
            
            Category.DAIRY_FOOD: f"Moderate energy density ({nutrition['energy_kcal']:.0f} kcal/100g) with good protein content ({nutrition['protein']:.1f}g) and moderate fat ({nutrition['fat_total']:.1f}g) consistent with dairy food products."
        }
        
        return rationale_templates.get(recommended_category, "Standard nutritional analysis applied.")

    @classmethod
    def _identify_scientific_alternatives(cls, recommended_category: Category, 
                                        category_fitness: Dict[Category, float]) -> List[Tuple[Category, float, str]]:
        """Identify scientifically viable alternative categories"""
        alternatives = []
        recommended_score = category_fitness[recommended_category]
        
        for category, score in category_fitness.items():
            if category != recommended_category and score >= 0.5:  # At least 50% fitness
                confidence_diff = recommended_score - score
                
                if confidence_diff < 0.2:
                    strength = "Strong alternative"
                elif confidence_diff < 0.4:
                    strength = "Viable alternative"
                else:
                    strength = "Possible alternative"
                
                reason = cls._get_alternative_reason(category, score)
                alternatives.append((category, score, f"{strength}: {reason}"))
        
        return sorted(alternatives, key=lambda x: x[1], reverse=True)

    @classmethod
    def _get_alternative_reason(cls, category: Category, score: float) -> str:
        """Get reason why a category is an alternative"""
        reasons = {
            Category.BEVERAGE: "If considering liquid characteristics primarily",
            Category.DAIRY_BEVERAGE: "If dairy content is significant",
            Category.FOOD: "If treating as general food product",
            Category.DAIRY_FOOD: "If dairy solids are primary component",
            Category.CHEESE: "If high protein/fat content is emphasized",
            Category.OILS_AND_SPREADS: "If fat content dominates nutritional profile"
        }
        
        return reasons.get(category, f"Based on {score:.1%} nutritional fitness")

    # Helper methods for nutritional analysis
    @classmethod
    def _categorize_energy_density(cls, energy_kcal: float) -> str:
        """Categorize energy density level"""
        if energy_kcal < 100:
            return "very_low"
        elif energy_kcal < 200:
            return "low"
        elif energy_kcal < 400:
            return "moderate"
        elif energy_kcal < 600:
            return "high"
        else:
            return "very_high"

    @classmethod
    def _categorize_protein_content(cls, protein: float) -> str:
        """Categorize protein content level"""
        if protein < 3:
            return "very_low"
        elif protein < 8:
            return "low"
        elif protein < 15:
            return "moderate"
        elif protein < 25:
            return "high"
        else:
            return "very_high"

    @classmethod
    def _categorize_fat_content(cls, fat: float) -> str:
        """Categorize fat content level"""
        if fat < 3:
            return "very_low"
        elif fat < 10:
            return "low"
        elif fat < 20:
            return "moderate"
        elif fat < 35:
            return "high"
        else:
            return "very_high"

    @classmethod
    def _categorize_sugar_content(cls, sugar: float) -> str:
        """Categorize sugar content level"""
        if sugar < 5:
            return "low"
        elif sugar < 15:
            return "moderate"
        elif sugar < 25:
            return "high"
        else:
            return "very_high"

    @classmethod
    def _categorize_sodium_content(cls, sodium: float) -> str:
        """Categorize sodium content level"""
        if sodium < 200:
            return "low"
        elif sodium < 600:
            return "moderate"
        elif sodium < 1000:
            return "high"
        else:
            return "very_high"

    @classmethod
    def _categorize_fiber_content(cls, fiber: float) -> str:
        """Categorize fiber content level"""
        if fiber < 2:
            return "low"
        elif fiber < 6:
            return "moderate"
        elif fiber < 10:
            return "high"
        else:
            return "very_high"

    @classmethod
    def _calculate_meal_satiety_index(cls, nutrition: Dict[str, any]) -> float:
        """Calculate meal satiety index based on composition"""
        base_satiety = 1.0
        
        # Protein boost
        if nutrition['protein'] >= 20:
            base_satiety *= 1.2
        elif nutrition['protein'] >= 15:
            base_satiety *= 1.15
        elif nutrition['protein'] >= 10:
            base_satiety *= 1.1
        
        # Fiber boost
        if nutrition['fiber'] >= 10:
            base_satiety *= 1.2
        elif nutrition['fiber'] >= 6:
            base_satiety *= 1.15
        elif nutrition['fiber'] >= 3:
            base_satiety *= 1.1
        
        # Liquid penalty
        if nutrition['liquid_percentage'] > 0.5:
            base_satiety *= 0.8
        elif nutrition['liquid_percentage'] > 0.2:
            base_satiety *= 0.9
        
        return max(0.5, min(1.5, base_satiety))

    @classmethod
    def _assess_overall_processing_level(cls, foods: List[Food]) -> str:
        """Assess overall processing level of the meal"""
        processing_scores = []
        
        for food in foods:
            food_name = food.food_name.lower()
            
            if any(term in food_name for term in ['raw', 'fresh', 'whole', 'natural']):
                processing_scores.append(1)
            elif any(term in food_name for term in ['canned', 'frozen', 'dried', 'cooked']):
                processing_scores.append(2)
            elif any(term in food_name for term in ['processed', 'enriched', 'flavored', 'instant']):
                processing_scores.append(3)
            else:
                processing_scores.append(2)  # Default to processed
        
        avg_score = sum(processing_scores) / len(processing_scores) if processing_scores else 2
        
        if avg_score <= 1.3:
            return 'minimally_processed'
        elif avg_score <= 2.3:
            return 'processed'
        else:
            return 'ultra_processed'

    @classmethod
    def _calculate_liquid_percentage(cls, foods: List[Food]) -> float:
        """Calculate percentage of meal that is liquid"""
        total_weight = sum(food.serving_size for food in foods)
        if total_weight == 0:
            return 0.0
        
        liquid_weight = 0.0
        for food in foods:
            food_name = food.food_name.lower()
            if any(term in food_name for term in ['juice', 'drink', 'beverage', 'milk', 'water']):
                liquid_weight += food.serving_size
            elif 'soup' in food_name:
                liquid_weight += food.serving_size * 0.7  # Soup is partially liquid
        
        return liquid_weight / total_weight

    @classmethod
    def _calculate_natural_content_score(cls, foods: List[Food]) -> float:
        """Calculate natural content score based on food types"""
        natural_scores = []
        
        for food in foods:
            food_name = food.food_name.lower()
            
            if any(term in food_name for term in ['fresh', 'raw', 'whole', 'natural', 'organic']):
                natural_scores.append(1.0)
            elif any(term in food_name for term in ['fruit', 'vegetable', 'nut', 'seed']):
                natural_scores.append(0.8)
            elif any(term in food_name for term in ['processed', 'artificial', 'synthetic']):
                natural_scores.append(0.2)
            else:
                natural_scores.append(0.5)
        
        return sum(natural_scores) / len(natural_scores) if natural_scores else 0.5

    @classmethod
    def _calculate_nutritional_density(cls, nutrition: Dict[str, any]) -> float:
        """Calculate overall nutritional density score"""
        # Simple nutritional density based on beneficial nutrients per calorie
        if nutrition['energy_kcal'] == 0:
            return 0.0
        
        beneficial_score = (
            nutrition['protein'] * 4 +       # Protein value
            nutrition['fiber'] * 8 +         # Fiber value (higher weight)
            min(nutrition['sugars'], 10) * 2 # Natural sugars (capped)
        )
        
        density = beneficial_score / nutrition['energy_kcal'] * 100
        return min(1.0, density / 50)  # Normalize to 0-1 scale

    @classmethod
    def _create_fallback_result(cls, category: Category, reason: str) -> ScientificCategorizationResult:
        """Create fallback result for edge cases"""
        return ScientificCategorizationResult(
            recommended_category=category,
            confidence=0.3,
            reasoning=[reason],
            nutritional_rationale=f"Fallback categorization: {reason}",
            alternative_categories=[],
            scientific_factors=cls._get_empty_nutrition_analysis()
        )

    @classmethod
    def _analyze_single_food(cls, food: Food) -> ScientificCategorizationResult:
        """Analyze single food for categorization"""
        return ScientificCategorizationResult(
            recommended_category=food.category,
            confidence=1.0,
            reasoning=["Single food item uses pre-assigned category"],
            nutritional_rationale="Individual food categorization maintained",
            alternative_categories=[],
            scientific_factors={
                'food_name': food.food_name,
                'category': food.category.value,
                'serving_size': food.serving_size
            }
        )

    @classmethod
    def _get_empty_nutrition_analysis(cls) -> Dict[str, any]:
        """Get empty nutrition analysis for fallback cases"""
        return {
            'energy_kcal': 0, 'protein': 0, 'fat_total': 0, 'saturated_fat': 0,
            'carbohydrates': 0, 'sugars': 0, 'fiber': 0, 'sodium': 0,
            'total_weight': 0, 'energy_density_level': 'unknown',
            'protein_level': 'unknown', 'fat_level': 'unknown',
            'sugar_level': 'unknown', 'sodium_level': 'unknown',
            'fiber_level': 'unknown', 'satiety_index': 1.0,
            'processing_level': 'unknown', 'liquid_percentage': 0.0,
            'natural_content_score': 0.0, 'nutritional_density': 0.0
        } 