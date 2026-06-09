"""Shared meal nutrient aggregation primitive.

Takes a list of `[{food_id, mass_g}]`, returns the full per-nutrient meal panel
keyed by CNF NutrientID with unit, amount, and per-100 g of meal normalisation.
Tracks how many foods carried each nutrient versus how many were silent on it,
so a downstream caller can tell the difference between "the meal had 0 mg" and
"we have no data for some foods".

This is the canonical primitive the research deep-dive uses. The five existing
scorer-specific aggregators (HEFI / HENI / FCS / HSR / ReCiPe) each enforce a
score-specific projection (filtering, mapping, unit conversion) and are left
in place; this aggregator returns the untrimmed superset.

Reference. Walks `CNFDataPipeline.nutrients_by_food` (built once at pipeline
cold-load via `cnf_data_pipeline._build_nutrients_by_food_index`) so the
aggregation is sub-millisecond at typical meal sizes.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# Canonical research-relevant CNF NutrientIDs. Subset of the full 174 that
# every nutrition-epi paper actually reports. Callers asking for "all" get
# the full registry; callers asking for "research_canonical" get this set.
RESEARCH_CANONICAL_NUTRIENT_IDS: Tuple[int, ...] = (
    # macros and energy
    208,   # ENERGY (KILOCALORIES)
    268,   # ENERGY (KILOJOULES)
    203,   # PROTEIN
    204,   # FAT, TOTAL LIPIDS
    205,   # CARBOHYDRATE, TOTAL (BY DIFFERENCE)
    269,   # SUGARS, TOTAL
    291,   # FIBRE, TOTAL DIETARY
    255,   # WATER
    221,   # ALCOHOL
    # detailed fats
    606,   # FATTY ACIDS, SATURATED, TOTAL
    645,   # FATTY ACIDS, MONOUNSATURATED, TOTAL
    646,   # FATTY ACIDS, POLYUNSATURATED, TOTAL
    605,   # FATTY ACIDS, TRANS, TOTAL
    601,   # CHOLESTEROL
    # minerals
    301,   # CALCIUM
    303,   # IRON
    304,   # MAGNESIUM
    305,   # PHOSPHORUS
    306,   # POTASSIUM
    307,   # SODIUM
    309,   # ZINC
    312,   # COPPER
    315,   # MANGANESE
    317,   # SELENIUM
    # vitamins
    320,   # VITAMIN A, RAE
    323,   # VITAMIN E (ALPHA-TOCOPHEROL)
    328,   # VITAMIN D (D2 + D3)
    430,   # VITAMIN K
    401,   # VITAMIN C
    404,   # THIAMIN
    405,   # RIBOFLAVIN
    406,   # NIACIN (NE)
    410,   # PANTOTHENIC ACID
    415,   # VITAMIN B6
    418,   # VITAMIN B12
    421,   # CHOLINE, TOTAL
    435,   # FOLATE, DFE
)


# Lazy module-global registries built once per process from the shared CNF
# pipeline. Built on first call to `aggregate_meal_nutrients`; safe under
# concurrent first calls via the lock.
_registry_lock = threading.Lock()
_nutrient_id_by_name: Optional[Dict[str, int]] = None
_nutrient_meta: Optional[Dict[int, Dict[str, str]]] = None


def _build_registries() -> Tuple[Dict[str, int], Dict[int, Dict[str, str]]]:
    """Construct the NutrientName -> NutrientID reverse index and the
    NutrientID -> {name, unit, symbol, tagname, decimals} metadata table.

    Reads `CNFDataPipeline.nutrient_name_df` exactly once; subsequent calls
    return the cached registries.
    """
    global _nutrient_id_by_name, _nutrient_meta
    if _nutrient_id_by_name is not None and _nutrient_meta is not None:
        return _nutrient_id_by_name, _nutrient_meta
    with _registry_lock:
        if _nutrient_id_by_name is not None and _nutrient_meta is not None:
            return _nutrient_id_by_name, _nutrient_meta
        from api.cnf_cache import get_api_cnf_pipeline
        pipeline = get_api_cnf_pipeline()
        nn_df = pipeline.nutrient_name_df
        by_name: Dict[str, int] = {}
        meta: Dict[int, Dict[str, str]] = {}
        for row in nn_df.itertuples(index=False):
            try:
                nid = int(row.NutrientID)
            except (TypeError, ValueError):
                continue
            name = str(getattr(row, 'NutrientName', '') or '').strip()
            if not name:
                continue
            by_name[name] = nid
            meta[nid] = {
                'name': name,
                'unit': str(getattr(row, 'NutrientUnit', '') or '').strip(),
                'symbol': str(getattr(row, 'NutrientSymbol', '') or '').strip(),
                'tagname': str(getattr(row, 'Tagname', '') or '').strip(),
                'decimals': int(getattr(row, 'NutrientDecimals', 2) or 2),
            }
        _nutrient_id_by_name = by_name
        _nutrient_meta = meta
        return by_name, meta


@dataclass
class NutrientValue:
    """One row of the meal-level nutrient panel."""
    nutrient_id: int
    name: str
    unit: str
    symbol: str
    tagname: str
    amount: float                       # summed across foods, in `unit`
    amount_per_100g_meal: float         # normalised to 100 g of meal mass
    n_foods_with_value: int             # how many foods carried this nutrient
    n_foods_missing_value: int          # how many foods were silent
    coverage_mass_g: float              # mass of foods that carried this nutrient
    partially_imputed: bool             # true when not every food carried it

    def to_dict(self) -> Dict:
        d = max(0, min(6, self.decimals_safe()))
        return {
            'nutrient_id': self.nutrient_id,
            'name': self.name,
            'unit': self.unit,
            'symbol': self.symbol,
            'tagname': self.tagname,
            'amount': round(self.amount, d),
            'amount_per_100g_meal': round(self.amount_per_100g_meal, d),
            'n_foods_with_value': self.n_foods_with_value,
            'n_foods_missing_value': self.n_foods_missing_value,
            'coverage_mass_g': round(self.coverage_mass_g, 2),
            'partially_imputed': self.partially_imputed,
        }

    def decimals_safe(self) -> int:
        return 3


@dataclass
class MealNutrientCoverage:
    n_foods: int
    total_mass_g: float
    n_foods_in_cnf: int
    n_foods_unknown: int
    unknown_food_ids: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'n_foods': self.n_foods,
            'total_mass_g': round(self.total_mass_g, 2),
            'n_foods_in_cnf': self.n_foods_in_cnf,
            'n_foods_unknown': self.n_foods_unknown,
            'unknown_food_ids': self.unknown_food_ids,
        }


@dataclass
class MealNutrientAggregate:
    nutrient_totals: Dict[int, NutrientValue]
    coverage: MealNutrientCoverage
    food_id_map: Dict[int, str]            # FoodID -> FoodDescription
    food_source_map: Dict[int, str]        # FoodID -> 'cnf' | 'wafct' | 'unknown'
    food_mass_map: Dict[int, float]        # FoodID -> deduped mass_g

    def to_dict(self) -> Dict:
        return {
            'nutrient_totals': {
                str(nid): nv.to_dict() for nid, nv in sorted(self.nutrient_totals.items())
            },
            'coverage': self.coverage.to_dict(),
            'food_id_map': {str(k): v for k, v in self.food_id_map.items()},
            'food_source_map': {str(k): v for k, v in self.food_source_map.items()},
            'food_mass_map': {str(k): round(v, 2) for k, v in self.food_mass_map.items()},
        }

    def energy_kcal(self) -> Optional[float]:
        """Convenience accessor for total meal energy in kcal (NutrientID 208)."""
        nv = self.nutrient_totals.get(208)
        return nv.amount if nv is not None else None


def aggregate_meal_nutrients(
    foods: List[Dict],
    *,
    nutrient_set: Optional[List[int]] = None,
) -> MealNutrientAggregate:
    """Sum CNF nutrients across a meal.

    Parameters
    ----------
    foods : List[{food_id: int, mass_g: float}]
        The meal's food list. Multiple entries for the same food_id are
        deduped (masses summed) before aggregation, mirroring the 24h-recall
        orchestrator's behaviour.
    nutrient_set : Optional[List[int]]
        If provided, restrict the returned nutrient panel to these CNF
        NutrientIDs. If None, return every nutrient that appeared in any
        of the meal's foods.

    Returns
    -------
    MealNutrientAggregate
        Per-nutrient totals plus coverage metadata. Unknown food IDs (not
        in CNF or WAFCT) are tracked in `coverage.unknown_food_ids` and
        excluded from the totals, never silently dropped.

    Implementation note. This is the canonical primitive. It returns the
    untrimmed superset and never imputes silent zeros; nutrients that are
    absent from a food are reflected in `n_foods_missing_value` and the
    `partially_imputed` flag, which lets a downstream caller decide whether
    to skip or surface a partial-coverage nutrient.
    """
    from api.cnf_cache import get_api_cnf_pipeline
    by_name, meta = _build_registries()
    pipeline = get_api_cnf_pipeline()

    # Dedup multiple entries for the same FoodID by summing masses.
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

    n_foods_input = len(foods)
    total_mass = sum(mass_by_food.values())

    # Sets for filtering and per-nutrient food bookkeeping.
    nutrient_filter: Optional[set] = (
        set(int(n) for n in nutrient_set) if nutrient_set is not None else None
    )

    # Per-nutrient accumulators: nid -> (amount, n_foods_with, mass_with)
    totals: Dict[int, float] = {}
    n_with: Dict[int, int] = {}
    mass_with: Dict[int, float] = {}

    food_id_map: Dict[int, str] = {}
    food_source_map: Dict[int, str] = {}
    n_in_cnf = 0
    unknown_ids: List[int] = []

    # Resolve FoodID -> FoodDescription once via the loaded DataFrame.
    food_name_df = pipeline.food_name_df
    desc_lookup = dict(
        zip(food_name_df['FoodID'].astype('Int64'), food_name_df['FoodDescription'])
    )

    for fid, mass in mass_by_food.items():
        nutrients = pipeline.nutrients_for(fid)
        if not nutrients:
            unknown_ids.append(fid)
            food_source_map[fid] = 'unknown'
            food_id_map[fid] = str(desc_lookup.get(fid, '') or '')
            continue
        n_in_cnf += 1
        food_id_map[fid] = str(desc_lookup.get(fid, '') or '')
        src = pipeline.food_source(fid) or 'cnf'
        food_source_map[fid] = src

        scale = mass / 100.0
        for nutrient_name, value in nutrients.items():
            nid = by_name.get(nutrient_name)
            if nid is None:
                continue
            if nutrient_filter is not None and nid not in nutrient_filter:
                continue
            try:
                amt = float(value) * scale
            except (TypeError, ValueError):
                continue
            totals[nid] = totals.get(nid, 0.0) + amt
            n_with[nid] = n_with.get(nid, 0) + 1
            mass_with[nid] = mass_with.get(nid, 0.0) + mass

    # Build the NutrientValue rows.
    nutrient_totals: Dict[int, NutrientValue] = {}
    for nid, amount in totals.items():
        m = meta.get(nid, {})
        with_count = n_with.get(nid, 0)
        missing_count = max(0, n_in_cnf - with_count)
        nutrient_totals[nid] = NutrientValue(
            nutrient_id=nid,
            name=m.get('name', ''),
            unit=m.get('unit', ''),
            symbol=m.get('symbol', ''),
            tagname=m.get('tagname', ''),
            amount=amount,
            amount_per_100g_meal=(amount / total_mass * 100.0) if total_mass > 0 else 0.0,
            n_foods_with_value=with_count,
            n_foods_missing_value=missing_count,
            coverage_mass_g=mass_with.get(nid, 0.0),
            partially_imputed=(missing_count > 0),
        )

    coverage = MealNutrientCoverage(
        n_foods=n_foods_input,
        total_mass_g=total_mass,
        n_foods_in_cnf=n_in_cnf,
        n_foods_unknown=len(unknown_ids),
        unknown_food_ids=sorted(unknown_ids),
    )

    return MealNutrientAggregate(
        nutrient_totals=nutrient_totals,
        coverage=coverage,
        food_id_map=food_id_map,
        food_source_map=food_source_map,
        food_mass_map={fid: round(m, 4) for fid, m in mass_by_food.items()},
    )


def get_nutrient_meta(nutrient_id: int) -> Optional[Dict[str, str]]:
    """Return {name, unit, symbol, tagname, decimals} for a CNF NutrientID.

    Convenience accessor for downstream callers (the DRI loader, the
    contribution analyser, the deep-dive endpoint) that need nutrient
    display metadata without re-walking the pipeline.
    """
    _, meta = _build_registries()
    return meta.get(int(nutrient_id))


def all_nutrient_meta() -> Dict[int, Dict[str, str]]:
    """Return the full {nutrient_id: {name, unit, symbol, tagname, decimals}}
    table. Useful for the deep-dive endpoint's provenance block."""
    _, meta = _build_registries()
    return dict(meta)


def reset_for_test() -> None:
    """Tests that mutate the underlying CNF pipeline can drop the cached
    registries with this hook so a clean rebuild happens on next call."""
    global _nutrient_id_by_name, _nutrient_meta
    with _registry_lock:
        _nutrient_id_by_name = None
        _nutrient_meta = None
