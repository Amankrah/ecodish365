"""AI-enhanced CNF search + recipe decomposer endpoints (AI-MATCH-1).

Two endpoints, both gated by a shared per-IP rate limit and a global monthly
spend circuit breaker:

  POST /api/cnf/search/ai-enhanced
       body: {query: str, top_k?: int, user_type?: 'individual'|'researcher'|'policy'}
       returns: CNFMatchResult.to_dict() + {used_ai_ranking, cache_hit}

  POST /api/recipes/decompose                       (Phase 8)
       body: {dish_name: str, total_mass_g: float, user_type?: str}
       returns: CNFDecomposedRecipe.to_dict()

Rate limit:
  - Per-IP: ``settings.AI_SEARCH_PER_IP_HOURLY`` (default 50/hr)
  - Decompose calls count as 5× a search against this budget (two-stage LLM)

Circuit breaker:
  - Global monthly spend: ``settings.AI_SEARCH_MONTHLY_BUDGET_CENTS`` (default 5000 ¢ = $50)
  - When exceeded → HTTP 503 with a clear "AI search temporarily unavailable"
    message until the next month-boundary cron reset.

Audience-aware (AUDIENCE-CODE-1):
  - Individual mode hides the LLM `justification` field
  - Researcher / policy modes see everything
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from django.conf import settings
from django.core.cache import cache
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

logger = logging.getLogger(__name__)


# Cost model (cents per call). Tuned to gpt-4.1-mini at $0.15 / $0.60 per 1M.
# Single-query LLM rank: ~1k prompt + 50 output tokens ≈ 0.18 ¢ → round 0.1 ¢.
# Recipe decompose: 2 LLM calls per ingredient × ~5 ingredients ≈ 0.5 ¢.
# Recall-24h: up to 6 decomposes per recall → 30 tokens, capped to 30¢.
_COST_SEARCH_CENTS = 1                # in 0.1¢ units → 0.1¢
_COST_DECOMPOSE_CENTS = 5             # 0.5¢
_COST_RECALL_24H_PER_MEAL_CENTS = 5   # same as decompose; recall composes them
_COST_RECALL_24H_CAP_CENTS = 30       # hard ceiling regardless of meal count


def _client_ip(request) -> str:
    """Best-effort client IP for rate limiting."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _enforce_rate_limit(
    request, kind: str = 'search', *, cost_override_cents: int = 0,
) -> 'Response | None':
    """Per-IP hourly token bucket + monthly global circuit breaker.

    Returns None on success, or a Response (429 / 503) to short-circuit the
    view. Uses Django's cache framework (works with both local-memory and
    Redis backends).

    ``cost_override_cents`` lets variable-cost endpoints (recall-24h, where
    cost scales with the meal count) override the default per-kind cost.
    """
    per_ip_limit = int(getattr(settings, 'AI_SEARCH_PER_IP_HOURLY', 50))
    monthly_budget_cents = int(getattr(settings, 'AI_SEARCH_MONTHLY_BUDGET_CENTS', 5000))

    # --- Monthly circuit breaker (global) ---
    month_key = 'ai_search_monthly_spend_cents:' + datetime.utcnow().strftime('%Y-%m')
    spent = int(cache.get(month_key, 0) or 0)
    if spent >= monthly_budget_cents:
        logger.warning('AI search circuit-breaker tripped: spent=%d¢ ≥ budget=%d¢ for %s',
                       spent, monthly_budget_cents, month_key)
        return Response({
            'success': False,
            'error': 'circuit_breaker',
            'message': ('AI search is temporarily unavailable: this month\'s LLM '
                        'budget has been reached. Falls back to basic search.'),
            'reset_at': month_key + '-01T00:00:00Z (next month start)',
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # --- Per-IP rate limit (token bucket via 1-hour cache key) ---
    ip = _client_ip(request)
    hour_key = f'ai_search_ip:{ip}:{datetime.utcnow().strftime("%Y-%m-%d-%H")}'
    used = int(cache.get(hour_key, 0) or 0)
    if used >= per_ip_limit:
        logger.info('AI search per-IP rate-limit hit: ip=%s used=%d/hr limit=%d/hr',
                    ip, used, per_ip_limit)
        return Response({
            'success': False,
            'error': 'rate_limit',
            'message': f'AI search rate limit reached ({per_ip_limit}/hour). '
                       f'Wait until the top of the next hour or use basic search.',
            'limit_per_hour': per_ip_limit,
            'used_this_hour': used,
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)

    # --- Increment counters (set TTLs so they self-expire) ---
    cache.set(hour_key, used + 1, timeout=3600)            # 1 hr
    if cost_override_cents > 0:
        cost = cost_override_cents
    elif kind == 'search':
        cost = _COST_SEARCH_CENTS
    else:
        cost = _COST_DECOMPOSE_CENTS
    cache.set(month_key, spent + cost, timeout=60 * 60 * 24 * 35)  # ~35 days

    return None


def _strip_individual_mode_fields(payload: Dict[str, Any], user_type: str) -> Dict[str, Any]:
    """AUDIENCE-CODE-1: in individual mode hide LLM-internal fields.

    Lay users see the match + alternatives but NOT the LLM justification or
    the raw confidence band (which exposes algorithm internals). Researcher
    and policy modes get the full payload.
    """
    if user_type != 'individual':
        return payload
    redacted = dict(payload)
    redacted['justification'] = ''                  # blank, not removed (stable schema)
    # Confidence stays — it's user-meaningful as a UI badge — but the
    # technical fallback_reason is hidden behind a simpler flag.
    if redacted.get('fallback_reason'):
        redacted['fallback_reason'] = 'low_confidence_or_internal'
    return redacted


# --- /api/cnf/search/ai-enhanced ----------------------------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def cnf_ai_enhanced_search(request):
    """Free-text query → top CNF FoodID match via embedding + LLM ranking.

    Request body:
        {
            "query": "low-fat chocolate milk",
            "top_k": 20,                                 // optional, default 20
            "user_type": "individual"                    // optional
        }

    Response (200):
        {
            "success": true,
            "result": { ... CNFMatchResult.to_dict() ... }
        }

    Errors: 400 (missing query), 429 (rate limit), 503 (circuit breaker), 500 (other).
    """
    query = request.data.get('query', '')
    if not query or not isinstance(query, str) or not query.strip():
        return Response({
            'success': False,
            'error': 'invalid_request',
            'message': 'Field "query" is required (non-empty string).',
        }, status=status.HTTP_400_BAD_REQUEST)

    top_k = request.data.get('top_k')
    if top_k is not None:
        try:
            top_k = max(1, min(50, int(top_k)))
        except (TypeError, ValueError):
            top_k = None

    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    # Rate limit + circuit breaker
    rate_err = _enforce_rate_limit(request, kind='search')
    if rate_err is not None:
        return rate_err

    # Run the matcher
    try:
        from api.services.cnf_matcher import get_default_matcher
        matcher = get_default_matcher()
        result = matcher.match(query, top_k=top_k)
    except FileNotFoundError as exc:
        logger.error('CNF AI search: corpus not built — %s', exc)
        return Response({
            'success': False,
            'error': 'corpus_not_built',
            'message': ('AI search not configured: CNF corpus embeddings are missing. '
                        'Admin: run python -m api.services.etl.build_cnf_corpus_embeddings.'),
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:  # noqa: BLE001
        logger.exception('CNF AI search failed for query=%r', query)
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': f'AI search failed: {exc!r}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    payload = _strip_individual_mode_fields(result.to_dict(), user_type)
    return Response({'success': True, 'result': payload}, status=status.HTTP_200_OK)


# --- /api/recipes/decompose ---------------------------------------------

def _strip_recipe_individual_mode_fields(payload: Dict[str, Any], user_type: str) -> Dict[str, Any]:
    """Individual mode: hide per-ingredient resolution_confidence + audit trail
    + raw LLM response. Researcher / policy mode see everything."""
    if user_type != 'individual':
        return payload
    redacted = dict(payload)
    # Strip raw LLM response (researcher-only audit trail)
    redacted['raw_llm_response'] = None
    # Strip unresolved-ingredients audit
    redacted['unresolved_ingredients_audit'] = []
    # Per-ingredient resolution_confidence is researcher-only too
    redacted['ingredients'] = [
        {**ing, 'resolution_confidence': None}
        for ing in payload.get('ingredients', [])
    ]
    return redacted


@api_view(['POST'])
@permission_classes([AllowAny])
def decompose_recipe(request):
    """Decompose a free-text dish name into CNF ingredients with masses.

    Two-stage: LLM proposes ingredient list → CNFMatcher resolves each
    ingredient name → CNF FoodID. Returns the full ingredient list with
    masses, ready to feed into HENI / HEFI / HSR / FCS scoring.

    Request body:
        {
            "dish_name": "spaghetti bolognese",
            "total_mass_g": 300.0,
            "user_type": "individual"            // optional
        }

    Response (200):
        {
            "success": true,
            "result": { ... CNFDecomposedRecipe.to_dict() ... }
        }

    Errors: 400 (invalid input), 429 (rate limit), 503 (circuit breaker), 500.

    Cost: counts as 5× a basic AI search against the monthly budget (two-
    stage LLM + per-ingredient matcher calls).
    """
    dish_name = request.data.get('dish_name', '')
    total_mass_g = request.data.get('total_mass_g')
    if not dish_name or not isinstance(dish_name, str) or not dish_name.strip():
        return Response({
            'success': False,
            'error': 'invalid_request',
            'message': 'Field "dish_name" is required (non-empty string).',
        }, status=status.HTTP_400_BAD_REQUEST)
    try:
        total_mass_g_f = float(total_mass_g)
        if total_mass_g_f <= 0:
            raise ValueError('total_mass_g must be > 0')
    except (TypeError, ValueError):
        return Response({
            'success': False,
            'error': 'invalid_request',
            'message': 'Field "total_mass_g" is required (positive float).',
        }, status=status.HTTP_400_BAD_REQUEST)
    # Sanity bound (no one cooks a 10kg single-dish meal at once)
    if total_mass_g_f > 5000.0:
        return Response({
            'success': False,
            'error': 'invalid_request',
            'message': 'total_mass_g exceeds 5000g cap.',
        }, status=status.HTTP_400_BAD_REQUEST)

    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    # Rate limit + circuit breaker (5x cost for decompose)
    rate_err = _enforce_rate_limit(request, kind='decompose')
    if rate_err is not None:
        return rate_err

    try:
        from api.services.cnf_recipe_decomposer import get_default_decomposer
        decomposer = get_default_decomposer()
        result = decomposer.decompose(dish_name, total_mass_g_f)
    except FileNotFoundError as exc:
        logger.error('Recipe decompose: corpus not built — %s', exc)
        return Response({
            'success': False,
            'error': 'corpus_not_built',
            'message': ('Recipe decomposition not configured: CNF corpus embeddings missing. '
                        'Admin: run python -m api.services.etl.build_cnf_corpus_embeddings.'),
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:  # noqa: BLE001
        logger.exception('Recipe decompose failed for dish=%r mass=%s',
                         dish_name, total_mass_g)
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': f'Recipe decomposition failed: {exc!r}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    payload = _strip_recipe_individual_mode_fields(result.to_dict(), user_type)
    return Response({'success': True, 'result': payload}, status=status.HTTP_200_OK)


# --- /api/recipes/recall-24h/ -------------------------------------------

def _strip_recall_individual_mode_fields(
    payload: Dict[str, Any], user_type: str,
) -> Dict[str, Any]:
    """Individual mode strips per-meal audit (researcher-only) + per-
    ingredient resolution_confidence + raw LLM responses. Researcher /
    policy modes see everything.

    Aggregated daily ingredients stay visible to everyone — they're the
    user-facing payload regardless of mode.
    """
    if user_type != 'individual':
        return payload
    redacted = dict(payload)
    # Per-meal: strip the audit + raw LLM + per-ingredient confidence.
    redacted_meals = []
    for meal in payload.get('meals', []):
        dec = dict(meal.get('decomposition', {}))
        dec['raw_llm_response'] = None
        dec['unresolved_ingredients_audit'] = []
        dec['ingredients'] = [
            {**ing, 'resolution_confidence': None}
            for ing in dec.get('ingredients', [])
        ]
        redacted_meals.append({'occasion': meal.get('occasion'), 'decomposition': dec})
    redacted['meals'] = redacted_meals
    return redacted


def _build_recall_explanations(
    result_dict: Dict[str, Any], user_type: str,
) -> Dict[str, Any]:
    """Audience-aware explanations block. Always surfaces the Brassard
    2022b single-day caveat up front so users see it BEFORE they route
    to HEFI — keeps the framing honest.
    """
    base_caveat_researcher = (
        'SINGLE-DAY CAVEAT (Brassard 2022b Discussion p. 588): '
        '"A single individual HEFI-2019 from one 24-h recall does NOT '
        'reflect usual adherence and must be interpreted with great '
        'caution." This recall is one day; for individual-level reporting, '
        'apply NCI multivariate MCMC usual-intake modelling (Zhang et al. '
        '2011) on ≥ 2 recall days. HSR daily aggregation is informational '
        'only — HSRAC v9 is a per-product within-category rating; daily '
        'HSR is mathematically computable but methodologically suspect.'
    )
    base_caveat_individual = (
        "What you logged is a single day's snapshot. Your real eating "
        'varies day-to-day, so any single-day score is best read as a '
        'rough indicator, not a definitive measure of how you usually eat. '
        'For HEFI especially, researchers recommend averaging at least '
        'two recall days before making personal conclusions.'
    )
    methodology = (
        'Each meal is decomposed into CNF ingredients with an LLM-assisted '
        '24-h recall flow (six-occasion AMPM-inspired structure: '
        'breakfast / AM snack / lunch / PM snack / dinner / evening '
        'snack). Per-meal decomposition uses the same CNFRecipeDecomposer '
        'pipeline as single-dish scoring (7 validation gates incl. mass '
        'closure, confidence floor, no hallucinated FoodIDs). Daily '
        'ingredient list is deduped by CNF FoodID with masses summed '
        'across meals — ready to feed any scoring endpoint.'
    )
    routing_guidance = {
        'hefi': 'HEFI-2019 is explicitly designed for 24-h recall data (Brassard 2022b). Natural fit.',
        'heni': 'HENI sums per-serving healthy-life-minutes across the day. Natural fit.',
        'fcs':  'FCS at the diet level (i.FCS, O\'Hearn 2022) is the energy-weighted mean. Natural fit.',
        'hsr':  'HSR daily aggregation is INFORMATIONAL ONLY — HSRAC v9 is a per-product within-category rating. Use for comparison, not policy.',
        'environmental': 'Per-day environmental impact aggregates ingredient-level LCA factors. Natural fit.',
    }

    if user_type == 'individual':
        return {
            'plain_summary': {
                'title': "Your day's eating, decomposed",
                'message': (
                    f"You logged {result_dict.get('occasions_count', 0)} "
                    f"meal occasion(s) totalling "
                    f"~{result_dict.get('estimated_daily_kcal', 0):.0f} kcal. "
                    f"We matched your day to "
                    f"{len(result_dict.get('aggregated_daily_ingredients', []))} "
                    f"CNF foods, ready to score against HEFI, HENI, HSR, "
                    f"FCS, or environmental impact."
                ),
            },
            'before_you_score': {
                'title': 'Before you score',
                'message': base_caveat_individual,
            },
        }
    return {
        'mandatory_caveat': {
            'title': 'Single-day caveat (mandatory)',
            'message': base_caveat_researcher,
        },
        'methodology': {
            'title': 'Recall methodology',
            'message': methodology,
        },
        'score_routing': {
            'title': 'Score-routing guidance',
            'message': routing_guidance,
        },
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def recall_24h(request):
    """Build a 24-h dietary recall: decompose each meal-occasion, aggregate
    into a single daily CNF ingredient list, return ready-to-route payload.

    Request body:
        {
            "meals": [
                {"occasion": "breakfast",     "dish_name": "...", "total_mass_g": 200},
                {"occasion": "am_snack",      "dish_name": "...", "total_mass_g": 150},
                {"occasion": "lunch",         "dish_name": "...", "total_mass_g": 300},
                {"occasion": "pm_snack",      "dish_name": "...", "total_mass_g": 30},
                {"occasion": "dinner",        "dish_name": "...", "total_mass_g": 350},
                {"occasion": "evening_snack", "dish_name": "...", "total_mass_g": 80}
            ],
            "user_type": "individual"     // optional
        }

    Response (200):
        {
            "success": true,
            "result":       { ... CNFRecall24hResult.to_dict() ... },
            "explanations": { ... audience-aware block ... }
        }

    Errors: 400 (invalid input), 429 (rate limit), 503 (circuit breaker), 500.

    Cost: 5¢ per meal up to 30¢ cap against the monthly budget.
    """
    meals_raw = request.data.get('meals')
    if not isinstance(meals_raw, list) or not meals_raw:
        return Response({
            'success': False,
            'error': 'invalid_request',
            'message': 'Field "meals" is required (non-empty list).',
        }, status=status.HTTP_400_BAD_REQUEST)
    if len(meals_raw) > len({'breakfast', 'am_snack', 'lunch', 'pm_snack',
                              'dinner', 'evening_snack'}):
        return Response({
            'success': False,
            'error': 'invalid_request',
            'message': 'Recall accepts at most 6 meal-occasions.',
        }, status=status.HTTP_400_BAD_REQUEST)

    # Parse + shape-check each meal before charging the rate limit.
    from api.services.cnf_recall_24h import (
        CNFRecall24h, MealEntry, OCCASIONS,
    )
    cleaned: list = []
    seen_occasions: set = set()
    for m in meals_raw:
        if not isinstance(m, dict):
            return Response({
                'success': False, 'error': 'invalid_request',
                'message': 'Each meal must be an object.',
            }, status=status.HTTP_400_BAD_REQUEST)
        occ = str(m.get('occasion', '')).strip().lower()
        if occ not in OCCASIONS:
            return Response({
                'success': False, 'error': 'invalid_request',
                'message': f'Invalid occasion {occ!r}. Must be one of {OCCASIONS}.',
            }, status=status.HTTP_400_BAD_REQUEST)
        if occ in seen_occasions:
            return Response({
                'success': False, 'error': 'invalid_request',
                'message': f'Duplicate occasion {occ!r}. Each occasion may appear only once.',
            }, status=status.HTTP_400_BAD_REQUEST)
        seen_occasions.add(occ)
        dn = str(m.get('dish_name', '')).strip()
        if not dn:
            return Response({
                'success': False, 'error': 'invalid_request',
                'message': f'Meal at occasion {occ!r} is missing dish_name.',
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            mass = float(m.get('total_mass_g'))
        except (TypeError, ValueError):
            return Response({
                'success': False, 'error': 'invalid_request',
                'message': f'Meal at occasion {occ!r}: total_mass_g must be a positive number.',
            }, status=status.HTTP_400_BAD_REQUEST)
        if mass <= 0 or mass > 5000.0:
            return Response({
                'success': False, 'error': 'invalid_request',
                'message': f'Meal at occasion {occ!r}: total_mass_g must be in (0, 5000].',
            }, status=status.HTTP_400_BAD_REQUEST)
        cleaned.append(MealEntry(occasion=occ, dish_name=dn, total_mass_g=mass))

    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    # Rate limit: 5¢ per meal up to 30¢ cap.
    cost = min(
        _COST_RECALL_24H_PER_MEAL_CENTS * len(cleaned),
        _COST_RECALL_24H_CAP_CENTS,
    )
    rate_err = _enforce_rate_limit(
        request, kind='recall_24h', cost_override_cents=cost,
    )
    if rate_err is not None:
        return rate_err

    try:
        from api.services.cnf_recall_24h import get_default_recall_24h
        orchestrator = get_default_recall_24h()
        result = orchestrator.recall(cleaned, user_type=user_type)
    except FileNotFoundError as exc:
        logger.error('Recall-24h: corpus not built — %s', exc)
        return Response({
            'success': False,
            'error': 'corpus_not_built',
            'message': ('Recall not configured: CNF corpus embeddings missing. '
                        'Admin: run python -m api.services.etl.build_cnf_corpus_embeddings.'),
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:  # noqa: BLE001
        logger.exception('Recall-24h failed for n_meals=%d', len(cleaned))
        return Response({
            'success': False,
            'error': 'internal_error',
            'message': f'Recall failed: {exc!r}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    result_dict = result.to_dict()
    payload = _strip_recall_individual_mode_fields(result_dict, user_type)
    explanations = _build_recall_explanations(result_dict, user_type)
    return Response(
        {'success': True, 'result': payload, 'explanations': explanations},
        status=status.HTTP_200_OK,
    )
