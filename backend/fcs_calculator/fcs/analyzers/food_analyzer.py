from dataclasses import dataclass, field
from typing import Dict, Union
from fcs.models.food_item import FoodItem
from fcs.models.enums import AttributeType, NOVACategory
from fcs.models.exceptions import InvalidScoreError
from fcs.constants.reference_targets import REFERENCE_TARGETS
from fcs.config import MIN_FCS, MAX_FCS

def get_reference_targets():
    return REFERENCE_TARGETS

@dataclass
class FoodAnalyzer:
    REFERENCE_TARGETS: Dict[str, tuple] = field(default_factory=get_reference_targets)

    @staticmethod
    def get_attribute_type(attribute: str) -> AttributeType:
        beneficial_attributes = [
            'vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b6', 'vitamin_b9', 
            'vitamin_b12', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'calcium', 'phosphorus', 
            'magnesium', 'iron', 'zinc', 'copper', 'selenium', 'potassium', 'fruit', 'vegetable', 
            'beans', 'whole_grains', 'nuts', 'seafood', 'yogurt', 'plant_oils', 'alpha_linolenic_acid', 
            'epa_dha', 'total_flavonoids', 'total_carotenoids', 'fiber', 'mcfas', 'fermentation'
        ]
        
        harmful_attributes = [
            'added_sugar', 'nitrites', 'artificial_sweeteners', 'partially_hydrated_oils', 
            'hydrogenated_oils', 'high_fructose_corn_syrup', 'monosodium_glutamate', 'cholesterol', 
            'transfat', 'frying', 'refined_grains', 'red_or_processed_meat', 'sodium'
        ]
        
        ratio_attributes = [
            'unsaturated_to_saturated_fat', 'fiber_to_carbohydrate', 'potassium_to_sodium'
        ]

        if attribute in beneficial_attributes:
            return AttributeType.BENEFICIAL
        elif attribute in harmful_attributes:
            return AttributeType.HARMFUL
        elif attribute in ratio_attributes:
            return AttributeType.RATIO
        else:
            raise ValueError(f"Unknown attribute type for attribute: {attribute}")

    def score_attribute(self, value: float, attribute: str, attribute_type: AttributeType) -> float:
        if attribute not in self.REFERENCE_TARGETS:
            raise ValueError(f"No reference targets for attribute: {attribute}")
        
        low_target, high_target = self.REFERENCE_TARGETS[attribute]
        
        if attribute_type == AttributeType.BENEFICIAL:
            score = 10 * (value - low_target) / (high_target - low_target)
            return max(0, min(10, score))
        elif attribute_type == AttributeType.HARMFUL:
            score = -10 * (value - low_target) / (high_target - low_target)
            return max(-10, min(0, score))
        else:  # RATIO
            score = 20 * (value - low_target) / (high_target - low_target) - 10
            return max(-10, min(10, score))

    def calculate_original_score(self, food_item: FoodItem) -> float:
        domain_scores = {domain: [] for domain in food_item.attributes.keys()}

        for domain, attributes in food_item.attributes.items():
            for attribute, value in attributes.items():
                attribute_type = self.get_attribute_type(attribute)
                score = self.score_attribute(value, attribute, attribute_type)
                domain_scores[domain].append(score)

        # Select top 5 scores for vitamins and minerals
        domain_scores['vitamins'] = sorted(domain_scores['vitamins'], reverse=True)[:5]
        domain_scores['minerals'] = sorted(domain_scores['minerals'], reverse=True)[:5]

        # Averaging and summing domain scores
        averaged_scores = {domain: sum(scores) / len(scores) if scores else 0 for domain, scores in domain_scores.items()}

        weighted_sum = (
            averaged_scores['nutrient_ratios'] +
            averaged_scores['vitamins'] +
            averaged_scores['minerals'] +
            averaged_scores['food_ingredients'] +
            averaged_scores['additives'] +
            averaged_scores['processing'] +
            0.5 * averaged_scores['specific_lipids'] +
            0.5 * averaged_scores['fibers_proteins_phytochemicals']
        )

        return weighted_sum

    def calculate_fcs(self, original_score: float) -> float:
        if not isinstance(original_score, (int, float)):
            raise InvalidScoreError("Original score must be a number.")

        fcs = 1 + 99 * ((original_score + 26.1) / 36.7)
        
        if not MIN_FCS <= fcs <= MAX_FCS:
            raise InvalidScoreError("Calculated FCS is outside the valid range.")

        return round(max(MIN_FCS, min(MAX_FCS, fcs)), 2)

    def categorize_nova(self, food_item: FoodItem) -> NOVACategory:
        processed_ingredients = ['refined_grains', 'red_or_processed_meat']
        ultra_processed_ingredients = ['added_sugar', 'nitrites', 'artificial_sweeteners', 'partially_hydrated_oils', 'hydrogenated_oils', 'high_fructose_corn_syrup', 'monosodium_glutamate']
        
        if any(food_item.attributes['additives'][ingredient] > 0 for ingredient in ultra_processed_ingredients):
            return NOVACategory.ULTRA_PROCESSED_FOODS
        elif any(food_item.attributes['food_ingredients'][ingredient] > 0 for ingredient in processed_ingredients):
            return NOVACategory.PROCESSED_FOODS
        elif food_item.attributes['food_ingredients']['plant_oils'] > 0:
            return NOVACategory.PROCESSED_CULINARY_INGREDIENTS
        else:
            return NOVACategory.MINIMALLY_PROCESSED

    def analyze_food_item(self, food_item: FoodItem) -> Dict[str, Union[float, str]]:
        original_score = self.calculate_original_score(food_item)
        fcs = self.calculate_fcs(original_score)
        nova = self.categorize_nova(food_item)
        food_item.set_nova_category(nova)
        
        return {
            "name": food_item.name,
            "original_score": round(original_score, 2),
            "fcs": fcs,
            "nova_category": nova.name
        }