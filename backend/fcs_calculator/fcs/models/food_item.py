from dataclasses import dataclass, field
from typing import Dict
from .enums import NOVACategory

@dataclass
class FoodItem:
    name: str
    attributes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    nova_category: NOVACategory = None

    def __post_init__(self):
        self.attributes = {
            'nutrient_ratios': {
                'unsaturated_to_saturated_fat': 0,
                'fiber_to_carbohydrate': 0,
                'potassium_to_sodium': 0
            },
            'vitamins': {f'vitamin_{vit}': 0 for vit in ['a', 'b1', 'b2', 'b3', 'b6', 'b9', 'b12', 'c', 'd', 'e']},
            'minerals': {mineral: 0 for mineral in ['calcium', 'phosphorus', 'magnesium', 'iron', 'zinc', 'copper', 'selenium', 'sodium', 'potassium']},
            'food_ingredients': {ingredient: 0 for ingredient in ['fruit', 'vegetable', 'beans', 'whole_grains', 'nuts', 'seafood', 'yogurt', 'plant_oils', 'refined_grains', 'red_or_processed_meat']},
            'additives': {additive: 0 for additive in ['added_sugar', 'nitrites', 'artificial_sweeteners', 'partially_hydrated_oils', 'hydrogenated_oils', 'high_fructose_corn_syrup', 'monosodium_glutamate']},
            'processing': {method: 0 for method in ['fermentation', 'frying']},
            'specific_lipids': {lipid: 0 for lipid in ['cholesterol', 'mcfas', 'alpha_linolenic_acid', 'epa_dha', 'transfat']},
            'fibers_proteins_phytochemicals': {compound: 0 for compound in ['total_flavonoids', 'total_carotenoids']}
        }

    def set_attribute(self, domain: str, attribute: str, value: float):
        if domain in self.attributes and attribute in self.attributes[domain]:
            self.attributes[domain][attribute] = value
        else:
            raise ValueError(f"Invalid domain or attribute: {domain}.{attribute}")

    def set_nova_category(self, category: NOVACategory):
        self.nova_category = category