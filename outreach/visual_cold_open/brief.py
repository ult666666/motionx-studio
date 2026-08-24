# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — internal visual brief + gpt-image-2 prompt builder.

A brief is built ONLY from fields the normalized draft workflow already verified for
the prospect (business name, category, the verified observation, source notes, and the
proposed creative direction). It invents no product features, customers, metrics,
awards, testimonials, funding, partnerships, or prior MOTIONX relationship, and it
never implies MOTIONX has already worked with the prospect.

The image prompt embeds explicit anti-fabrication instructions to the model and a
"rough speculative concept sketch, not final client work" framing.
"""
from __future__ import annotations

import os as _os
import re
import sys as _sys
from dataclasses import dataclass, field
from typing import List, Optional

# ── path bootstrap (repo convention: no __init__.py; import siblings + preflight) ─
_VCO_DIR = _os.path.dirname(_os.path.abspath(__file__))
_OUTREACH_DIR = _os.path.dirname(_VCO_DIR)
for _p in (_VCO_DIR, _OUTREACH_DIR):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

# ── Fabrication guard ───────────────────────────────────────────────────────────
# Phrases/patterns that would imply an invented client, metric, award, testimonial,
# funding, partnership, press, or an existing MOTIONX relationship. Case-insensitive.
FABRICATION_PATTERNS = [
    (r"\bcase stud(y|ies)\b", "implies a case study / prior engagement"),
    (r"\btestimonial", "implies a testimonial"),
    (r"\baward[- ]?winning\b|\bawards?\b", "implies an award"),
    (r"\btrusted by\b|\bas seen (in|on)\b|\bfeatured (in|on)\b", "implies press/social proof"),
    (r"\bour client\b|\bworked with\b|\bpartnered with\b|\bpartnership with\b",
     "implies a client / partnership / prior work"),
    (r"\bclients?\b|\bcustomers? love\b", "implies named clients"),
    (r"\b\d+\s?%|\b\d+x\b|\bROI\b|\bconversion rate\b|\bincreased\b .*\bby\b",
     "implies an invented metric"),
    (r"\braised\b .*\b(funding|round|seed|series [a-z])\b|\bfunded\b", "implies funding"),
    (r"\bmillions? of (users|customers)\b|\b#1\b|\bbest[- ]selling\b|\bbestseller\b",
     "implies unverified traction"),
    (r"\bguarantee(d)?\b", "implies a guarantee"),
    (r"\bpress logos?\b|\blogo wall\b|\bpartner logos?\b", "implies fake press/partner logos"),
    # broadened coverage (finding: spelled-out metrics / ratings / counts / synonyms)
    (r"\b\d+[- ]?star\b", "implies a star rating"),
    (r"\b(doubled|tripled|quadrupled|\d+[- ]?fold)\b", "implies an invented multiplier"),
    (r"\b(hundreds|thousands|millions) of (?:\w+\s+){0,3}"
     r"(customers|users|clients|orders|sales|fans|people|brands|businesses|downloads|reviews)\b",
     "implies unverified traction"),
    (r"\b(serving|over|more than|trusted by)\s+[\d,]+\+?\s+"
     r"(customers|users|clients|brands|companies|orders)\b", "implies a customer count"),
    (r"\b(per ?cent|percent)\b[^.]*\b(increase|growth|lift|boost|more)\b",
     "implies a spelled-out metric"),
    (r"\b(winner|prize|accolade|voted|acclaimed|editor'?s choice|top[- ]rated|"
     r"five[- ]star|five star|number one)\b", "implies an award/rating"),
    (r"\b(rated|reviewed)\b[^.]*\b(\d(\.\d)?)\b[^.]*\b(stars?|/\s?5|out of)\b",
     "implies a review score"),
]
_COMPILED_FAB = [(re.compile(p, re.IGNORECASE), why) for p, why in FABRICATION_PATTERNS]

# Language that would imply MOTIONX already worked with / for the prospect. Includes
# the studio's own core verbs (film/design/build/launch/...) so a generated frame can
# never read as commissioned work.
PRIOR_RELATIONSHIP_PATTERNS = [
    re.compile(r"\bwe (built|made|created|produced|delivered|shipped|filmed|shot|"
               r"directed|animated|designed|redesigned|developed|edited|launched|"
               r"rebranded|handled|ran|crafted|helped|led) (your|their|the|its)\b", re.I),
    re.compile(r"\bour (previous |last |past |earlier )?(work|project|collaboration|"
               r"engagement|campaign|film|partnership) (with|for)\b", re.I),
    re.compile(r"\b(when|since) we (last )?(worked|collaborated)\b", re.I),
    re.compile(r"\bas your (studio|agency|partner|creative|team)\b", re.I),
    re.compile(r"\bwe (brought|delivered|gave) [^.]*\b(to|for) (your|their)\b", re.I),
    re.compile(r"\b(already|previously) (worked|partnered|collaborated) (with|for)\b", re.I),
]


def scan_fabrication(*texts: str) -> List[str]:
    """Return a list of human-readable fabrication findings across the given texts."""
    findings: List[str] = []
    for text in texts:
        if not text:
            continue
        for rx, why in _COMPILED_FAB:
            if rx.search(text):
                findings.append(f"{why}: matched {rx.pattern!r}")
        for rx in PRIOR_RELATIONSHIP_PATTERNS:
            if rx.search(text):
                findings.append(f"implies a prior MOTIONX relationship: {rx.pattern!r}")
    return findings


@dataclass
class VisualBrief:
    company_name: str
    product_or_category: str
    one_verified_detail: str
    why_motion_fits: str
    frame1: str                       # cinematic product/world opening
    frame2: str                       # motion transition / interaction / transformation
    frame3: str                       # extension into website / launch page / campaign
    uncertainty_flags: List[str] = field(default_factory=list)
    fabrication_findings: List[str] = field(default_factory=list)
    source_notes: str = ""

    @property
    def is_clean(self) -> bool:
        return not self.fabrication_findings and bool(self.one_verified_detail.strip())

    def to_dict(self) -> dict:
        return {
            "company_name": self.company_name,
            "product_or_category": self.product_or_category,
            "one_verified_detail": self.one_verified_detail,
            "why_motion_fits": self.why_motion_fits,
            "frame1": self.frame1,
            "frame2": self.frame2,
            "frame3": self.frame3,
            "uncertainty_flags": self.uncertainty_flags,
            "fabrication_findings": self.fabrication_findings,
        }


def _first_nonempty(*vals: Optional[str]) -> str:
    for v in vals:
        if v and str(v).strip():
            return str(v).strip()
    return ""


def build_brief(item: dict) -> VisualBrief:
    """Build a VisualBrief from a normalized-draft source item.

    Uses only already-verified fields. Records uncertainty flags rather than
    inventing missing information; runs the fabrication guard over every text it
    emits so a fabricated detail in the source cannot leak into the prompt.
    """
    company = _first_nonempty(item.get("business_name"), item.get("prospect_name"),
                              item.get("company"))
    category = _first_nonempty(item.get("category"), item.get("prospect_kind"))
    # The single verified product/company detail — the ONLY concrete claim allowed.
    verified_detail = _first_nonempty(
        item.get("verified_observation"),
        item.get("approved_claim_wording"),
        item.get("official_claim_wording"),
    )
    creative_direction = _first_nonempty(item.get("proposed_creative_direction"),
                                         item.get("central_idea"))
    specific_opportunity = _first_nonempty(item.get("specific_opportunity"),
                                           item.get("concise_interpretation"))

    uncertainty: List[str] = []
    if not verified_detail:
        uncertainty.append("no verified product/company detail on the source item")
    if not category:
        uncertainty.append("prospect category/kind not recorded")
    if not creative_direction:
        uncertainty.append("no proposed creative direction recorded")

    why_motion = (
        f"A motion-first product film could open {company}'s world cinematically, "
        f"then carry that same look into a launch page or campaign system — one "
        f"connected direction rather than separate assets."
    )

    # Frames are speculative DIRECTIONS grounded in the verified detail. They never
    # assert new product features; they describe how a rough concept board might look.
    subject = product_phrase = _first_nonempty(category, "the product") or "the product"
    frame1 = (
        f"Opening product world for {company}: a cinematic, product-led establishing "
        f"frame grounded in what was actually observed — {verified_detail or subject}. "
        f"Premium lighting, real setting, no on-screen claims."
    )
    frame2 = (
        f"A motion / interaction moment: {creative_direction or 'a single transition or '
        'behaviour that reveals the product'}. One clear movement — a transformation, "
        f"interface motion, or reveal — not a montage."
    )
    frame3 = (
        f"Extension into a launch page / campaign system: the same visual world "
        f"restated as a website hero or campaign frame"
        + (f", supporting {specific_opportunity}" if specific_opportunity else "")
        + ". Minimal, generic placeholder text only."
    )

    brief = VisualBrief(
        company_name=company or "the company",
        product_or_category=product_phrase,
        one_verified_detail=verified_detail,
        why_motion_fits=why_motion,
        frame1=frame1,
        frame2=frame2,
        frame3=frame3,
        uncertainty_flags=uncertainty,
        source_notes=_first_nonempty(item.get("verified_source_notes")),
    )
    brief.fabrication_findings = scan_fabrication(
        brief.company_name, brief.product_or_category, brief.one_verified_detail,
        brief.why_motion_fits, brief.frame1, brief.frame2, brief.frame3,
    )
    return brief


# ── gpt-image-2 prompt builder ──────────────────────────────────────────────────
_PROMPT_TEMPLATE = """\
Create one horizontal 3-panel rough concept board for a speculative MOTIONX visual \
cold-open outreach asset.

Context:
MOTIONX is a motion-first creative studio. The idea is to show how {company} / \
{product} could be introduced through a cinematic product film and then extended \
into a launch page or campaign system.

Important:
This is a rough speculative concept sketch, not final client work.
Do not include fake metrics, fake testimonials, fake awards, fake customers, fake \
press logos, or claims of prior work.
Do not overuse text. Any text should be minimal, generic, and readable.
Do not invent product features beyond this verified detail: {verified_detail}.
Keep the design premium, cinematic, product-led, motion-first, clean, and modern.

Format:
One horizontal image split into three clearly composed cinematic frames.

Frame 1 — Opening Product World:
{frame1}

Frame 2 — Motion / Interaction Moment:
{frame2}

Frame 3 — Website / Launch / Campaign Extension:
{frame3}

Visual style:
Premium cinematic lighting, clean product-focused composition, modern digital \
surfaces, subtle motion-design cues, elegant depth, launch-film storyboard energy, \
high-end but not overly glossy, rough concept-board feel.

Output:
A polished-looking but clearly conceptual 3-frame board suitable as an email \
attachment."""


def build_image_prompt(brief: VisualBrief) -> str:
    """Render the gpt-image-2 prompt from a (clean) brief."""
    detail = brief.one_verified_detail or (
        f"only the general category '{brief.product_or_category}' — keep it generic "
        f"and invent no specifics"
    )
    return _PROMPT_TEMPLATE.format(
        company=brief.company_name,
        product=brief.product_or_category,
        verified_detail=detail,
        frame1=brief.frame1,
        frame2=brief.frame2,
        frame3=brief.frame3,
    )


# The template's fixed anti-fabrication instruction lines. Only these EXACT lines are
# excluded from the final-prompt scan — never a prefix like "do not", which would have
# let a fabricated interpolated value (e.g. the verified-detail line, which also starts
# with "Do not invent…") slip through unscanned (review finding).
_STATIC_GUARDRAIL_LINES = frozenset({
    "This is a rough speculative concept sketch, not final client work.",
    "Do not include fake metrics, fake testimonials, fake awards, fake customers, "
    "fake press logos, or claims of prior work.",
    "Do not overuse text. Any text should be minimal, generic, and readable.",
})


def prompt_is_clean(prompt: str) -> List[str]:
    """Fabrication scan of the FINAL prompt, excluding ONLY the fixed guardrail lines.

    The interpolated 'Do not invent product features beyond this verified detail: …'
    line is deliberately NOT excluded, so a fabricated verified detail there is still
    scanned (defence in depth on top of build_brief's field-level scan)."""
    scannable = "\n".join(
        line for line in prompt.splitlines()
        if line.strip() not in _STATIC_GUARDRAIL_LINES
    )
    return scan_fabrication(scannable)
