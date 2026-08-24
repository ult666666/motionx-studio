# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — email copy integration.

The visual-cold-open mode adds ONE honest sentence about the attached rough sketch —
and only when an image is actually attached. When no image is attached, the body is
the normalized draft body with zero 'attached' language (a misleading draft is never
created).

Bodies are rendered through the existing deterministic renderers in `preflight.py`
(canonical signature, compliance footer, https anchor), so the signature/footer/link
hygiene is byte-identical to the normalized workflow. The attachment sentence is
inserted as its own paragraph immediately BEFORE the signature block.
"""
from __future__ import annotations

import os as _os
import sys as _sys
from typing import Optional, Tuple

_VCO_DIR = _os.path.dirname(_os.path.abspath(__file__))
_OUTREACH_DIR = _os.path.dirname(_VCO_DIR)
for _p in (_VCO_DIR, _OUTREACH_DIR):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import preflight  # noqa: E402  (the normalized workflow's renderer + validator)

# The exact acceptable attachment language (task-approved wording).
ATTACHMENT_SENTENCE = (
    "I attached a rough 3-frame sketch — not polished work, just a visual way to show "
    "the direction: product-world opening, motion/interaction moment, then how that "
    "same world could extend into a launch page or campaign system."
)

# A distinctive sentinel unique to ATTACHMENT_SENTENCE — detecting the attachment
# copy by this phrase (not by generic tokens like "attach"/"sketch") avoids both false
# positives from legitimate prospect copy and false negatives from wording drift.
_ATTACHMENT_SENTINEL = "rough 3-frame sketch"


def item_to_draftmodel(item: dict) -> "preflight.DraftModel":
    """Map a normalized-draft source item onto a DraftModel for rendering."""
    price = item.get("optional_price", item.get("selected_price"))
    try:
        price = int(price) if price not in (None, "", "None") else None
    except (TypeError, ValueError):
        price = None
    return preflight.DraftModel(
        prospect_name=item.get("prospect_name", "") or item.get("business_name", ""),
        recipient_email=item.get("recipient_email", ""),
        recipient_type=item.get("recipient_type", "generic"),
        recipient_confidence=item.get("recipient_confidence", "MEDIUM"),
        greeting=item.get("greeting", ""),
        verified_observation=item.get("verified_observation", ""),
        concise_interpretation=item.get("concise_interpretation", ""),
        central_idea=item.get("central_idea", ""),
        motionx_positioning_sentence=item.get("motionx_positioning_sentence", ""),
        cta=item.get("cta", ""),
        selected_offer=item.get("selected_offer", ""),
        subject=item.get("subject", ""),
        optional_price=price,
    )


def _insert_before_signature_plain(plaintext: str, sentence: str) -> str:
    """Insert `sentence` as a paragraph just before the '--' signature delimiter."""
    marker = "\n\n--\n"
    idx = plaintext.find(marker)
    if idx == -1:
        # Fallback: append before end (should not happen with canonical render).
        return plaintext + "\n\n" + sentence
    return plaintext[:idx] + "\n\n" + sentence + plaintext[idx:]


def _insert_before_signature_html(html: str, sentence: str) -> str:
    marker = "<br><br>--<br>"
    idx = html.find(marker)
    if idx == -1:
        return html.replace("</div>", f"<br><br>{sentence}</div>")
    return html[:idx] + f"<br><br>{sentence}" + html[idx:]


def build_bodies(
    item: dict,
    postal_address: str,
    attached: bool,
) -> Tuple[str, str, str]:
    """Return (subject, plaintext, html).

    When `attached` is True the approved attachment sentence is woven in; when False
    the body is the normalized body with no attachment language whatsoever.
    """
    d = item_to_draftmodel(item)
    subject = d.subject
    plaintext = preflight.render_plaintext(d, postal_address)
    html = preflight.render_html(d, postal_address)

    if attached:
        plaintext = _insert_before_signature_plain(plaintext, ATTACHMENT_SENTENCE)
        html = _insert_before_signature_html(html, ATTACHMENT_SENTENCE)
    return subject, plaintext, html


def body_mentions_attachment(text: str) -> bool:
    return _ATTACHMENT_SENTINEL in (text or "").lower()


def assert_attachment_language_consistent(text: str, attached: bool) -> None:
    """Guard: 'attached' language must appear iff an image is attached."""
    mentions = body_mentions_attachment(text)
    if attached and not mentions:
        raise ValueError("attachment expected but body has no attachment sentence")
    if not attached and mentions:
        raise ValueError(
            "body contains attachment language but no image is attached — refusing to "
            "create a misleading draft"
        )
