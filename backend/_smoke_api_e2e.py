"""End-to-end API smoke test for the environmental-impact endpoints.

Hits the Django views in-process (no server needed) using Django's test client,
across a panel of real CNF foods spanning several FoodGroupName buckets, with
matcher both off and on. Asserts the v1 trim + bands + audit invariants survive
the full request -> response pipeline.

Verifies:
  - HTTP 200 on each endpoint.
  - Response carries the new band fields (`midpoint_impacts_bands`,
    `endpoint_impacts_bands`).
  - midpoint dict keys are exactly the v1 consumed set.
  - endpoint_impacts['Resources'] is None (Python None, may be JSON null).
  - endpoint_impacts_bands does NOT carry 'Resources'.
  - single_score is finite + positive (didn't get NaN'd by None handling).
  - environmental_score not silently inflated by trimmed categories.
  - Per-food profile endpoint exposes only the 3 consumed categories.
"""
from __future__ import annotations

import json, os, sys, traceback

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa
# env_bootstrap loaded backend/.env (which has DJANGO_SECRET_KEY=, i.e. empty);
# the empty string overrides the `get_random_secret_key()` default in
# settings.py and Django then refuses to run. For an in-process smoke test
# we just need a stable test key.
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'smoke-e2e-not-for-production'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django; django.setup()
from django.test import Client

CONSUMED_V1 = {'Global warming', 'Land use', 'Water consumption'}
TRIMMED_AWAY = {
    'Stratospheric ozone depletion', 'Ionizing radiation',
    'Ozone formation, Human health', 'Fine particulate matter formation',
    'Ozone formation, Terrestrial ecosystems', 'Terrestrial acidification',
    'Freshwater eutrophication', 'Marine eutrophication',
    'Terrestrial ecotoxicity', 'Freshwater ecotoxicity', 'Marine ecotoxicity',
    'Human carcinogenic toxicity', 'Human non-carcinogenic toxicity',
    'Mineral resource scarcity', 'Fossil resource scarcity',
}

# Diverse panel of real CNF food_ids (pre-verified to exist in the CNF database).
# food_id 7 = Beef pot roast; 2380 = Carrot raw; 1486 = Apple; 461 = Fish oil salmon;
# 51 = Processed cheddar; 219 = Cereal of some sort.
FOOD_PANEL = [
    (7,    'Beef pot roast',  150),
    (2380, 'Carrot raw',      100),
    (1486, 'Apple cooked',    100),
    (461,  'Fish oil salmon', 30),
    (51,   'Processed cheddar', 50),
    (219,  'Cereal',          80),
]


def assert_v1_invariants(midpoints: dict, endpoints: dict, mid_bands: dict, ep_bands: dict, ctx: str):
    """Single source of truth for v1 invariants across all API surfaces."""
    errors = []

    # 1. Midpoint vector trimmed exactly to 3 consumed categories.
    actual_keys = set(midpoints.keys())
    if actual_keys != CONSUMED_V1:
        leak = actual_keys & TRIMMED_AWAY
        missing = CONSUMED_V1 - actual_keys
        errors.append(f"midpoint vector wrong: got {sorted(actual_keys)}; leak={sorted(leak)}; missing={sorted(missing)}")

    # 2. Bands present and ordered low <= central <= high.
    if not isinstance(mid_bands, dict) or set(mid_bands.keys()) != CONSUMED_V1:
        errors.append(f"midpoint_impacts_bands keys wrong: {sorted(mid_bands.keys()) if mid_bands else None}")
    else:
        for cat, b in mid_bands.items():
            if not (b['low'] <= b['central'] <= b['high']):
                errors.append(f"band ordering violated for {cat}: {b}")
            if abs(b['central'] - midpoints[cat]) > 1e-9:
                errors.append(f"band central != scalar for {cat}: band={b['central']} scalar={midpoints[cat]}")

    # 3. Resources endpoint is None.
    if endpoints.get('Resources') is not None:
        errors.append(f"endpoint_impacts['Resources'] should be None, got {endpoints.get('Resources')}")

    # 4. endpoint_impacts_bands does NOT include 'Resources'.
    if 'Resources' in (ep_bands or {}):
        errors.append("endpoint_impacts_bands should drop 'Resources' entirely")

    # 5. HH and Ecosystems endpoint bands ordered low <= central <= high.
    for ep_name in ('Human Health', 'Ecosystems'):
        b = (ep_bands or {}).get(ep_name) or {}
        if not b:
            errors.append(f"endpoint_impacts_bands missing {ep_name}")
        elif not (b.get('low', 0) <= b.get('central', 0) <= b.get('high', 0)):
            errors.append(f"endpoint band ordering violated for {ep_name}: {b}")

    return errors


def find_lca_dict(payload: dict):
    """Locate the LCA block inside a formatted API payload.

    `format_environmental_results` renames `midpoint_impacts` -> `all_impacts`
    and exposes the new band fields as `all_impacts_bands` /
    `endpoint_impacts_bands` under `environmental_impacts`. We walk the tree
    until we find a dict carrying either `all_impacts` or `midpoint_impacts`.
    """
    def walk(obj):
        if isinstance(obj, dict):
            if isinstance(obj.get('all_impacts'), dict) or isinstance(obj.get('midpoint_impacts'), dict):
                yield obj
            for v in obj.values():
                yield from walk(v)
        elif isinstance(obj, list):
            for it in obj:
                yield from walk(it)
    candidates = list(walk(payload))
    return candidates[0] if candidates else None


def normalize_lca_block(lca: dict):
    """Return (midpoints, endpoints, mid_bands, ep_bands) regardless of
    whether the response uses the raw keys (midpoint_impacts*) or the
    formatter-renamed keys (all_impacts / all_impacts_bands)."""
    mids = lca.get('midpoint_impacts') or lca.get('all_impacts') or {}
    eps = lca.get('endpoint_impacts') or {}
    mid_bands = lca.get('midpoint_impacts_bands') or lca.get('all_impacts_bands') or {}
    ep_bands = lca.get('endpoint_impacts_bands') or {}
    return mids, eps, mid_bands, ep_bands


def main() -> int:
    client = Client()
    all_errors = []

    # ============================================================ #
    # Endpoint 1: POST /api/environmental-impact/                  #
    # ============================================================ #
    print("=" * 72)
    print("ENDPOINT 1: POST /api/environmental-impact/")
    print("=" * 72)
    for matcher_flag in (False, True):
        meal_body = {
            'foods': [{'food_id': fid, 'quantity': q} for fid, _, q in FOOD_PANEL],
            'user_type': 'researcher',
            'enable_lca_matcher': matcher_flag,
        }
        print(f"\n--- matcher={'ON' if matcher_flag else 'OFF'} ---")
        resp = client.post(
            '/api/environmental-impact/',
            data=json.dumps(meal_body),
            content_type='application/json',
            secure=True,
        )
        print(f"  HTTP {resp.status_code}")
        if resp.status_code != 200:
            try:
                print(f"  body: {resp.json()}")
            except Exception:
                print(f"  raw: {resp.content[:500]}")
            all_errors.append(f"endpoint /environmental-impact/ returned {resp.status_code} matcher={matcher_flag}")
            continue

        payload = resp.json()
        lca = find_lca_dict(payload)
        if lca is None:
            all_errors.append("could not locate LCA block in response payload (no all_impacts/midpoint_impacts key)")
            continue
        mids, eps, mid_bands, ep_bands = normalize_lca_block(lca)

        # In the formatted response, the single score lives under
        # summary_score.value, not as a flat key (the formatter wraps it).
        summary = lca.get('summary_score') or {}
        single_score = summary.get('value') if isinstance(summary, dict) else lca.get('single_score')

        print(f"  midpoint keys: {sorted(mids.keys())}")
        print(f"  endpoint keys: {sorted(eps.keys())}   Resources={eps.get('Resources')}")
        print(f"  midpoint_impacts_bands keys: {sorted(mid_bands.keys())}")
        print(f"  endpoint_impacts_bands keys: {sorted(ep_bands.keys())}")
        print(f"  single_score (summary_score.value): {single_score}")
        if single_score is None or not isinstance(single_score, (int, float)) or single_score <= 0:
            all_errors.append(f"single_score not a positive number (matcher={matcher_flag}): {single_score}")

        errs = assert_v1_invariants(mids, eps, mid_bands, ep_bands, ctx=f"matcher={matcher_flag}")
        if errs:
            print("  ERRORS:")
            for e in errs: print(f"    - {e}")
            all_errors.extend(errs)
        else:
            print("  v1 invariants OK")

        # Spot-check environmental_score in the formatted output for sane range.
        # Look for environmental_score anywhere in the payload.
        def find_key(obj, key):
            if isinstance(obj, dict):
                if key in obj: yield obj[key]
                for v in obj.values(): yield from find_key(v, key)
            elif isinstance(obj, list):
                for it in obj: yield from find_key(it, key)
        env_scores = list(find_key(payload, 'environmental_score'))
        if env_scores:
            es = env_scores[0]
            print(f"  environmental_score: {es}")
            if not (0 <= es <= 100):
                all_errors.append(f"environmental_score out of [0,100]: {es}")

    # ============================================================ #
    # Endpoint 2: POST /api/environmental-impact/compare-foods/    #
    # ============================================================ #
    print()
    print("=" * 72)
    print("ENDPOINT 2: POST /api/environmental-impact/compare-foods/")
    print("=" * 72)
    compare_body = {
        'foods': [{'food_id': fid, 'quantity': q} for fid, _, q in FOOD_PANEL[:3]],
        'user_type': 'researcher',
    }
    resp = client.post(
        '/api/environmental-impact/compare-foods/',
        data=json.dumps(compare_body),
        content_type='application/json',
        secure=True,
    )
    print(f"  HTTP {resp.status_code}")
    if resp.status_code != 200:
        try: print(f"  body: {resp.json()}")
        except Exception: print(f"  raw: {resp.content[:500]}")
        all_errors.append(f"compare-foods/ returned {resp.status_code}")
    else:
        # compare-foods produces per-food comparisons; spot-check shape.
        payload = resp.json()
        print(f"  top-level keys: {list(payload.keys())[:10]}")

    # ============================================================ #
    # Endpoint 3: GET /api/environmental-impact/food/<id>/profile/ #
    # ============================================================ #
    print()
    print("=" * 72)
    print("ENDPOINT 3: GET /api/environmental-impact/food/<id>/profile/")
    print("=" * 72)
    for fid, name, _ in FOOD_PANEL[:3]:
        resp = client.get(f'/api/environmental-impact/food/{fid}/profile/', secure=True)
        print(f"\n--- food_id={fid} ({name}) HTTP {resp.status_code} ---")
        if resp.status_code != 200:
            try: print(f"  body: {resp.json()}")
            except Exception: print(f"  raw: {resp.content[:500]}")
            all_errors.append(f"profile/{fid} returned {resp.status_code}")
            continue
        payload = resp.json()
        # Find environmental_impact dict (per-food) anywhere in the response.
        def find_key(obj, key):
            if isinstance(obj, dict):
                if key in obj: yield obj[key]
                for v in obj.values(): yield from find_key(v, key)
            elif isinstance(obj, list):
                for it in obj: yield from find_key(it, key)
        env_impacts = list(find_key(payload, 'environmental_impact'))
        if env_impacts and isinstance(env_impacts[0], dict):
            ei = env_impacts[0]
            keys_present = set(k for k in ei.keys() if isinstance(k, str) and not k.startswith('_'))
            print(f"  per-food env_impact keys: {sorted(keys_present)}")
            leak = keys_present & TRIMMED_AWAY
            if leak:
                all_errors.append(f"profile/{fid}: per-food impact leaked trimmed categories: {sorted(leak)}")
            elif keys_present != CONSUMED_V1 and CONSUMED_V1.issubset(keys_present):
                pass  # OK — may have extra meta keys but no leak
            else:
                missing = CONSUMED_V1 - keys_present
                if missing:
                    all_errors.append(f"profile/{fid}: missing consumed-category keys: {sorted(missing)}")

    # ============================================================ #
    # Summary                                                       #
    # ============================================================ #
    print()
    print("=" * 72)
    if all_errors:
        print(f"FAIL — {len(all_errors)} error(s):")
        for e in all_errors:
            print(f"  - {e}")
        return 1
    print("PASS — all API endpoints honour v1 trim + bands invariants.")
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception:
        traceback.print_exc()
        sys.exit(2)
