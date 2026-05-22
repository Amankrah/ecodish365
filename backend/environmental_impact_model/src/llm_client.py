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


def _env_provider() -> str:
    return (os.environ.get("LLM_PROVIDER") or "openai").lower()


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
        return _parse_json_permissive(content)


class AnthropicChatJSONClient:
    """Wraps `anthropic.Anthropic()` and uses the assistant-prefill trick to
    coerce JSON output. Anthropic's `messages.create` does not have an
    OpenAI-style `response_format=json_object` flag, but prefilling the
    assistant turn with `{` reliably forces the model to continue as a JSON
    object — the recommended Anthropic pattern (per Anthropic prompting
    guide on prefilling)."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        import anthropic  # lazy import
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model or _PROVIDER_DEFAULT_MODELS["anthropic"]
        self.provider = "anthropic"

    def chat_completion_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict:
        rsp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 1024,
            temperature=temperature,
            system=system,
            messages=[
                {"role": "user", "content": user},
                {"role": "assistant", "content": "{"},
            ],
        )
        # `rsp.content` is a list of content blocks; the first is the text block
        # that continues from our "{" prefill. Re-prepend the "{" we forced.
        text = rsp.content[0].text if rsp.content else ""
        return _parse_json_permissive("{" + text)


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
      model arg     →  _PROVIDER_DEFAULT_MODELS[provider]
    """
    provider = (provider or _env_provider()).lower()
    if provider == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            logger.info("OPENAI_API_KEY missing; ChatJSONClient unavailable")
            return None
        try:
            return OpenAIChatJSONClient(api_key=key, model=model)
        except ImportError as exc:  # pragma: no cover - openai is in requirements
            logger.warning("openai SDK not importable: %s", exc)
            return None
    if provider == "anthropic":
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            logger.info("ANTHROPIC_API_KEY missing; ChatJSONClient unavailable")
            return None
        try:
            return AnthropicChatJSONClient(api_key=key, model=model)
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
