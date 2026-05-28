"""Tests for fpid_aggregator — ingredient-level food-group attribution + reconstruction QC.

Food IDs are discovered dynamically from the live FPED/FPID data (not hard-coded), so the
tests survive CNF/FNDDS edition refreshes.
"""
from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-fpid')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.services.fpid_aggregator import fpid_breakdown, fpid_reconstruction  # noqa: E402
from api.services.fped_profile_loader import (  # noqa: E402
    get_food_meta,
    get_profiles,
    reset_for_test,
)


def setup_function():
    reset_for_test()
    from heni_calculator.heni.data import fpid_loader
    fpid_loader.reset_for_test()


def _find_food(predicate, limit=2000):
    """First FoodID (with a profile) whose fpid_breakdown(200g) satisfies predicate."""
    for fid in list(get_profiles().keys())[:limit]:
        meta = get_food_meta(fid)
        if not meta or meta['bridge_confidence'] < 0.7:
            continue
        b = fpid_breakdown(fid, mass_g=200.0)
        if b is not None and predicate(b):
            return fid, b
    return None, None


def test_breakdown_attributes_red_meat_to_a_meat_ingredient():
    fid, b = _find_food(
        lambda x: any(g['component'] == 'protein_meat_oz' and x['coverage']['unmapped_pct'] < 20
                      for g in x['by_group'])
    )
    assert fid is not None, 'fixtures: need a well-covered red-meat composite'
    red = next(g for g in b['by_group'] if g['component'] == 'protein_meat_oz')
    assert red['amount'] > 0
    assert red['sources'], 'red meat must name its source ingredient(s)'
    top = red['sources'][0]['sr_description'].lower()
    assert any(w in top for w in ('beef', 'pork', 'lamb', 'veal', 'meat')), top
    assert b['coverage']['n_with_fpid'] > 0


def test_reconstruction_plausible_for_well_covered_food():
    fid, _ = _find_food(lambda x: x['coverage']['unmapped_pct'] < 10
                        and any(g['component'] == 'protein_meat_oz' for g in x['by_group']))
    assert fid is not None
    r = fpid_reconstruction(fid)
    assert r is not None
    assert r['cosine'] is not None and r['cosine'] >= 0.70
    assert r['plausible'] is True


def test_partial_coverage_reports_unmapped_mass():
    # Some recipes contain SR ingredients with no FPID row (e.g. NFS oils/milk) -> the
    # gap must surface as unmapped recipe mass, never be hidden.
    fid, b = _find_food(lambda x: x['coverage']['n_with_fpid'] < x['coverage']['n_ingredients'])
    assert fid is not None, 'fixtures: need a recipe with at least one un-FPID ingredient'
    assert b['coverage']['unmapped_pct'] > 0


def test_unbridged_food_returns_none():
    assert fpid_breakdown(99999999) is None
    assert fpid_reconstruction(99999999) is None


def test_get_food_meta():
    fid = next(iter(get_profiles().keys()))
    meta = get_food_meta(fid)
    assert meta is not None
    assert set(meta) == {'food_code', 'fdc_id', 'bridge_confidence'}
    assert meta['fdc_id'] > 0 and meta['food_code'] > 0
    assert get_food_meta(99999999) is None
