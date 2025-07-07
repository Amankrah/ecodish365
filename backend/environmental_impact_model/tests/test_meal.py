import unittest
from unittest.mock import Mock, patch
from src.meal import Meal
from src.food import Food

class TestMeal(unittest.TestCase):

    def setUp(self):
        self.mock_data_loader = Mock()
        self.mock_data_loader.get_nutrient_name.side_effect = lambda x: 'ENERGY (KILOCALORIES)' if x == 208 else f'Nutrient{x}'

        self.mock_food1 = Mock(spec=Food)
        self.mock_food1.food_id = 1
        self.mock_food1.food_name = 'Apple'
        self.mock_food1.quantity = 100
        self.mock_food1.get_nutrient_amount.return_value = 52
        self.mock_food1.get_all_nutrients.return_value = {'ENERGY (KILOCALORIES)': 52, 'Nutrient1': 0.3, 'Nutrient2': 14}
        self.mock_food1.get_environmental_impact.return_value = {'Global warming': 0.1, 'Water consumption': 0.2}
        self.mock_food1.data_loader = self.mock_data_loader

        self.mock_food2 = Mock(spec=Food)
        self.mock_food2.food_id = 2
        self.mock_food2.food_name = 'Chicken'
        self.mock_food2.quantity = 150
        self.mock_food2.get_nutrient_amount.return_value = 165
        self.mock_food2.get_all_nutrients.return_value = {'ENERGY (KILOCALORIES)': 165, 'Nutrient1': 31, 'Nutrient2': 0}
        self.mock_food2.get_environmental_impact.return_value = {'Global warming': 0.5, 'Water consumption': 0.3}
        self.mock_food2.data_loader = self.mock_data_loader

        self.meal = Meal([self.mock_food1, self.mock_food2])

    def test_init(self):
        self.assertEqual(len(self.meal.foods), 2)
        self.assertEqual(self.meal.data_loader, self.mock_data_loader)

    def test_init_empty_meal(self):
        with self.assertRaises(ValueError):
            Meal([])

    def test_calculate_total_calories(self):
        self.assertEqual(self.meal.calculate_total_calories(), 217)

    def test_calculate_nutrient_profile(self):
        profile = self.meal.calculate_nutrient_profile()
        self.assertEqual(profile, {'ENERGY (KILOCALORIES)': 217, 'Nutrient1': 31.3, 'Nutrient2': 14})

    def test_calculate_environmental_impact(self):
        impact = self.meal.calculate_environmental_impact()
        self.assertEqual(impact, {'Global warming': 0.6, 'Water consumption': 0.5})

    def test_get_food_breakdown(self):
        breakdown = self.meal.get_food_breakdown()
        expected = [
            {"id": 1, "name": 'Apple', "quantity": 100},
            {"id": 2, "name": 'Chicken', "quantity": 150}
        ]
        self.assertEqual(breakdown, expected)

    def test_str_representation(self):
        self.assertEqual(str(self.meal), "Meal with 2 food items")

    def test_get_nutrient_amount(self):
        self.assertEqual(self.meal.get_nutrient_amount('ENERGY (KILOCALORIES)'), 217)

if __name__ == '__main__':
    unittest.main()