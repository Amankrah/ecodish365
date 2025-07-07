import unittest
from unittest.mock import Mock, patch
from datetime import datetime
from src.monetization import Monetization

class TestMonetization(unittest.TestCase):

    def setUp(self):
        self.mock_data_loader = Mock()
        self.mock_data_loader.get_impact_factor.side_effect = lambda category: {
            'Global warming': 0.084,
            'Water consumption': 0.066,
            'Land use': 0.185
        }[category]
        self.mock_data_loader.get_cpi.side_effect = lambda year: {
            2015: 100,
            2024: 132
        }[year]

        self.lca_results = {
            'Global warming': 100,
            'Water consumption': 50,
            'Land use': 25
        }

        self.monetization = Monetization(self.lca_results, self.mock_data_loader)
        self.monetization.current_year = 2024  # Set current year for consistent testing

    def test_monetize_impacts(self):
        result = self.monetization.monetize_impacts()
        expected = {
            'Global warming': 11.088,
            'Water consumption': 4.356,
            'Land use': 6.105
        }
        for category, value in expected.items():
            self.assertAlmostEqual(result[category], value, places=3)

    def test_adjust_for_inflation(self):
        original_value = 100
        adjusted_value = self.monetization.adjust_for_inflation(original_value)
        self.assertAlmostEqual(adjusted_value, 132, places=2)

    def test_get_total_monetized_impact(self):
        total_impact = self.monetization.get_total_monetized_impact()
        self.assertAlmostEqual(total_impact, 21.549, places=3)

    def test_get_monetized_impact_breakdown(self):
        breakdown = self.monetization.get_monetized_impact_breakdown()
        expected = {
            'Global warming': {'original': 8.4, 'adjusted': 11.088},
            'Water consumption': {'original': 3.3, 'adjusted': 4.356},
            'Land use': {'original': 4.625, 'adjusted': 6.105}
        }
        for category, values in expected.items():
            self.assertAlmostEqual(breakdown[category]['original'], values['original'], places=3)
            self.assertAlmostEqual(breakdown[category]['adjusted'], values['adjusted'], places=3)

    def test_monetize_impacts_with_missing_factor(self):
        self.mock_data_loader.get_impact_factor.side_effect = ValueError("Factor not found")
        result = self.monetization.monetize_impacts()
        for value in result.values():
            self.assertEqual(value, 0.0)

    @patch('src.monetization.datetime')
    def test_current_year(self, mock_datetime):
        mock_datetime.now.return_value = datetime(2025, 1, 1)
        monetization = Monetization(self.lca_results, self.mock_data_loader)
        self.assertEqual(monetization.current_year, 2025)

    def test_str_representation(self):
        expected_str = "Monetization of environmental impacts (Base year: 2015, Current year: 2024)"
        self.assertEqual(str(self.monetization), expected_str)

if __name__ == '__main__':
    unittest.main()