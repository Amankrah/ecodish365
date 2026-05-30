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
from typing import Any, Dict, List, Optional

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
# Dietary-pattern: 1¢ baseline (no LLM); +1¢ when include_narrative=true.
_COST_SEARCH_CENTS = 1                # in 0.1¢ units → 0.1¢
_COST_DECOMPOSE_CENTS = 5             # 0.5¢
_COST_RECALL_24H_PER_MEAL_CENTS = 5   # same as decompose; recall composes them
_COST_RECALL_24H_CAP_CENTS = 30       # hard ceiling regardless of meal count
_COST_DIETARY_PATTERN_CENTS = 1       # no LLM by default
_COST_DIETARY_PATTERN_NARRATIVE_CENTS = 2  # +1¢ when include_narrative=true


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

    # WAFCT-EXTEND (2026-05-24): optional source filter restricts the
    # candidate pool to one food database (cnf / wafct / both).
    source = str(request.data.get('source', 'both')).lower()
    if source not in ('cnf', 'wafct', 'both'):
        source = 'both'
    source_filter = source if source in ('cnf', 'wafct') else None

    # Rate limit + circuit breaker
    rate_err = _enforce_rate_limit(request, kind='search')
    if rate_err is not None:
        return rate_err

    # Run the matcher
    try:
        from api.services.cnf_matcher import get_default_matcher
        matcher = get_default_matcher()
        result = matcher.match(query, top_k=top_k, source=source_filter)
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

    # WAFCT-EXTEND (2026-05-24): optional `source` restricts Stage-2
    # ingredient resolution to one food database (cnf / wafct / both).
    source_raw = str(request.data.get('source', 'both')).lower()
    source = source_raw if source_raw in ('cnf', 'wafct') else None

    # Rate limit + circuit breaker (5x cost for decompose)
    rate_err = _enforce_rate_limit(request, kind='decompose')
    if rate_err is not None:
        return rate_err

    try:
        from api.services.cnf_recipe_decomposer import get_default_decomposer
        decomposer = get_default_decomposer()
        result = decomposer.decompose(dish_name, total_mass_g_f, source=source)
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
        "What you logged is one day of eating. Your habits change from day to "
        "day, so treat any single-day score as a snapshot, not a verdict on "
        "how you usually eat. Logging several days gives a clearer picture."
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
                'title': "Your day's foods",
                'message': (
                    f"You logged {result_dict.get('occasions_count', 0)} "
                    f"meal(s) totalling about "
                    f"{result_dict.get('estimated_daily_kcal', 0):.0f} calories. "
                    f"We matched your day to "
                    f"{len(result_dict.get('aggregated_daily_ingredients', []))} "
                    f"foods, ready to score for nutrition, health, and "
                    f"environment."
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
        entry_type = str(m.get('entry_type', 'text')).strip().lower()
        if entry_type not in ('text', 'packaged', 'direct'):
            return Response({
                'success': False, 'error': 'invalid_request',
                'message': f'Meal at occasion {occ!r}: entry_type must be "text", "packaged", or "direct".',
            }, status=status.HTTP_400_BAD_REQUEST)
        pre_decomposed = None
        if entry_type in ('packaged', 'direct'):
            pre = m.get('pre_decomposed')
            if not isinstance(pre, dict):
                return Response({
                    'success': False, 'error': 'invalid_request',
                    'message': f'{entry_type.title()} meal at {occ!r} requires pre_decomposed object.',
                }, status=status.HTTP_400_BAD_REQUEST)
            ings = pre.get('ingredients')
            if not isinstance(ings, list) or not ings:
                return Response({
                    'success': False, 'error': 'invalid_request',
                    'message': f'Packaged meal at {occ!r}: pre_decomposed.ingredients must be a non-empty list.',
                }, status=status.HTTP_400_BAD_REQUEST)
            pre_decomposed = pre
        cleaned.append(MealEntry(
            occasion=occ,
            dish_name=dn,
            total_mass_g=mass,
            entry_type=entry_type,
            pre_decomposed=pre_decomposed,
        ))

    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    # WAFCT-EXTEND (2026-05-24): optional `source` restricts every meal's
    # Stage-2 ingredient resolution to one food database.
    source_raw = str(request.data.get('source', 'both')).lower()
    source = source_raw if source_raw in ('cnf', 'wafct') else None

    # Rate limit: 5¢ per text meal (LLM decompose) up to 30¢ cap. Packaged
    # meals arrive pre-decomposed from the scan flow — no per-meal LLM cost.
    text_meal_count = sum(
        1 for m in cleaned if (m.entry_type or 'text') not in ('packaged', 'direct')
    )
    cost = min(
        _COST_RECALL_24H_PER_MEAL_CENTS * text_meal_count,
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
        result = orchestrator.recall(cleaned, user_type=user_type, source=source)
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


# --- /api/dietary-pattern/classify/ -------------------------------------

_NARRATIVE_SYSTEM_PROMPT = (
    "You are explaining a dietary-pattern match to a {user_type} user.\n\n"
    "Input is the top 3 eating-style matches, the user's heaviest foods, "
    "and a confidence level.\n\n"
    "Write 2-3 short sentences:\n"
    "- Sentence 1: name the closest eating style, its match strength as a "
    "percentage, and one or two foods that pulled the match that way.\n"
    "- Sentence 2: mention a close second style if there is one.\n"
    "- Sentence 3 (optional): one practical observation or swap idea. No "
    "health promises or risk claims.\n\n"
    "RULES:\n"
    "- Say \"today's food choices resemble\" or \"your day looks most like\". "
    "Never say \"you are\" or \"you eat\".\n"
    "- Do not cite studies, mortality, or disease risk.\n"
    "- Use plain, conversational language.\n"
    "- Do not mention cosine, embeddings, or technical scoring terms.\n\n"
    "Respond with JSON only: {{\"narrative\": \"...\"}}"
)


_CONFIDENCE_PLAIN = {
    'high': 'strong match',
    'moderate': 'reasonable match',
    'low': 'uncertain match',
}


def _top_pattern_display(result_dict: Dict[str, Any]) -> str:
    resemblances = result_dict.get('resemblances') or []
    if resemblances:
        return str(resemblances[0].get('display_name') or result_dict.get('top_pattern', '?'))
    return str(result_dict.get('top_pattern', '?'))


def _confidence_phrase(confidence: str) -> str:
    return _CONFIDENCE_PLAIN.get(confidence, confidence.replace('_', ' '))


def _strip_pattern_individual_mode_fields(
    payload: Dict[str, Any], user_type: str,
) -> Dict[str, Any]:
    """Individual mode strips researcher-only fields per the matcher's
    JSON `individual_mode_visible` / `researcher_mode_visible` config.

    Already filtered at the matcher (EAT-Lancet prototype excluded for
    individual mode). This additionally redacts per-prototype researcher-
    only fields (literature_anchor, outcome_evidence_reused, distinctive
    user foods) from the response body.
    """
    if user_type != 'individual':
        return payload
    redacted = dict(payload)
    redacted_resemblances = []
    for r in payload.get('resemblances', []):
        rr = dict(r)
        rr['literature_anchor'] = ''
        rr['outcome_evidence_reused'] = ''
        rr['distinctive_user_foods'] = []
        redacted_resemblances.append(rr)
    redacted['resemblances'] = redacted_resemblances
    return redacted


def _extract_n_days(meta_label: Optional[str]) -> str:
    """Extract the leading integer from a meta_label like '5-day average,
    2026-05-17 to 2026-05-21' → '5'. Returns 'multi' if no integer prefix."""
    if not meta_label:
        return 'multi'
    import re
    m = re.match(r'\s*(\d+)\s*-\s*day', meta_label)
    return m.group(1) if m else 'multi'


def _build_pattern_explanations(
    result_dict: Dict[str, Any], user_type: str, narrative: Optional[str],
    meta_label: Optional[str] = None,
    decomposition_provenance: Optional[str] = None,
) -> Dict[str, Any]:
    """Audience-aware explanations block. Always carries the mandatory
    single-day caveat (or its softened multi-day variant when `meta_label`
    is set, or the packaged-food-inferred variant when `decomposition_provenance`
    is set). Researcher / policy adds methodology + the per-prototype
    literature anchor in the response.

    `narrative` (when include_narrative=true) is shipped here too so the
    frontend has a single explanations dict to render.

    `meta_label` (RECALL-HISTORY-1, 2026-05-24): when set (e.g.
    "5-day average, 2026-05-17 to 2026-05-21"), the caveat language
    swaps from the single-day disclaimer to the softened multi-day
    variant — honest improvement without overclaiming. The frontend
    drives this from the `/recall-history` "Score N-day average" path.

    `decomposition_provenance` (PKG-IMG-1 Phase 2, 2026-05-26): when set
    to "packaged_food_inferred", the caveat language additionally notes
    that the ingredient composition was INFERRED from a label ingredient
    list (positions + NF panel macros), not measured. The frontend drives
    this from the `/scan-product` packaged-food decomposition path.
    """
    is_multi_day = bool(meta_label)
    is_inferred_composition = decomposition_provenance == 'packaged_food_inferred'
    base_caveat_individual = (
        "This is one snapshot of what you ate. To understand your usual "
        "habits, log several days. These eating-style labels describe the "
        "shape of your food choices. They are not personal health predictions."
    )
    base_caveat_researcher = (
        "MANDATORY CAVEAT: this resemblance is computed on a single-day "
        "ingredient list and characterises only the shape of one day's "
        "food selection. It is NOT a usual-eating-pattern classifier — "
        "same Brassard 2022b limitation as HEFI-2019 from a single 24-h "
        "recall (Appl Physiol Nutr Metab 2022;47:611-624 Discussion p. 588). "
        "Prototype outcome citations refer to populations following each "
        "pattern long-term in randomised / cohort studies (Trichopoulou "
        "2003, Estruch 2013 PREDIMED, Sacks 2001 DASH, Orlich 2013 AHS-2), "
        "NOT to single-day resemblance. Do not interpret a high "
        "Mediterranean-resemblance cosine as a personal CVD-risk reduction."
    )
    multi_day_caveat_individual = (
        f"This is your {meta_label}. That starts to reflect your usual "
        "eating, but it is still a limited sample. These labels describe "
        "the overall shape of your food choices across these days. They are "
        "not personal health predictions. Check individual days on your food "
        "diary to see how your pattern shifts."
    )
    multi_day_caveat_researcher = (
        f"MULTI-DAY AVERAGE CAVEAT ({meta_label}): the resemblance below is "
        "computed on a mass-weighted concatenation of {N} saved recall days "
        "(volume-weighted, NOT per-day-equal-weighted — high-kcal days "
        "contribute proportionally more). This approximates the directional "
        "intent of multi-day averaging but is NOT the NCI multivariate "
        "MCMC usual-intake method (Zhang 2011) which Brassard 2022b "
        "(Discussion p. 588) recommends for population-level usual-intake "
        "claims. Prototype outcome citations refer to populations following "
        "each pattern long-term in randomised / cohort studies "
        "(Trichopoulou 2003, Estruch 2013 PREDIMED, Sacks 2001 DASH, "
        "Orlich 2013 AHS-2), NOT to N-day average resemblance. For per-day "
        "variation in addition to this average, see the timeline view on "
        "the recall-history page."
    ).replace('{N}', str(_extract_n_days(meta_label)))

    # PKG-IMG-1 Phase 2 caveat — fires when the ingredient list came from
    # a packaged-food label decomposition (not a recall or measured intake).
    # Regulation only requires descending-mass-order on labels; the per-
    # ingredient masses are LLM-inferred from positions + NF panel macros.
    inferred_composition_caveat_individual = (
        "This match used an ingredient list read from a packaged food label. "
        "Amounts for each ingredient are estimated from label order and "
        "nutrition facts, not weighed. Treat the result as directional. A "
        "single packaged product is not a full day of eating."
    )
    inferred_composition_caveat_researcher = (
        "INFERRED-COMPOSITION CAVEAT (PKG-IMG-1 Phase 2): the ingredient "
        "list was extracted from a single packaged-food label image; per-"
        "ingredient masses are LLM-inferred constrained by (a) regulatory "
        "descending-mass-order, (b) any label-disclosed percentages "
        "(Regulation 1169/2011 QUID-style; rare in North America), and "
        "(c) mass-conservation against the NF panel macros (target ± 10 %). "
        "Composition is structurally INFERRED, not measured. The pattern "
        "cosine is therefore a directional signal about the product, NOT a "
        "validated measurement of dietary pattern intake. For inference at "
        "the dietary-level, route through /recall-24h instead."
    )

    out: Dict[str, Any] = {}
    pattern_name = _top_pattern_display(result_dict)
    confidence = _confidence_phrase(str(result_dict.get('top_pattern_confidence', '')))
    if user_type == 'individual':
        if is_inferred_composition:
            out['plain_summary'] = {
                'title': 'Packaged product eating style',
                'message': (
                    f"This product's ingredients look most like the "
                    f"{pattern_name} eating style ({confidence}). "
                    f"Read this as a property of the product, not your whole diet."
                ),
            }
            out['mandatory_caveat'] = {
                'title': 'About this result',
                'message': inferred_composition_caveat_individual,
            }
        elif is_multi_day:
            out['plain_summary'] = {
                'title': f'Your {meta_label}',
                'message': (
                    f"Across {meta_label}, your average food choices look most "
                    f"like the {pattern_name} eating style ({confidence})."
                ),
            }
            out['mandatory_caveat'] = {
                'title': 'About this average',
                'message': multi_day_caveat_individual,
            }
        else:
            out['plain_summary'] = {
                'title': "Today's eating style",
                'message': (
                    f"Today's food choices look most like the {pattern_name} "
                    f"eating style ({confidence})."
                ),
            }
            out['mandatory_caveat'] = {
                'title': 'About this result',
                'message': base_caveat_individual,
            }
    else:
        if is_inferred_composition:
            out['mandatory_caveat'] = {
                'title': 'Inferred-composition caveat (packaged food)',
                'message': inferred_composition_caveat_researcher,
            }
        elif is_multi_day:
            out['mandatory_caveat'] = {
                'title': 'Multi-day average caveat',
                'message': multi_day_caveat_researcher,
            }
        else:
            out['mandatory_caveat'] = {
                'title': 'Mandatory caveat (single-day resemblance)',
                'message': base_caveat_researcher,
            }
        out['methodology'] = {
            'title': 'Method',
            'message': (
                "Mass-weighted day vector built from per-food embeddings "
                "(text-embedding-3-small, 1,536-dim, L2-normalised) of the "
                "user's aggregated ingredient list, cosine-scored against "
                "literature-anchored prototype vectors (mean of curated "
                "example days per pattern). Softmax temperature T=0.1. "
                "Confidence bands: high if top cosine ≥ 0.75 AND ≥ 0.05 "
                "gap to runner-up; moderate if ≥ 0.60; low otherwise. "
                "Co-leading patterns within 0.05 cosine of top reported "
                "jointly. See DIETARY_PATTERN_JUSTIFICATION.md for the "
                "full design memo."
            ),
        }
    if narrative:
        out['narrative'] = {
            'title': 'Plain-language summary',
            'message': narrative,
        }
    return out


def _generate_narrative(
    result_dict: Dict[str, Any], user_type: str, foods: List[Dict[str, Any]],
) -> Optional[str]:
    """Optional LLM narrative via the matcher's existing chat_json_client.

    Returns None on any failure (the resemblance result still ships).
    """
    try:
        from api.services.cnf_matcher import get_default_matcher
        from api.cnf_cache import get_api_cnf_pipeline
        client = get_default_matcher().chat_json_client
        if client is None:
            return None
        pipeline = get_api_cnf_pipeline()

        # Build a compact user-side context: top-5 foods by mass, top-3 patterns.
        top_foods = sorted(foods, key=lambda f: -float(f.get('mass_g', 0)))[:5]
        fn = pipeline.food_name_df
        food_names = []
        for f in top_foods:
            row = fn[fn['FoodID'] == int(f['food_id'])][:1]
            name = str(row.iloc[0]['FoodDescription'])[:50] if len(row) else f'FoodID {f["food_id"]}'
            food_names.append(f'{f["mass_g"]:.0f}g {name}')

        top3 = result_dict.get('resemblances', [])[:3]
        patterns_summary = '; '.join(
            f'{r["display_name"]} ({r["cosine"] * 100:.0f}%)' for r in top3
        )
        confidence = result_dict.get('top_pattern_confidence', 'moderate')
        co_leading = result_dict.get('co_leading') or []

        user = (
            f"User's day (top-5 foods by mass): {' | '.join(food_names)}\n\n"
            f"Top-3 resemblances: {patterns_summary}\n"
            f"Confidence band: {confidence}\n"
            f"Co-leading patterns within 5% cosine of the top: "
            f"{', '.join(co_leading) if co_leading else 'none'}\n\n"
            "Generate the 2-3 sentence narrative now."
        )

        resp = client.chat_completion_json(
            system=_NARRATIVE_SYSTEM_PROMPT.format(user_type=user_type),
            user=user,
            temperature=0.0,
            max_tokens=200,
        )
        if isinstance(resp, dict):
            return str(resp.get('narrative', ''))[:600] or None
        if isinstance(resp, str):
            return resp[:600]
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning('Dietary-pattern narrative generation failed: %s', exc)
        return None


@api_view(['POST'])
@permission_classes([AllowAny])
def dietary_pattern_classify(request):
    """Score a daily ingredient list against the prototype-pattern library.

    Request body:
        {
            "foods": [{"food_id": 4471, "mass_g": 100}, ...],
            "user_type": "individual",
            "include_narrative": false,
            "meta_label": null  // RECALL-HISTORY-1: when set, e.g.
                                // "5-day average, 2026-05-17 to 2026-05-21",
                                // swaps caveat to multi-day variant.
        }

    Response (200):
        {
            "success": true,
            "result": { ... PatternResemblanceResult.to_dict() ... },
            "explanations": { mandatory_caveat + methodology + narrative? }
        }

    Errors: 400 (invalid input), 429 (rate limit), 503 (circuit breaker), 500.
    Cost: 1¢ baseline; 2¢ when include_narrative=true.
    """
    foods_raw = request.data.get('foods')
    if not isinstance(foods_raw, list) or not foods_raw:
        return Response({
            'success': False,
            'error': 'invalid_request',
            'message': 'Field "foods" is required (non-empty list of {food_id, mass_g}).',
        }, status=status.HTTP_400_BAD_REQUEST)

    cleaned: List[Dict[str, Any]] = []
    for f in foods_raw:
        if not isinstance(f, dict):
            return Response({
                'success': False, 'error': 'invalid_request',
                'message': 'Each food must be an object with food_id and mass_g.',
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            fid = int(f.get('food_id'))
            mass = float(f.get('mass_g'))
        except (TypeError, ValueError):
            continue
        if fid <= 0 or mass <= 0:
            continue
        cleaned.append({'food_id': fid, 'mass_g': mass})

    if not cleaned:
        return Response({
            'success': False, 'error': 'invalid_request',
            'message': 'No foods with positive food_id and mass_g.',
        }, status=status.HTTP_400_BAD_REQUEST)

    user_type = str(request.data.get('user_type', 'individual'))
    if user_type not in ('individual', 'researcher', 'policy'):
        user_type = 'individual'

    include_narrative = bool(request.data.get('include_narrative', False))

    # RECALL-HISTORY-1 (2026-05-24): optional meta_label swaps the
    # single-day mandatory caveat to a softened multi-day variant. The
    # frontend's /recall-history page passes e.g. "5-day average,
    # 2026-05-17 to 2026-05-21" when routing the N-day-average view.
    # Bounded length + plain-text scrub to keep it safe to render.
    meta_label_raw = request.data.get('meta_label')
    meta_label: Optional[str] = None
    if isinstance(meta_label_raw, str):
        ml = meta_label_raw.strip()[:120]
        if ml:
            meta_label = ml

    # PKG-IMG-1 Phase 2 (2026-05-26): optional decomposition_provenance
    # swaps the single-day caveat to a "packaged food, inferred composition"
    # variant. The frontend's /scan-product page passes
    # 'packaged_food_inferred' after running the ingredient-list decomposer.
    decomp_provenance_raw = request.data.get('decomposition_provenance')
    decomposition_provenance: Optional[str] = None
    if isinstance(decomp_provenance_raw, str):
        dp = decomp_provenance_raw.strip()
        if dp in ('packaged_food_inferred',):
            decomposition_provenance = dp

    cost = (_COST_DIETARY_PATTERN_NARRATIVE_CENTS if include_narrative
            else _COST_DIETARY_PATTERN_CENTS)
    rate_err = _enforce_rate_limit(
        request, kind='dietary_pattern', cost_override_cents=cost,
    )
    if rate_err is not None:
        return rate_err

    try:
        from api.services.dietary_pattern import get_default_pattern_matcher
        matcher = get_default_pattern_matcher()
        visible = matcher.visible_for(user_type)
        # Individual mode skips per-prototype distinctive-foods computation
        # — they're researcher-only response fields anyway.
        result = matcher.classify(
            cleaned,
            prototypes_visible=visible,
            include_distinctive_foods=(user_type != 'individual'),
        )
    except FileNotFoundError as exc:
        logger.error('Dietary-pattern classify: prototypes file missing — %s', exc)
        return Response({
            'success': False, 'error': 'prototypes_not_built',
            'message': ('Dietary-pattern classifier not configured: prototypes JSON '
                        'is missing at backend/api/data/dietary_pattern_prototypes.json.'),
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as exc:  # noqa: BLE001
        logger.exception('Dietary-pattern classify failed for n_foods=%d', len(cleaned))
        return Response({
            'success': False, 'error': 'internal_error',
            'message': f'Dietary-pattern classification failed: {exc!r}',
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    result_dict = result.to_dict()
    payload = _strip_pattern_individual_mode_fields(result_dict, user_type)

    narrative: Optional[str] = None
    if include_narrative and result.matched:
        narrative = _generate_narrative(result_dict, user_type, cleaned)

    explanations = _build_pattern_explanations(
        result_dict, user_type, narrative,
        meta_label=meta_label,
        decomposition_provenance=decomposition_provenance,
    )

    # FPED-1 (2026-05-28): explain the opaque embedding resemblance in food-group
    # terms — the top component deltas of the user's day vs the winning prototype's
    # average day. Pure interpretive overlay; wrapped so it can never break the
    # classification response.
    if result.matched and result_dict.get('top_pattern'):
        try:
            from api.views.fped_explanations import fped_pattern_drivers
            proto_foods, n_days = matcher.prototype_example_foods(result_dict['top_pattern'])
            drivers = fped_pattern_drivers(cleaned, proto_foods, n_days)
            if drivers:
                explanations['fped_drivers'] = {
                    'title': 'Why it matched (food groups)',
                    'pattern': result_dict['top_pattern'],
                    'drivers': drivers,
                    'caveat': (
                        'These are the biggest food-group differences between '
                        'your day and a typical day in this eating style. '
                        'They help explain the match. They do not change the '
                        'score.'
                    ),
                }
        except Exception:  # noqa: BLE001 — overlay must never break classification
            logger.debug('FPED driver overlay skipped', exc_info=True)

    return Response(
        {'success': True, 'result': payload, 'explanations': explanations},
        status=status.HTTP_200_OK,
    )
