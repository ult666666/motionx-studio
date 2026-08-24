# -*- coding: utf-8 -*-
"""Shared path bootstrap + tiny helpers for the visual-cold-open tests.

Pure stdlib. Imported by each test_visual_*.py. Puts the visual_cold_open package
dir and the outreach dir on sys.path (mirrors outreach/tests/test_preflight.py).
"""
import os
import struct
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTREACH_DIR = os.path.dirname(_TESTS_DIR)
_VCO_DIR = os.path.join(_OUTREACH_DIR, "visual_cold_open")
for _p in (_VCO_DIR, _OUTREACH_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def make_png(width: int = 1536, height: int = 1024, min_bytes: int = 2048) -> bytes:
    """Build a minimal but structurally-valid PNG (signature + IHDR + padding + IEND).

    QA only reads the signature, the IHDR dimensions, and the total size, so this is
    enough to exercise the QA path without Pillow or a real render.
    """
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr_body = struct.pack(">II", width, height) + b"\x08\x06\x00\x00\x00"
    ihdr = struct.pack(">I", len(ihdr_body)) + b"IHDR" + ihdr_body + b"\x00\x00\x00\x00"
    pad_len = max(0, min_bytes - (len(sig) + len(ihdr) + 12))
    pad = struct.pack(">I", pad_len) + b"tEXt" + (b"\x00" * pad_len) + b"\x00\x00\x00\x00"
    iend = struct.pack(">I", 0) + b"IEND" + b"\xaeB`\x82"
    return sig + ihdr + pad + iend


class FakeImageResult:
    def __init__(self, b64):
        self.data = [type("D", (), {"b64_json": b64})()]


class FakeImageClient:
    """Stand-in for GptImageClient — records prompts, returns a valid PNG."""
    def __init__(self, png_bytes=None, model="gpt-image-2", fail_qa=False):
        import base64
        self.model = model
        self.calls = []
        self._png = png_bytes if png_bytes is not None else make_png()
        if fail_qa:  # a tiny non-PNG blob that will fail QA
            self._png = b"ERR"
        self._b64 = base64.b64encode(self._png).decode()

    def preflight(self):
        return {"ok": True, "detail": "fake gpt-image-2 reachable"}

    def generate(self, prompt, size="1536x1024", quality="medium", image_format="png"):
        self.calls.append({"prompt": prompt, "size": size, "quality": quality})
        import image_client as vco_image
        return vco_image.GeneratedImage(
            data=self._png, model=self.model, size=size,
            quality=quality, image_format=image_format)


class FakeGmailBackend:
    """Records draft ops; explodes if any send is attempted."""
    def __init__(self, account="charles@madebymotionx.com", labels=("DRAFT",)):
        self.account = account
        self.labels = list(labels)
        self.created = []
        self.updated = []
        self.next_id = 100

    def verify_account(self):
        return self.account

    def create_draft(self, raw):
        self.created.append(raw)
        self.next_id += 1
        return {"id": f"draft{self.next_id}",
                "message": {"id": f"msg{self.next_id}", "threadId": f"th{self.next_id}"}}

    def update_draft(self, draft_id, raw):
        self.updated.append((draft_id, raw))
        return {"id": draft_id, "message": {"id": "m", "threadId": "t"}}

    def verify_draft_only(self, draft_id):
        return {"draft_id": draft_id, "message_id": "m", "thread_id": "t",
                "label_ids": self.labels, "is_draft": "DRAFT" in self.labels,
                "is_sent": "SENT" in self.labels,
                "draft_only": "DRAFT" in self.labels and "SENT" not in self.labels}
