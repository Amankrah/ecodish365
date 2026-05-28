"""Tests for the FPED decomposition-plausibility QC (Phase 5)."""
from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-fped')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.services.fped_aggregator import decomposition_plausibility  # noqa: E402
from api.services.fped_profile_loader import reset_for_test  # noqa: E402


def setup_function():
    reset_for_test()


def test_consistent_decomposition_is_plausible():
    # Applesauce (1700) "decomposed" into apple (1696): both fruit-dominant.
    qc = decomposition_plausibility(1700, [{'food_id': 1696, 'mass_g': 100}])
    assert qc is not None and qc['available']
    assert qc['cosine'] is not None and qc['cosine'] >= 0.7
    assert qc['plausible'] is True


def test_inconsistent_decomposition_flagged():
    # Applesauce "decomposed" into white bread (4066): grain, not fruit.
    qc = decomposition_plausibility(1700, [{'food_id': 4066, 'mass_g': 100}])
    assert qc is not None
    assert qc['plausible'] is False
    assert qc['cosine'] < 0.7


def test_no_fped_twin_returns_none():
    # A composite with no FPED profile (never bridged) → QC not applicable.
    assert decomposition_plausibility(99999999, [{'food_id': 1696, 'mass_g': 100}]) is None


def test_empty_ingredients_returns_none():
    assert decomposition_plausibility(1700, []) is None
