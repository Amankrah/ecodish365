"""Tests for fped_cohort — food-group exposure distribution across N recalls."""
from __future__ import annotations

import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-cohort')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.services.fped_cohort import aggregate_cohort  # noqa: E402
from api.services.fped_profile_loader import reset_for_test  # noqa: E402


def setup_function():
    reset_for_test()


def _find_food(predicate, limit=8000):
    from api.services.fped_profile_loader import get_profiles
    for fid, prof in get_profiles().items():
        if fid < limit and predicate(prof):
            return fid
    return None


def _comp(cohort, component):
    return next(c for c in cohort['components'] if c['component'] == component)


def test_median_and_iqr_across_recalls():
    veg_id = _find_food(lambda p: p.get('veg_total_cup', 0) > 0.2)
    assert veg_id, 'fixtures: need a vegetable FPED profile'
    # 3 recalls with increasing vegetable mass -> median = middle recall's intake.
    recalls = [
        [{'food_id': veg_id, 'mass_g': 100}],
        [{'food_id': veg_id, 'mass_g': 200}],
        [{'food_id': veg_id, 'mass_g': 300}],
    ]
    cohort = aggregate_cohort(recalls)
    assert cohort['n_recalls'] == 3
    veg = _comp(cohort, 'veg_total_cup')
    assert veg['min'] < veg['median'] < veg['max']
    # middle recall (200 g) is the median; ends are min/max.
    assert abs(veg['median'] - 2 * veg['min']) < 0.05
    assert veg['q1'] <= veg['median'] <= veg['q3']


def test_pct_meeting_target_aim_at_least():
    # A big vegetable serving should meet the veg target; a tiny one should not.
    veg_id = _find_food(lambda p: p.get('veg_total_cup', 0) > 0.2)
    big = [{'food_id': veg_id, 'mass_g': 2000}]   # well above the ~2.5 cup target
    tiny = [{'food_id': veg_id, 'mass_g': 1}]     # essentially zero
    cohort = aggregate_cohort([big, tiny])
    veg = _comp(cohort, 'veg_total_cup')
    assert veg['direction'] == 'aim_at_least'
    assert veg['pct_meeting_myplate'] == 50.0  # exactly one of two recalls meets it


def test_pct_meeting_target_keep_at_most():
    # added sugars is a keep_at_most limit: a huge sugar load should breach it.
    sugar_id = _find_food(lambda p: p.get('added_sugars_tsp', 0) > 1.0)
    assert sugar_id, 'fixtures: need an added-sugars FPED profile'
    over = [{'food_id': sugar_id, 'mass_g': 3000}]  # far over the limit
    cohort = aggregate_cohort([over])
    sug = _comp(cohort, 'added_sugars_tsp')
    assert sug['direction'] == 'keep_at_most'
    assert sug['pct_meeting_myplate'] == 0.0  # the only recall is over the limit


def test_single_recall_median_is_that_value():
    veg_id = _find_food(lambda p: p.get('veg_total_cup', 0) > 0.2)
    cohort = aggregate_cohort([[{'food_id': veg_id, 'mass_g': 150}]])
    assert cohort['n_recalls'] == 1
    veg = _comp(cohort, 'veg_total_cup')
    assert veg['median'] == veg['min'] == veg['max']


def test_empty_cohort():
    cohort = aggregate_cohort([])
    assert cohort['n_recalls'] == 0
    assert cohort['components'] == []


def test_unmatched_food_flagged_in_coverage():
    cohort = aggregate_cohort([[{'food_id': 99999999, 'mass_g': 100}]])
    assert cohort['coverage']['n_recalls_with_unmatched'] == 1
