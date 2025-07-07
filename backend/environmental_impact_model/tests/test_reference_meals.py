import unittest
from unittest.mock import Mock, patch
from src.reference_meals import ReferenceMeals
from src.food import Food
from src.meal import Meal
import pandas as pd

class TestReferenceMeals(unittest.TestCase):

    def setUp(self):
        self.mock_data_loader = Mock()
        
        # Mock food_name DataFrame
        self.mock_data_loader.food_name = pd.DataFrame({
            'FoodID': [1, 2, 3, 4, 5],
            'FoodDescription': ['Apple', 'Chicken', 'Bread', 'Soda', 'Chips']
        })
        
        # Mock get_food_group method
        self.mock_data_loader.get_food_group.side_effect = lambda food_id: {
            1: 'Fruits',
            2: 'Meat and Poultry',
            3: 'Grain Products',
            4: 'Beverages',
            5: 'Snacks'
        }[food_id]
        
        # Mock get_food_data method
        self.mock_data_loader.get_food_data.side_effect = lambda food_id: {
            'food_info': {'FoodDescription': f'Food {food_id}'},
            'nutrients': [],
            'food_group': {'FoodGroupName': self.mock_data_loader.get_food_group(food_id)}
        }
        
        self.reference_meals = ReferenceMeals(self.mock_data_loader)

    def test_load_food_groups(self):
        food_groups = self.reference_meals._load_food_groups()
        self.assertIn('Fruits', food_groups)
        self.assertIn('Meat and Poultry', food_groups)
        self.assertIn('Grain Products', food_groups)
        self.assertIn('Beverages', food_groups)
        self.assertIn('Snacks', food_groups)

    @patch('src.reference_meals.Food')
    def test_create_sustainable_meal(self, mock_food):
        mock_food.return_value = Mock(food_id=1)
        meal = self.reference_meals.create_sustainable_meal('lunch')
        self.assertIsInstance(meal, Meal)
        self.assertTrue(len(meal.foods) > 0)
        mock_food.assert_called()

    @patch('src.reference_meals.Food')
    def test_create_unsustainable_meal(self, mock_food):
        mock_food.return_value = Mock(food_id=2)
        meal = self.reference_meals.create_unsustainable_meal('dinner')
        self.assertIsInstance(meal, Meal)
        self.assertTrue(len(meal.foods) > 0)
        mock_food.assert_called()

    @patch('src.reference_meals.Food')
    def test_create_ultra_processed_meal(self, mock_food):
        mock_food.return_value = Mock(food_id=4)
        meal = self.reference_meals.create_ultra_processed_meal('snack')
        self.assertIsInstance(meal, Meal)
        self.assertTrue(len(meal.foods) > 0)
        mock_food.assert_called()

    @patch('src.reference_meals.ReferenceMeals.create_sustainable_meal')
    @patch('src.reference_meals.ReferenceMeals.create_unsustainable_meal')
    @patch('src.reference_meals.ReferenceMeals.create_ultra_processed_meal')
    def test_get_meal_comparison(self, mock_ultra, mock_unsustainable, mock_sustainable):
        mock_sustainable.return_value = Mock(spec=Meal)
        mock_unsustainable.return_value = Mock(spec=Meal)
        mock_ultra.return_value = Mock(spec=Meal)
        
        comparison = self.reference_meals.get_meal_comparison('breakfast')
        self.assertIn('sustainable', comparison)
        self.assertIn('unsustainable', comparison)
        self.assertIn('ultra_processed', comparison)
        for meal in comparison.values():
            self.assertIsInstance(meal, Meal)

    def test_invalid_meal_type(self):
        with self.assertRaises(ValueError):
            self.reference_meals.create_sustainable_meal('invalid_meal_type')

    @patch('src.reference_meals.random.choice')
    @patch('src.reference_meals.Food')
    def test_random_food_selection(self, mock_food, mock_random_choice):
        mock_random_choice.return_value = 1
        mock_food.return_value = Mock(food_id=1)
        meal = self.reference_meals.create_sustainable_meal('lunch')
        self.assertIsInstance(meal, Meal)
        self.assertTrue(len(meal.foods) > 0)
        mock_food.assert_called_with(1, unittest.mock.ANY, self.mock_data_loader)

    def test_str_representation(self):
        expected_str = "ReferenceMeals(meal_types=['breakfast', 'lunch', 'dinner', 'snack'])"
        self.assertEqual(str(self.reference_meals), expected_str)

if __name__ == '__main__':
    unittest.main()