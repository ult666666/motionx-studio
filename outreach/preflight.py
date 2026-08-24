"""
MOTIONX outreach — deterministic draft renderer + preflight validator.

Validator engine POLICY_VERSION = "2.7" ("Artifact Readback Integrity"), built on
v2.6 Geography & Scope (+ v2.6.1 signature) over v2.5 Human Voice, v2.4 Humanization /
Batch Diversity & Offer Fit, and v2.3.1 Claim Scope. The umbrella *operating* policy is
v2.9 (config.json / SKILL.md); this engine is what runs pass `policy_version="2.7"` to
preflight(). (The v2.4 notes below are retained as historical context; the current
per-release detail lives in the inline v2.6/v2.7 comments and outreach/CHANGELOG.md.)

Pure standard-library, no network, no secrets. The real postal address is NEVER
embedded here; render_footer() takes it as an argument and is only called with the
real value at Gmail draft-creation time. Tests/fixtures pass a redacted placeholder.

Single source of truth for: the canonical signature, the website URL, offers/prices,
the structured DraftModel, the body renderer, the centralized per-draft preflight()
gate, AND the batch-level batch_preflight() gate. The email is rendered FROM
structured fields, never free-form concatenated, so each part is independently
validateable.

v2.4 adds, all tracing to defects seen in the 2026-06-20 20-draft batch (individual
emails passed while the BATCH looked automated):
  * batch_preflight() — a second stage over the whole authorized batch: subject
    diversity, CTA diversity, positioning diversity, repeated-phrase frequency, and
    near-duplicate-body detection. A draft must pass BOTH preflight() and
    batch_preflight() before it may be created/updated in Gmail.
  * check_negative_framing()  — language that makes the prospect defensive
    ("standard template", "booking template", "reads stronger than…").
  * check_business_inference() — speculation about maturity/occupancy/demand/health
    ("reads like a newer studio still filling its first members").
  * check_existing_asset()    — proposing to create an asset the prospect already has
    ("give it a home of its own" when a memberships page already exists).
  * check_currentness()       — stale seasonal/promo/product premises.
  * check_offer_fit()         — positioning that mismatches the prospect type
    (calling an architecture or wedding-photography film a "product film").

KNOWN CONNECTOR LIMITATION (documented, not a defect): Gmail auto-linkifies any
domain text in a draft and wraps it in a `google.com/url?q=...&source=gmail`
redirect on storage. This cannot be removed via the Gmail connector. The validator
therefore enforces a CLEAN https link at the render layer (no google.com/url, no
q=http, no shorteners). v2.7 update (supersedes the earlier "q=https wrapper is always
an accepted artifact" rule): a `google.com/url` wrapper in the stored *plaintext* is a
HARD FAIL when no htmlBody was supplied — the recipient would see the raw wrapper (the
batch20/21 escape). It is an accepted transport artifact ONLY when render_html() anchors
were supplied (html_supplied=True) and the wrapper carries `q=https://` to the canonical
domain. A `q=http://` downgrade or a wrong destination always fails. See
check_readback_artifact() and the v2.7 note below.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

POLICY_VERSION = "2.7"  # "Artifact Readback Integrity" (built on 2.6 Geography & Scope)

# v2.7 — Artifact Readback Integrity. Traces to a real, repeated escape found 2026-07-02:
# batch20/21 drafts (and at least one message already SENT to a prospect) carried a
# google.com/url?q=…&ust=… redirect wrapper as the VISIBLE "Website:" line in the stored
# plaintext signature. The old readback check only rejected q=http:// downgrades, so a
# wrapper containing q=https passed even though the recipient sees the raw wrapper URL.
# v2.7 makes the stored-artifact check strict and connector-aware: a wrapper in the
# stored plaintext is a HARD FAIL when no htmlBody was supplied (recipient-visible);
# with render_html() anchors supplied, a q=https wrapper to the canonical domain is a
# known connector ingest artifact (the composer/send path uses the clean html part).
# It also verifies the compliance footer (postal line + opt-out) on the stored artifact,
# and hardens the price gate (any single $ amount must match the selected offer's price).

# v2.6 — Geography & Scope Integrity. Traces to a real escape: the 2026-06-23 batch7
# run created a Gmail draft for a Canadian brand (Victory Barber, Victoria BC) before it
# was caught manually at the CRM stage. The authorized outreach scope is US-based
# independents ("nationwide" = US unless Charles widens it). This makes geography a
# DETERMINISTIC gate so an out-of-scope prospect can never reach draft creation again.
# A draft fails GEOGRAPHY_OUT_OF_SCOPE unless prospect_country normalizes to the US, OR
# context explicitly authorizes a wider scope (context["geography_authorized"]=True).
ALLOWED_COUNTRIES = {"US", "USA", "U.S.", "U.S.A.", "UNITED STATES",
                     "UNITED STATES OF AMERICA", "AMERICA"}

# ── Canonical constants ────────────────────────────────────────────────────────
# v2.6.1 — Signature standard updated to Charles's own template (left as an edited draft
# 2026-06-24). Adds the "--" delimiter and the labelled Website:/Email Address: lines, which
# the earlier v2.3 block had stripped. The website keeps the full https:// scheme so Gmail
# stores q=https (a bare domain downgrades to q=http). The postal address + opt-out remain a
# separately-injected compliance footer (postal never hard-coded in the repo).
CANONICAL_SIGNATURE = (
    "--\n"
    "Charles Dai\n"
    "Founder, MotionX\n"
    "Product Films · Motion-First Websites · Launch Systems\n"
    "Website: https://madebymotionx.com\n"
    "Email Address: charles@madebymotionx.com"
)
CANONICAL_URL_DISPLAY = "madebymotionx.com"
CANONICAL_URL_HREF = "https://madebymotionx.com"
OPT_OUT_LINE = 'Not relevant? Reply "no thanks" and I won\'t follow up.'
POSTAL_PLACEHOLDER = "{{MOTIONX_POSTAL_ADDRESS}}"

OFFERS = {
    "Product Film": 399,
    "Motion-First Website": 699,
    "Film + Website Launch System": 999,
    "Campaign Content Add-On": 190,
}

# v2.5 length standard — a longer AI email is still an AI email, but a too-short email
# usually omits the reasoning that makes the idea credible. Hard 75–140, prefer 90–125.
WORD_MIN, WORD_MAX = 75, 140
WORD_PREF_MIN, WORD_PREF_MAX = 90, 125
WORD_SIMPLE_MIN = 75  # an 82-word email with real reasoning should not fail for being <90

GENERIC_PREFIXES = {
    "info", "hello", "contact", "support", "bookings", "office",
    "experience", "admin", "team", "hi", "studio", "hey", "sales",
}

# Signature: any of these substrings (case-insensitive) is drift. (v2.6.1: the new
# canonical signature intentionally includes "Website:", "Email Address:", and the
# founder address charles@madebymotionx.com, so those are no longer banned. We still
# ban the public alias in the founder signature, "Available Worldwide", a bare http://
# downgrade, link-tracker wrappers, social handles, and a "Based in" location line.)
SIGNATURE_BANNED = [
    "hello@madebymotionx.com", "available worldwide", "http://",
    "google.com/url", "linkedin", "instagram", "twitter", "facebook", "based in",
]

# Link hygiene (render layer): reject these substrings anywhere a link appears.
LINK_BANNED = ["google.com/url", "q=http", "bit.ly", "tinyurl", "t.co/", "goo.gl",
               "http://madebymotionx", "https://https://", "://www.google.com/url"]

# Free-work CTA — implies unpaid speculative production.
FREE_WORK_PATTERNS = [
    r"\bsketch\b", r"\bmock ?up\b", r"\bmock this up\b", r"\bstoryboard\b",
    r"free (sample|sketch|storyboard|concept|version|mock|design)",
    r"rough (visual )?direction", r"visual treatment",
    r"\bput together a (visual|rough|quick)", r"\bdesign a quick\b",
    r"first concept for free", r"\bsee a rough\b", r"\bi'?ll make (you )?something\b",
    r"\bmake (you )?a (free |quick )?(sample|version|sketch)",
]

# Literary / AI-sounding phrases — flagged for editorial review (treated as fail in
# strict preflight; a non-strict editorial pass may downgrade specific ones).
AI_PHRASES = [
    "feel of-a-piece", "of-a-piece", "could carry it", "real early-adopter offer",
    "unlock", "elevate", "transform your", "leverage", "seamless",
    "compelling visual narrative", "immersive experience", "bring the brand to life",
    "maximize conversion", "drive engagement", "visual ecosystem", "cohesive journey",
    "tell your story in a powerful way", "huge opportunity", "partnership proposal",
    "next level", "game-chang", "cutting-edge", "unlock your brand",
]

# Medical / regulated claim inferences — banned unless narrowly supported (and even
# then normally avoided).
MEDICAL_BANNED_PATTERNS = [
    r"how the treatment (tighten|work|works|lifts)", r"beneath the skin",
    r"under the skin", r"prov(e|es|ing) effectiveness", r"guaranteed (results|outcome)",
    r"visible results for every", r"clinically superior", r"increases bookings",
    r"improves conversion", r"demonstrat(e|es|ing) (how|what)",
    r"showing how the treatment", r"how it (tightens|works) (beneath|under)",
]
CLAIMS_SENSITIVE_HINTS = {
    "med spa", "medical spa", "medspa", "aesthetic", "wellness", "healthcare",
    "clinic", "supplement", "dermatolog", "injectable", "cosmetic", "skin tightening",
}

SUBJECT_BANNED = ["partnership proposal", "quick question", "guaranteed",
                  "huge opportunity", "last chance", "free concept", "re:", "fwd:"]
SUBJECT_REPEAT_PATTERNS = [r"^a page for ", r"^a short film for ",
                           r"^a (concept|creative idea) for "]

# ── v2.4 individual-defect constants ────────────────────────────────────────────
# Negative framing — language that puts the prospect on the defensive by judging
# their current site/marketing. (Defect: Flirt "clean, standard template";
# Enchanted Glow "runs on a booking template / reads stronger than…".)
NEGATIVE_FRAMING_PATTERNS = [
    r"\bstandard template\b", r"\bgeneric template\b", r"\bbasic template\b",
    r"\bcookie[- ]cutter\b", r"\bjust a template\b", r"\bon a (booking )?template\b",
    r"\binside a (booking )?template\b", r"\breads? stronger\b", r"\blooks? stronger\b",
    r"\bwould look better\b", r"\bis (out ?dated|dated|generic|basic|plain|weak|bland)\b",
    r"\byour (current )?(site|website|page|copy|branding) is\b",
    r"\b(site|website|page) (is|feels|looks) (out ?dated|generic|basic|plain|weak|dated|tired|flat)\b",
    r"\bdoesn'?t convert\b", r"\bnot converting\b", r"\blosing (customers|bookings|sales)\b",
    r"\bbranding is inconsistent\b", r"\bstronger than what you have\b",
    r"\bbetter than your current\b", r"\bclean,? standard\b",
]

# Unsupported business-inference — speculation about internal conditions from public
# promotions. (Defect: Rise "reads like a newer studio still filling its first members".)
BUSINESS_INFERENCE_PATTERNS = [
    r"\bstill filling\b", r"\bfilling (its|their|your) first\b", r"\bnewer (studio|business|brand)\b",
    r"\bnew(ly)? (opened|launched) (studio|business)\b", r"\bstill (growing|building|ramping)\b",
    r"\bbuilding (initial|early) demand\b", r"\btrying to (build|fill|grow)\b",
    r"\b(low|weak|soft) (occupancy|demand|bookings|membership|sales)\b",
    r"\bstruggling\b", r"\bfill(ing)? classes\b", r"\bfill(ing)? (the|your) (studio|calendar|schedule)\b",
    r"\bread(s)? like a (newer|new|young|small)\b", r"\bprobably (trying|looking) to\b",
    r"\bramp(ing)? up\b", r"\bget(ting)? off the ground\b", r"\bearly[- ]stage\b",
    r"\bfind(ing)? (its|their|your) (first|early) (members|customers|clients)\b",
]

# Phrases tracked for BATCH frequency (softer than the hard AI_PHRASES ban). Recurring
# across the 20-draft batch made it read automated. Each is a normalized substring.
TRACKED_BATCH_PHRASES = [
    "a natural fit", "a natural moment", "a good moment", "a good, time-bound",
    "could carry", "could run on", "could run with", "could sit on", "give it a home",
    "a home of its own", "a moment of its own", "i think a short", "i run motionx",
    "founder-led studio creating", "founder-led studio building", "founder-led studio making",
    "would a short written concept be useful", "would a short written outline be useful",
    "is a natural fit for", "natural fit for a short film", "is a good moment for",
    "would be useful", "on the product page and your social", "on the collection page and your social",
]

# "create a NEW asset" verbs — combined with existing_assets / an asset noun, this is a
# contradiction (proposing what they already have). (Defect: My Skin "a home of its own"
# when a memberships page already exists.)
ASSET_CREATION_PHRASES = [
    r"\bgive (it|them|the \w+) a home\b", r"\b(a )?home of its own\b",
    r"\bits own (dedicated )?(page|home)\b", r"\b(a )?page of its own\b",
    r"\bcreate (a|its own) \w+ page\b", r"\bbuild (a|its own) \w+ page\b",
    r"\bgive (the|your) \w+ (a )?(dedicated )?(page|home)\b",
    r"\bneeds? (a|its own) (dedicated )?(page|home)\b",
    r"\ba dedicated (page|home) of its own\b",
]

# Offer/prospect-fit: prospect kinds where "product film" positioning is a mismatch.
NON_PRODUCT_PROSPECT_KINDS = {"service_brand", "studio", "photographer", "architecture",
                             "lighting_studio", "design_studio", "med_spa", "fitness", "wellness"}
CURRENTNESS_STATUSES = {"CURRENT", "UPCOMING", "EVERGREEN", "ENDED", "UNCLEAR", "STALE_PAGE_ONLY"}

# ── v2.5 "Human Voice & Conversational Credibility" constants ────────────────────
# Abstract agency vocabulary. Not banned outright, but concentration reads as AI/agency
# copy rather than a founder's note. >=2 distinct hits → ABSTRACT_LANGUAGE_OVERUSE.
ABSTRACT_TERMS = [
    "visual identity", "campaign ecosystem", "brand narrative", "conversion journey",
    "immersive", "cinematic destination", "cohesive system", "cohesive visual",
    "distinctive storytelling", "carry the story", "motion language",
    "strategic launch asset", "focused destination", "digital ecosystem",
    "customer journey", "elevate", "amplify", "unlock your", "transform your brand",
    "recognizably ", "brand story across", "visual storytelling",
]
# Softer crutch words tracked at BATCH level (overuse across the batch), not per-draft.
SOFT_CRUTCH_WORDS = ["focused", "clear", "cinematic", "motion-first", "carry", "seamless"]

# Hard AI-phrase patterns — phrases a founder would basically never type. Any → fail.
AI_VOICE_PATTERNS = [
    r"cohesive visual identity", r"visual identity across", r"digital ecosystem",
    r"cinematic destination", r"elevates? the customer journey", r"carry the story across",
    r"carry that recognition", r"a cohesive system", r"strategic launch asset",
    r"immersive (brand )?experience", r"elevate your brand", r"amplify your",
    r"unlock your brand", r"distinctive storytelling", r"brand narrative",
    r"recognizably [A-Z][a-z]+",  # "recognizably AKILA"
]

# Modal hedges. >MODAL_MAX in a body reads as non-committal AI prose.
MODAL_PATTERN = re.compile(
    r"\b(could|would|might|can|cannot|could'?ve)\b|\b(i|we|it|you|they|that)'d\b", re.I)
MODAL_MAX = 4

# CTAs that became generic crutches in earlier batches.
GENERIC_CTAS = {
    "would a short written concept be useful?",
    "would a short written outline be useful?",
    "would a concise concept note be useful?",
    "would a brief written direction be useful?",
}

# Mini-proposal smell — a cold email should open a conversation, not scope production.
MINI_PROPOSAL_TERMS = [
    r"shot list", r"\bdeliverables?\b", r"channel (roll-?out|strategy|plan)",
    r"\broll-?out\b", r"placement plan", r"\bphase [12]\b", r"\bmilestones?\b",
    r"\bscope of work\b", r"\bstatement of work\b", r"production plan",
    r"\bfive[- ]shot\b", r"\bsix[- ]shot\b", r"sequence of \w+ shots",
]
EM_DASH = "—"
MAX_EM_DASHES = 1
MAX_SENTENCE_WORDS = 34  # a sentence longer than this is hard to say aloud
HUMAN_VOICE_FIELDS = ("human_reaction", "why_this_idea", "prospect_specific_connection")


# ── Structured draft model ─────────────────────────────────────────────────────
@dataclass
class DraftModel:
    prospect_name: str
    recipient_email: str
    recipient_type: str          # "personal" | "generic" | "brand"
    recipient_confidence: str    # "HIGH" | "MEDIUM" | "LOW"
    greeting: str
    verified_observation: str
    concise_interpretation: str
    central_idea: str
    motionx_positioning_sentence: str
    cta: str
    selected_offer: str
    subject: str
    optional_price: Optional[int] = None
    greeting_evidence: str = ""          # recorded evidence supporting a named greeting
    claims_sensitive: bool = False
    official_claim_wording: str = ""
    official_claim_url: str = ""
    verified_source_notes: str = ""
    signature: str = CANONICAL_SIGNATURE
    # v2.3.1 claim-scope fields (Claim Scope & Evidence Precision)
    observation_scope: str = "PAGE"           # PAGE|WEBSITE|SOCIAL_CHANNEL|MULTI_CHANNEL|SITE_WIDE|CROSS_CHANNEL
    pages_checked: list = field(default_factory=list)
    channels_checked: list = field(default_factory=list)  # e.g. ["official_website", "instagram"]
    absence_claim: bool = False
    absence_evidence_level: str = "OBSERVED_ON_PAGE"  # see EVIDENCE_LEVELS
    approved_claim_wording: str = ""
    # v2.4 humanization / offer-fit / currentness fields
    prospect_kind: str = "product_brand"      # product_brand|service_brand|studio|photographer|architecture|lighting_studio|design_studio|med_spa|fitness|wellness|other
    existing_assets: list = field(default_factory=list)  # asset keys already on the site, e.g. ["memberships_page"]
    proposed_asset: str = ""                   # asset key the idea would create, e.g. "memberships_page"
    currentness_status: str = "CURRENT"       # CURRENT|UPCOMING|EVERGREEN|ENDED|UNCLEAR|STALE_PAGE_ONLY
    reframed_as_evergreen: bool = False        # True if a stale/ended premise is honestly reframed
    product_availability: str = "AVAILABLE"   # AVAILABLE|UNAVAILABLE|NA
    promotion_status: str = "NA"              # CURRENT|ENDED|NA
    seasonal_relevance: str = "CURRENT"       # CURRENT|PASSED|NA
    verified_current_date: str = ""           # ISO date the currentness was re-checked
    # v2.5 human-voice fields (personalization-by-thought, not just by-fact)
    human_reaction: str = ""                  # a genuine reaction in Charles's own words
    why_this_idea: str = ""                   # why THIS idea came to mind for THIS prospect
    prospect_specific_connection: str = ""    # a connection between two observed details
    voice_risk: str = "LOW"                   # LOW|MEDIUM|HIGH (editorial)
    brand_noun_removal_result: str = "DISTINCT"  # DISTINCT|GENERIC (Phase 7 test result)
    conversational_read_result: str = "PASS"  # PASS|FAIL (read-aloud editorial pass)
    price_rationale: str = ""                 # why price was included/omitted
    credibility_style: str = ""               # how MOTIONX is introduced (for batch variety)
    # v2.6 geography & scope integrity
    prospect_country: str = "US"              # firsthand-verified country of the business
    geography_evidence: str = ""              # the on-site source line proving the country


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def count_words(text: str) -> int:
    return len(re.findall(r"\S+", text))


def personalized_body(d: DraftModel) -> str:
    """Greeting → CTA only (the part counted for word-count + ratio)."""
    parts = [d.greeting, d.verified_observation, d.concise_interpretation,
             d.central_idea, d.motionx_positioning_sentence, d.cta]
    return "\n\n".join(p for p in parts if p)


# ── Deterministic renderers ────────────────────────────────────────────────────
def render_signature() -> str:
    return CANONICAL_SIGNATURE


def render_footer(postal_address: str) -> str:
    return f"MOTIONX · {postal_address}\n{OPT_OUT_LINE}"


def render_link_html() -> str:
    return f'<a href="{CANONICAL_URL_HREF}">{CANONICAL_URL_DISPLAY}</a>'


def render_plaintext(d: DraftModel, postal_address: str) -> str:
    return "\n\n".join([personalized_body(d), render_signature(), render_footer(postal_address)])


def render_html(d: DraftModel, postal_address: str) -> str:
    body = personalized_body(d).replace("\n\n", "<br><br>")
    # v2.6.1 signature: "--" delimiter, labelled Website:/Email Address: lines, website
    # rendered as a clean https anchor (display = domain), founder email shown.
    sig = (f"--<br>Charles Dai<br>Founder, MotionX<br>"
           f"Product Films · Motion-First Websites · Launch Systems<br>"
           f"Website: {render_link_html()}<br>"
           f"Email Address: charles@madebymotionx.com")
    foot = f"MOTIONX · {postal_address}<br>{OPT_OUT_LINE}"
    return f'<div dir="auto">{body}<br><br>{sig}<br><br>{foot}</div>'


# ── Individual validators (return list of (code, reason)) ───────────────────────
def check_signature(sig: str) -> list[tuple[str, str]]:
    fails = []
    low = sig.lower()
    for bad in SIGNATURE_BANNED:
        if bad in low:
            fails.append(("SIGNATURE_DRIFT", f"signature contains banned token: {bad!r}"))
    if sig.strip() != CANONICAL_SIGNATURE:
        fails.append(("SIGNATURE_DRIFT", "signature does not match the canonical block exactly"))
    return fails


def check_links(text: str) -> list[tuple[str, str]]:
    fails = []
    low = text.lower()
    for bad in LINK_BANNED:
        if bad in low:
            fails.append(("REDIRECT_URL", f"link contains banned pattern: {bad!r}"))
    return fails


def check_gmail_readback_link(stored_body: str, is_plaintext: bool = True) -> list[tuple[str, str]]:
    """Run on the body read back FROM Gmail. v2.7: in the PLAINTEXT body the
    google.com/url wrapper is a defect (the recipient sees the raw wrapper URL —
    the batch20/21 escape); it is tolerated only inside an htmlBody anchor href
    (is_plaintext=False). A q=http downgrade or wrong domain always fails."""
    fails = []
    low = stored_body.lower()
    if "q=http://" in low:
        fails.append(("REDIRECT_URL", "Gmail stored an http:// destination (downgrade)"))
    if "madebymotionx.com" not in low:
        fails.append(("REDIRECT_URL", "canonical domain missing from stored body"))
    if is_plaintext and "google.com/url" in low:
        fails.append(("READBACK_ARTIFACT_DEFECT",
                      "google.com/url wrapper present in stored plaintext — recipient "
                      "would see the raw redirect URL (batch20/21 defect)"))
    return fails


def check_readback_artifact(stored_plaintext: str,
                            expected_price: Optional[int] = None,
                            html_supplied: bool = False) -> list[tuple[str, str]]:
    """v2.7 post-creation gate: run on the PLAINTEXT body read back from Gmail after
    create_draft. Verifies the artifact a recipient would actually see — link hygiene,
    resolved postal footer, opt-out line — independent of what the DraftModel claimed.

    Connector reality (verified by canary drafts 2026-07-02): since ~2026-06-30 the
    Gmail connector rewrites ANY url/domain in the submitted plaintext into a
    google.com/url wrapper at ingest (scheme-less input additionally downgrades to
    q=http). The stored html part cannot be read back while a draft. Therefore:
    - html_supplied=False (plaintext-only create): a wrapper in the stored plaintext IS
      recipient-visible (Gmail derives the html view from it) -> HARD FAIL. This is
      exactly how the batch20/21 sent messages shipped with visible wrappers.
    - html_supplied=True (render_html() anchors were provided): Gmail's composer loads
      the html part, so what Charles reviews and sends is the clean anchor; the mangled
      stored plaintext is regenerated by Gmail at UI-send time. A q=https wrapper to the
      canonical domain is then a known ingest artifact (record it in the packet); q=http
      or a non-canonical destination still HARD FAILS.
    A draft whose stored artifact fails here must be re-created (never shipped as-is)."""
    fails = []
    low = stored_plaintext.lower()
    if "q=http://" in low:
        fails.append(("REDIRECT_URL", "Gmail stored an http:// destination (downgrade)"))
    if "madebymotionx.com" not in low:
        fails.append(("REDIRECT_URL", "canonical domain missing from stored body"))
    if "google.com/url" in low:
        if not html_supplied:
            fails.append(("READBACK_ARTIFACT_DEFECT",
                          "google.com/url wrapper in stored plaintext with NO htmlBody "
                          "supplied — recipients would see the raw redirect URL "
                          "(batch20/21 defect); re-create with render_html() anchors"))
        elif "q=https://madebymotionx.com" not in low:
            fails.append(("READBACK_ARTIFACT_DEFECT",
                          "wrapper present and destination is not the canonical "
                          "https://madebymotionx.com"))
    if POSTAL_PLACEHOLDER.lower() in low:
        fails.append(("READBACK_ARTIFACT_DEFECT",
                      "postal placeholder was never substituted in the stored draft"))
    if OPT_OUT_LINE.lower() not in low:
        fails.append(("READBACK_ARTIFACT_DEFECT", "opt-out line missing from stored draft"))
    if not re.search(r"^motionx · .+", low, re.MULTILINE):
        fails.append(("READBACK_ARTIFACT_DEFECT",
                      "postal footer line (MOTIONX · <address>) missing from stored draft"))
    if expected_price is not None:
        amounts = {int(a.replace(",", "")) for a in re.findall(r"\$(\d[\d,]*)", stored_plaintext)}
        if amounts and amounts != {expected_price}:
            fails.append(("READBACK_ARTIFACT_DEFECT",
                          f"stored draft price(s) {sorted(amounts)} != expected ${expected_price}"))
    return fails


def resolve_recipient(email: str, evidence_personal: bool) -> tuple[str, str]:
    """Return (confidence, recipient_type)."""
    local = email.split("@", 1)[0].lower()
    if evidence_personal:
        return "HIGH", "personal"
    if local in GENERIC_PREFIXES:
        return "LOW", "generic"
    # brand-ish gmail / ambiguous personal-looking address with no recorded evidence
    return "MEDIUM", "brand"


def check_greeting(d: DraftModel) -> list[tuple[str, str]]:
    fails = []
    g = d.greeting.strip().rstrip(",").lower()
    is_team = g.endswith(" team")
    if is_team:
        return fails  # team greeting always safe
    # named greeting: requires HIGH, or MEDIUM with recorded evidence
    if d.recipient_confidence == "HIGH":
        return fails
    if d.recipient_confidence == "MEDIUM" and d.greeting_evidence.strip():
        return fails
    fails.append(("RECIPIENT_UNCERTAIN",
                  "first-name greeting without HIGH confidence or recorded mailbox evidence"))
    return fails


def check_free_work_cta(cta: str) -> list[tuple[str, str]]:
    low = cta.lower()
    for pat in FREE_WORK_PATTERNS:
        if re.search(pat, low):
            return [("FREE_WORK_CTA", f"CTA implies free speculative work: matched /{pat}/")]
    return []


def check_ai_language(text: str) -> list[tuple[str, str]]:
    fails = []
    low = text.lower()
    for phrase in AI_PHRASES:
        if phrase in low:
            fails.append(("AI_LANGUAGE", f"literary/AI-sounding phrase: {phrase!r}"))
    return fails


def check_medical(d: DraftModel) -> list[tuple[str, str]]:
    if not d.claims_sensitive:
        return []
    fails = []
    blob = " ".join([d.verified_observation, d.concise_interpretation,
                     d.central_idea, d.motionx_positioning_sentence, d.cta]).lower()
    for pat in MEDICAL_BANNED_PATTERNS:
        if re.search(pat, blob):
            fails.append(("MEDICAL_CLAIM_UNSUPPORTED",
                          f"regulated-claim inference: matched /{pat}/"))
    if not d.official_claim_url:
        fails.append(("MEDICAL_CLAIM_UNSUPPORTED",
                      "claims-sensitive prospect without recorded official_claim_url"))
    return fails


def check_offer_and_price(d: DraftModel) -> list[tuple[str, str]]:
    fails = []
    if d.selected_offer not in OFFERS:
        fails.append(("MULTIPLE_OFFERS", f"unknown/!single offer: {d.selected_offer!r}"))
    blob = personalized_body(d)
    prices = set(re.findall(r"\$\d[\d,]*", blob))
    if len(prices) > 1:
        fails.append(("PRICE_MISMATCH", f"multiple prices in body: {sorted(prices)}"))
    elif len(prices) == 1:
        # v2.7 hardening: a lone $ amount must equal the selected offer's configured
        # price even when optional_price was never set (previously a wrong lone price
        # with optional_price=None passed silently).
        amount = int(next(iter(prices)).lstrip("$").replace(",", ""))
        if amount != OFFERS.get(d.selected_offer):
            fails.append(("PRICE_MISMATCH",
                          f"body price ${amount} != configured ${OFFERS.get(d.selected_offer)} "
                          f"for {d.selected_offer}"))
    if d.optional_price is not None:
        if d.optional_price != OFFERS.get(d.selected_offer):
            fails.append(("PRICE_MISMATCH",
                          f"price ${d.optional_price} != configured ${OFFERS.get(d.selected_offer)} for {d.selected_offer}"))
        if f"${d.optional_price}" not in blob and f"${d.optional_price:,}" not in blob:
            fails.append(("PRICE_MISMATCH", "optional_price set but not present in body"))
    # crude service-menu detector: two distinct offer names both named in body
    named = [o for o in OFFERS if o.lower() in blob.lower()]
    if len(named) > 1:
        fails.append(("MULTIPLE_OFFERS", f"multiple offers named in body: {named}"))
    return fails


def check_word_count(d: DraftModel) -> tuple[int, list[tuple[str, str]]]:
    n = count_words(personalized_body(d))
    if n < WORD_MIN:
        return n, [("BODY_TOO_SHORT", f"{n} words < {WORD_MIN}")]
    if n > WORD_MAX:
        return n, [("BODY_TOO_LONG", f"{n} words > {WORD_MAX}")]
    return n, []


def check_diagnosis_ratio(d: DraftModel) -> list[tuple[str, str]]:
    """Deterministic structural FLOOR: observation+interpretation = max 2 compact
    sentences (1 neutral recognition + 1 interpretation, per the three-layer model) and
    the idea/fit/MOTIONX/CTA side must hold the majority of the words. This is a backstop,
    NOT the whole rule: the stricter *editorial* target — at most ONE *friction/criticism*
    sentence and >=70% of the email on the idea + next step (config
    max_diagnosis_sentences=1, idea_and_next_step_min_ratio=0.7; tone-guide.md /
    SKILL.md Step 7) — is the authoritative bar on conflict, enforced by the empathy
    editor + check_negative_framing rather than this ratio gate."""
    fails = []
    diag_sentences = len(_sentences(d.verified_observation)) + len(_sentences(d.concise_interpretation))
    if diag_sentences > 2:
        fails.append(("DIAGNOSIS_HEAVY",
                      f"observation+interpretation = {diag_sentences} sentences (max 2)"))
    diag_words = count_words(d.verified_observation) + count_words(d.concise_interpretation)
    idea_words = (count_words(d.central_idea) + count_words(d.motionx_positioning_sentence)
                  + count_words(d.cta))
    if idea_words < diag_words:
        fails.append(("DIAGNOSIS_HEAVY",
                      f"diagnosis words ({diag_words}) >= idea/next-step words ({idea_words})"))
    return fails


def check_subject(subject: str, recent_subjects: Optional[list[str]] = None) -> list[tuple[str, str]]:
    fails = []
    low = subject.lower().strip()
    if not (2 <= count_words(subject) <= 6):
        fails.append(("SUBJECT_WEAK", f"subject is {count_words(subject)} words (want ~2-5)"))
    for bad in SUBJECT_BANNED:
        if bad in low:
            fails.append(("SUBJECT_WEAK", f"banned subject phrase: {bad!r}"))
    for pat in SUBJECT_REPEAT_PATTERNS:
        if re.search(pat, low):
            fails.append(("SUBJECT_WEAK", f"overused subject pattern: /{pat}/"))
    if any(ord(c) > 0x2600 for c in subject):
        fails.append(("SUBJECT_WEAK", "subject contains emoji"))
    if recent_subjects:
        for prev in recent_subjects:
            if prev and _subject_shape(prev) == _subject_shape(subject):
                fails.append(("SUBJECT_WEAK", f"structural repeat of recent subject: {prev!r}"))
                break
    return fails


_SUBJECT_FUNCWORDS = {"a", "an", "the", "for", "in", "of", "to", "with", "and",
                      "your", "my", "on", "at"}


def _subject_shape(s: str) -> str:
    """Keep function words literal, X-out content words — so 'A short film for X'
    and 'Your scent map in motion' are distinct shapes (only true templated repeats
    like 'A short film for Y' collapse together)."""
    toks = re.findall(r"[a-z0-9'+]+", s.lower())
    return " ".join(t if t in _SUBJECT_FUNCWORDS else "X" for t in toks)


def validate_state_transition(action: str, record: dict) -> list[tuple[str, str]]:
    """Draft creation/update must never set sent/contacted/follow_up state."""
    fails = []
    if action in ("draft_created", "draft_updated", "draft_failed_preflight"):
        if record.get("status") in ("sent", "contacted"):
            fails.append(("STATE_INVALID", f"draft action wrote status={record.get('status')!r}"))
        if record.get("follow_up_due") or record.get("follow_up_started"):
            fails.append(("STATE_INVALID", "draft action started a follow-up timer"))
        if record.get("sent_at"):
            fails.append(("STATE_INVALID", "draft action set sent_at"))
    return fails


# ── Claim-scope validator (v2.3.1 "Claim Scope & Evidence Precision") ───────────
# A limited review must produce a limited claim. An absolute absence claim needs
# recorded evidence at the matching scope.
OBSERVATION_SCOPES = {"PAGE", "WEBSITE", "SOCIAL_CHANNEL", "MULTI_CHANNEL", "SITE_WIDE", "CROSS_CHANNEL"}
EVIDENCE_LEVELS = {"OBSERVED_ON_PAGE", "CHECKED_OFFICIAL_CHANNEL", "CHECKED_RELEVANT_SITE_ROUTES",
                   "VERIFIED_SITE_WIDE", "VERIFIED_CROSS_CHANNEL", "INSUFFICIENT"}
# evidence levels that justify a site-wide ("nothing on the website") absence claim:
_SITE_ROUTE_EVIDENCE = {"CHECKED_RELEVANT_SITE_ROUTES", "VERIFIED_SITE_WIDE", "VERIFIED_CROSS_CHANNEL"}
# evidence that justifies a cross-channel ("nothing anywhere, incl. social") claim:
_CROSS_CHANNEL_EVIDENCE = {"VERIFIED_CROSS_CHANNEL"}

# (pattern, failure_code) for film/video or "only/entirely" claims spanning a line/brand/channel
_CROSS_CHANNEL_ABSENCE = [
    (r"no film for the line", "ABSENCE_EVIDENCE_INSUFFICIENT"),
    (r"there is no film", "ABSENCE_EVIDENCE_INSUFFICIENT"),
    (r"\bno video\b", "ABSENCE_EVIDENCE_INSUFFICIENT"),
    (r"no .{0,30}film appears across", "ABSENCE_EVIDENCE_INSUFFICIENT"),
    (r"uses only still", "CHANNEL_SCOPE_OVERREACH"),
    (r"carried entirely by still", "CHANNEL_SCOPE_OVERREACH"),
    (r"\bonly still photography\b", "CHANNEL_SCOPE_OVERREACH"),
]
# patterns asserting a site-wide absence of a page/route
_SITE_WIDE_ABSENCE = [
    r"no page of its own", r"has no .{0,20}\bpage\b",
    r"does not (currently )?(list|have) .{0,30}\bpage\b",
    r"\bno dedicated .{0,30}\bpage\b", r"\bno booking path\b", r"\bno sign-?up\b",
]
_GENERIC_ABSOLUTE = [r"\bnowhere\b", r"does not exist anywhere"]


def scope_violations(text, evidence_level="OBSERVED_ON_PAGE", channels_checked=None):
    """Return [(code, reason)] for absolute absence claims unsupported by the
    recorded evidence scope. Page-scoped phrasing ('I didn't see X on that page',
    'currently led by') does not trigger — only true absolutes do."""
    channels_checked = channels_checked or []
    low = text.lower()
    fails = []
    has_cross_channel = evidence_level in _CROSS_CHANNEL_EVIDENCE and len(channels_checked) >= 2
    has_site_routes = evidence_level in _SITE_ROUTE_EVIDENCE
    for pat, code in _CROSS_CHANNEL_ABSENCE:
        if re.search(pat, low) and not has_cross_channel:
            fails.append((code, f"cross-channel/line absence /{pat}/ needs VERIFIED_CROSS_CHANNEL (2+ channels); have {evidence_level}, channels={channels_checked}"))
    for pat in _SITE_WIDE_ABSENCE:
        if re.search(pat, low) and not has_site_routes:
            fails.append(("CLAIM_SCOPE_UNSUPPORTED", f"site-wide absence /{pat}/ needs CHECKED_RELEVANT_SITE_ROUTES+; have {evidence_level}"))
    for pat in _GENERIC_ABSOLUTE:
        if re.search(pat, low) and not (has_site_routes or has_cross_channel):
            fails.append(("ABSOLUTE_LANGUAGE_UNSUPPORTED", f"absolute /{pat}/ without verified-scope evidence"))
    return fails


def check_claim_scope(d: DraftModel) -> list[tuple[str, str]]:
    return scope_violations(personalized_body(d), d.absence_evidence_level, d.channels_checked)


# ── v2.4 individual validators ──────────────────────────────────────────────────
def check_negative_framing(d: DraftModel) -> list[tuple[str, str]]:
    """Flag language that judges the prospect's current site/marketing (puts them on
    the defensive). Preferred framing: what's working now → the moment → one extension."""
    blob = personalized_body(d).lower()
    fails = []
    for pat in NEGATIVE_FRAMING_PATTERNS:
        if re.search(pat, blob):
            fails.append(("NEGATIVE_FRAMING", f"prospect-defensive phrasing: matched /{pat}/"))
    return fails


def check_business_inference(d: DraftModel) -> list[tuple[str, str]]:
    """Flag speculation about internal business conditions (maturity, occupancy,
    demand, revenue, health) inferred from public promotions."""
    blob = personalized_body(d).lower()
    fails = []
    for pat in BUSINESS_INFERENCE_PATTERNS:
        if re.search(pat, blob):
            fails.append(("UNSUPPORTED_INFERENCE", f"inferred internal business condition: matched /{pat}/"))
    return fails


def check_existing_asset(d: DraftModel) -> list[tuple[str, str]]:
    """Fail if the idea proposes creating an asset the prospect already has.
    Two signals: (1) proposed_asset is recorded as an existing_asset; (2) 'give it a
    home / a page of its own' creation phrasing while existing_assets is non-empty."""
    fails = []
    existing = {a.strip().lower() for a in d.existing_assets}
    if d.proposed_asset and d.proposed_asset.strip().lower() in existing:
        fails.append(("PROPOSED_ASSET_ALREADY_EXISTS",
                      f"idea proposes {d.proposed_asset!r} which is already in existing_assets"))
    if existing:
        blob = personalized_body(d).lower()
        for pat in ASSET_CREATION_PHRASES:
            if re.search(pat, blob):
                fails.append(("PROPOSED_ASSET_ALREADY_EXISTS",
                              f"creation phrasing /{pat}/ but the prospect already has assets {sorted(existing)}"))
                break
    return fails


def check_currentness(d: DraftModel) -> list[tuple[str, str]]:
    """Stale seasonal/promo/product premises. A draft built on ended/stale content
    fails unless it is honestly reframed as evergreen/future (reframed_as_evergreen)."""
    fails = []
    if d.currentness_status not in CURRENTNESS_STATUSES:
        fails.append(("CURRENTNESS_UNVERIFIED", f"unknown currentness_status {d.currentness_status!r}"))
    if d.currentness_status == "UNCLEAR":
        fails.append(("CURRENTNESS_UNVERIFIED", "currentness could not be verified"))
    if d.currentness_status in ("ENDED", "STALE_PAGE_ONLY") and not d.reframed_as_evergreen:
        fails.append(("STALE_OPPORTUNITY",
                      f"premise is {d.currentness_status} and not reframed as evergreen/future"))
    if d.product_availability == "UNAVAILABLE":
        fails.append(("PRODUCT_UNAVAILABLE", "proposed product/SKU is not currently available"))
    if d.promotion_status == "ENDED":
        fails.append(("PROMOTION_ENDED", "proposed promotion has ended"))
    if d.seasonal_relevance == "PASSED" and not d.reframed_as_evergreen:
        fails.append(("STALE_OPPORTUNITY", "seasonal window has passed and is not reframed"))
    return fails


def check_geography(d: DraftModel, context: Optional[dict] = None) -> list[tuple[str, str]]:
    """v2.6 — geography is a deterministic scope gate. The business must be US-based
    (firsthand-verified) unless context explicitly authorizes a wider scope. Currency
    or a /us storefront does NOT prove US; only a verified country does. A blank
    prospect_country is treated as UNVERIFIED and fails (fail-closed)."""
    context = context or {}
    if context.get("geography_authorized"):
        return []
    norm = (d.prospect_country or "").strip().upper().rstrip(".")
    norm_variants = {norm, norm.replace(".", ""), (d.prospect_country or "").strip().upper()}
    if norm_variants & ALLOWED_COUNTRIES:
        return []
    if not norm:
        return [("GEOGRAPHY_OUT_OF_SCOPE",
                 "prospect_country is blank/UNVERIFIED — fail-closed (verify US before drafting)")]
    return [("GEOGRAPHY_OUT_OF_SCOPE",
             f"prospect_country={d.prospect_country!r} is outside the authorized US scope")]


def check_offer_fit(d: DraftModel) -> list[tuple[str, str]]:
    """Positioning must match the offer AND the prospect type. A service/studio/
    photographer must not be pitched a 'product film'; a single Product Film pitch
    should not advertise 'launch systems' in the positioning sentence (signature is
    exempt — it is checked separately)."""
    fails = []
    pos = d.motionx_positioning_sentence.lower()
    if d.prospect_kind in NON_PRODUCT_PROSPECT_KINDS and "product film" in pos:
        fails.append(("OFFER_MISMATCH",
                      f"'product film' positioning for prospect_kind={d.prospect_kind!r} (use brand/capability film)"))
    if d.selected_offer == "Product Film" and re.search(r"launch system", pos):
        fails.append(("OFFER_MISMATCH",
                      "single Product Film pitch advertises 'launch systems' in the positioning sentence"))
    return fails


# ── v2.5 human-voice helpers + validators ───────────────────────────────────────
def _split_sentences(text: str) -> list[str]:
    """Paragraph-aware sentence split: paragraph breaks also end a unit, so the comma
    after a greeting ('Hi Brand team,') never merges into the next sentence."""
    out: list[str] = []
    for para in re.split(r"\n\s*\n", text.strip()):
        para = para.strip()
        if para:
            out.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip())
    return out


def _paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]


_LIST_RE = re.compile(r"(?:[\w'’&-]+(?:\s+[\w'’&-]+){0,3},\s+){2,}")


def _list_groups(text: str) -> int:
    """Count sentences with a decorative list = >=2 consecutive comma-separated SHORT
    items (each <=4 words), e.g. 'the pour, the melt, the candles' or 'Volcano, Tan
    Lines, Mango Milk'. Multi-clause sentences ('intro, and I noticed X, though Y') are
    NOT lists — their comma fragments are long clauses, so they don't match. One list
    per email is fine; several read as AI cadence / a mini-proposal."""
    return sum(1 for s in _split_sentences(text) if _LIST_RE.search(s))


def count_modals(text: str) -> int:
    return len(MODAL_PATTERN.findall(text))


def count_abstract(text: str) -> int:
    low = text.lower()
    return sum(1 for t in ABSTRACT_TERMS if t.lower() in low)


def check_abstract_language(d: DraftModel) -> list[tuple[str, str]]:
    body = personalized_body(d)
    hits = [t for t in ABSTRACT_TERMS if t.lower() in body.lower()]
    if len(hits) >= 2:
        return [("ABSTRACT_LANGUAGE_OVERUSE", f"{len(hits)} abstract/agency terms: {hits}")]
    return []


def check_ai_phrase_patterns(d: DraftModel) -> list[tuple[str, str]]:
    body = personalized_body(d)
    fails = []
    for pat in AI_VOICE_PATTERNS:
        if re.search(pat, body, re.I):
            fails.append(("AI_PHRASE_PATTERN", f"AI/agency phrase: /{pat}/"))
    return fails


def check_modal_overuse(d: DraftModel) -> list[tuple[str, str]]:
    n = count_modals(personalized_body(d))
    if n > MODAL_MAX:
        return [("MODAL_VERB_OVERUSE", f"{n} modal hedges (could/would/might/can/'d) > {MODAL_MAX}")]
    return []


def check_personalization_depth(d: DraftModel) -> list[tuple[str, str]]:
    """A product/collection name proves research happened; it is not yet meaningful
    personalization. Require at least one recorded thought: reaction, why-this-idea,
    or a specific connection."""
    if not any(getattr(d, f, "").strip() for f in HUMAN_VOICE_FIELDS):
        return [("PERSONALIZATION_FACT_ONLY",
                 "no human_reaction / why_this_idea / prospect_specific_connection recorded")]
    return []


def check_brand_noun_removal(d: DraftModel) -> list[tuple[str, str]]:
    """Phase 7: if the body, with the prospect's nouns removed, could be sent to an
    unrelated business in the same category, it fails. Recorded by the editorial pass."""
    if d.brand_noun_removal_result.strip().upper() == "GENERIC":
        return [("GENERIC_WITH_SPECIFIC_NOUNS",
                 "brand-noun-removal: body reusable for another business (add reasoning, not nouns)")]
    return []


def check_mini_proposal(d: DraftModel) -> list[tuple[str, str]]:
    body = personalized_body(d)
    low = body.lower()
    fails = []
    for pat in MINI_PROPOSAL_TERMS:
        if re.search(pat, low):
            fails.append(("MINI_PROPOSAL_OVERBUILT", f"production-scoping language: /{pat}/"))
            break
    if _list_groups(body) >= 3:
        fails.append(("MINI_PROPOSAL_OVERBUILT", f"{_list_groups(body)} decorative lists (over-scoped)"))
    return fails


def check_excessive_listing(d: DraftModel) -> list[tuple[str, str]]:
    g = _list_groups(personalized_body(d))
    if g >= 2:
        return [("EXCESSIVE_LISTING", f"{g} three-item lists in one email (AI cadence)")]
    return []


def check_read_aloud(d: DraftModel) -> list[tuple[str, str]]:
    """Read-aloud test: too many em dashes or an over-long, multi-clause sentence is
    hard to say naturally."""
    body = personalized_body(d)
    fails = []
    if body.count(EM_DASH) > MAX_EM_DASHES:
        fails.append(("SENTENCE_RHYTHM_ARTIFICIAL",
                      f"{body.count(EM_DASH)} em dashes (max {MAX_EM_DASHES}) — hard to read aloud"))
    long_s = [s for s in _split_sentences(body) if count_words(s) > MAX_SENTENCE_WORDS]
    if long_s:
        fails.append(("SENTENCE_RHYTHM_ARTIFICIAL",
                      f"sentence of {max(count_words(s) for s in long_s)} words (> {MAX_SENTENCE_WORDS})"))
    return fails


def check_credibility_boilerplate(d: DraftModel) -> list[tuple[str, str]]:
    """The signature already names the company. The inline credibility line should not
    be the repeated agency boilerplate."""
    pos = d.motionx_positioning_sentence.lower()
    if re.search(r"founder-led studio (building|making|creating)", pos):
        return [("CREDIBILITY_BOILERPLATE",
                 "generic 'founder-led studio building/making…' credibility line")]
    return []


def check_cta_generic(d: DraftModel) -> list[tuple[str, str]]:
    if d.cta.strip().lower() in GENERIC_CTAS:
        return [("CTA_GENERIC", f"overused generic CTA: {d.cta!r}")]
    return []


def check_human_voice(d: DraftModel) -> list[tuple[str, str]]:
    """Composite editorial gate. Fails when the read-aloud pass failed or voice risk is
    high — the human signal the deterministic checks can't fully capture."""
    fails = []
    if d.conversational_read_result.strip().upper() == "FAIL":
        fails.append(("HUMAN_VOICE_LOW", "conversational_read_result=FAIL (editorial)"))
    if d.voice_risk.strip().upper() == "HIGH":
        fails.append(("HUMAN_VOICE_LOW", "voice_risk=HIGH (editorial)"))
    return fails


# ── Centralized preflight ──────────────────────────────────────────────────────
def preflight(d: DraftModel, context: Optional[dict] = None) -> dict:
    """Run every gate. Returns a machine-readable result. A draft must not reach
    Gmail unless status == 'PASS'."""
    context = context or {}
    failures: list[tuple[str, str]] = []

    # context gates
    if context.get("suppressed"):
        failures.append(("PREVIOUSLY_CONTACTED", "recipient/domain on suppression list"))
    if context.get("same_domain_within_cooldown"):
        failures.append(("PREVIOUSLY_CONTACTED", "same-domain contact within cooldown window"))
    if context.get("duplicate_draft"):
        failures.append(("DUPLICATE_DRAFT", "an existing Gmail draft targets this recipient"))
    if context.get("found_in_sent"):
        failures.append(("DUPLICATE_DRAFT", "recipient already appears in Gmail Sent"))
    if context.get("commercial_path_unavailable"):
        failures.append(("COMMERCIAL_PATH_UNAVAILABLE", "purchase/booking/inquiry path not currently available"))
    if context.get("source_contradiction"):
        failures.append(("SOURCE_CONTRADICTION", "site-wide contradiction unresolved"))
    if context.get("policy_version") and context["policy_version"] != POLICY_VERSION:
        failures.append(("POLICY_STALE", f"policy {context['policy_version']} != {POLICY_VERSION}"))

    # content gates
    failures += check_greeting(d)
    failures += check_free_work_cta(d.cta)
    failures += check_medical(d)
    failures += check_offer_and_price(d)
    failures += check_diagnosis_ratio(d)
    failures += check_claim_scope(d)
    failures += check_negative_framing(d)      # v2.4
    failures += check_business_inference(d)     # v2.4
    failures += check_existing_asset(d)         # v2.4
    failures += check_currentness(d)            # v2.4
    failures += check_offer_fit(d)              # v2.4
    failures += check_geography(d, context)     # v2.6
    failures += check_abstract_language(d)      # v2.5
    failures += check_ai_phrase_patterns(d)     # v2.5
    failures += check_modal_overuse(d)          # v2.5
    failures += check_personalization_depth(d)  # v2.5
    failures += check_brand_noun_removal(d)     # v2.5
    failures += check_mini_proposal(d)          # v2.5
    failures += check_excessive_listing(d)      # v2.5
    failures += check_read_aloud(d)             # v2.5
    failures += check_credibility_boilerplate(d) # v2.5
    failures += check_cta_generic(d)            # v2.5
    failures += check_human_voice(d)            # v2.5
    failures += check_subject(d.subject, context.get("recent_subjects"))
    failures += check_signature(d.signature)
    body_for_lang = personalized_body(d)
    failures += check_ai_language(body_for_lang)
    failures += check_links(body_for_lang + " " + d.signature)
    wc, wc_fail = check_word_count(d)
    failures += wc_fail

    status = "PASS" if not failures else "FAIL"
    return {
        "status": status,
        "policy_version": POLICY_VERSION,
        "final_body_word_count": wc,
        "recipient_confidence": d.recipient_confidence,
        "selected_offer": d.selected_offer,
        "selected_price": d.optional_price,
        "observation_scope": d.observation_scope,
        "absence_evidence_level": d.absence_evidence_level,
        "prospect_kind": d.prospect_kind,
        "currentness_status": d.currentness_status,
        "modal_count": count_modals(personalized_body(d)),
        "abstract_count": count_abstract(personalized_body(d)),
        "em_dashes": personalized_body(d).count(EM_DASH),
        "list_groups": _list_groups(personalized_body(d)),
        "failure_codes": sorted({c for c, _ in failures}),
        "failures": [{"code": c, "reason": r} for c, r in failures],
    }


# ── Batch-level preflight (v2.4 "Batch Diversity") ──────────────────────────────
# An email can pass individually while the BATCH reads automated: same subject shapes,
# same CTA, same positioning sentence, the same filler phrases, near-duplicate bodies.
# batch_preflight() runs over the whole authorized batch AFTER each draft passes
# preflight(). A draft is only cleared for Gmail if it passes BOTH stages.

# Default thresholds for an ~20-draft batch (fractions so they scale to any size).
BATCH_DEFAULTS = {
    "surface_pattern_max_frac": 0.25,   # >25% sharing "on film"/"in motion"/"page" → FAIL
    "subject_shape_max_count": 4,       # a single subject SHAPE shared by >4 (>=5) → FAIL
    "exact_cta_max": 4,                 # exact CTA repeated >4 → FAIL
    "exact_positioning_max": 4,         # exact positioning sentence repeated >4 → FAIL
    "tracked_phrase_max_frac": 0.25,    # a tracked filler phrase in >25% of drafts → FAIL
    "shingle_overuse_frac": 0.25,       # any identical 5-word shingle in >25% of drafts → FAIL
    "near_dup_jaccard": 0.5,            # body-pair 4-word-shingle Jaccard >= 0.5 → FAIL
}

_SUBJECT_CENTRAL_NOUNS = {"page", "pages"}


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", text.lower())).strip()


# Price quotes are standardized commercial boilerplate (like the signature/footer):
# the same "$399"/"$699" recurs by design. Strip the dollar amount before generic
# near-duplicate / shingle analysis so the price line doesn't drive false similarity.
# Positioning diversity is still enforced (exact-positioning + tracked-phrase checks).
_PRICE_AMT_RE = re.compile(r"\$\s?\d[\d,]*")


def _strip_price(text: str) -> str:
    return _PRICE_AMT_RE.sub(" ", text)


def _word_shingles(text: str, n: int) -> set:
    toks = _norm(text).split()
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)} if len(toks) >= n else set()


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _surface_pattern(subject: str) -> set:
    low = " " + _norm(subject) + " "
    tags = set()
    if low.rstrip().endswith(" on film") or " on film " in low:
        tags.add("on film")
    if low.rstrip().endswith(" in motion") or " in motion " in low:
        tags.add("in motion")
    toks = _norm(subject).split()
    if any(t in _SUBJECT_CENTRAL_NOUNS for t in toks):
        tags.add("page")
    return tags


def batch_preflight(drafts: list, config: Optional[dict] = None) -> dict:
    """Validate the whole authorized batch for diversity/humanization. Returns a
    machine-readable result; status FAIL blocks the batch (fix the flagged drafts)."""
    cfg = {**BATCH_DEFAULTS, **(config or {})}
    n = len(drafts)
    failures: list[tuple[str, str]] = []
    flags: list[str] = []
    checks: dict = {}
    if n == 0:
        return {"status": "PASS", "n": 0, "checks": {}, "failure_codes": [], "flags": [],
                "failures": []}

    subjects = [d.subject for d in drafts]
    ctas = [d.cta.strip() for d in drafts]
    positionings = [d.motionx_positioning_sentence.strip() for d in drafts]
    bodies = [personalized_body(d) for d in drafts]

    # 1. exact duplicate subjects
    dupe_subj = sorted({s for s in subjects if subjects.count(s) > 1})
    checks["subject_duplicates"] = dupe_subj
    if dupe_subj:
        failures.append(("BATCH_SUBJECT_DUPLICATE", f"exact duplicate subject(s): {dupe_subj}"))

    # 2. surface-pattern over-concentration (on film / in motion / page)
    surf_counts = {"on film": 0, "in motion": 0, "page": 0}
    for s in subjects:
        for tag in _surface_pattern(s):
            surf_counts[tag] += 1
    checks["subject_surface_counts"] = surf_counts
    for tag, c in surf_counts.items():
        # n>1 guard: a fraction-concentration check is degenerate for a single-draft
        # batch (any present tag is "100% of the batch"); per SKILL a 1-draft batch is a
        # trivial PASS. Multi-draft behaviour is unchanged.
        if n > 1 and c / n > cfg["surface_pattern_max_frac"]:
            failures.append(("BATCH_SUBJECT_PATTERN",
                             f"{c}/{n} subjects share surface pattern {tag!r} (> {int(cfg['surface_pattern_max_frac']*100)}%)"))

    # 3. subject SHAPE over-concentration. Only TEMPLATED skeletons count — a shape
    #    containing at least one function word (e.g. "X on X", "X X for X"). A bare
    #    all-content shape ("X X X" = just three nouns) is not a template, so it is
    #    ignored (otherwise every batch of plain noun-phrase subjects false-fails).
    shapes: dict = {}
    for s in subjects:
        sh = _subject_shape(s)
        if any(tok in _SUBJECT_FUNCWORDS for tok in sh.split()):
            shapes.setdefault(sh, []).append(s)
    if shapes:
        worst = max(shapes.items(), key=lambda kv: len(kv[1]))
        checks["subject_shape_max"] = {"shape": worst[0], "count": len(worst[1]), "examples": worst[1][:3]}
        if len(worst[1]) > cfg["subject_shape_max_count"]:
            failures.append(("BATCH_SUBJECT_SHAPE",
                             f"{len(worst[1])} subjects share templated shape {worst[0]!r} (max {cfg['subject_shape_max_count']})"))

    # 3b. punctuation gimmick flag (e.g. "X, in motion")
    gimmicks = [s for s in subjects if re.search(r",\s+(in motion|on film)\b", s.lower())]
    if gimmicks:
        flags.append(f"BATCH_SUBJECT_PUNCT: comma gimmick in {gimmicks}")
        checks["subject_punct_gimmicks"] = gimmicks

    # 4. exact CTA repetition
    cta_counts = {c: ctas.count(c) for c in set(ctas)}
    over_cta = {c: k for c, k in cta_counts.items() if k > cfg["exact_cta_max"]}
    checks["cta_counts"] = cta_counts
    if over_cta:
        failures.append(("BATCH_CTA_REPEAT", f"exact CTA over {cfg['exact_cta_max']}x: {over_cta}"))

    # 5. exact positioning repetition
    pos_counts = {p: positionings.count(p) for p in set(positionings)}
    over_pos = {p: k for p, k in pos_counts.items() if k > cfg["exact_positioning_max"]}
    checks["positioning_counts"] = pos_counts
    if over_pos:
        failures.append(("BATCH_POSITIONING_REPEAT",
                         f"exact positioning over {cfg['exact_positioning_max']}x: {list(over_pos.values())}"))

    # 6. tracked filler-phrase frequency (signature/footer excluded — bodies are
    #    personalized_body only, which never contains them)
    low_bodies = [_norm(b) for b in bodies]
    phrase_hits = {}
    for ph in TRACKED_BATCH_PHRASES:
        c = sum(1 for b in low_bodies if ph in b)
        if c:
            phrase_hits[ph] = c
    over_phrase = {ph: c for ph, c in phrase_hits.items() if n > 1 and c / n > cfg["tracked_phrase_max_frac"]}
    checks["tracked_phrase_hits"] = phrase_hits
    if over_phrase:
        failures.append(("BATCH_PHRASE_OVERUSE",
                         f"filler phrase(s) in > {int(cfg['tracked_phrase_max_frac']*100)}% of batch: {over_phrase}"))

    # 6b. generic identical 5-word shingle in >25% of drafts (price amount stripped —
    #     it is standardized commercial boilerplate, exempt like the signature/footer)
    shingle_doc_freq: dict = {}
    for b in bodies:
        for sh in _word_shingles(_strip_price(b), 5):
            shingle_doc_freq[sh] = shingle_doc_freq.get(sh, 0) + 1
    over_shingle = {sh: c for sh, c in shingle_doc_freq.items() if n > 1 and c / n > cfg["shingle_overuse_frac"]}
    if over_shingle:
        top = dict(sorted(over_shingle.items(), key=lambda kv: -kv[1])[:5])
        failures.append(("BATCH_PHRASE_OVERUSE",
                         f"identical 5-word phrase(s) in > {int(cfg['shingle_overuse_frac']*100)}% of batch: {top}"))
        checks["shingle_overuse"] = top

    # 7. near-duplicate bodies (4-word-shingle Jaccard; price amount stripped)
    sh_sets = [_word_shingles(_strip_price(b), 4) for b in bodies]
    near = []
    for i in range(n):
        for j in range(i + 1, n):
            jac = _jaccard(sh_sets[i], sh_sets[j])
            if jac >= cfg["near_dup_jaccard"]:
                near.append((drafts[i].prospect_name, drafts[j].prospect_name, round(jac, 2)))
    checks["near_duplicate_pairs"] = near
    if near:
        failures.append(("BATCH_NEAR_DUPLICATE", f"near-duplicate body pairs (Jaccard>={cfg['near_dup_jaccard']}): {near}"))

    status = "PASS" if not failures else "FAIL"
    return {
        "status": status,
        "n": n,
        "checks": checks,
        "flags": flags,
        "failure_codes": sorted({c for c, _ in failures}),
        "failures": [{"code": c, "reason": r} for c, r in failures],
    }


# ── Batch-level VOICE preflight (v2.5) ──────────────────────────────────────────
# Separate from batch_preflight() (diversity) so v2.4 behaviour is untouched. Catches a
# batch that is lexically varied yet shares one AI cadence: same paragraph shape, same
# credibility opener, same modal density, shallow personalization across the set.
BATCH_VOICE_DEFAULTS = {
    "paragraph_pattern_max_frac": 0.6,    # >60% sharing the exact paragraph count → FAIL
    "credibility_opener_max_frac": 0.5,   # >50% sharing the same 3-word credibility opener → FAIL
    "structure_opener_max_frac": 0.4,     # >40% of idea sentences starting "A short/focused X could" → FAIL
    "mean_modal_max": 3.0,                # batch mean modal count per body → FAIL above
    "shallow_personalization_max_frac": 0.25,  # >25% missing all human-voice fields → FAIL
    "punctuation_pattern_max_frac": 0.6,  # >60% sharing identical em-dash count → FAIL (when >1 dash)
}

_STRUCT_OPENER = re.compile(r"^\s*a (short|focused|single|motion-?led|calm)\b.*\bcould\b", re.I)


def batch_voice_preflight(drafts: list, config: Optional[dict] = None) -> dict:
    cfg = {**BATCH_VOICE_DEFAULTS, **(config or {})}
    n = len(drafts)
    if n == 0:
        return {"status": "PASS", "n": 0, "checks": {}, "failure_codes": [], "failures": []}
    failures: list[tuple[str, str]] = []
    checks: dict = {}

    bodies = [personalized_body(d) for d in drafts]

    # 1. paragraph-count concentration
    para_counts = [len(_paragraphs(b)) for b in bodies]
    if para_counts:
        from collections import Counter
        pc = Counter(para_counts)
        top_para, top_n = pc.most_common(1)[0]
        checks["paragraph_counts"] = dict(pc)
        if top_n / n > cfg["paragraph_pattern_max_frac"] and n >= 4:
            failures.append(("BATCH_PARAGRAPH_PATTERN",
                             f"{top_n}/{n} drafts have {top_para} paragraphs (> {int(cfg['paragraph_pattern_max_frac']*100)}%)"))

    # 2. credibility opener concentration (first 3 words of the positioning line)
    openers = [" ".join(_norm(d.motionx_positioning_sentence).split()[:3]) for d in drafts]
    from collections import Counter as _C
    oc = _C(o for o in openers if o)
    checks["credibility_openers"] = dict(oc)
    if oc:
        top_o, top_on = oc.most_common(1)[0]
        if top_on / n > cfg["credibility_opener_max_frac"] and n >= 4:
            failures.append(("BATCH_CREDIBILITY_PATTERN",
                             f"{top_on}/{n} share credibility opener {top_o!r} (> {int(cfg['credibility_opener_max_frac']*100)}%)"))

    # 3. structural idea-opener concentration ("A short film could…", "A focused page could…")
    struct = sum(1 for d in drafts if _STRUCT_OPENER.search(d.central_idea.strip()))
    checks["structure_opener_hits"] = struct
    if struct / n > cfg["structure_opener_max_frac"] and n >= 4:
        failures.append(("BATCH_STRUCTURE_CONCENTRATION",
                         f"{struct}/{n} ideas open with 'A short/focused … could …' (> {int(cfg['structure_opener_max_frac']*100)}%)"))

    # 4. modal density across the batch
    modals = [count_modals(b) for b in bodies]
    mean_modal = sum(modals) / n
    checks["mean_modal"] = round(mean_modal, 2)
    if mean_modal > cfg["mean_modal_max"]:
        failures.append(("BATCH_MODAL_PATTERN",
                         f"batch mean modal count {mean_modal:.1f} > {cfg['mean_modal_max']}"))

    # 5. shallow personalization across the batch
    shallow = sum(1 for d in drafts
                  if not any(getattr(d, f, "").strip() for f in HUMAN_VOICE_FIELDS))
    checks["shallow_personalization"] = shallow
    if shallow / n > cfg["shallow_personalization_max_frac"]:
        failures.append(("BATCH_PERSONALIZATION_SHALLOW",
                         f"{shallow}/{n} drafts have no recorded human-voice thought"))

    # 6. punctuation pattern (identical em-dash count when dashes are used)
    dash_counts = [b.count(EM_DASH) for b in bodies]
    dc = _C(dash_counts)
    top_d, top_dn = dc.most_common(1)[0]
    checks["em_dash_counts"] = dict(dc)
    if top_d > 1 and top_dn / n > cfg["punctuation_pattern_max_frac"] and n >= 4:
        failures.append(("BATCH_PUNCTUATION_PATTERN",
                         f"{top_dn}/{n} drafts share {top_d} em dashes (repeated punctuation rhythm)"))

    # 7. composite AI-voice concentration: two or more of the above firing
    distinct_codes = {c for c, _ in failures}
    if len(distinct_codes) >= 2:
        failures.append(("BATCH_AI_VOICE_CONCENTRATION",
                         f"multiple batch-voice signals fired: {sorted(distinct_codes)}"))

    status = "PASS" if not failures else "FAIL"
    return {
        "status": status, "n": n, "checks": checks,
        "failure_codes": sorted({c for c, _ in failures}),
        "failures": [{"code": c, "reason": r} for c, r in failures],
    }


if __name__ == "__main__":
    print(f"MOTIONX outreach preflight — policy v{POLICY_VERSION}")
    print("Canonical signature:\n" + CANONICAL_SIGNATURE)
