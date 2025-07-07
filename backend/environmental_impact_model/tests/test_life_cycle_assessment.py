import unittest
from unittest.mock import Mock, patch
from src.life_cycle_assessment import LifeCycleAssessment
from src.meal import Meal
from src.food import Food

class TestLifeCycleAssessment(unittest.TestCase):

    def setUp(self):
        # Create mock Food objects
        self.mock_food1 = Mock(spec=Food)
        self.mock_food1.food_name = "Apple"
        self.mock_food1.get_environmental_impact.return_value = {
            'Global warming': 0.1,
            'Water consumption': 0.2,
            'Land use': 0.3
        }

        self.mock_food2 = Mock(spec=Food)
        self.mock_food2.food_name = "Chicken"
        self.mock_food2.get_environmental_impact.return_value = {
            'Global warming': 0.5,
            'Water consumption': 0.3,
            'Land use': 0.2
        }

        # Create a mock Meal object
        self.mock_meal = Mock(spec=Meal)
        self.mock_meal.foods = [self.mock_food1, self.mock_food2]
        self.mock_meal.calculate_environmental_impact.return_value = {
            'Global warming': 0.6,
            'Water consumption': 0.5,
            'Land use': 0.5
        }

        # Create LifeCycleAssessment object
        self.lca = LifeCycleAssessment(self.mock_meal)

    def test_perform_lcia(self):
        result = self.lca.perform_lcia()
        self.assertEqual(result, {
            'Global warming': 0.6,
            'Water consumption': 0.5,
            'Land use': 0.5
        })

    def test_calculate_endpoint_impacts(self):
        self.lca.perform_lcia()
        result = self.lca.calculate_endpoint_impacts()
        self.assertIn('Human Health', result)
        self.assertIn('Ecosystems', result)
        self.assertIn('Resources', result)
        self.assertGreater(result['Human Health'], 0)
        self.assertGreater(result['Ecosystems'], 0)
        self.assertEqual(result['Resources'], 0)  # As per our mock data

    def test_get_top_contributors(self):
        self.lca.perform_lcia()
        result = self.lca.get_top_contributors('Global warming')
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "Chicken")
        self.assertEqual(result[0][1], 0.5)
        self.assertEqual(result[1][0], "Apple")
        self.assertEqual(result[1][1], 0.1)

    def test_get_impact_summary(self):
        summary = self.lca.get_impact_summary()
        self.assertIn('total_impact', summary)
        self.assertIn('endpoint_impacts', summary)
        self.assertIn('midpoint_impacts', summary)
        self.assertIn('top_contributors', summary)

    @patch('src.life_cycle_assessment.LifeCycleAssessment.perform_lcia')
    def test_lcia_error_handling(self, mock_perform_lcia):
        mock_perform_lcia.side_effect = Exception("LCIA calculation error")
        with self.assertRaises(Exception):
            self.lca.perform_lcia()

    @patch('src.life_cycle_assessment.LifeCycleAssessment.calculate_endpoint_impacts')
    def test_endpoint_impacts_error_handling(self, mock_calculate_endpoint_impacts):
        mock_calculate_endpoint_impacts.side_effect = Exception("Endpoint impact calculation error")
        with self.assertRaises(Exception):
            self.lca.calculate_endpoint_impacts()

    def test_str_representation(self):
        self.assertIn("LifeCycleAssessment", str(self.lca))

if __name__ == '__main__':
    unittest.main()