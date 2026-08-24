# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — SAMPLE email copy (short founder-to-founder note).

This is the copy used by --sample-only runs. It is intentionally simpler than the
normalized workflow's full personalized body: a short, low-pressure note built around
ONE verified observation, using the task-approved "Rough visual thought for …" shape.

Honesty guards (shared with the normalized layer):
  * The attachment sentence (identical to copy_integration.ATTACHMENT_SENTENCE) is woven
    in ONLY when an image is actually attached; a preview with no image carries zero
    "attached" language. Enforced by copy_integration.assert_attachment_language_consistent.
  * No first name is invented — when a verified first name is absent, a neutral team
    greeting is used ("Hi <Company> team —").
  * The canonical signature + compliance footer come from preflight.py, byte-identical
    to the normalized workflow.
  * The composed body is fabrication-scanned by the caller (defence in depth).
"""
from __future__ import annotations

import os as _os
import sys as _sys
from typing import Tuple

_VCO_DIR = _os.path.dirname(_os.path.abspath(__file__))
_OUTREACH_DIR = _os.path.dirname(_VCO_DIR)
for _p in (_VCO_DIR, _OUTREACH_DIR):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import preflight  # noqa: E402  (canonical signature/footer/link renderers)
import copy_integration as ci  # noqa: E402  (single source of the attachment sentence)

SUBJECT_TEMPLATE = "Rough visual thought for {company}"

_POSITIONING = ("MOTIONX is focused on this bridge: product film first, then the "
                "web/campaign system around it.")
_CTA = "Worth me tightening this into a more concrete direction?"


def _company(item: dict) -> str:
    return (item.get("business_name") or item.get("company")
            or item.get("prospect_name") or "your team").strip()


def _greeting(item: dict) -> str:
    first = (item.get("first_name") or "").strip()
    if first:
        return f"Hey {first} —"
    return f"Hi {_company(item)} team —"


def _naturalize_observation(obs: str) -> str:
    """Turn a third-person sourcing note into a natural second-person clause.

    Only a small, meaning-preserving reshaping of a leading boilerplate phrase — the
    factual content is never changed. Falls back to the verbatim observation.
    """
    o = (obs or "").strip()
    if not o:
        return ""
    # The observation is embedded mid-sentence between em dashes, so drop a single
    # trailing period to avoid "… product story. — and had a thought".
    if o.endswith(".") and not o.endswith(".."):
        o = o[:-1]
    low = o.lower()
    for prefix, repl in (
        ("official site sells ", "you sell "),
        ("the official site sells ", "you sell "),
        ("official site offers ", "you offer "),
        ("official site ", "your site "),
        ("the site ", "your site "),
    ):
        if low.startswith(prefix):
            return repl + o[len(prefix):]
    # Otherwise decapitalize the first character so it reads inside the sentence.
    return o[0].lower() + o[1:] if o[:1].isupper() else o


def build_sample_bodies(item: dict, postal_address: str,
                        attached: bool) -> Tuple[str, str, str]:
    """Return (subject, plaintext, html) for the sample founder-to-founder note.

    `attached` controls the single attachment paragraph; the honesty guard asserts the
    "attached" language appears iff `attached` is True.
    """
    company = _company(item)
    subject = SUBJECT_TEMPLATE.format(company=company)
    obs = _naturalize_observation(item.get("verified_observation", ""))
    domain = (item.get("domain") or "").strip()
    where = domain or f"{company}'s site"

    if obs:
        opening = (f"{_greeting(item)} I was looking at {where} — {obs} — and had a "
                   f"quick thought for how the product could open as a cinematic "
                   f"motion piece.")
    else:
        # No verified observation → stay generic; never invent a specific detail.
        opening = (f"{_greeting(item)} I was looking at {where} and had a quick "
                   f"thought for how the product could open as a cinematic motion "
                   f"piece.")

    paras = [opening]
    if attached:
        paras.append(ci.ATTACHMENT_SENTENCE)
    paras.append(_POSITIONING)
    paras.append(_CTA)
    body_core = "\n\n".join(paras)

    plaintext = "\n\n".join(
        [body_core, preflight.render_signature(), preflight.render_footer(postal_address)])
    html = _render_html(body_core, postal_address)

    # Honesty guard: attachment language iff an image is attached.
    ci.assert_attachment_language_consistent(plaintext, attached=attached)
    ci.assert_attachment_language_consistent(html, attached=attached)
    return subject, plaintext, html


def _render_html(body_core: str, postal_address: str) -> str:
    body = body_core.replace("\n\n", "<br><br>")
    sig = (f"--<br>Charles Dai<br>Founder, MotionX<br>"
           f"Product Films · Motion-First Websites · Launch Systems<br>"
           f"Website: {preflight.render_link_html()}<br>"
           f"Email Address: charles@madebymotionx.com")
    foot = f"MOTIONX · {postal_address}<br>{preflight.OPT_OUT_LINE}"
    return f'<div dir="auto">{body}<br><br>{sig}<br><br>{foot}</div>'
