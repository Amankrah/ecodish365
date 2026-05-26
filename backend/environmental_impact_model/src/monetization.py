from typing import Dict, List, Optional
import logging
import os
from datetime import datetime
from src.data_loader import DataLoader
from .cnf_integrator import get_cnf_integrator

# Per-country regional monetization adjustments. Canada is the only entry
# today (validated against ECCC + Canadian valuation literature). For any
# other ISO-3 code the multipliers collapse to identity ({}) and a clear
# log message is emitted explaining the Canadian calibration of the absolute
# CAD prices is unchanged. Add entries as authoritative per-country economic
# valuation studies become available.
# Per-country regional adjustment factors applied multiplicatively to the
# Canadian-calibrated absolute prices in `monetary_values`. Exercised when
# API callers pass `country='CAN'` to /api/environmental/* (see
# environmental_views.py:896 / 1255 / 1420). Default (no country) does NOT
# apply these multipliers — the absolute prices stand alone.
#
# Sources for the Canadian multipliers below:
# - 'Global warming' 1.15: Arctic amplification driver — ECCC NIR 2024
#   (literature_extractions.md §I51 lines 3838-3850) documents that Canada
#   warms at ~2x the global rate and contributes a disproportionate share of
#   per-capita food-system emissions; the 1.15 multiplier captures the
#   marginal Canadian regulatory premium on per-tonne CO2-eq damage relative
#   to the world-average ECCC SC-CO2 value, NOT a re-derivation of the
#   damage function. NIR §ES.2 (lines 3790-3804) further documents the
#   -60% electricity-sector decarbonisation 2005→2022 that REDUCES the
#   share of food-system emissions attributable to grid electricity, but
#   the climate-damage premium on the residual emissions is unchanged.
# - 'Water consumption' 0.7: Canada holds ~7% of global renewable freshwater
#   for 0.5% of population (per Statistics Canada Census of Environment); the
#   marginal water-scarcity cost is correspondingly lower than the world avg.
# - 'Land use' 0.8: Canada's agricultural land base is large relative to
#   conversion rates (NIR 2024 §ES.4 lines 3808-3821: agriculture stable at
#   56 Mt CO2-eq since 2005, no LULUCF acceleration outside the 2022 prairie
#   drought spike).
# CE Delft Environmental Prices Handbook (literature_extractions.md §H48)
# publishes its midpoint weighting factors in EUR 2015 per kg. To express in
# our reporting currency (2021 CAD, matching the ECCC SC-CO2 base year),
# we apply a two-step chain:
#   1. EUR 2015 → CAD 2015 via OECD PPP comparative price levels (~1.42)
#   2. CAD 2015 → CAD 2021 via Statistics Canada CPI All-items
#      (CANSIM 18-10-0005-01: 2015 = 126.6, 2021 = 141.6 → 1.118×)
# Combined: 1 EUR 2015 ≈ 1.587 CAD 2021, rounded to 1.59.
# Re-derive when refreshing to a later base year via Monetization.adjust_for_inflation().
EUR_2015_TO_CAD_2021: float = 1.42 * 1.118  # ≈ 1.587

_REGIONAL_MONETIZATION_BY_COUNTRY: Dict[str, Dict[str, float]] = {
    "CAN": {
        'Global warming': 1.15,  # See module-level comment above (NIR 2024 §ES.2)
        'Water consumption': 0.7,  # See module-level comment (~7% global freshwater)
        'Land use': 0.8,  # See module-level comment (NIR 2024 §ES.4)
        'Fossil resource scarcity': 1.1,  # Oil sands extraction intensity
    },
}


class Monetization:
    """
    Convert LCA midpoint impacts to monetary values (CAD).

    Base monetary factors (`monetary_values`) are CAD-calibrated using ECCC
    SC-GHG, CE Delft Environmental Prices Handbook 2024 (EUR -> CAD via PPP),
    and True Price 2024 inputs. Per-country regional adjustments
    (`regional_factors`) are applied on top.

    The `country` parameter (ISO-3, default `None` -> Canada) selects which
    country's regional adjustment block applies. For unrecognised countries
    the multipliers collapse to identity (1.0) and a log message is emitted —
    the absolute CAD prices are NOT re-priced (that requires per-country
    economic valuation studies we do not yet have).
    """

    def __init__(
        self,
        lca_results: Dict[str, float],
        data_loader: DataLoader,
        country: Optional[str] = None,
    ):
        self.lca_results = lca_results
        self.data_loader = data_loader
        self.cnf_integrator = get_cnf_integrator()
        self.logger = logging.getLogger(__name__)
        self.base_year = 2021  # Matches ECCC SC-GHG base year (2021 CAD)
        self.current_year = datetime.now().year
        # Normalize country: None or 'CAN' -> Canadian defaults; anything else
        # -> identity regional adjustments + informational log message.
        self.country = country or "CAN"

        # Monetary valuation factors (CAD per indicator unit).
        # 2026-05-25 first update: 'Global warming' value updated to the
        # ECCC 2023 SC-CO2 2026 central (C$275/t-CO2, 2 % Ramsey discount)
        # per literature_extractions.md §H47.
        # 2026-05-25 follow-up: nine non-GHG ReCiPe midpoints with clean
        # 1:1 unit mapping refreshed to CE Delft Environmental Prices
        # Handbook (literature_extractions.md §H48 Table 2 Hierarchist
        # weighting factors), converted via EUR_2015_TO_CAD_2021 ≈ 1.59.
        # Categories left at pre-page-citation v0 placeholders (with explicit
        # documentation in `monetary_value_sources`): Human cancer/non-cancer
        # toxicity and Ozone formation Human/Terrestrial — CE Delft publishes
        # one combined value where ReCiPe publishes two and we have no
        # principled allocation key; Ionizing radiation — unit mismatch
        # (CE Delft kBq U-235-eq vs ReCiPe kBq Co-60-eq); Fossil/Mineral
        # resource scarcity — CE Delft flags as "not fully quantified";
        # Water consumption — anchored to Canadian municipal tariff median,
        # different basis from CE Delft EU28.
        self.monetary_values = {
            # Climate (per tonne CO2-eq).
            # 2026 central estimate at the 2 % Near-term Ramsey discount rate
            # from ECCC (2023) "Guidance on the Social Cost of GHG Emissions",
            # Table 1 (C$2021/t-CO2). Replaces the pre-page-citation 221.0
            # value that predated the 2023 federal guidance.
            #
            # Methodological gotcha (per ECCC §4.2): we MUST NOT apply this
            # value to CH4 / N2O by re-multiplying through GWP100 — ECCC's
            # SC-CH4 (C$2,687/t) and SC-N2O (C$78,633/t) are damage-anchored
            # at the per-gas level and disagree with GWP × SC-CO2 by 1.5–3×.
            # Our LCA layer collapses CH4 + N2O into 'Global warming' via
            # AR5 GWPs at the midpoint (see life_cycle_assessment.py:70),
            # so SC-CH4 / SC-N2O entries would be dead code here. Adding
            # per-gas monetisation is deferred until the LCA layer surfaces
            # CH4 / N2O as separate mass flows (architecture change).
            'Global warming': 275.0,

            # Health impacts (per tonne emission unless noted)
            'Fine particulate matter formation': 39.2 * EUR_2015_TO_CAD_2021 * 1000,  # CE Delft 2018 Table 2 €39.2/kg PM10-eq
            'Human carcinogenic toxicity': 0.1029,        # per kg 1,4-DCB-eq — v0 placeholder; see source dict (CE Delft has no cancer/non-cancer split)
            'Human non-carcinogenic toxicity': 0.000808,  # per kg 1,4-DCB-eq — v0 placeholder; see source dict
            'Ionizing radiation': 0.000056,               # per kBq Co-60-eq — v0 placeholder; CE Delft uses kBq U-235-eq (unit mismatch)
            'Ozone formation, Human health': 8500.0,      # v0 placeholder; CE Delft POCP is single category (€1.15/kg NMVOC-eq); see source dict

            # Ecosystem impacts
            'Terrestrial acidification': 7.48 * EUR_2015_TO_CAD_2021 * 1000,   # CE Delft 2018 Table 2 €7.48/kg SO2-eq Hierarchist
            'Freshwater eutrophication': 1.86 * EUR_2015_TO_CAD_2021 * 1000,   # CE Delft 2018 Table 2 €1.86/kg P-eq
            'Marine eutrophication': 3.11 * EUR_2015_TO_CAD_2021 * 1000,       # CE Delft 2018 Table 2 €3.11/kg N
            'Terrestrial ecotoxicity': 8.69 * EUR_2015_TO_CAD_2021,            # per kg 1,4-DB-eq — CE Delft 2018 Table 2 €8.69/kg
            'Freshwater ecotoxicity':  0.0361 * EUR_2015_TO_CAD_2021,          # per kg 1,4-DB-eq — CE Delft 2018 Table 2 €0.0361/kg
            'Marine ecotoxicity':      0.00739 * EUR_2015_TO_CAD_2021,         # per kg 1,4-DB-eq — CE Delft 2018 Table 2 €0.00739/kg
            'Ozone formation, Terrestrial ecosystems': 2100.0,  # v0 placeholder; see Ozone formation Human health note

            # Atmospheric
            'Stratospheric ozone depletion': 123 * EUR_2015_TO_CAD_2021 * 1000,  # CE Delft 2018 Table 2 €123/kg CFC-11-eq Hierarchist

            # Resource depletion (per kg) — v0 placeholders; CE Delft 2018 §Table 3 flags Resource availability as "Not fully quantified" (lines 3669-3672)
            'Fossil resource scarcity': 0.2205,
            'Mineral resource scarcity': 0.0956,

            # Water and land
            'Water consumption': 0.0162,                                    # per m3 — Canadian municipal tariff median; NOT CE Delft (different basis)
            'Land use': 0.126 * EUR_2015_TO_CAD_2021,                       # per m2·yr crop-eq — CE Delft 2018 Table 2 €0.126/m²·yr Hierarchist
        }

        # Source attribution for each monetary value (CODE-4).
        # `status='pending_page_citation'` marks values whose source family is
        # known (e.g. CE Delft, True Price) but whose exact figure has not yet
        # been reconciled against the page-cited document. These will be
        # updated once literature group H PDFs are retrieved.
        self.monetary_value_sources: Dict[str, Dict[str, str]] = {
            'Global warming': {
                'source': 'ECCC 2023, Guidance on the Social Cost of GHG Emissions, Table 1 (2026 central, 2 % Near-term Ramsey discount rate)',
                'currency_year': '2021 CAD',
                'status': 'verified',
                'page_anchor': 'literature_extractions.md §H47 lines 3496-3509',
                'sensitivity_range_2026': '170 (2.5 % discount) – 275 (2.0 %, central) – 467 (1.5 %)',
                'methodological_note': 'CO2-eq aggregate only; CH4/N2O folded in via AR5 GWPs per ReCiPe midpoint. Per ECCC §4.2 this is a known underestimate but per-gas separation requires an LCA-layer architecture change.',
                'last_verified': '2026-05-25',
            },
            'Fine particulate matter formation': {
                'source': 'CE Delft 2018, Environmental Prices Handbook EU28 version, Table 2 (Summary p. 5), Hierarchist weighting factor €39.2/kg PM10-eq',
                'currency_year': '2021 CAD (converted from EUR 2015 via EUR_2015_TO_CAD_2021 ≈ 1.59)',
                'status': 'verified',
                'page_anchor': 'literature_extractions.md §H48 line 3633',
                'last_verified': '2026-05-25',
            },
            'Water consumption': {
                'source': 'Canadian municipal tariff median; True Price 2024',
                'currency_year': '2024 CAD',
                'status': 'pending_page_citation',
                'override_env': 'WATER_COST_PER_M3',
                'methodological_note': 'NOT refreshed from CE Delft H48 — that handbook does not list water consumption in Table 2; the existing municipal-tariff anchor uses a different basis (Canadian utility tariff median vs scarcity-weighted external cost). Refresh blocked on True Price 2024 PDF retrieval (wishlist H49).',
                'last_verified': '2026-05-25',
            },
            'Land use': {
                'source': 'CE Delft 2018, Environmental Prices Handbook EU28 version, Table 2 (Summary p. 5), Hierarchist weighting factor €0.126/m²·yr',
                'currency_year': '2021 CAD (converted from EUR 2015 via EUR_2015_TO_CAD_2021 ≈ 1.59)',
                'status': 'verified',
                'page_anchor': 'literature_extractions.md §H48 line 3641',
                'methodological_note': 'Replaces the True Price 2024 Canadian farmland-rental placeholder. ReCiPe land use unit (m²·yr crop-eq) matches CE Delft directly.',
                'last_verified': '2026-05-25',
            },
            # CE Delft Table 2 (H48 §lines 3623-3644) Hierarchist weighting
            # factors — verified, page-anchored entries for the categories
            # with clean 1:1 unit mapping to ReCiPe 2016 v1.1 H midpoints.
            **{
                category_meta['name']: {
                    'source': f'CE Delft 2018, Environmental Prices Handbook EU28 version, Table 2 (Summary p. 5), Hierarchist weighting factor {category_meta["price"]}',
                    'currency_year': '2021 CAD (converted from EUR 2015 via EUR_2015_TO_CAD_2021 ≈ 1.59)',
                    'status': 'verified',
                    'page_anchor': f'literature_extractions.md §H48 line {category_meta["line"]}',
                    'last_verified': '2026-05-25',
                }
                for category_meta in [
                    {'name': 'Terrestrial acidification',         'price': '€7.48/kg SO2-eq',      'line': 3635},
                    {'name': 'Freshwater eutrophication',         'price': '€1.86/kg P-eq',        'line': 3636},
                    {'name': 'Marine eutrophication',             'price': '€3.11/kg N',           'line': 3637},
                    {'name': 'Terrestrial ecotoxicity',           'price': '€8.69/kg 1,4-DB-eq',   'line': 3638},
                    {'name': 'Freshwater ecotoxicity',            'price': '€0.0361/kg 1,4-DB-eq', 'line': 3639},
                    {'name': 'Marine ecotoxicity',                'price': '€0.00739/kg 1,4-DB-eq','line': 3640},
                    {'name': 'Stratospheric ozone depletion',     'price': '€123/kg CFC-11-eq',    'line': 3630},
                ]
            },
            # Categories left at v0 placeholder values — CE Delft mapping
            # is blocked on a real unit/scope mismatch documented in each
            # entry below. These will be revisited when either a principled
            # allocation key emerges (toxicity split) or the LCA layer is
            # extended (Ionizing radiation Co-60 conversion).
            'Human carcinogenic toxicity': {
                'source': 'v0 placeholder (no published source)',
                'currency_year': '2021 CAD (assumed)',
                'status': 'mapping_blocked',
                'methodological_note': 'CE Delft H48 publishes ONE combined Human toxicity weighting factor (€0.0894/kg 1,4-DB-eq, line 3631); ReCiPe 2016 splits into cancer + non-cancer with no allocation key in the source documents. Sticking with v0 placeholder until a defensible split is published. CE Delft combined would yield C$0.142/kg if applied to either field — overcounts by 2× if applied to both.',
                'last_verified': '2026-05-25',
            },
            'Human non-carcinogenic toxicity': {
                'source': 'v0 placeholder (no published source)',
                'currency_year': '2021 CAD (assumed)',
                'status': 'mapping_blocked',
                'methodological_note': 'See Human carcinogenic toxicity entry above — same CE Delft no-split issue.',
                'last_verified': '2026-05-25',
            },
            'Ionizing radiation': {
                'source': 'v0 placeholder (no published source)',
                'currency_year': '2021 CAD (assumed)',
                'status': 'mapping_blocked',
                'methodological_note': 'Unit mismatch: CE Delft H48 line 3634 publishes €0.0461/kBq U-235-eq; ReCiPe 2016 uses kBq Co-60-eq. The two are not directly substitutable without a radionuclide-specific characterisation-factor remapping (out of v1 scope).',
                'last_verified': '2026-05-25',
            },
            'Ozone formation, Human health': {
                'source': 'v0 placeholder (no published source)',
                'currency_year': '2021 CAD (assumed)',
                'status': 'mapping_blocked',
                'methodological_note': 'CE Delft H48 line 3632 publishes ONE combined POCP weighting factor (€1.15/kg NMVOC-eq); ReCiPe 2016 splits photochemical ozone formation into Human health and Terrestrial ecosystems endpoints with no allocation key in the source documents. CE Delft combined would yield C$1828/t if 50/50 split — significantly below current placeholder (8500). Refresh deferred until allocation key established.',
                'last_verified': '2026-05-25',
            },
            'Ozone formation, Terrestrial ecosystems': {
                'source': 'v0 placeholder (no published source)',
                'currency_year': '2021 CAD (assumed)',
                'status': 'mapping_blocked',
                'methodological_note': 'See Ozone formation, Human health entry above — same CE Delft no-split issue.',
                'last_verified': '2026-05-25',
            },
            'Fossil resource scarcity': {
                'source': 'v0 placeholder (no published source)',
                'currency_year': '2021 CAD (assumed)',
                'status': 'not_in_source',
                'methodological_note': 'CE Delft H48 Table 3 line 3671 explicitly flags Resource availability as "Not fully quantified". No defensible refresh available from this source.',
                'last_verified': '2026-05-25',
            },
            'Mineral resource scarcity': {
                'source': 'v0 placeholder (no published source)',
                'currency_year': '2021 CAD (assumed)',
                'status': 'not_in_source',
                'methodological_note': 'See Fossil resource scarcity entry above — same CE Delft scope gap.',
                'last_verified': '2026-05-25',
            },
            # Every ReCiPe midpoint category is now explicitly entered above
            # (verified or mapping_blocked / not_in_source); no comprehension
            # fallback needed.
        }
        
        # Per-country regional adjustment factors. Selected from the module-level
        # table by `self.country`; unknown countries fall back to an empty dict
        # (identity multipliers) with a logged informational message.
        self.regional_factors = _REGIONAL_MONETIZATION_BY_COUNTRY.get(self.country, {})
        if self.country not in _REGIONAL_MONETIZATION_BY_COUNTRY:
            self.logger.info(
                "Monetization country %s has no published regional adjustment; "
                "using identity multipliers. Absolute CAD prices remain Canadian-calibrated.",
                self.country,
            )

        # Allow environment-based override for water pricing to reflect local tariffs
        try:
            env_water = os.getenv('WATER_COST_PER_M3')
            if env_water is not None and str(env_water).strip() != '':
                val = float(str(env_water).strip())
                if val > 0:
                    self.monetary_values['Water consumption'] = val
        except Exception:
            pass
        
        # Data quality and uncertainty notes
        self.value_uncertainties = {
            'Global warming': 'Official ECCC value - high confidence',
            'Water consumption': 'Based on municipal rates; varies by municipality (override with WATER_COST_PER_M3)',
            'Land use': 'Based on agricultural rental rates - medium confidence for ecosystem services',
            'Fine particulate matter formation': 'Extrapolated from international studies - medium confidence',
            'Toxicity categories': 'High uncertainty - limited Canadian-specific data',
            'Resource scarcity': 'Market-based estimates - medium confidence'
        }

    def monetize_impacts(self) -> Dict[str, float]:
        """
        Convert environmental impacts to monetary values with Canadian adjustments.
        
        :return: Dictionary with impact categories as keys and monetized values as values
        """
        try:
            monetized_impacts = {}
            # Categories whose valuation factors are expressed per tonne. Our LCA results are in kg,
            # so we convert kg->tonne by multiplying by 1/1000 before applying the factor.
            per_tonne_categories = {
                'Global warming',
                'Fine particulate matter formation',
                'Terrestrial acidification',
                'Freshwater eutrophication',
                'Marine eutrophication',
                'Stratospheric ozone depletion',
                'Ozone formation, Human health',
                'Ozone formation, Terrestrial ecosystems',
            }
            
            for impact_category, impact_value in self.lca_results.items():
                if impact_category in self.monetary_values:
                    # Align units: convert kg to tonne for categories priced per tonne
                    unit_scale = (1.0 / 1000.0) if impact_category in per_tonne_categories else 1.0
                    monetized_value = (impact_value * unit_scale) * self.monetary_values[impact_category]
                    
                    # Apply Canadian regional adjustment if available
                    regional_factor = self.regional_factors.get(impact_category, 1.0)
                    monetized_value *= regional_factor
                    
                    # Adjust for inflation
                    adjusted_value = self.adjust_for_inflation(monetized_value)
                    monetized_impacts[impact_category] = adjusted_value
                else:
                    self.logger.warning(f"No monetary value found for {impact_category}")
                    monetized_impacts[impact_category] = 0.0

            return monetized_impacts
        except Exception as e:
            self.logger.error(f"Error in monetizing impacts: {str(e)}")
            raise

    def adjust_for_inflation(self, value: float) -> float:
        """
        Adjust the monetary value for inflation using the provided formula.
        Note: ECCC SCC values are in 2021 dollars, so base year adjusted accordingly.
        
        :param value: The value to be adjusted
        :return: Inflation-adjusted value
        """
        try:
            # Fetch CPI values
            cpi_current = self.data_loader.get_cpi(self.current_year)
            cpi_base = self.data_loader.get_cpi(self.base_year)

            # Apply the inflation formula
            adjusted_value = value * (cpi_current / cpi_base)

            return adjusted_value
        except AttributeError:
            self.logger.warning("CPI data not available. Using unadjusted value.")
            return value
        except Exception as e:
            self.logger.error(f"Error adjusting for inflation: {str(e)}")
            return value

    def get_total_monetized_impact(self) -> float:
        """
        Calculate the total monetized environmental impact.
        
        :return: Total monetized impact value
        """
        try:
            monetized_impacts = self.monetize_impacts()
            return sum(monetized_impacts.values())
        except Exception as e:
            self.logger.error(f"Error calculating total monetized impact: {str(e)}")
            raise

    def get_monetized_impact_breakdown(self) -> Dict[str, Dict[str, float]]:
        """
        Get a breakdown of monetized impacts, including both original and adjusted values.
        
        :return: Dictionary with impact categories as keys and sub-dictionaries of original and adjusted values
        """
        try:
            breakdown = {}
            monetized_impacts = self.monetize_impacts()
            
            per_tonne_categories = {
                'Global warming', 'Fine particulate matter formation', 'Terrestrial acidification',
                'Freshwater eutrophication', 'Marine eutrophication', 'Stratospheric ozone depletion',
                'Ozone formation, Human health', 'Ozone formation, Terrestrial ecosystems'
            }
            
            for impact_category, impact_value in self.lca_results.items():
                if impact_category in self.monetary_values:
                    # Apply correct unit scaling
                    unit_scale = (1.0 / 1000.0) if impact_category in per_tonne_categories else 1.0
                    original_value = (impact_value * unit_scale) * self.monetary_values[impact_category]
                    adjusted_value = monetized_impacts[impact_category]
                    
                    breakdown[impact_category] = {
                        "original": original_value,
                        "adjusted": adjusted_value,
                        "regional_factor": self.regional_factors.get(impact_category, 1.0),
                        "confidence": self.value_uncertainties.get(impact_category, "Medium confidence")
                    }
                else:
                    self.logger.warning(f"No monetary value found for {impact_category}")
                    breakdown[impact_category] = {
                        "original": 0.0,
                        "adjusted": 0.0,
                        "regional_factor": 1.0,
                        "confidence": "No data available"
                    }
            return breakdown
        except Exception as e:
            self.logger.error(f"Error getting monetized impact breakdown: {str(e)}")
            raise
    
    def calculate_cost_per_calorie(self, total_calories: float) -> float:
        """
        Calculate environmental cost per calorie.
        
        :param total_calories: Total calories in the meal
        :return: Environmental cost per calorie in CAD
        """
        try:
            total_cost = self.get_total_monetized_impact()
            if total_calories > 0:
                return total_cost / total_calories
            return 0.0
        except Exception as e:
            self.logger.error(f"Error calculating cost per calorie: {str(e)}")
            return 0.0
    
    def calculate_cost_per_gram_protein(self, total_protein: float) -> float:
        """
        Calculate environmental cost per gram of protein.
        
        :param total_protein: Total protein in the meal (grams)
        :return: Environmental cost per gram protein in CAD
        """
        try:
            total_cost = self.get_total_monetized_impact()
            if total_protein > 0:
                return total_cost / total_protein
            return 0.0
        except Exception as e:
            self.logger.error(f"Error calculating cost per gram protein: {str(e)}")
            return 0.0

    def calculate_cost_per_100g(self, total_weight_grams: float) -> float:
        """
        Calculate environmental cost per 100 grams of analyzed food/meal.

        :param total_weight_grams: Total analyzed weight in grams (including waste where applicable)
        :return: Environmental cost per 100 grams in CAD
        """
        try:
            total_cost = self.get_total_monetized_impact()
            units_of_100g = (total_weight_grams / 100.0) if float(total_weight_grams or 0) > 0 else 0.0
            if units_of_100g > 0:
                return total_cost / units_of_100g
            return 0.0
        except Exception as e:
            self.logger.error(f"Error calculating cost per 100g: {str(e)}")
            return 0.0
    
    def get_cost_breakdown_by_category(self) -> Dict[str, Dict[str, float]]:
        """
        Get cost breakdown categorized by impact type.
        """
        try:
            monetized = self.monetize_impacts()
            
            categories = {
                'Climate & Energy': ['Global warming', 'Fossil resource scarcity', 'Ozone formation, Human health', 
                                   'Ozone formation, Terrestrial ecosystems', 'Stratospheric ozone depletion'],
                'Human Health': ['Fine particulate matter formation', 'Human carcinogenic toxicity', 
                               'Human non-carcinogenic toxicity', 'Ionizing radiation'],
                'Ecosystem Quality': ['Terrestrial acidification', 'Freshwater eutrophication', 'Marine eutrophication',
                                    'Terrestrial ecotoxicity', 'Freshwater ecotoxicity', 'Marine ecotoxicity'],
                'Resource Depletion': ['Water consumption', 'Land use', 'Mineral resource scarcity']
            }
            
            breakdown = {}
            total_value = sum(monetized.values())
            
            for category, impacts in categories.items():
                category_total = sum(monetized.get(impact, 0) for impact in impacts)
                category_impacts = {impact: monetized.get(impact, 0) for impact in impacts if monetized.get(impact, 0) > 0}
                breakdown[category] = {
                    'total_cost': category_total,
                    'individual_impacts': category_impacts,
                    'percentage_of_total': (category_total / total_value * 100) if total_value > 0 else 0
                }
            
            return breakdown
        except Exception as e:
            self.logger.error(f"Error getting cost breakdown by category: {str(e)}")
            return {}
    
    def compare_with_reference_cost(self, reference_cost: float) -> Dict[str, float]:
        """
        Compare meal's environmental cost with a reference cost.
        
        :param reference_cost: Reference environmental cost in CAD
        :return: Comparison metrics
        """
        try:
            total_cost = self.get_total_monetized_impact()
            
            return {
                'meal_cost': total_cost,
                'reference_cost': reference_cost,
                'cost_ratio': total_cost / reference_cost if reference_cost > 0 else float('inf'),
                'cost_difference': total_cost - reference_cost,
                'percentage_difference': ((total_cost - reference_cost) / reference_cost * 100) if reference_cost > 0 else 0
            }
        except Exception as e:
            self.logger.error(f"Error comparing with reference cost: {str(e)}")
            return {}
    
    def get_top_cost_drivers(self, top_n: int = 5) -> List[Dict[str, float]]:
        """
        Get the top cost-driving impact categories.
        
        :param top_n: Number of top categories to return
        :return: List of top impact categories with their costs
        """
        try:
            monetized = self.monetize_impacts()
            
            # Sort by cost in descending order
            sorted_impacts = sorted(monetized.items(), key=lambda x: x[1], reverse=True)
            
            top_drivers = []
            total_cost = sum(monetized.values())
            
            for i, (impact, cost) in enumerate(sorted_impacts[:top_n]):
                if cost > 0:
                    confidence = self.value_uncertainties.get(impact, "Medium confidence")
                    top_drivers.append({
                        'rank': i + 1,
                        'impact_category': impact,
                        'cost': cost,
                        'percentage_of_total': (cost / total_cost * 100) if total_cost > 0 else 0,
                        'data_confidence': confidence
                    })
            
            return top_drivers
        except Exception as e:
            self.logger.error(f"Error getting top cost drivers: {str(e)}")
            return []

    def get_data_quality_summary(self) -> Dict[str, int]:
        """
        Provide a summary of data quality and confidence levels.
        
        :return: Dictionary with confidence level counts
        """
        confidence_levels = {
            'High confidence': 0,
            'Medium confidence': 0,
            'Low confidence': 0,
            'No data available': 0
        }
        
        for category in self.lca_results.keys():
            if category in self.monetary_values:
                confidence = self.value_uncertainties.get(category, "Medium confidence")
                if "high confidence" in confidence.lower():
                    confidence_levels['High confidence'] += 1
                elif "medium confidence" in confidence.lower():
                    confidence_levels['Medium confidence'] += 1
                elif "uncertainty" in confidence.lower() or "limited" in confidence.lower():
                    confidence_levels['Low confidence'] += 1
                else:
                    confidence_levels['Medium confidence'] += 1
            else:
                confidence_levels['No data available'] += 1
        
        return confidence_levels

    def get_monetary_value_sources(self) -> Dict[str, Dict[str, str]]:
        """
        Return the source-attribution metadata for each monetary value, keyed by
        impact category. Each entry includes the citing source family, currency
        year, citation-readiness status, and last-verified ISO date. Categories
        whose `status` is `pending_page_citation` should not be cited verbatim in
        publications until their exact value has been reconciled against the
        page-cited document (see literature_wishlist.md group H).
        """
        return {
            category: dict(self.monetary_value_sources[category])
            for category in self.lca_results
            if category in self.monetary_value_sources
        }

    def __str__(self) -> str:
        return f"Monetization of environmental impacts (Base year: {self.base_year}, Current year: {self.current_year}) - Updated with official Canadian values"

    def __repr__(self) -> str:
        return self.__str__()