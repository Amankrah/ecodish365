import logging
from typing import Dict
from .data_loader import DataLoader
from .cnf_integrator import get_cnf_integrator

class Food:
    """
    Enhanced Food class that integrates with the CNF singleton for improved data access
    and environmental impact calculations using current LCA best practices.
    """
    
    def __init__(self, food_id: int, quantity: float, data_loader: 'DataLoader'):
        self.logger = logging.getLogger(__name__)
        self.food_id = food_id
        self.quantity = quantity
        self.data_loader = data_loader
        self.cnf_integrator = get_cnf_integrator()
        
        try:
            self.data = self.data_loader.get_food_data(food_id)
        except ValueError as e:
            self.logger.error(f"Failed to initialize Food with ID {food_id}: {str(e)}")
            raise

        self.food_name = self.data['food_info']['FoodDescription']
        self.food_group = self.data['food_group'].get('FoodGroupName', 'Unknown')
        self.nutrients = self._process_nutrients()
        # Build a normalized nutrient map for robust lookups (case/alias tolerant)
        self._nutrients_normalized = self._build_normalized_nutrients(self.nutrients)
        self._nutrient_alias = self._build_nutrient_aliases()
        self.conversion_factors = self._get_conversion_factors()

    def _process_nutrients(self) -> Dict[str, float]:
        return {
            self.data_loader.get_nutrient_name(nutrient['NutrientID']): nutrient['NutrientValue']
            for nutrient in self.data['nutrients']
        }

    def _normalize_name(self, name: str) -> str:
        # Upper-case, strip, remove punctuation except spaces and letters, collapse spaces
        import re
        upper = (name or '').upper()
        cleaned = re.sub(r"[^A-Z0-9\s]", " ", upper)
        collapsed = re.sub(r"\s+", " ", cleaned).strip()
        return collapsed

    def _build_normalized_nutrients(self, nutrients: Dict[str, float]) -> Dict[str, float]:
        normalized: Dict[str, float] = {}
        for key, value in nutrients.items():
            normalized[self._normalize_name(key)] = value
        return normalized

    def _build_nutrient_aliases(self) -> Dict[str, str]:
        # Map common query names to CNF canonical nutrient names (normalized)
        canonical_fat = self._normalize_name('FAT (TOTAL LIPIDS)')
        canonical_carb = self._normalize_name('CARBOHYDRATE, TOTAL (BY DIFFERENCE)')
        canonical_energy = self._normalize_name('ENERGY (KILOCALORIES)')
        aliases = {
            # Protein is already canonical 'PROTEIN'
            self._normalize_name('FAT'): canonical_fat,
            self._normalize_name('TOTAL FAT'): canonical_fat,
            self._normalize_name('FAT TOTAL'): canonical_fat,
            self._normalize_name('LIPID'): canonical_fat,
            self._normalize_name('TOTAL LIPID'): canonical_fat,

            self._normalize_name('CARBOHYDRATE'): canonical_carb,
            self._normalize_name('CARBOHYDRATES'): canonical_carb,
            self._normalize_name('TOTAL CARBOHYDRATE'): canonical_carb,
            self._normalize_name('CARBOHYDRATE TOTAL'): canonical_carb,

            self._normalize_name('ENERGY'): canonical_energy,
            self._normalize_name('KILOCALORIES'): canonical_energy,
            self._normalize_name('KCAL'): canonical_energy,
        }
        return aliases

    def _get_conversion_factors(self) -> Dict[int, float]:
        conversion_factors = {}
        for _, row in self.data_loader.conversion_factor[self.data_loader.conversion_factor['FoodID'] == self.food_id].iterrows():
            conversion_factors[row['MeasureID']] = row['ConversionFactorValue']
        return conversion_factors

    def get_nutrient_amount(self, nutrient_name: str) -> float:
        # Robust, alias-tolerant lookup
        normalized = self._normalize_name(nutrient_name)
        # Direct normalized hit
        base_amount = self._nutrients_normalized.get(normalized)
        if base_amount is None:
            # Alias mapping
            target = self._nutrient_alias.get(normalized)
            if target:
                base_amount = self._nutrients_normalized.get(target, 0.0)
            else:
                # Final attempt: exact original case key
                base_amount = self.nutrients.get(nutrient_name, 0.0)
        # Scale to actual quantity (CNF values are per 100g)
        try:
            return (float(base_amount or 0.0) * float(self.quantity)) / 100.0
        except Exception:
            return 0.0

    def get_total_quantity(self) -> float:
        """Calculate total quantity including waste."""
        waste_factor = 0.319  # 31.9% waste
        return self.quantity / (1 - waste_factor)

    def get_environmental_impact(self) -> Dict[str, float]:
        """
        Calculate environmental impact using the CNF integrator's improved impact factors.
        Based on current LCA science and Canadian-specific data.
        
        :return: Dictionary with impact categories as keys and impact values as values
        """
        try:
            # Get impact factors from the CNF integrator
            impact_factors = self.cnf_integrator.get_environmental_impact_factors(self.food_id)
            
            # Calculate actual quantity including food waste
            actual_quantity = self.get_total_quantity()
            quantity_factor = actual_quantity / 100.0  # Convert to per 100g basis
            
            # Scale impacts by quantity; skip metadata and non-numeric factors
            impacts = {}
            for impact_category, factor_per_100g in impact_factors.items():
                if isinstance(impact_category, str) and impact_category.startswith('_'):
                    continue
                if not isinstance(factor_per_100g, (int, float)):
                    continue
                impacts[impact_category] = float(factor_per_100g) * quantity_factor
            
            # Apply nutritional density adjustments
            nutritional_adjustments = self._calculate_nutritional_adjustments()
            for impact_category in impacts:
                impacts[impact_category] *= nutritional_adjustments.get(impact_category, 1.0)
            
            return impacts
            
        except Exception as e:
            self.logger.error(f"Error calculating environmental impact for food ID {self.food_id}: {e}")
            # Return minimal fallback impacts
            return {
                'Global warming': 0.5 * (self.quantity / 100),
                'Land use': 0.3 * (self.quantity / 100),
                'Water consumption': 0.1 * (self.quantity / 100)
            }
    
    def _calculate_nutritional_adjustments(self) -> Dict[str, float]:
        """
        Calculate adjustment factors based on nutritional density.
        Foods with higher nutritional value get lower environmental burden per nutritional unit.
        """
        adjustments = {}
        
        # Get key nutrients
        protein = self.get_nutrient_amount('PROTEIN')
        fiber = self.get_nutrient_amount('FIBRE')
        vitamins = (
            self.get_nutrient_amount('VITAMIN A') +
            self.get_nutrient_amount('VITAMIN C') +
            self.get_nutrient_amount('FOLATE')
        )
        
        # Calculate nutritional density score (higher is better)
        nutritional_score = (protein * 0.4 + fiber * 0.3 + vitamins * 0.3) / 100
        
        # Adjustment factor (1.0 = no adjustment, <1.0 = lower burden per nutrition)
        base_adjustment = max(0.7, min(1.3, 1.0 - (nutritional_score * 0.1)))
        
        # Apply to all impact categories with some variation
        impact_categories = [
            'Global warming', 'Stratospheric ozone depletion', 'Ionizing radiation',
            'Ozone formation, Human health', 'Fine particulate matter formation',
            'Ozone formation, Terrestrial ecosystems', 'Terrestrial acidification',
            'Freshwater eutrophication', 'Marine eutrophication', 'Terrestrial ecotoxicity',
            'Freshwater ecotoxicity', 'Marine ecotoxicity', 'Human carcinogenic toxicity',
            'Human non-carcinogenic toxicity', 'Land use', 'Mineral resource scarcity',
            'Fossil resource scarcity', 'Water consumption'
        ]
        
        for category in impact_categories:
            if category in ['Land use', 'Water consumption']:
                # Land and water use less affected by nutritional density
                adjustments[category] = base_adjustment * 1.2
            elif category in ['Global warming', 'Fossil resource scarcity']:
                # Carbon and energy impacts more affected by processing
                adjustments[category] = base_adjustment * 0.9
            else:
                adjustments[category] = base_adjustment
        
        return adjustments
    
    def get_sustainability_score(self) -> Dict[str, float]:
        """
        Calculate a comprehensive sustainability score considering multiple factors.
        """
        impacts = self.get_environmental_impact()
        
        # Normalize impacts to 0-100 scale (lower environmental impact = higher score)
        # These are typical maximum values per 100g food
        max_values = {
            'Global warming': 100,  # kg CO2 eq
            'Land use': 200,  # m2a crop eq
            'Water consumption': 20,  # m3
            'Terrestrial acidification': 0.5,  # kg SO2 eq
            'Freshwater eutrophication': 0.02,  # kg P eq
            'Marine eutrophication': 0.2,  # kg N eq
        }
        
        sustainability_scores = {}
        for impact_category, impact_value in impacts.items():
            if impact_category in max_values:
                # Convert to 0-100 scale (100 = best, 0 = worst)
                normalized = min(100, (impact_value / max_values[impact_category]) * 100)
                sustainability_scores[impact_category] = max(0, 100 - normalized)
        
        # Overall sustainability score (weighted average)
        weights = {
            'Global warming': 0.3,
            'Land use': 0.2,
            'Water consumption': 0.2,
            'Terrestrial acidification': 0.1,
            'Freshwater eutrophication': 0.1,
            'Marine eutrophication': 0.1
        }
        
        overall_score = 0
        total_weight = 0
        for category, weight in weights.items():
            if category in sustainability_scores:
                overall_score += sustainability_scores[category] * weight
                total_weight += weight
        
        if total_weight > 0:
            sustainability_scores['overall'] = overall_score / total_weight
        else:
            sustainability_scores['overall'] = 50  # Neutral score if no data
        
        return sustainability_scores
    
    def __str__(self) -> str:
        return f"Food(id={self.food_id}, name='{self.food_name}', quantity={self.quantity}g)"

    def __repr__(self) -> str:
        return self.__str__()