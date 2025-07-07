from typing import Dict
import logging
from datetime import datetime
from src.data_loader import DataLoader

class Monetization:
    def __init__(self, lca_results: Dict[str, float], data_loader: DataLoader):
        self.lca_results = lca_results
        self.data_loader = data_loader
        self.logger = logging.getLogger(__name__)
        self.base_year = 2015  # The base year for our impact factors
        self.current_year = datetime.now().year
        self.monetary_values = {
            'Fine particulate matter formation': 65.934,
            'Fossil resource scarcity': 0.571,
            'Freshwater ecotoxicity': 0.053,
            'Freshwater eutrophication': 2.725,
            'Global warming': 0.084,
            'Human carcinogenic toxicity': 0.131,
            'Human non-carcinogenic toxicity': 0.131,
            'Ionizing radiation': 0.001,
            'Land use': 0.185,
            'Marine ecotoxicity': 0.011,
            'Marine eutrophication': 4.557,
            'Mineral resource scarcity': 0.293,
            'Ozone formation, Human health': 0.097,
            'Ozone formation, Terrestrial ecosystems': 0.014,
            'Stratospheric ozone depletion': 180.220,
            'Terrestrial acidification': 10.960,
            'Terrestrial ecotoxicity': 12.733,
            'Water consumption': 0.066
        }

    def monetize_impacts(self) -> Dict[str, float]:
        """
        Convert environmental impacts to monetary values.
        
        :return: Dictionary with impact categories as keys and monetized values as values
        """
        try:
            monetized_impacts = {}
            for impact_category, impact_value in self.lca_results.items():
                if impact_category in self.monetary_values:
                    monetized_value = impact_value * self.monetary_values[impact_category]
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
            for impact_category, impact_value in self.lca_results.items():
                if impact_category in self.monetary_values:
                    original_value = impact_value * self.monetary_values[impact_category]
                    adjusted_value = monetized_impacts[impact_category]
                    breakdown[impact_category] = {
                        "original": original_value,
                        "adjusted": adjusted_value
                    }
                else:
                    self.logger.warning(f"No monetary value found for {impact_category}")
                    breakdown[impact_category] = {
                        "original": 0.0,
                        "adjusted": 0.0
                    }
            return breakdown
        except Exception as e:
            self.logger.error(f"Error getting monetized impact breakdown: {str(e)}")
            raise

    def __str__(self) -> str:
        return f"Monetization of environmental impacts (Base year: {self.base_year}, Current year: {self.current_year})"

    def __repr__(self) -> str:
        return self.__str__()