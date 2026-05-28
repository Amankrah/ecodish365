"""Unit tests for SUBST-1 substitution analyzer (Phases 1–3)."""
import os
import unittest

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
django.setup()

from api.services.substitution_rules import (
    ingredient_matches_rule,
    RULES_BY_ID,
)
from api.services.substitution_constraints import replacement_allowed, parse_extended_constraints
from api.services.substitution_culinary import culinary_swap_plausible, extreme_nutrient_swing
from api.services.substitution_analyzer import (
    analyze_substitutions,
    score_modified_composition,
    batch_analyze_substitutions,
)
from api.services.substitution_pareto import compute_pareto_frontier


class TestSubstitutionRuleMatching(unittest.TestCase):
    def test_beef_matches_beef_rule(self):
        rule = RULES_BY_ID['beef_to_legumes']
        self.assertTrue(ingredient_matches_rule(
            food_id=2683,
            food_description='Beef, ground, lean, raw',
            food_group='Beef Products',
            food_group_id=13,
            rule=rule,
        ))

    def test_lentils_do_not_match_beef_rule(self):
        rule = RULES_BY_ID['beef_to_legumes']
        self.assertFalse(ingredient_matches_rule(
            food_id=3392,
            food_description='Lentils, raw',
            food_group='Legumes and Legume Products',
            food_group_id=16,
            rule=rule,
        ))

    def test_milk_matches_milk_rule_not_chocolate(self):
        rule = RULES_BY_ID['milk_to_soy']
        self.assertTrue(ingredient_matches_rule(
            food_id=113,
            food_description='Milk, fluid, whole, pasteurized',
            food_group='Dairy and Egg Products',
            food_group_id=1,
            rule=rule,
        ))
        self.assertFalse(ingredient_matches_rule(
            food_id=69,
            food_description='Milk, fluid, chocolate, whole',
            food_group='Dairy and Egg Products',
            food_group_id=1,
            rule=rule,
        ))

    def test_white_bread_matches_not_whole_wheat(self):
        rule = RULES_BY_ID['white_to_whole_wheat']
        self.assertTrue(ingredient_matches_rule(
            food_id=3732,
            food_description='Bread, white, commercial, toasted',
            food_group='Baked Products',
            food_group_id=18,
            rule=rule,
        ))
        self.assertFalse(ingredient_matches_rule(
            food_id=4067,
            food_description='Bread, whole wheat, commercial',
            food_group='Baked Products',
            food_group_id=18,
            rule=rule,
        ))


class TestSubstitutionAnalyzer(unittest.TestCase):
    def test_beef_composition_suggests_legumes_with_hefi_gain(self):
        result = analyze_substitutions(
            [{'food_id': 2683, 'mass_g': 100.0}],
            purpose='general_health',
            max_suggestions=3,
        )
        self.assertTrue(result['success'])
        self.assertGreaterEqual(len(result['suggestions']), 1)
        top = result['suggestions'][0]
        self.assertEqual(top['rule_id'], 'beef_to_legumes')
        self.assertEqual(top['replacement']['food_id'], 3392)
        self.assertGreater(top['hefi']['delta'], 0)
        self.assertIn('fcs', top)
        self.assertEqual(result['metadata']['phase'], 4)

    def test_scorecard_included_on_suggestions(self):
        result = analyze_substitutions(
            [{'food_id': 2683, 'mass_g': 100.0}],
            purpose='general_health',
            max_suggestions=2,
            include_scorecard=True,
        )
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['baseline'].get('scorecard'))
        if result['suggestions']:
            self.assertIn('scorecard', result['suggestions'][0])
            self.assertIn('deltas', result['suggestions'][0]['scorecard'])
            self.assertIn('hefi', result['suggestions'][0]['scorecard']['deltas'])

    def test_vegetarian_constraint_blocks_beef_replacement(self):
        constraints = parse_extended_constraints({'vegetarian': True})
        self.assertFalse(replacement_allowed(
            replacement_food_id=2683,
            replacement_description='Beef, ground, lean',
            replacement_group_id=13,
            original_group_id=13,
            constraints=constraints,
        ))

    def test_apply_rescores_modified_composition(self):
        applied = score_modified_composition([{'food_id': 3392, 'mass_g': 100.0}])
        self.assertTrue(applied['success'])
        self.assertIn('scorecard', applied)
        self.assertIn('hefi', applied['scorecard'])

    def test_batch_analyze_multiple_items(self):
        batch = batch_analyze_substitutions([
            {'label': 'beef', 'composition': [{'food_id': 2683, 'mass_g': 50}]},
            {'label': 'bread', 'composition': [{'food_id': 3732, 'mass_g': 80}]},
        ], max_suggestions=2, include_scorecard=False)
        self.assertEqual(batch['metadata']['count'], 2)
        self.assertEqual(len(batch['results']), 2)

    def test_pareto_frontier_tags_suggestions(self):
        suggestions = [
            {
                'id': 'a',
                'scorecard': {'deltas': {'hefi': {'delta': 2.0}, 'fcs': {'delta': 0.0}}},
            },
            {
                'id': 'b',
                'scorecard': {'deltas': {'hefi': {'delta': 0.0}, 'fcs': {'delta': 5.0}}},
            },
        ]
        frontier = compute_pareto_frontier(suggestions)
        self.assertGreaterEqual(len(frontier), 1)
        for s in suggestions:
            self.assertIn('pareto', s)

    def test_culinary_blocks_tomato_to_mushroom(self):
        self.assertFalse(culinary_swap_plausible(
            'Tomato, red, ripe, boiled',
            'Mushroom, fungi, Cloud ears, dried',
        ))

    def test_functional_role_blocks_oil_to_non_oil(self):
        from api.services.substitution_roles import infer_functional_role, same_functional_role
        self.assertEqual(infer_functional_role('Vegetable oil, palm'), 'fat')
        self.assertFalse(same_functional_role('Vegetable oil, palm', 'Rice, white, boiled'))

    def test_culinary_allows_palm_to_peanut_oil(self):
        self.assertTrue(culinary_swap_plausible(
            'Vegetable oil, palm',
            'Oil, peanut',
        ))

    def test_culinary_blocks_salt_to_tomato_paste(self):
        self.assertFalse(culinary_swap_plausible(
            'Salt, table',
            'Tomato paste, concentrated, without salt',
            original_mass_g=5.0,
        ))

    def test_culinary_blocks_salt_to_taro_with_salt(self):
        self.assertFalse(culinary_swap_plausible(
            'Salt, table',
            'Taro, dasheen, tannia, cooked, with salt',
            original_mass_g=5.0,
        ))

    def test_primary_seasoning_not_confused_with_modified_foods(self):
        from api.services.substitution_roles import is_primary_seasoning, infer_functional_role
        self.assertTrue(is_primary_seasoning('Salt, table'))
        self.assertFalse(is_primary_seasoning('Taro, cooked, with salt'))
        self.assertFalse(is_primary_seasoning('Tomato paste, concentrated, without salt'))
        self.assertEqual(infer_functional_role('Taro, cooked, with salt'), 'other')

    def test_wafct_recipe_does_not_match_salt_to_tomato_paste(self):
        from api.services.wafct_recipes import recipe_swap_candidates
        cands = recipe_swap_candidates(
            dish_name='RICE AND GARDEN EGGS STEW WITH FISH',
            ingredient_description='Salt, table',
            exclude_ids=set(),
            limit=5,
        )
        repl_descs = [c['food_description'].lower() for c in cands]
        self.assertEqual(cands, [])
        self.assertFalse(any('tomato paste' in d for d in repl_descs))

    def test_stew_with_salt_never_suggests_tomato_paste_for_salt(self):
        """Regression: salt slot must not swap to tomato paste via WAFCT/matcher."""
        composition = [
            {'food_id': 700153, 'mass_g': 200, 'food_description': 'Grains, rice, white, medium-grain, cooked'},
            {'food_id': 700420, 'mass_g': 150, 'food_description': 'Eggplant (aubergine, brinjal), raw'},
            {'food_id': 700512, 'mass_g': 150, 'food_description': 'Fish, tuna, skipjack (aku), fresh, raw'},
            {'food_id': 700589, 'mass_g': 50, 'food_description': 'Tomato, red, ripe, raw, year round average'},
            {'food_id': 700532, 'mass_g': 25, 'food_description': 'Onion, raw'},
            {'food_id': 700876, 'mass_g': 15, 'food_description': 'Vegetable oil, palm'},
            {'food_id': 214, 'mass_g': 5, 'food_description': 'Salt, table'},
        ]
        result = analyze_substitutions(
            composition,
            purpose='general_health',
            max_suggestions=8,
            dish_name='RICE AND GARDEN EGGS STEW WITH FISH',
            reformulation_mode='greedy',
            constraints={'max_swaps': 3},
            include_scorecard=False,
        )
        self.assertTrue(result['success'])
        banned = ('tomato paste', 'taro', 'cracker', 'saltine')
        for s in result['suggestions']:
            for sw in (s.get('swaps') or [s]):
                orig = (sw.get('original') or s.get('original', {})).get('food_description', '')
                if 'salt' in orig.lower() and orig.lower().startswith('salt'):
                    repl = (sw.get('replacement') or s.get('replacement', {})).get('food_description', '').lower()
                    for b in banned:
                        self.assertNotIn(b, repl, msg=f'Bad salt swap: {repl}')

    def test_extreme_nutrient_swing_blocks_absurd_sodium_delta(self):
        self.assertTrue(extreme_nutrient_swing(
            {'sodium_mg': {'diff': -1936.0}, 'fibre_g': {'diff': 0.0}},
            swapped_mass_g=5.0,
        ))
        self.assertFalse(extreme_nutrient_swing(
            {'sodium_mg': {'diff': -50.0}, 'fibre_g': {'diff': 0.5}},
            swapped_mass_g=100.0,
        ))

    def test_stew_composition_blocks_nonsense_swaps(self):
        """West African stew — should not suggest cloud-ear mushroom for tomato."""
        composition = [
            {'food_id': 700153, 'mass_g': 100.0, 'food_description': 'Rice, white, boiled* (without salt), drained'},
            {'food_id': 700475, 'mass_g': 60.0, 'food_description': 'Native eggplant, fruit, boiled* (as part of a recipe)'},
            {'food_id': 3055, 'mass_g': 60.0, 'food_description': 'Fish, eel, mixed species, baked or broiled'},
            {'food_id': 2461, 'mass_g': 15.0, 'food_description': 'Tomato, red, ripe, boiled'},
            {'food_id': 2402, 'mass_g': 10.0, 'food_description': 'Onion, boiled, drained'},
            {'food_id': 423, 'mass_g': 5.0, 'food_description': 'Vegetable oil, palm'},
        ]
        result = analyze_substitutions(
            composition,
            purpose='general_health',
            max_suggestions=5,
            include_scorecard=False,
        )
        self.assertTrue(result['success'])
        for s in result['suggestions']:
            repl = s['replacement']['food_description'].lower()
            self.assertNotIn('cloud ear', repl)
            self.assertNotIn('baobab', repl)

    def test_higher_fibre_discovers_candidates(self):
        result = analyze_substitutions(
            [{'food_id': 3732, 'mass_g': 80.0, 'food_description': 'Bread, white, commercial, toasted'}],
            purpose='higher_fibre',
            max_suggestions=5,
        )
        self.assertTrue(result['success'])
        self.assertGreater(len(result['suggestions']), 0)
        sources = {s.get('candidate_source') for s in result['suggestions']}
        self.assertTrue(sources & {'curated_rule', 'nutrient_discovery', 'matcher_alternative'})

    def test_max_swaps_two_allows_multi(self):
        result = analyze_substitutions(
            [
                {'food_id': 2683, 'mass_g': 50.0},
                {'food_id': 3732, 'mass_g': 50.0, 'food_description': 'Bread, white, commercial'},
            ],
            purpose='general_health',
            max_suggestions=5,
            constraints={'max_swaps': 2},
        )
        self.assertTrue(result['success'])
        self.assertGreaterEqual(result['metadata']['constraints']['max_swaps'], 2)

    def test_empty_composition_raises(self):
        with self.assertRaises(ValueError):
            analyze_substitutions([])


if __name__ == '__main__':
    unittest.main()
