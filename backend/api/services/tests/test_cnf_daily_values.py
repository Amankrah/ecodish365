"""Tests for the Health Canada %DV reference + frontend/backend parity.

The backend table (api/data/cnf_daily_values.json) and the frontend mirror
(frontend/src/lib/cnfDailyValues.data.json) must carry identical `values`, so %DV
display and %DV-threshold filtering can never drift.
"""
from __future__ import annotations

import json
import os

os.environ.setdefault('DJANGO_SECRET_KEY', 'test-dv')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')

import django  # noqa: E402

django.setup()

from api.services import cnf_daily_values as dv  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, '..', '..', '..', '..'))  # tests->services->api->backend->repo
_BACKEND_JSON = os.path.join(_REPO, 'backend', 'api', 'data', 'cnf_daily_values.json')
_FRONTEND_JSON = os.path.join(_REPO, 'frontend', 'src', 'lib', 'cnfDailyValues.data.json')


def setup_function():
    dv.reset_for_test()


def test_frontend_backend_values_are_identical():
    back = json.loads(open(_BACKEND_JSON, encoding='utf-8').read())['values']
    front = json.loads(open(_FRONTEND_JSON, encoding='utf-8').read())['values']
    assert back == front, 'cnf_daily_values.json and cnfDailyValues.data.json values diverged'


def test_known_daily_values():
    assert dv.get_daily_value(307)['dv'] == 2300      # sodium mg
    assert dv.get_daily_value(303)['dv'] == 18        # iron mg
    assert dv.get_daily_value(301)['unit'] == 'mg'    # calcium
    assert dv.get_daily_value(320)['unit'] == 'µg'    # vitamin A RAE
    # Protein / total carbohydrate carry no Canadian %DV.
    assert dv.get_daily_value(203) is None
    assert dv.get_daily_value(205) is None


def test_percent_dv_basic():
    # 1150 mg calcium / 1300 mg DV ≈ 88.5 %
    pct = dv.percent_dv(301, 1150)
    assert pct is not None and abs(pct - 88.46) < 0.1
    # No DV -> None
    assert dv.percent_dv(203, 50) is None


def test_percent_dv_saturated_sums_trans():
    # Saturated fat (606) %DV sums trans fat (605) against the 20 g DV.
    pct = dv.percent_dv(606, 4.0, lookup_other=lambda nid: 1.0 if nid == 605 else None)
    assert pct is not None and abs(pct - 25.0) < 1e-6   # (4 + 1) / 20 * 100
    # Without the trans lookup, only saturated counts.
    assert abs(dv.percent_dv(606, 4.0) - 20.0) < 1e-6
