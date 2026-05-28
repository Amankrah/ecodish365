"""Aggregate a meal/day into USDA Food Pattern (FPED) component totals + guideline gaps.

Reusable core for the FPED food-group exposure layer: recall/scorecard researcher
surfaces, clinician gap summaries, and dietary-pattern drivers all call this.

Given a list of {food_id, mass_g}, it sums each food's per-100 g FPED profile
(scaled by mass/100) into daily component totals, reports coverage (foods with a
bridged profile vs unmatched foods, so partial coverage is never silent), and computes
gaps vs both MyPlate/DGA and Canada's-Food-Guide reference targets.
"""
from __future__ import annotations

import json
import math
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .fped_profile_loader import (
    FPED_COMPONENT_UNITS,
    get_fped_profile_for_food,
)

_TARGETS_PATH = Path(__file__).resolve().parent.parent / 'data' / 'food_pattern_targets.json'

_lock = threading.Lock()
_targets_cache: Optional[Dict] = None


def _load_targets() -> Dict:
    global _targets_cache
    if _targets_cache is not None:
        return _targets_cache
    with _lock:
        if _targets_cache is None:
            if _TARGETS_PATH.exists():
                _targets_cache = json.loads(_TARGETS_PATH.read_text(encoding='utf-8'))
            else:
                _targets_cache = {'targets': {}, '_provenance': {}}
    return _targets_cache


@dataclass
class FpedGap:
    component: str
    label: str
    unit: str
    intake: float
    direction: str          # 'aim_at_least' | 'keep_at_most'
    myplate_target: float
    cfg_target: float
    myplate_pct_of_target: Optional[float]   # intake / target * 100
    cfg_pct_of_target: Optional[float]
    myplate_status: str     # 'short' | 'met' | 'over'
    cfg_status: str

    def to_dict(self) -> Dict:
        return {
            'component': self.component, 'label': self.label, 'unit': self.unit,
            'intake': round(self.intake, 2), 'direction': self.direction,
            'myplate_target': self.myplate_target, 'cfg_target': self.cfg_target,
            'myplate_pct_of_target': (None if self.myplate_pct_of_target is None
                                      else round(self.myplate_pct_of_target, 0)),
            'cfg_pct_of_target': (None if self.cfg_pct_of_target is None
                                  else round(self.cfg_pct_of_target, 0)),
            'myplate_status': self.myplate_status, 'cfg_status': self.cfg_status,
        }


@dataclass
class FpedAggregate:
    component_totals: Dict[str, float]
    gaps: List[FpedGap]
    coverage: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'component_totals': {k: round(v, 3) for k, v in self.component_totals.items()},
            'component_units': FPED_COMPONENT_UNITS,
            'gaps': [g.to_dict() for g in self.gaps],
            'coverage': self.coverage,
        }


def _status(intake: float, target: float, direction: str) -> str:
    if target <= 0:
        # keep_at_most with target 0 (e.g. CFG refined grains): any intake is 'over'.
        return 'over' if (direction == 'keep_at_most' and intake > 0) else 'met'
    if direction == 'keep_at_most':
        return 'over' if intake > target else 'met'
    # aim_at_least: allow a 10 % grace band before calling it 'short'.
    return 'met' if intake >= 0.9 * target else 'short'


def aggregate_fped(foods: List[Dict]) -> FpedAggregate:
    """Aggregate [{food_id, mass_g}, ...] into FPED component totals + dual-guideline gaps.

    Foods without a bridged FPED profile (no US analog, or analog with no FPED row) are
    counted in `coverage` and excluded from the totals — never silently dropped.
    """
    totals: Dict[str, float] = {k: 0.0 for k in FPED_COMPONENT_UNITS}
    n_foods = len(foods)
    n_covered = n_no_profile = 0
    covered_mass = total_mass = 0.0

    for f in foods:
        fid = int(f.get('food_id'))
        mass = float(f.get('mass_g', 0.0) or 0.0)
        total_mass += mass
        # A profile exists for any food (CNF or WAFCT) that bridged to a US analog.
        # Foods without one (region-specific, no close analog) are counted as
        # uncovered, never silently dropped.
        prof = get_fped_profile_for_food(fid)
        if prof is None:
            n_no_profile += 1
            continue
        n_covered += 1
        covered_mass += mass
        scale = mass / 100.0
        for k, v in prof.items():
            totals[k] = totals.get(k, 0.0) + v * scale

    # Derived seafood total (high + low omega-3) for the seafood target.
    totals['protein_seafood_total_oz'] = (
        totals.get('protein_seafood_high_omega3_oz', 0.0)
        + totals.get('protein_seafood_low_omega3_oz', 0.0)
    )

    targets = _load_targets().get('targets', {})
    gaps: List[FpedGap] = []
    for comp, t in targets.items():
        intake = totals.get(comp, 0.0)
        mp, cfg = float(t['myplate_2000kcal']), float(t['cfg2019_approx'])
        direction = t['direction']
        gaps.append(FpedGap(
            component=comp, label=t.get('label', comp), unit=t.get('unit', ''),
            intake=intake, direction=direction,
            myplate_target=mp, cfg_target=cfg,
            myplate_pct_of_target=(round(intake / mp * 100, 0) if mp > 0 else None),
            cfg_pct_of_target=(round(intake / cfg * 100, 0) if cfg > 0 else None),
            myplate_status=_status(intake, mp, direction),
            cfg_status=_status(intake, cfg, direction),
        ))

    coverage = {
        'n_foods': n_foods,
        'n_covered': n_covered,
        'n_no_profile': n_no_profile,
        'covered_mass_g': round(covered_mass, 1),
        'total_mass_g': round(total_mass, 1),
        'coverage_pct_by_mass': (round(100 * covered_mass / total_mass, 1) if total_mass > 0 else 0.0),
    }
    return FpedAggregate(component_totals=totals, gaps=gaps, coverage=coverage)


# Base 37 components (exclude the derived seafood-total key) for vector comparisons.
_BASE_COMPONENTS = list(FPED_COMPONENT_UNITS.keys())


def decomposition_plausibility(
    composite_food_id: int,
    ingredients: List[Dict],
    cosine_floor: float = 0.70,
) -> Optional[Dict]:
    """FPED consistency QC for an LLM ingredient decomposition.

    When the decomposed composite is itself a catalog food with an FPED profile (its
    "FPED twin"), compare the mass-weighted FPED profile of the decomposed
    ingredients (normalised per 100 g of dish) to the twin's direct profile via
    cosine similarity + largest component divergence. A reproducible, non-black-box
    check that the LLM's ingredient split rolls up to a food-group profile
    consistent with the dish.

    Returns None when no FPED twin exists (free-text dishes, packaged products, or
    composites the bridge didn't cover) — i.e. when this QC cannot be applied.
    """
    direct = get_fped_profile_for_food(int(composite_food_id))
    if direct is None:
        return None
    total_mass = sum(float(i.get('mass_g', 0.0) or 0.0) for i in ingredients)
    if total_mass <= 0:
        return None

    agg = aggregate_fped(ingredients)
    recon = {k: agg.component_totals.get(k, 0.0) / total_mass * 100.0 for k in _BASE_COMPONENTS}

    du = [float(direct.get(k, 0.0)) for k in _BASE_COMPONENTS]
    rv = [recon.get(k, 0.0) for k in _BASE_COMPONENTS]
    dot = sum(a * b for a, b in zip(du, rv))
    na = math.sqrt(sum(a * a for a in du))
    nb = math.sqrt(sum(b * b for b in rv))
    cosine = (dot / (na * nb)) if na > 0 and nb > 0 else None

    divergences = []
    for k in _BASE_COMPONENTS:
        d = recon.get(k, 0.0) - float(direct.get(k, 0.0))
        if abs(d) >= 0.1:
            divergences.append({
                'component': k, 'unit': FPED_COMPONENT_UNITS.get(k, ''),
                'twin_per_100g': round(float(direct.get(k, 0.0)), 2),
                'reconstructed_per_100g': round(recon.get(k, 0.0), 2),
                'delta': round(d, 2),
            })
    divergences.sort(key=lambda x: -abs(x['delta']))

    return {
        'available': True,
        'composite_food_id': int(composite_food_id),
        'cosine': (round(cosine, 3) if cosine is not None else None),
        'plausible': bool(cosine is not None and cosine >= cosine_floor),
        'cosine_floor': cosine_floor,
        'top_divergences': divergences[:5],
        'note': (
            'FPED rollup of the decomposed ingredients vs the composite food\'s '
            'own FPED profile (per 100 g of dish). Higher cosine = the ingredient '
            'split is more food-group-consistent with the dish. Requires an FPED '
            'twin on the composite (bridged catalog food only).'
        ),
    }


# The everyday-recognisable food groups a swap actually moves, with friendly labels
# + display units. Same vocabulary as the dietary-pattern drivers, so the food-group
# story reads consistently across the FPED surfaces. (component -> (label, unit))
FPED_MAJOR_GROUPS: Dict[str, tuple] = {
    'veg_total_cup': ('vegetables', 'cup eq.'),
    'fruit_total_cup': ('fruit', 'cup eq.'),
    'grain_whole_oz': ('whole grains', 'oz eq.'),
    'grain_refined_oz': ('refined grains', 'oz eq.'),
    'protein_meat_oz': ('red meat', 'oz eq.'),
    'protein_cured_meat_oz': ('processed meat', 'oz eq.'),
    'protein_poultry_oz': ('poultry', 'oz eq.'),
    'protein_seafood_total_oz': ('seafood', 'oz eq.'),
    'protein_legumes_oz': ('legumes', 'oz eq.'),
    'protein_nuts_seeds_oz': ('nuts/seeds', 'oz eq.'),
    'dairy_total_cup': ('dairy', 'cup eq.'),
    'added_sugars_tsp': ('added sugars', 'tsp eq.'),
}


def fped_swap_delta(
    baseline_foods: List[Dict],
    replacement_foods: List[Dict],
    top_n: int = 4,
) -> Optional[Dict]:
    """Express an ingredient swap in food-group terms.

    Aggregates the baseline foods and the replacement foods separately, then
    reports the major USDA Food Pattern groups that change ("−2.0 oz red meat,
    +1.5 cup legumes") — the DASH/Mediterranean/CFG language a swap's ΔHEFI/ΔHENI
    doesn't convey. Handles single- and multi-swap (pass all originals vs all
    replacements). Returns None when no group changes meaningfully.

    `partial` is True when either side contained a food with no FPED profile
    (region-specific / unmatched), so the reported deltas understate the change.
    """
    base = aggregate_fped(baseline_foods)
    repl = aggregate_fped(replacement_foods)
    partial = base.coverage.get('n_no_profile', 0) > 0 or repl.coverage.get('n_no_profile', 0) > 0

    changed = []
    for comp, (label, unit) in FPED_MAJOR_GROUPS.items():
        b = base.component_totals.get(comp, 0.0)
        a = repl.component_totals.get(comp, 0.0)
        d = a - b
        if abs(d) < 0.05:
            continue
        changed.append({
            'component': comp, 'label': label, 'unit': unit,
            'before': round(b, 2), 'after': round(a, 2), 'delta': round(d, 2),
            'direction': 'more' if d > 0 else 'less',
        })
    if not changed:
        return None
    changed.sort(key=lambda x: -abs(x['delta']))
    return {
        'changed': changed[:top_n],
        'n_changed': len(changed),
        'partial': partial,
    }
