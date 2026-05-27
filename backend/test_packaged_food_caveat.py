"""Unit tests for PKG-IMG-1 Phase 2.x packaged-food caveat helper."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))

from api.views.packaged_food_caveat import (  # noqa: E402
    build_packaged_food_caveat,
    parse_decomposition_provenance,
)


class TestPackagedFoodCaveat(unittest.TestCase):
    def test_parse_whitelist(self):
        self.assertEqual(
            parse_decomposition_provenance('packaged_food_inferred'),
            'packaged_food_inferred',
        )
        self.assertIsNone(parse_decomposition_provenance('other'))
        self.assertIsNone(parse_decomposition_provenance(None))

    def test_empty_when_not_inferred(self):
        self.assertEqual(build_packaged_food_caveat('hefi', 'individual'), {})
        self.assertEqual(
            build_packaged_food_caveat(
                'fcs', 'researcher', decomposition_provenance='cnf_only',
            ),
            {},
        )

    def test_individual_hefi_caveat(self):
        out = build_packaged_food_caveat(
            'hefi', 'individual', decomposition_provenance='packaged_food_inferred',
        )
        self.assertIn('inferred_composition_caveat', out)
        msg = out['inferred_composition_caveat']['message']
        self.assertIn('INFORMED ESTIMATE', msg)

    def test_researcher_hsr_caveat(self):
        out = build_packaged_food_caveat(
            'hsr', 'researcher', decomposition_provenance='packaged_food_inferred',
        )
        msg = out['inferred_composition_caveat']['message']
        self.assertIn('PKG-IMG-1', msg)
        self.assertIn('Combined-meal HSR is omitted', msg)

    def test_all_indicators(self):
        for indicator in ('hefi', 'heni', 'hsr', 'fcs', 'environmental'):
            out = build_packaged_food_caveat(
                indicator, 'individual', decomposition_provenance='packaged_food_inferred',
            )
            self.assertTrue(out['inferred_composition_caveat']['message'])


if __name__ == '__main__':
    unittest.main()
