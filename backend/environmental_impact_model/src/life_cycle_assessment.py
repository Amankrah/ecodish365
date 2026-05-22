"""Life Cycle Assessment for meal-level environmental impacts.

Methodology-, perspective-, and country-agnostic LCIA pipeline. All factor data
flows from a `MethodologyFactorPack` (default: ReCiPe 2016 v1.1) loaded from
JSON packs that were produced by the ETL out of the official RIVM workbooks:

- `data/recipe2016_endpoint_factors.json`     — mid->endpoint CFs per I/H/E
- `data/recipe2016_normalization.json`        — World 2010 per-person norms
- `data/recipe2016_country_factors.json`      — per-country endpoint CFs for
                                                 spatially-explicit categories
- `data/recipe2016_factor_packs_meta.json`    — provenance (SHA-256s + extracted_at_utc)

Runtime configuration (all optional, defaults match prior behaviour except where
documented):

  LifeCycleAssessment(meal, *,
      methodology='recipe2016',
      perspective='H',                # 'I' (short-term) / 'H' (default) / 'E' (long-term)
      country=None,                   # ISO-3 (e.g. 'CAN', 'USA'); None = global mean
      consumer_perspective='global',  # 'global' (supply-chain) | 'national' (in-country)
      matcher=None,                   # optional Agribalyse matcher
  )

When `consumer_perspective='national'` and `country` is set, the country-specific
midpoint-to-endpoint CF is substituted for the world-average for those impact
pathways the workbook covers per-country (the three water-consumption pathways
in v1). All other pathways use the world-average. A per-category factor-source
audit dict is exposed on `self.endpoint_factor_sources` for API surfacing.

The v1 midpoint scope trim is unchanged: {Global warming, Land use, Water
consumption} are the three consumed midpoint categories. The 15 other ReCiPe
midpoints stay out of the consumed vector until TODO-CODE-LCA-2 lands.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING
from src.meal import Meal
from .cnf_integrator import get_cnf_integrator
from .methodology_factors import MethodologyFactorPack, get_methodology_pack


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


VALID_PERSPECTIVES = ('I', 'H', 'E')
VALID_CONSUMER_PERSPECTIVES = ('global', 'national')


class LifeCycleAssessment:
    """ReCiPe 2016 v1.1 LCIA (configurable methodology / perspective / country).

    All factor numbers are loaded from the methodology pack at construction
    time; the class itself holds no hard-coded LCA constants. See module
    docstring for the configuration surface.
    """

    def __init__(
        self,
        meal: Meal,
        matcher: Optional["LCAMatcher"] = None,
        *,
        methodology: str = 'recipe2016',
        perspective: str = 'H',
        country: Optional[str] = None,
        consumer_perspective: str = 'global',
    ):
        self.meal = meal
        self.logger = logging.getLogger(__name__)
        self.cnf_integrator = get_cnf_integrator()

        # Configuration validation
        if perspective not in VALID_PERSPECTIVES:
            raise ValueError(
                f"Invalid perspective {perspective!r}. Use one of {VALID_PERSPECTIVES}."
            )
        if consumer_perspective not in VALID_CONSUMER_PERSPECTIVES:
            raise ValueError(
                f"Invalid consumer_perspective {consumer_perspective!r}. "
                f"Use one of {VALID_CONSUMER_PERSPECTIVES}."
            )
        self.perspective = perspective
        self.consumer_perspective = consumer_perspective
        self.country = country  # None means world-average

        # Methodology pack (factor data)
        self.pack: MethodologyFactorPack = get_methodology_pack(methodology)
        if country is not None and not self.pack.supports_country(country):
            raise ValueError(
                f"Country {country!r} not present in {methodology} pack. "
                f"Use `pack.list_countries()` to enumerate; pass None for world-average."
            )

        # State
        self.midpoint_impacts: Dict[str, float] = {}
        self.midpoint_impacts_bands: Dict[str, Dict[str, float]] = {}
        self.endpoint_impacts: Dict[str, Optional[float]] = {}
        self.endpoint_impacts_bands: Dict[str, Optional[Dict[str, float]]] = {}
        # Per-pathway audit trail: 'world_average' or e.g. 'country_specific:CAN'
        self.endpoint_factor_sources: Dict[str, str] = {}

        # Optional LCA matcher (§3.5 GROUP-D-RECONCILIATION)
        self.matcher = matcher
        self.matcher_decisions: List[Dict[str, Any]] = []
        # Cache of per-food impact dicts keyed by food_id (avoids duplicating
        # matcher_decisions entries when called multiple times for the same food).
        self._food_impacts_cache: Dict[int, Dict[str, Any]] = {}

        # Per-midpoint-category confidence, restricted to consumed v1 categories.
        consumed = {'Global warming', 'Land use', 'Water consumption'}
        self.factor_confidence = {
            'high':   [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'high' and k in consumed],
            'medium': [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'medium' and k in consumed],
            'low':    [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'low' and k in consumed],
        }

    # ------------------------------------------------------------------
    # Factor resolver — substitutes country-specific endpoint CFs where
    # applicable, falls back to world-average otherwise. Records the source
    # of each factor in `self.endpoint_factor_sources`.
    # ------------------------------------------------------------------
    def _ef(self, pathway_key: str) -> float:
        """Resolve the midpoint-to-endpoint factor for one pathway, honouring
        the configured consumer_perspective / country / perspective."""
        world = self.pack.endpoint_factor(pathway_key, self.perspective)
        if self.consumer_perspective == 'national' and self.country:
            country_cf = self.pack.country_endpoint_cf(
                self.country, pathway_key, self.perspective
            )
            if country_cf is not None:
                self.endpoint_factor_sources[pathway_key] = f"country_specific:{self.country}"
                return country_cf
        # Either global perspective, or country has no specific CF for this pathway.
        self.endpoint_factor_sources[pathway_key] = "world_average"
        return float(world) if world is not None else 0.0

    # ------------------------------------------------------------------
    # LCIA driver
    # ------------------------------------------------------------------
    def perform_lcia(self) -> Dict[str, float]:
        """Calculate midpoint impacts based on meal composition + quantities."""
        try:
            self.midpoint_impacts = self._calculate_midpoint_impacts()
            return self.midpoint_impacts
        except Exception as e:
            self.logger.error(f"Error performing LCIA: {str(e)}", exc_info=True)
            raise

    def _calculate_midpoint_impacts(self) -> Dict[str, float]:
        """Aggregate v1 midpoint impacts {Global warming, Land use, Water consumption}
        across the meal's foods, normalised to per-100-kcal functional unit.

        v1 SCOPE TRIMMED. The 15 other ReCiPe midpoints are NOT aggregated:
        3 are unit-incompatible with P&N grounding, 12 have no per-food-group
        numerical literature target. See `_smoke_validate_cnf_integrator.py`
        and the §7.5 manuscript limitation.

        NO MIDPOINT REGIONAL SCALING is applied. The legacy
        `_get_canadian_regional_factors` multipliers (0.65 water, 0.78 land,
        etc.) were unsourced inventions and were removed when the country-aware
        endpoint CF path was introduced. Regional adaptation now applies at
        the endpoint conversion step (where the workbook authoritatively
        supports it for the spatially-explicit categories).
        """
        total_impacts = {
            'Global warming': 0.0,     # kg CO2 eq
            'Land use': 0.0,           # m2a crop eq
            'Water consumption': 0.0,  # m3
        }
        total_impacts_bands: Dict[str, Dict[str, float]] = {
            cat: {'low': 0.0, 'central': 0.0, 'high': 0.0} for cat in total_impacts
        }

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
                is_fallback = cat_source.startswith("fallback_low_confidence") or cat_source == "group_default"
                if is_fallback:
                    categories_with_default += 1
                else:
                    categories_with_match += 1
                total_impacts[impact_category] += value
                cat_band = food_bands.get(impact_category)
                if cat_band:
                    for side in ('low', 'central', 'high'):
                        total_impacts_bands[impact_category][side] += cat_band[side]
            # Annotate audit entry for the matched food, if any
            if self.matcher_decisions:
                last_decision = self.matcher_decisions[-1]
                if last_decision.get("food_id") == getattr(food, "food_id", None):
                    is_match = isinstance(food_source, str) and food_source.startswith("agribalyse_match:")
                    last_decision["regional_scaling_applied"] = False  # midpoint regional scaling retired
                    last_decision["categories_from_match"] = categories_with_match
                    last_decision["categories_from_group_default"] = categories_with_default

        # Functional unit normalization (per 100 kcal)
        total_calories = self.meal.calculate_total_calories()
        functional_unit_factor = 100 / total_calories if total_calories > 0 else 1
        for impact_category in total_impacts:
            total_impacts[impact_category] *= functional_unit_factor
            for side in ('low', 'central', 'high'):
                total_impacts_bands[impact_category][side] *= functional_unit_factor

        self.midpoint_impacts_bands = total_impacts_bands
        return total_impacts

    def _get_food_environmental_impacts(self, food) -> Dict[str, float]:
        """Per-food impacts resolved via cnf_integrator group defaults overlaid
        by matcher-supplied Agribalyse factors (when matched and enabled).
        Cached per food_id to prevent duplicate matcher_decisions entries.

        See `cnf_integrator.get_environmental_impact_factors` for the per-group
        factor block; see `lca_matcher.LCAMatcher.match` for the overlay path.
        """
        cache_key = getattr(food, 'food_id', None)
        if cache_key is not None and cache_key in self._food_impacts_cache:
            return self._food_impacts_cache[cache_key]

        quantity_factor = food.quantity / 100.0

        try:
            group_default_factors = self.cnf_integrator.get_environmental_impact_factors(food.food_id)
        except Exception as e:  # noqa: BLE001
            self.logger.warning(f"Could not get impacts for food ID {food.food_id}: {e}")
            return {category: 0.0 for category in ['Global warming', 'Land use', 'Water consumption']}

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
            except Exception as exc:  # noqa: BLE001
                self.logger.warning(
                    "LCAMatcher raised for food_id=%s, falling back to group default: %s",
                    food.food_id, exc,
                )

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
            category_sources[category] = "fallback_low_confidence:group_default"
            band = group_default_bands.get(category)
            if band:
                food_impacts_bands[category] = {
                    side: band[side] * quantity_factor
                    for side in ('low', 'central', 'high')
                }
        # Overlay matched factors (matcher wins where keys overlap)
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

        food_impacts["_source"] = food_source
        food_impacts["_category_sources"] = category_sources
        food_impacts["_bands"] = food_impacts_bands
        if cache_key is not None:
            self._food_impacts_cache[cache_key] = food_impacts
        return food_impacts

    # ------------------------------------------------------------------
    # Endpoint conversion
    # ------------------------------------------------------------------
    def calculate_endpoint_impacts(self) -> Dict[str, Optional[float]]:
        """Convert midpoints to {Human Health, Ecosystems, Resources} using the
        methodology pack's mid->endpoint factors under the configured perspective.

        When `consumer_perspective='national'` and `country` is set, country-
        specific endpoint CFs replace the world-average for those pathways the
        workbook supports per-country (v1: the three water-consumption pathways).
        See `self.endpoint_factor_sources` for the per-pathway audit trail.

        v1 trim: with only {Global warming, Land use, Water consumption} as
        consumed midpoints, Resources is None (no fossil/mineral midpoints).
        Resources re-enters the endpoint output once TODO-CODE-LCA-2 lands.
        """
        if not self.midpoint_impacts:
            self.perform_lcia()
        try:
            # Reset audit trail for this run
            self.endpoint_factor_sources = {}
            self.endpoint_impacts = self._endpoint_from_midpoint_vector(self.midpoint_impacts)
            self.endpoint_impacts_bands = self._endpoint_bands_from_midpoint_bands(
                self.midpoint_impacts_bands
            )
            return self.endpoint_impacts
        except Exception as e:
            self.logger.error(f"Error calculating endpoint impacts: {str(e)}", exc_info=True)
            raise

    def _endpoint_from_midpoint_vector(
        self, mid: Dict[str, float]
    ) -> Dict[str, Optional[float]]:
        """Apply midpoint→endpoint conversion factors to a midpoint vector.

        Uses `self._ef(pathway_key)` so country-specific CFs are substituted
        when configured. Resources returns None when neither fossil nor mineral
        scarcity is in the consumed midpoint set (v1 trim).
        """
        human_health = (
            mid.get('Global warming', 0)                    * self._ef('climate_change_human') +
            mid.get('Stratospheric ozone depletion', 0)     * self._ef('ozone_depletion_human') +
            mid.get('Ionizing radiation', 0)                * self._ef('ionizing_radiation_human') +
            mid.get('Fine particulate matter formation', 0) * self._ef('particulate_matter_human') +
            mid.get('Ozone formation, Human health', 0)     * self._ef('photochemical_ozone_human') +
            mid.get('Human carcinogenic toxicity', 0)       * self._ef('human_toxicity_cancer') +
            mid.get('Human non-carcinogenic toxicity', 0)   * self._ef('human_toxicity_non_cancer') +
            mid.get('Water consumption', 0)                 * self._ef('water_use_human')
        )
        ecosystems = (
            mid.get('Global warming', 0)                          * self._ef('climate_change_ecosystem') +
            mid.get('Ozone formation, Terrestrial ecosystems', 0) * self._ef('photochemical_ozone_ecosystem') +
            mid.get('Terrestrial acidification', 0)               * self._ef('terrestrial_acidification_ecosystem') +
            mid.get('Terrestrial ecotoxicity', 0)                 * self._ef('terrestrial_ecotoxicity_ecosystem') +
            mid.get('Water consumption', 0)                       * self._ef('water_use_ecosystem_terrestrial') +
            mid.get('Land use', 0)                                * self._ef('land_use_ecosystem') +
            mid.get('Global warming', 0)                          * self._ef('climate_change_ecosystem_freshwater') +
            mid.get('Freshwater eutrophication', 0)               * self._ef('freshwater_eutrophication_ecosystem') +
            mid.get('Freshwater ecotoxicity', 0)                  * self._ef('freshwater_ecotoxicity_ecosystem') +
            mid.get('Water consumption', 0)                       * self._ef('water_use_ecosystem_freshwater') +
            mid.get('Marine ecotoxicity', 0)                      * self._ef('marine_ecotoxicity_ecosystem') +
            mid.get('Marine eutrophication', 0)                   * self._ef('marine_eutrophication_ecosystem')
        )
        has_resource_midpoints = (
            mid.get('Fossil resource scarcity') is not None or
            mid.get('Mineral resource scarcity') is not None
        )
        if has_resource_midpoints:
            resources: Optional[float] = (
                mid.get('Fossil resource scarcity', 0)  * self._ef('fossil_scarcity_crude_oil') +
                mid.get('Mineral resource scarcity', 0) * self._ef('mineral_scarcity')
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
    ) -> Dict[str, Optional[Dict[str, float]]]:
        """Re-run endpoint math on low/central/high envelopes."""
        if not midpoint_bands:
            return {}
        endpoint_bands: Dict[str, Dict[str, float]] = {
            'Human Health': {}, 'Ecosystems': {}, 'Resources': {}
        }
        for side in ('low', 'central', 'high'):
            mid_side = {cat: bands[side] for cat, bands in midpoint_bands.items() if side in bands}
            ep = self._endpoint_from_midpoint_vector(mid_side)
            for k, v in ep.items():
                if v is not None:
                    endpoint_bands[k][side] = v
        return {k: v for k, v in endpoint_bands.items() if v}

    # ------------------------------------------------------------------
    # Normalisation + single score
    # ------------------------------------------------------------------
    def calculate_normalized_midpoints(self) -> Dict[str, Dict[str, float]]:
        """Per-category normalised midpoint contributions in person-year equivalents.

        Returns {category: {value, person_years}} where person_years is the
        midpoint impact divided by the World 2010 per-person-per-year norm
        for that category, expressed as a fraction of one global average
        citizen's annual midpoint footprint.
        """
        if not self.midpoint_impacts:
            self.perform_lcia()
        norms = self.pack.normalization('midpoint', self.perspective)
        normalized: Dict[str, Dict[str, float]] = {}
        for category, value in self.midpoint_impacts.items():
            norm = norms.get(category)
            if norm is None or norm == 0:
                continue
            normalized[category] = {
                'midpoint_value': value,
                'world_norm_per_person_yr': norm,
                'person_years_equivalent': value / norm,
            }
        return normalized

    def calculate_single_score(
        self,
        normalization_set: Optional[str] = None,
        use_updated_normalization: Optional[bool] = None,
    ) -> float:
        """Endpoint-level normalised + weighted single score.

        Normalisation pulls per-AoP World 2010 person/year scores from the
        methodology pack under the configured perspective. The legacy
        `normalization_set` / `use_updated_normalization` arguments are
        retained as no-ops with deprecation warnings — the pack-derived
        normalisation is the single source of truth.

        Resources may be None (v1 trim, no fossil/mineral midpoints); when so,
        weight is renormalised across present endpoints to avoid silently
        biasing the score toward zero.
        """
        if not self.endpoint_impacts:
            self.calculate_endpoint_impacts()

        if use_updated_normalization is not None:
            self.logger.warning(
                "`use_updated_normalization` is deprecated; normalisation now "
                "loads from the methodology pack at construction time."
            )
        if normalization_set is not None:
            self.logger.warning(
                "`normalization_set` is deprecated; normalisation now loads "
                "from the methodology pack at construction time."
            )

        normalization_factors = self.pack.normalization('aop', self.perspective)
        weighting_factors = {'Human Health': 1 / 3, 'Ecosystems': 1 / 3, 'Resources': 1 / 3}
        present_endpoints = {k: v for k, v in self.endpoint_impacts.items() if v is not None}
        total_weight = sum(weighting_factors[k] for k in present_endpoints)
        single_score = 0.0
        for endpoint, impact in present_endpoints.items():
            norm = normalization_factors.get(endpoint)
            if not norm:
                continue
            normalized = impact / norm
            renormalised_weight = weighting_factors[endpoint] / total_weight
            single_score += normalized * renormalised_weight
        return single_score

    def get_impact_breakdown(self) -> Dict[str, Dict[str, float]]:
        """Per-food breakdown of midpoint impacts."""
        breakdown = {}
        for food in self.meal.foods:
            food_impacts = self._get_food_environmental_impacts(food)
            breakdown[f"{food.food_name} ({food.quantity}g)"] = food_impacts
        return breakdown

    # ------------------------------------------------------------------
    # Sustainability score (matcher-aware path)
    # ------------------------------------------------------------------
    def calculate_matcher_aware_sustainability_score(self) -> Dict[str, Any]:
        """Meal-level sustainability score using matcher-aware per-food impacts."""
        per_food_scores: List[Dict[str, Any]] = []
        weighted_sum = 0.0
        total_weight = 0.0
        total_quantity = sum(getattr(f, 'quantity', 0) for f in self.meal.foods) or 1.0

        for food in self.meal.foods:
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

    # ------------------------------------------------------------------
    # Reporting / introspection
    # ------------------------------------------------------------------
    def get_factor_confidence_by_category(self) -> Dict[str, Dict[str, str]]:
        if not self.midpoint_impacts:
            return {}
        return {
            category: dict(LCA_FACTOR_CONFIDENCE[category])
            for category in self.midpoint_impacts
            if category in LCA_FACTOR_CONFIDENCE
        }

    def get_data_quality_report(self) -> Dict[str, object]:
        provenance = self.pack.methodology_provenance()
        return {
            'methodology_version': f"{provenance['methodology']} {provenance['methodology_version']}",
            'perspective': self.perspective,
            'country': self.country,
            'consumer_perspective': self.consumer_perspective,
            'methodology_provenance': provenance,
            'sources': [
                'Huijbregts et al. 2017, doi:10.1007/s11367-016-1246-y',
                'RIVM 2016-0104a (October 2017), ReCiPe 2016 v1.1 workbooks',
            ],
            'confidence_summary': {
                'high_confidence':   len(self.factor_confidence['high']),
                'medium_confidence': len(self.factor_confidence['medium']),
                'low_confidence':    len(self.factor_confidence['low']),
            },
            'confidence_by_category': self.get_factor_confidence_by_category(),
            'endpoint_factor_sources': dict(self.endpoint_factor_sources),
            'known_issues': [
                'Toxicity factors carry an explicit low-confidence flag (RIVM 2017 §1.3 p. 20).',
                'Fossil resource scarcity endpoint approximated as crude-oil-equivalent; '
                'per-substance resolution requires LCI upgrade.',
                'Land use endpoint captures local impact only; global extinction not modelled.',
                'Egalitarian climate factors omit climate-carbon feedbacks for non-CO2 GHGs.',
                'v1 midpoint scope trimmed to {Global warming, Land use, Water consumption}; '
                '15 other ReCiPe midpoints not consumed pending TODO-CODE-LCA-2.',
            ],
            'recommendations': [
                'Use midpoint results for primary analysis; treat endpoint single-score as ranking aid.',
                'Cross-validate with IMPACT World+ or PEF for critical applications.',
            ],
        }

    def sanity_check(self) -> Dict[str, str]:
        """Sanity checks on calculated impacts with data-quality context."""
        warnings: Dict[str, str] = {}
        for impact, value in self.midpoint_impacts.items():
            if value < 0:
                warnings[impact] = f"Negative value: {value}"
            elif impact == 'Global warming' and value > 50:
                warnings[impact] = f"Unusually high carbon footprint: {value:.3f} kg CO2 eq"
            elif impact == 'Water consumption' and value > 10:
                warnings[impact] = f"Unusually high water consumption: {value:.3f} m3"
            elif impact == 'Land use' and value > 20:
                warnings[impact] = f"Unusually high land use: {value:.3f} m2a"

        for impact in self.factor_confidence['low']:
            if impact in self.midpoint_impacts and self.midpoint_impacts[impact] > 0.1:
                warnings[f"{impact}_confidence"] = (
                    f"Significant impact in low-confidence category: "
                    f"{self.midpoint_impacts[impact]:.3f}"
                )

        total_calories = self.meal.calculate_total_calories()
        if total_calories < 50:
            warnings['meal_calories'] = f"Very low calorie meal: {total_calories} kcal"
        elif total_calories > 2000:
            warnings['meal_calories'] = f"Very high calorie meal: {total_calories} kcal"

        return warnings

    def __str__(self) -> str:
        bits = [self.pack.version_string(), f"perspective={self.perspective}"]
        if self.country:
            bits.append(f"country={self.country}/{self.consumer_perspective}")
        return f"LifeCycleAssessment ({', '.join(bits)}) for {self.meal}"

    def __repr__(self) -> str:
        return self.__str__()
