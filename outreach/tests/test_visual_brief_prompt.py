#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the visual brief + gpt-image-2 prompt builder + fabrication guard.

Run: python3 outreach/tests/test_visual_brief_prompt.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _vco_bootstrap  # noqa: E402
import brief as vco_brief  # noqa: E402

CLEAN_ITEM = {
    "business_name": "Basalt Vessels",
    "category": "consumer product brand (glassware)",
    "verified_observation": "the homepage centers a single hand-blown pint glass with "
                            "a mountain shape in the base",
    "proposed_creative_direction": "a slow pour that reveals the mountain in the glass base",
    "specific_opportunity": "a launch page that reuses the film's opening frame",
    "verified_source_notes": "basaltvessels.example/home (Tier 1)",
}


def test_brief_uses_verified_detail_and_all_three_frames():
    b = vco_brief.build_brief(CLEAN_ITEM)
    assert b.company_name == "Basalt Vessels"
    assert "hand-blown pint glass" in b.one_verified_detail
    assert b.frame1 and b.frame2 and b.frame3, "all three frames must be present"
    assert b.is_clean, f"clean item should produce a clean brief: {b.fabrication_findings}"


def test_prompt_contains_template_guardrails_and_detail():
    b = vco_brief.build_brief(CLEAN_ITEM)
    p = vco_brief.build_image_prompt(b)
    for needle in ["3-panel", "speculative concept sketch",
                   "Do not include fake metrics", "Frame 1", "Frame 2", "Frame 3",
                   "Basalt Vessels", "hand-blown pint glass"]:
        assert needle in p, f"prompt missing {needle!r}"
    assert vco_brief.prompt_is_clean(p) == [], "clean prompt must pass fabrication scan"


def test_missing_verified_detail_flags_uncertainty():
    item = dict(CLEAN_ITEM)
    item["verified_observation"] = ""
    item["approved_claim_wording"] = ""
    item["official_claim_wording"] = ""
    b = vco_brief.build_brief(item)
    assert not b.is_clean or b.one_verified_detail == "", "no detail => not fully clean"
    assert any("verified product/company detail" in f for f in b.uncertainty_flags)


def test_fabrication_guard_catches_fabricated_fields():
    findings = vco_brief.scan_fabrication(
        "award-winning glassware trusted by thousands",
        "our client saw conversion rate increase by 40%",
        "we built your last launch page",
    )
    joined = " ".join(findings).lower()
    assert findings, "fabrication guard must catch these"
    assert "award" in joined
    assert "metric" in joined or "conversion" in joined or "%" in joined
    assert any("prior motionx relationship" in f.lower() or "prior work" in f.lower()
               for f in findings)


def test_fabricated_source_detail_blocks_brief():
    item = dict(CLEAN_ITEM)
    item["verified_observation"] = "an award-winning glass trusted by 10,000 customers"
    b = vco_brief.build_brief(item)
    assert b.fabrication_findings, "fabricated verified detail must be flagged"
    assert not b.is_clean


def test_prompt_is_clean_flags_injected_fabrication():
    b = vco_brief.build_brief(CLEAN_ITEM)
    p = vco_brief.build_image_prompt(b)
    tampered = p + "\nAlso show a wall of press logos and a 5-star testimonial."
    assert vco_brief.prompt_is_clean(tampered), "injected fabrication must be caught"


def test_no_prior_relationship_language_in_generated_frames():
    b = vco_brief.build_brief(CLEAN_ITEM)
    for frame in (b.frame1, b.frame2, b.frame3):
        assert vco_brief.scan_fabrication(frame) == [], f"frame leaked fabrication: {frame}"


def test_prior_relationship_catches_studio_core_verbs():
    # finding [7]: studio's own verbs must read as prior work
    for phrase in ("we filmed your latest collection",
                   "we designed the launch page for you",
                   "our previous project with your team",
                   "since we last worked together",
                   "as your creative partner"):
        assert vco_brief.scan_fabrication(phrase), f"should flag prior relationship: {phrase!r}"


def test_fabrication_catches_spelled_out_metrics_ratings_counts():
    # finding [8]: number-word / synonym coverage
    for phrase in ("a five-star rated glass",
                   "sales doubled last quarter",
                   "serving 10,000 customers",
                   "thousands of happy customers",
                   "voted best product of the year",
                   "our editor's choice pick"):
        assert vco_brief.scan_fabrication(phrase), f"should flag fabrication: {phrase!r}"


def test_prompt_scan_does_not_bypass_verified_detail_line():
    # finding [6]: a fabricated verified detail lands on a 'Do not invent ...' line;
    # prompt_is_clean must still catch it (not skip the whole line by prefix).
    item = dict(CLEAN_ITEM)
    item["verified_observation"] = "an award-winning mug trusted by thousands"
    b = vco_brief.build_brief(item)
    # brief-level guard already flags it, but build a prompt from a *clean* brief and
    # inject the fabricated detail onto the guardrail line to prove the scan sees it.
    clean = vco_brief.build_brief(CLEAN_ITEM)
    p = vco_brief.build_image_prompt(clean).replace(
        clean.one_verified_detail, "an award-winning mug trusted by thousands")
    assert vco_brief.prompt_is_clean(p), "fabrication on the verified-detail line must be caught"


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
