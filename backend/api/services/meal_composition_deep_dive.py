"""Composition deep-dive service.

Combines three perspectives on the same meal into a single response:

1. FPED food-group decomposition (cup-eq fruits, cup-eq vegetables by
   subgroup, oz-eq grains whole and refined, cup-eq dairy by subgroup,
   oz-eq protein foods by source, oils, solid fats, added sugars,
   alcoholic drinks) plus the MyPlate and Canada Food Guide gap reading.
2. NOVA processing-level breakdown: per-food classification (Monteiro
   2019 four-group framework) plus the meal-level distribution as
   mass-weighted percent at each NOVA level and energy-weighted percent
   at each NOVA level. The energy-weighted column is the canonical
   reporting unit in the ultra-processed-foods literature (Monteiro
   et al. 2018 Lancet Public Health).
3. Macronutrient distribution against the IOM AMDR bands: percent of
   energy from carbohydrate, protein, fat and alcohol, with a per-macro
   status flag (inside, above, below the AMDR range).

The service is deterministic (no LLM in the NOVA path; the classifier
runs with `enable_llm=False`), reuses every primitive that already lives
in the codebase, and returns a `MealCompositionDeepDive` dataclass that
the research deep-dive endpoint composes alongside the nutrient panel
and DRI rows.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Atwater conversion factors (kcal per gram).
#
# General Atwater (IOM 2005 Ch 6/8/9): 4-9-4 for protein/fat/carbohydrate,
# 7 for alcohol. Used as the fallback when per-food specific factors are
# unavailable.
_KCAL_PER_GRAM = {
    'protein':      4.0,
    'fat':          9.0,
    'carbohydrate': 4.0,
    'alcohol':      7.0,
}

# Specific Atwater factors per food category (FAO 2003, "Food energy —
# methods of analysis and conversion factors", Table 3.3). Keyed on the
# canonical food category from
# `api.services.food_group_category.canonical_category_for_food`. Materially
# different from the general 4-9-4 for legumes, fruits, vegetables, fish,
# and dairy — using the general factor over-states kcal by 5-15 percent
# for high-fibre / low-digestibility foods. The deep-dive endpoint now
# computes per-food Atwater kcal using these factors and falls back to
# the general factor only for canonical_category=='unknown' (truly
# uncategorised foods, expected to be < 1 percent post-FDC-MULTI-SOURCE).
_SPECIFIC_ATWATER_KCAL_PER_GRAM: Dict[str, Dict[str, float]] = {
    # category:        protein, fat,  carbohydrate
    'dairy':                  {'protein': 4.27, 'fat': 8.79, 'carbohydrate': 3.87},
    'dairy_egg_combined':     {'protein': 4.27, 'fat': 8.79, 'carbohydrate': 3.87},
    'eggs':                   {'protein': 4.36, 'fat': 9.02, 'carbohydrate': 3.68},
    'fats_oils':              {'protein': 4.27, 'fat': 8.84, 'carbohydrate': 3.87},  # mainly fat anyway
    'fruits':                 {'protein': 3.36, 'fat': 8.37, 'carbohydrate': 3.60},
    'vegetables':             {'protein': 2.44, 'fat': 8.37, 'carbohydrate': 3.57},
    'legumes':                {'protein': 3.47, 'fat': 8.37, 'carbohydrate': 4.07},
    'nuts_seeds':             {'protein': 3.47, 'fat': 8.37, 'carbohydrate': 4.07},
    'cereals_grains':         {'protein': 3.59, 'fat': 8.37, 'carbohydrate': 3.78},
    'breakfast_cereals':      {'protein': 3.87, 'fat': 8.37, 'carbohydrate': 4.12},
    'beef':                   {'protein': 4.27, 'fat': 9.02, 'carbohydrate': 3.87},
    'pork':                   {'protein': 4.27, 'fat': 9.02, 'carbohydrate': 3.87},
    'lamb_veal_game':         {'protein': 4.27, 'fat': 9.02, 'carbohydrate': 3.87},
    'poultry':                {'protein': 4.27, 'fat': 9.02, 'carbohydrate': 3.87},
    'fish':                   {'protein': 4.27, 'fat': 9.02, 'carbohydrate': 3.87},
    'sausages_luncheon':      {'protein': 4.27, 'fat': 9.02, 'carbohydrate': 3.87},
    'beverages':              {'protein': 4.00, 'fat': 9.00, 'carbohydrate': 4.00},  # heterogeneous; use general
    'alcoholic_beverages':    {'protein': 4.00, 'fat': 9.00, 'carbohydrate': 4.00},
    'sweets':                 {'protein': 3.87, 'fat': 8.37, 'carbohydrate': 3.87},
    'babyfoods':              {'protein': 4.00, 'fat': 9.00, 'carbohydrate': 4.00},
    'baked_products':         {'protein': 3.87, 'fat': 8.37, 'carbohydrate': 4.12},
    'fast_foods':             {'protein': 4.00, 'fat': 9.00, 'carbohydrate': 4.00},  # mixed; use general
    'mixed_dishes':           {'protein': 4.00, 'fat': 9.00, 'carbohydrate': 4.00},  # mixed; use general
    'snacks':                 {'protein': 3.87, 'fat': 8.37, 'carbohydrate': 4.12},
    'soups_sauces':           {'protein': 4.00, 'fat': 9.00, 'carbohydrate': 4.00},
    'spices_herbs':           {'protein': 4.00, 'fat': 9.00, 'carbohydrate': 4.00},
    'unknown':                {'protein': 4.00, 'fat': 9.00, 'carbohydrate': 4.00},  # explicit fallback
}


def _specific_atwater_for_food(food_id: int) -> Dict[str, float]:
    """Return per-food protein/fat/carbohydrate kcal-per-gram factors.

    Falls back to general 4-9-4 if the canonical-category bridge can't
    classify the food. Caller multiplies grams of each macro by the
    returned factor to get specific-Atwater kcal contribution per food.
    """
    try:
        from api.services.food_group_category import canonical_category_for_food
        cat = canonical_category_for_food(int(food_id))
    except Exception:  # noqa: BLE001
        cat = 'unknown'
    return _SPECIFIC_ATWATER_KCAL_PER_GRAM.get(cat, _SPECIFIC_ATWATER_KCAL_PER_GRAM['unknown'])


_food_meta_lock = threading.Lock()
_food_meta_cache: Optional[Dict[int, Dict[str, Any]]] = None


def _get_food_meta_index() -> Dict[int, Dict[str, Any]]:
    """Build `{FoodID: {description, food_group_id, food_group_name}}` once
    per process from the loaded CNF DataFrames. Used by the NOVA classifier
    call site so we do not pay the merge on every food.
    """
    global _food_meta_cache
    if _food_meta_cache is not None:
        return _food_meta_cache
    with _food_meta_lock:
        if _food_meta_cache is not None:
            return _food_meta_cache
        from api.cnf_cache import get_api_cnf_pipeline
        pipeline = get_api_cnf_pipeline()
        food_df = pipeline.food_name_df
        group_df = pipeline.food_group_df
        group_name = dict(
            zip(group_df['FoodGroupID'].astype('Int64'), group_df['FoodGroupName'])
        )
        idx: Dict[int, Dict[str, Any]] = {}
        for row in food_df.itertuples(index=False):
            try:
                fid = int(row.FoodID)
            except (TypeError, ValueError):
                continue
            try:
                gid = int(row.FoodGroupID)
            except (TypeError, ValueError):
                gid = 0
            idx[fid] = {
                'description': str(getattr(row, 'FoodDescription', '') or ''),
                'food_group_id': gid,
                'food_group_name': str(group_name.get(gid, '') or ''),
            }
        _food_meta_cache = idx
        return idx


@dataclass
class NovaPerFoodRow:
    food_id: int
    food_description: str
    food_group_name: str
    mass_g: float
    energy_kcal: float
    nova_level: int
    nova_confidence: float
    nova_rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            'food_id': self.food_id,
            'food_description': self.food_description,
            'food_group_name': self.food_group_name,
            'mass_g': round(self.mass_g, 2),
            'energy_kcal': round(self.energy_kcal, 2),
            'nova_level': self.nova_level,
            'nova_confidence': round(self.nova_confidence, 2),
            'nova_rationale': self.nova_rationale,
        }


@dataclass
class NovaShare:
    by_mass_pct: Dict[int, float]    # NOVA level -> percent of meal mass
    by_energy_pct: Dict[int, float]  # NOVA level -> percent of meal energy
    total_mass_g: float
    total_energy_kcal: float
    classified_food_count: int
    median_confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'by_mass_pct': {str(k): round(v, 2) for k, v in self.by_mass_pct.items()},
            'by_energy_pct': {str(k): round(v, 2) for k, v in self.by_energy_pct.items()},
            'total_mass_g': round(self.total_mass_g, 2),
            'total_energy_kcal': round(self.total_energy_kcal, 2),
            'classified_food_count': self.classified_food_count,
            'median_confidence': round(self.median_confidence, 2),
        }


@dataclass
class MacronutrientDistribution:
    energy_kcal_total: float
    grams_carbohydrate: float
    grams_protein: float
    grams_fat: float
    grams_alcohol: float
    kcal_from_carbohydrate: float
    kcal_from_protein: float
    kcal_from_fat: float
    kcal_from_alcohol: float
    pct_carbohydrate: float
    pct_protein: float
    pct_fat: float
    pct_alcohol: float
    amdr_status: Dict[str, str] = field(default_factory=dict)
    amdr_ranges: Dict[str, Dict[str, float]] = field(default_factory=dict)
    energy_reconciliation_note: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'energy_kcal_total': round(self.energy_kcal_total, 2),
            'grams': {
                'carbohydrate': round(self.grams_carbohydrate, 2),
                'protein': round(self.grams_protein, 2),
                'fat': round(self.grams_fat, 2),
                'alcohol': round(self.grams_alcohol, 2),
            },
            'kcal_from': {
                'carbohydrate': round(self.kcal_from_carbohydrate, 2),
                'protein': round(self.kcal_from_protein, 2),
                'fat': round(self.kcal_from_fat, 2),
                'alcohol': round(self.kcal_from_alcohol, 2),
            },
            'pct_energy': {
                'carbohydrate': round(self.pct_carbohydrate, 2),
                'protein': round(self.pct_protein, 2),
                'fat': round(self.pct_fat, 2),
                'alcohol': round(self.pct_alcohol, 2),
            },
            'amdr_status': self.amdr_status,
            'amdr_ranges': self.amdr_ranges,
            'energy_reconciliation_note': self.energy_reconciliation_note,
        }


@dataclass
class MealCompositionDeepDive:
    fped_aggregate: Dict[str, Any]
    nova_per_food: List[NovaPerFoodRow]
    nova_share: NovaShare
    macronutrient_distribution: MacronutrientDistribution
    coverage: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'fped_aggregate': self.fped_aggregate,
            'nova_per_food': [r.to_dict() for r in self.nova_per_food],
            'nova_share': self.nova_share.to_dict(),
            'macronutrient_distribution': self.macronutrient_distribution.to_dict(),
            'coverage': self.coverage,
        }


def _amdr_status_for(pct: float, low: float, high: float) -> str:
    if pct < low:
        return 'below_amdr'
    if pct > high:
        return 'above_amdr'
    return 'within_amdr'


def _build_macronutrient_distribution(
    nutrient_amounts: Dict[int, float],
    amdr_ranges: Dict[str, Dict[str, float]],
    foods: Optional[List[Dict]] = None,
) -> MacronutrientDistribution:
    """Compute the macronutrient distribution from the CNF nutrient panel.

    Uses CNF NutrientID 208 (kilocalories) as the energy denominator when
    present; falls back to the Atwater-summed total when 208 is missing
    or zero. The reconciliation note flags any divergence between the two.

    FDC-MULTI-SOURCE / academic-rigor (2026-06-26): when `foods` is supplied,
    Atwater kcal is computed per-food using FAO 2003 *specific* Atwater
    factors (table `_SPECIFIC_ATWATER_KCAL_PER_GRAM`, keyed on canonical
    food category). This typically reduces drift vs the CNF-listed kcal
    from 5-15 percent (general 4-9-4) to <3 percent because CNF itself
    uses specific Atwater internally for FoodID-208. When `foods` is None,
    falls back to the legacy meal-level general 4-9-4 Atwater path.
    """
    grams_pro = float(nutrient_amounts.get(203, 0.0) or 0.0)
    grams_fat = float(nutrient_amounts.get(204, 0.0) or 0.0)
    grams_cho = float(nutrient_amounts.get(205, 0.0) or 0.0)
    grams_alc = float(nutrient_amounts.get(221, 0.0) or 0.0)

    used_specific = False
    if foods:
        # Per-food specific Atwater. Walk each food once, fetching its
        # per-100g grams of pro/fat/cho via the shared aggregator (already
        # cached), scale by mass, multiply by the category-specific factor.
        try:
            from api.services.meal_nutrient_aggregator import aggregate_meal_nutrients
            kcal_pro_specific = 0.0
            kcal_fat_specific = 0.0
            kcal_cho_specific = 0.0
            for f in foods:
                fid = int(f.get('food_id'))
                mass = float(f.get('mass_g', 0.0) or 0.0)
                if mass <= 0:
                    continue
                sub = aggregate_meal_nutrients([{'food_id': fid, 'mass_g': mass}],
                                                nutrient_set=[203, 204, 205])
                fpro = sub.nutrient_totals.get(203)
                ffat = sub.nutrient_totals.get(204)
                fcho = sub.nutrient_totals.get(205)
                gpro = fpro.amount if fpro is not None else 0.0
                gfat = ffat.amount if ffat is not None else 0.0
                gcho = fcho.amount if fcho is not None else 0.0
                factors = _specific_atwater_for_food(fid)
                kcal_pro_specific += gpro * factors['protein']
                kcal_fat_specific += gfat * factors['fat']
                kcal_cho_specific += gcho * factors['carbohydrate']
            kcal_pro = kcal_pro_specific
            kcal_fat = kcal_fat_specific
            kcal_cho = kcal_cho_specific
            used_specific = True
        except Exception:  # noqa: BLE001 — defensive; fall back to general
            kcal_pro = grams_pro * _KCAL_PER_GRAM['protein']
            kcal_fat = grams_fat * _KCAL_PER_GRAM['fat']
            kcal_cho = grams_cho * _KCAL_PER_GRAM['carbohydrate']
    else:
        kcal_pro = grams_pro * _KCAL_PER_GRAM['protein']
        kcal_fat = grams_fat * _KCAL_PER_GRAM['fat']
        kcal_cho = grams_cho * _KCAL_PER_GRAM['carbohydrate']

    kcal_alc = grams_alc * _KCAL_PER_GRAM['alcohol']  # alcohol always 7 kcal/g
    kcal_atwater = kcal_pro + kcal_fat + kcal_cho + kcal_alc

    kcal_listed = float(nutrient_amounts.get(208, 0.0) or 0.0)

    atwater_label = 'specific Atwater (FAO 2003)' if used_specific else 'general Atwater (4-9-4)'
    if kcal_listed > 0:
        denom = kcal_listed
        if kcal_atwater > 0:
            drift_pct = abs(kcal_atwater - kcal_listed) / kcal_listed * 100.0
            note = (f'{atwater_label}-implied kcal {kcal_atwater:.0f} vs CNF-listed '
                    f'kcal {kcal_listed:.0f}; relative drift '
                    f'{drift_pct:.1f} percent. Percent-of-energy figures '
                    f'use the CNF-listed total.')
        else:
            note = f'{atwater_label}-implied kcal is zero; CNF-listed kcal used.'
    elif kcal_atwater > 0:
        denom = kcal_atwater
        note = f'CNF kcal not present; {atwater_label}-implied total used.'
    else:
        denom = 0.0
        note = 'No energy in meal; percent-of-energy figures not computable.'

    if denom > 0:
        pct_cho = kcal_cho / denom * 100.0
        pct_pro = kcal_pro / denom * 100.0
        pct_fat = kcal_fat / denom * 100.0
        pct_alc = kcal_alc / denom * 100.0
    else:
        pct_cho = pct_pro = pct_fat = pct_alc = 0.0

    cho_band = amdr_ranges.get('carbohydrate', {})
    pro_band = amdr_ranges.get('protein', {})
    fat_band = amdr_ranges.get('fat', {})
    amdr_status = {}
    if cho_band:
        amdr_status['carbohydrate'] = _amdr_status_for(
            pct_cho, cho_band['pct_kcal_min'], cho_band['pct_kcal_max'])
    if pro_band:
        amdr_status['protein'] = _amdr_status_for(
            pct_pro, pro_band['pct_kcal_min'], pro_band['pct_kcal_max'])
    if fat_band:
        amdr_status['fat'] = _amdr_status_for(
            pct_fat, fat_band['pct_kcal_min'], fat_band['pct_kcal_max'])

    return MacronutrientDistribution(
        energy_kcal_total=denom,
        grams_carbohydrate=grams_cho,
        grams_protein=grams_pro,
        grams_fat=grams_fat,
        grams_alcohol=grams_alc,
        kcal_from_carbohydrate=kcal_cho,
        kcal_from_protein=kcal_pro,
        kcal_from_fat=kcal_fat,
        kcal_from_alcohol=kcal_alc,
        pct_carbohydrate=pct_cho,
        pct_protein=pct_pro,
        pct_fat=pct_fat,
        pct_alcohol=pct_alc,
        amdr_status=amdr_status,
        amdr_ranges=amdr_ranges,
        energy_reconciliation_note=note,
    )


def _classify_food(food_id: int, food_meta: Dict[str, Any]) -> Tuple[int, float, str]:
    """Call the deterministic NOVA classifier for one food.

    Returns (level, confidence, rationale). Defensive against a classifier
    import failure: in that case we degrade to NOVA 1 with confidence 0
    so the deep-dive still ships rather than 500-ing.
    """
    try:
        from fcs_calculator.fcs.utils.nova_classifier import classify
        r = classify(
            food_id=food_id,
            food_description=food_meta.get('description', ''),
            food_group_name=food_meta.get('food_group_name', ''),
            food_group_id=food_meta.get('food_group_id', 0),
            chat_json_client=None,
            enable_llm=False,
        )
        return r.level, r.confidence, r.rationale
    except Exception as exc:  # noqa: BLE001
        logger.warning('NOVA classifier failed for food_id=%s: %s', food_id, exc)
        return 1, 0.0, 'classifier_error'


def composition_deep_dive(foods: List[Dict]) -> MealCompositionDeepDive:
    """Compose FPED + NOVA + macronutrient distribution into one response.

    `foods` is `[{food_id: int, mass_g: float}]`. Multiple entries for the
    same food_id are deduped via the shared aggregator.
    """
    from api.services.fped_aggregator import aggregate_fped
    from api.services.meal_nutrient_aggregator import aggregate_meal_nutrients
    from api.services import dri_compendium

    food_meta_idx = _get_food_meta_index()

    # Per-food deduplication on FoodID. Mirrors the recall-24h orchestrator's
    # behaviour: multiple entries for the same FoodID sum their masses, so
    # the NOVA classifier is called at most once per distinct food.
    mass_by_food: Dict[int, float] = {}
    for f in foods:
        try:
            fid = int(f.get('food_id'))
            m = float(f.get('mass_g', 0.0) or 0.0)
        except (TypeError, ValueError):
            continue
        if m <= 0:
            continue
        mass_by_food[fid] = mass_by_food.get(fid, 0.0) + m

    deduped_foods = [{'food_id': fid, 'mass_g': m} for fid, m in mass_by_food.items()]

    # Pull per-food energy (kcal) once, used by NOVA energy weighting and
    # by the macronutrient distribution at the meal-level.
    nutrient_agg = aggregate_meal_nutrients(deduped_foods)
    meal_nutrient_amounts = {nid: nv.amount for nid, nv in nutrient_agg.nutrient_totals.items()}

    # Per-food energy: walk each food independently through the aggregator
    # for the energy nutrient only; we already have the meal-level summed
    # value, but we need per-food kcal to drive the energy-weighted NOVA
    # share. Sub-millisecond at typical meal sizes.
    per_food_energy: Dict[int, float] = {}
    for fid, m in mass_by_food.items():
        sub = aggregate_meal_nutrients([{'food_id': fid, 'mass_g': m}], nutrient_set=[208])
        nv = sub.nutrient_totals.get(208)
        per_food_energy[fid] = nv.amount if nv is not None else 0.0

    # FPED aggregate. The aggregator accepts the deduped list directly.
    fped = aggregate_fped(
        deduped_foods,
        reference_kcal=meal_nutrient_amounts.get(208),
    ).to_dict()

    # NOVA per food.
    per_food: List[NovaPerFoodRow] = []
    classified = 0
    confidences: List[float] = []
    by_mass_g: Dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    by_energy_kcal: Dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    total_mass = 0.0
    total_energy = 0.0
    for fid, m in mass_by_food.items():
        meta = food_meta_idx.get(fid, {})
        level, conf, rationale = _classify_food(fid, meta)
        energy = per_food_energy.get(fid, 0.0)
        per_food.append(NovaPerFoodRow(
            food_id=fid,
            food_description=meta.get('description', ''),
            food_group_name=meta.get('food_group_name', ''),
            mass_g=m,
            energy_kcal=energy,
            nova_level=level,
            nova_confidence=conf,
            nova_rationale=rationale,
        ))
        if rationale != 'classifier_error':
            classified += 1
            confidences.append(conf)
        by_mass_g[level] = by_mass_g.get(level, 0.0) + m
        by_energy_kcal[level] = by_energy_kcal.get(level, 0.0) + energy
        total_mass += m
        total_energy += energy

    by_mass_pct = {
        lvl: ((by_mass_g.get(lvl, 0.0) / total_mass * 100.0) if total_mass > 0 else 0.0)
        for lvl in (1, 2, 3, 4)
    }
    by_energy_pct = {
        lvl: ((by_energy_kcal.get(lvl, 0.0) / total_energy * 100.0) if total_energy > 0 else 0.0)
        for lvl in (1, 2, 3, 4)
    }
    median_conf = (
        sorted(confidences)[len(confidences) // 2] if confidences else 0.0
    )
    nova_share = NovaShare(
        by_mass_pct=by_mass_pct,
        by_energy_pct=by_energy_pct,
        total_mass_g=total_mass,
        total_energy_kcal=total_energy,
        classified_food_count=classified,
        median_confidence=median_conf,
    )

    # Macronutrient distribution. Per-food list passed so we can compute
    # FAO 2003 specific Atwater kcal rather than general 4-9-4.
    amdr_ranges = dri_compendium.get_amdr_ranges()
    macros = _build_macronutrient_distribution(
        meal_nutrient_amounts, amdr_ranges, foods=deduped_foods,
    )

    coverage = {
        'n_foods_total': len(mass_by_food),
        'n_foods_with_fped': fped.get('coverage', {}).get('n_covered', 0),
        'n_foods_with_nova': classified,
        'mass_g_total': round(total_mass, 2),
        'mass_g_with_fped': fped.get('coverage', {}).get('covered_mass_g', 0.0),
        'energy_kcal_total': round(total_energy, 2),
    }

    return MealCompositionDeepDive(
        fped_aggregate=fped,
        nova_per_food=per_food,
        nova_share=nova_share,
        macronutrient_distribution=macros,
        coverage=coverage,
    )


def reset_for_test() -> None:
    global _food_meta_cache
    with _food_meta_lock:
        _food_meta_cache = None
