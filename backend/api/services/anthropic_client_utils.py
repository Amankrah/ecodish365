"""Shared Anthropic Messages API helpers for JSON extraction / chat.

Newer models (e.g. claude-opus-4-7) reject ``temperature`` and assistant
prefill. Haiku still accepts the legacy path — we probe only when needed.
"""
from __future__ import annotations

_JSON_ONLY_SUFFIX = (
    "\n\nRespond with ONE JSON object only. "
    "No markdown fences, no commentary."
)


def anthropic_skips_legacy_attempts(model: str) -> bool:
    """True when the model should use the modern JSON-only path directly."""
    m = (model or "").lower()
    # Opus 4.x (incl. claude-opus-4-7): no temperature, no assistant prefill.
    return "opus-4" in m


def build_anthropic_json_attempts(
    model: str,
    user: str,
) -> tuple[tuple[bool, bool, str], ...]:
    """Return (use_prefill, use_temperature, user_text) attempts in order."""
    json_user = user + _JSON_ONLY_SUFFIX
    if anthropic_skips_legacy_attempts(model):
        return ((False, False, json_user),)
    return (
        (True, True, user),
        (True, False, user),
        (False, False, json_user),
    )


def anthropic_error_is_retryable(exc: Exception) -> bool:
    msg = str(exc).lower()
    if "temperature" in msg and "deprecated" in msg:
        return True
    if "prefill" in msg or "end with a user message" in msg:
        return True
    return False
