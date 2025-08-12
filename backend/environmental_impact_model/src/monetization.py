from typing import Dict, List
import logging
import os
from datetime import datetime
from src.data_loader import DataLoader
from .cnf_integrator import get_cnf_integrator

class Monetization:
    """
    Enhanced Monetization class with corrected economic factors and Canadian-specific adjustments.
    Uses current environmental valuation methodologies including official Environment Canada 
    social cost of carbon and verified Canadian market pricing.
    """
    
    def __init__(self, lca_results: Dict[str, float], data_loader: DataLoader):
        self.lca_results = lca_results
        self.data_loader = data_loader
        self.cnf_integrator = get_cnf_integrator()
        self.logger = logging.getLogger(__name__)
        self.base_year = 2021  # Updated to match ECCC SCC base year
        self.current_year = datetime.now().year
        
        # Corrected monetary values based on official Canadian sources and verified data (CAD 2024)
        self.monetary_values = {
            # CORRECTED: Official Environment and Climate Change Canada (ECCC) 2024 value
            'Global warming': 266.0,  # CAD per tonne CO2-eq (ECCC SCC 2024, 2021 dollars)
            
            # Health impacts - based on international studies adjusted for Canadian context
            'Fine particulate matter formation': 45000.0,  # CAD per tonne PM2.5-eq
            'Human carcinogenic toxicity': 2.5,  # CAD per kg 1,4-DCB-eq
            'Human non-carcinogenic toxicity': 1.8,  # CAD per kg 1,4-DCB-eq
            'Ionizing radiation': 0.15,  # CAD per kBq Co-60-eq
            'Ozone formation, Human health': 8500.0,  # CAD per tonne NOx-eq
            
            # Ecosystem impacts - based on European Environmental Prices Handbook adjusted for CAD
            'Terrestrial acidification': 8500.0,  # CAD per tonne SO2-eq
            'Freshwater eutrophication': 12500.0,  # CAD per tonne P-eq
            'Marine eutrophication': 3200.0,  # CAD per tonne N-eq
            'Terrestrial ecotoxicity': 0.08,  # CAD per kg 1,4-DCB-eq
            'Freshwater ecotoxicity': 0.12,  # CAD per kg 1,4-DCB-eq
            'Marine ecotoxicity': 0.05,  # CAD per kg 1,4-DCB-eq
            'Ozone formation, Terrestrial ecosystems': 2100.0,  # CAD per tonne NOx-eq
            
            # Atmospheric impacts
            'Stratospheric ozone depletion': 125000.0,  # CAD per tonne CFC11-eq
            
            # Resource depletion
            'Fossil resource scarcity': 0.85,  # CAD per kg oil-eq
            'Mineral resource scarcity': 2.1,  # CAD per kg Cu-eq
            
            # UPDATED: Use an approximate Canada-wide median for potable water ($1–$4.7/m³ range)
            'Water consumption': 2.0,  # CAD per m³ (median; can override via WATER_COST_PER_M3)
            
            # CORRECTED: Based on Statistics Canada agricultural rental data
            'Land use': 0.03,  # CAD per m²*year crop-eq (Canadian farmland rental rates ~2.55% of land value)
        }
        
        # Canadian regional adjustment factors (validated against scientific literature)
        self.regional_factors = {
            'Global warming': 1.15,  # Higher due to Arctic amplification (Canada warming 2x global rate)
            'Water consumption': 0.7,  # Lower due to abundant freshwater (7% global renewable supply)
            'Land use': 0.8,  # Lower due to abundant land resources (minimal conversion rates)
            'Fossil resource scarcity': 1.1,  # Adjusted for oil sands intensity (2.2x extraction emissions)
        }

        # Allow environment-based override for water pricing to reflect local tariffs
        try:
            env_water = os.getenv('WATER_COST_PER_M3')
            if env_water is not None and str(env_water).strip() != '':
                val = float(str(env_water).strip())
                if val > 0:
                    self.monetary_values['Water consumption'] = val
        except Exception:
            pass
        
        # Data quality and uncertainty notes
        self.value_uncertainties = {
            'Global warming': 'Official ECCC value - high confidence',
            'Water consumption': 'Based on municipal rates; varies by municipality (override with WATER_COST_PER_M3)',
            'Land use': 'Based on agricultural rental rates - medium confidence for ecosystem services',
            'Fine particulate matter formation': 'Extrapolated from international studies - medium confidence',
            'Toxicity categories': 'High uncertainty - limited Canadian-specific data',
            'Resource scarcity': 'Market-based estimates - medium confidence'
        }

    def monetize_impacts(self) -> Dict[str, float]:
        """
        Convert environmental impacts to monetary values with Canadian adjustments.
        
        :return: Dictionary with impact categories as keys and monetized values as values
        """
        try:
            monetized_impacts = {}
            # Categories whose valuation factors are expressed per tonne. Our LCA results are in kg,
            # so we convert kg->tonne by multiplying by 1/1000 before applying the factor.
            per_tonne_categories = {
                'Global warming',
                'Fine particulate matter formation',
                'Terrestrial acidification',
                'Freshwater eutrophication',
                'Marine eutrophication',
                'Stratospheric ozone depletion',
                'Ozone formation, Human health',
                'Ozone formation, Terrestrial ecosystems',
            }
            
            for impact_category, impact_value in self.lca_results.items():
                if impact_category in self.monetary_values:
                    # Align units: convert kg to tonne for categories priced per tonne
                    unit_scale = (1.0 / 1000.0) if impact_category in per_tonne_categories else 1.0
                    monetized_value = (impact_value * unit_scale) * self.monetary_values[impact_category]
                    
                    # Apply Canadian regional adjustment if available
                    regional_factor = self.regional_factors.get(impact_category, 1.0)
                    monetized_value *= regional_factor
                    
                    # Adjust for inflation
                    adjusted_value = self.adjust_for_inflation(monetized_value)
                    monetized_impacts[impact_category] = adjusted_value
                else:
                    self.logger.warning(f"No monetary value found for {impact_category}")
                    monetized_impacts[impact_category] = 0.0

            return monetized_impacts
        except Exception as e:
            self.logger.error(f"Error in monetizing impacts: {str(e)}")
            raise

    def adjust_for_inflation(self, value: float) -> float:
        """
        Adjust the monetary value for inflation using the provided formula.
        Note: ECCC SCC values are in 2021 dollars, so base year adjusted accordingly.
        
        :param value: The value to be adjusted
        :return: Inflation-adjusted value
        """
        try:
            # Fetch CPI values
            cpi_current = self.data_loader.get_cpi(self.current_year)
            cpi_base = self.data_loader.get_cpi(self.base_year)

            # Apply the inflation formula
            adjusted_value = value * (cpi_current / cpi_base)

            return adjusted_value
        except AttributeError:
            self.logger.warning("CPI data not available. Using unadjusted value.")
            return value
        except Exception as e:
            self.logger.error(f"Error adjusting for inflation: {str(e)}")
            return value

    def get_total_monetized_impact(self) -> float:
        """
        Calculate the total monetized environmental impact.
        
        :return: Total monetized impact value
        """
        try:
            monetized_impacts = self.monetize_impacts()
            return sum(monetized_impacts.values())
        except Exception as e:
            self.logger.error(f"Error calculating total monetized impact: {str(e)}")
            raise

    def get_monetized_impact_breakdown(self) -> Dict[str, Dict[str, float]]:
        """
        Get a breakdown of monetized impacts, including both original and adjusted values.
        
        :return: Dictionary with impact categories as keys and sub-dictionaries of original and adjusted values
        """
        try:
            breakdown = {}
            monetized_impacts = self.monetize_impacts()
            
            per_tonne_categories = {
                'Global warming', 'Fine particulate matter formation', 'Terrestrial acidification',
                'Freshwater eutrophication', 'Marine eutrophication', 'Stratospheric ozone depletion',
                'Ozone formation, Human health', 'Ozone formation, Terrestrial ecosystems'
            }
            
            for impact_category, impact_value in self.lca_results.items():
                if impact_category in self.monetary_values:
                    # Apply correct unit scaling
                    unit_scale = (1.0 / 1000.0) if impact_category in per_tonne_categories else 1.0
                    original_value = (impact_value * unit_scale) * self.monetary_values[impact_category]
                    adjusted_value = monetized_impacts[impact_category]
                    
                    breakdown[impact_category] = {
                        "original": original_value,
                        "adjusted": adjusted_value,
                        "regional_factor": self.regional_factors.get(impact_category, 1.0),
                        "confidence": self.value_uncertainties.get(impact_category, "Medium confidence")
                    }
                else:
                    self.logger.warning(f"No monetary value found for {impact_category}")
                    breakdown[impact_category] = {
                        "original": 0.0,
                        "adjusted": 0.0,
                        "regional_factor": 1.0,
                        "confidence": "No data available"
                    }
            return breakdown
        except Exception as e:
            self.logger.error(f"Error getting monetized impact breakdown: {str(e)}")
            raise
    
    def calculate_cost_per_calorie(self, total_calories: float) -> float:
        """
        Calculate environmental cost per calorie.
        
        :param total_calories: Total calories in the meal
        :return: Environmental cost per calorie in CAD
        """
        try:
            total_cost = self.get_total_monetized_impact()
            if total_calories > 0:
                return total_cost / total_calories
            return 0.0
        except Exception as e:
            self.logger.error(f"Error calculating cost per calorie: {str(e)}")
            return 0.0
    
    def calculate_cost_per_gram_protein(self, total_protein: float) -> float:
        """
        Calculate environmental cost per gram of protein.
        
        :param total_protein: Total protein in the meal (grams)
        :return: Environmental cost per gram protein in CAD
        """
        try:
            total_cost = self.get_total_monetized_impact()
            if total_protein > 0:
                return total_cost / total_protein
            return 0.0
        except Exception as e:
            self.logger.error(f"Error calculating cost per gram protein: {str(e)}")
            return 0.0
    
    def get_cost_breakdown_by_category(self) -> Dict[str, Dict[str, float]]:
        """
        Get cost breakdown categorized by impact type.
        """
        try:
            monetized = self.monetize_impacts()
            
            categories = {
                'Climate & Energy': ['Global warming', 'Fossil resource scarcity', 'Ozone formation, Human health', 
                                   'Ozone formation, Terrestrial ecosystems', 'Stratospheric ozone depletion'],
                'Human Health': ['Fine particulate matter formation', 'Human carcinogenic toxicity', 
                               'Human non-carcinogenic toxicity', 'Ionizing radiation'],
                'Ecosystem Quality': ['Terrestrial acidification', 'Freshwater eutrophication', 'Marine eutrophication',
                                    'Terrestrial ecotoxicity', 'Freshwater ecotoxicity', 'Marine ecotoxicity'],
                'Resource Depletion': ['Water consumption', 'Land use', 'Mineral resource scarcity']
            }
            
            breakdown = {}
            total_value = sum(monetized.values())
            
            for category, impacts in categories.items():
                category_total = sum(monetized.get(impact, 0) for impact in impacts)
                category_impacts = {impact: monetized.get(impact, 0) for impact in impacts if monetized.get(impact, 0) > 0}
                breakdown[category] = {
                    'total_cost': category_total,
                    'individual_impacts': category_impacts,
                    'percentage_of_total': (category_total / total_value * 100) if total_value > 0 else 0
                }
            
            return breakdown
        except Exception as e:
            self.logger.error(f"Error getting cost breakdown by category: {str(e)}")
            return {}
    
    def compare_with_reference_cost(self, reference_cost: float) -> Dict[str, float]:
        """
        Compare meal's environmental cost with a reference cost.
        
        :param reference_cost: Reference environmental cost in CAD
        :return: Comparison metrics
        """
        try:
            total_cost = self.get_total_monetized_impact()
            
            return {
                'meal_cost': total_cost,
                'reference_cost': reference_cost,
                'cost_ratio': total_cost / reference_cost if reference_cost > 0 else float('inf'),
                'cost_difference': total_cost - reference_cost,
                'percentage_difference': ((total_cost - reference_cost) / reference_cost * 100) if reference_cost > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Error comparing with reference cost: {str(e)}")
            return {}
    
    def get_top_cost_drivers(self, top_n: int = 5) -> List[Dict[str, float]]:
        """
        Get the top cost-driving impact categories.
        
        :param top_n: Number of top categories to return
        :return: List of top impact categories with their costs
        """
        try:
            monetized = self.monetize_impacts()
            
            # Sort by cost in descending order
            sorted_impacts = sorted(monetized.items(), key=lambda x: x[1], reverse=True)
            
            top_drivers = []
            total_cost = sum(monetized.values())
            
            for i, (impact, cost) in enumerate(sorted_impacts[:top_n]):
                if cost > 0:
                    confidence = self.value_uncertainties.get(impact, "Medium confidence")
                    top_drivers.append({
                        'rank': i + 1,
                        'impact_category': impact,
                        'cost': cost,
                        'percentage_of_total': (cost / total_cost * 100) if total_cost > 0 else 0,
                        'data_confidence': confidence
                    })
            
            return top_drivers
        except Exception as e:
            self.logger.error(f"Error getting top cost drivers: {str(e)}")
            return []

    def get_data_quality_summary(self) -> Dict[str, int]:
        """
        Provide a summary of data quality and confidence levels.
        
        :return: Dictionary with confidence level counts
        """
        confidence_levels = {
            'High confidence': 0,
            'Medium confidence': 0,
            'Low confidence': 0,
            'No data available': 0
        }
        
        for category in self.lca_results.keys():
            if category in self.monetary_values:
                confidence = self.value_uncertainties.get(category, "Medium confidence")
                if "high confidence" in confidence.lower():
                    confidence_levels['High confidence'] += 1
                elif "medium confidence" in confidence.lower():
                    confidence_levels['Medium confidence'] += 1
                elif "uncertainty" in confidence.lower() or "limited" in confidence.lower():
                    confidence_levels['Low confidence'] += 1
                else:
                    confidence_levels['Medium confidence'] += 1
            else:
                confidence_levels['No data available'] += 1
        
        return confidence_levels

    def __str__(self) -> str:
        return f"Monetization of environmental impacts (Base year: {self.base_year}, Current year: {self.current_year}) - Updated with official Canadian values"

    def __repr__(self) -> str:
        return self.__str__()