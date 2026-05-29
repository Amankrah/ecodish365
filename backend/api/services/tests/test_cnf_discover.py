"""Tests for multi-criteria nutrient discovery (the research-workbench pipeline method).

Deterministic against the loaded CNF catalogue. Validates the four research capabilities:
multi-criteria AND, energy-adjusted density, nutrient ratios, and %DV thresholds, plus
food-group / source scoping, sorting and limit.
"""
from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-discover')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.cnf_cache import get_dish_cnf_pipeline  # noqa: E402

# Stable CNF NutrientIDs.
PROTEIN, FAT, SODIUM, POTASSIUM, IRON, ENERGY = 203, 204, 307, 306, 303, 208
VEG_GROUP = 11  # Vegetables and Vegetable Products


def _pipe():
    return get_dish_cnf_pipeline()


def test_single_criterion_all_satisfy_min():
    out = _pipe().discover_foods([{'nutrient_id': PROTEIN, 'min': 25}], limit=30)
    assert out['count'] > 0
    for f in out['foods']:
        assert f['nutrient_values'][str(PROTEIN)] >= 25


def test_multi_criteria_and_narrows():
    lean = _pipe().discover_foods(
        [{'nutrient_id': PROTEIN, 'min': 20}, {'nutrient_id': FAT, 'max': 5}], limit=50)
    assert lean['count'] > 0
    for f in lean['foods']:
        assert f['nutrient_values'][str(PROTEIN)] >= 20
        assert f['nutrient_values'][str(FAT)] <= 5
    # Adding the fat ceiling must not return MORE foods than protein alone.
    prot_only = _pipe().discover_foods([{'nutrient_id': PROTEIN, 'min': 20}], limit=500)
    assert lean['count'] <= prot_only['count']


def test_energy_adjusted_density_basis():
    out = _pipe().discover_foods(
        [{'nutrient_id': PROTEIN, 'min': 1}], basis='per_100kcal', limit=20)
    assert out['count'] > 0 and out['basis'] == 'per_100kcal'
    for f in out['foods']:
        e = f['energy_kcal']
        if e and e > 0:
            expected = f['nutrient_values'][str(PROTEIN)] / e * 100.0
            assert abs(f['basis_values'][str(PROTEIN)] - expected) < 0.05


def test_nutrient_ratio_reported_and_sorted():
    out = _pipe().discover_foods(
        [], ratio={'numerator_id': SODIUM, 'denominator_id': POTASSIUM},
        sort={'key': 'ratio', 'direction': 'desc'}, limit=20)
    assert out['count'] > 0
    ratios = [f['ratio_value'] for f in out['foods'] if f['ratio_value'] is not None]
    assert ratios == sorted(ratios, reverse=True)  # descending
    for f in out['foods']:
        if f['ratio_value'] is not None and f['nutrient_values'].get(str(POTASSIUM)):
            expected = f['nutrient_values'][str(SODIUM)] / f['nutrient_values'][str(POTASSIUM)]
            assert abs(f['ratio_value'] - expected) < 0.01


def test_dv_threshold_filters_on_percent_dv():
    # Iron DV is 18 mg; >= 50% DV per 100 g means >= 9 mg per 100 g.
    out = _pipe().discover_foods(
        [], dv_threshold={'nutrient_id': IRON, 'min_pct': 50}, limit=50)
    for f in out['foods']:
        assert f['nutrient_values'][str(IRON)] >= 9.0 - 1e-6


def test_food_group_scope():
    out = _pipe().discover_foods(
        [{'nutrient_id': IRON, 'min': 1}], food_group_id=VEG_GROUP, limit=30)
    assert out['count'] > 0
    for f in out['foods']:
        assert f['FoodGroupID'] == VEG_GROUP


def test_source_scope_wafct():
    out = _pipe().discover_foods(
        [{'nutrient_id': PROTEIN, 'min': 1}], source='wafct', limit=20)
    # WAFCT may be absent in some environments; only assert when present.
    for f in out['foods']:
        assert f['FoodID'] >= 700000


def test_limit_respected():
    out = _pipe().discover_foods([{'nutrient_id': PROTEIN, 'min': 0}], limit=7)
    assert out['count'] <= 7
