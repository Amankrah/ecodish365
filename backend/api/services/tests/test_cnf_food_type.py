"""Tests for the CNF single-vs-mixed food-type loader (cnf_food_type).

Deterministic against the built api/data/cnf_food_type.json. Skips if the label
file has not been built yet (the labels come from a one-time LLM ETL, not CI).
"""
from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-foodtype')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

import pytest  # noqa: E402

from api.services import cnf_food_type  # noqa: E402
from api.services.cnf_food_type import (  # noqa: E402
    get_food_type,
    is_mixed,
    reset_for_test,
)

# Stable CNF FoodIDs with unambiguous types (verified against the built labels).
_APPLE = 1696        # single (raw fruit)
_MILK = 123          # single (whole fluid milk)
_EGG = 125           # single (whole raw egg)
_WHITE_BREAD = 4066  # mixed (commercial baked product, multi-ingredient)
_PIZZA = 6781        # mixed (fast-food pizza with toppings)
_UNKNOWN = 99999999  # never labeled


def setup_function():
    reset_for_test()


def _require_labels():
    if not get_food_type(_APPLE) and not get_food_type(_PIZZA):
        pytest.skip('cnf_food_type.json not built yet (run build_cnf_food_type ETL)')


def test_single_ingredients_are_single():
    _require_labels()
    for fid in (_APPLE, _MILK, _EGG):
        rec = get_food_type(fid)
        assert rec is not None and rec['food_type'] == 'single', fid
        assert is_mixed(fid) is False


def test_mixed_dishes_are_mixed():
    _require_labels()
    for fid in (_WHITE_BREAD, _PIZZA):
        rec = get_food_type(fid)
        assert rec is not None and rec['food_type'] == 'mixed', fid
        assert is_mixed(fid) is True


def test_unknown_food_is_none():
    # An unlabeled / unknown id must read as "don't know", not a guess.
    assert get_food_type(_UNKNOWN) is None
    assert is_mixed(_UNKNOWN) is None


def test_wafct_foods_are_covered_when_present():
    # WAFCT foods (FoodID >= 700000) are labeled too, so the override gate can fire on
    # West African composite dishes. Skips where the WAFCT workbook wasn't ingested.
    rec = get_food_type(700000)  # "Baling béinré ... porridge" -> a composite local dish
    if rec is None:
        pytest.skip('WAFCT not ingested / not labeled in this environment')
    assert rec['food_type'] in ('single', 'mixed')
    assert is_mixed(700000) is (rec['food_type'] == 'mixed')


def test_record_shape():
    _require_labels()
    rec = get_food_type(_APPLE)
    assert set(('food_type', 'confidence', 'rationale')).issubset(rec.keys())
    assert rec['food_type'] in ('single', 'mixed')
    assert 0.0 <= rec['confidence'] <= 1.0


def test_reset_for_test_reloads():
    _require_labels()
    assert is_mixed(_APPLE) is False
    reset_for_test()
    assert cnf_food_type._cache is None  # cleared
    assert is_mixed(_APPLE) is False     # lazily reloads on next access
