"""Multi-provider chat-JSON client for the LCA matcher (§3.5) and recipe
decomposer (§3.5 Tier γ).

Both call sites need the same thing: send a (system, user) message pair to an
LLM at temperature 0 and parse a JSON object back. This module provides a
provider-agnostic factory + duck-typed Protocol so the matcher and decomposer
can run against OpenAI or Anthropic without provider-specific code in either
file.

Provider selection: defaults to `LLM_PROVIDER` env var (or "openai"). The
matcher / decomposer continue to read `OPENAI_API_KEY` for the embedding side
(Anthropic does not expose an embedding API as of 2026-05); the ranking /
decomposition side reads whichever key matches the chosen provider.

Model overrides (optional):
  - CHAT_LLM_MODEL — text JSON clients (CNF ranking, ingredient decomposition,
    LCA matcher ranking, recipe decomposer). Example: claude-opus-4-7.
  - MULTIMODAL_LLM_MODEL — vision extraction only (see multimodal_client.py).

Typical packaged-food Opus setup (embeddings stay OpenAI):
  OPENAI_API_KEY=...           # embeddings (CNF matcher retrieval)
  ANTHROPIC_API_KEY=...
  LLM_PROVIDER=anthropic
  MULTIMODAL_LLM_MODEL=claude-opus-4-7
  CHAT_LLM_MODEL=claude-opus-4-7

Pattern mirrored from `heni_calculator/heni/categorization/llm_categorizer.py`
(itself multi-provider) but lifted into a shared factory so all three call
sites can share the dispatch logic.

2026-05-22 model defaults:
  - openai     → "gpt-4.1-mini"   ($0.40/$1.60 per 1M; strict JSON schema)
  - anthropic  → "claude-haiku-4-5" ($1/$5 per 1M; JSON via prefill)

Both providers' clients are lazily imported so callers without that
provider's SDK installed still work as long as they don't select it.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Optional, Protocol, runtime_checkable


logger = logging.getLogger(__name__)


_PROVIDER_DEFAULT_MODELS = {
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-haiku-4-5",
}


# --- Token usage telemetry (AI footprint audit §5.5) ------------------------
#
# A process-local registry of (input_tokens, output_tokens, n_calls) keyed by
# (provider, model). Populated by every chat.completion call this module
# dispatches, so that downstream harnesses (per-meal AI footprint, Scenario S8)
# can sum token usage across a meal-scoring pass without instrumenting each
# call site individually. See `get_token_usage()` and `reset_token_usage()`.
#
# Telemetry is opt-out per LLM_TELEMETRY env var; default on. The registry is
# explicitly *not* thread-safe across processes (no cross-Gunicorn-worker
# aggregation) by design: per-request token accounting belongs to the
# request-bound harness that reads `reset_token_usage()` before a scoring
# pass and `get_token_usage()` after.
_TOKEN_USAGE: "dict[tuple[str, str], dict[str, int]]" = {}


def _telemetry_enabled() -> bool:
    return (os.environ.get("LLM_TELEMETRY", "1") or "1") != "0"


def _record_usage(provider: str, model: str,
                  input_tokens: int, output_tokens: int) -> None:
    if not _telemetry_enabled():
        return
    key = (provider, model)
    entry = _TOKEN_USAGE.setdefault(
        key, {"input_tokens": 0, "output_tokens": 0, "n_calls": 0},
    )
    entry["input_tokens"] += int(input_tokens or 0)
    entry["output_tokens"] += int(output_tokens or 0)
    entry["n_calls"] += 1


def get_token_usage() -> "dict[str, dict]":
    """Snapshot of accumulated token usage by (provider, model).

    Returns a serialisable dict keyed by 'provider/model' with per-key totals
    plus an aggregate 'total' entry. Safe to call any time; resets only on
    explicit `reset_token_usage()`.
    """
    out: dict[str, dict] = {}
    agg_in = agg_out = agg_n = 0
    for (provider, model), entry in _TOKEN_USAGE.items():
        out[f"{provider}/{model}"] = dict(entry)
        agg_in += entry["input_tokens"]
        agg_out += entry["output_tokens"]
        agg_n += entry["n_calls"]
    out["total"] = {
        "input_tokens": agg_in,
        "output_tokens": agg_out,
        "n_calls": agg_n,
    }
    return out


def reset_token_usage() -> None:
    _TOKEN_USAGE.clear()


def _env_provider() -> str:
    return (os.environ.get("LLM_PROVIDER") or "openai").lower()


def _env_chat_model(provider: str) -> str:
    explicit = os.environ.get("CHAT_LLM_MODEL")
    if explicit:
        return explicit
    return _PROVIDER_DEFAULT_MODELS[provider]


@runtime_checkable
class ChatJSONClient(Protocol):
    """Duck-typed client that returns parsed JSON from a (system, user) pair."""

    model: str

    def chat_completion_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict: ...


class OpenAIChatJSONClient:
    """Wraps `openai.OpenAI()` and uses chat.completions with JSON-object mode.

    Can also adapt a pre-built OpenAI-style client via `from_client()` — used
    by `LCAMatcher` / `RecipeDecomposer` for back-compat with callers that
    still pass a raw `openai.OpenAI()` instance, and by tests that inject
    a `MagicMock` mimicking the OpenAI chat-completion interface.
    """

    def __init__(self, api_key: str, model: Optional[str] = None):
        from openai import OpenAI  # lazy import
        self._client = OpenAI(api_key=api_key)
        self.model = model or _PROVIDER_DEFAULT_MODELS["openai"]
        self.provider = "openai"

    @classmethod
    def from_client(cls, client: Any, model: Optional[str] = None) -> "OpenAIChatJSONClient":
        """Wrap a pre-built client (e.g. `openai.OpenAI(...)`, or a test
        MagicMock with `.chat.completions.create`) into a ChatJSONClient."""
        self = cls.__new__(cls)
        self._client = client
        self.model = model or _PROVIDER_DEFAULT_MODELS["openai"]
        self.provider = "openai"
        return self

    def chat_completion_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict:
        kwargs: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        rsp = self._client.chat.completions.create(**kwargs)
        content = rsp.choices[0].message.content or "{}"
        try:
            usage = getattr(rsp, "usage", None)
            if usage is not None:
                _record_usage(
                    self.provider, self.model,
                    int(getattr(usage, "prompt_tokens", 0) or 0),
                    int(getattr(usage, "completion_tokens", 0) or 0),
                )
        except Exception:  # noqa: BLE001 — telemetry never breaks scoring
            pass
        return _parse_json_permissive(content)


class AnthropicChatJSONClient:
    """Wraps `anthropic.Anthropic()`. JSON output via assistant-prefill when
    supported; newer models (e.g. claude-opus-4-7) reject temperature and/or
    prefill — those fall back to an explicit JSON-only user suffix."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        import anthropic  # lazy import
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model or _env_chat_model("anthropic")
        self.provider = "anthropic"

    def chat_completion_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict:
        from api.services.anthropic_client_utils import (
            anthropic_error_is_retryable,
            build_anthropic_json_attempts,
        )
        attempts = build_anthropic_json_attempts(self.model, user)
        last_exc: Optional[Exception] = None
        for use_prefill, use_temperature, user_text in attempts:
            messages: list[dict] = [{"role": "user", "content": user_text}]
            if use_prefill:
                messages.append({"role": "assistant", "content": "{"})
            kwargs: dict = {
                "model": self.model,
                "max_tokens": max_tokens or 1024,
                "system": system,
                "messages": messages,
            }
            if use_temperature:
                kwargs["temperature"] = temperature
            try:
                rsp = self._client.messages.create(**kwargs)
                text = rsp.content[0].text if rsp.content else ""
                raw = ("{" + text) if use_prefill else text
                try:
                    usage = getattr(rsp, "usage", None)
                    if usage is not None:
                        _record_usage(
                            self.provider, self.model,
                            int(getattr(usage, "input_tokens", 0) or 0),
                            int(getattr(usage, "output_tokens", 0) or 0),
                        )
                except Exception:  # noqa: BLE001 — telemetry never breaks scoring
                    pass
                return _parse_json_permissive(raw)
            except Exception as exc:  # noqa: BLE001 — probe model capabilities
                last_exc = exc
                if anthropic_error_is_retryable(exc):
                    continue
                raise
        if last_exc is not None:
            raise last_exc
        return {}


def _parse_json_permissive(raw: str) -> dict:
    """Tolerant JSON parser. Strips ```json fences and falls back to
    locating the outermost {...} pair if a literal parse fails. Returns {}
    if nothing parses (callers are expected to validate required keys)."""
    if not raw:
        return {}
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start:end])
            except json.JSONDecodeError:
                pass
        return {}


def coerce_chat_json_client(
    client: Any, *, model: Optional[str] = None,
) -> Optional[ChatJSONClient]:
    """Best-effort coercion. Returns the client unchanged if it is already
    an instance of one of the known ChatJSONClient classes; if it has an
    OpenAI-style `.chat.completions.create` interface (covers real
    openai.OpenAI() and test MagicMocks shaped the same way), wraps it via
    the legacy adapter. Returns None when given None.

    The instanceof check is *intentional* over a generic
    `hasattr(client, "chat_completion_json")` test: MagicMock instances
    auto-create that attribute on first access, which would let test
    fixtures shaped as raw OpenAI clients silently bypass the adapter and
    return a MagicMock instead of the configured response.
    """
    if client is None:
        return None
    if isinstance(client, (OpenAIChatJSONClient, AnthropicChatJSONClient)):
        return client
    # Anything else that exposes `.chat.completions.create` — real openai
    # client OR a test mock shaped that way — goes through the adapter.
    chat = getattr(client, "chat", None)
    if chat is not None and getattr(chat, "completions", None) is not None:
        return OpenAIChatJSONClient.from_client(client, model=model)
    # Last-ditch: trust the duck type if the call site explicitly built a
    # ChatJSONClient-compatible object outside our class hierarchy.
    if hasattr(client, "chat_completion_json"):
        return client
    return None


def build_chat_json_client(
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[ChatJSONClient]:
    """Factory. Returns a ChatJSONClient for the chosen provider, or None
    when no API key is available (matcher / decomposer will then operate in
    degraded mode — same defensive pattern as `build_default_matcher`).

    Resolution order:
      provider arg  →  LLM_PROVIDER env  →  "openai"
      api_key arg   →  OPENAI_API_KEY or ANTHROPIC_API_KEY env (per provider)
      model arg     →  CHAT_LLM_MODEL env  →  provider default
    """
    provider = (provider or _env_provider()).lower()
    if provider not in _PROVIDER_DEFAULT_MODELS:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {provider!r}. "
            f"Supported: {sorted(_PROVIDER_DEFAULT_MODELS)}"
        )
    resolved_model = model or _env_chat_model(provider)
    if provider == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            logger.info("OPENAI_API_KEY missing; ChatJSONClient unavailable")
            return None
        try:
            return OpenAIChatJSONClient(api_key=key, model=resolved_model)
        except ImportError as exc:  # pragma: no cover - openai is in requirements
            logger.warning("openai SDK not importable: %s", exc)
            return None
    if provider == "anthropic":
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            logger.info("ANTHROPIC_API_KEY missing; ChatJSONClient unavailable")
            return None
        try:
            return AnthropicChatJSONClient(api_key=key, model=resolved_model)
        except ImportError as exc:
            logger.warning(
                "anthropic SDK not installed; install with "
                "`pip install anthropic` to use LLM_PROVIDER=anthropic: %s", exc,
            )
            return None
    raise ValueError(
        f"Unknown LLM_PROVIDER: {provider!r}. "
        f"Supported: {sorted(_PROVIDER_DEFAULT_MODELS)}"
    )
