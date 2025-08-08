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
        # FCS 2.0 Beneficial attributes (linear scaling 0-10 points)
        beneficial_attributes = [
            # Vitamins
            'vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b6', 'vitamin_b9', 
            'vitamin_b12', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k',
            # Minerals (excluding sodium which is harmful)
            'calcium', 'phosphorus', 'magnesium', 'iron', 'zinc', 'copper', 'selenium', 
            'potassium', 'manganese', 'chromium', 'molybdenum',
            # Food ingredients (beneficial)
            'fruit', 'vegetable', 'beans', 'whole_grains', 'nuts', 'seafood', 'yogurt', 'plant_oils',
            # Beneficial lipids
            'alpha_linolenic_acid', 'epa_dha', 'mcfas', 'oleic_acid', 'linoleic_acid',
            'monounsaturated_fat', 'polyunsaturated_fat',
            # Fiber and protein
            'fiber', 'protein', 'amino_acid_score',
            # Phytochemicals
            'total_flavonoids', 'total_carotenoids', 'anthocyanins', 'isoflavones', 'proanthocyanidins', 'lignans',
            'choline', 'betaine',
            # Processing (beneficial)
            'fermentation', 'minimal_processing'
        ]
        
        # FCS 2.0 Harmful attributes (inverse scaling -10 to 0 points)  
        harmful_attributes = [
            # Food ingredients (harmful)
            'added_sugar', 'refined_grains', 'red_or_processed_meat',
            # Additives
            'nitrites', 'artificial_sweeteners', 'partially_hydrated_oils', 'hydrogenated_oils', 
            'high_fructose_corn_syrup', 'monosodium_glutamate', 'artificial_colors', 'preservatives',
            # Processing (harmful)
            'nova_processing', 'frying', 'smoking', 'canning',
            # Harmful nutrients/lipids
            'cholesterol', 'transfat', 'sodium', 'saturated_fat', 'total_sugars'
        ]
        
        # FCS 2.0 Ratio attributes (log-linear scaling -10 to 10 points)
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
        """
        FCS 2.0 Domain-based scoring with proper weighting and selection methodology
        """
        domain_scores = {}
        
        # Calculate individual attribute scores for each domain
        raw_domain_scores = {domain: [] for domain in food_item.attributes.keys()}
        
        for domain, attributes in food_item.attributes.items():
            for attribute, value in attributes.items():
                try:
                    attribute_type = self.get_attribute_type(attribute)
                    score = self.score_attribute(value, attribute, attribute_type)
                    raw_domain_scores[domain].append(score)
                except ValueError:
                    # Skip unknown attributes
                    continue
        
        # Domain 1: Nutrient Ratios (full weight, arithmetic mean)
        if raw_domain_scores['nutrient_ratios']:
            domain_scores['nutrient_ratios'] = sum(raw_domain_scores['nutrient_ratios']) / len(raw_domain_scores['nutrient_ratios'])
        else:
            domain_scores['nutrient_ratios'] = 0
            
        # Domain 2: Vitamins (full weight, top 5 selection)
        if raw_domain_scores['vitamins']:
            top_5_vitamins = sorted(raw_domain_scores['vitamins'], reverse=True)[:5]
            domain_scores['vitamins'] = sum(top_5_vitamins) / len(top_5_vitamins) if top_5_vitamins else 0
        else:
            domain_scores['vitamins'] = 0
            
        # Domain 3: Minerals (full weight, top 5 selection) 
        if raw_domain_scores['minerals']:
            top_5_minerals = sorted(raw_domain_scores['minerals'], reverse=True)[:5]
            domain_scores['minerals'] = sum(top_5_minerals) / len(top_5_minerals) if top_5_minerals else 0
        else:
            domain_scores['minerals'] = 0
            
        # Domain 4: Food Ingredients (full weight, summation method per FCS 2.0)
        if raw_domain_scores['food_ingredients']:
            domain_scores['food_ingredients'] = sum(raw_domain_scores['food_ingredients'])
        else:
            domain_scores['food_ingredients'] = 0
            
        # Domain 5: Additives (full weight, arithmetic mean)
        if raw_domain_scores['additives']:
            domain_scores['additives'] = sum(raw_domain_scores['additives']) / len(raw_domain_scores['additives'])
        else:
            domain_scores['additives'] = 0
            
        # Domain 6: Processing (full weight, weighted calculation per Food Compass methodology)
        # NOVA gets full weight, fermentation and frying get half weight
        if raw_domain_scores['processing']:
            processing_attrs = food_item.attributes['processing']
            nova_score = processing_attrs.get('nova_processing', 0) * 1.0  # Full weight
            fermentation_score = processing_attrs.get('fermentation', 0) * 0.5  # Half weight
            frying_score = processing_attrs.get('frying', 0) * 0.5  # Half weight
            other_scores = sum([
                self.score_attribute(processing_attrs.get(attr, 0), attr, self.get_attribute_type(attr))
                for attr in ['minimal_processing', 'pasteurization', 'smoking', 'canning']
                if processing_attrs.get(attr, 0) != 0
            ])
            
            # Weighted average: NOVA(1.0) + fermentation(0.5) + frying(0.5) + others
            total_weight = 1.0 + 0.5 + 0.5 + (len([attr for attr in ['minimal_processing', 'pasteurization', 'smoking', 'canning'] if processing_attrs.get(attr, 0) != 0]))
            domain_scores['processing'] = (nova_score + fermentation_score + frying_score + other_scores) / total_weight if total_weight > 0 else 0
        else:
            domain_scores['processing'] = 0
            
        # Domain 7: Specific Lipids (half weight, top 3 selection)
        if raw_domain_scores['specific_lipids']:
            top_3_lipids = sorted(raw_domain_scores['specific_lipids'], reverse=True)[:3]
            domain_scores['specific_lipids'] = sum(top_3_lipids) / len(top_3_lipids) if top_3_lipids else 0
        else:
            domain_scores['specific_lipids'] = 0
            
        # Domain 8: Fiber and Protein (half weight, arithmetic mean)
        if raw_domain_scores['fiber_protein']:
            domain_scores['fiber_protein'] = sum(raw_domain_scores['fiber_protein']) / len(raw_domain_scores['fiber_protein'])
        else:
            domain_scores['fiber_protein'] = 0
            
        # Domain 9: Phytochemicals (half weight, arithmetic mean)
        if raw_domain_scores['phytochemicals']:
            domain_scores['phytochemicals'] = sum(raw_domain_scores['phytochemicals']) / len(raw_domain_scores['phytochemicals'])
        else:
            domain_scores['phytochemicals'] = 0

        # FCS 2.0 Weighted sum with proper domain weights
        weighted_sum = (
            # Full weight domains (1-6)
            domain_scores['nutrient_ratios'] +
            domain_scores['vitamins'] +
            domain_scores['minerals'] +
            domain_scores['food_ingredients'] +
            domain_scores['additives'] +
            domain_scores['processing'] +
            # Half weight domains (7-9) 
            0.5 * domain_scores['specific_lipids'] +
            0.5 * domain_scores['fiber_protein'] +
            0.5 * domain_scores['phytochemicals']
        )

        # Optional debug logging (can be enabled for troubleshooting)
        # print(f"DEBUG Domain Scores:")
        # for domain, score in domain_scores.items():
        #     weight = 0.5 if domain in ['specific_lipids', 'fiber_protein', 'phytochemicals'] else 1.0
        #     print(f"  {domain}: {score:.2f} (weight: {weight})")
        # print(f"DEBUG: Total weighted sum = {weighted_sum:.2f}")

        return weighted_sum

    def calculate_fcs(self, original_score: float) -> float:
        if not isinstance(original_score, (int, float)):
            raise InvalidScoreError("Original score must be a number.")

        # FCS 2.0 transformation: Map domain scores to 1-100 scale
        # With 9 domains, scores typically range from about -90 to +90
        # Domain scoring: -10 to +10 per domain, with some half-weighted
        # Expected range: roughly -70 to +70 for realistic foods
        
        # Improved transformation formula based on expected score distribution
        # Maps typical score range (-70 to +70) to FCS range (1 to 100)
        min_expected_score = -70  # Very poor nutritional quality
        max_expected_score = 70   # Excellent nutritional quality
        
        # Linear transformation to 1-100 scale
        fcs = 1 + 99 * ((original_score - min_expected_score) / (max_expected_score - min_expected_score))
        
        # Debug logging to understand the calculation
        print(f"DEBUG: original_score = {original_score}")
        print(f"DEBUG: Expected score range: {min_expected_score} to {max_expected_score}")
        print(f"DEBUG: fcs calculation = 1 + 99 * (({original_score} - {min_expected_score}) / {max_expected_score - min_expected_score})")
        print(f"DEBUG: fcs = {fcs}")
        print(f"DEBUG: Valid range: {MIN_FCS} <= {fcs} <= {MAX_FCS}")
        
        # Clamp to valid range instead of raising error - some foods may be extreme
        fcs_clamped = max(MIN_FCS, min(MAX_FCS, fcs))
        
        if fcs != fcs_clamped:
            print(f"DEBUG: FCS was clamped from {fcs} to {fcs_clamped}")

        return round(fcs_clamped, 2)

    def categorize_nova(self, food_item: FoodItem) -> NOVACategory:
        """
        NOVA categorization for mixed dishes and single foods
        Uses processing level determined by CNF analysis, with special handling for mixed dishes
        """
        # Get the processing level determined by CNF integrator
        processing_level = food_item.get_nova_processing_level()
        
        print(f"DEBUG NOVA: Using processing level {processing_level} determined by CNF analysis for: {food_item.name}")
        
        # Special case: Mixed dishes (processing_level = -1)
        if processing_level == -1:
            print(f"DEBUG NOVA: Mixed dish detected - no single NOVA category assignment")
            # Return a default category but mark it as mixed in the result
            return NOVACategory.MINIMALLY_PROCESSED  # Will be overridden in analysis result
        
        # Map processing level to NOVA category for single foods
        level_to_category = {
            1: NOVACategory.MINIMALLY_PROCESSED,
            2: NOVACategory.PROCESSED_CULINARY_INGREDIENTS, 
            3: NOVACategory.PROCESSED_FOODS,
            4: NOVACategory.ULTRA_PROCESSED_FOODS
        }
        
        nova_category = level_to_category.get(processing_level, NOVACategory.MINIMALLY_PROCESSED)
        
        print(f"DEBUG NOVA: Mapped processing level {processing_level} to NOVA category: {nova_category.name}")
        
        return nova_category

    def analyze_food_item(self, food_item: FoodItem) -> Dict[str, Union[float, str]]:
        # Get NOVA category using the processing level determined by CNF analysis
        nova = self.categorize_nova(food_item)
        food_item.set_nova_category(nova)
        
        # NOVA processing score is already set by CNF integrator, just verify it
        current_nova_score = food_item.attributes['processing'].get('nova_processing', 0)
        processing_level = food_item.get_nova_processing_level()
        
        # Handle mixed dishes vs single foods
        if processing_level == -1:
            nova_category_display = "MIXED_PROCESSING_LEVELS"
            print(f"DEBUG: Mixed dish with energy-weighted processing penalty: {current_nova_score:.2f}")
        else:
            nova_category_display = nova.name
            print(f"DEBUG: Single food NOVA category: {nova.name} with score: {current_nova_score} (set by CNF integrator)")
        
        # Calculate the original score with NOVA already included
        original_score = self.calculate_original_score(food_item)
        fcs = self.calculate_fcs(original_score)
        
        result = {
            "name": food_item.name,
            "original_score": round(original_score, 2),
            "fcs": fcs,
            "nova_category": nova_category_display
        }
        
        # Add processing details for mixed dishes
        processing_details = food_item.get_processing_details()
        if processing_details:
            result["processing_details"] = processing_details
        
        return result