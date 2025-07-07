import unittest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

from src.data_loader import DataLoader

class TestDataLoader(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sample_data = {
            'FOOD_GROUP.csv': 'FoodGroupID,FoodGroupName\n1,Fruits\n2,Vegetables',
            'FOOD_NAME.csv': 'FoodID,FoodName,FoodGroupID\n1,Apple,1\n2,Carrot,2',
            'NUTRIENT_AMOUNT.csv': 'FoodID,NutrientID,NutrientValue\n1,1,0.5\n1,2,0.3\n2,1,0.2',
            'NUTRIENT_NAME.csv': 'NutrientID,NutrientName,NutrientUnit\n1,ENERGY (KILOCALORIES),kcal\n2,PROTEIN,g',
            'impact_factors.csv': 'ImpactCategory,ImpactFactor\nCategory1,1.5\nCategory2,2.0'
        }
        for filename, content in self.sample_data.items():
            with open(os.path.join(self.temp_dir, filename), 'w') as f:
                f.write(content)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        loader = DataLoader(self.temp_dir)
        self.assertEqual(loader.data_dir, self.temp_dir)
        self.assertIsNotNone(loader.logger)

    def test_load_all_data(self):
        loader = DataLoader(self.temp_dir)
        self.assertIsInstance(loader.food_group, pd.DataFrame)
        self.assertIsInstance(loader.food_name, pd.DataFrame)
        self.assertIsInstance(loader.nutrient_amount, pd.DataFrame)
        self.assertIsInstance(loader.nutrient_name, pd.DataFrame)
        self.assertIsInstance(loader.impact_factors, pd.DataFrame)

    def test_create_nutrient_mappings(self):
        loader = DataLoader(self.temp_dir)
        self.assertIn(1, loader.nutrient_id_to_name)
        self.assertIn('ENERGY (KILOCALORIES)', loader.nutrient_name_to_id)

    def test_get_nutrient_id(self):
        loader = DataLoader(self.temp_dir)
        self.assertEqual(loader.get_nutrient_id('ENERGY (KILOCALORIES)'), 1)
        self.assertIsNone(loader.get_nutrient_id('NON_EXISTENT_NUTRIENT'))

    def test_get_nutrient_name(self):
        loader = DataLoader(self.temp_dir)
        self.assertEqual(loader.get_nutrient_name(1), 'ENERGY (KILOCALORIES)')
        self.assertEqual(loader.get_nutrient_name(999), 'Unknown')

    def test_load_csv_file_not_found(self):
        loader = DataLoader(self.temp_dir)
        with self.assertRaises(FileNotFoundError):
            loader._load_csv('non_existent_file.csv')

    def test_load_csv_empty_file(self):
        empty_file = os.path.join(self.temp_dir, 'empty.csv')
        open(empty_file, 'w').close()
        loader = DataLoader(self.temp_dir)
        with self.assertRaises(pd.errors.EmptyDataError):
            loader._load_csv('empty.csv')

    def test_get_food_data(self):
        loader = DataLoader(self.temp_dir)
        food_data = loader.get_food_data(1)
        self.assertIn('food_info', food_data)
        self.assertIn('nutrients', food_data)
        self.assertIn('food_group', food_data)

    def test_get_food_data_not_found(self):
        loader = DataLoader(self.temp_dir)
        with self.assertRaises(ValueError):
            loader.get_food_data(999)

    def test_get_impact_factor(self):
        loader = DataLoader(self.temp_dir)
        impact_factor = loader.get_impact_factor('Category1')
        self.assertEqual(impact_factor, 1.5)

    def test_get_impact_factor_not_found(self):
        loader = DataLoader(self.temp_dir)
        with self.assertRaises(ValueError):
            loader.get_impact_factor('NonExistentCategory')

    @patch('src.data_loader.chardet.detect')
    def test_load_csv_with_encoding(self, mock_detect):
        mock_detect.return_value = {'encoding': 'utf-8'}
        loader = DataLoader(self.temp_dir)
        
        # Reset the mock to clear previous calls
        mock_detect.reset_mock()
        
        # Now test a single file load
        df = loader._load_csv('FOOD_GROUP.csv')
        self.assertIsInstance(df, pd.DataFrame)
        mock_detect.assert_called_once()

if __name__ == '__main__':
    unittest.main()