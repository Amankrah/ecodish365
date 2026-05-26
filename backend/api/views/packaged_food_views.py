"""API surface for packaged-food image extraction (PKG-IMG-1).

Two endpoints:

  POST /api/packaged-food/extract/
    multipart upload of one image → strict NFPanelExtraction JSON.
    Cost: 1¢ per extraction (cache hits free). Rate-limited via the
    same per-IP / monthly circuit breaker that gates all AI endpoints.

  POST /api/hsr/calculate-from-panel/
    JSON body: { panel, category, consumed_portion_grams?, user_type? }
    → HSR result with audience-aware explanation + extraction provenance.
    Cost: 0¢ (no LLM call; pure HSR math).

The frontend's typical 2-step flow:
  1. Camera/upload → extract → render prefilled editable form.
  2. User confirms (possibly edits) → calculate-from-panel → render HSR result.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.services.packaged_food_extractor import (
    extract_nf_panel,
    extract_packaged_food,
    CACHE_TTL_SECONDS,
)
from api.services.multimodal_client import ImageDecodeError, MAX_UPLOAD_BYTES
from api.services.packaged_food_schema import (
    NFPanelExtraction,
    PackagedFoodExtraction,
    IngredientListExtraction,
)
from api.services.ingredient_to_cnf_decomposer import decompose_packaged_food
from api.views.cnf_ai_search_views import _enforce_rate_limit


logger = logging.getLogger(__name__)


# Cost override for the multimodal call (each call ~$0.005 at gpt-4o-mini
# vision pricing; we round up to 1¢ for the rate-limiter budget). Cache
# hits cost 0¢ — we still count them against the per-IP hourly limit (30/hr)
# but not against the monthly budget.
_PKG_FOOD_EXTRACT_COST_CENTS = 1


@api_view(['POST'])
@permission_classes([AllowAny])
def packaged_food_extract(request):
    """Multipart image upload → strict NFPanelExtraction.

    Request:
      multipart/form-data with field 'image' = binary file
      (optional) form field 'target' = 'hsr' (default; only 'hsr' supported in v1)

    Response 200:
      The NFPanelExtraction JSON. Frontend uses this to prefill the editable
      confirmation form. `extraction_succeeded=false` is still a 200 — the
      frontend reads the flag to render an empty/retry state.

    Errors:
      400 invalid_image  — bytes failed to decode (corrupt / unsupported)
      400 image_too_large — over MAX_UPLOAD_BYTES
      400 missing_image  — no 'image' field
      429 rate_limit     — per-IP hourly limit reached
      503 circuit_breaker — monthly LLM budget exhausted
      503 llm_unavailable — no API key configured
    """
    image_file = request.FILES.get('image')
    if image_file is None:
        return Response({
            'success': False,
            'error': 'missing_image',
            'message': 'Field "image" (multipart/form-data) is required.',
        }, status=status.HTTP_400_BAD_REQUEST)

    target = str(request.data.get('target', 'hsr')).lower()
    if target not in ('hsr',):
        target = 'hsr'  # v1: silently coerce, Phase 2 will add 'ingredients'

    # Read into memory once (DRF chunks for us up to MAX_UPLOAD_BYTES).
    try:
        image_bytes = image_file.read()
    except Exception as exc:  # noqa: BLE001
        logger.exception("pkg-food: failed to read upload")
        return Response({
            'success': False,
            'error': 'upload_read_failed',
            'message': f'Could not read uploaded file: {exc}',
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(image_bytes) == 0:
        return Response({
            'success': False,
            'error': 'empty_upload',
            'message': 'Uploaded file is empty.',
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        return Response({
            'success': False,
            'error': 'image_too_large',
            'message': f'Image exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Rate limit (cache-hit-aware: we don't know yet whether this will hit
    # cache, so we charge optimistically — refunding cache hits would
    # require splitting the rate limiter into reserve + commit, which is
    # over-engineered for v1).
    rate_err = _enforce_rate_limit(
        request, kind='search',
        cost_override_cents=_PKG_FOOD_EXTRACT_COST_CENTS,
    )
    if rate_err is not None:
        return rate_err

    # Run extraction.
    try:
        result = extract_nf_panel(image_bytes, target=target)
    except ImageDecodeError as exc:
        return Response({
            'success': False,
            'error': 'invalid_image',
            'message': str(exc),
        }, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as exc:
        logger.error("pkg-food extract: %s", exc)
        return Response({
            'success': False,
            'error': 'llm_unavailable',
            'message': str(exc),
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:  # noqa: BLE001
        logger.exception("pkg-food extract: unexpected failure")
        return Response({
            'success': False,
            'error': 'extraction_failed',
            'message': f'Unexpected extraction error: {exc!r}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'success': True,
        'extraction': result.extraction.model_dump(),
        'cache_hit': result.cache_hit,
        'cache_ttl_seconds': CACHE_TTL_SECONDS,
    })


# ----------------------------------------------------------------------
# HSR-from-panel view: bridges extracted NF panel → existing HSR engine
# ----------------------------------------------------------------------

# CNF nutrient-name keys expected by HSRFood.nutrients (per
# hsr_calculator.hsr.constants.nutrients.NUTRIENTS_TO_REPORT). We populate
# these from the panel's per-serving column so the existing HSR pipeline
# works without any math change.
_HSR_NUTRIENT_KEYS = {
    'PROTEIN': 'protein_g',
    'FAT (TOTAL LIPIDS)': 'fat_total_g',
    'CARBOHYDRATE, TOTAL (BY DIFFERENCE)': 'carbohydrate_total_g',
    'ENERGY (KILOCALORIES)': 'energy_kcal',
    'ENERGY (KILOJOULES)': 'energy_kj',
    'SUGARS, TOTAL': 'sugars_total_g',
    'FIBRE, TOTAL DIETARY': 'fibre_g',
    'CALCIUM': 'calcium_mg',
    'SODIUM': 'sodium_mg',
    'FATTY ACIDS, SATURATED, TOTAL': 'fat_sat_g',
}


def _panel_to_hsr_nutrients(panel_per_serving: Dict[str, Any]) -> Dict[str, float]:
    """Convert NFPanelExtraction.per_serving (dict form) into the
    {nutrient_name_upper: value} shape HSRFood expects.

    Returns ONLY the nutrients with a numeric value; missing fields are
    omitted so HSR's _calculate_weighted_sum defaults them to 0.
    """
    out: Dict[str, float] = {}
    for hsr_key, panel_key in _HSR_NUTRIENT_KEYS.items():
        field = panel_per_serving.get(panel_key) or {}
        v = field.get('value')
        if v is None:
            continue
        try:
            out[hsr_key] = float(v)
        except (TypeError, ValueError):
            continue
    return out


@api_view(['POST'])
@permission_classes([AllowAny])
def hsr_calculate_from_panel(request):
    """Compute HSR from a (user-confirmed) NF panel JSON + category.

    Request body:
      {
        "panel": { ... NFPanelExtraction.model_dump() ... },
        "category": "1" | "1D" | "2" | "2D" | "3" | "3D",   // user's final choice
        "consumed_portion_grams": null | number,            // optional; default = serving_size
        "fvnl_percent": null | number,                      // optional; user-supplied 0-100
        "user_type": "individual" | "researcher" | "policy" // optional; default 'individual'
      }

    Response 200:
      {
        "success": true,
        "hsr_result": { ... existing HSR result shape ... },
        "explanations": { ... audience-aware HSR explanation pack ... },
        "provenance": {
          "extraction_source": "llm_vision",
          "model": "...", "image_sha256": "...",
          "user_type": "...", "edited_fields": [...],
          "confirmed_at": "ISO timestamp"
        }
      }

    Errors:
      400 invalid_request — missing/malformed panel, category, or critical fields
    """
    import datetime as _dt
    from hsr_calculator.hsr.models.food import Food as HSRFood
    from hsr_calculator.hsr.models.meal import Meal as HSRMeal
    from hsr_calculator.hsr.models.category import Category
    from hsr_calculator.hsr.calculators.hsr_calculator import (
        HSRCalculator, HSRConfig,
    )
    from api.views.hsr_explanations import get_explanations as get_hsr_explanations

    body = request.data
    panel_data = body.get('panel')
    category_str = str(body.get('category', '2'))
    consumed_g = body.get('consumed_portion_grams')
    fvnl_percent = body.get('fvnl_percent')
    user_type = str(body.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    if not isinstance(panel_data, dict):
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': 'Field "panel" must be the NFPanelExtraction object from /api/packaged-food/extract/.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Validate the panel via the canonical schema. Drops unexpected fields,
    # surfaces structured errors.
    try:
        panel = NFPanelExtraction.model_validate(panel_data)
    except Exception as exc:  # noqa: BLE001
        return Response({
            'success': False, 'error': 'invalid_panel',
            'message': f'Panel did not validate against NFPanelExtraction schema: {exc}',
        }, status=status.HTTP_400_BAD_REQUEST)

    if not panel.extraction_succeeded:
        return Response({
            'success': False, 'error': 'panel_extraction_failed',
            'message': f'Cannot score: {panel.failure_reason}',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Determine serving size in grams (HSR engine works on grams).
    panel_serving_value = panel.serving_size.value
    panel_serving_unit = (panel.serving_size.unit or '').lower()
    if panel_serving_value is None:
        return Response({
            'success': False, 'error': 'missing_serving_size',
            'message': 'Panel serving_size.value is required to compute HSR.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # ml→g: assume density 1.0 for water-based liquids. The frontend can
    # show a density-override field; for v1 we accept 1:1 with a metadata note.
    serving_grams = float(panel_serving_value)
    if panel_serving_unit in ('ml', 'milliliter', 'milliliters', 'millilitre', 'millilitres'):
        ml_to_g_assumption = True
    else:
        ml_to_g_assumption = False

    # Consumed-portion handles "how much did the user actually eat?". HSR
    # itself is per-100g and portion-independent, so this is informational
    # only — passed through to the response, not into the HSR calculation.
    if consumed_g is not None:
        try:
            consumed_grams = float(consumed_g)
        except (TypeError, ValueError):
            consumed_grams = serving_grams
    else:
        consumed_grams = serving_grams

    # Parse HSR category.
    try:
        cat = Category(category_str)
    except ValueError:
        return Response({
            'success': False, 'error': 'invalid_category',
            'message': f'category must be one of {[c.value for c in Category]}; got {category_str!r}.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Build HSRFood from the panel.
    per_serving_dict = panel.per_serving.model_dump()
    nutrients = _panel_to_hsr_nutrients(per_serving_dict)

    if not nutrients:
        return Response({
            'success': False, 'error': 'no_nutrients',
            'message': 'Panel per-serving block has no usable nutrient values.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # FVNL: user-supplied for packaged foods (the panel doesn't disclose it).
    try:
        fvnl_pct = float(fvnl_percent) if fvnl_percent is not None else 0.0
    except (TypeError, ValueError):
        fvnl_pct = 0.0
    fvnl_pct = max(0.0, min(100.0, fvnl_pct))

    food_name = (panel.product_name_visible.value or 'Unknown packaged food')

    food = HSRFood(
        food_id=0,  # 0 = synthetic / non-CNF; HSR engine doesn't require a valid ID
        food_name=food_name,
        serving_size=serving_grams,
        nutrients=nutrients,
        fvnl_percent=fvnl_pct,
        category=cat,  # explicit; bypasses auto-assignment
    )
    # Set category metadata fields that __post_init__ would normally set
    # (skipped when category is supplied at construction time).
    food.category_confidence = 1.0
    food.category_source = "user_confirmed_from_image"

    meal = HSRMeal(foods=[food])
    meal.category = cat  # ensure mealcategorizer doesn't override our user choice

    cfg = HSRConfig(
        use_scientific_thresholds=False,
        differentiate_sugar_sources=False,
        apply_satiety_adjustments=False,
        use_unified_energy_approach=False,
        consider_processing_level=False,
        include_confidence_metrics=True,
        detailed_explanations=True,
    )
    calculator = HSRCalculator(meal, cfg)
    hsr_result_obj = calculator.calculate_hsr()
    # HSRResult dataclass has flat fields (no .rating sub-object).
    # See hsr_calculator/hsr/models/hsr_result.py.
    hsr_result = {
        'star_rating': hsr_result_obj.star_rating,
        'category': cat.value,
        'baseline_points': hsr_result_obj.component_score.baseline_points,
        'modifying_points': hsr_result_obj.component_score.modifying_points,
        'final_score': hsr_result_obj.component_score.final_score,
        'level': hsr_result_obj.level.value if hsr_result_obj.level else None,
    }

    explanations = get_hsr_explanations(
        star_rating=float(hsr_result['star_rating']),
        category=cat.value,
        user_type=user_type,
    )

    # Compose provenance block. The frontend can compute `edited_fields`
    # by diffing the form against the original extraction; for now we
    # report what we know server-side.
    extraction_meta = panel.extraction_metadata
    provenance = {
        'extraction_source': 'llm_vision',
        'model': extraction_meta.model,
        'provider': extraction_meta.provider,
        'prompt_version': extraction_meta.prompt_version,
        'schema_version': extraction_meta.schema_version,
        'image_sha256': extraction_meta.image_sha256,
        'extracted_at': extraction_meta.extracted_at,
        'confirmed_at': _dt.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'user_type': user_type,
        'category_source': food.category_source,
        'ml_to_g_assumption': ml_to_g_assumption,
        'serving_size_grams': serving_grams,
        'consumed_portion_grams': consumed_grams,
        'fvnl_percent_supplied_by_user': fvnl_percent is not None,
        'extraction_warnings': extraction_meta.extraction_warnings,
        'sanity_guard_rejections': extraction_meta.sanity_guard_rejections,
    }

    # Result notes: nutrient drivers + interpretive caveats. These surface
    # on the result page so users see WHY they got the score they got and
    # which product-specific gotchas (condensed soup, fruit/veg-heavy panel)
    # might change the interpretation. Computed here rather than client-side
    # so the rules stay version-controlled.
    result_notes = _build_result_notes(
        panel=panel, category=cat, hsr_stars=float(hsr_result['star_rating']),
        nutrients=nutrients, serving_grams=serving_grams,
        ml_unit_used=ml_to_g_assumption, fvnl_pct=fvnl_pct,
    )

    return Response({
        'success': True,
        'hsr_result': hsr_result,
        'explanations': explanations,
        'provenance': provenance,
        'result_notes': result_notes,
        'user_type': user_type,
    })


# ----------------------------------------------------------------------
# Result-notes: drivers + interpretive caveats specific to this product
# ----------------------------------------------------------------------

def _build_result_notes(
    *, panel: NFPanelExtraction, category, hsr_stars: float,
    nutrients: Dict[str, float], serving_grams: float,
    ml_unit_used: bool, fvnl_pct: float,
) -> Dict[str, Any]:
    """Compute per-100g/per-serving signals so the UI can explain the score.

    `drivers`   list of {kind: 'baseline_high' | 'baseline_low' | 'modifying_good',
                         nutrient, value, unit, per_100, threshold_phrase, severity}
    `notes`     list of {kind: 'condensed_product' | 'fvnl_hint' | 'ml_to_g',
                         severity: 'info' | 'warn', message, suggestion}
    The frontend renders these as callout cards.
    """
    drivers: List[Dict[str, Any]] = []
    notes: List[Dict[str, Any]] = []
    serving_unit = (panel.serving_size.unit or 'g').lower()

    # --- Driver thresholds (per 100 g/mL of product, HSR-domain rules of thumb) ---
    # These are NOT the HSR baseline-point breakpoints (those are version-controlled
    # in rust_core); they are honest user-facing thresholds for "high in X" callouts
    # informed by Canadian/Australian regulatory % DV bands (≥15% of DV per serving
    # = "high"; ≤5% per serving = "low"). We work per-serving since that's what the
    # label discloses directly.

    def _per_100(value: float) -> float:
        if serving_grams <= 0:
            return 0.0
        return value * 100.0 / serving_grams

    def push_driver(kind: str, key: str, value: float, unit: str,
                    threshold_phrase: str, severity: str) -> None:
        drivers.append({
            'kind': kind, 'nutrient': key, 'value': value, 'unit': unit,
            'value_per_100': round(_per_100(value), 1),
            'unit_per_100': f'{unit}/100{serving_unit}',
            'threshold_phrase': threshold_phrase, 'severity': severity,
        })

    sodium = nutrients.get('SODIUM', 0.0)
    if sodium >= 600:
        push_driver('baseline_high', 'sodium', sodium, 'mg',
                    f'High in sodium ({sodium:.0f} mg/serving — Health Canada labels '
                    f'≥15% Daily Value (i.e. ≥345 mg) as "a lot")',
                    'high')
    elif sodium >= 345:
        push_driver('baseline_high', 'sodium', sodium, 'mg',
                    f'Moderate in sodium ({sodium:.0f} mg/serving)', 'moderate')

    sat_fat = nutrients.get('FATTY ACIDS, SATURATED, TOTAL', 0.0)
    if sat_fat >= 5:
        push_driver('baseline_high', 'saturated_fat', sat_fat, 'g',
                    f'High in saturated fat ({sat_fat:.1f} g/serving)', 'high')

    sugars = nutrients.get('SUGARS, TOTAL', 0.0)
    if sugars >= 15:
        push_driver('baseline_high', 'sugars', sugars, 'g',
                    f'High in total sugars ({sugars:.0f} g/serving — '
                    f'Health Canada labels ≥15 g as "a lot")', 'high')
    elif sugars >= 5:
        push_driver('baseline_high', 'sugars', sugars, 'g',
                    f'Moderate in sugars ({sugars:.0f} g/serving)', 'moderate')

    fibre = nutrients.get('FIBRE, TOTAL DIETARY', 0.0)
    if fibre >= 4:
        push_driver('modifying_good', 'fibre', fibre, 'g',
                    f'Good source of fibre ({fibre:.0f} g/serving — '
                    f'≥4 g per serving qualifies as "source of" per Canadian rules)',
                    'good')

    protein = nutrients.get('PROTEIN', 0.0)
    if protein >= 10:
        push_driver('modifying_good', 'protein', protein, 'g',
                    f'High in protein ({protein:.0f} g/serving)', 'good')
    elif protein >= 5:
        push_driver('modifying_good', 'protein', protein, 'g',
                    f'Moderate protein ({protein:.0f} g/serving)', 'moderate')

    energy_kcal = nutrients.get('ENERGY (KILOCALORIES)', 0.0)
    if energy_kcal >= 500:
        push_driver('baseline_high', 'energy', energy_kcal, 'kcal',
                    f'Energy-dense ({energy_kcal:.0f} kcal/serving)', 'high')

    # --- Interpretive notes ---

    # 1. Condensed-product detection. Strong signal: product name or
    #    serving raw_text contains "condensed" / "concentré" (FR equivalent).
    product_text = ' '.join(filter(None, [
        (panel.product_name_visible.value or ''),
        (panel.brand_visible.value or ''),
        (panel.serving_size.raw_text or ''),
    ])).lower()
    is_condensed = any(tok in product_text for tok in (
        'condensed', 'concentré', 'concentre', 'concentrate',
    ))
    if is_condensed:
        notes.append({
            'kind': 'condensed_product',
            'severity': 'warn',
            'title': 'Label values are for the CONCENTRATED product',
            'message': (
                'This product\'s nutrition panel reports values for the '
                'concentrated/condensed form on the shelf, not the as-prepared '
                'serving you actually eat after diluting with water or milk. '
                'Per-100 mL sodium, sugars and energy in the final bowl will be '
                'roughly half the values shown here (depending on the dilution '
                'ratio in the prep instructions). The Health Star Rating '
                'computed here answers "how nutritious is the can?", not '
                '"how nutritious is the soup I\'ll actually consume?"'
            ),
            'suggestion': (
                'For the as-prepared rating, halve sodium, sugars and energy '
                'in the form and re-score, OR refer to the on-pack rating if '
                'the manufacturer publishes one for the prepared product.'
            ),
        })

    # 2. FVNL hint. Heuristic: when the user supplied FVNL=0 but the product
    #    name strongly suggests fruit/vegetable/legume/nut content, suggest a
    #    revised estimate. This is a UI-side hint — the score itself respects
    #    whatever the user typed.
    if fvnl_pct < 5:
        fvnl_keywords = {
            'tomato': ('tomato-based products', 40, 60),
            'tomate': ('tomato-based products', 40, 60),
            'vegetable soup': ('vegetable-based soups', 40, 60),
            'minestrone': ('vegetable-based soups', 50, 70),
            'lentil': ('legume-based products', 30, 60),
            'bean': ('legume-based products', 30, 60),
            'chickpea': ('legume-based products', 30, 60),
            'pois chiche': ('legume-based products', 30, 60),
            'fruit': ('fruit-based products', 50, 95),
            'salsa': ('salsa / tomato-based', 60, 80),
            'guacamole': ('avocado-based', 70, 90),
            'hummus': ('chickpea-based', 50, 70),
            'pesto': ('basil + nut based', 40, 60),
            'almond': ('nut products', 90, 100),
            'peanut': ('nut products', 90, 100),
            'cashew': ('nut products', 90, 100),
        }
        for keyword, (display, lo, hi) in fvnl_keywords.items():
            if keyword in product_text:
                notes.append({
                    'kind': 'fvnl_hint',
                    'severity': 'info',
                    'title': f'FVNL is set to {fvnl_pct:.0f}% — likely too low for this product',
                    'message': (
                        f'HSR awards bonus points for fruit/vegetable/nut/legume content. '
                        f'You set FVNL = {fvnl_pct:.0f}%, but the product name suggests '
                        f'{display}, which typically have {lo}–{hi}% F+V+N+L content by '
                        f'mass (look at the ingredient list — the first few ingredients '
                        f'by descending mass-order tell you the dominant components). '
                        f'Try setting FVNL ≈ {(lo + hi) // 2}% and re-scoring; the star '
                        f'rating could rise by 0.5–1.5 stars.'
                    ),
                    'suggestion': (
                        f'Click "Scan another" to re-score with a corrected FVNL estimate, '
                        f'or just remember: this {hsr_stars:.1f}-star rating assumes the '
                        f'product contains 0% fruit/veg/nuts/legumes.'
                    ),
                })
                break  # only one FVNL hint per result

    # 3. ml→g density assumption — only worth flagging when sodium > 100 mg
    #    (because for low-sodium watery products the density-1.0 assumption
    #    is very accurate; for cream-based or fat-heavy products it's less so).
    if ml_unit_used and sodium > 100:
        notes.append({
            'kind': 'ml_to_g',
            'severity': 'info',
            'title': 'Liquid serving converted to grams via density = 1.0',
            'message': (
                f'Your serving size was given in millilitres ({serving_grams:.0f} mL). '
                f'HSR works per 100 g of product, so we treated 100 mL ≈ 100 g '
                f'(density assumption = 1.0). This is accurate for water-based '
                f'drinks and broths but slightly off (typically ±5–10%) for cream- '
                f'or fat-heavy liquids. Star ratings rarely shift by more than a '
                f'half-star under realistic density corrections.'
            ),
            'suggestion': '',
        })

    return {'drivers': drivers, 'notes': notes}


# =======================================================================
# PKG-IMG-1 Phase 2 (2026-05-26) — adaptive extract + ingredient decompose
# =======================================================================
# Phase 1's /api/packaged-food/extract/ still works for HSR-only callers.
# Phase 2 adds:
#   POST /api/packaged-food/extract-combined/  — adaptive: NF + ingredients
#   POST /api/packaged-food/decompose-ingredients/  — text-only LLM decomposes
#                                                     into CNF-mapped composition
# The combined extract endpoint costs 1¢ (same multimodal call as Phase 1
# but with the heavier prompt). Decompose costs 2¢ (text-only LLM call;
# slightly more expensive token-wise because it has to reason about candidates
# and macro reconciliation).

_PKG_FOOD_EXTRACT_COMBINED_COST_CENTS = 1  # same multimodal call, heavier prompt
_PKG_FOOD_DECOMPOSE_COST_CENTS = 2          # text-only LLM, larger reasoning load


@api_view(['POST'])
@permission_classes([AllowAny])
def packaged_food_extract_combined(request):
    """Adaptive multipart image upload → NF panel + ingredient list extraction.

    Same multipart contract as `/api/packaged-food/extract/` (Phase 1) but
    returns the unified `PackagedFoodExtraction` wrapper with either or
    both pieces populated. Frontend reads `has_nf_panel` and
    `has_ingredient_list` to route the user appropriately.

    Response 200:
      {
        "success": true,
        "extraction": { ... PackagedFoodExtraction.model_dump() ... },
        "cache_hit": bool,
        "cache_ttl_seconds": int
      }
    """
    image_file = request.FILES.get('image')
    if image_file is None:
        return Response({
            'success': False, 'error': 'missing_image',
            'message': 'Field "image" (multipart/form-data) is required.',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        image_bytes = image_file.read()
    except Exception as exc:  # noqa: BLE001
        logger.exception("pkg-food combined: failed to read upload")
        return Response({
            'success': False, 'error': 'upload_read_failed',
            'message': f'Could not read uploaded file: {exc}',
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(image_bytes) == 0:
        return Response({
            'success': False, 'error': 'empty_upload',
            'message': 'Uploaded file is empty.',
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(image_bytes) > MAX_UPLOAD_BYTES:
        return Response({
            'success': False, 'error': 'image_too_large',
            'message': f'Image exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB.',
        }, status=status.HTTP_400_BAD_REQUEST)

    rate_err = _enforce_rate_limit(
        request, kind='search',
        cost_override_cents=_PKG_FOOD_EXTRACT_COMBINED_COST_CENTS,
    )
    if rate_err is not None:
        return rate_err

    try:
        result = extract_packaged_food(image_bytes)
    except ImageDecodeError as exc:
        return Response({
            'success': False, 'error': 'invalid_image', 'message': str(exc),
        }, status=status.HTTP_400_BAD_REQUEST)
    except RuntimeError as exc:
        logger.error("pkg-food combined: %s", exc)
        return Response({
            'success': False, 'error': 'llm_unavailable', 'message': str(exc),
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:  # noqa: BLE001
        logger.exception("pkg-food combined: unexpected failure")
        return Response({
            'success': False, 'error': 'extraction_failed',
            'message': f'Unexpected extraction error: {exc!r}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'success': True,
        'extraction': result.extraction.model_dump(),
        'cache_hit': result.cache_hit,
        'cache_ttl_seconds': CACHE_TTL_SECONDS,
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def packaged_food_decompose_ingredients(request):
    """Ingredient list (+ NF panel) → CNF-mapped composition.

    Request body JSON:
      {
        "nf_panel":        { ... NFPanelExtraction.model_dump() ... },
        "ingredient_list": { ... IngredientListExtraction.model_dump() ... }
      }

    Response 200:
      {
        "success": true,
        "decomposition": { ... DecompositionResult.model_dump() ... }
      }

    The decomposition is INFERRED, not measured. Regulation only requires
    descending-mass-order, not percentages. Frontend should surface the
    `decomposition_confidence` field prominently and let the user edit the
    masses in the composition table before scoring.
    """
    body = request.data
    nf_data = body.get('nf_panel')
    ing_data = body.get('ingredient_list')

    if not isinstance(nf_data, dict):
        return Response({
            'success': False, 'error': 'missing_nf_panel',
            'message': 'Field "nf_panel" is required (user-confirmed NF panel JSON).',
        }, status=status.HTTP_400_BAD_REQUEST)
    if not isinstance(ing_data, dict):
        return Response({
            'success': False, 'error': 'missing_ingredient_list',
            'message': 'Field "ingredient_list" is required (user-confirmed ingredient JSON).',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        panel = NFPanelExtraction.model_validate(nf_data)
    except Exception as exc:  # noqa: BLE001
        return Response({
            'success': False, 'error': 'invalid_nf_panel', 'message': f'{exc}',
        }, status=status.HTTP_400_BAD_REQUEST)
    try:
        ingredients = IngredientListExtraction.model_validate(ing_data)
    except Exception as exc:  # noqa: BLE001
        return Response({
            'success': False, 'error': 'invalid_ingredient_list', 'message': f'{exc}',
        }, status=status.HTTP_400_BAD_REQUEST)

    rate_err = _enforce_rate_limit(
        request, kind='decompose',
        cost_override_cents=_PKG_FOOD_DECOMPOSE_COST_CENTS,
    )
    if rate_err is not None:
        return rate_err

    try:
        result = decompose_packaged_food(panel=panel, ingredients=ingredients)
    except RuntimeError as exc:
        logger.error("pkg-food decompose: %s", exc)
        return Response({
            'success': False, 'error': 'llm_unavailable', 'message': str(exc),
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:  # noqa: BLE001
        logger.exception("pkg-food decompose: unexpected failure")
        return Response({
            'success': False, 'error': 'decomposition_failed',
            'message': f'Unexpected error: {exc!r}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response({
        'success': True,
        'decomposition': result.model_dump(),
    })
