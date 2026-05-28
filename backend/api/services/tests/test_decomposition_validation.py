"""Tests for decomposition_validation — deterministic ground-truth lenses (no LLM)."""
from __future__ import annotations

import glob
import json
import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-decompval')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.services.decomposition_validation import (  # noqa: E402
    fndds_recipe_comparison,
    nutrient_reconstruction,
)
from api.services.fped_profile_loader import reset_for_test  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

# Stable CNF FoodIDs.
_APPLE = 1696
_WHITE_BREAD = 4066
_PIZZA = 6781
_CHEESE_SOUFFLE = 2  # bridged to FNDDS at 0.9


def setup_function():
    reset_for_test()
    from heni_calculator.heni.data import fpid_loader
    fpid_loader.reset_for_test()


def test_self_reconstruction_is_exact():
    # Reconstructing a food from 100 g of ITSELF must reproduce its own nutrients.
    out = nutrient_reconstruction(_APPLE, [{'food_id': _APPLE, 'mass_g': 100}], total_mass_g=100)
    assert out is not None
    assert out['kcal_rel_error'] is not None and out['kcal_rel_error'] < 0.01
    assert out['macro_mean_abs_rel_error'] < 0.01
    assert out['resolved_mass_fraction'] == 1.0


def test_wrong_ingredient_has_large_error():
    # "Reconstructing" an apple from pizza must blow up the nutrient error.
    out = nutrient_reconstruction(_APPLE, [{'food_id': _PIZZA, 'mass_g': 100}], total_mass_g=100)
    assert out is not None
    assert out['kcal_rel_error'] > 1.0  # pizza is many times an apple's kcal/100g


def test_unresolved_mass_undercounts():
    # Only 50 g resolved out of a 100 g target -> ~half the kcal recovered.
    out = nutrient_reconstruction(_APPLE, [{'food_id': _APPLE, 'mass_g': 50}], total_mass_g=100)
    assert out is not None
    assert out['resolved_mass_fraction'] == 0.5
    assert 0.4 < out['kcal_rel_error'] < 0.6  # ~50% shortfall


def test_no_profile_and_empty_return_none():
    assert nutrient_reconstruction(99999999, [{'food_id': _APPLE, 'mass_g': 100}]) is None
    assert nutrient_reconstruction(_APPLE, []) is None


def test_fndds_comparison_bridged_vs_unbridged():
    # A dairy/egg split of cheese souffle should align with USDA's recipe (dairy-dominant).
    dairy_split = [{'food_id': 125, 'mass_g': 50}, {'food_id': 123, 'mass_g': 50}]  # egg + milk
    out = fndds_recipe_comparison(_CHEESE_SOUFFLE, dairy_split)
    assert out is not None
    assert out['fped_rollup_cosine'] is not None and out['fped_rollup_cosine'] >= 0.5
    assert out['fndds_n_ingredients'] > 0
    # Unbridged / unknown food -> None.
    assert fndds_recipe_comparison(99999999, dairy_split) is None


def test_should_override_with_catalog():
    # Pure gate-decision logic (no LLM).
    from api.services.cnf_recipe_decomposer import _should_override_with_catalog as so
    assert so(None, decomp_matched=False) is True          # failed decomposition -> use catalog
    assert so(None, decomp_matched=True) is False           # no recon -> keep decomposition
    assert so({'kcal_rel_error': 0.10, 'macro_mean_abs_rel_error': 0.15}, True) is False  # faithful
    assert so({'kcal_rel_error': 0.50, 'macro_mean_abs_rel_error': 0.10}, True) is True   # bad kcal
    assert so({'kcal_rel_error': 0.10, 'macro_mean_abs_rel_error': 0.50}, True) is True   # bad macro


def test_catalog_recipe_and_has_nutrients():
    from api.services.cnf_recipe_decomposer import get_default_decomposer
    dec = get_default_decomposer()
    assert dec._has_nutrients(_APPLE) is True
    assert dec._has_nutrients(99999999) is False

    class _M:  # minimal stand-in for a MatchResult
        food_id = _APPLE
        food_description = 'Apple, raw'
        food_group = 'Fruits and fruit juices'
        confidence = 0.93
    r = dec._catalog_recipe(_M(), 'apple', 'apple', 150.0, reason='catalog_direct_match', t0=0.0)
    assert r.matched is True
    assert len(r.ingredients) == 1
    assert r.ingredients[0].food_id == _APPLE
    assert r.ingredients[0].mass_g == 150.0
    assert r.resolved_mass_g == 150.0 and r.unresolved_mass_g == 0.0
    assert r.fallback_reason == 'catalog_direct_match'


def test_benchmark_artifact_schema_if_present():
    # Mirror test_matcher_benchmark: pin the artifact shape when one exists; skip otherwise.
    files = sorted(glob.glob(os.path.join(_BACKEND, 'decomposer_benchmark_*.json')))
    if not files:
        return
    b = json.loads(open(files[-1], encoding='utf-8').read())
    for k in ('git_rev', 'sample_size', 'seed', 'summary', 'per_food'):
        assert k in b, f'missing top-level key {k}'
    assert 'overall' in b['summary'] and 'by_group' in b['summary']
    if b['per_food']:
        row = b['per_food'][0]
        for k in ('food_id', 'cnf_group', 'matched', 'automated_verdict'):
            assert k in row, f'missing per_food key {k}'
        assert row['automated_verdict'] in ('pass', 'borderline', 'flagged', 'no_truth')
