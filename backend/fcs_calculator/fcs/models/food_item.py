from dataclasses import dataclass, field
from typing import Dict, Optional
from .enums import NOVACategory

@dataclass
class FoodItem:
    name: str
    attributes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    nova_category: NOVACategory = None
    _nova_processing_level: int = 1  # Default to minimally processed
    _processing_details: Optional[Dict] = None  # For mixed dish processing details

    def __post_init__(self):
        self.attributes = {
            # Domain 1: Nutrient Ratios (full weight)
            'nutrient_ratios': {
                'unsaturated_to_saturated_fat': 0,
                'fiber_to_carbohydrate': 0,
                'potassium_to_sodium': 0
            },
            # Domain 2: Vitamins (full weight, top 5 selection)
            'vitamins': {
                f'vitamin_{vit}': 0 for vit in ['a', 'b1', 'b2', 'b3', 'b6', 'b9', 'b12', 'c', 'd', 'e', 'k']
            },
            # Domain 3: Minerals (full weight, top 5 selection)
            'minerals': {
                mineral: 0 for mineral in ['calcium', 'phosphorus', 'magnesium', 'iron', 'zinc', 'copper', 'selenium', 'sodium', 'potassium', 'manganese', 'chromium', 'molybdenum']
            },
            # Domain 4: Food-based Ingredients (full weight, uses summation)
            'food_ingredients': {
                ingredient: 0 for ingredient in ['fruit', 'vegetable', 'beans', 'whole_grains', 'nuts', 'seafood', 'yogurt', 'plant_oils', 'refined_grains', 'red_or_processed_meat', 'added_sugar']
            },
            # Domain 5: Additives (full weight)
            'additives': {
                additive: 0 for additive in ['nitrites', 'artificial_sweeteners', 'partially_hydrated_oils', 'hydrogenated_oils', 'high_fructose_corn_syrup', 'monosodium_glutamate', 'artificial_colors', 'preservatives']
            },
            # Domain 6: Processing Characteristics (full weight)
            'processing': {
                method: 0 for method in ['nova_processing', 'fermentation', 'frying', 'minimal_processing', 'pasteurization', 'smoking', 'canning']
            },
            # Domain 7: Specific Lipids (half weight, top 3 selection)
            'specific_lipids': {
                lipid: 0 for lipid in ['cholesterol', 'mcfas', 'alpha_linolenic_acid', 'epa_dha', 'transfat', 'oleic_acid', 'linoleic_acid', 'total_fat', 'saturated_fat', 'monounsaturated_fat', 'polyunsaturated_fat']
            },
            # Domain 8: Fiber and Protein (half weight)
            'fiber_protein': {
                nutrient: 0 for nutrient in ['fiber', 'protein', 'amino_acid_score', 'total_carbohydrate', 'total_sugars']
            },
            # Domain 9: Phytochemicals (half weight)
            'phytochemicals': {
                compound: 0 for compound in ['total_flavonoids', 'total_carotenoids', 'anthocyanins', 'isoflavones', 'proanthocyanidins', 'lignans', 'choline', 'betaine']
            }
        }

    def set_attribute(self, domain: str, attribute: str, value: float):
        if domain in self.attributes and attribute in self.attributes[domain]:
            self.attributes[domain][attribute] = value
        else:
            raise ValueError(f"Invalid domain or attribute: {domain}.{attribute}")

    def set_nova_category(self, category: NOVACategory):
        self.nova_category = category
    
    def get_nova_processing_level(self) -> int:
        """Get the NOVA processing level set by CNF analysis"""
        return getattr(self, '_nova_processing_level', 1)
    
    def set_nova_processing_level(self, level: int):
        """Set the NOVA processing level (used by CNF integrator)"""
        self._nova_processing_level = level
    
    def get_processing_details(self) -> Optional[Dict]:
        """Get detailed processing information for mixed dishes"""
        return getattr(self, '_processing_details', None)
    
    def set_processing_details(self, details: Dict):
        """Set detailed processing information (used by CNF integrator)"""
        self._processing_details = details