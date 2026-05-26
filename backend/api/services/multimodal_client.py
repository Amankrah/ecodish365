"""Multi-provider multimodal (image + text) chat client for PKG-IMG-1.

Mirrors `environmental_impact_model.src.llm_client` (text-only) but extends
to image-in / JSON-out: the packaged-food extractor sends a single image
(plus a structured-output prompt) and expects a strict JSON object back.

Provider selection follows the same `LLM_PROVIDER` env convention as the
text-only client. Model overrides are split:
  - MULTIMODAL_LLM_MODEL — this module (vision extraction)
  - CHAT_LLM_MODEL       — llm_client.py (decomposition, CNF ranking, …)

Multimodal model defaults (2026-05-26):
  - openai     → "gpt-4o-mini"             (vision-capable, ~$0.15/$0.60 per 1M tok + $0.0036/image at 1024 long-edge)
  - anthropic  → "claude-haiku-4-5"        (vision-capable; image-pricing folded into input-token rate ~$1/$5 per 1M)

We deliberately default to the cheaper *mini* / *haiku* models. NF panel
extraction is a text-recognition task, not a reasoning task, so the larger
models add little quality at 5-10× the cost. If quality on the 5-product
test panel proves marginal, the model can be overridden via the
`MULTIMODAL_LLM_MODEL` env var without a code change.

Image normalisation:
  - HEIC (iOS default) and AVIF (modern web compression) are opened via
    `pillow-heif` / `pillow-avif-plugin` and re-encoded to JPEG before
    being sent. The vision APIs accept JPEG/PNG/WebP/GIF but not HEIC/AVIF.
  - Long-edge downscale to 1600 px caps the per-call cost and keeps NF
    panel text legible (we tested: a 4032 px iPhone photo of a NF panel
    is unchanged in extraction accuracy after 1600-px downscale).

Caching: SHA-256 of the normalised JPEG bytes + prompt_version is the
Django-cache key. A duplicate upload of the same image (e.g. user clicks
"re-extract") returns the cached extraction for free for 7 days.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import os
from typing import Any, Optional, Protocol, runtime_checkable

# Register HEIC/AVIF openers at module import. Both are idempotent + cheap.
try:
    import pillow_heif  # type: ignore
    pillow_heif.register_heif_opener()
except ImportError:
    pass
try:
    import pillow_avif  # noqa: F401  # importing registers the plugin
except ImportError:
    pass

from PIL import Image, UnidentifiedImageError


logger = logging.getLogger(__name__)


_MULTIMODAL_DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5",
}

# Long-edge cap for downscaling. Below this we don't re-encode; above we
# do. Chosen empirically — Canadian NF panels remain fully legible.
MAX_IMAGE_LONG_EDGE_PX = 1600

# Max bytes accepted from the wire. Above this we reject before paying the
# LLM call — keeps an accidental 50 MB phone-burst-mode upload from
# bursting the rate-limit budget.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


def _env_provider() -> str:
    return (os.environ.get("LLM_PROVIDER") or "openai").lower()


def _env_model(provider: str) -> str:
    explicit = os.environ.get("MULTIMODAL_LLM_MODEL")
    if explicit:
        return explicit
    return _MULTIMODAL_DEFAULT_MODELS[provider]


# --- Image normalisation -------------------------------------------------


class ImageDecodeError(ValueError):
    """Raised when the uploaded bytes can't be decoded as an image."""


def normalize_image_bytes(raw: bytes) -> tuple[bytes, dict]:
    """Decode an image of any supported format, downscale if >1600 px long
    edge, and re-encode as JPEG quality 85. Returns (jpeg_bytes, metadata).

    Metadata fields:
      - source_format: 'JPEG' | 'PNG' | 'WEBP' | 'HEIF' | 'AVIF' | ...
      - source_dimensions: (w, h) of the input
      - normalised_dimensions: (w, h) of the JPEG output
      - normalised_bytes: len(jpeg_bytes)
      - sha256: hex digest of jpeg_bytes (the cache + audit key)
    """
    if len(raw) > MAX_UPLOAD_BYTES:
        raise ImageDecodeError(
            f"Image too large: {len(raw)} bytes (max {MAX_UPLOAD_BYTES}).",
        )
    try:
        im = Image.open(io.BytesIO(raw))
        source_format = im.format or "UNKNOWN"
        source_dim = im.size
        # Force load before any conversion (Pillow is lazy).
        im.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ImageDecodeError(f"Could not decode image: {exc}") from exc

    # Strip alpha + ICC profile differences by converting to RGB. JPEG
    # doesn't support alpha; doing this once avoids surprises downstream.
    if im.mode != "RGB":
        im = im.convert("RGB")

    # Downscale if necessary.
    long_edge = max(im.size)
    if long_edge > MAX_IMAGE_LONG_EDGE_PX:
        scale = MAX_IMAGE_LONG_EDGE_PX / long_edge
        new_size = (int(im.size[0] * scale), int(im.size[1] * scale))
        im = im.resize(new_size, Image.Resampling.LANCZOS)

    # Re-encode as JPEG quality 85. This is the standard image-quality
    # / size sweet spot for OCR-ish workloads.
    out = io.BytesIO()
    im.save(out, format="JPEG", quality=85, optimize=True)
    jpeg_bytes = out.getvalue()

    return jpeg_bytes, {
        "source_format": source_format,
        "source_dimensions": list(source_dim),
        "normalised_dimensions": list(im.size),
        "normalised_bytes": len(jpeg_bytes),
        "sha256": hashlib.sha256(jpeg_bytes).hexdigest(),
    }


# --- Client interface ---------------------------------------------------


@runtime_checkable
class MultimodalJSONClient(Protocol):
    """Duck-typed client. `image_jpeg_bytes` is the already-normalised JPEG
    from `normalize_image_bytes`. Returns parsed JSON object."""

    model: str
    provider: str

    def extract_with_image(
        self,
        *,
        system: str,
        user: str,
        image_jpeg_bytes: bytes,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict: ...


class OpenAIMultimodalClient:
    """Wraps `openai.OpenAI()`. Uses chat.completions with vision content
    parts (data: URL with base64 JPEG) and `response_format=json_object`
    for strict JSON output."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        from openai import OpenAI  # lazy import
        self._client = OpenAI(api_key=api_key)
        self.model = model or _env_model("openai")
        self.provider = "openai"

    def extract_with_image(
        self,
        *,
        system: str,
        user: str,
        image_jpeg_bytes: bytes,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict:
        b64 = base64.b64encode(image_jpeg_bytes).decode("ascii")
        kwargs: dict = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": user},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}",
                        "detail": "high",  # higher cost but needed for small NF text
                    }},
                ]},
            ],
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        rsp = self._client.chat.completions.create(**kwargs)
        content = rsp.choices[0].message.content or "{}"
        return _parse_json_permissive(content)


class AnthropicMultimodalClient:
    """Wraps `anthropic.Anthropic()`. Vision via message content blocks
    with type='image'; JSON output via assistant-prefill when supported,
    otherwise an explicit JSON-only user suffix."""

    def __init__(self, api_key: str, model: Optional[str] = None):
        import anthropic  # lazy import
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model or _env_model("anthropic")
        self.provider = "anthropic"

    def extract_with_image(
        self,
        *,
        system: str,
        user: str,
        image_jpeg_bytes: bytes,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> dict:
        b64 = base64.b64encode(image_jpeg_bytes).decode("ascii")
        user_blocks = [
            {"type": "image", "source": {
                "type": "base64", "media_type": "image/jpeg", "data": b64,
            }},
            {"type": "text", "text": user},
        ]

        # Newer Anthropic models reject temperature and/or assistant prefill.
        # Try the legacy path first (Haiku), then fall back gracefully.
        attempts: tuple[tuple[bool, bool, str], ...] = (
            (True, True, user),
            (True, False, user),
            (False, False, user + "\n\nRespond with ONE JSON object only. "
             "No markdown fences, no commentary."),
        )
        last_exc: Optional[Exception] = None
        for use_prefill, use_temperature, user_text in attempts:
            blocks = list(user_blocks)
            blocks[1] = {"type": "text", "text": user_text}
            messages: list[dict] = [{"role": "user", "content": blocks}]
            if use_prefill:
                messages.append({"role": "assistant", "content": "{"})
            kwargs: dict = {
                "model": self.model,
                "max_tokens": max_tokens or 2048,
                "system": system,
                "messages": messages,
            }
            if use_temperature:
                kwargs["temperature"] = temperature
            try:
                rsp = self._client.messages.create(**kwargs)
                text = rsp.content[0].text if rsp.content else ""
                raw = ("{" + text) if use_prefill else text
                return _parse_json_permissive(raw)
            except Exception as exc:  # noqa: BLE001 — probe model capabilities
                last_exc = exc
                msg = str(exc).lower()
                if "temperature" in msg and "deprecated" in msg:
                    continue
                if "prefill" in msg or "end with a user message" in msg:
                    continue
                raise
        if last_exc is not None:
            raise last_exc
        return {}


def _parse_json_permissive(raw: str) -> dict:
    """Same tolerant parser as llm_client._parse_json_permissive — strips
    fenced code blocks + falls back to outermost {...} extraction."""
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


# --- Factory ------------------------------------------------------------


def build_multimodal_client(
    *,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> Optional[MultimodalJSONClient]:
    """Factory matching `llm_client.build_chat_json_client`. Returns None
    when no API key is available (caller short-circuits to a 503).
    """
    provider = (provider or _env_provider()).lower()
    if provider == "openai":
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            logger.info("OPENAI_API_KEY missing; MultimodalJSONClient unavailable")
            return None
        try:
            return OpenAIMultimodalClient(api_key=key, model=model)
        except ImportError as exc:  # pragma: no cover
            logger.warning("openai SDK not importable: %s", exc)
            return None
    if provider == "anthropic":
        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            logger.info("ANTHROPIC_API_KEY missing; MultimodalJSONClient unavailable")
            return None
        try:
            return AnthropicMultimodalClient(api_key=key, model=model)
        except ImportError as exc:
            logger.warning(
                "anthropic SDK not installed; install with "
                "`pip install anthropic` to use LLM_PROVIDER=anthropic: %s", exc,
            )
            return None
    raise ValueError(
        f"Unknown LLM_PROVIDER: {provider!r}. "
        f"Supported: {sorted(_MULTIMODAL_DEFAULT_MODELS)}"
    )
