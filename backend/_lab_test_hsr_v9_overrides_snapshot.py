"""Lab Test A — HSR v9 classifier-refinement snapshot.

Probes the four HSR-CODE-1.x defects (A water override / B eligible fruit-veg
override / D sweet-corn FVNL eligibility / E Cat 1 V-points exact ≥ semantics)
against a small panel of CNF foods that exercise each rule. Run BEFORE and
AFTER the fix to prove the only stars / FVNL values that change are the ones
each rule targets — no collateral drift on neighbouring foods.

Mirrors the snapshot-before-implement pattern we used for the FCS / HENI /
env caches. Saves to `_lab_test_hsr_v9_overrides_baseline.json`. Tolerances:
star_rating exact (half-star quantization), fvnl_percent ≤ 1e-9.
"""
from __future__ import annotations

import io
import json
import math
import os
import sys
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

_HERE = os.path.abspath('.')
for sub in ('environmental_impact_model', 'dish_cnf_db_pipeline'):
    sys.path.insert(0, os.path.join(_HERE, sub))
import dish_project.env_bootstrap  # noqa: E402
if not os.environ.get('DJANGO_SECRET_KEY'):
    os.environ['DJANGO_SECRET_KEY'] = 'lab-test-hsr-v9-overrides'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402
django.setup()
from django.test import Client  # noqa: E402


@dataclass
class HSRProbeRow:
    label: str
    cnf_food_id: int
    serving_g: float
    expected_after_fix_stars: float
    rule: str         # 'A', 'B', 'D', 'E', or 'control' (no rule should fire)
    rationale: str


# Panel exercising each defect + control rows. Targets are the FIXED-state
# expectations; baseline (current code) is captured verbatim via the snapshot.
PANEL: List[HSRProbeRow] = [
    # Rule A — Water / Unsweetened Flavoured water name override
    HSRProbeRow(
        label='Water, municipal',
        cnf_food_id=2933, serving_g=250.0, expected_after_fix_stars=5.0, rule='A',
        rationale='HSRAC v9 Table 7 Cat 1 maps plain water to 5.0 stars BY NAME. '
                  'Current code lands at 3.5 by score because STAR_THRESHOLDS_CAT1 '
                  'pads the top two bins with NEG_INFINITY (numerically unreachable).',
    ),
    # Rule B — Eligible fruit/veg name override
    HSRProbeRow(
        label='Fruit cocktail, canned, juice pack',
        cnf_food_id=1552, serving_g=125.0, expected_after_fix_stars=5.0, rule='B',
        rationale='HSRAC v9 Table 7 Cat 2 maps "canned (in juice/water) fruit" to '
                  '5.0 stars by name. Current code may drop below 5.0 by score.',
    ),
    HSRProbeRow(
        label='Fruit cocktail, canned, heavy syrup',
        cnf_food_id=1555, serving_g=125.0, expected_after_fix_stars=5.0, rule='B',
        rationale='Heavy syrup adds sugar; v9 still maps to 5.0 by name. The '
                  'override exists precisely so canned/dried products with added '
                  'sugar or salt still hit the 5.0 band.',
    ),
    # Rule B (continued) — Sweet corn raw qualifies for the v9 whole-veg
    # 5.0-star override.
    HSRProbeRow(
        label='Sweet corn, yellow, raw',
        cnf_food_id=2388, serving_g=100.0, expected_after_fix_stars=5.0, rule='B',
        rationale='v9 Table 7 explicitly names sweet corn as an eligible '
                  'fruit/veg → 5.0 stars by name. Baseline lands at 4.5 stars by '
                  'score (high FVNL in group 11 gets close but does not reach the '
                  'top band for raw produce without the name override).',
    ),
    # Rule D — Sweet-corn FVNL eligibility (v8 Sept 2023). Forward-looking
    # insurance: CNF already routes whole sweet corn to food group 11; the
    # fix targets foods where the data source places "sweet corn" outside
    # the FVNL-eligible groups. No CNF probe exercises this directly today,
    # so the only D check is the control row below — generic "corn"-named
    # products must NOT trigger the override.
    HSRProbeRow(
        label='Fruit-juice-sweetened corn flakes cereal (D negative control)',
        cnf_food_id=1303, serving_g=30.0, expected_after_fix_stars=3.5, rule='control',
        rationale='Cereal whose name contains "corn" but is NOT "sweet corn". '
                  'D fix is anchored on the specific phrase "sweet corn" / '
                  '"corn, sweet" so this product must NOT get the v8 vegetable '
                  'override. Verifies the fix has correct specificity.',
    ),
    # Rule E — Cat 1 V-points exact ≥ semantics
    HSRProbeRow(
        label='Apple juice, frozen concentrate (Cat 1 E control)',
        cnf_food_id=1496, serving_g=250.0, expected_after_fix_stars=0.5, rule='control',
        rationale='Cat 1 beverage with INTEGER-valued FVNL (45.0). E fix '
                  'floors FVNL before the Rust call, but floor(45.0)=45.0 → '
                  'identical V-points → identical stars. Verifies the fix is '
                  'a no-op when FVNL is already integer-valued.',
    ),
    # Pure controls — fixes must not change these
    HSRProbeRow(
        label='Whole milk (Cat 1D control)',
        cnf_food_id=113, serving_g=250.0, expected_after_fix_stars=4.0, rule='control',
        rationale='Cat 1D — not affected by A/B/D/E. Snapshot must match before/after.',
    ),
    HSRProbeRow(
        label='White bread (Cat 2 control)',
        cnf_food_id=4066, serving_g=30.0, expected_after_fix_stars=3.5, rule='control',
        rationale='No name-override keywords. Snapshot must match before/after.',
    ),
]

BASELINE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '_lab_test_hsr_v9_overrides_baseline.json',
)


def _call_hsr(client: Client, row: HSRProbeRow) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    body = {'food_ids': [row.cnf_food_id], 'serving_sizes': [row.serving_g]}
    r = client.post('/api/hsr/calculate/',
                    data=json.dumps(body),
                    content_type='application/json',
                    secure=True)
    if r.status_code != 200:
        return None, None, f'HTTP {r.status_code}: {r.content[:200]!r}'
    try:
        p = r.json()
        rating = p['hsr_result']['rating']
        stars = float(rating['star_rating'])
        # FVNL% is surfaced per-food in `food_details[*]` (see hsr endpoint).
        fvnl = None
        food_details = p.get('food_details') or []
        if food_details:
            fvnl = float(food_details[0].get('fvnl_percent', 0.0))
        return stars, fvnl, None
    except Exception as exc:  # noqa: BLE001
        return None, None, f'parse: {exc!r}'


def _snapshot(client: Client) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in PANEL:
        stars, fvnl, err = _call_hsr(client, row)
        out.append({
            'label': row.label,
            'cnf_food_id': row.cnf_food_id,
            'serving_g': row.serving_g,
            'rule': row.rule,
            'baseline_stars': stars,
            'baseline_fvnl_percent': fvnl,
            'error': err,
        })
        ok = err is None
        print(f"  fid={row.cnf_food_id:<5} rule={row.rule:<7} "
              f"{'ok ' if ok else 'ERR'} stars={stars} fvnl={fvnl} — {row.label[:50]}")
    return out


def _diff(a: Any, b: Any, path: str, float_tol: float = 1e-9) -> List[str]:
    diffs: List[str] = []
    if isinstance(a, float) or isinstance(b, float):
        try:
            af, bf = float(a), float(b)
        except Exception:
            diffs.append(f'  {path}: types {type(a).__name__} vs {type(b).__name__}')
            return diffs
        if math.isnan(af) and math.isnan(bf):
            return diffs
        if abs(af - bf) > float_tol:
            diffs.append(f'  {path}: {af!r} != {bf!r} (delta {af - bf:+g})')
        return diffs
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                diffs.append(f'  {path}.{k}: missing current')
            elif k not in b:
                diffs.append(f'  {path}.{k}: missing baseline')
            else:
                diffs.extend(_diff(a[k], b[k], f'{path}.{k}', float_tol))
        return diffs
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            diffs.append(f'  {path}: list len {len(a)} != {len(b)}')
            return diffs
        for i, (av, bv) in enumerate(zip(a, b)):
            diffs.extend(_diff(av, bv, f'{path}[{i}]', float_tol))
        return diffs
    if a != b:
        diffs.append(f'  {path}: {a!r} != {b!r}')
    return diffs


def capture() -> int:
    client = Client()
    print(f'Capturing HSR v9-override baseline (n={len(PANEL)}) → {BASELINE_PATH}')
    print('-' * 100)
    snap = _snapshot(client)
    with open(BASELINE_PATH, 'w', encoding='utf-8') as f:
        json.dump({'panel': snap}, f, indent=2, sort_keys=True)
    print()
    print(f'Wrote baseline ({len(snap)} rows)')
    return 0


def verify_fixed() -> int:
    """After-fix verification: assert each rule's expected change happened,
    and that controls did NOT change."""
    if not os.path.exists(BASELINE_PATH):
        print(f'No baseline at {BASELINE_PATH}. Run "capture" first.')
        return 2
    with open(BASELINE_PATH, encoding='utf-8') as f:
        baseline = json.load(f)
    baseline_by_fid = {row['cnf_food_id']: row for row in baseline['panel']}

    client = Client()
    print(f'Verifying HSR v9-override fixes (n={len(PANEL)})')
    print('-' * 100)
    n_pass = n_fail = 0
    for row in PANEL:
        stars, fvnl, err = _call_hsr(client, row)
        b = baseline_by_fid.get(row.cnf_food_id, {})
        b_stars = b.get('baseline_stars')
        b_fvnl = b.get('baseline_fvnl_percent')

        if err is not None:
            print(f"  ERROR fid={row.cnf_food_id} {row.label}: {err}")
            n_fail += 1
            continue

        verdict = 'PASS'
        notes: List[str] = []

        if row.rule == 'control':
            # Controls must match baseline exactly.
            if stars != b_stars:
                verdict = 'FAIL'
                notes.append(f'control stars drifted {b_stars} → {stars}')
            if b_fvnl is not None and fvnl is not None and abs(fvnl - b_fvnl) > 1e-9:
                verdict = 'FAIL'
                notes.append(f'control fvnl drifted {b_fvnl} → {fvnl}')
        elif row.rule in ('A', 'B'):
            # Name overrides must lift to the specified star value.
            if stars != row.expected_after_fix_stars:
                verdict = 'FAIL'
                notes.append(f'expected {row.expected_after_fix_stars} stars, got {stars}')
        elif row.rule == 'D':
            # FVNL must rise; stars must improve by ≥ 0.5 vs baseline.
            if fvnl is None or b_fvnl is None:
                verdict = 'FAIL'
                notes.append('fvnl not available')
            elif fvnl <= b_fvnl:
                verdict = 'FAIL'
                notes.append(f'fvnl did not rise: {b_fvnl} → {fvnl}')
            elif stars is None or b_stars is None or stars - b_stars < 0.5:
                # Star improvement isn't strictly required (the cereal may have
                # other penalty-heavy components), but we document it.
                notes.append(f'stars {b_stars} → {stars} (fvnl rose {b_fvnl} → {fvnl})')
        elif row.rule == 'E':
            # FVNL flooring is an internal change; the stars must not go UP
            # (the fix removes spurious V-points, so stars stay same or drop).
            if stars is not None and b_stars is not None and stars > b_stars:
                verdict = 'FAIL'
                notes.append(f'stars rose unexpectedly: {b_stars} → {stars}')
            notes.append(f'stars {b_stars} → {stars}, fvnl {b_fvnl} → {fvnl}')

        if verdict == 'PASS':
            n_pass += 1
        else:
            n_fail += 1
        print(f"  fid={row.cnf_food_id:<5} rule={row.rule:<7} {verdict:<4} "
              f"stars={b_stars}→{stars}  fvnl={b_fvnl}→{fvnl}"
              + (f"  ({'; '.join(notes)})" if notes else ''))

    print()
    print(f'PASS {n_pass}/{len(PANEL)}  FAIL {n_fail}/{len(PANEL)}')
    return 0 if n_fail == 0 else 1


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else 'capture'
    if mode == 'capture':
        return capture()
    if mode in ('verify', 'verify_fixed'):
        return verify_fixed()
    print(f'Unknown mode: {mode!r}. Use "capture" or "verify".')
    return 2


if __name__ == '__main__':
    sys.exit(main())
