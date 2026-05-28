"""Smoke tests for the FPED profile loader (Phase 1 of the FPED/FPID unlock).

Pins the public API + bridge-gated inclusion: any food (CNF or WAFCT) with a bridged
US analog gets a profile; unmatched FoodIDs return None.
"""
from __future__ import annotations

import os

import pytest

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-fped')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.services.fped_profile_loader import (  # noqa: E402
    FPED_COMPONENT_UNITS,
    get_fped_profile_for_food,
    get_profiles,
    reset_for_test,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_for_test()
    yield
    reset_for_test()


def test_profile_table_loads():
    profs = get_profiles()
    assert len(profs) > 7000, 'expected the full bridged corpus (CNF + WAFCT) to be profiled'


def test_apple_is_fruit():
    p = get_fped_profile_for_food(1696)  # Apple, raw, with skin
    assert p is not None
    assert len(p) == 37, 'all 37 FPED components must be present'
    assert p['fruit_total_cup'] > 0
    assert p['grain_refined_oz'] == 0


def test_white_bread_is_refined_grain():
    p = get_fped_profile_for_food(4066)  # Bread, white, commercial
    assert p is not None
    assert p['grain_refined_oz'] > 0
    assert p['fruit_total_cup'] == 0


def test_every_component_has_a_unit():
    p = get_fped_profile_for_food(1696)
    assert p is not None
    for key in p:
        assert key in FPED_COMPONENT_UNITS, f'{key} missing from FPED_COMPONENT_UNITS'


def test_bridged_wafct_food_included():
    # WAFCT foods that bridged to a US analog get a profile, same as CNF.
    # 700153 = "Rice, white, boiled" bridged at 0.9 confidence → grain profile.
    p = get_fped_profile_for_food(700153)
    assert p is not None
    assert p['grain_total_oz'] > 0


def test_unknown_food_returns_none():
    assert get_fped_profile_for_food(99999999) is None
