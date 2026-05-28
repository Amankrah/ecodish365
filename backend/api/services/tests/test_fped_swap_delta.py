"""Tests for fped_swap_delta — expressing an ingredient swap in food-group terms."""
from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-fped')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.services.fped_aggregator import fped_swap_delta  # noqa: E402
from api.services.fped_profile_loader import (  # noqa: E402
    get_fped_profile_for_food,
    reset_for_test,
)


def setup_function():
    reset_for_test()


def _find_food(predicate, limit=8000):
    """Find a CNF FoodID whose FPED profile satisfies predicate(profile)."""
    from api.services.fped_profile_loader import get_profiles
    for fid, prof in get_profiles().items():
        if fid < limit and predicate(prof):
            return fid
    return None


def test_meat_to_legume_swap_shifts_food_groups():
    # Find a red-meat food and a legume food by their FPED profiles.
    meat_id = _find_food(lambda p: p.get('protein_meat_oz', 0) > 1.5)
    legume_id = _find_food(lambda p: p.get('protein_legumes_oz', 0) > 1.0)
    assert meat_id and legume_id, 'fixtures: need a red-meat and a legume FPED profile'

    out = fped_swap_delta(
        [{'food_id': meat_id, 'mass_g': 100}],
        [{'food_id': legume_id, 'mass_g': 100}],
    )
    assert out is not None
    by_label = {c['label']: c for c in out['changed']}
    assert 'red meat' in by_label and by_label['red meat']['direction'] == 'less'
    assert 'legumes' in by_label and by_label['legumes']['direction'] == 'more'
    assert out['partial'] is False


def test_identity_swap_returns_none():
    # Swapping a food for itself changes no food group.
    assert fped_swap_delta(
        [{'food_id': 1696, 'mass_g': 100}],
        [{'food_id': 1696, 'mass_g': 100}],
    ) is None


def test_unmatched_food_marks_partial():
    meat_id = _find_food(lambda p: p.get('protein_meat_oz', 0) > 1.5)
    out = fped_swap_delta(
        [{'food_id': meat_id, 'mass_g': 100}],
        [{'food_id': 99999999, 'mass_g': 100}],  # no FPED profile
    )
    # Swapping a profiled meat out for an unmatched food: red meat drops to ~0,
    # so there IS a change, and partial flags the unreliable replacement side.
    assert out is not None
    assert out['partial'] is True
