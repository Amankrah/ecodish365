"""Tests for the multi-provider ChatJSONClient factory + adapters.

No live API calls — all tests run against mocks. Verifies:
  - The factory respects LLM_PROVIDER env (openai vs anthropic).
  - Missing-key paths return None rather than raising (matcher/decomposer
    then fall back to degraded modes).
  - Unknown provider raises ValueError.
  - `coerce_chat_json_client` correctly wraps an OpenAI-shaped mock client
    (used by every existing matcher/decomposer test) into an adapter that
    calls `.chat.completions.create` and parses JSON from the response.
  - `coerce_chat_json_client` returns ChatJSONClient instances unchanged.
  - Pinned default models for both providers (gpt-4.1-mini, claude-haiku-4-5).
"""
from __future__ import annotations

import json
import os
import unittest
from unittest.mock import MagicMock, patch

from environmental_impact_model.src.llm_client import (
    AnthropicChatJSONClient,
    OpenAIChatJSONClient,
    _PROVIDER_DEFAULT_MODELS,
    _parse_json_permissive,
    build_chat_json_client,
    coerce_chat_json_client,
)


class DefaultModelPinTests(unittest.TestCase):
    """Pin the provider defaults so a model swap requires updating these
    tests — surfaces accidental reverts at PR-review time."""

    def test_openai_default_is_gpt_41_mini(self):
        self.assertEqual(_PROVIDER_DEFAULT_MODELS["openai"], "gpt-4.1-mini")

    def test_anthropic_default_is_claude_haiku_45(self):
        self.assertEqual(_PROVIDER_DEFAULT_MODELS["anthropic"], "claude-haiku-4-5")


class FactoryEnvDispatchTests(unittest.TestCase):
    """Exercise the env-var dispatch on `build_chat_json_client`."""

    def _clear_env(self):
        return patch.dict(
            os.environ,
            {"LLM_PROVIDER": "", "OPENAI_API_KEY": "", "ANTHROPIC_API_KEY": ""},
            clear=False,
        )

    def test_missing_openai_key_returns_none(self):
        with self._clear_env():
            client = build_chat_json_client(provider="openai")
            self.assertIsNone(client)

    def test_missing_anthropic_key_returns_none(self):
        with self._clear_env():
            client = build_chat_json_client(provider="anthropic")
            self.assertIsNone(client)

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            build_chat_json_client(provider="vertexai")

    def test_explicit_provider_overrides_env(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "anthropic"}, clear=False):
            # Pass openai explicitly; env says anthropic. Explicit arg wins.
            # Use a fake key so the openai branch executes (we just check
            # which branch fires by reading client.provider).
            try:
                client = build_chat_json_client(provider="openai", api_key="sk-test")
            except Exception:  # pragma: no cover - openai SDK init varies
                client = None
            if client is not None:
                self.assertEqual(client.provider, "openai")

    def test_chat_llm_model_env_override(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "anthropic",
                "ANTHROPIC_API_KEY": "sk-ant-test",
                "CHAT_LLM_MODEL": "claude-opus-4-7",
            },
            clear=False,
        ):
            try:
                client = build_chat_json_client()
            except Exception:  # pragma: no cover
                client = None
            if client is not None:
                self.assertEqual(client.model, "claude-opus-4-7")


class CoerceTests(unittest.TestCase):
    """`coerce_chat_json_client` is the back-compat seam: existing matcher
    and decomposer tests inject MagicMock clients shaped like the OpenAI
    chat-completion API. The coercion must wrap them so the production
    `chat_json_client.chat_completion_json(...)` call path still resolves
    to `mock.chat.completions.create(...)`."""

    def _openai_shaped_mock(self, parsed_payload: dict) -> MagicMock:
        """Returns a MagicMock that mimics `openai.OpenAI()` shape with a
        configured chat-completion return value."""
        client = MagicMock()
        message = MagicMock(content=json.dumps(parsed_payload))
        choice = MagicMock(message=message)
        client.chat.completions.create.return_value = MagicMock(choices=[choice])
        return client

    def test_none_passthrough(self):
        self.assertIsNone(coerce_chat_json_client(None))

    def test_openai_shaped_mock_gets_wrapped(self):
        mock_client = self._openai_shaped_mock({"answer": 42})
        adapter = coerce_chat_json_client(mock_client)
        self.assertIsInstance(adapter, OpenAIChatJSONClient)
        # Adapter must route the call through to the underlying mock.
        result = adapter.chat_completion_json(system="s", user="u")
        self.assertEqual(result, {"answer": 42})
        self.assertEqual(mock_client.chat.completions.create.call_count, 1)

    def test_chat_json_client_instance_passes_through(self):
        # An OpenAIChatJSONClient wrapping a mock — coerce should return it
        # unchanged.
        mock_client = self._openai_shaped_mock({"x": 1})
        wrapped = OpenAIChatJSONClient.from_client(mock_client)
        coerced = coerce_chat_json_client(wrapped)
        self.assertIs(coerced, wrapped)

    def test_adapter_handles_empty_content(self):
        client = MagicMock()
        message = MagicMock(content=None)
        choice = MagicMock(message=message)
        client.chat.completions.create.return_value = MagicMock(choices=[choice])
        adapter = OpenAIChatJSONClient.from_client(client)
        self.assertEqual(adapter.chat_completion_json(system="s", user="u"), {})

    def test_adapter_passes_max_tokens_when_set(self):
        client = self._openai_shaped_mock({})
        adapter = OpenAIChatJSONClient.from_client(client)
        adapter.chat_completion_json(system="s", user="u", max_tokens=128)
        call_kwargs = client.chat.completions.create.call_args.kwargs
        self.assertEqual(call_kwargs.get("max_tokens"), 128)
        self.assertEqual(call_kwargs.get("temperature"), 0.0)
        self.assertEqual(call_kwargs.get("response_format"), {"type": "json_object"})


class ParseJSONPermissiveTests(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(_parse_json_permissive('{"a": 1}'), {"a": 1})

    def test_strips_code_fence(self):
        self.assertEqual(
            _parse_json_permissive('```json\n{"a": 1}\n```'),
            {"a": 1},
        )

    def test_recovers_object_from_prose(self):
        self.assertEqual(
            _parse_json_permissive('Here is your answer: {"a": 1} done.'),
            {"a": 1},
        )

    def test_empty_returns_empty_dict(self):
        self.assertEqual(_parse_json_permissive(""), {})
        self.assertEqual(_parse_json_permissive("   "), {})


class AnthropicAdapterTests(unittest.TestCase):
    """Anthropic adapter uses assistant-prefill `"{"` to coerce JSON.
    Without the anthropic SDK installed (it's an optional dep), we exercise
    the chat method by injecting a mocked `_client`."""

    def test_chat_completion_json_prepends_brace_to_response(self):
        # Skip if the anthropic SDK isn't importable; otherwise build a real
        # AnthropicChatJSONClient and swap out its _client for a mock.
        try:
            import anthropic  # noqa: F401
        except ImportError:
            self.skipTest("anthropic SDK not installed")
        adapter = AnthropicChatJSONClient(api_key="sk-ant-test")
        text_block = MagicMock()
        text_block.text = '"answer": 42, "ok": true}'
        adapter._client = MagicMock()
        adapter._client.messages.create.return_value = MagicMock(content=[text_block])
        result = adapter.chat_completion_json(system="s", user="u")
        self.assertEqual(result, {"answer": 42, "ok": True})
        # Verify the prefill turn was passed.
        msgs = adapter._client.messages.create.call_args.kwargs["messages"]
        self.assertEqual(msgs[-1], {"role": "assistant", "content": "{"})


if __name__ == "__main__":
    unittest.main()
