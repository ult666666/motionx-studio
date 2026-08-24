#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the gpt-image-2 client. Pure stdlib; no real API calls.

Run: python3 outreach/tests/test_visual_image_client.py
"""
import base64
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _vco_bootstrap  # noqa: E402  (sets up sys.path)
import image_client as ic  # noqa: E402
import config as vco_config  # noqa: E402


class _Images:
    def __init__(self, b64, fail_times=0):
        self.b64 = b64
        self.fail_times = fail_times
        self.calls = []

    def generate(self, **kwargs):
        self.calls.append(kwargs)
        if self.fail_times > 0:
            self.fail_times -= 1
            raise RuntimeError("transient 503")
        return _vco_bootstrap.FakeImageResult(self.b64)


class _Client:
    def __init__(self, b64, fail_times=0):
        self.images = _Images(b64, fail_times)
        self.models = type("M", (), {"retrieve": staticmethod(lambda m: {"id": m})})()


def test_generate_builds_request_and_decodes_b64():
    png = _vco_bootstrap.make_png()
    b64 = base64.b64encode(png).decode()
    client = _Client(b64)
    gi = ic.GptImageClient(client=client)
    out = gi.generate("a prompt", size="1536x1024", quality="medium", image_format="png")
    assert out.data == png, "decoded bytes must equal the original PNG"
    req = client.images.calls[0]
    assert req["model"] == "gpt-image-2", req
    assert req["prompt"] == "a prompt"
    assert req["size"] == "1536x1024"
    assert req["n"] == 1
    assert req["output_format"] == "png"


def test_save_image_writes_outside_repo_and_refuses_inside():
    png = _vco_bootstrap.make_png()
    with tempfile.TemporaryDirectory() as d:
        repo = os.path.join(d, "repo")
        outside = os.path.join(d, "assets", "x.png")
        os.makedirs(repo)
        p = ic.save_image_bytes(outside, png, repo_root=repo)
        assert os.path.exists(p)
        with open(p, "rb") as fh:
            assert fh.read() == png
        # refuses to write inside the repo
        try:
            ic.save_image_bytes(os.path.join(repo, "bad.png"), png, repo_root=repo)
            raise AssertionError("should have refused to write inside repo")
        except ValueError:
            pass


def test_fails_closed_on_missing_model():
    try:
        ic.GptImageClient(model="dall-e-3")
        raise AssertionError("wrong model must raise")
    except ic.ImageAccessError:
        pass


def test_fails_closed_on_missing_key_and_client():
    saved = os.environ.pop("OPENAI_API_KEY", None)
    try:
        gi = ic.GptImageClient()  # no injected client, no key
        try:
            gi.generate("p")
            raise AssertionError("must fail closed without key/client")
        except ic.ImageAccessError:
            pass
    finally:
        if saved is not None:
            os.environ["OPENAI_API_KEY"] = saved


def test_bounded_backoff_retries_then_succeeds():
    png = _vco_bootstrap.make_png()
    b64 = base64.b64encode(png).decode()
    client = _Client(b64, fail_times=2)
    slept = []
    gi = ic.GptImageClient(client=client, max_retries=3, sleep=lambda s: slept.append(s))
    out = gi.generate("p")
    assert out.data == png
    assert len(client.images.calls) == 3
    assert slept == [1.0, 2.0], f"exponential backoff expected, got {slept}"


def test_retries_exhausted_raises_generation_error():
    client = _Client("x", fail_times=99)
    gi = ic.GptImageClient(client=client, max_retries=2, sleep=lambda s: None)
    try:
        gi.generate("p")
        raise AssertionError("should raise after exhausting retries")
    except ic.ImageGenerationError:
        pass


def test_repr_does_not_leak_key():
    gi = ic.GptImageClient(api_key="sk-shouldnotappear123456", client=object())
    assert "sk-shouldnotappear" not in repr(gi), "repr must not leak the API key"


def test_preflight_ok_and_missing_key():
    png = _vco_bootstrap.make_png()
    b64 = base64.b64encode(png).decode()
    assert ic.GptImageClient(client=_Client(b64)).preflight()["ok"] is True
    saved = os.environ.pop("OPENAI_API_KEY", None)
    try:
        assert ic.GptImageClient().preflight()["ok"] is False
    finally:
        if saved is not None:
            os.environ["OPENAI_API_KEY"] = saved


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
