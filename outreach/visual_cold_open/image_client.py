# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — gpt-image-2 client.

Thin wrapper over the official OpenAI Images API. Designed to be fully unit-testable
OFFLINE: inject a fake client (any object exposing `.images.generate(...)` and
`.models.retrieve(...)`); only when no client is injected does it lazily import the
real `openai` SDK and read OPENAI_API_KEY from the environment.

Guarantees:
  * Uses model exactly `gpt-image-2` (a mismatched model raises).
  * Never prints or logs the API key (redacted __repr__; key kept local).
  * Fails closed when the key or a client is missing.
  * Bounded exponential backoff on transient API errors.
  * Decodes the returned base64 image to bytes; the caller writes it OUTSIDE the repo.
"""
from __future__ import annotations

import base64
import os as _os
import sys as _sys
import time
from dataclasses import dataclass
from typing import Callable, Optional

_VCO_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _VCO_DIR not in _sys.path:
    _sys.path.insert(0, _VCO_DIR)

import config as vco_config  # noqa: E402
import safety  # noqa: E402


class ImageAccessError(RuntimeError):
    """Raised when gpt-image-2 is not reachable (missing key / no client / auth)."""


class ImageGenerationError(RuntimeError):
    """Raised when generation fails after bounded retries, or QA-unusable output."""


@dataclass
class GeneratedImage:
    data: bytes
    model: str
    size: str
    quality: str
    image_format: str

    @property
    def byte_len(self) -> int:
        return len(self.data)


class GptImageClient:
    def __init__(
        self,
        model: str = vco_config.REQUIRED_IMAGE_MODEL,
        api_key: Optional[str] = None,
        client: object = None,
        max_retries: int = 3,
        backoff_base_seconds: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if model != vco_config.REQUIRED_IMAGE_MODEL:
            raise ImageAccessError(
                f"This mode requires model {vco_config.REQUIRED_IMAGE_MODEL!r}; a "
                f"downgrade to {model!r} needs Charles's explicit authorization."
            )
        self.model = model
        self.max_retries = max(1, int(max_retries))
        self.backoff_base_seconds = float(backoff_base_seconds)
        self._sleep = sleep
        self._injected_client = client
        # Keep the key ONLY as a local flag of presence; do not retain it on the
        # instance in a way that could be logged.
        self._has_env_key = bool(api_key or _os.environ.get("OPENAI_API_KEY"))
        self._explicit_key = api_key  # not exposed via __repr__

    def __repr__(self) -> str:  # never leak the key
        return (f"GptImageClient(model={self.model!r}, "
                f"has_key={self._has_env_key}, injected_client={self._injected_client is not None})")

    # ── client resolution ──────────────────────────────────────────────────────
    def _client(self):
        if self._injected_client is not None:
            return self._injected_client
        if not self._has_env_key:
            raise ImageAccessError(
                "OPENAI_API_KEY is not set. Export it (or use approved secret "
                "management) before generating images. It is never read from the repo."
            )
        try:
            import openai  # lazy — real dependency, not needed for unit tests
        except Exception as exc:  # pragma: no cover - environment dependent
            raise ImageAccessError(
                "The 'openai' package is not installed. `pip install openai` in the "
                "CLI environment before live/image generation."
            ) from exc
        kwargs = {}
        if self._explicit_key:
            kwargs["api_key"] = self._explicit_key
        self._injected_client = openai.OpenAI(**kwargs)
        return self._injected_client

    # ── preflight (cheap access check, no batch generation) ─────────────────────
    def preflight(self) -> dict:
        """Confirm gpt-image-2 is callable without generating a batch of images.

        Returns {"ok": bool, "detail": str}. Uses a cheap models.retrieve call; a
        missing key/permission fails closed.
        """
        try:
            client = self._client()
        except ImageAccessError as exc:
            return {"ok": False, "detail": safety.redact_secrets(str(exc))}
        retrieve = getattr(getattr(client, "models", None), "retrieve", None)
        if callable(retrieve):
            try:
                retrieve(self.model)
                return {"ok": True, "detail": f"{self.model} reachable"}
            except Exception as exc:  # pragma: no cover - network dependent
                return {"ok": False,
                        "detail": safety.redact_secrets(f"{self.model} not reachable: {exc}")}
        # No models API on the (fake) client — treat presence of a client as ok.
        return {"ok": True, "detail": "client present (models.retrieve unavailable)"}

    # ── generation ──────────────────────────────────────────────────────────────
    def generate(
        self,
        prompt: str,
        size: str = vco_config.DEFAULT_IMAGE_SIZE,
        quality: str = vco_config.DEFAULT_IMAGE_QUALITY,
        image_format: str = vco_config.DEFAULT_IMAGE_FORMAT,
    ) -> GeneratedImage:
        client = self._client()
        images = getattr(client, "images", None)
        if images is None or not hasattr(images, "generate"):
            raise ImageAccessError("client does not expose images.generate(...)")

        request = {
            "model": self.model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": 1,
        }
        # gpt-image supports output_format; pass it when a non-default is requested.
        if image_format:
            request["output_format"] = image_format

        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                resp = images.generate(**request)
                data = self._decode_response(resp)
                return GeneratedImage(
                    data=data, model=self.model, size=size,
                    quality=quality, image_format=image_format,
                )
            except (ImageGenerationError, ImageAccessError):
                raise
            except Exception as exc:  # transient API/network error → bounded backoff
                last_exc = exc
                if attempt + 1 < self.max_retries:
                    self._sleep(self.backoff_base_seconds * (2 ** attempt))
        raise ImageGenerationError(
            safety.redact_secrets(f"image generation failed after "
                                  f"{self.max_retries} attempts: {last_exc}")
        )

    @staticmethod
    def _decode_response(resp) -> bytes:
        """Extract and base64-decode the first image from an Images API response."""
        data_list = getattr(resp, "data", None)
        if data_list is None and isinstance(resp, dict):
            data_list = resp.get("data")
        if not data_list:
            raise ImageGenerationError("image response had no data")
        first = data_list[0]
        b64 = getattr(first, "b64_json", None)
        if b64 is None and isinstance(first, dict):
            b64 = first.get("b64_json")
        if not b64:
            raise ImageGenerationError(
                "image response had no b64_json (gpt-image-2 returns base64, not a URL)"
            )
        try:
            return base64.b64decode(b64)
        except Exception as exc:
            raise ImageGenerationError(f"could not base64-decode image data: {exc}") from exc


def save_image_bytes(path: str, data: bytes, repo_root: str = "") -> str:
    """Write image bytes to `path`, refusing to write inside the git repo.

    Returns the absolute path written. Creates parent directories as needed.
    """
    abs_path = _os.path.abspath(_os.path.expanduser(path))
    if repo_root:
        repo_abs = _os.path.abspath(_os.path.expanduser(repo_root))
        if abs_path == repo_abs or abs_path.startswith(repo_abs + _os.sep):
            raise ValueError(
                f"refusing to write a generated asset inside the repo: {abs_path}"
            )
    _os.makedirs(_os.path.dirname(abs_path), exist_ok=True)
    with open(abs_path, "wb") as fh:
        fh.write(data)
    return abs_path
