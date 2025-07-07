import unittest
from unittest.mock import Mock, patch
from src.food import Food
from src.data_loader import DataLoader

class TestFood(unittest.TestCase):

    def setUp(self):
        self.mock_data_loader = Mock(spec=DataLoader)
        self.mock_data_loader.get_food_data.return_value = {
            'food_info': {'FoodID': 1, 'FoodDescription': 'Apple'},
            'nutrients': [
                {'NutrientID': 1, 'NutrientValue': 52},  # ENERGY (KILOCALORIES)
                {'NutrientID': 2, 'NutrientValue': 0.3}  # PROTEIN
            ],
            'food_group': {'FoodGroupName': 'Fruits'}
        }
        self.mock_data_loader.get_impact_factor.return_value = 0.1
        self.mock_data_loader.get_nutrient_id.side_effect = lambda x: 1 if x == 'ENERGY (KILOCALORIES)' else 2
        self.mock_data_loader.get_nutrient_name.side_effect = lambda x: 'ENERGY (KILOCALORIES)' if x == 1 else 'PROTEIN'

    def test_init(self):
        food = Food(1, 100, self.mock_data_loader)
        self.assertEqual(food.food_id, 1)
        self.assertEqual(food.quantity, 100)
        self.assertEqual(food.food_name, 'Apple')
        self.assertEqual(food.food_group, 'Fruits')

    def test_get_total_quantity(self):
        food = Food(1, 100, self.mock_data_loader)
        self.assertAlmostEqual(food.get_total_quantity(), 146.84, places=2)

    def test_get_nutrient_amount(self):
        food = Food(1, 100, self.mock_data_loader)
        self.assertAlmostEqual(food.get_nutrient_amount('ENERGY (KILOCALORIES)'), 76.36, places=2)
    def test_get_all_nutrients(self):
        food = Food(1, 100, self.mock_data_loader)
        nutrients = food.get_all_nutrients()
        self.assertAlmostEqual(nutrients['ENERGY (KILOCALORIES)'], 76.36, places=2)
        self.assertAlmostEqual(nutrients['PROTEIN'], 0.44, places=2)

    def test_get_environmental_impact(self):
        food = Food(1, 1000, self.mock_data_loader)
        impacts = food.get_environmental_impact()
        self.assertAlmostEqual(impacts['Global warming'], 0.1468, places=4)

    def test_str_representation(self):
        food = Food(1, 100, self.mock_data_loader)
        self.assertEqual(str(food), "Food(id=1, name='Apple', quantity=100g)")

if __name__ == '__main__':
    unittest.main()