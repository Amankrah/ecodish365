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
_COST_SEARCH_CENTS = 1                # in 0.1¢ units → 0.1¢
_COST_DECOMPOSE_CENTS = 5             # 0.5¢


def _client_ip(request) -> str:
    """Best-effort client IP for rate limiting."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _enforce_rate_limit(request, kind: str = 'search') -> 'Response | None':
    """Per-IP hourly token bucket + monthly global circuit breaker.

    Returns None on success, or a Response (429 / 503) to short-circuit the
    view. Uses Django's cache framework (works with both local-memory and
    Redis backends).
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
    cost = _COST_SEARCH_CENTS if kind == 'search' else _COST_DECOMPOSE_CENTS
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
