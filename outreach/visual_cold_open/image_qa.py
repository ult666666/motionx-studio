# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — visual QA.

A practical, dependency-free QA layer: metadata checks, PNG header parsing (pure
stdlib — no Pillow), file/format sanity, prospect/company match, and a fabrication
scan of the brief + prompt. It deliberately does NOT attempt heavy computer vision or
OCR (not available here); it records that in-image text was not machine-inspected as
an uncertainty flag so a human reviews the actual picture.
"""
from __future__ import annotations

import os as _os
import struct
import sys as _sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

_VCO_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _VCO_DIR not in _sys.path:
    _sys.path.insert(0, _VCO_DIR)

import brief as vco_brief  # noqa: E402
import config as vco_config  # noqa: E402

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

_MIME_BY_EXT = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
}


class QAError(RuntimeError):
    pass


def png_dimensions(data: bytes) -> Tuple[int, int]:
    """Return (width, height) from a PNG's IHDR chunk. Raises on a non-PNG."""
    if len(data) < 24 or data[:8] != _PNG_SIGNATURE:
        raise QAError("not a valid PNG (signature mismatch)")
    # After the 8-byte signature: 4-byte length, 4-byte 'IHDR', then width/height.
    if data[12:16] != b"IHDR":
        raise QAError("PNG IHDR chunk not found where expected")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def sniff_format(data: bytes) -> Optional[str]:
    """Best-effort magic-byte format sniff for the formats we might emit."""
    if data[:8] == _PNG_SIGNATURE:
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def mime_for_format(fmt: str) -> str:
    return _MIME_BY_EXT.get((fmt or "").lower().lstrip("."), "application/octet-stream")


@dataclass
class QAResult:
    passed: bool
    checks: dict = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)
    uncertainty_flags: List[str] = field(default_factory=list)
    width: int = 0
    height: int = 0
    mime_type: str = ""

    @property
    def status(self) -> str:
        return (vco_config.STATUS["VERIFIED_DRAFT_ONLY"] if self.passed
                else vco_config.STATUS["BLOCKED_ON_VISUAL_QA"])


def qa_image_file(
    path: str,
    expected_company: str,
    manifest_company: str,
    brief: "vco_brief.VisualBrief",
    prompt: str,
    expected_format: str = "png",
    min_width: int = vco_config.MIN_IMAGE_WIDTH,
    min_height: int = vco_config.MIN_IMAGE_HEIGHT,
) -> QAResult:
    """Run the minimum pass criteria against a generated asset on disk."""
    checks: dict = {}
    failures: List[str] = []
    uncertainty: List[str] = []
    width = height = 0
    mime = ""

    # 1. file exists / readable / non-empty
    checks["file_exists"] = _os.path.exists(path)
    if not checks["file_exists"]:
        failures.append(f"image file does not exist: {path}")
        return QAResult(False, checks, failures, uncertainty)
    try:
        with open(path, "rb") as fh:
            data = fh.read()
        checks["readable"] = True
    except OSError as exc:
        checks["readable"] = False
        failures.append(f"image file unreadable: {exc}")
        return QAResult(False, checks, failures, uncertainty)

    checks["non_empty"] = len(data) > 0
    if not data:
        failures.append("image file is empty (0 bytes)")
        return QAResult(False, checks, failures, uncertainty)

    # 2. format / mime match vs extension
    sniffed = sniff_format(data)
    ext = _os.path.splitext(path)[1].lower().lstrip(".")
    checks["magic_matches_format"] = (sniffed == expected_format.lower())
    checks["extension_matches_format"] = (ext == expected_format.lower())
    if sniffed != expected_format.lower():
        failures.append(
            f"file content is {sniffed or 'unknown'} but expected {expected_format}"
        )
    if ext != expected_format.lower():
        failures.append(f"file extension .{ext} != expected .{expected_format}")
    mime = mime_for_format(expected_format)

    # 3. dimensions plausible (PNG only can be parsed dependency-free)
    if sniffed == "png":
        try:
            width, height = png_dimensions(data)
            checks["dimensions_readable"] = True
        except QAError as exc:
            checks["dimensions_readable"] = False
            failures.append(str(exc))
        else:
            plausible = (width >= min_width and height >= min_height)
            checks["dimensions_plausible"] = plausible
            # A 3-panel board should be horizontal (wider than tall).
            checks["horizontal_aspect"] = width > height
            if not plausible:
                failures.append(
                    f"dimensions {width}x{height} below minimum {min_width}x{min_height}"
                )
            if width <= height:
                uncertainty.append(
                    f"asset is not clearly horizontal ({width}x{height}); expected a "
                    f"wide 3-panel board"
                )
    else:
        uncertainty.append("non-PNG asset: dimensions not parsed without extra deps")

    # 4. known failure/error placeholder heuristic (suspiciously tiny file)
    checks["not_tiny_placeholder"] = len(data) >= 1024
    if len(data) < 1024:
        failures.append(f"asset is suspiciously small ({len(data)} bytes) — likely an "
                        f"error placeholder, not a real render")

    # 5. prospect/company match against the manifest
    match = _company_matches(expected_company, manifest_company)
    checks["company_matches_manifest"] = match
    if not match:
        failures.append(
            f"company mismatch: brief={expected_company!r} vs manifest={manifest_company!r}"
        )

    # 6. fabrication scan of the brief + prompt (defence in depth)
    fab = vco_brief.scan_fabrication(
        brief.one_verified_detail, brief.frame1, brief.frame2, brief.frame3
    )
    fab += vco_brief.prompt_is_clean(prompt)
    checks["fabrication_clean"] = not fab
    if fab:
        failures.extend(f"fabrication in brief/prompt: {f}" for f in fab)

    # 7. in-image text/OCR not inspected (no vision here) — surface for human review
    uncertainty.append(
        "in-image text was not machine-inspected (no OCR/vision available); a human "
        "must confirm no broken tiny text, fake metrics, awards, testimonials, "
        "customer names, or 'case study' language appears in the render"
    )
    uncertainty.extend(brief.uncertainty_flags)

    passed = not failures
    return QAResult(
        passed=passed, checks=checks, failures=failures,
        uncertainty_flags=uncertainty, width=width, height=height, mime_type=mime,
    )


def _company_matches(a: str, b: str) -> bool:
    def norm(s: str) -> str:
        return "".join(ch for ch in (s or "").lower() if ch.isalnum())
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return False
    return na == nb or na in nb or nb in na
