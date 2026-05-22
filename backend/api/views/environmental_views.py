import logging
from typing import Dict, Any, List, Optional
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from environmental_impact_model.src.data_loader import DataLoader as EnvDataLoader
from environmental_impact_model.src.food import Food as EnvFood
from environmental_impact_model.src.meal import Meal as EnvMeal
from environmental_impact_model.src.life_cycle_assessment import LifeCycleAssessment
from environmental_impact_model.src.monetization import Monetization
from environmental_impact_model.src.reference_meals import ReferenceMeals
from environmental_impact_model.src.cnf_integrator import get_cnf_integrator
from environmental_impact_model.src.methodology_factors import (
    get_methodology_pack, list_available_methodologies,
)
from environmental_impact_model.src.utils import format_impact_value, categorize_sustainability_score
from api.seo_utils import seo_metadata


_VALID_PERSPECTIVES = ("I", "H", "E")
_VALID_CONSUMER_PERSPECTIVES = ("global", "national")
_VALID_BASES = ("per_serving", "per_100g_product", "per_100_kcal", "per_100g_protein")


def _validate_methodology_params(
    methodology: str,
    perspective: str,
    country: Optional[str],
    consumer_perspective: str,
    basis: str = "per_100_kcal",
) -> Optional[Dict[str, Any]]:
    """Return None when all values are acceptable; otherwise return an error
    payload suitable for a 400 response. Centralises validation across the 3
    public endpoints so error messages stay consistent."""
    if methodology not in list_available_methodologies():
        return {
            "error": f"Unknown methodology {methodology!r}.",
            "valid_methodologies": list_available_methodologies(),
        }
    if perspective not in _VALID_PERSPECTIVES:
        return {
            "error": f"Invalid perspective {perspective!r}.",
            "valid_perspectives": list(_VALID_PERSPECTIVES),
            "hint": "H (default) = Hierarchist; I = Individualist; E = Egalitarian.",
        }
    if consumer_perspective not in _VALID_CONSUMER_PERSPECTIVES:
        return {
            "error": f"Invalid consumer_perspective {consumer_perspective!r}.",
            "valid_consumer_perspectives": list(_VALID_CONSUMER_PERSPECTIVES),
            "hint": "global (default) keeps world-average factors; national substitutes country-specific endpoint CFs.",
        }
    if basis not in _VALID_BASES:
        return {
            "error": f"Invalid basis {basis!r}.",
            "valid_bases": list(_VALID_BASES),
            "hint": "per_serving = raw absolute meal impact; per_100g_product = mass-normalised; per_100_kcal (default) = caloric-density-fair; per_100g_protein = useful for comparing protein sources.",
        }
    if country is not None:
        try:
            pack = get_methodology_pack(methodology)
        except Exception:  # noqa: BLE001
            return {"error": f"Methodology pack {methodology!r} failed to load."}
        if not pack.supports_country(country):
            return {
                "error": f"Country {country!r} not present in {methodology} pack.",
                "valid_countries_count": len(pack.list_countries()),
                "hint": "Use the /environmental-impact/methodology/ endpoint to list valid ISO-3 codes.",
            }
    return None

import os
import threading
# §3.5 GROUP-D-RECONCILIATION: lazy-initialized, module-cached LCAMatcher.
# Activation is gated on the `enable_lca_matcher` request flag (default false);
# when off, the matcher is never constructed and the existing group-default
# LCA path is bit-for-bit identical to the pre-matcher pipeline.
_LCA_MATCHER_CACHE = {"instance": None, "tried": False}
_LCA_MATCHER_LOCK = threading.Lock()
# Tier γ: parallel singleton cache for the recipe decomposer
_RECIPE_DECOMPOSER_CACHE = {"instance": None, "tried": False}
_RECIPE_DECOMPOSER_LOCK = threading.Lock()


def _build_sensitivity_block(meal, matcher_decisions):
    """Aggregate per-food EF 3.1 indicators (from the matcher's dual-namespace
    payload) by quantity, and return a side-by-side ReCiPe ⇄ EF table for the
    directly-equivalent categories (climate change + climate sub-columns +
    stratospheric ozone). Used as supplementary §4.4 / §5 sensitivity data.

    AGRIBALYSE-INGEST §3.2 / §3.5: this block is the public surface of the
    "EF-vs-ReCiPe is sensitivity, not primary" framing. The matched
    EF columns are reported in their native units (mPt/kg, mol H+ eq/kg, ...);
    consumers must NOT silently aggregate them with the ReCiPe midpoints.
    """
    if not matcher_decisions:
        return {"matched_count": 0, "ef31_aggregated_per_meal": {}, "unit_metadata": {}, "note": "matcher returned no matched rows"}

    food_id_to_quantity = {f.food_id: f.quantity for f in meal.foods}
    aggregated: Dict[str, float] = {}
    unit_metadata: Dict[str, str] = {}
    matched_count = 0
    for dec in matcher_decisions:
        if not dec.get("matched"):
            continue
        matched_count += 1
        ef = dec.get("ef31_indicators") or {}
        units = dec.get("unit_metadata") or {}
        qty_g = food_id_to_quantity.get(dec.get("food_id"), 0.0)
        qty_factor = qty_g / 100.0  # EF factors are per 100 g.
        for ind_name, per_100g_val in ef.items():
            if not isinstance(per_100g_val, (int, float)):
                continue
            aggregated[ind_name] = aggregated.get(ind_name, 0.0) + per_100g_val * qty_factor
            unit_metadata.setdefault(ind_name, units.get(ind_name, ""))
    # Replace per-kg unit fragment with per-meal in the surfaced unit string.
    unit_metadata_per_meal = {k: v.replace("/kg de produit", "/meal").replace("/kg", "/meal") for k, v in unit_metadata.items()}
    return {
        "matched_count": matched_count,
        "ef31_aggregated_per_meal": aggregated,
        "unit_metadata": unit_metadata_per_meal,
        "note": (
            "EF 3.1 (Agribalyse) indicators aggregated across matched foods. "
            "Reported in native units; categories without a direct ReCiPe "
            "equivalent (PM, acidification, toxicity, ecotoxicity, water "
            "scarcity, land EF score) should be interpreted alongside the "
            "ReCiPe midpoints rather than substituted for them. Climate "
            "change EF ≡ ReCiPe Global warming (kg CO2 eq) and is the only "
            "indicator that cross-validates directly."
        ),
    }


def _get_default_lca_matcher():
    """Return a singleton LCAMatcher (or None if construction failed or no
    API key is available and we want to suppress the degraded retrieval-only
    mode in production). Constructs on first call only.
    """
    with _LCA_MATCHER_LOCK:
        if _LCA_MATCHER_CACHE["instance"] is not None or _LCA_MATCHER_CACHE["tried"]:
            return _LCA_MATCHER_CACHE["instance"]
        _LCA_MATCHER_CACHE["tried"] = True
        try:
            from environmental_impact_model.src.lca_matcher import build_default_matcher
            api_key = os.environ.get("OPENAI_API_KEY")
            matcher = build_default_matcher(api_key=api_key)
            _LCA_MATCHER_CACHE["instance"] = matcher
            return matcher
        except Exception as exc:  # noqa: BLE001 - log + degrade
            logging.getLogger(__name__).warning(
                "Failed to construct default LCA matcher; falling back to "
                "group-default LCA only: %s", exc,
            )
            return None


def _get_default_recipe_decomposer(matcher=None):
    """Return a singleton RecipeDecomposer (Tier γ). Reuses the matcher's
    AgribalyseIndex + EmbeddingRetriever if a matcher is already constructed,
    so we don't double-load the embeddings."""
    with _RECIPE_DECOMPOSER_LOCK:
        if _RECIPE_DECOMPOSER_CACHE["instance"] is not None or _RECIPE_DECOMPOSER_CACHE["tried"]:
            return _RECIPE_DECOMPOSER_CACHE["instance"]
        _RECIPE_DECOMPOSER_CACHE["tried"] = True
        try:
            from environmental_impact_model.src.recipe_decomposer import RecipeDecomposer
            from environmental_impact_model.src.llm_client import build_chat_json_client
            # Reuse the matcher's index/retriever + chat client if available;
            # otherwise build fresh from env config.
            if matcher is not None:
                index = matcher.index
                retriever = matcher.retriever
                chat_json_client = matcher.chat_json_client
            else:
                from environmental_impact_model.src.lca_matcher import (
                    AgribalyseIndex, EmbeddingRetriever,
                )
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    return None  # Embeddings still require OpenAI key
                try:
                    from openai import OpenAI
                    embedding_client = OpenAI(api_key=api_key)
                except Exception as exc:
                    logging.getLogger(__name__).warning(
                        "openai client init failed in decomposer setup: %s", exc,
                    )
                    return None
                index = AgribalyseIndex(embedding_client=embedding_client)
                retriever = EmbeddingRetriever(index, embedding_client=embedding_client)
                chat_json_client = build_chat_json_client()  # respects LLM_PROVIDER
            if chat_json_client is None:
                return None  # No ranking client available; decomposer needs LLM
            decomposer = RecipeDecomposer(
                index=index, retriever=retriever, chat_json_client=chat_json_client,
            )
            _RECIPE_DECOMPOSER_CACHE["instance"] = decomposer
            return decomposer
        except Exception as exc:  # noqa: BLE001 - log + degrade
            logging.getLogger(__name__).warning(
                "Failed to construct default RecipeDecomposer; Tier γ disabled: %s",
                exc,
            )
            return None

logger = logging.getLogger(__name__)

def get_user_explanations(user_type: str = "individual") -> Dict[str, Dict[str, str]]:
    """
    Get user-friendly explanations tailored to different audience types.
    """
    explanations = {
        "individual": {
            "monetization": {
                "title": "💰 Environmental Cost in Dollars",
                "simple_explanation": "This shows what your meal's environmental impact costs society in Canadian dollars.",
                "detailed_explanation": "Every meal has hidden environmental costs - like climate change from greenhouse gases, health costs from air pollution, and cleanup costs for water contamination. We calculate these real costs in dollars so you can understand the true price of your food choices.",
                "what_it_means": "A higher cost means your meal has a bigger environmental impact on our planet and future generations.",
                "action_tips": "Choose meals with lower environmental costs to save money for society and protect the environment."
            },
            "reference_meals": {
                "title": "📊 How Your Meal Compares",
                "simple_explanation": "We compare your meal to three typical meal types to show you where it stands.",
                "detailed_explanation": "We created three reference meals: (1) Sustainable meals with mostly plants, local foods, and minimal processing, (2) Unsustainable meals with lots of red meat and processed foods, (3) Ultra-processed meals with packaged and fast foods.",
                "what_it_means": "Numbers above 1.0 mean your meal has more environmental impact than that meal type. Numbers below 1.0 mean less impact.",
                "action_tips": "Aim for your meal to be similar to or better than the sustainable meal (ratio close to 1.0 or lower)."
            },
            "lca_results": {
                "title": "🌍 Environmental Impact Categories",
                "simple_explanation": "These show different ways your meal affects the environment.",
                "detailed_explanation": "Life Cycle Assessment (LCA) looks at your meal's environmental impact from farm to plate, including carbon footprint (climate change), water use, land use, and effects on human health and ecosystems.",
                "what_it_means": "Each category shows a different environmental impact. Lower numbers are better for the planet.",
                "action_tips": "Focus on reducing the highest impact categories by choosing different ingredients."
            }
        },
        "researcher": {
            "monetization": {
                "title": "Economic Valuation of Environmental Externalities",
                "simple_explanation": "Monetary valuation of environmental impacts using published valuation factors.",
                "detailed_explanation": "Climate cost: CAD 221 / tonne CO₂-eq (ECCC 2023 SC-GHG Technical Update, base year 2021 CAD). Other categories draw on CE Delft Environmental Prices Handbook and True Price Foundation per-category factors with Canadian regional adjustments — see `monetization.py` for per-category source attribution. Health-impact and ecosystem-service valuations are not separately computed in v1 (they are absorbed into the per-category Environmental Prices figures rather than DALY-derived).",
                "what_it_means": "Approximate societal externality cost of the meal under the chosen valuation framework; numbers are framework-dependent and not directly comparable across studies that use different SC-GHG vintages or valuation handbooks.",
                "action_tips": "Use as a relative-ranking tool within this pipeline; for cost-benefit analyses outside it, document the underlying valuation factors used."
            },
            "reference_meals": {
                "title": "Standardized Meal Compositions for Scientific Comparison",
                "simple_explanation": "Controlled meal compositions representing different dietary patterns for benchmarking.",
                "detailed_explanation": "Reference meals are constructed using systematic food selection criteria: (1) Sustainable: Plant-forward, minimally processed, local when possible, (2) Unsustainable: Animal product-heavy, resource-intensive foods, (3) Ultra-processed: High degree of processing, packaging, and industrial ingredients. Portions are standardized by meal type and caloric content.",
                "what_it_means": "Provides standardized baselines for comparative analysis across studies and populations.",
                "action_tips": "Use as control groups for intervention studies or population-level dietary pattern analysis."
            },
            "lca_results": {
                "title": "Life Cycle Assessment Using ReCiPe 2016 Methodology",
                "simple_explanation": "Environmental impact assessment using ReCiPe 2016 H midpoint factors, restricted in v1 to three literature-anchored categories.",
                "detailed_explanation": "v1 release: ReCiPe 2016 v1.1 Hierarchist midpoint factors with Canadian regional adjustments, restricted to three categories that have per-food-group numerical literature grounding — Global warming (Poore & Nemecek 2018), Land use (P&N 2018), and Water consumption (Mekonnen & Hoekstra 2011/2012 blue-water-only). The other 15 standard ReCiPe midpoints are not consumed in v1 because per-food-group literature grounding is unavailable; see §7.5 of the methodology. Functional unit normalized to per 100 kcal.",
                "what_it_means": "Results are directly comparable to studies that use the same three indicators on the same per-100-kcal basis; broader 18-indicator comparison requires the v2 licensed AGRIBALYSE-LCI re-scoring work.",
                "action_tips": "Cite Poore & Nemecek 2018 (Science) and Mekonnen & Hoekstra 2011/2012 alongside ReCiPe 2016 (Huijbregts et al. 2017) when reporting; document the v1 three-category scope explicitly."
            }
        },
        "policy": {
            "monetization": {
                "title": "Policy-Relevant Environmental Cost Estimates",
                "simple_explanation": "Economic estimates of environmental damages for policy analysis and decision-making.",
                "detailed_explanation": "Monetized impacts provide policy-relevant cost estimates for regulatory impact assessment, carbon pricing mechanisms, and public investment decisions. Climate cost uses CAD 221 / tonne CO₂-eq from the ECCC 2023 SC-GHG Technical Update (base year 2021 CAD); other categories draw on CE Delft Environmental Prices Handbook and True Price Foundation valuations with Canadian regional adjustments — see `monetization.py` for per-category sources.",
                "what_it_means": "Quantifies the economic rationale for environmental policies and interventions in the food system.",
                "action_tips": "Use for policy cost-effectiveness analysis, taxation/subsidy design, and public health investment prioritization."
            },
            "reference_meals": {
                "title": "Policy Scenario Benchmarks",
                "simple_explanation": "Representative dietary patterns for policy scenario modeling and target setting.",
                "detailed_explanation": "Reference meals represent policy-relevant dietary patterns aligned with: (1) Canada's Food Guide recommendations (sustainable), (2) Current average Canadian diet patterns (unsustainable), (3) Worst-case processed food scenarios (ultra-processed). Enable assessment of policy interventions and dietary guideline impacts.",
                "what_it_means": "Provides baseline scenarios for evaluating policy effectiveness and setting environmental targets.",
                "action_tips": "Use for dietary guideline development, food policy evaluation, and environmental target setting."
            },
            "lca_results": {
                "title": "Environmental Performance Indicators for Food Policy",
                "simple_explanation": "Three ReCiPe 2016 H midpoint indicators (GW, Land use, blue-water consumption), reported per 100 kcal.",
                "detailed_explanation": "v1 release ships three literature-anchored ReCiPe 2016 H midpoints with documented sources (P&N 2018 for GW + Land; M&H 2011/2012 blue-water-only for Water). Methodology follows the framework of ISO 14040/14044 LCA standards; the licensed AGRIBALYSE-LCI re-scoring needed to extend to all 18 ReCiPe midpoints under Canada-specific characterisation factors is deferred to v2. Indicators map to Canada's Net Zero 2050 (climate) and broader food-system SDG targets at a thematic level rather than to specific numeric targets.",
                "what_it_means": "Provides a structured baseline for food-related environmental policy framing on the three indicators above; reach beyond these requires v2 work or external LCA data.",
                "action_tips": "Use for relative ranking and intervention-target setting on GW / Land / Water; document the v1 three-indicator scope when citing in policy documents."
            }
        }
    }
    
    return explanations.get(user_type, explanations["individual"])

def format_environmental_results(meal_data: Dict[str, Any], user_type: str = "individual") -> Dict[str, Any]:
    """
    Format environmental results with user-appropriate explanations and context.
    """
    explanations = get_user_explanations(user_type)
    
    # Format monetization results with clear explanations
    monetization_data = meal_data.get('monetization', {})
    # Build monetized_impacts by flattening per-category individual impacts if not explicitly provided
    _flat_monetized_impacts = {}
    try:
        for _info in (monetization_data.get('cost_breakdown_by_category') or {}).values():
            for _impact, _cost in (_info.get('individual_impacts') or {}).items():
                _flat_monetized_impacts[_impact] = _flat_monetized_impacts.get(_impact, 0) + float(_cost or 0)
    except Exception:
        _flat_monetized_impacts = {}

    formatted_monetization = {
        "explanation": explanations["monetization"],
        "results": {
            "total_environmental_cost": {
                "value": monetization_data.get('total_cost', 0),
                "unit": "CAD",
                "formatted": f"${monetization_data.get('total_cost', 0):.3f} CAD",
                "context": "Total cost of environmental damage caused by this meal"
            },
            "cost_per_calorie": {
                "value": monetization_data.get('cost_per_calorie', 0),
                "unit": "CAD/kcal",
                "formatted": f"${monetization_data.get('cost_per_calorie', 0):.5f} CAD per calorie",
                "context": "Environmental cost per calorie consumed"
            },
            "cost_per_protein": {
                "value": monetization_data.get('cost_per_protein', 0),
                "unit": "CAD/g protein",
                "formatted": f"${monetization_data.get('cost_per_protein', 0):.5f} CAD per gram protein",
                "context": "Environmental cost per gram of protein"
            },
            "top_cost_drivers": monetization_data.get('top_cost_drivers', [])[:3],
            "cost_breakdown": monetization_data.get('cost_breakdown_by_category', {}),
            "monetized_impacts": _flat_monetized_impacts,
            # CODE-4: per-category source attribution (additive).
            "value_sources": monetization_data.get('value_sources', {}),
        },
        "interpretation": _get_cost_interpretation(monetization_data.get('total_cost', 0), user_type)
    }
    
    # Format reference meal comparisons with clear explanations
    reference_data = meal_data.get('reference_comparisons', {})
    formatted_comparisons = {
        "explanation": explanations["reference_meals"],
        "results": {},
        "interpretation": {}
    }
    
    for meal_type, comparison_data in reference_data.items():
        if 'error' not in comparison_data:
            cost_ratio = comparison_data.get('cost_ratio', 1.0)
            carbon_ratio = comparison_data.get('carbon_ratio', 1.0)
            
            formatted_comparisons["results"][meal_type] = {
                "environmental_cost_ratio": {
                    "value": cost_ratio,
                    "formatted": f"{cost_ratio:.2f}x",
                    "meaning": _get_ratio_meaning(cost_ratio)
                },
                "carbon_footprint_ratio": {
                    "value": carbon_ratio,
                    "formatted": f"{carbon_ratio:.2f}x",
                    "meaning": _get_ratio_meaning(carbon_ratio)
                },
                "reference_meal_description": _get_meal_description(meal_type)
            }
            
            formatted_comparisons["interpretation"][meal_type] = _get_comparison_interpretation(cost_ratio, carbon_ratio, meal_type, user_type)
    
    # Format LCA results with explanations
    lca_data = meal_data.get('lca', {})
    formatted_lca = {
        "explanation": explanations["lca_results"],
        "key_impacts": {
            "carbon_footprint": {
                "value": lca_data.get('midpoint_impacts', {}).get('Global warming', 0),
                "unit": "kg CO2-eq",
                "formatted": format_impact_value(lca_data.get('midpoint_impacts', {}).get('Global warming', 0), "kg CO2-eq"),
                "category": "Climate Change",
                "importance": "Primary driver of global warming and climate change"
            },
            "water_consumption": {
                "value": lca_data.get('midpoint_impacts', {}).get('Water consumption', 0),
                "unit": "m³",
                "formatted": format_impact_value(lca_data.get('midpoint_impacts', {}).get('Water consumption', 0), "m³"),
                "category": "Resource Use",
                "importance": "Freshwater resource depletion"
            },
            "land_use": {
                "value": lca_data.get('midpoint_impacts', {}).get('Land use', 0),
                "unit": "m²a crop-eq",
                "formatted": format_impact_value(lca_data.get('midpoint_impacts', {}).get('Land use', 0), "m²a crop-eq"),
                "category": "Ecosystem Impact",
                "importance": "Land conversion and biodiversity impact"
            }
        },
        "summary_score": {
            "value": lca_data.get('single_score', 0),
            "formatted": f"{lca_data.get('single_score', 0):.3e} points",
            "explanation": "Single aggregated score combining all environmental impacts"
        },
        "all_impacts": lca_data.get('midpoint_impacts', {}),
        "endpoint_impacts": lca_data.get('endpoint_impacts', {}),
        # v1 'demote, don't perfect' uncertainty bands. Parallel to all_impacts
        # and endpoint_impacts; each consumed category maps to {low, central, high}.
        # Resources is intentionally absent from endpoint_impacts_bands when the
        # underlying Resources endpoint is None (v1 trim).
        "all_impacts_bands": lca_data.get('midpoint_impacts_bands', {}),
        "endpoint_impacts_bands": lca_data.get('endpoint_impacts_bands', {}),
        # Tier α: multi-basis functional-unit exposure. The headline `all_impacts`
        # / `endpoint_impacts` above reflect the request's `basis` choice
        # (default per_100_kcal); the by-basis dicts give all four bases
        # (per_serving, per_100g_product, per_100_kcal, per_100g_protein)
        # for transparent re-display without re-querying.
        "impacts_by_basis":         lca_data.get('midpoint_impacts_by_basis', {}),
        "impacts_bands_by_basis":   lca_data.get('midpoint_impacts_bands_by_basis', {}),
        "endpoint_impacts_by_basis": lca_data.get('endpoint_impacts_by_basis', {}),
        "basis_factors":            lca_data.get('basis_factors', {}),
        # CODE-5: per-category confidence rating and methodology provenance
        # (additive — existing consumers ignore unknown keys).
        "factor_confidence_by_category": lca_data.get('factor_confidence_by_category', {}),
        "data_quality": lca_data.get('data_quality', {}),
        # AGRIBALYSE-INGEST: §3.5 LCA matcher additive fields. Always present
        # in the response shape; populated when enable_lca_matcher=true.
        "lca_matcher_enabled": lca_data.get('lca_matcher_enabled', False),
        "lca_matcher_decisions": lca_data.get('lca_matcher_decisions', []),
        "catalog_version": lca_data.get('catalog_version'),
        "recipe2016_h_ef31_sensitivity": lca_data.get('recipe2016_h_ef31_sensitivity'),
        # Tier γ: composite recipe decomposition audit trail. Populated only
        # when `enable_recipe_decomposer=true` AND the matcher fell back on
        # a composite-y CNF food (Mixed Dishes, Soups, Fast Foods, Babyfoods, ...).
        "recipe_decomposer_enabled": lca_data.get('recipe_decomposer_enabled', False),
        "recipe_decomposition_decisions": lca_data.get('recipe_decomposition_decisions', []),
    }
    
    # Surface sustainability scores (numeric) calculated server-side so the UI
    # does not need to infer them. Keep a minimal, stable shape — additive
    # keys (environmental_rating, category_zones, methodology_note,
    # overall_weights) are passed through for v1 literature-anchored zone
    # display. Frontend consumers ignore unknown keys.
    sustainability_raw = meal_data.get('sustainability', {}) or {}
    formatted_sustainability = {
        "overall_sustainability_score": sustainability_raw.get('overall_sustainability_score', 50),
        "sustainability_rating": sustainability_raw.get('sustainability_rating', 'Unknown'),
        "environmental_score": sustainability_raw.get('environmental_score'),
        "environmental_rating": sustainability_raw.get('environmental_rating'),
        "nutritional_score": sustainability_raw.get('nutritional_score'),
        "processing_score": sustainability_raw.get('processing_score'),
        "category_scores": sustainability_raw.get('category_scores', {}),
        # v1 literature-anchored per-category zones (Stylianou 2021 SI Table 11B + P&N 2018).
        "category_zones": sustainability_raw.get('category_zones', {}),
        "methodology_note": sustainability_raw.get('methodology_note', ''),
        "overall_weights": sustainability_raw.get('overall_weights'),
        # Provide a simple recommendation aligned with overall assessment below
        "recommendations": []
    }

    # Add a simple recommendation based on the overall assessment that we compute below
    # (We keep this small coupling to avoid duplicating logic.)
    # This will be filled after overall assessment is computed.

    return {
        "monetization": formatted_monetization,
        "reference_comparisons": formatted_comparisons,
        "environmental_impacts": formatted_lca,
        # Include sustainability block so clients can render numeric score directly
        "sustainability": formatted_sustainability,
        "overall_assessment": _get_overall_assessment(meal_data, user_type)
    }

def _get_cost_interpretation(total_cost: float, user_type: str) -> Dict[str, str]:
    """Get interpretation of environmental cost based on user type."""
    interpretations = {
        "individual": {
            "low": "Great choice! This meal has a low environmental cost.",
            "medium": "This meal has a moderate environmental impact. Consider choosing more plant-based options.",
            "high": "This meal has a high environmental cost. Try reducing meat portions or choosing more sustainable ingredients."
        },
        "researcher": {
            # NB: the low/medium/high cutoffs (CAD 0.05 / 0.20) are pragmatic
            # heuristic thresholds, not empirical percentiles. Phrasing avoids
            # implying a published distribution we have not computed.
            "low":  "Below the heuristic CAD 0.05 / meal cost threshold — comparatively low monetised externality.",
            "medium": "Between CAD 0.05 and 0.20 / meal — mid-range monetised externality.",
            "high": "Above CAD 0.20 / meal — comparatively high monetised externality on this heuristic scale.",
        },
        "policy": {
            # Removed claim of "alignment with sustainable dietary targets and
            # climate objectives" — the score is not computed against a
            # specific Net Zero 2050 sub-target or Canada Food Guide
            # quantitative threshold. Wording reflects the heuristic nature.
            "low":  "Low monetised externality on the configured valuation scale; flag for context, not as a policy benchmark.",
            "medium": "Moderate monetised externality; informative for intervention triage rather than absolute compliance.",
            "high": "Comparatively high monetised externality; flag for further evaluation under the relevant policy framework.",
        }
    }
    
    if total_cost < 0.05:
        level = "low"
    elif total_cost < 0.20:
        level = "medium" 
    else:
        level = "high"
    
    return {
        "level": level,
        "message": interpretations.get(user_type, interpretations["individual"])[level],
        "context": f"Based on environmental cost of ${total_cost:.3f} CAD"
    }

def _get_ratio_meaning(ratio: float) -> str:
    """Get human-readable meaning of comparison ratios."""
    if ratio < 0.5:
        return "Much better (less than half the impact)"
    elif ratio < 0.8:
        return "Better (lower impact)"
    elif ratio < 1.2:
        return "Similar impact"
    elif ratio < 2.0:
        return "Worse (higher impact)"
    else:
        return "Much worse (more than double the impact)"

def _get_meal_description(meal_type: str) -> str:
    """Get description of reference meal types."""
    descriptions = {
        "sustainable": "Plant-forward meal with legumes, whole grains, vegetables, and minimal animal products - represents environmentally responsible eating",
        "unsustainable": "Meat-heavy meal with beef or lamb, processed foods, and resource-intensive ingredients - represents high-impact eating patterns", 
        "ultra_processed": "Meal dominated by packaged foods, fast food items, and highly processed ingredients - represents convenience-focused eating",
        "balanced": "Mixed meal following dietary guidelines with moderate amounts of animal products, vegetables, and whole grains"
    }
    return descriptions.get(meal_type, "Reference meal for comparison")

def _get_comparison_interpretation(cost_ratio: float, carbon_ratio: float, meal_type: str, user_type: str) -> str:
    """Get interpretation of meal comparison results."""
    if user_type == "individual":
        if meal_type == "sustainable":
            if cost_ratio <= 1.0:
                return "Excellent! Your meal is as sustainable as our eco-friendly reference meal."
            else:
                return f"Your meal has {cost_ratio:.1f}x more environmental impact than a sustainable meal. Try adding more plants!"
        elif meal_type == "unsustainable":
            if cost_ratio < 1.0:
                return f"Good news! Your meal is {1/cost_ratio:.1f}x better than a high-impact meal."
            else:
                return "Your meal has similar or higher impact than an unsustainable meal. Consider healthier choices."
    
    elif user_type == "researcher":
        return f"Environmental cost ratio: {cost_ratio:.2f}, Carbon footprint ratio: {carbon_ratio:.2f} relative to {meal_type} reference scenario."
    
    else:  # policy
        return f"Policy scenario comparison: {cost_ratio:.2f}x cost ratio indicates {'alignment with' if cost_ratio <= 1.0 else 'deviation from'} sustainable dietary targets."
    
    return f"Comparison to {meal_type} meal shows {cost_ratio:.2f}x environmental cost difference."

def _get_overall_assessment(meal_data: Dict[str, Any], user_type: str) -> Dict[str, str]:
    """Get overall assessment and recommendations."""
    sustainability_score = meal_data.get('sustainability', {}).get('overall_sustainability_score', 50)
    cost = meal_data.get('monetization', {}).get('total_cost', 0)
    
    if user_type == "individual":
        # Bands harmonised with `LifeCycleAssessment._sustainability_rating`
        # (Excellent >= 80, Good >= 65, Moderate >= 50, Poor >= 35, else Very Poor).
        # Previously this gated Excellent at >= 70, which produced "Excellent
        # Choice!" labels for meals that the score tile showed as "Good".
        if sustainability_score >= 80 and cost < 0.1:
            return {
                "rating": "Excellent Choice! 🌟",
                "message": "Your meal is both environmentally friendly and nutritious. Keep up the great work!",
                "recommendation": "Share your sustainable eating choices with friends and family."
            }
        elif sustainability_score >= 65:
            return {
                "rating": "Good Choice 👍",
                "message": "Your meal scores well overall, with some room to lower the environmental impact further.",
                "recommendation": "Consider seasonal produce, smaller animal-product portions, or substituting in legumes."
            }
        elif sustainability_score >= 50:
            return {
                "rating": "Moderate 🟡",
                "message": "Your meal has a mixed sustainability profile.",
                "recommendation": "Look for the highest-impact category in the per-category cards and target a substitution there."
            }
        else:
            return {
                "rating": "Room for Improvement 🔄",
                "message": "Your meal has a high environmental impact in at least one category.",
                "recommendation": "Reducing red-meat or large dairy portions usually gives the biggest single improvement."
            }
    
    elif user_type == "researcher":
        return {
            "rating": f"Sustainability Score: {sustainability_score:.1f}/100",
            "message": "Quantitative score blending three literature-anchored ReCiPe categories (50%), a nutritional density signal (30%), and a heuristic processing-intensity proxy (20%).",
            "recommendation": "Suitable for relative ranking within this panel; cross-method comparison (e.g. against IMPACT World+ studies) requires re-derivation per §7.5 caveats."
        }

    else:  # policy
        return {
            "rating": f"Indicative Sustainability Score: {sustainability_score:.1f}/100",
            "message": "Heuristic three-component score; not calibrated against a specific Net Zero 2050 sub-target or Canada Food Guide quantitative threshold.",
            "recommendation": "Use as a relative-ranking signal across food choices; pair with the per-category ReCiPe and monetisation outputs for any policy-relevant claim."
        }

@api_view(['POST'])
@permission_classes([AllowAny])
@seo_metadata(
    title="Environmental Impact Calculator | EcoDish365",
    description="Calculate the comprehensive environmental impact of your meals with our advanced LCA tool. Get clear explanations and compare to reference meals.",
    keywords="environmental impact, LCA, food sustainability, carbon footprint, meal comparison, monetization"
)
def environmental_impact(request):
    """
    Comprehensive environmental impact assessment with user-friendly explanations.
    
    Supports different explanation levels for:
    - individual: Everyday consumers seeking actionable insights
    - researcher: Scientists and academics needing technical details
    - policy: Policymakers requiring evidence-based assessments
    """
    try:
        # Get request parameters
        food_data = request.data.get('foods', [])
        user_type = request.data.get('user_type', 'individual')  # individual, researcher, policy
        # §3.5 LCA matcher flag (default off — preserves existing behaviour bit-for-bit).
        enable_lca_matcher = bool(request.data.get('enable_lca_matcher', False))
        matcher = _get_default_lca_matcher() if enable_lca_matcher else None
        # Tier γ: composite-food recipe decomposition. Default off (preserves
        # existing behaviour bit-for-bit). Reuses the matcher's index +
        # embedding client if available, so no double-load.
        enable_recipe_decomposer = bool(request.data.get('enable_recipe_decomposer', False))
        decomposer = _get_default_recipe_decomposer(matcher=matcher) if enable_recipe_decomposer else None

        # Methodology / perspective / country / basis (all optional; defaults
        # preserve today's H + global-supply-chain + per-100-kcal behaviour).
        # Validate here so an invalid value gives a 400 with a helpful message
        # instead of an internal 500 from LifeCycleAssessment.__init__.
        methodology = request.data.get('methodology', 'recipe2016')
        perspective = request.data.get('perspective', 'H')
        country = request.data.get('country')  # ISO-3 or None
        consumer_perspective = request.data.get('consumer_perspective', 'global')
        basis = request.data.get('basis', 'per_100_kcal')
        param_error = _validate_methodology_params(
            methodology, perspective, country, consumer_perspective, basis,
        )
        if param_error is not None:
            return Response(param_error, status=status.HTTP_400_BAD_REQUEST)

        if not food_data:
            return Response({
                "error": "No food data provided. Please include 'foods' array with food_id and quantity.",
                "example": {
                    "foods": [
                        {"food_id": 2003, "quantity": 150},
                        {"food_id": 3580, "quantity": 100}
                    ],
                    "user_type": "individual"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize data loader and CNF integrator
        cnf_integrator = get_cnf_integrator()
        if not cnf_integrator.is_initialized():
            # Try to initialize with default path
            cnf_integrator.initialize('raw_cnf')
        
        data_loader = EnvDataLoader()
        
        # Create meal
        foods = [EnvFood(food_id=item['food_id'], quantity=item['quantity'], data_loader=data_loader) 
                for item in food_data]
        meal = EnvMeal(foods)
        
        # Perform comprehensive analysis
        comprehensive_analysis = _analyze_meal_comprehensive(
            meal, data_loader, matcher=matcher,
            methodology=methodology, perspective=perspective,
            country=country, consumer_perspective=consumer_perspective,
            basis=basis,
            decomposer=decomposer,
        )

        # Format results with user-appropriate explanations
        formatted_results = format_environmental_results(comprehensive_analysis, user_type)

        # Surface the methodology pack version + parameters in the envelope so
        # the UI can render an active-configuration chip without parsing nested
        # `lca` fields. (Backward-compatible: existing fields preserved.)
        lca_block = comprehensive_analysis.get('lca', {}) if isinstance(comprehensive_analysis, dict) else {}
        methodology_metadata = {
            "user_type": user_type,
            "methodology_pack": lca_block.get('methodology_pack'),
            "parameters": lca_block.get('parameters', {}),
            "methodology": (
                f"ReCiPe 2016 v1.1 ({perspective})"
                + (f" — consumer={consumer_perspective}, country={country}" if country else "")
            ),
            "data_source": "Canadian Nutrient File (Health Canada)",
            "currency": "CAD",
            "functional_unit": "per 100 kcal",
        }

        # Create final response (reuse enriched meal_info with macronutrient distribution)
        result = {
            "data": formatted_results,
            "meal_info": comprehensive_analysis.get('meal_info', {
                "composition": meal.get_food_breakdown(),
                "total_calories": meal.calculate_total_calories(),
                "total_weight": meal.get_total_weight(),
            }),
            "metadata": methodology_metadata,
            "seo_metadata": {
                "title": f"Environmental Impact Assessment - {user_type.title()} View | DISH Research",
                "description": f"Comprehensive environmental impact assessment tailored for {user_type}s. Get clear explanations of your meal's carbon footprint, environmental costs, and sustainability rating.",
                "keywords": f"environmental impact, {user_type}, LCA, food sustainability, carbon footprint, meal assessment"
            }
        }
        
        return Response(result)
        
    except ValueError as e:
        logger.error(f"Validation error in environmental impact calculation: {str(e)}")
        return Response({
            "error": "Invalid input data",
            "details": str(e),
            "help": "Please check that all food_id values exist in the database and quantities are positive numbers."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"Error in environmental impact calculation: {str(e)}", exc_info=True)
        return Response({
            "error": "An unexpected error occurred during the environmental impact calculation.",
            "help": "Please try again or contact support if the problem persists."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _analyze_meal_comprehensive(
    meal: EnvMeal,
    data_loader: EnvDataLoader,
    matcher=None,
    *,
    methodology: str = 'recipe2016',
    perspective: str = 'H',
    country: Optional[str] = None,
    consumer_perspective: str = 'global',
    basis: str = 'per_100_kcal',
    decomposer=None,
) -> Dict[str, Any]:
    """Perform comprehensive meal analysis including LCA, monetization, and reference comparisons.

    When `matcher` is provided (§3.5 GROUP-D-RECONCILIATION), the per-food impact
    factors come from the matcher's Agribalyse mapping at confidence ≥ threshold,
    with logged fallback to the existing cnf_integrator group-default path.

    Country / perspective / consumer-perspective parameters thread through to
    `LifeCycleAssessment` (which loads the methodology pack) and `Monetization`
    (which selects per-country economic adjustments). Defaults reproduce
    today's Hierarchist + global-supply-chain + Canadian-monetary behaviour.
    """
    try:
        # Basic meal info
        # Basic meal info
        total_calories = meal.calculate_total_calories()
        total_weight = meal.get_total_weight()
        composition_list = meal.get_food_breakdown()

        # Macronutrient distribution (% of energy) with robust nutrient name matching
        def _get_nutrient_amount_any(names):
            for n in names:
                val = meal.get_nutrient_amount(n)
                if val and val > 0:
                    return val
            return 0.0

        protein_g = _get_nutrient_amount_any([
            'PROTEIN', 'PROTEINS'
        ])
        fat_g = _get_nutrient_amount_any([
            'FAT', 'TOTAL FAT', 'FAT, TOTAL', 'TOTAL LIPID', 'TOTAL LIPID (G)', 'LIPID (TOTAL)', 'LIPIDS'
        ])
        carbs_g = _get_nutrient_amount_any([
            'CARBOHYDRATE', 'CARBOHYDRATES', 'TOTAL CARBOHYDRATE', 'CARBOHYDRATE, TOTAL',
            'AVAILABLE CARBOHYDRATE', 'CARBOHYDRATE, AVAILABLE'
        ])
        protein_kcal = protein_g * 4.0
        fat_kcal = fat_g * 9.0
        carbs_kcal = carbs_g * 4.0
        kcal_sum = protein_kcal + fat_kcal + carbs_kcal
        if kcal_sum <= 0 and total_calories > 0:
            # Fallback to total calories if macro calories unavailable
            kcal_sum = total_calories
        # Compute initial percentages
        protein_pct = (protein_kcal / kcal_sum * 100.0) if kcal_sum > 0 else 0.0
        carb_pct = (carbs_kcal / kcal_sum * 100.0) if kcal_sum > 0 else 0.0
        fat_pct = (fat_kcal / kcal_sum * 100.0) if kcal_sum > 0 else 0.0

        # If only one macro present and others zero but total_calories > kcal_sum (e.g., measured energy),
        # rescale using total_calories to avoid showing 100% for a single macro.
        if total_calories > 0 and kcal_sum > 0 and (fat_kcal == 0 or carbs_kcal == 0):
            protein_pct = (protein_kcal / total_calories * 100.0)
            carb_pct = (carbs_kcal / total_calories * 100.0)
            fat_pct = (fat_kcal / total_calories * 100.0)

        # Normalize to ensure the sum does not exceed 100 due to rounding
        total_pct = protein_pct + carb_pct + fat_pct
        if total_pct > 0:
            scale = min(1.0, 100.0 / total_pct)
            protein_pct *= scale
            carb_pct *= scale
            fat_pct *= scale

        macronutrient_distribution = {
            'protein_percent': protein_pct,
            'carbohydrate_percent': carb_pct,
            'fat_percent': fat_pct,
        }

        meal_info = {
            'total_calories': total_calories,
            'total_weight': total_weight,
            'composition': composition_list,
            'macronutrient_distribution': macronutrient_distribution,
        }
        
        # Life Cycle Assessment — methodology pack + perspective + country
        # + basis + (optional) recipe decomposer (Tier γ composite fallback)
        lca = LifeCycleAssessment(
            meal, matcher=matcher,
            methodology=methodology,
            perspective=perspective,
            country=country,
            consumer_perspective=consumer_perspective,
            basis=basis,
            decomposer=decomposer,
        )
        lca_results = lca.perform_lcia()
        endpoint_impacts = lca.calculate_endpoint_impacts()
        single_score = lca.calculate_single_score()
        normalized_midpoints = lca.calculate_normalized_midpoints()

        lca_data = {
            'midpoint_impacts': lca_results,
            'endpoint_impacts': endpoint_impacts,
            'single_score': single_score,
            # v1 'demote, don't perfect': expose worst/best-case envelope bands
            # alongside the central values. Bands present only for the 3
            # literature-anchored midpoint categories (Global warming, Land use,
            # Water consumption); other categories not in the consumed vector.
            'midpoint_impacts_bands': lca.midpoint_impacts_bands,
            'endpoint_impacts_bands': lca.endpoint_impacts_bands,
            # Per-category confidence rating (CODE-5; additive).
            'factor_confidence_by_category': lca.get_factor_confidence_by_category(),
            # Methodology pack version + provenance + per-pathway factor source
            # (world-average vs country-specific) so the UI can render
            # transparent attribution.
            'data_quality': lca.get_data_quality_report(),
            'methodology_pack': lca.pack.version_string(),
            'parameters': {
                'methodology': methodology,
                'perspective': perspective,
                'country': country,
                'consumer_perspective': consumer_perspective,
                'basis': basis,
            },
            'endpoint_factor_sources': dict(lca.endpoint_factor_sources),
            'normalized_contributions_per_person': normalized_midpoints,
            # Tier α: full 4-basis impact dicts for transparency. The headline
            # `midpoint_impacts` / `endpoint_impacts` above reflect the chosen
            # `basis`; consumers wanting per-100-g-product or per-100-g-protein
            # output can read directly from these without re-querying.
            'midpoint_impacts_by_basis': lca.midpoint_impacts_by_basis,
            'midpoint_impacts_bands_by_basis': lca.midpoint_impacts_bands_by_basis,
            'endpoint_impacts_by_basis': lca.endpoint_impacts_by_basis,
            'basis_factors': lca.basis_factors,
            # Tier γ: composite recipe decomposition audit trail (parallel
            # to `lca_matcher_decisions`). Populated when
            # `enable_recipe_decomposer=True` AND the matcher fell back on
            # a composite CNF food.
            'recipe_decomposition_decisions': lca.recipe_decomposition_decisions,
            'recipe_decomposer_enabled': decomposer is not None,
        }
        # §3.5 GROUP-D-RECONCILIATION + AGRIBALYSE-INGEST: surface matcher
        # audit trail and dual-namespace EF sensitivity block when active.
        if matcher is not None:
            lca_data['lca_matcher_decisions'] = lca.matcher_decisions
            lca_data['lca_matcher_enabled'] = True
            # Catalog version from the first matcher decision (same for all).
            lca_data['catalog_version'] = (
                lca.matcher_decisions[0].get('catalog_version')
                if lca.matcher_decisions else None
            )
            lca_data['recipe2016_h_ef31_sensitivity'] = _build_sensitivity_block(
                meal, lca.matcher_decisions
            )
        else:
            lca_data['lca_matcher_enabled'] = False

        # Monetization — accepts country to select per-country regional
        # adjustments (Canadian default).
        monetization = Monetization(lca_results, data_loader, country=country)
        total_calories = meal_info['total_calories']
        total_protein = meal.get_nutrient_amount('PROTEIN')

        monetization_data = {
            'total_cost': monetization.get_total_monetized_impact(),
            'cost_per_calorie': monetization.calculate_cost_per_calorie(total_calories),
            'cost_per_protein': monetization.calculate_cost_per_gram_protein(total_protein),
            'cost_breakdown_by_category': monetization.get_cost_breakdown_by_category(),
            'top_cost_drivers': monetization.get_top_cost_drivers(),
            # Per-category source attribution (CODE-4; additive).
            'value_sources': monetization.get_monetary_value_sources(),
        }
        
        # Reference meal comparisons
        reference_meals = ReferenceMeals(data_loader)
        reference_comparisons = {}
        
        meal_types = ['sustainable', 'unsustainable', 'ultra_processed', 'balanced']
        main_cost = monetization_data['total_cost']
        main_carbon = lca_results.get('Global warming', 0)
        
        for meal_type in meal_types:
            try:
                if meal_type == 'sustainable':
                    ref_meal = reference_meals.create_sustainable_meal('lunch')
                elif meal_type == 'unsustainable':
                    ref_meal = reference_meals.create_unsustainable_meal('lunch')
                elif meal_type == 'ultra_processed':
                    ref_meal = reference_meals.create_ultra_processed_meal('lunch')
                elif meal_type == 'balanced':
                    ref_meal = reference_meals.create_balanced_meal('lunch')
                
                # Calculate reference meal impacts using the SAME parameters
                # as the user's meal so the comparison is apples-to-apples.
                ref_lca = LifeCycleAssessment(
                    ref_meal,
                    methodology=methodology,
                    perspective=perspective,
                    country=country,
                    consumer_perspective=consumer_perspective,
                    basis=basis,
                )
                ref_impacts = ref_lca.perform_lcia()
                ref_monetization = Monetization(ref_impacts, data_loader, country=country)
                ref_cost = ref_monetization.get_total_monetized_impact()
                ref_carbon = ref_impacts.get('Global warming', 0)
                
                # Avoid infinities in JSON by guarding zero denominators
                safe_cost_ratio = (main_cost / ref_cost) if (isinstance(ref_cost, (int, float)) and ref_cost > 0) else 1.0
                safe_carbon_ratio = (main_carbon / ref_carbon) if (isinstance(ref_carbon, (int, float)) and ref_carbon > 0) else 1.0

                reference_comparisons[meal_type] = {
                    'cost_ratio': safe_cost_ratio,
                    'carbon_ratio': safe_carbon_ratio,
                    'reference_cost': ref_cost,
                    'reference_carbon': ref_carbon,
                    'notes': 'Ratios default to 1.0 when reference denominator is zero or invalid.'
                }
                
            except Exception as e:
                logger.warning(f"Failed to create {meal_type} reference meal: {e}")
                reference_comparisons[meal_type] = {'error': str(e)}
        
        # Sustainability scoring — delegated to the shared helper used by
        # both `/environmental-impact/` and `/environmental-impact/compare-foods/`
        # so the same food always scores the same regardless of endpoint.
        sustainability = _compose_blended_sustainability(meal, lca)
        
        return {
            'meal_info': meal_info,
            'lca': lca_data,
            'monetization': monetization_data,
            'reference_comparisons': reference_comparisons,
            'sustainability': sustainability
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive meal analysis: {e}")
        raise

# Blend weights for the headline sustainability score across endpoints.
# Documented in §3.x: environment is the dominant driver, nutrition is the
# second-order signal, processing is heuristic. Centralised here so that
# both `/environmental-impact/` and `/environmental-impact/compare-foods/`
# produce identical numbers for identical inputs.
SUSTAINABILITY_BLEND_WEIGHTS = {'environmental': 0.5, 'nutritional': 0.3, 'processing': 0.2}


def _compose_blended_sustainability(meal: EnvMeal, lca: LifeCycleAssessment) -> Dict[str, Any]:
    """Single source of truth for the sustainability-score block returned by
    the environmental-impact API endpoints.

    Inputs:
      - `meal`  : the EnvMeal under analysis (used for nutritional + processing).
      - `lca`   : the already-constructed LifeCycleAssessment for that meal
                  (matcher-aware via its `_get_food_environmental_impacts` cache).

    Returns the same dict shape consumed by both the main and the comparison
    endpoints. Centralisation prevents the previous divergence where the
    main endpoint showed a blended 68 / 100 for beans-lima 100 g while the
    comparison endpoint showed env-only 87 / 100 for the SAME food.
    """
    from environmental_impact_model.src.life_cycle_assessment import (
        LifeCycleAssessment as _LCA,
    )

    # Environmental (literature-anchored, matcher-aware) ---------------------
    env_sustainability = lca.calculate_matcher_aware_sustainability_score()
    environmental_score = float(env_sustainability.get('overall_sustainability_score', 50) or 50)
    env_rating = env_sustainability.get('sustainability_rating', 'Unknown')

    # Quantity-weighted per-category scores + dominant Low/Mod/High zone.
    category_scores: Dict[str, float] = {}
    category_zones: Dict[str, str] = {}
    for cat in ('Global warming', 'Land use', 'Water consumption'):
        num = denom = 0.0
        zone_counts: Dict[str, float] = {}
        for fs in env_sustainability.get('individual_food_scores', []):
            qty = float(fs.get('quantity_g') or 0)
            cat_score = fs.get(cat)
            cat_zone = fs.get(f'{cat}_zone')
            if isinstance(cat_score, (int, float)) and qty > 0:
                num += cat_score * qty
                denom += qty
                if cat_zone:
                    zone_counts[cat_zone] = zone_counts.get(cat_zone, 0) + qty
        if denom > 0:
            category_scores[cat] = num / denom
            if zone_counts:
                severity = {'Low': 0, 'Moderate': 1, 'High': 2}
                category_zones[cat] = max(zone_counts, key=lambda z: (zone_counts[z], severity.get(z, 0)))

    # Nutritional + processing (left untouched; pre-existing helpers) --------
    try:
        nutrition_quality = meal.get_nutritional_quality_score()
        nutritional_score = float(nutrition_quality.get('nutritional_quality_score', 0) or 0)
    except Exception:
        nutritional_score = 0.0
    try:
        processing_score = float(_estimate_processing_score(meal))
    except Exception:
        processing_score = 0.0

    # Blended overall + harmonised rating bands ------------------------------
    w = SUSTAINABILITY_BLEND_WEIGHTS
    overall_blend = (
        w['environmental'] * environmental_score
        + w['nutritional'] * nutritional_score
        + w['processing']  * processing_score
    )
    overall_rating = _LCA._sustainability_rating(overall_blend)

    return {
        'overall_sustainability_score': overall_blend,
        'sustainability_rating':        overall_rating,
        'environmental_score':          environmental_score,
        'environmental_rating':         env_rating,
        'nutritional_score':            nutritional_score,
        'processing_score':             processing_score,
        'category_scores':              category_scores,
        'category_zones':               category_zones,
        'individual_food_scores':       env_sustainability.get('individual_food_scores', []),
        'methodology_note':             env_sustainability.get('methodology_note', ''),
        'overall_weights':              dict(w),
    }


def _compute_environmental_component_scores(lca_midpoints: Dict[str, float]) -> Dict[str, Any]:
    """Compute environmental component score and category scores (0-100, higher better) from LCA midpoints.

    v1 trim alignment: the consumed midpoint vector is now the 3 literature-anchored
    categories (Global warming, Land use, Water consumption). Previously this
    function weighted in Terrestrial acidification, Freshwater eutrophication,
    and Marine eutrophication; those keys are no longer present in `lca_midpoints`,
    so `.get(category, 0.0)` would silently return 0 for each, mechanically scoring
    them at the maximum 100 — boosting the headline environmental_score by the
    sum of the trimmed-category weights (0.3 of 1.0). Now: iterate only over the
    consumed-vector categories and re-normalise weights to sum to 1.0 across them,
    matching the same renormalisation that `LifeCycleAssessment.calculate_single_score`
    applies when Resources endpoint is None.
    """
    # Per-100-kcal normalisation maxima for the v1 trimmed midpoint set.
    # The pre-v1 maxima (GW=100, Land=200, Water=20) were calibrated for a
    # 6-category score where acidification + eutrophications carried the
    # lower-scoring share. After the v1 trim those 3 are gone, and the old
    # maxima were so generous that any real meal scored ~99.9/100 (a beef-only
    # meal trips at GW=5 kg CO2/100 kcal => score=95 with the old GW max=100;
    # a balanced meal hits GW=0.1 kg CO2/100 kcal => score=99.9). That's the
    # "silently inflated env_score" defect the e2e smoke caught. Retuned to
    # realistic worst-case per-100-kcal values from the LCA literature:
    #   GWP   : beef-heavy meal ~3-5 kg CO2 / 100 kcal (Stylianou 2021 SI Table 11B
    #           green/red zone thresholds at 0.32 / 0.61 kg CO2 / serving suggest
    #           that "high impact" sits ~1.5-5 kg / 100 kcal; use 5 as the
    #           full-scale max so a beef-heavy meal scores ~0 / 100).
    #   Land  : beef-heavy meal ~20-30 m2a / 100 kcal (P&N beef herd 164 m2a /
    #           100g protein x 0.20 / 200 kcal = 16 m2a / 100 kcal); use 30.
    #   Water : nut/almond-heavy meal ~1-2 m3 blue / 100 kcal; use 2.
    max_values = {
        'Global warming':    5.0,   # kg CO2 eq per 100 kcal (worst-case beef-heavy)
        'Land use':          30.0,  # m2a crop eq per 100 kcal (worst-case beef)
        'Water consumption': 2.0,   # m3 blue per 100 kcal (worst-case almonds)
    }
    weights = {
        'Global warming':    0.43,
        'Land use':          0.29,
        'Water consumption': 0.28,
    }

    category_scores: Dict[str, float] = {}
    weighted_sum = 0.0
    total_weight = 0.0

    for category, max_val in max_values.items():
        impact_val = float(lca_midpoints.get(category, 0.0) or 0.0)
        normalized = min(100.0, (impact_val / max_val) * 100.0) if max_val > 0 else 0.0
        score = max(0.0, 100.0 - normalized)
        category_scores[category] = score
        w = weights.get(category, 0.0)
        if w > 0:
            weighted_sum += score * w
            total_weight += w

    environmental_score = (weighted_sum / total_weight) if total_weight > 0 else 50.0

    return {
        'environmental_score': environmental_score,
        'category_scores': category_scores,
    }

def _estimate_processing_score(meal: EnvMeal) -> float:
    """Estimate a processing score (0-100, higher is better = less processed) heuristically.

    Uses food group heuristics as proxy for processing intensity when NOVA/FCS
    is unavailable.

    KNOWN LIMITATION: the per-group multipliers conflate animal-product impact
    with processing intensity (e.g. "Beef Products" is rated 0.55 even when
    the food is raw beef, which is NOVA-1 minimally-processed). The proxy
    therefore double-counts against the environmental score in the overall
    blend for animal-protein foods. A NOVA- or FCS-10-based score per food
    would resolve this; see code_action_items.md HENI-CODE-1 / FCS-CODE-1
    for ingredient-level processing scoring already implemented for HENI
    and FCS pipelines but not yet wired into this LCA path.
    """
    breakdown = meal.get_food_breakdown()
    if not breakdown:
        return 50.0

    # Assign processing quality multipliers (higher is better)
    group_multiplier = {
        # Minimally processed
        'Vegetables and Vegetable Products': 1.0,
        'Legumes and Legume Products': 0.95,
        'Fruits and fruit juices': 0.9,
        'Cereals, Grains and Pasta': 0.85,
        'Nuts and Seeds': 0.85,
        'Finfish and Shellfish Products': 0.8,
        # Moderate processing
        'Dairy and Egg Products': 0.7,
        'Poultry Products': 0.7,
        'Pork Products': 0.6,
        'Beef Products': 0.55,
        # Highly processed
        'Fast Foods': 0.3,
        'Sausages and Luncheon meats': 0.25,
        'Sweets': 0.25,
        'Snacks': 0.25,
        'Breakfast cereals': 0.4,
    }

    total_qty = sum(float(item.get('quantity', 0) or 0) for item in breakdown)
    if total_qty <= 0:
        return 50.0

    # Quantity-weighted average multiplier
    weighted = 0.0
    for item in breakdown:
        qty = float(item.get('quantity', 0) or 0)
        grp = str(item.get('group', ''))
        mult = group_multiplier.get(grp, 0.7)  # default moderate
        weighted += mult * qty

    avg_mult = weighted / total_qty
    # Convert multiplier in ~[0.25..1.0] to a 0-100 score linearly
    score = max(0.0, min(100.0, (avg_mult - 0.25) / (1.0 - 0.25) * 100.0))
    return score

@api_view(['POST'])
@permission_classes([AllowAny])
@seo_metadata(
    title="Compare Environmental Impact of Foods | DISH Research",
    description="Compare the environmental impact of multiple foods side-by-side with detailed analysis.",
    keywords="food comparison, environmental impact comparison, sustainability comparison"
)
def compare_foods_environmental(request):
    """
    Compare environmental impact of multiple individual foods.
    Input: List of foods with quantities
    Output: Side-by-side comparison with detailed explanations
    """
    try:
        foods_data = request.data.get('foods', [])
        user_type = request.data.get('user_type', 'individual')
        methodology = request.data.get('methodology', 'recipe2016')
        perspective = request.data.get('perspective', 'H')
        country = request.data.get('country')
        consumer_perspective = request.data.get('consumer_perspective', 'global')
        basis = request.data.get('basis', 'per_100_kcal')
        param_error = _validate_methodology_params(
            methodology, perspective, country, consumer_perspective, basis,
        )
        if param_error is not None:
            return Response(param_error, status=status.HTTP_400_BAD_REQUEST)

        if not foods_data or len(foods_data) < 2:
            return Response({
                "error": "Please provide at least 2 foods for comparison",
                "example": {
                    "foods": [
                        {"food_id": 2003, "quantity": 100, "name": "Chicken Breast"},
                        {"food_id": 3580, "quantity": 100, "name": "Black Beans"}
                    ],
                    "user_type": "individual"
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ensure CNF integrator is initialized similarly to the main endpoint
        cnf_integrator = get_cnf_integrator()
        if not cnf_integrator.is_initialized():
            cnf_integrator.initialize('raw_cnf')

        data_loader = EnvDataLoader()
        food_comparisons = []
        
        # Analyze each food individually
        for food_data in foods_data:
            try:
                food = EnvFood(
                    food_id=food_data['food_id'],
                    quantity=food_data['quantity'],
                    data_loader=data_loader,
                )

                # Build a single-food meal and run the same LCA/monetization flow used by the main endpoint
                single_meal = EnvMeal([food])
                lca = LifeCycleAssessment(
                    single_meal,
                    methodology=methodology,
                    perspective=perspective,
                    country=country,
                    consumer_perspective=consumer_perspective,
                    basis=basis,
                )
                lca_midpoints = lca.perform_lcia()
                lca_endpoints = lca.calculate_endpoint_impacts()
                lca_single_score = lca.calculate_single_score()

                # Monetization based on LCA midpoints
                item_monetization = Monetization(lca_midpoints, data_loader, country=country)
                item_total_cost = item_monetization.get_total_monetized_impact()

                # Align units with main analysis: use the same LCA outputs (per 100 kcal functional unit)
                # Do NOT re-normalize by weight here, to keep values consistent with the analysis view
                lca_midpoints_normalized = lca_midpoints
                lca_endpoints_normalized = lca_endpoints
                cost_total = item_total_cost

                # Sustainability score via the shared blended-score helper so the
                # comparison endpoint produces the SAME numeric score and rating
                # as the main `/environmental-impact/` endpoint for the same
                # food + quantity. Previously this used `food.get_sustainability_score()`
                # (env-only, group-default, no matcher) which made beans-lima
                # show 87/100 here but 68/100 in the main calculator panel.
                sustainability_block = _compose_blended_sustainability(single_meal, lca)
                sustainability_score = {
                    'overall': sustainability_block['overall_sustainability_score'],
                    **sustainability_block,
                }

                food_comparisons.append({
                    "food_info": {
                        "name": food.food_name,
                        "food_group": food.food_group,
                        "quantity": food_data['quantity'],
                        "food_id": food_data['food_id'],
                    },
                    # Backward-compatible summary metrics used by the UI
                    "environmental_impact_per_100g": {
                        "carbon_footprint": lca_midpoints_normalized.get('Global warming', 0.0),
                        "water_consumption": lca_midpoints_normalized.get('Water consumption', 0.0),
                        "land_use": lca_midpoints_normalized.get('Land use', 0.0),
                    },
                    "sustainability_score": sustainability_score.get('overall', 50),
                    # v1: also expose the harmonised rating + per-category zones
                    # so the comparison UI can render the same chips as the main
                    # analysis view (consistent with §3.x sustainability scoring).
                    "sustainability_rating":   sustainability_score.get('sustainability_rating', 'Unknown'),
                    "environmental_score":     sustainability_score.get('environmental_score'),
                    "environmental_rating":    sustainability_score.get('environmental_rating'),
                    "nutritional_score":       sustainability_score.get('nutritional_score'),
                    "processing_score":        sustainability_score.get('processing_score'),
                    "category_zones":          sustainability_score.get('category_zones', {}),
                    "overall_weights":         sustainability_score.get('overall_weights'),
                    # Keep legacy field name mapped to midpoint impacts per 100g
                    "all_impacts": lca_midpoints_normalized,
                    # Provide structured LCA outputs mirroring the comprehensive endpoint
                    "lca_per_100g": {
                        "midpoint_impacts": lca_midpoints_normalized,
                        "endpoint_impacts": lca_endpoints_normalized,
                        "single_score": lca_single_score,
                        # CODE-5: per-category confidence rating (additive).
                        "factor_confidence_by_category": lca.get_factor_confidence_by_category(),
                    },
                    # Monetization summary (total and per 100g) plus optional breakdowns
                    "monetization": {
                        "total_cost": cost_total,
                        "cost_per_100g": cost_total,
                        "cost_breakdown_by_category": item_monetization.get_cost_breakdown_by_category(),
                        "top_cost_drivers": item_monetization.get_top_cost_drivers(),
                        # CODE-4: per-category source attribution (additive).
                        "value_sources": item_monetization.get_monetary_value_sources(),
                    },
                    # Legacy convenience field retained for the existing UI mapping
                    "environmental_cost_per_100g": cost_total,
                })
                
            except Exception as e:
                food_comparisons.append({
                    "food_id": food_data['food_id'],
                    "error": f"Analysis failed: {str(e)}"
                })
        
        # Create comparison insights
        successful_comparisons = [fc for fc in food_comparisons if 'error' not in fc]
        if len(successful_comparisons) >= 2:
            comparison_insights = _generate_food_comparison_insights(successful_comparisons, user_type)
        else:
            comparison_insights = {"error": "Need at least 2 successful food analyses"}
        
        # Get explanations
        explanations = get_user_explanations(user_type)
        
        result = {
            "food_comparisons": food_comparisons,
            "comparison_insights": comparison_insights,
            "explanations": {
                "title": "🍎 Food Environmental Impact Comparison",
                "description": explanations["lca_results"]["detailed_explanation"],
                "comparison_explanation": "All impacts are shown per 100g for fair comparison between different foods.",
                "sustainability_explanation": "Sustainability scores (0-100) consider both environmental impact and nutritional value."
            },
            "metadata": {
                "user_type": user_type,
                "comparison_basis": "per 100g",
                "total_foods": len(foods_data)
            }
        }
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error in food comparison: {str(e)}")
        return Response({
            "error": "Food comparison failed",
            "help": "Please check that all food_id values exist in the database."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
@seo_metadata(
    title="Food Environmental Profile | EcoDish365", 
    description="Get detailed environmental profile for a specific food item.",
    keywords="food profile, environmental impact, sustainability profile"
)
def food_environmental_profile(request, food_id):
    """
    Get detailed environmental profile for a single food item.
    Provides comprehensive analysis including all impact categories.
    """
    try:
        user_type = request.GET.get('user_type', 'individual')
        quantity = float(request.GET.get('quantity', 100))  # Default 100g
        methodology = request.GET.get('methodology', 'recipe2016')
        perspective = request.GET.get('perspective', 'H')
        country = request.GET.get('country') or None
        consumer_perspective = request.GET.get('consumer_perspective', 'global')
        basis = request.GET.get('basis', 'per_100_kcal')
        param_error = _validate_methodology_params(
            methodology, perspective, country, consumer_perspective, basis,
        )
        if param_error is not None:
            return Response(param_error, status=status.HTTP_400_BAD_REQUEST)

        data_loader = EnvDataLoader()
        food = EnvFood(food_id=food_id, quantity=quantity, data_loader=data_loader)

        # Get comprehensive data
        environmental_impact = food.get_environmental_impact()

        # Create single-food meal for LCA analysis
        meal = EnvMeal([food])
        lca = LifeCycleAssessment(
            meal,
            methodology=methodology,
            perspective=perspective,
            country=country,
            consumer_perspective=consumer_perspective,
            basis=basis,
        )
        lca_results = lca.perform_lcia()

        # Sustainability score via the shared helper — same blend (env + nut +
        # processing at 50/30/20) and same rating bands as the main and
        # comparison endpoints. Previously this endpoint called
        # `food.get_sustainability_score()` directly (env-only, group-default,
        # no matcher), making it diverge from the other two endpoints.
        sustainability_block = _compose_blended_sustainability(meal, lca)
        sustainability_score = {
            'overall': sustainability_block['overall_sustainability_score'],
            **sustainability_block,
        }
        
        # Monetization (country-aware)
        monetization = Monetization(lca_results, data_loader, country=country)

        # Format based on user type
        explanations = get_user_explanations(user_type)
        
        profile = {
            "food_info": {
                "name": food.food_name,
                "food_group": food.food_group,
                "quantity_analyzed": f"{quantity}g",
                "food_id": food_id
            },
            "environmental_profile": {
                "explanation": explanations["lca_results"],
                "key_impacts": {
                    "carbon_footprint": {
                        "total": environmental_impact.get('Global warming', 0),
                        "per_100g": environmental_impact.get('Global warming', 0) / (quantity/100),
                        "unit": "kg CO₂-eq",
                        "rating": _get_carbon_rating(environmental_impact.get('Global warming', 0) / (quantity/100))
                    },
                    "water_consumption": {
                        "total": environmental_impact.get('Water consumption', 0),
                        "per_100g": environmental_impact.get('Water consumption', 0) / (quantity/100),
                        "unit": "m³",
                        "rating": _get_water_rating(environmental_impact.get('Water consumption', 0) / (quantity/100))
                    },
                    "land_use": {
                        "total": environmental_impact.get('Land use', 0),
                        "per_100g": environmental_impact.get('Land use', 0) / (quantity/100),
                        "unit": "m²a crop-eq",
                        "rating": _get_land_rating(environmental_impact.get('Land use', 0) / (quantity/100))
                    }
                },
                "all_impact_categories": {k: (v / (quantity/100)) if (quantity and quantity != 0) else 0.0 for k, v in environmental_impact.items()},
                "overall_rating": _get_overall_environmental_rating(environmental_impact, quantity)
            },
            "sustainability_assessment": {
                "explanation": "Sustainability score combines environmental impact with nutritional quality",
                "overall_score": sustainability_score.get('overall', 50),
                "rating": _get_sustainability_rating_text(sustainability_score.get('overall', 50)),
                "individual_scores": sustainability_score
            },
            "economic_impact": {
                "explanation": explanations["monetization"],
                "total_cost": monetization.get_total_monetized_impact(),
                "cost_per_100g": monetization.get_total_monetized_impact() / (quantity/100),
                "cost_per_calorie": monetization.calculate_cost_per_calorie(meal.calculate_total_calories()),
                "currency": "CAD",
                # CODE-4: per-category source attribution (additive).
                "value_sources": monetization.get_monetary_value_sources(),
            },
            # CODE-5: ReCiPe factor confidence + provenance for the listed impact
            # categories. Additive; existing consumers ignore unknown keys.
            "lca_quality": {
                "factor_confidence_by_category": lca.get_factor_confidence_by_category(),
                "data_quality": lca.get_data_quality_report(),
                # v1 'demote, don't perfect' uncertainty bands per consumed
                # midpoint and endpoint category. Mirrors the main endpoint shape.
                "midpoint_impacts_bands": lca.midpoint_impacts_bands,
                "endpoint_impacts_bands": lca.endpoint_impacts_bands,
            },
            "nutritional_context": {
                "calories_per_100g": meal.calculate_total_calories() / (quantity/100),
                "energy_density": meal.get_energy_density(),
                "food_group_typical_impact": _get_food_group_context(food.food_group)
            },
            "recommendations": _get_food_recommendations(food, sustainability_score.get('overall', 50), user_type)
        }
        
        return Response(profile)
        
    except ValueError as e:
        return Response({
            "error": "Food not found",
            "food_id": food_id,
            "help": "Please check that the food_id exists in our database."
        }, status=status.HTTP_404_NOT_FOUND)
    
    except Exception as e:
        logger.error(f"Error getting food profile for {food_id}: {str(e)}")
        return Response({
            "error": "Could not generate food profile",
            "food_id": food_id
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _generate_food_comparison_insights(comparisons: List[Dict], user_type: str) -> Dict[str, Any]:
    """Generate insights from food comparison analysis."""
    if not comparisons:
        return {}
    
    # Find best and worst performers
    best_carbon = min(comparisons, key=lambda x: x['environmental_impact_per_100g']['carbon_footprint'])
    worst_carbon = max(comparisons, key=lambda x: x['environmental_impact_per_100g']['carbon_footprint'])
    best_sustainability = max(comparisons, key=lambda x: x['sustainability_score'])
    worst_sustainability = min(comparisons, key=lambda x: x['sustainability_score'])
    
    # Guard against div-by-zero when the lowest carbon footprint is exactly 0
    # (matched-only meals with the v1 bands, or matcher rows that report 0 GW).
    lo_cf = float(best_carbon['environmental_impact_per_100g']['carbon_footprint'] or 0)
    hi_cf = float(worst_carbon['environmental_impact_per_100g']['carbon_footprint'] or 0)
    diff_str = (
        f"{hi_cf / lo_cf:.1f}x difference" if lo_cf > 0
        else "lowest = 0; ratio not estimable"
    )
    insights = {
        "winners": {
            "lowest_carbon_footprint": {
                "food": best_carbon['food_info']['name'],
                "value": f"{lo_cf:.2f} kg CO₂-eq per 100 kcal"
            },
            "most_sustainable": {
                "food": best_sustainability['food_info']['name'],
                "score": f"{best_sustainability['sustainability_score']:.0f}/100"
            }
        },
        "environmental_differences": {
            "carbon_footprint_range": {
                "lowest": lo_cf,
                "highest": hi_cf,
                "difference": diff_str,
            }
        },
        "key_takeaways": []
    }
    
    # Generate user-appropriate takeaways. Use the guarded diff_str / lo_cf
    # from above so divide-by-zero on a 0 lowest-carbon doesn't crash the
    # endpoint.
    ratio_text = f"{hi_cf / lo_cf:.1f}x" if lo_cf > 0 else "not estimable (lowest = 0)"
    if user_type == "individual":
        insights["key_takeaways"] = [
            f"🌱 {best_carbon['food_info']['name']} has the lowest carbon footprint",
            f"⭐ {best_sustainability['food_info']['name']} is the most sustainable overall",
            f"🔄 Swapping {worst_carbon['food_info']['name']} for {best_carbon['food_info']['name']} could reduce your environmental impact"
        ]
    elif user_type == "researcher":
        insights["key_takeaways"] = [
            f"Carbon footprint varies by {ratio_text} across compared foods",
            f"Sustainability scores range from {worst_sustainability['sustainability_score']:.0f} to {best_sustainability['sustainability_score']:.0f}",
            "Within-product spread can exceed between-product spread (P&N 2018 Fig. 3); cross-validate with primary LCI data before drawing causal conclusions",
        ]
    else:  # policy
        insights["key_takeaways"] = [
            f"Policy interventions could target high-impact foods like {worst_carbon['food_info']['name']}",
            f"Promoting {best_carbon['food_info']['name']} could reduce population-level environmental impact",
            "Results inform evidence-based dietary guidelines and environmental policies"
        ]
    
    return insights

def _get_carbon_rating(carbon_per_100g: float) -> Dict[str, str]:
    """Get carbon footprint rating."""
    if carbon_per_100g <= 0.5:
        return {"rating": "Excellent", "color": "green", "description": "Very low carbon footprint"}
    elif carbon_per_100g <= 2.0:
        return {"rating": "Good", "color": "lightgreen", "description": "Low carbon footprint"}
    elif carbon_per_100g <= 5.0:
        return {"rating": "Moderate", "color": "yellow", "description": "Moderate carbon footprint"}
    elif carbon_per_100g <= 10.0:
        return {"rating": "High", "color": "orange", "description": "High carbon footprint"}
    else:
        return {"rating": "Very High", "color": "red", "description": "Very high carbon footprint"}

def _get_water_rating(water_per_100g: float) -> Dict[str, str]:
    """Get water consumption rating.

    Thresholds recalibrated for the v1 water-value retune: cnf_integrator now
    ships M&H 2011/2012 BLUE-WATER-ONLY consumptive footprints (not the
    green+blue+grey total). Pre-retune thresholds (0.1 / 0.5 / 2.0 / 5.0) were
    calibrated against total-footprint magnitudes 10-30× higher; after the
    retune those bands would rate every food "Excellent" or "Good".
    New scale anchored on M&H blue-water typical values:
      veg ~0.006 / cereal ~0.025 / beef ~0.062 / nuts ~0.8 m³/100g (almonds extreme).
    """
    if water_per_100g <= 0.01:
        return {"rating": "Excellent", "color": "green", "description": "Very low blue-water use"}
    elif water_per_100g <= 0.05:
        return {"rating": "Good", "color": "lightgreen", "description": "Low blue-water use"}
    elif water_per_100g <= 0.20:
        return {"rating": "Moderate", "color": "yellow", "description": "Moderate blue-water use"}
    elif water_per_100g <= 1.00:
        return {"rating": "High", "color": "orange", "description": "High blue-water use"}
    else:
        return {"rating": "Very High", "color": "red", "description": "Very high blue-water use (e.g. tree nuts)"}

def _get_land_rating(land_per_100g: float) -> Dict[str, str]:
    """Get land use rating."""
    if land_per_100g <= 1.0:
        return {"rating": "Excellent", "color": "green", "description": "Very low land use"}
    elif land_per_100g <= 5.0:
        return {"rating": "Good", "color": "lightgreen", "description": "Low land use"}
    elif land_per_100g <= 20.0:
        return {"rating": "Moderate", "color": "yellow", "description": "Moderate land use"}
    elif land_per_100g <= 50.0:
        return {"rating": "High", "color": "orange", "description": "High land use"}
    else:
        return {"rating": "Very High", "color": "red", "description": "Very high land use"}

def _get_overall_environmental_rating(environmental_impact: Dict, quantity: float) -> Dict[str, str]:
    """Get overall environmental rating."""
    # Normalize impacts per 100g
    denom = (quantity/100) if quantity else None
    carbon = (environmental_impact.get('Global warming', 0) / denom) if denom else 0.0
    water = (environmental_impact.get('Water consumption', 0) / denom) if denom else 0.0
    land = (environmental_impact.get('Land use', 0) / denom) if denom else 0.0
    
    # Simple scoring based on thresholds. Water threshold recalibrated for
    # the M&H blue-water-only retune (was 0.5 m³/100g for total-footprint
    # values — too generous after the retune; everything would pass).
    score = 0
    if carbon <= 2.0: score += 1
    if water <= 0.05: score += 1
    if land <= 5.0: score += 1
    
    if score == 3:
        return {"rating": "Excellent", "color": "green", "description": "Low environmental impact across all categories"}
    elif score == 2:
        return {"rating": "Good", "color": "lightgreen", "description": "Good environmental performance"}
    elif score == 1:
        return {"rating": "Moderate", "color": "yellow", "description": "Moderate environmental impact"}
    else:
        return {"rating": "High Impact", "color": "orange", "description": "High environmental impact - consider alternatives"}

def _get_sustainability_rating_text(score: float) -> str:
    """Convert sustainability score to text rating.

    Bands harmonised with `LifeCycleAssessment._sustainability_rating` and
    `Meal._get_sustainability_rating` so the same score yields the same
    label everywhere. Previously this used non-aligned bands (>=70 "Very
    Good", >=60 "Good", >=50 "Fair") that made the comparison endpoint
    show "Fair" for foods the main endpoint rated "Good" / "Moderate".
    """
    if score >= 80: return "Excellent - Highly sustainable choice"
    if score >= 65: return "Good - Reasonably sustainable with room to improve"
    if score >= 50: return "Moderate - Mixed sustainability profile"
    if score >= 35: return "Poor - Significant sustainability issues"
    return "Very Poor - Major sustainability concerns"

def _get_food_group_context(food_group: str) -> str:
    """Get context about typical environmental impact for food group."""
    context = {
        "Vegetables and Vegetable Products": "Generally low environmental impact with high nutritional value",
        "Fruits and fruit juices": "Low to moderate impact, higher for out-of-season or imported fruits",
        "Beef Products": "Highest environmental impact due to methane emissions and land use",
        "Pork Products": "High impact but lower than beef, mainly from feed production",
        "Poultry Products": "Moderate impact, more efficient than red meat",
        "Dairy and Egg Products": "Moderate to high impact depending on production system",
        "Legumes and Legume Products": "Low impact and nitrogen-fixing benefits for soil",
        "Nuts and Seeds": "Moderate impact, high water use for some varieties",
        "Cereals, Grains and Pasta": "Low to moderate impact, varies by processing",
        "Fish and Shellfish Products": "Variable impact depending on fishing/farming methods"
    }
    return context.get(food_group, "Impact varies depending on production and processing methods")

def _get_food_recommendations(food, sustainability_score: float, user_type: str) -> List[str]:
    """Generate food-specific recommendations."""
    recommendations = []
    
    if user_type == "individual":
        if sustainability_score >= 70:
            recommendations.extend([
                "✅ Great choice! This food has good environmental performance",
                "💡 Share this sustainable choice with friends and family"
            ])
        elif sustainability_score >= 50:
            recommendations.extend([
                "👍 Decent choice with room for improvement",
                "🌱 Look for organic or local versions when possible"
            ])
        else:
            recommendations.extend([
                "🔄 Consider more sustainable alternatives",
                "📚 Learn about the environmental impact of your food choices"
            ])
        
        # Food group specific recommendations.
        # Note: removed prior "choose grass-fed beef" suggestion — per-kg GHG of
        # grass-fed beef is typically HIGHER than feedlot beef (longer growing
        # time, lower productivity; Poore & Nemecek 2018 Fig. 1), so that
        # advice was environmentally misleading.
        if food.food_group in ["Beef Products", "Lamb, Veal and Game"]:
            recommendations.append("🥩 Try smaller portions, or substitute with poultry, legumes, or fish for lower-impact protein")
        elif food.food_group in ["Vegetables and Vegetable Products", "Legumes and Legume Products"]:
            # Qualified — greenhouse / air-freighted produce can have ~5× field-grown GHG.
            recommendations.append("🌟 Generally low-impact; prefer in-season and field-grown to avoid hothouse / air-freight premiums")

    return recommendations


@api_view(['GET'])
@permission_classes([AllowAny])
def methodology_info(request):
    """List available LCA methodologies, perspectives, countries, and
    country-aware impact pathways. The frontend uses this to populate the
    Advanced methodology dropdowns without bundling the data client-side.
    """
    try:
        methodology = request.GET.get('methodology', 'recipe2016')
        if methodology not in list_available_methodologies():
            return Response({
                "error": f"Unknown methodology {methodology!r}.",
                "valid_methodologies": list_available_methodologies(),
            }, status=status.HTTP_400_BAD_REQUEST)
        pack = get_methodology_pack(methodology)
        return Response({
            "available_methodologies": list_available_methodologies(),
            "active_methodology": methodology,
            "active_methodology_version": pack.version_string(),
            "available_perspectives": pack.list_perspectives(),
            "available_consumer_perspectives": list(_VALID_CONSUMER_PERSPECTIVES),
            "available_countries": pack.list_countries(),
            "country_aware_pathways": pack.list_country_aware_pathways(),
            "country_aware_categories": pack.list_country_aware_categories(),
            "methodology_provenance": pack.methodology_provenance(),
            "perspective_descriptions": {
                "I": "Individualist — short timeframe (20 yr), optimistic; lower DALY/kg CO2.",
                "H": "Hierarchist — default 100 yr horizon (RIVM convention).",
                "E": "Egalitarian — long timeframe (1000 yr), pessimistic; ~13× higher GW DALY than H.",
            },
            "consumer_perspective_descriptions": {
                "global": "Use world-average endpoint CFs for every pathway (default; appropriate when food supply chains span multiple countries).",
                "national": "Substitute country-specific endpoint CFs where the workbook supports it (currently the three water-consumption pathways). Best for in-country produced + consumed analysis.",
            },
        })
    except Exception as exc:  # noqa: BLE001
        logger.error("methodology_info error: %s", exc, exc_info=True)
        return Response(
            {"error": "Failed to load methodology metadata.", "details": str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )