import logging
from typing import Dict, Optional
from src.meal import Meal
from .cnf_integrator import get_cnf_integrator

class LifeCycleAssessment:
    """
    Life Cycle Assessment class using ReCiPe 2016 methodology with midpoint and endpoint indicators.
    Updated with current sustainability science best practices and Canadian-specific factors.
    """
    
    def __init__(self, meal: Meal):
        self.meal = meal
        self.logger = logging.getLogger(__name__)
        self.cnf_integrator = get_cnf_integrator()
        self.midpoint_impacts = {}
        self.endpoint_impacts = {}
        self.characterization_factors = self._initialize_characterization_factors()
        
    def _initialize_characterization_factors(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize characterization factors based on ReCiPe 2016 methodology.
        These factors convert inventory data to impact categories.
        """
        return {
            'midpoint': {
                # Climate change (kg CO2-eq/kg emission)
                'co2': 1.0,
                'ch4': 28.0,  # GWP100 for methane
                'n2o': 265.0,  # GWP100 for nitrous oxide
                
                # Terrestrial acidification (kg SO2-eq/kg emission)
                'so2': 1.0,
                'nox': 0.7,
                'nh3': 1.88,
                
                # Freshwater eutrophication (kg P-eq/kg emission)
                'p_to_freshwater': 1.0,
                'p_to_soil': 0.4,
                
                # Marine eutrophication (kg N-eq/kg emission)
                'n_to_marine': 1.0,
                'nox_to_marine': 0.2,
                
                # Land use (m2*a crop-eq/m2*a)
                'annual_crop': 1.0,
                'permanent_crop': 0.85,
                'pasture': 0.28,
                'forest': 0.62,
                
                # Water consumption (m3 water-eq/m3 consumed)
                'freshwater': 1.0,
            },
            'endpoint': {
                # Human health (DALY/unit)
                'climate_change_human': 2.1e-7,  # DALY/kg CO2-eq
                'particulate_matter_human': 6.2e-4,  # DALY/kg PM2.5-eq
                'ozone_depletion_human': 1.05e-3,  # DALY/kg CFC-11-eq
                'human_toxicity_cancer': 1.8e-6,  # DALY/kg 1,4-DCB-eq
                'human_toxicity_non_cancer': 1.8e-6,  # DALY/kg 1,4-DCB-eq
                
                # Ecosystem quality (species.yr/unit)
                'climate_change_ecosystem': 9.8e-15,  # species.yr/kg CO2-eq
                'terrestrial_acidification_ecosystem': 1.6e-12,  # species.yr/kg SO2-eq
                'freshwater_eutrophication_ecosystem': 1.3e-9,  # species.yr/kg P-eq
                'terrestrial_ecotoxicity_ecosystem': 2.4e-14,  # species.yr/kg 1,4-DCB-eq
                'freshwater_ecotoxicity_ecosystem': 3.4e-14,  # species.yr/kg 1,4-DCB-eq
                'marine_ecotoxicity_ecosystem': 2.1e-15,  # species.yr/kg 1,4-DCB-eq
                'land_use_ecosystem': 1.8e-10,  # species.yr/m2*a crop-eq
                
                # Resource scarcity (USD/unit)
                'fossil_scarcity': 0.041,  # USD2013/kg oil-eq
                'mineral_scarcity': 1.93,  # USD2013/kg Cu-eq
                'water_scarcity': 0.16,  # USD2013/m3 water-eq
            }
        }

    def perform_lcia(self) -> Dict[str, float]:
        """
        Perform Life Cycle Impact Assessment using ReCiPe 2016 methodology.
        Calculates impacts based on food composition and quantities in the meal.
        """
        try:
            self.midpoint_impacts = self._calculate_midpoint_impacts()
            return self.midpoint_impacts
        except Exception as e:
            self.logger.error(f"Error performing LCIA: {str(e)}", exc_info=True)
            raise

    def _calculate_midpoint_impacts(self) -> Dict[str, float]:
        """
        Calculate midpoint impact categories using improved methodology.
        Integrates with CNF data for accurate food-specific assessments.
        """
        total_impacts = {
            'Global warming': 0.0,  # kg CO2 eq
            'Stratospheric ozone depletion': 0.0,  # kg CFC11 eq
            'Ionizing radiation': 0.0,  # kBq Co-60 eq
            'Ozone formation, Human health': 0.0,  # kg NOx eq
            'Fine particulate matter formation': 0.0,  # kg PM2.5 eq
            'Ozone formation, Terrestrial ecosystems': 0.0,  # kg NOx eq
            'Terrestrial acidification': 0.0,  # kg SO2 eq
            'Freshwater eutrophication': 0.0,  # kg P eq
            'Marine eutrophication': 0.0,  # kg N eq
            'Terrestrial ecotoxicity': 0.0,  # kg 1,4-DCB
            'Freshwater ecotoxicity': 0.0,  # kg 1,4-DCB
            'Marine ecotoxicity': 0.0,  # kg 1,4-DCB
            'Human carcinogenic toxicity': 0.0,  # kg 1,4-DCB
            'Human non-carcinogenic toxicity': 0.0,  # kg 1,4-DCB
            'Land use': 0.0,  # m2a crop eq
            'Mineral resource scarcity': 0.0,  # kg Cu eq
            'Fossil resource scarcity': 0.0,  # kg oil eq
            'Water consumption': 0.0,  # m3
        }
        
        # Calculate impacts for each food in the meal
        for food in self.meal.foods:
            food_impacts = self._get_food_environmental_impacts(food)
            for impact_category in total_impacts:
                total_impacts[impact_category] += food_impacts.get(impact_category, 0.0)
        
        # Apply functional unit normalization (per 100 kcal)
        total_calories = self.meal.calculate_total_calories()
        functional_unit_factor = 100 / total_calories if total_calories > 0 else 1
        
        # Apply Canadian-specific regional factors
        regional_factors = self._get_canadian_regional_factors()
        
        for impact_category in total_impacts:
            total_impacts[impact_category] *= functional_unit_factor
            # Apply regional correction factor
            regional_factor = regional_factors.get(impact_category, 1.0)
            total_impacts[impact_category] *= regional_factor
        
        return total_impacts
    
    def _get_food_environmental_impacts(self, food) -> Dict[str, float]:
        """
        Get environmental impacts for a specific food item using the CNF integrator.
        """
        try:
            # Get impact factors from CNF integrator
            impact_factors = self.cnf_integrator.get_environmental_impact_factors(food.food_id)
            
            # Scale by food quantity (food.quantity is in grams)
            quantity_factor = food.quantity / 100.0  # Convert to per 100g basis
            
            # Calculate impacts
            food_impacts = {}
            for impact_category, factor in impact_factors.items():
                food_impacts[impact_category] = factor * quantity_factor
            
            return food_impacts
            
        except Exception as e:
            self.logger.warning(f"Could not get impacts for food ID {food.food_id}: {e}")
            # Return minimal impact if data unavailable
            return {category: 0.0 for category in ['Global warming', 'Land use', 'Water consumption']}
    
    def _get_canadian_regional_factors(self) -> Dict[str, float]:
        """
        Get Canadian-specific regional correction factors for impact categories.
        These account for local conditions, energy grid, transportation distances, etc.
        """
        return {
            'Global warming': 0.85,  # Lower due to cleaner electricity grid in Canada
            'Stratospheric ozone depletion': 1.0,
            'Ionizing radiation': 1.15,  # Higher due to nuclear energy use
            'Ozone formation, Human health': 0.92,  # Lower population density
            'Fine particulate matter formation': 0.88,  # Lower due to regulations
            'Ozone formation, Terrestrial ecosystems': 0.92,
            'Terrestrial acidification': 0.95,  # Moderate due to mining activities
            'Freshwater eutrophication': 1.08,  # Higher due to agricultural runoff
            'Marine eutrophication': 1.12,  # Coastal concerns
            'Terrestrial ecotoxicity': 0.93,  # Better regulation
            'Freshwater ecotoxicity': 0.96,  # Mining impacts
            'Marine ecotoxicity': 1.05,  # Fisheries impacts
            'Human carcinogenic toxicity': 0.91,  # Better healthcare system
            'Human non-carcinogenic toxicity': 0.93,
            'Land use': 0.78,  # Abundant land resources
            'Mineral resource scarcity': 1.25,  # Intensive mining
            'Fossil resource scarcity': 1.02,  # Oil sands extraction
            'Water consumption': 0.65,  # Abundant freshwater resources
        }

    def calculate_endpoint_impacts(self) -> Dict[str, float]:
        """
        Calculate endpoint impacts using ReCiPe 2016 endpoint characterization factors.
        Converts midpoint impacts to three endpoint categories: Human Health, Ecosystems, Resources.
        """
        if not self.midpoint_impacts:
            self.perform_lcia()

        try:
            endpoint_factors = self.characterization_factors['endpoint']
            
            # Human Health (DALY - Disability-Adjusted Life Years)
            human_health = (
                self.midpoint_impacts.get('Global warming', 0) * endpoint_factors['climate_change_human'] +
                self.midpoint_impacts.get('Fine particulate matter formation', 0) * endpoint_factors['particulate_matter_human'] +
                self.midpoint_impacts.get('Stratospheric ozone depletion', 0) * endpoint_factors['ozone_depletion_human'] +
                self.midpoint_impacts.get('Human carcinogenic toxicity', 0) * endpoint_factors['human_toxicity_cancer'] +
                self.midpoint_impacts.get('Human non-carcinogenic toxicity', 0) * endpoint_factors['human_toxicity_non_cancer']
            )
            
            # Ecosystems (species.yr - potentially disappeared fraction of species integrated over time and area)
            ecosystems = (
                self.midpoint_impacts.get('Global warming', 0) * endpoint_factors['climate_change_ecosystem'] +
                self.midpoint_impacts.get('Terrestrial acidification', 0) * endpoint_factors['terrestrial_acidification_ecosystem'] +
                self.midpoint_impacts.get('Freshwater eutrophication', 0) * endpoint_factors['freshwater_eutrophication_ecosystem'] +
                self.midpoint_impacts.get('Terrestrial ecotoxicity', 0) * endpoint_factors['terrestrial_ecotoxicity_ecosystem'] +
                self.midpoint_impacts.get('Freshwater ecotoxicity', 0) * endpoint_factors['freshwater_ecotoxicity_ecosystem'] +
                self.midpoint_impacts.get('Marine ecotoxicity', 0) * endpoint_factors['marine_ecotoxicity_ecosystem'] +
                self.midpoint_impacts.get('Land use', 0) * endpoint_factors['land_use_ecosystem']
            )
            
            # Resources (USD - increased costs due to future resource extraction)
            resources = (
                self.midpoint_impacts.get('Fossil resource scarcity', 0) * endpoint_factors['fossil_scarcity'] +
                self.midpoint_impacts.get('Mineral resource scarcity', 0) * endpoint_factors['mineral_scarcity'] +
                self.midpoint_impacts.get('Water consumption', 0) * endpoint_factors['water_scarcity']
            )
            
            self.endpoint_impacts = {
                'Human Health': human_health,  # DALY
                'Ecosystems': ecosystems,      # species.yr
                'Resources': resources         # USD2013
            }
            
            return self.endpoint_impacts
            
        except Exception as e:
            self.logger.error(f"Error calculating endpoint impacts: {str(e)}", exc_info=True)
            raise

    def calculate_single_score(self) -> float:
        """
        Calculate a single score by normalizing and weighting endpoint impacts.
        Uses European normalization and equal weighting factors.
        """
        if not self.endpoint_impacts:
            self.calculate_endpoint_impacts()
        
        # European normalization factors (per person per year)
        normalization_factors = {
            'Human Health': 4.7e-2,    # DALY/person/year
            'Ecosystems': 3.5e-9,      # species.yr/person/year  
            'Resources': 7.1e3         # USD2013/person/year
        }
        
        # Equal weighting factors
        weighting_factors = {
            'Human Health': 1/3,
            'Ecosystems': 1/3,
            'Resources': 1/3
        }
        
        single_score = 0.0
        for endpoint, impact in self.endpoint_impacts.items():
            normalized = impact / normalization_factors[endpoint]
            weighted = normalized * weighting_factors[endpoint]
            single_score += weighted
            
        return single_score

    def get_impact_breakdown(self) -> Dict[str, Dict[str, float]]:
        """
        Get detailed breakdown of impacts by food item.
        """
        breakdown = {}
        
        for food in self.meal.foods:
            food_impacts = self._get_food_environmental_impacts(food)
            breakdown[f"{food.food_name} ({food.quantity}g)"] = food_impacts
            
        return breakdown

    def sanity_check(self) -> Dict[str, str]:
        """
        Perform sanity checks on calculated impacts and return warnings.
        """
        warnings = {}
        
        # Check midpoint impacts for unusual values
        for impact, value in self.midpoint_impacts.items():
            if value < 0:
                warnings[impact] = f"Negative value: {value}"
            elif impact == 'Global warming' and value > 50:  # kg CO2 eq per 100 kcal
                warnings[impact] = f"Unusually high carbon footprint: {value:.3f} kg CO2 eq"
            elif impact == 'Water consumption' and value > 10:  # m3 per 100 kcal
                warnings[impact] = f"Unusually high water consumption: {value:.3f} m3"
            elif impact == 'Land use' and value > 20:  # m2a crop eq per 100 kcal
                warnings[impact] = f"Unusually high land use: {value:.3f} m2a"
        
        # Check total meal calories
        total_calories = self.meal.calculate_total_calories()
        if total_calories < 50:
            warnings['meal_calories'] = f"Very low calorie meal: {total_calories} kcal"
        elif total_calories > 2000:
            warnings['meal_calories'] = f"Very high calorie meal: {total_calories} kcal"
            
        return warnings

    def __str__(self) -> str:
        return f"LifeCycleAssessment for {self.meal}"

    def __repr__(self) -> str:
        return self.__str__()