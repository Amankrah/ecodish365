"""Tests for the FPED aggregator (Phase 2): totals, dual-guideline gaps, coverage."""
from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-fped')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.services.fped_aggregator import aggregate_fped  # noqa: E402
from api.services.fped_profile_loader import get_fped_profile_for_food, reset_for_test  # noqa: E402


def setup_function():
    reset_for_test()


def test_totals_match_hand_sum():
    # 200 g apple + 100 g white bread.
    agg = aggregate_fped([
        {'food_id': 1696, 'mass_g': 200.0},
        {'food_id': 4066, 'mass_g': 100.0},
    ])
    apple = get_fped_profile_for_food(1696)
    bread = get_fped_profile_for_food(4066)
    expected_fruit = apple['fruit_total_cup'] * 2.0
    expected_refined = bread['grain_refined_oz'] * 1.0
    assert abs(agg.component_totals['fruit_total_cup'] - expected_fruit) < 1e-6
    assert abs(agg.component_totals['grain_refined_oz'] - expected_refined) < 1e-6


def test_gaps_have_both_guidelines_and_directions():
    agg = aggregate_fped([{'food_id': 1696, 'mass_g': 200.0}])
    by_comp = {g.component: g for g in agg.gaps}
    veg = by_comp['veg_total_cup']
    assert veg.direction == 'aim_at_least'
    assert veg.myplate_target == 2.5 and veg.cfg_target == 2.5
    # ~0 vegetables from an apple-only day → short on both.
    assert veg.myplate_status == 'short' and veg.cfg_status == 'short'
    refined = by_comp['grain_refined_oz']
    assert refined.direction == 'keep_at_most'


def test_bridged_wafct_food_counts():
    # A bridged WAFCT food (700153 rice, conf 0.9) contributes like any CNF food.
    agg = aggregate_fped([
        {'food_id': 1696, 'mass_g': 150.0},     # CNF apple
        {'food_id': 700153, 'mass_g': 100.0},   # WAFCT rice (bridged → grain)
    ])
    assert agg.coverage['n_foods'] == 2
    assert agg.coverage['n_covered'] == 2
    assert agg.coverage['covered_mass_g'] == 250.0
    assert agg.component_totals['grain_total_oz'] > 0   # rice grain counted


def test_unmatched_food_flagged_not_dropped():
    agg = aggregate_fped([
        {'food_id': 1696, 'mass_g': 150.0},      # covered
        {'food_id': 99999999, 'mass_g': 100.0},  # no profile
    ])
    assert agg.coverage['n_covered'] == 1
    assert agg.coverage['n_no_profile'] == 1
    assert agg.coverage['covered_mass_g'] == 150.0


def test_to_dict_shape():
    d = aggregate_fped([{'food_id': 1696, 'mass_g': 100.0}]).to_dict()
    assert 'component_totals' in d and 'gaps' in d and 'coverage' in d
    assert 'component_units' in d
    assert all('myplate_status' in g and 'cfg_status' in g for g in d['gaps'])
