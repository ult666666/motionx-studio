#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the MIME attachment builder + attachment-copy integration.

Run: python3 outreach/tests/test_visual_mime.py
"""
import base64
import email
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _vco_bootstrap  # noqa: E402
import mime_builder as mb  # noqa: E402
import copy_integration as ci  # noqa: E402

PNG = _vco_bootstrap.make_png()
FROM = "charles@madebymotionx.com"
TO = "team@example.com"

ITEM = {
    "prospect_name": "Example", "business_name": "Example Co",
    "recipient_email": TO, "recipient_type": "generic", "recipient_confidence": "MEDIUM",
    "greeting": "Hi Example team,",
    "verified_observation": "Your homepage shows a single hero product.",
    "concise_interpretation": "The product carries the page.",
    "central_idea": "A short film could open that same world.",
    "motionx_positioning_sentence": "I'm Charles, founder of MOTIONX.",
    "cta": "Worth a quick conversation?",
    "selected_offer": "Product Film", "subject": "Product world",
    "optional_price": 399,
}
POSTAL = "MOTIONX Mailbox, 123 Test St, Testville CA"


def test_build_message_with_attachment_is_multipart_png():
    m = mb.build_message(FROM, TO, "Subj", "plain body", "<div>html body</div>",
                         attachment=("motionx_visual_cold_open_example_2026-07-07.png",
                                     PNG, "image/png"))
    assert mb.has_attachment(m), "message must contain an attachment"
    parts = {p.get_content_type(): p for p in m.walk()}
    assert "image/png" in parts, parts.keys()
    att = parts["image/png"]
    assert att.get_filename() == "motionx_visual_cold_open_example_2026-07-07.png"
    assert att.get_payload(decode=True) == PNG, "attachment bytes must round-trip"


def test_raw_is_base64url_and_round_trips():
    raw = mb.build_raw(FROM, TO, "Subject X", "plain", "<div>h</div>",
                       attachment=("a.png", PNG, "image/png"))
    # base64url must decode cleanly back into a parseable MIME message
    decoded = base64.urlsafe_b64decode(raw.encode())
    msg = email.message_from_bytes(decoded)
    assert msg["Subject"] == "Subject X"
    assert msg["To"] == TO
    got = [p.get_payload(decode=True) for p in msg.walk()
           if p.get_content_disposition() == "attachment"]
    assert got and got[0] == PNG


def test_no_attachment_when_none():
    m = mb.build_message(FROM, TO, "S", "p", "<div>h</div>", attachment=None)
    assert not mb.has_attachment(m)


def test_copy_says_attached_only_when_attached():
    _, plain_yes, html_yes = ci.build_bodies(ITEM, POSTAL, attached=True)
    assert ci.ATTACHMENT_SENTENCE in plain_yes
    assert "rough 3-frame sketch" in html_yes
    _, plain_no, html_no = ci.build_bodies(ITEM, POSTAL, attached=False)
    assert "attach" not in plain_no.lower()
    assert "3-frame" not in plain_no.lower()
    assert "attach" not in html_no.lower()


def test_attachment_language_consistency_guard():
    _, plain_yes, _ = ci.build_bodies(ITEM, POSTAL, attached=True)
    ci.assert_attachment_language_consistent(plain_yes, attached=True)  # ok
    _, plain_no, _ = ci.build_bodies(ITEM, POSTAL, attached=False)
    ci.assert_attachment_language_consistent(plain_no, attached=False)  # ok
    # mismatches must raise
    for body, attached in ((plain_no, True), (plain_yes, False)):
        try:
            ci.assert_attachment_language_consistent(body, attached=attached)
            raise AssertionError("inconsistent attachment language must raise")
        except ValueError:
            pass


def test_body_preserves_canonical_signature_and_footer():
    _, plain, _ = ci.build_bodies(ITEM, POSTAL, attached=True)
    assert "Charles Dai" in plain and "Founder, MotionX" in plain
    assert "Website: https://madebymotionx.com" in plain
    assert POSTAL in plain and "no thanks" in plain
    # attachment sentence sits BEFORE the signature delimiter
    assert plain.index(ci.ATTACHMENT_SENTENCE) < plain.index("\n--\n")


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
