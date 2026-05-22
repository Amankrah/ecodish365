"""Life Cycle Assessment for meal-level environmental impacts (ReCiPe 2016 v1.1 H).

Characterisation factors are sourced from:
- Huijbregts MAJ, et al. ReCiPe2016: a harmonised LCIA method at midpoint and endpoint
  level. Int J Life Cycle Assess. 2017;22(2):138-147. doi:10.1007/s11367-016-1246-y.
- RIVM Report 2016-0104a (October 2017). ReCiPe 2016 v1.1, Report I: Characterization.

Per-substance midpoint factors in `_initialize_characterization_factors`['midpoint']
are provided for reference and for forward-compatibility with a future per-substance
LCI (planned via AGRIBALYSE integration). They are NOT consumed by the current
pipeline: per-meal impact flow goes through `cnf_integrator.get_environmental_impact_factors(food_id)`,
which returns pre-aggregated per-100 g per-food-group impact category values.

Endpoint factors in `_initialize_characterization_factors`['endpoint'] ARE consumed
by `calculate_endpoint_impacts`. Page-cited provenance for each is in
`RECIPE_ENDPOINT_FACTOR_PROVENANCE` below.
"""

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from src.meal import Meal
from .cnf_integrator import get_cnf_integrator


def _matched_band_ratios_for_group(group_default_factors: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Recover {category: {low_ratio, high_ratio}} from a cnf_integrator
    factor block — used to apply the same uncertainty width to matcher-supplied
    centrals as to group-default centrals (instead of a flat +/-1.5x proxy).

    The group_default_factors dict already carries `_uncertainty_bands` with
    {low, central, high}; we recover the ratios as low/central and high/central.
    """
    bands = group_default_factors.get('_uncertainty_bands') or {}
    ratios: Dict[str, Dict[str, float]] = {}
    for cat, band in bands.items():
        c = band.get('central') or 0.0
        if c > 0:
            ratios[cat] = {
                'low_ratio':  band.get('low', c) / c,
                'high_ratio': band.get('high', c) / c,
            }
    return ratios

if TYPE_CHECKING:  # avoid circular / heavy import at module load
    from .lca_matcher import LCAMatcher  # noqa: F401


# ---------------------------------------------------------------------------
# ReCiPe 2016 v1.1 Hierarchist endpoint characterisation factors
# Source: RIVM Report 2016-0104a (October 2017), Table 1.5, p. 25
# All factors are for the Hierarchist (H) cultural perspective unless noted.
# ---------------------------------------------------------------------------
RECIPE_ENDPOINT_FACTOR_PROVENANCE: Dict[str, Dict[str, object]] = {
    # Human health pathways (yr / unit emission -> DALY)
    'climate_change_human':           {'value': 9.3e-7,  'unit': 'yr/kg CO2',     'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
    'ozone_depletion_human':          {'value': 5.3e-4,  'unit': 'yr/kg CFC-11',  'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
    'ionizing_radiation_human':       {'value': 8.5e-9,  'unit': 'yr/kBq Co-60',  'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
    'particulate_matter_human':       {'value': 6.3e-4,  'unit': 'yr/kg PM2.5',   'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
    'photochemical_ozone_human':      {'value': 9.1e-7,  'unit': 'yr/kg NOx',     'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
    'human_toxicity_cancer':          {'value': 3.3e-6,  'unit': 'yr/kg 1,4-DCB', 'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'confidence': 'low'},
    'human_toxicity_non_cancer':      {'value': 6.7e-9,  'unit': 'yr/kg 1,4-DCB', 'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'confidence': 'low'},
    'water_use_human':                {'value': 2.2e-6,  'unit': 'yr/m3 water',   'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},

    # Ecosystem quality pathways - terrestrial (species.yr / unit)
    'climate_change_ecosystem':                {'value': 2.8e-9,  'unit': 'species.yr/kg CO2',     'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'terrestrial'},
    'photochemical_ozone_ecosystem':           {'value': 1.3e-7,  'unit': 'species.yr/kg NOx',     'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'terrestrial'},
    'terrestrial_acidification_ecosystem':     {'value': 2.1e-7,  'unit': 'species.yr/kg SO2',     'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'terrestrial'},
    'terrestrial_ecotoxicity_ecosystem':       {'value': 5.4e-8,  'unit': 'species.yr/kg 1,4-DCB', 'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'terrestrial', 'confidence': 'low'},
    'water_use_ecosystem_terrestrial':         {'value': 1.4e-8,  'unit': 'species.yr/m3',         'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'terrestrial'},
    'land_use_ecosystem':                      {'value': 8.9e-9,  'unit': 'species/m2.yr crop',    'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'terrestrial'},

    # Ecosystem quality pathways - freshwater
    'climate_change_ecosystem_freshwater':     {'value': 7.7e-14, 'unit': 'species.yr/kg CO2',     'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'freshwater'},
    'freshwater_eutrophication_ecosystem':     {'value': 6.1e-7,  'unit': 'species.yr/kg P',       'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'freshwater'},
    'freshwater_ecotoxicity_ecosystem':        {'value': 7.0e-10, 'unit': 'species.yr/kg 1,4-DCB', 'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'freshwater', 'confidence': 'low'},
    'water_use_ecosystem_freshwater':          {'value': 6.0e-13, 'unit': 'species.yr/m3',         'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'freshwater'},

    # Ecosystem quality pathways - marine
    'marine_ecotoxicity_ecosystem':            {'value': 1.1e-10, 'unit': 'species.yr/kg 1,4-DCB', 'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'marine', 'confidence': 'low'},
    'marine_eutrophication_ecosystem':         {'value': 1.7e-9,  'unit': 'species.yr/kg N',       'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H', 'compartment': 'marine'},

    # Resource scarcity (USD2013 / unit).
    # Per-resource resolution required for fossils: footnote 3 to Table 1.5, p. 25.
    'mineral_scarcity':                {'value': 0.23, 'unit': 'USD2013/kg Cu',           'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
    'fossil_scarcity_crude_oil':       {'value': 0.46, 'unit': 'USD2013/kg crude oil',    'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
    'fossil_scarcity_hard_coal':       {'value': 0.03, 'unit': 'USD2013/kg hard coal',    'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
    'fossil_scarcity_natural_gas':     {'value': 0.30, 'unit': 'USD2013/Nm3 natural gas', 'source': 'RIVM 2016-0104a', 'table': '1.5', 'page': 25, 'perspective': 'H'},
}


# Normalisation factors (per person per year, European reference).
# The "published" set is from ReCiPe2016 v1.1 as released (Sleeswijk-family). The
# "proposed_2024_unsourced" set was previously labelled `# Updated European
# normalization factors (RIVM October 2024)` in the codebase; no corresponding
# RIVM artefact post-dating October 2017 was retrievable as of 2026-05-20.
# Manuscripts MUST NOT cite this set without verification. See
# `code_action_items.md` (CODE-3).
NORMALIZATION_FACTORS_RECIPE2016_PUBLISHED: Dict[str, float] = {
    'Human Health': 4.7e-2,    # DALY/person/year
    'Ecosystems':   3.5e-9,    # species.yr/person/year
    'Resources':    7.1e3,     # USD2013/person/year
}
NORMALIZATION_FACTORS_PROPOSED_2024_UNSOURCED: Dict[str, float] = {
    'Human Health': 4.63e-2,
    'Ecosystems':   3.41e-9,
    'Resources':    7.35e3,
}


# Per-midpoint-category confidence rating, derived from RIVM 2016-0104a §1.3
# (p. 20) and Huijbregts et al. 2017 §4 (pp. 144-145). The toxicity categories
# carry an explicit reliability caveat in the source documents; AGRIBALYSE
# (ADEME 2024) concurs ("encore peu robustes").
LCA_FACTOR_CONFIDENCE: Dict[str, Dict[str, str]] = {
    'Global warming':                          {'level': 'high',   'rationale': 'CO2/CH4/N2O GWPs from IPCC AR5; widely used.'},
    'Water consumption':                       {'level': 'high',   'rationale': 'Volumetric inventory; ReCiPe scarcity weighting documented.'},
    'Terrestrial acidification':               {'level': 'high',   'rationale': 'Global SO2/NOx/NH3 fate updated in ReCiPe 2016 (Roy et al. 2014).'},
    'Fine particulate matter formation':       {'level': 'high',   'rationale': 'Van Zelm et al. 2016, with H secondary aerosol inclusion.'},
    'Stratospheric ozone depletion':           {'level': 'medium', 'rationale': 'Semi-empirical ODPs; preliminary N2O ODP only.'},
    'Ionizing radiation':                      {'level': 'medium', 'rationale': 'DDREF differs by perspective; DALYs/incidence updated.'},
    'Ozone formation, Human health':           {'level': 'medium', 'rationale': 'Replaces European average; respiratory mortality included.'},
    'Ozone formation, Terrestrial ecosystems': {'level': 'medium', 'rationale': 'Damage to terrestrial ecosystems new in 2016.'},
    'Freshwater eutrophication':               {'level': 'medium', 'rationale': 'Country-specific factors recalculated in v1.1 (pop. 2015).'},
    'Marine eutrophication':                   {'level': 'medium', 'rationale': 'Endpoint added in v1.1 (Oct 2017 erratum).'},
    'Land use':                                {'level': 'medium', 'rationale': 'Local impact only; global extinction not captured.'},
    'Mineral resource scarcity':               {'level': 'medium', 'rationale': 'Surplus Ore Potential, future production undiscounted.'},
    'Fossil resource scarcity':                {'level': 'medium', 'rationale': 'No constant mid-to-endpoint factor; resolved per resource.'},
    'Human carcinogenic toxicity':             {'level': 'low',    'rationale': 'USES-LCA 2.0; flagged unreliable in RIVM 2017 §1.3.'},
    'Human non-carcinogenic toxicity':         {'level': 'low',    'rationale': 'USES-LCA 2.0; v1.1 corrected a model bug (Oct 2017).'},
    'Terrestrial ecotoxicity':                 {'level': 'low',    'rationale': 'Ecotox damage factor = 1; known sensitivity point.'},
    'Freshwater ecotoxicity':                  {'level': 'low',    'rationale': 'Ecotox damage factor = 1; known sensitivity point.'},
    'Marine ecotoxicity':                      {'level': 'low',    'rationale': 'Ecotox damage factor = 1; known sensitivity point.'},
}


class LifeCycleAssessment:
    """
    Life Cycle Assessment class using ReCiPe 2016 v1.1 (Hierarchist) methodology
    with midpoint and endpoint indicators.

    Endpoint characterisation factors are page-cited from RIVM 2016-0104a Table
    1.5 (p. 25); per-factor provenance is in `RECIPE_ENDPOINT_FACTOR_PROVENANCE`
    at module scope. Per-meal impact flow uses pre-aggregated per-food-group
    factors from `cnf_integrator`; the substance-level midpoint dict in
    `_initialize_characterization_factors` is documentation-only.
    """

    def __init__(self, meal: Meal, matcher: Optional["LCAMatcher"] = None):
        self.meal = meal
        self.logger = logging.getLogger(__name__)
        self.cnf_integrator = get_cnf_integrator()
        self.midpoint_impacts = {}
        # v1 uncertainty bands ('demote, don't perfect'). Parallel field;
        # each midpoint category maps to {'low': X, 'central': Y, 'high': Z}.
        # central matches `self.midpoint_impacts` (backward compat).
        self.midpoint_impacts_bands: Dict[str, Dict[str, float]] = {}
        self.endpoint_impacts = {}
        self.endpoint_impacts_bands: Dict[str, Optional[Dict[str, float]]] = {}
        self.characterization_factors = self._initialize_characterization_factors()

        # §3.5 LCA matcher (GROUP-D-RECONCILIATION). When None (default), the
        # existing group-default cnf_integrator path is used for every food.
        # When set, the matcher is consulted per food and its decision is
        # logged to `self.matcher_decisions` for API surfacing.
        self.matcher = matcher
        self.matcher_decisions: List[Dict[str, Any]] = []
        # Cache of per-food impact dicts keyed by food_id. Prevents the
        # matcher_decisions list from being duplicated when downstream
        # callers (e.g. `calculate_matcher_aware_sustainability_score`)
        # re-request the same food's impacts after `perform_lcia` has
        # already processed it.
        self._food_impacts_cache: Dict[int, Dict[str, Any]] = {}

        # Per-midpoint-category confidence — v1 scope trim filters to only the
        # categories actually consumed by `_calculate_midpoint_impacts`. The
        # module-level `LCA_FACTOR_CONFIDENCE` table is the source of truth for
        # the ratings, retained at full 18 categories for forward-compat with
        # TODO-CODE-LCA-2 restoration. `sanity_check` and `get_data_quality_report`
        # only ever iterate present categories, so trimming here cannot
        # silently mis-rate something that isn't being computed.
        consumed = {'Global warming', 'Land use', 'Water consumption'}
        self.factor_confidence = {
            'high':   [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'high' and k in consumed],
            'medium': [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'medium' and k in consumed],
            'low':    [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'low' and k in consumed],
        }

    def _initialize_characterization_factors(self) -> Dict[str, Dict[str, float]]:
        """
        Initialise ReCiPe 2016 v1.1 Hierarchist characterisation factors.

        The 'midpoint' sub-dict (per-substance GWP, acidification potentials, etc.)
        is provided for reference and for forward-compatibility with a future
        per-substance LCI. It is NOT consumed by the current pipeline; real impact
        routing goes through `cnf_integrator.get_environmental_impact_factors`,
        which returns pre-aggregated per-food-group, per-100-g impact-category
        values. See module docstring.

        The 'endpoint' sub-dict IS consumed by `calculate_endpoint_impacts`.
        Values are taken from RIVM 2016-0104a Table 1.5, p. 25 (Hierarchist).
        See module-level `RECIPE_ENDPOINT_FACTOR_PROVENANCE` for per-factor
        source, table, page and unit.
        """
        # Endpoint values are the canonical source-of-truth for the live pipeline;
        # extract them from the provenance dict so the two cannot drift apart.
        endpoint = {key: meta['value'] for key, meta in RECIPE_ENDPOINT_FACTOR_PROVENANCE.items()}

        return {
            'midpoint': {
                # ------------------------------------------------------------------
                # REFERENCE ONLY — not consumed by the current pipeline. See module
                # docstring. Values are Hierarchist, 100-yr time horizon, from
                # RIVM 2016-0104a Table 2.2 (pp. 29-34).
                # ------------------------------------------------------------------
                # Climate change (kg CO2-eq / kg emission)
                'co2': 1.0,
                'ch4_biogenic': 34.0,  # RIVM 2017 Table 2.2 p. 29 (H, 100-yr)
                'ch4_fossil':   36.0,  # RIVM 2017 Table 2.2 p. 29 (H, 100-yr)
                'n2o':         298.0,  # RIVM 2017 Table 2.2 p. 29 (H, 100-yr)

                # Terrestrial acidification (kg SO2-eq / kg emission) - Roy et al. 2014
                'so2': 1.0,
                'nox': 0.7,
                'nh3': 1.88,

                # Freshwater eutrophication (kg P-eq / kg emission) - Helmes et al. 2012
                'p_to_freshwater': 1.0,
                'p_to_soil': 0.4,

                # Marine eutrophication (kg N-eq / kg emission)
                'n_to_marine': 1.0,
                'nox_to_marine': 0.2,

                # Land use (m2.yr crop-eq / m2.yr) - De Baan et al. 2013; Curran et al. 2014
                'annual_crop': 1.0,
                'permanent_crop': 0.85,
                'pasture': 0.28,
                'forest': 0.62,

                # Water consumption (m3 water-eq / m3 consumed)
                'freshwater': 1.0,
            },
            'endpoint': endpoint,
        }

    def perform_lcia(self) -> Dict[str, float]:
        """
        Perform Life Cycle Impact Assessment using corrected ReCiPe 2016 v1.1 methodology.
        Calculates impacts based on food composition and quantities in the meal.
        """
        try:
            self.midpoint_impacts = self._calculate_midpoint_impacts()
            return self.midpoint_impacts
        except Exception as e:
            self.logger.error(f"Error performing LCIA: {str(e)}", exc_info=True)
            raise

    def _calculate_midpoint_impacts(self) -> Dict[str, float]:
        """
        Calculate midpoint impact categories using ReCiPe 2016 H factors.

        v1 SCOPE TRIMMED to the 3 categories the pipeline can defend per-food-group
        from published literature (`_smoke_validate_cnf_integrator.py` audit):
          - `Global warming`     : Poore & Nemecek 2018 Fig. 1 (kg CO2 eq / 100 g)
          - `Land use`           : Poore & Nemecek 2018 Fig. 1 (m2a crop eq / 100 g)
          - `Water consumption`  : Mekonnen & Hoekstra 2011/2012 blue-water-only (m3 / 100 g)

        The previously-shipped 15 additional categories (terrestrial acidification,
        the two eutrophications, both ozone-formation pathways, fine PM, ionising
        radiation, stratospheric ozone depletion, the toxicity pair, the three
        ecotoxicities, mineral + fossil resource scarcity) are NOT aggregated in
        v1: 3 of them are unit-incompatible with the available P&N grounding and
        12 have no per-food-group numerical literature target on any basis. Shipping
        them as conservative defaults presented false multidimensional rigor; honest
        narrow coverage beats invented breadth. They re-enter the consumed set when
        TODO-CODE-LCA-2 (licensed AGRIBALYSE-LCI re-scored under ReCiPe) lands;
        see `code_action_items.md` and the §7.5 limitation in the manuscript.

        EF climate sub-keys (`Global warming (fossil|biogenic|LUC)`) supplied by
        the matcher still ride through `food_impacts` for the per-meal audit block
        but are deliberately NOT folded into `midpoint_impacts` (EF identity
        total = sum(sub-cols) holds within 1% across all 2,425 v32 rows;
        summing both would double-count climate against
        `climate_change_human` / `climate_change_ecosystem` downstream).
        """
        total_impacts = {
            'Global warming': 0.0,     # kg CO2 eq
            'Land use': 0.0,           # m2a crop eq
            'Water consumption': 0.0,  # m3
        }
        # Parallel band aggregation. Each category accumulates
        # low / central / high sums independently. Meal-level "low" = sum of
        # per-food lows; this is a worst/best envelope under the simplifying
        # assumption that producer percentiles co-vary across foods within
        # a meal — true for the demote-don't-perfect framing, not for a real
        # 90% CI. Full PDF propagation requires Monte-Carlo (deferred).
        total_impacts_bands: Dict[str, Dict[str, float]] = {
            cat: {'low': 0.0, 'central': 0.0, 'high': 0.0} for cat in total_impacts
        }
        
        # Apply Canadian regional factors per-(food, category) per the
        # AGRIBALYSE-INGEST policy: suppress the multiplier for categories
        # whose value came from an Agribalyse match (Agribalyse already
        # encodes FR/EU geography), keep it for categories that fell back
        # to the cnf_integrator group default (those are global Poore &
        # Nemecek means that the Canadian layer is meant to localise).
        regional_factors = self._get_canadian_regional_factors()

        for food in self.meal.foods:
            food_impacts = self._get_food_environmental_impacts(food)
            category_sources = food_impacts.get("_category_sources", {}) if isinstance(food_impacts, dict) else {}
            food_bands = food_impacts.get("_bands", {}) if isinstance(food_impacts, dict) else {}
            food_source = food_impacts.get("_source", "fallback_low_confidence:group_default") if isinstance(food_impacts, dict) else "fallback_low_confidence:group_default"
            categories_with_match = 0
            categories_with_default = 0
            for impact_category in total_impacts:
                value = food_impacts.get(impact_category, 0.0)
                cat_source = category_sources.get(impact_category, "fallback_low_confidence:group_default")
                # Treat both the legacy "group_default" tag and the v1 explicit
                # "fallback_low_confidence:group_default" tag as the fallback path.
                is_fallback = cat_source.startswith("fallback_low_confidence") or cat_source == "group_default"
                regional_mult = regional_factors.get(impact_category, 1.0) if is_fallback else 1.0
                if is_fallback:
                    categories_with_default += 1
                else:
                    categories_with_match += 1
                total_impacts[impact_category] += value * regional_mult
                # Propagate bands with the same Canadian regional multiplier
                # applied to all three (low/central/high) for fallback foods.
                cat_band = food_bands.get(impact_category)
                if cat_band:
                    for side in ('low', 'central', 'high'):
                        total_impacts_bands[impact_category][side] += cat_band[side] * regional_mult
            # Tag the matching matcher_decisions audit entry with the
            # per-category accounting (only when matcher fired for this food).
            if self.matcher_decisions:
                last_decision = self.matcher_decisions[-1]
                if last_decision.get("food_id") == getattr(food, "food_id", None):
                    is_match = isinstance(food_source, str) and food_source.startswith("agribalyse_match:")
                    last_decision["regional_scaling_applied"] = not is_match
                    last_decision["categories_from_match"] = categories_with_match
                    last_decision["categories_from_group_default"] = categories_with_default

        # Apply functional unit normalization (per 100 kcal).
        total_calories = self.meal.calculate_total_calories()
        functional_unit_factor = 100 / total_calories if total_calories > 0 else 1
        for impact_category in total_impacts:
            total_impacts[impact_category] *= functional_unit_factor
            for side in ('low', 'central', 'high'):
                total_impacts_bands[impact_category][side] *= functional_unit_factor

        # Persist bands at meal level for downstream consumers / API surface.
        self.midpoint_impacts_bands = total_impacts_bands
        return total_impacts
    
    def _get_food_environmental_impacts(self, food) -> Dict[str, float]:
        """
        Get environmental impacts for a specific food item.

        Cached per `food.food_id` on `self._food_impacts_cache` to avoid
        duplicating `self.matcher_decisions` entries when re-requested by
        downstream callers (e.g. `calculate_matcher_aware_sustainability_score`).

        Resolution order (§3.5 / §3.7 AGRIBALYSE-INGEST):
          1. Always fetch the cnf_integrator group-default factors (Poore &
             Nemecek per-food-group means).
          2. If `self.matcher` is set AND returns a high-confidence match,
             OVERLAY the matched Agribalyse factors over the group defaults
             (the v32 catalog's `recipe2016_midpoints_per_100g` only carries
             the ~5 EF↔ReCiPe directly-equivalent categories; the other 13
             ReCiPe categories stay on group defaults per the dual-namespace
             plan).
          3. Record per-category source so `_calculate_midpoint_impacts` can
             apply Canadian regional scaling selectively — suppress on
             matched categories (Agribalyse already encodes FR/EU geography),
             keep on group-default categories (the Canadian layer is the
             whole point of `_get_canadian_regional_factors`).
        """
        # Memoised: same food_id returns the cached impacts dict without
        # re-firing the matcher (avoids appending to matcher_decisions twice).
        cache_key = getattr(food, 'food_id', None)
        if cache_key is not None and cache_key in self._food_impacts_cache:
            return self._food_impacts_cache[cache_key]

        quantity_factor = food.quantity / 100.0  # Convert to per 100g basis

        # Step 1: always start from the group-default Poore & Nemecek factors.
        try:
            group_default_factors = self.cnf_integrator.get_environmental_impact_factors(food.food_id)
        except Exception as e:  # noqa: BLE001 - log + degraded fallback
            self.logger.warning(f"Could not get impacts for food ID {food.food_id}: {e}")
            return {category: 0.0 for category in ['Global warming', 'Land use', 'Water consumption']}

        # Step 2: optionally overlay matcher-supplied factors.
        matched_factors: Dict[str, float] = {}
        food_source = "group_default"
        if self.matcher is not None:
            try:
                result = self.matcher.match(
                    food_id=food.food_id,
                    food_description=getattr(food, "food_name", "") or "",
                    food_group=getattr(food, "food_group", None),
                )
                self.matcher_decisions.append(result.to_audit())
                if result.matched and result.midpoint_factors:
                    matched_factors = {
                        k: v for k, v in result.midpoint_factors.items()
                        if isinstance(v, (int, float))
                    }
                    food_source = f"agribalyse_match:{result.ciqual_code}"
            except Exception as exc:  # noqa: BLE001 - log + fallback
                self.logger.warning(
                    "LCAMatcher raised for food_id=%s, falling back to group default: %s",
                    food.food_id, exc,
                )

        # Step 3: merge — matched factors WIN where keys overlap; group
        # defaults FILL the gaps. Track per-category source.
        food_impacts: Dict[str, float] = {}
        food_impacts_bands: Dict[str, Dict[str, float]] = {}
        category_sources: Dict[str, str] = {}
        group_default_bands = group_default_factors.get('_uncertainty_bands') or {}
        for category, factor in group_default_factors.items():
            if isinstance(category, str) and category.startswith('_'):
                continue
            if not isinstance(factor, (int, float)):
                continue
            food_impacts[category] = float(factor) * quantity_factor
            # v1 audit-trail labelling: group-mean fallback is the last-resort
            # tier and should NEVER be silently mixed with per-food matched
            # values. Tag it as `fallback_low_confidence:group_default` so any
            # consumer can see what's a measurement vs an extrapolation.
            category_sources[category] = "fallback_low_confidence:group_default"
            # v1 bands: only present for the 3 grounded categories
            # (Global warming, Land use, Water consumption).
            band = group_default_bands.get(category)
            if band:
                food_impacts_bands[category] = {
                    side: band[side] * quantity_factor
                    for side in ('low', 'central', 'high')
                }
        # Overlay matched factors. The v32 catalog may also introduce keys
        # that the cnf_integrator never returns (e.g. parallel climate
        # sub-columns like "Global warming (fossil)"); include them too.
        # Matcher-supplied factors are point estimates without published
        # uncertainty. The previous proxy was a flat +/-1.5x band; the
        # literature-validation smoke test (`_smoke_api_vs_literature.py`)
        # revealed that 1.5x is too narrow to honestly bracket the
        # documented 2-4x inter-method spread (P&N anchoring vs Stylianou
        # IMPACT World+). We now reuse the SAME group-default uncertainty
        # ratios on the matched central — this gives a width that reflects
        # within-product spread on the per-food central, rather than
        # pretending the matched value is uncertainty-free at ±50 %.
        group_band_ratios = (group_default_bands.get('_ratios')
                             or _matched_band_ratios_for_group(group_default_factors))
        for category, factor in matched_factors.items():
            if isinstance(category, str) and category.startswith('_'):
                continue
            scaled = float(factor) * quantity_factor
            food_impacts[category] = scaled
            category_sources[category] = food_source
            ratios = group_band_ratios.get(category, {'low_ratio': 0.5, 'high_ratio': 2.0})
            food_impacts_bands[category] = {
                'low':     scaled * ratios['low_ratio'],
                'central': scaled,
                'high':    scaled * ratios['high_ratio'],
            }

        # Underscore-prefixed keys are filtered by aggregation loops.
        food_impacts["_source"] = food_source
        food_impacts["_category_sources"] = category_sources
        food_impacts["_bands"] = food_impacts_bands
        if cache_key is not None:
            self._food_impacts_cache[cache_key] = food_impacts
        return food_impacts
    
    def _get_canadian_regional_factors(self) -> Dict[str, float]:
        """
        Get scientifically-validated Canadian regional correction factors for impact categories.
        These account for local conditions based on comprehensive research validation.
        
        Confidence levels: High (7 factors), Moderate (2 factors)
        Source: Canadian government data, energy statistics, environmental indicators
        """
        return {
            # HIGH CONFIDENCE - Excellent scientific justification
            'Global warming': 0.85,  # Canadian grid ~150 gCO2e/kWh vs global average (82% non-GHG sources)
            'Ionizing radiation': 1.15,  # 13-15% nuclear electricity + world's 2nd largest U producer
            'Land use': 0.78,  # 9.98M km² with only 6.5% agricultural use (abundant land resources)
            'Mineral resource scarcity': 1.25,  # $55.5B annual mining production, intensive extraction
            'Water consumption': 0.65,  # 103,899 m³/person/year renewable freshwater (using ~1% of supply)
            'Fine particulate matter formation': 0.88,  # Strong air quality regulations and monitoring
            'Fossil resource scarcity': 1.02,  # Oil sands extraction intensity documented
            
            # MODERATE CONFIDENCE - Good supporting evidence
            'Freshwater eutrophication': 1.08,  # Agricultural runoff in Great Lakes/Prairie regions
            'Marine eutrophication': 1.12,  # Coastal concerns documented but regionally variable
            
            # DEFAULT VALUES - Limited Canada-specific data
            'Stratospheric ozone depletion': 1.0,
            'Ozone formation, Human health': 0.92,  # Lower population density effects
            'Ozone formation, Terrestrial ecosystems': 0.92,
            'Terrestrial acidification': 0.95,  # Moderate due to mining activities
            'Terrestrial ecotoxicity': 0.93,  # Better regulatory framework
            'Freshwater ecotoxicity': 0.96,  # Some mining impacts
            'Marine ecotoxicity': 1.05,  # Fisheries-related impacts
            'Human carcinogenic toxicity': 0.91,  # Better healthcare system access
            'Human non-carcinogenic toxicity': 0.93,
        }

    def calculate_endpoint_impacts(self) -> Dict[str, float]:
        """
        Calculate endpoint impacts using ReCiPe 2016 v1.1 Hierarchist factors from
        RIVM 2016-0104a Table 1.5 (p. 25).

        Converts midpoint impacts to three areas of protection:
        - Human Health (DALY)
        - Ecosystems (species.yr) — aggregated terrestrial + freshwater + marine
        - Resources (USD2013) — fossils resolved per-resource (see CODE-7 / note below)

        v1 TRIMMED SCOPE (consistent with `_calculate_midpoint_impacts`):
        - Human Health is driven only by Global warming and Water consumption in v1
          (the other 6 HH-contributing midpoints are not consumed; missing keys
          default to 0 here, so the endpoint is mathematically intact but
          quantitatively a lower bound rather than a full ReCiPe HH endpoint).
        - Ecosystems is driven only by Global warming, Water consumption, and Land
          use — the other 7 ecosystem-contributing midpoints are not consumed.
        - Resources is identically 0 in v1 (both Fossil and Mineral resource
          scarcity are not consumed at midpoint; we set the field to None rather
          than 0 to make it obvious it is not estimable and should not enter
          single-score weighting). When TODO-CODE-LCA-2 lands the trimmed
          midpoints come back, the endpoint computation is unchanged.

        Caveats (pre-existing):
        - Toxicity endpoint factors carry an explicit low-confidence flag
          (RIVM 2017 §1.3 p. 20; Huijbregts 2017 §4 pp. 144-145).
        - Fossil resource scarcity has no constant midpoint-to-endpoint factor
          (RIVM 2017 footnote 3 to Table 1.5, p. 25); per-substance resolution
          requires an LCI upgrade.
        - Water-use endpoint (yr/m3 to HH; species.yr/m3 to ecosystems) is
          distinct from the *monetary* valuation of water in `monetization.py`.
        """
        if not self.midpoint_impacts:
            self.perform_lcia()

        try:
            ef = self.characterization_factors['endpoint']
            mid = self.midpoint_impacts

            self.endpoint_impacts = self._endpoint_from_midpoint_vector(mid, ef)
            # Bands: re-run the same endpoint math on low/central/high envelopes.
            self.endpoint_impacts_bands = self._endpoint_bands_from_midpoint_bands(
                self.midpoint_impacts_bands, ef
            )
            return self.endpoint_impacts

        except Exception as e:
            self.logger.error(f"Error calculating endpoint impacts: {str(e)}", exc_info=True)
            raise

    def _endpoint_from_midpoint_vector(
        self, mid: Dict[str, float], ef: Dict[str, float]
    ) -> Dict[str, Optional[float]]:
        """Pure function: midpoint vector + endpoint CFs -> {HH, Ecosystems, Resources}.

        Extracted so the same math can be reused for the central scalar and for
        the low/high band envelopes. Returns Resources=None when neither fossil
        nor mineral scarcity is present in the trimmed midpoint set (v1).
        """
        # Human Health (DALY) — keep all upstream contributors; missing keys
        # default to 0 in the trimmed-v1 case, so the result is mathematically
        # intact but quantitatively a lower bound on the full ReCiPe endpoint.
        human_health = (
            mid.get('Global warming', 0)                    * ef['climate_change_human'] +
            mid.get('Stratospheric ozone depletion', 0)     * ef['ozone_depletion_human'] +
            mid.get('Ionizing radiation', 0)                * ef['ionizing_radiation_human'] +
            mid.get('Fine particulate matter formation', 0) * ef['particulate_matter_human'] +
            mid.get('Ozone formation, Human health', 0)     * ef['photochemical_ozone_human'] +
            mid.get('Human carcinogenic toxicity', 0)       * ef['human_toxicity_cancer'] +
            mid.get('Human non-carcinogenic toxicity', 0)   * ef['human_toxicity_non_cancer'] +
            mid.get('Water consumption', 0)                 * ef['water_use_human']
        )
        ecosystems = (
            mid.get('Global warming', 0)                          * ef['climate_change_ecosystem'] +
            mid.get('Ozone formation, Terrestrial ecosystems', 0) * ef['photochemical_ozone_ecosystem'] +
            mid.get('Terrestrial acidification', 0)               * ef['terrestrial_acidification_ecosystem'] +
            mid.get('Terrestrial ecotoxicity', 0)                 * ef['terrestrial_ecotoxicity_ecosystem'] +
            mid.get('Water consumption', 0)                       * ef['water_use_ecosystem_terrestrial'] +
            mid.get('Land use', 0)                                * ef['land_use_ecosystem'] +
            mid.get('Global warming', 0)                          * ef['climate_change_ecosystem_freshwater'] +
            mid.get('Freshwater eutrophication', 0)               * ef['freshwater_eutrophication_ecosystem'] +
            mid.get('Freshwater ecotoxicity', 0)                  * ef['freshwater_ecotoxicity_ecosystem'] +
            mid.get('Water consumption', 0)                       * ef['water_use_ecosystem_freshwater'] +
            mid.get('Marine ecotoxicity', 0)                      * ef['marine_ecotoxicity_ecosystem'] +
            mid.get('Marine eutrophication', 0)                   * ef['marine_eutrophication_ecosystem']
        )
        has_resource_midpoints = (
            mid.get('Fossil resource scarcity') is not None or
            mid.get('Mineral resource scarcity') is not None
        )
        if has_resource_midpoints:
            resources: Optional[float] = (
                mid.get('Fossil resource scarcity', 0)  * ef['fossil_scarcity_crude_oil'] +
                mid.get('Mineral resource scarcity', 0) * ef['mineral_scarcity']
            )
        else:
            resources = None
        return {
            'Human Health': human_health,
            'Ecosystems':   ecosystems,
            'Resources':    resources,
        }

    def _endpoint_bands_from_midpoint_bands(
        self,
        midpoint_bands: Dict[str, Dict[str, float]],
        ef: Dict[str, float],
    ) -> Dict[str, Optional[Dict[str, float]]]:
        """Re-run endpoint math on low/central/high envelopes."""
        if not midpoint_bands:
            return {}
        endpoint_bands: Dict[str, Dict[str, float]] = {
            'Human Health': {}, 'Ecosystems': {}, 'Resources': {}
        }
        for side in ('low', 'central', 'high'):
            mid_side = {cat: bands[side] for cat, bands in midpoint_bands.items() if side in bands}
            ep = self._endpoint_from_midpoint_vector(mid_side, ef)
            for k, v in ep.items():
                if v is not None:
                    endpoint_bands[k][side] = v
        # Drop endpoint bands that have no sides (e.g. Resources in v1 trim).
        return {k: v for k, v in endpoint_bands.items() if v}

    def calculate_single_score(
        self,
        normalization_set: str = 'recipe2016_published',
        use_updated_normalization: Optional[bool] = None,
    ) -> float:
        """
        Calculate a single score by normalising and weighting the three endpoint
        damages.

        :param normalization_set: Which set of person-equivalent normalisation
            factors to apply. One of:
              - 'recipe2016_published' (default): published ReCiPe 2016 values.
              - 'proposed_2024_unsourced': a set previously labelled `RIVM
                October 2024` in the codebase, for which no RIVM artefact was
                retrievable as of 2026-05-20. RETAINED FOR ABLATION ONLY; MUST
                NOT be cited in publications. See code_action_items.md CODE-3.
        :param use_updated_normalization: Deprecated. True -> 'proposed_2024_unsourced',
            False -> 'recipe2016_published'. Will be removed in a future revision.
        """
        if not self.endpoint_impacts:
            self.calculate_endpoint_impacts()

        # Backwards-compatibility shim for the deprecated boolean flag.
        if use_updated_normalization is not None:
            self.logger.warning(
                "`use_updated_normalization` is deprecated; use `normalization_set` instead."
            )
            normalization_set = (
                'proposed_2024_unsourced' if use_updated_normalization else 'recipe2016_published'
            )

        if normalization_set == 'recipe2016_published':
            normalization_factors = NORMALIZATION_FACTORS_RECIPE2016_PUBLISHED
        elif normalization_set == 'proposed_2024_unsourced':
            normalization_factors = NORMALIZATION_FACTORS_PROPOSED_2024_UNSOURCED
        else:
            raise ValueError(
                f"Unknown normalization_set '{normalization_set}'. "
                "Expected 'recipe2016_published' or 'proposed_2024_unsourced'."
            )

        # Equal weighting across areas of protection (standard ReCiPe approach).
        # v1 trim: Resources may be None (when both fossil + mineral scarcity
        # are absent from the trimmed midpoint set); re-distribute its weight
        # to the remaining endpoints rather than coerce None to 0 (which would
        # silently bias the score toward 0 / under-estimate impact).
        weighting_factors = {'Human Health': 1 / 3, 'Ecosystems': 1 / 3, 'Resources': 1 / 3}
        present_endpoints = {k: v for k, v in self.endpoint_impacts.items() if v is not None}
        total_weight = sum(weighting_factors[k] for k in present_endpoints)
        single_score = 0.0
        for endpoint, impact in present_endpoints.items():
            normalized = impact / normalization_factors[endpoint]
            renormalised_weight = weighting_factors[endpoint] / total_weight
            single_score += normalized * renormalised_weight
        return single_score

    def get_impact_breakdown(self) -> Dict[str, Dict[str, float]]:
        """
        Get detailed breakdown of impacts by food item.
        """
        breakdown = {}

        for food in self.meal.foods:
            food_impacts = self._get_food_environmental_impacts(food)
            breakdown[f"{food.food_name} ({food.quantity}g)"] = food_impacts

        return breakdown

    def calculate_matcher_aware_sustainability_score(self) -> Dict[str, Any]:
        """Compute a meal-level sustainability score that uses the LCA's
        matcher-aware per-food impacts (Agribalyse overlay when matched,
        group default otherwise), instead of `Food.get_environmental_impact()`'s
        group-default-only path.

        Fixes the consistency defect where the LCA panel showed (matched)
        2.5 kg CO2/100g for canned beef stew while the sustainability score
        was computed against the (group-default) 0.25 kg/100g Mixed Dishes
        value — making the score artificially generous on every matched
        meat / dairy / fast-food entry.

        Returns the same shape as `Meal.get_sustainability_score()` plus a
        `methodology` block per food.
        """
        per_food_scores: List[Dict[str, Any]] = []
        weighted_sum = 0.0
        total_weight = 0.0
        total_quantity = sum(getattr(f, 'quantity', 0) for f in self.meal.foods) or 1.0

        for food in self.meal.foods:
            # Per-food impacts from the LCA matcher-aware merge (drops
            # underscore-prefixed metadata keys; impacts are already scaled
            # by quantity to the food's actual serving).
            food_impacts_raw = self._get_food_environmental_impacts(food)
            impacts = {
                k: v for k, v in food_impacts_raw.items()
                if not (isinstance(k, str) and k.startswith('_'))
                and isinstance(v, (int, float))
            }
            food_score = food.get_sustainability_score(impacts=impacts)
            food_score['food_id'] = getattr(food, 'food_id', None)
            food_score['food_name'] = getattr(food, 'food_name', None)
            food_score['quantity_g'] = getattr(food, 'quantity', None)
            food_score['source_tag'] = food_impacts_raw.get('_source', 'unknown')
            per_food_scores.append(food_score)

            weight = getattr(food, 'quantity', 0) / total_quantity
            weighted_sum += float(food_score.get('overall', 50)) * weight
            total_weight += weight

        overall = weighted_sum / total_weight if total_weight > 0 else 50.0
        return {
            'overall_sustainability_score': overall,
            'sustainability_rating': self._sustainability_rating(overall),
            'individual_food_scores': per_food_scores,
            'methodology_note': (
                'Per-category sustainability scores anchored on literature-published '
                'population-percentile zones (Stylianou et al. 2021 SI Table 11B for '
                'GW and Water; P&N 2018 panel medians for Land). Computed against '
                'LCA-matcher-aware per-food impacts, so matched foods reflect the '
                'Agribalyse overlay value rather than the cnf_integrator group default.'
            ),
        }

    @staticmethod
    def _sustainability_rating(score: float) -> str:
        if score >= 80: return 'Excellent'
        if score >= 65: return 'Good'
        if score >= 50: return 'Moderate'
        if score >= 35: return 'Poor'
        return 'Very Poor'

    def get_factor_confidence_by_category(self) -> Dict[str, Dict[str, str]]:
        """
        Return the per-midpoint-category confidence rating restricted to the
        categories actually present in `self.midpoint_impacts`. Used by the API
        layer to render a confidence chip per output category.
        """
        if not self.midpoint_impacts:
            return {}
        return {
            category: dict(LCA_FACTOR_CONFIDENCE[category])
            for category in self.midpoint_impacts
            if category in LCA_FACTOR_CONFIDENCE
        }

    def get_data_quality_report(self) -> Dict[str, object]:
        """
        Provide a data-quality and confidence report for the run.
        """
        quality_report = {
            'methodology_version': 'ReCiPe 2016 v1.1 Hierarchist',
            'sources': [
                'Huijbregts et al. 2017, doi:10.1007/s11367-016-1246-y',
                'RIVM 2016-0104a (October 2017), Table 1.5 p. 25',
            ],
            'confidence_summary': {
                'high_confidence':   len(self.factor_confidence['high']),
                'medium_confidence': len(self.factor_confidence['medium']),
                'low_confidence':    len(self.factor_confidence['low']),
            },
            'confidence_by_category': self.get_factor_confidence_by_category(),
            'endpoint_factor_provenance': RECIPE_ENDPOINT_FACTOR_PROVENANCE,
            'regional_adaptation': 'Canadian factors applied (see cnf_integrator regional_factors)',
            'known_issues': [
                'Toxicity factors carry an explicit low-confidence flag (RIVM 2017 §1.3 p. 20).',
                'Fossil resource scarcity endpoint approximated as crude-oil-equivalent; '
                'per-substance resolution requires LCI upgrade (RIVM 2017 footnote 3 to Table 1.5, p. 25).',
                'Land use endpoint captures local impact only; global extinction not modelled.',
                'Egalitarian climate factors omit climate-carbon feedbacks for non-CO2 GHGs (RIVM 2017 footnote 1, p. 28).',
            ],
            'recommendations': [
                'Use midpoint results for primary analysis; treat endpoint single-score as ranking aid.',
                'Exercise caution with toxicity-related impacts.',
                'Cross-validate with IMPACT World+ or PEF for critical applications.',
            ],
        }
        return quality_report

    def sanity_check(self) -> Dict[str, str]:
        """
        Perform sanity checks on calculated impacts with data-quality context.
        """
        warnings: Dict[str, str] = {}

        # Range checks on midpoint impacts (per 100 kcal functional unit).
        for impact, value in self.midpoint_impacts.items():
            if value < 0:
                warnings[impact] = f"Negative value: {value}"
            elif impact == 'Global warming' and value > 50:
                warnings[impact] = f"Unusually high carbon footprint: {value:.3f} kg CO2 eq"
            elif impact == 'Water consumption' and value > 10:
                warnings[impact] = f"Unusually high water consumption: {value:.3f} m3"
            elif impact == 'Land use' and value > 20:
                warnings[impact] = f"Unusually high land use: {value:.3f} m2a"

        # Flag low-confidence categories with non-trivial impact.
        for impact in self.factor_confidence['low']:
            if impact in self.midpoint_impacts and self.midpoint_impacts[impact] > 0.1:
                warnings[f"{impact}_confidence"] = (
                    f"Significant impact in low-confidence category: "
                    f"{self.midpoint_impacts[impact]:.3f}"
                )

        # Calorie-range sanity.
        total_calories = self.meal.calculate_total_calories()
        if total_calories < 50:
            warnings['meal_calories'] = f"Very low calorie meal: {total_calories} kcal"
        elif total_calories > 2000:
            warnings['meal_calories'] = f"Very high calorie meal: {total_calories} kcal"

        # Standing limitation: fossil resource scarcity approximation.
        if 'Fossil resource scarcity' in self.midpoint_impacts:
            warnings['fossil_scarcity_approximation'] = (
                "Fossil resource scarcity endpoint approximated as crude-oil-equivalent; "
                "per-substance resolution requires LCI upgrade (RIVM 2017 Table 1.5 footnote 3)."
            )

        # GWP reference (substance dict is documentation-only).
        gwp = self.characterization_factors['midpoint']
        warnings['gwp_reference'] = (
            f"GWP100 (H, RIVM 2017 Table 2.2 p. 29): CO2={gwp['co2']}, "
            f"CH4_biogenic={gwp['ch4_biogenic']}, CH4_fossil={gwp['ch4_fossil']}, "
            f"N2O={gwp['n2o']}. Substance-level factors are reference-only."
        )
        return warnings

    def __str__(self) -> str:
        return f"LifeCycleAssessment (ReCiPe 2016 v1.1 + Canadian adaptations) for {self.meal}"

    def __repr__(self) -> str:
        return self.__str__()