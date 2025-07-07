import logging
from typing import Dict
from .data_loader import DataLoader

class Food:
    def __init__(self, food_id: int, quantity: float, data_loader: 'DataLoader'):
        self.logger = logging.getLogger(__name__)
        self.food_id = food_id
        self.quantity = quantity
        self.data_loader = data_loader
        
        try:
            self.data = self.data_loader.get_food_data(food_id)
        except ValueError as e:
            self.logger.error(f"Failed to initialize Food with ID {food_id}: {str(e)}")
            raise

        self.food_name = self.data['food_info']['FoodDescription']
        self.food_group = self.data['food_group']['FoodGroupName']
        self.nutrients = self._process_nutrients()
        self.conversion_factors = self._get_conversion_factors()

    def _process_nutrients(self) -> Dict[str, float]:
        return {
            self.data_loader.get_nutrient_name(nutrient['NutrientID']): nutrient['NutrientValue']
            for nutrient in self.data['nutrients']
        }

    def _get_conversion_factors(self) -> Dict[int, float]:
        conversion_factors = {}
        for _, row in self.data_loader.conversion_factor[self.data_loader.conversion_factor['FoodID'] == self.food_id].iterrows():
            conversion_factors[row['MeasureID']] = row['ConversionFactorValue']
        return conversion_factors

    def get_nutrient_amount(self, nutrient_name: str) -> float:
        base_amount = self.nutrients.get(nutrient_name, 0)
        return (base_amount * self.quantity) / 100  # Assuming nutrient values are per 100g

    def get_total_quantity(self) -> float:
        """Calculate total quantity including waste."""
        waste_factor = 0.319  # 31.9% waste
        return self.quantity / (1 - waste_factor)

    def get_environmental_impact(self) -> Dict[str, float]:
        """
        Calculate environmental impact based on food data.
        This is a placeholder method and should be implemented based on actual impact data.
        
        :return: Dictionary with impact categories as keys and impact values as values
        """
        # This is a simplified placeholder. In a real scenario, you'd use actual impact data.
        impact_categories = [
            'Fine particulate matter formation',
            'Fossil resource scarcity',
            'Freshwater ecotoxicity',
            'Freshwater eutrophication',
            'Global warming',
            'Human carcinogenic toxicity',
            'Human non-carcinogenic toxicity',
            'Ionizing radiation',
            'Land use',
            'Marine ecotoxicity',
            'Marine eutrophication',
            'Mineral resource scarcity',
            'Ozone formation, Human health',
            'Ozone formation, Terrestrial ecosystems',
            'Stratospheric ozone depletion',
            'Terrestrial acidification',
            'Terrestrial ecotoxicity',
            'Water consumption'
        ]

        # Placeholder impact calculation
        # In a real implementation, these values would come from LCA databases or calculations
        # Define impact factors for each food group
        food_group_factors = {
            'Dairy and Egg Products': 1.5,
            'Spices and Herbs': 0.5,
            'Babyfoods': 1.0,
            'Fats and Oils': 1.2,
            'Poultry Products': 1.8,
            'Soups, Sauces and Gravies': 1.0,
            'Sausages and Luncheon meats': 2.0,
            'Breakfast cereals': 0.8,
            'Fruits and fruit juices': 0.6,
            'Pork Products': 2.2,
            'Vegetables and Vegetable Products': 0.5,
            'Nuts and Seeds': 0.7,
            'Beef Products': 2.5,
            'Beverages': 0.8,
            'Finfish and Shellfish Products': 1.3,
            'Legumes and Legume Products': 0.6,
            'Lamb, Veal and Game': 2.3,
            'Baked Products': 1.1,
            'Sweets': 1.2,
            'Cereals, Grains and Pasta': 0.9,
            'Fast Foods': 1.8,
            'Mixed Dishes': 1.5,
            'Snacks': 1.3
        }

        # Get the impact factor for the food's group
        group_factor = food_group_factors.get(self.food_group, 1.0)

        # Base impact per 100g (this could be refined with more accurate data)
        base_impact = 0.1

        impacts = {}
        for category in impact_categories:
            # Calculate impact based on food group factor and quantity
            impact = base_impact * group_factor * (self.get_total_quantity() / 100)
            
            # Adjust impact based on specific categories
            if category == 'Global warming' and self.food_group in ['Beef Products', 'Lamb, Veal and Game']:
                impact *= 1.5  # Higher global warming impact for ruminant meats
            elif category == 'Water consumption' and self.food_group in ['Fruits and fruit juices', 'Vegetables and Vegetable Products']:
                impact *= 1.2  # Higher water consumption for produce
            elif category == 'Land use' and self.food_group in ['Beef Products', 'Dairy and Egg Products']:
                impact *= 1.3  # Higher land use for cattle-based products
            
            impacts[category] = impact
        
        return impacts
    
    def __str__(self) -> str:
        return f"Food(id={self.food_id}, name='{self.food_name}', quantity={self.quantity}g)"

    def __repr__(self) -> str:
        return self.__str__()