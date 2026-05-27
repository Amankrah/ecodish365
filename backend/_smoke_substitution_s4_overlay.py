#!/usr/bin/env python
"""Tier D — S4-lite day-level S5 substitution overlay (SUBST-1 manuscript).

For each S4-lite day containing at least one S5-eligible ingredient (beef,
cow's milk, cola, refined white bread), applies all matching curated S5 rules
(mass-preserving) and reports full-day scorecard deltas vs baseline.

Uses deterministic rule application (no embedding discovery) for speed and
reproducibility. Optional `--with-analyzer` runs the production analyzer on
eligible days only (slower; requires API keys).

Outputs (repo root):
  results/S5-subst/s4_overlay.csv
  results/S5-subst/s4_overlay.json
  results/S5-subst/s4_overlay_exemplars.json
  backend/_smoke_substitution_s4_overlay_results.json

Run from `backend/`:
    set PYTHONIOENCODING=utf-8 && python _smoke_substitution_s4_overlay.py
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dish_project.settings')
import django  # noqa: E402

django.setup()

from api.services.substitution_analyzer import _normalize_composition  # noqa: E402
from api.services.substitution_rules import SUBSTITUTION_RULES, ingredient_matches_rule  # noqa: E402
from api.services.substitution_scorecard import enrich_scorecard_deltas  # noqa: E402

from _smoke_s4_lite_panel import S4_LITE_PANEL, S4LiteDay  # noqa: E402

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:  # noqa: BLE001
    pass

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_OUT = os.path.join(_REPO, 'results', 'S5-subst')
_S4_BASELINE = os.path.join(_REPO, 'results', 'S4-lite', 'meals_panel.csv')


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=_REPO, text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:  # noqa: BLE001
        return 'unknown'


def _day_rows(day: S4LiteDay) -> List[Dict[str, Any]]:
    return [{'food_id': fid, 'mass_g': g} for fid, g, _ in day.foods]


def _matching_rules(rows: List[Dict[str, Any]]) -> List[Tuple[int, str]]:
    norm = _normalize_composition(rows)
    hits: List[Tuple[int, str]] = []
    for idx, ing in enumerate(norm):
        for rule in SUBSTITUTION_RULES:
            if ingredient_matches_rule(
                food_id=ing['food_id'],
                food_description=ing['food_description'],
                food_group=ing['food_group'],
                food_group_id=ing.get('food_group_id'),
                rule=rule,
            ):
                hits.append((idx, rule.id))
                break
    return hits


def _apply_all_s5_rules(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    norm = _normalize_composition(rows)
    modified = [dict(r) for r in norm]
    swaps: List[Dict[str, Any]] = []

    for idx, ing in enumerate(norm):
        for rule in SUBSTITUTION_RULES:
            if not ingredient_matches_rule(
                food_id=ing['food_id'],
                food_description=ing['food_description'],
                food_group=ing['food_group'],
                food_group_id=ing.get('food_group_id'),
                rule=rule,
            ):
                continue
            modified[idx] = {
                **modified[idx],
                'food_id': rule.target_food_id,
                'food_description': rule.target_food_description,
            }
            swaps.append({
                'rule_id': rule.id,
                'original_food_id': ing['food_id'],
                'original_description': ing['food_description'],
                'replacement_food_id': rule.target_food_id,
                'replacement_description': rule.target_food_description,
                'mass_g': ing['mass_g'],
            })
            break

    return modified, swaps


def _val(sc: Dict[str, Any], key: str) -> Optional[float]:
    block = sc.get(key) or {}
    v = block.get('value')
    return float(v) if v is not None else None


def _delta_block(deltas: Dict[str, Any], key: str) -> Dict[str, Any]:
    return deltas.get(key) or {}


def _load_s4_baselines() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not os.path.isfile(_S4_BASELINE):
        return out
    with open(_S4_BASELINE, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            out[row['day_id']] = row
    return out


def _optional_analyzer_check(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Lightweight analyzer sanity check (curated rules only via rank_score path)."""
    try:
        from api.services.substitution_analyzer import analyze_substitutions
        result = analyze_substitutions(
            rows,
            purpose='general_health',
            max_suggestions=3,
            include_scorecard=False,
            reformulation_mode='singles',
            constraints={'max_swaps': 1},
        )
        top = (result.get('suggestions') or [None])[0]
        return {
            'n_suggestions': len(result.get('suggestions') or []),
            'top_rule_id': top.get('rule_id') if top else None,
            'top_rank_score': top.get('rank_score') if top else None,
        }
    except Exception as exc:  # noqa: BLE001
        return {'error': str(exc)}


def _process_day(
    day: S4LiteDay,
    s4_baselines: Dict[str, Dict[str, Any]],
    *,
    with_analyzer: bool,
) -> Dict[str, Any]:
    rows = _day_rows(day)
    rule_hits = _matching_rules(rows)
    t0 = time.perf_counter()

    result: Dict[str, Any] = {
        'day_id': day.day_id,
        'label': day.label,
        'stratum': day.stratum,
        'nutrition_tier': day.nutrition_tier,
        'n_foods': len(day.foods),
        's5_eligible': len(rule_hits) > 0,
        's5_rule_hits': [{'index': i, 'rule_id': r} for i, r in rule_hits],
        'rationale': day.rationale,
    }

    if not rule_hits:
        result['overlay_mode'] = 'skipped'
        result['elapsed_ms'] = round((time.perf_counter() - t0) * 1000, 1)
        return result

    modified, swaps = _apply_all_s5_rules(rows)
    baseline_norm = _normalize_composition(rows)
    scorecard = enrich_scorecard_deltas(baseline_norm, modified)
    deltas = scorecard['deltas']
    s4 = s4_baselines.get(day.day_id, {})

    result.update({
        'overlay_mode': 'deterministic_all_s5',
        'n_swaps_applied': len(swaps),
        'swaps': swaps,
        'baseline': {
            'hefi': _val(scorecard['baseline'], 'hefi'),
            'heni_min': _val(scorecard['baseline'], 'heni'),
            'hsr': _val(scorecard['baseline'], 'hsr'),
            'fcs': _val(scorecard['baseline'], 'fcs'),
            'environmental': _val(scorecard['baseline'], 'environmental'),
            'top_pattern': (scorecard['baseline'].get('dietary_pattern') or {}).get('top_pattern_id'),
        },
        'modified': {
            'hefi': _val(scorecard['modified'], 'hefi'),
            'heni_min': _val(scorecard['modified'], 'heni'),
            'hsr': _val(scorecard['modified'], 'hsr'),
            'fcs': _val(scorecard['modified'], 'fcs'),
            'environmental': _val(scorecard['modified'], 'environmental'),
            'top_pattern': (scorecard['modified'].get('dietary_pattern') or {}).get('top_pattern_id'),
        },
        'delta': {
            'hefi': _delta_block(deltas, 'hefi').get('delta'),
            'heni_min': _delta_block(deltas, 'heni').get('delta'),
            'hsr': _delta_block(deltas, 'hsr').get('delta'),
            'fcs': _delta_block(deltas, 'fcs').get('delta'),
            'environmental': _delta_block(deltas, 'environmental').get('delta'),
        },
        'improved': {
            'hefi': _delta_block(deltas, 'hefi').get('improved'),
            'heni': _delta_block(deltas, 'heni').get('improved'),
            'hsr': _delta_block(deltas, 'hsr').get('improved'),
            'fcs': _delta_block(deltas, 'fcs').get('improved'),
            'environmental': _delta_block(deltas, 'environmental').get('improved'),
        },
        's4_lite_baseline_hefi': float(s4['hefi_score']) if s4.get('hefi_score') else None,
        's4_lite_baseline_heni': float(s4['heni_minutes']) if s4.get('heni_minutes') else None,
        's4_lite_baseline_env_gw': float(s4['env_gw_per_100kcal']) if s4.get('env_gw_per_100kcal') else None,
    })

    heni_ok = result['improved'].get('heni') is True
    env_ok = result['improved'].get('environmental') is True
    hefi_ok = result['improved'].get('hefi') is True
    result['win_win_heni_env'] = heni_ok and env_ok
    result['win_win_hefi_heni_env'] = hefi_ok and heni_ok and env_ok

    if with_analyzer:
        result['analyzer'] = _optional_analyzer_check(rows)

    result['elapsed_ms'] = round((time.perf_counter() - t0) * 1000, 1)
    return result


def _build_exemplars(processed: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not processed:
        return {}

    def _heni_gain(r: Dict[str, Any]) -> float:
        v = (r.get('delta') or {}).get('heni_min')
        return -float(v) if v is not None else 0.0

    def _env_gain(r: Dict[str, Any]) -> float:
        v = (r.get('delta') or {}).get('environmental')
        return -float(v) if v is not None else 0.0

    best_overlay = max(scored := processed, key=lambda r: _heni_gain(r) + _env_gain(r) * 500)
    best_hefi = max(scored, key=lambda r: float((r.get('delta') or {}).get('hefi') or -999))
    lose_lose_before = min(scored, key=lambda r: float((r.get('baseline') or {}).get('hefi') or 999))

    return {
        'best_heni_env_overlay': {
            'day_id': best_overlay['day_id'],
            'label': best_overlay['label'],
            'n_swaps': best_overlay['n_swaps_applied'],
            'delta': best_overlay['delta'],
            'win_win_heni_env': best_overlay.get('win_win_heni_env'),
        },
        'largest_hefi_gain': {
            'day_id': best_hefi['day_id'],
            'label': best_hefi['label'],
            'delta': best_hefi['delta'],
        },
        'pre_overlay_lose_lose_anchor': {
            'day_id': lose_lose_before['day_id'],
            'label': lose_lose_before['label'],
            'baseline': lose_lose_before.get('baseline'),
            'delta_after_s5': lose_lose_before.get('delta'),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='S4-lite S5 substitution overlay')
    parser.add_argument('--all-days', action='store_true', help='Include ineligible days in JSON output')
    parser.add_argument('--with-analyzer', action='store_true', help='Run analyzer check per day (slow)')
    args = parser.parse_args()

    os.makedirs(_OUT, exist_ok=True)
    s4_baselines = _load_s4_baselines()

    print('S4-lite × S5 substitution overlay (Tier D)')
    print('=' * 60)

    all_results = [
        _process_day(day, s4_baselines, with_analyzer=args.with_analyzer)
        for day in S4_LITE_PANEL
    ]
    eligible = [r for r in all_results if r.get('s5_eligible')]
    processed = [r for r in eligible if r.get('overlay_mode') != 'skipped']

    for r in processed:
        d = r.get('delta') or {}
        ww = ' WIN-WIN' if r.get('win_win_heni_env') else ''
        print(
            f"{r['day_id']:4s} swaps={r['n_swaps_applied']}  "
            f"ΔHEFI {d.get('hefi', 0):+.1f}  ΔHENI {d.get('heni_min', 0):+.1f}  "
            f"Δenv {d.get('environmental', 0):+.4f}{ww}"
        )

    win_wins = sum(1 for r in processed if r.get('win_win_heni_env'))
    hefi_up = sum(1 for r in processed if r.get('improved', {}).get('hefi') is True)

    manifest = {
        'harness': 'S4-lite S5 substitution overlay (Tier D)',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'git_sha': _git_sha(),
        'overlay_method': 'deterministic_all_s5',
        's4_lite_days': len(S4_LITE_PANEL),
        's5_eligible_days': len(eligible),
        'overlay_success': len(processed),
        'win_win_heni_env_count': win_wins,
        'hefi_improved_count': hefi_up,
    }

    exemplars = _build_exemplars(processed)
    payload = {
        'manifest': manifest,
        'days': all_results if args.all_days else eligible,
        'exemplars': exemplars,
        'summary': {
            'eligible_day_ids': [r['day_id'] for r in eligible],
            'win_win_days': [r['day_id'] for r in processed if r.get('win_win_heni_env')],
            'hefi_improved_days': [r['day_id'] for r in processed if r.get('improved', {}).get('hefi')],
        },
    }

    json_path = os.path.join(_OUT, 's4_overlay.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

    csv_path = os.path.join(_OUT, 's4_overlay.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow([
            'day_id', 'label', 'stratum', 'n_swaps',
            'baseline_hefi', 'modified_hefi', 'delta_hefi', 'improved_hefi',
            'baseline_heni_min', 'modified_heni_min', 'delta_heni_min', 'improved_heni',
            'baseline_fcs', 'modified_fcs', 'delta_fcs',
            'baseline_env', 'modified_env', 'delta_env', 'improved_env',
            'win_win_heni_env', 's4_baseline_hefi', 's4_baseline_heni', 's4_baseline_env_gw',
        ])
        for r in processed:
            b, m, d = r.get('baseline') or {}, r.get('modified') or {}, r.get('delta') or {}
            imp = r.get('improved') or {}
            w.writerow([
                r['day_id'], r['label'], r['stratum'], r.get('n_swaps_applied'),
                b.get('hefi'), m.get('hefi'), d.get('hefi'), imp.get('hefi'),
                b.get('heni_min'), m.get('heni_min'), d.get('heni_min'), imp.get('heni'),
                b.get('fcs'), m.get('fcs'), d.get('fcs'),
                b.get('environmental'), m.get('environmental'), d.get('environmental'), imp.get('environmental'),
                r.get('win_win_heni_env'),
                r.get('s4_lite_baseline_hefi'), r.get('s4_lite_baseline_heni'), r.get('s4_lite_baseline_env_gw'),
            ])

    ex_path = os.path.join(_OUT, 's4_overlay_exemplars.json')
    with open(ex_path, 'w', encoding='utf-8') as f:
        json.dump(exemplars, f, indent=2)

    backend_copy = os.path.join(os.path.dirname(__file__), '_smoke_substitution_s4_overlay_results.json')
    with open(backend_copy, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2)

    print(f'\nEligible: {len(eligible)}/{len(S4_LITE_PANEL)} days')
    print(f'Win-win (HENI+env): {win_wins}/{len(processed)}')
    print(f'HEFI improved: {hefi_up}/{len(processed)}')
    print(f'Wrote {csv_path}')
    print(f'Wrote {json_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
