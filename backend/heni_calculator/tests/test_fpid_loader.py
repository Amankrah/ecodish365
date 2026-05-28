"""Smoke tests for the FPID ingredient loader.

The loader is an integration-surface stub with no production consumer yet.
These tests pin the public API shape against three real FNDDS finished foods
with known-good FPID coverage, plus the not-found path.

Fixture food codes were chosen from the FNDDS 2017-2018 survey foods bundle
to span a range of ingredient counts (1, 2, 8) so any regression in the
input_food join or the FPID lookup surfaces quickly.
"""
from __future__ import annotations

import pytest

from heni_calculator.heni.data.fpid_loader import (
    FpidIngredient,
    get_fpid_ingredients_by_fdc_id,
    get_fpid_ingredients_for_fndds,
    reset_for_test,
)


# (food_code, fdc_id, expected_ingredient_count, expected_description_substring)
_FIXTURES = [
    (11111000, 2705385, 1, 'Milk, whole'),
    (11115400, 2705394, 2, 'Kefir'),
    (11360200, 2705412, 8, 'Oat milk'),
]


@pytest.fixture(autouse=True)
def _reset_loader():
    """Clear singleton state between tests so cache loading is exercised."""
    reset_for_test()
    yield
    reset_for_test()


@pytest.mark.parametrize('food_code, _fdc_id, expected_n, _desc', _FIXTURES)
def test_get_fpid_ingredients_for_fndds_known_foods(
        food_code: int, _fdc_id: int, expected_n: int, _desc: str) -> None:
    ingredients = get_fpid_ingredients_for_fndds(food_code)
    assert ingredients is not None, f'food_code={food_code} should resolve to ingredients'
    assert len(ingredients) == expected_n, (
        f'food_code={food_code} expected {expected_n} ingredients, got {len(ingredients)}'
    )
    for ing in ingredients:
        assert isinstance(ing, FpidIngredient)
        assert ing.sr_code > 0
        assert ing.sr_description, 'sr_description should be populated'
        assert ing.gram_weight >= 0.0
        # pattern_equivalents may be empty if the sr_code isn't in FPID, but
        # the dict itself must exist.
        assert isinstance(ing.pattern_equivalents, dict)


@pytest.mark.parametrize('_food_code, fdc_id, expected_n, _desc', _FIXTURES)
def test_get_fpid_ingredients_by_fdc_id_matches_food_code_path(
        _food_code: int, fdc_id: int, expected_n: int, _desc: str) -> None:
    """The two entry points must agree for the same finished food."""
    via_fdc = get_fpid_ingredients_by_fdc_id(fdc_id)
    via_food_code = get_fpid_ingredients_for_fndds(_food_code)
    assert via_fdc is not None and via_food_code is not None
    assert len(via_fdc) == len(via_food_code) == expected_n
    # Same ordering (seq_num-sorted on load).
    for a, b in zip(via_fdc, via_food_code):
        assert a.sr_code == b.sr_code
        assert a.seq_num == b.seq_num
        assert a.gram_weight == b.gram_weight


def test_at_least_one_ingredient_has_fpid_pattern_data() -> None:
    """Across the fixtures, at least one ingredient must have non-empty FPID
    pattern data — otherwise the join is silently broken."""
    saw_pattern_data = False
    for food_code, _fdc, _n, _desc in _FIXTURES:
        ingredients = get_fpid_ingredients_for_fndds(food_code) or []
        for ing in ingredients:
            if ing.pattern_equivalents:
                saw_pattern_data = True
                break
        if saw_pattern_data:
            break
    assert saw_pattern_data, (
        'No fixture ingredient resolved to an FPID row. The CODE <-> sr_code '
        'join is likely broken (check FPID CODE coercion to int64).'
    )


def test_unknown_food_code_returns_none() -> None:
    assert get_fpid_ingredients_for_fndds(99999999) is None


def test_unknown_fdc_id_returns_none() -> None:
    assert get_fpid_ingredients_by_fdc_id(-1) is None


def test_reset_for_test_clears_cache() -> None:
    """Sanity: reset_for_test forces a fresh load on the next call."""
    first = get_fpid_ingredients_for_fndds(11111000)
    reset_for_test()
    second = get_fpid_ingredients_for_fndds(11111000)
    assert first is not None and second is not None
    assert len(first) == len(second)
