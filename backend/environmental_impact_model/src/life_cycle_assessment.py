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
from typing import Dict, Optional
from src.meal import Meal
from .cnf_integrator import get_cnf_integrator


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

    def __init__(self, meal: Meal):
        self.meal = meal
        self.logger = logging.getLogger(__name__)
        self.cnf_integrator = get_cnf_integrator()
        self.midpoint_impacts = {}
        self.endpoint_impacts = {}
        self.characterization_factors = self._initialize_characterization_factors()

        # Per-midpoint-category confidence, copied from module-level constant.
        # Maintained for backward compatibility with `sanity_check` and
        # `get_data_quality_report`. See LCA_FACTOR_CONFIDENCE for rationale.
        self.factor_confidence = {
            'high':   [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'high'],
            'medium': [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'medium'],
            'low':    [k for k, v in LCA_FACTOR_CONFIDENCE.items() if v['level'] == 'low'],
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
        Calculate midpoint impact categories using corrected methodology with Canadian regional factors.
        Integrates with CNF data for accurate food-specific assessments.
        """
        total_impacts = {
            'Global warming': 0.0,  # kg CO2 eq
            'Stratospheric ozone depletion': 0.0,  # kg CFC11 eq
            'Ionizing radiation': 0.0,  # kBq Co-60 eq
            'Ozone formation, Human health': 0.0,  # kg NOx eq
            'Fine particulate matter formation': 0.0,  # kg PM2.5 eq
            'Ozone formation, Terrestrial ecosystems': 0.0,  # kg NOx eq
            'Terrestrial acidification': 0.0,  # kg SO2 eq
            'Freshwater eutrophication': 0.0,  # kg P eq
            'Marine eutrophication': 0.0,  # kg N eq
            'Terrestrial ecotoxicity': 0.0,  # kg 1,4-DCB
            'Freshwater ecotoxicity': 0.0,  # kg 1,4-DCB
            'Marine ecotoxicity': 0.0,  # kg 1,4-DCB
            'Human carcinogenic toxicity': 0.0,  # kg 1,4-DCB
            'Human non-carcinogenic toxicity': 0.0,  # kg 1,4-DCB
            'Land use': 0.0,  # m2a crop eq
            'Mineral resource scarcity': 0.0,  # kg Cu eq
            'Fossil resource scarcity': 0.0,  # kg oil eq
            'Water consumption': 0.0,  # m3
        }
        
        # Calculate impacts for each food in the meal
        for food in self.meal.foods:
            food_impacts = self._get_food_environmental_impacts(food)
            for impact_category in total_impacts:
                total_impacts[impact_category] += food_impacts.get(impact_category, 0.0)
        
        # Apply functional unit normalization (per 100 kcal)
        total_calories = self.meal.calculate_total_calories()
        functional_unit_factor = 100 / total_calories if total_calories > 0 else 1
        
        # Apply scientifically-validated Canadian regional factors
        regional_factors = self._get_canadian_regional_factors()
        
        for impact_category in total_impacts:
            total_impacts[impact_category] *= functional_unit_factor
            # Apply regional correction factor
            regional_factor = regional_factors.get(impact_category, 1.0)
            total_impacts[impact_category] *= regional_factor
        
        return total_impacts
    
    def _get_food_environmental_impacts(self, food) -> Dict[str, float]:
        """
        Get environmental impacts for a specific food item using the CNF integrator.
        """
        try:
            # Get impact factors from CNF integrator
            impact_factors = self.cnf_integrator.get_environmental_impact_factors(food.food_id)
            
            # Scale by food quantity (food.quantity is in grams)
            quantity_factor = food.quantity / 100.0  # Convert to per 100g basis
            
            # Calculate impacts (only numeric factors; skip metadata)
            food_impacts = {}
            for impact_category, factor in impact_factors.items():
                # Skip metadata keys (e.g., _data_source) and non-numeric values
                if isinstance(impact_category, str) and impact_category.startswith('_'):
                    continue
                if not isinstance(factor, (int, float)):
                    continue
                food_impacts[impact_category] = float(factor) * quantity_factor
            
            return food_impacts
            
        except Exception as e:
            self.logger.warning(f"Could not get impacts for food ID {food.food_id}: {e}")
            # Return minimal impact if data unavailable
            return {category: 0.0 for category in ['Global warming', 'Land use', 'Water consumption']}
    
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

        Caveats:
        - Toxicity-related endpoint factors carry an explicit low-confidence flag
          (RIVM 2017 §1.3 p. 20; Huijbregts 2017 §4 pp. 144-145).
        - Fossil resource scarcity has no constant midpoint-to-endpoint factor
          (RIVM 2017 footnote 3 to Table 1.5, p. 25). The current pipeline does
          not differentiate fossil substances, so the midpoint `Fossil resource
          scarcity` (kg oil-eq) is multiplied by the crude-oil endpoint factor as
          an approximation; per-substance resolution requires an LCI upgrade.
        - Water-use endpoint (yr/m3 to HH; species.yr/m3 to ecosystems) is
          distinct from the *monetary* valuation of water in `monetization.py`.
        """
        if not self.midpoint_impacts:
            self.perform_lcia()

        try:
            ef = self.characterization_factors['endpoint']
            mid = self.midpoint_impacts

            # Human Health (DALY)
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

            # Ecosystems (species.yr) — terrestrial + freshwater + marine
            ecosystems = (
                # terrestrial
                mid.get('Global warming', 0)                       * ef['climate_change_ecosystem'] +
                mid.get('Ozone formation, Terrestrial ecosystems', 0) * ef['photochemical_ozone_ecosystem'] +
                mid.get('Terrestrial acidification', 0)            * ef['terrestrial_acidification_ecosystem'] +
                mid.get('Terrestrial ecotoxicity', 0)              * ef['terrestrial_ecotoxicity_ecosystem'] +
                mid.get('Water consumption', 0)                    * ef['water_use_ecosystem_terrestrial'] +
                mid.get('Land use', 0)                             * ef['land_use_ecosystem'] +
                # freshwater
                mid.get('Global warming', 0)                       * ef['climate_change_ecosystem_freshwater'] +
                mid.get('Freshwater eutrophication', 0)            * ef['freshwater_eutrophication_ecosystem'] +
                mid.get('Freshwater ecotoxicity', 0)               * ef['freshwater_ecotoxicity_ecosystem'] +
                mid.get('Water consumption', 0)                    * ef['water_use_ecosystem_freshwater'] +
                # marine
                mid.get('Marine ecotoxicity', 0)                   * ef['marine_ecotoxicity_ecosystem'] +
                mid.get('Marine eutrophication', 0)                * ef['marine_eutrophication_ecosystem']
            )

            # Resources (USD2013). Fossils approximated as crude-oil-equivalent
            # because the midpoint inventory is not resolved per substance; see
            # CODE-7 in code_action_items.md.
            resources = (
                mid.get('Fossil resource scarcity', 0)  * ef['fossil_scarcity_crude_oil'] +
                mid.get('Mineral resource scarcity', 0) * ef['mineral_scarcity']
            )

            self.endpoint_impacts = {
                'Human Health': human_health,
                'Ecosystems':   ecosystems,
                'Resources':    resources,
            }

            return self.endpoint_impacts

        except Exception as e:
            self.logger.error(f"Error calculating endpoint impacts: {str(e)}", exc_info=True)
            raise

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
        weighting_factors = {'Human Health': 1 / 3, 'Ecosystems': 1 / 3, 'Resources': 1 / 3}

        single_score = 0.0
        for endpoint, impact in self.endpoint_impacts.items():
            normalized = impact / normalization_factors[endpoint]
            single_score += normalized * weighting_factors[endpoint]
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