# MOTIONX outreach — policy changelog

No private lead data in this file. CRM data and the postal address live only in
`~/.motionx-outreach/` (outside Git).

> **Current:** operating policy **v2.9** / validator engine (`preflight.py` POLICY_VERSION)
> **v2.7** — **170 regression tests green**. NOTE: entries below are NOT strictly
> reverse-chronological — the newest work (engine 2.5→2.6 Geography + v2.6.1 signature,
> then v2.9 operating / engine 2.7 Artifact Readback Integrity) is appended at the
> **bottom** of this file. The top entry (v2.7 Continuous Improvement Loop) is a
> point-in-time record from when the engine was still 2.5.

## v2.7 — 2026-06-22 — Continuous Improvement Loop (operating-mode addendum)
**What changed:** the system now improves itself a little on every run. Added
`outreach/self-improvement.md` (the loop + a living "Accumulated authoring heuristics"
list distilled from real gate failures) and `outreach/authoring_lint.py` (a fast,
advisory pre-validator that catches the historically most-iterated defects —
comma-triplet lists, repeated positioning shingles, paragraph-count concentration,
mini-proposal phrasing — *before* the formal gates). `config.json` gains a
`continuous_improvement` block; `SKILL.md` gains a "v2.7" section so the loop loads every
run. A per-run journal lives at `~/.motionx-outreach/improvement-log.md` (outside Git).
**What did NOT change:** no content gate; the validator engine stays **2.5** (runs still
pass `policy_version="2.5"`); all 147 regression tests untouched. **Hard rule:** never
weaken a gate or lower a threshold to make a run look better — improvement = higher
quality and/or fewer wasted iterations, never a lower bar. Every heuristic/tooling change
must trace to a real observed failure or near-miss; additive and reversible by default.
Traces to the 2026-06-22 45-draft session retro (EXCESSIVE_LISTING, BATCH_PHRASE_OVERUSE,
BATCH_PARAGRAPH_PATTERN, MINI_PROPOSAL_OVERBUILT were the recurring authoring failures;
snippet-sourced scout emails and a bare-domain link downgrade were the integrity/deliver
near-misses).

## v2.6 — 2026-06-21 — Manual On-Demand Drafting Mode (operating-mode addendum)
**What changed:** formalized a first-class **`run_mode = MANUAL`** for Charles-initiated,
in-session draft batches (e.g. "draft N emails"), distinct from the autonomous
`run_mode = SCHEDULED` routine. Previously this was handled ad hoc as "override" batches
(the 2026-06-21 L0027–L0031 run); v2.6 makes it explicit in `SKILL.md` (new "v2.6 —
Manual On-Demand Drafting Mode" section + Step 0 `run_mode` selection + a note on the
Ramp & volume caps section) and in `config.json` (`manual_on_demand_mode` block).

**Operating-mode only — NO content gate changed.** The deterministic validator
`preflight.py` stays at engine version **2.5**; runs pass `policy_version="2.5"` so
`POLICY_STALE` never trips. All 147 regression tests are unchanged and still green.
`config.json` now carries `outreach_policy_version: "2.6"` (operating/governance) and
`validator_engine_version: "2.5"` (gate engine).

**MANUAL relaxes run-size/scheduling only:** the ramp/slot/weekend/daily/weekly volume
caps. **MANUAL never relaxes any quality/integrity gate:** TEST + DRAFT_ONLY,
reconcile-first, suppression + 90-day same-domain, no fabrication / no guessed emails,
Tier-1 + full account thesis, lead ≥80 / personalization ≥9 / draft-quality ≥9,
`preflight()` + `batch_preflight()` + `batch_voice_preflight()`, recipient-certainty,
commercial-readiness, signature/footer/link hygiene, postal-resolved-or-block, one
packet per draft, CRM/log writes, notify. **The requested N is a ceiling, not a quota** —
"never lower a threshold to fill a quota" stands; a manual run that yields fewer than N
(or zero) because nothing else clears the bar is a successful, compliant run. Manual
drafts are accounted as `manual_override` and do not alter SCHEDULED entitlement,
`program_start_date`, or the business-day index.

## v2.5 — 2026-06-21 — Human Voice & Conversational Credibility
**Defect observed (across the v2.4 drafts, even after Charles expanded some to 85–110
words):** the emails still had a recognizable AI voice — symmetrical 3–4 paragraph
structure, every paragraph doing one predictable job, agency abstractions ("its own
visual identity", "recognizably AKILA", "carry that recognition"), a repeated "I run
MOTIONX, a founder-led studio…" credibility line, "A short/focused page could…"
openers, modal stacking (could/would/might), em-dash + three-item-list cadence, and
mini-proposal scoping. The personalization was by *fact* (a product name proves
research happened) rather than by *thought* (a genuine reaction). A longer AI email is
still an AI email.

**Principle:** distinguish personalized information from personalized writing from
personalized intent. The recipient should feel "Charles actually looked and had one
genuine thought," not "an AI inspected our homepage and generated a polished proposal."

**Length standard changed:** prefer 90–125 words, hard 75–140 (was 55–125). A short
email fails when it omits the reasoning that makes the idea credible — not merely for
being short. Never pad to hit a number.

**New per-draft gates (`outreach/preflight.py`):**
- `check_abstract_language` → ABSTRACT_LANGUAGE_OVERUSE (≥2 agency abstractions).
- `check_ai_phrase_patterns` → AI_PHRASE_PATTERN ("cohesive visual identity", "cinematic
  destination", "carry the story across", "recognizably [Brand]", …).
- `check_modal_overuse` → MODAL_VERB_OVERUSE (>4 could/would/might/can/'d).
- `check_personalization_depth` → PERSONALIZATION_FACT_ONLY (requires a recorded
  human_reaction / why_this_idea / prospect_specific_connection).
- `check_brand_noun_removal` → GENERIC_WITH_SPECIFIC_NOUNS (Phase-7 test: if the body
  with the brand nouns removed could be reused for another business in the category).
- `check_mini_proposal` → MINI_PROPOSAL_OVERBUILT (shot lists, channel rollouts, ≥3
  decorative lists).
- `check_excessive_listing` → EXCESSIVE_LISTING (≥2 three-item lists in one email).
- `check_read_aloud` → SENTENCE_RHYTHM_ARTIFICIAL (>1 em dash, or a sentence >34 words).
- `check_credibility_boilerplate` → CREDIBILITY_BOILERPLATE ("founder-led studio
  building/making…"); the signature already names the company.
- `check_cta_generic` → CTA_GENERIC (the recycled "Would a short written concept…").
- `check_human_voice` → HUMAN_VOICE_LOW (editorial: conversational_read_result=FAIL /
  voice_risk=HIGH).

**New batch gate `batch_voice_preflight()`** (separate from v2.4 `batch_preflight`, so
diversity behaviour is untouched): BATCH_PARAGRAPH_PATTERN (>60% same paragraph count),
BATCH_CREDIBILITY_PATTERN (>50% same credibility opener), BATCH_STRUCTURE_CONCENTRATION
(>40% "A short/focused … could …" openers), BATCH_MODAL_PATTERN (batch mean modal >3),
BATCH_PERSONALIZATION_SHALLOW (>25% with no recorded thought), BATCH_PUNCTUATION_PATTERN
(shared em-dash rhythm), BATCH_AI_VOICE_CONCENTRATION (≥2 of the above). A draft must
pass `preflight()` AND `batch_preflight()` AND `batch_voice_preflight()`.

**New DraftModel fields:** `human_reaction`, `why_this_idea`,
`prospect_specific_connection`, `voice_risk`, `brand_noun_removal_result`,
`conversational_read_result`, `price_rationale`, `credibility_style`.

**Tests:** `outreach/tests/test_preflight.py` — 112 → 147 (added length/completeness,
abstract/AI-phrase, personalization depth + brand-noun removal, modal overuse,
mini-proposal, excessive listing, credibility boilerplate, generic CTA, read-aloud,
human-voice composite, and the batch-voice suite incl. a human PASS fixture and an
AI-cadence FAIL fixture). All 147 pass. No Gmail access in tests; real postal address
never used. `base()` upgraded to a v2.5-compliant human draft.

**Known limitations:** voice heuristics are deterministic proxies for a human read, not
a substitute — they catch clear AI cadence, not every flat sentence. `why_this_idea` /
`brand_noun_removal_result` are editor-asserted (recorded, then validated), like the
v2.3.1 evidence levels. The decorative-list detector keys on short consecutive
comma-items, so an unusual list shape could slip through. v2.5 did not weaken any
factual, compliance, state, claim-scope, currentness, offer-fit, or batch-diversity
gate. The Gmail connector still cannot edit a draft in place — scheduled drafts cannot
be revised by the routine and are reported for manual in-place editing instead.

## v2.4 — 2026-06-21 — Humanization, Batch Diversity & Offer Fit
**Defects observed (in the 2026-06-20 20-draft batch — each draft passed v2.3.1
individually, yet the BATCH read automated):**
- Subject lines reused a few shapes ("X on film", "X in motion", "X launch page",
  "One page for X").
- CTAs repeated almost verbatim ("Would a short written concept/outline be useful?"
  in nearly every draft).
- The MOTIONX positioning sentence repeated almost verbatim across most drafts.
- Filler phrases recurred across unrelated businesses ("a natural fit", "a good
  moment", "a natural moment", "could carry", "give it a home").
- Speculation about business performance/maturity ("reads like a newer studio still
  filling its first members" — Rise Pilates).
- Direct criticism of an existing site/template ("clean, standard template" — Flirt;
  "runs on a booking template / reads stronger than…" — Enchanted Glow).
- An offer that contradicted what the business already had ("give the membership
  program a home of its own" when a memberships page already existed — My Skin).
- Stale seasonal premise still merchandised online (PARU's Lunar-New-Year blend in
  late June); Earthen's unverifiable "July 2026" date.
- A first name on a generic inbox (greeting certainty).
- Product-film positioning applied to non-product prospects (Oculus = architectural
  lighting studio; Erin = wedding photographer).
- One prospect too large/corporate for a $399 pilot (Sugar Paper).

**Architecture added:** a SECOND validation stage. `preflight()` stays per-draft;
new `batch_preflight(drafts)` runs over the whole authorized batch. A draft is only
cleared for Gmail when it passes BOTH.

**Per-draft gates added (`outreach/preflight.py`):**
- `check_negative_framing` → NEGATIVE_FRAMING (prospect-defensive language).
- `check_business_inference` → UNSUPPORTED_INFERENCE (maturity/occupancy/demand/health).
- `check_existing_asset` → PROPOSED_ASSET_ALREADY_EXISTS (proposing what they have).
- `check_currentness` → STALE_OPPORTUNITY / PRODUCT_UNAVAILABLE / PROMOTION_ENDED /
  CURRENTNESS_UNVERIFIED (stale seasonal/promo/product premises).
- `check_offer_fit` → OFFER_MISMATCH (positioning must match offer + prospect type).
New DraftModel fields: `prospect_kind`, `existing_assets`, `proposed_asset`,
`currentness_status`, `reframed_as_evergreen`, `product_availability`,
`promotion_status`, `seasonal_relevance`, `verified_current_date`.

**Batch gates (`batch_preflight`):** BATCH_SUBJECT_DUPLICATE, BATCH_SUBJECT_PATTERN
(>25% sharing "on film"/"in motion"/"page"), BATCH_SUBJECT_SHAPE (a templated subject
skeleton shared by >4), BATCH_CTA_REPEAT (exact CTA >4×), BATCH_POSITIONING_REPEAT
(exact positioning sentence >4×), BATCH_PHRASE_OVERUSE (a tracked filler phrase OR any
identical 5-word shingle in >25% of bodies), BATCH_NEAR_DUPLICATE (body-pair 4-word
Jaccard ≥ 0.5). A "X, in motion" comma gimmick is FLAGGED. The canonical signature,
the compliance footer, and the standardized price quote are EXEMPT from repetition
analysis (commercial boilerplate). Only TEMPLATED subject shapes (containing a
function word, e.g. "X on X", "X X for X") count — a bare all-content "X X X" is not a
template, so plain noun-phrase subjects don't false-fail.

**Config:** `batch_preflight_required_before_draft`, `batch_diversity_thresholds`,
`batch_quality_score_categories`, `cta_categories`, `prospect_kinds`,
`currentness_statuses`, plus the new failure codes.

**Tests:** `outreach/tests/test_preflight.py` — 71 → 112 cases (added negative-framing,
business-inference, existing-asset, currentness, offer-fit, and the full batch suite:
subject/CTA/positioning/phrase diversity, near-duplicate, a genuinely varied 20-draft
PASS fixture). All 112 pass. No Gmail access in tests; real postal address never used.

**Reconciled against earlier spec language:** the "no more than 2 of the same surface
pattern" line is operationalized as the testable 25% caps; "more than 5 sharing the
same shape" is enforced at >4 (≥5 fails), matching the "5 near-identical 'One page
for…'" acceptance case.

**Known limitations:** validators are conservative phrase/shingle/evidence heuristics,
not full NLP — they catch clear cases, not every subtle over-claim or paraphrase.
`existing_assets` must list the *conflicting* asset specifically (listing every page a
site has would over-trigger the asset guard). Gmail connector still has no
update/delete-draft (corrections create a new draft + manual deletion of the old).
v2.4 did not weaken any v2.3/v2.3.1 gate; prior records keep their original
policy_version.

## v2.3.1 — 2026-06-20 — Claim Scope & Evidence Precision (patch)
**Defect observed:** v2.3 drafts (Drenched, Facial Lounge) converted a limited,
page-level observation into an unsupported absolute absence claim — "with no page of
its own", "with no film for the line yet", "carried entirely by still photography" —
when only the homepage / one product page had been checked.
**Why it mattered:** factual precision + credibility; an absolute that the research
didn't prove is exactly the kind of claim a skeptical founder catches.
**Patch added:** structured claim-scope fields on the draft model
(`observation_scope`, `pages_checked`, `channels_checked`, `absence_claim`,
`absence_evidence_level`, `approved_claim_wording`) + a scope-aware validator
(`check_claim_scope`/`scope_violations`) wired into `preflight()`. Absolute absence
claims require matching evidence (site-wide → `CHECKED_RELEVANT_SITE_ROUTES`+;
cross-channel/"only/entirely" → `VERIFIED_CROSS_CHANNEL`, 2+ channels). Default to
scoped wording. New codes: CLAIM_SCOPE_UNSUPPORTED, ABSENCE_EVIDENCE_INSUFFICIENT,
CHANNEL_SCOPE_OVERREACH, ABSOLUTE_LANGUAGE_UNSUPPORTED.
**Tests added:** 16 claim-scope cases (incl. the original Drenched/Facial sentences
as FAIL fixtures and the corrected sentences as PASS) — suite now 71 cases, all pass.
**Known limits:** the validator is conservative phrase+evidence matching, not full
NLP; it flags clear absolutes, not every subtle over-claim. Did NOT weaken any v2.3
gate. Existing v2.3 records keep their original policy_version (not relabeled 2.3.1).

## v2.3 — 2026-06-20 — Draft Reliability & Deliverability Upgrade
**Defects observed (across real samples: Beauty Boost XERF, Santa Barbara candle):**
- Google redirect link with `http://` downgrade in the rendered/stored draft.
- Signature drift: extra sender-email line, "Available Worldwide", expanded lines.
- Uncertain first-name greeting on a brand/general mailbox.
- Medical mechanism phrasing ("showing how the treatment tightens").
- Free-work CTA ("rough visual direction", "Want me to sketch…").
- Literary/AI phrasing ("feel of-a-piece", "could carry it", "real early-adopter offer").
- Connector has no update/delete-draft → repeated manual cleanup of duplicate drafts.

**Rules added (deterministic, in `outreach/preflight.py`):**
- Canonical signature renderer (one approved block; banned-token rejection).
- URL canonicalizer/validator (https only at render; `q=http`/shortener/redirect = fail;
  Gmail's `google.com/url?q=https` wrapper documented as an accepted transport artifact).
- Recipient-certainty engine (HIGH/MEDIUM/LOW → greeting rule).
- Medical/regulated-claim guard (official wording only; banned inferences).
- Free-work-CTA guard; AI/literary-language gate.
- Structured diagnosis-ratio rule; one-offer/one-price gate; word-count gate; subject gate.
- Centralized `preflight()` → PASS/FAIL + failure codes; max 3 revision attempts.
- State-transition guard (draft never writes sent/contacted/follow_up).
- Config: run-size + cap fields (`default_drafts_per_run` 1, `max_drafts_per_run` 2, etc.).

**Tests added:** `outreach/tests/test_preflight.py` — 55 cases (signature, link, recipient,
CTA, medical, language, offer/price, state, body-length, full preflight). All pass.

**Known limitations:**
- Gmail wraps all draft links in `google.com/url?q=…`; cannot be removed via the connector
  (best achievable: `q=https`).
- The Gmail connector cannot update or delete drafts; corrections create a new draft and
  the superseded one must be deleted manually.
- Preflight language/ratio checks are conservative heuristics, not full NLP.

## Defect taxonomy (record per outcome in `outcome-log.csv` Notes; do not over-rewrite policy)
`no_reply` · `positive_reply` · `wrong_recipient` · `not_relevant` · `too_expensive` ·
`already_has_provider` · `timing` · `bounced` · `opted_out` · `personalization_inaccurate` ·
`subject_weak` · `cta_unclear` · `offer_mismatch`

Propose a policy change only when (a) the same defect recurs across multiple real samples,
or (b) a serious compliance/state-integrity issue appears even once. Keep this changelog
current: version · date · defects · rules added · tests added · known limitations.

## v2.2 — 2026-06-20 — Quality patch (research ≠ communication)
Length/diagnosis/score discipline; site-wide contradiction check; recipient-certainty,
plain-language, commercial-readiness gates; compact footer; Draft Quality Score ≥9 via a
separate editorial pass. (Superseded length/score rules from v2.1; all other v2.1
reliability rules remain.)

## v2.6 — Geography & Scope Integrity (engine 2.5 → 2.6) + v2.6.1 signature standard (2026-06-24)
**Why:** the 2026-06-23 batch7 run created a Gmail draft for a Canadian brand (Victory
Barber, Victoria BC) before it was caught manually at the CRM stage — a real out-of-scope
escape. Geography was an authoring convention, not a gate.
**Engine v2.6 (deterministic):** new `check_geography(d, context)` →
`GEOGRAPHY_OUT_OF_SCOPE`, fail-closed. New `DraftModel` fields `prospect_country`
(default "US") + `geography_evidence`. A draft fails unless the country normalizes to the
US (`ALLOWED_COUNTRIES`) or `context["geography_authorized"]=True`. Currency / a /us
storefront do NOT prove US; a blank country fails closed. Runs now pass
`policy_version="2.6"`. Tests: 147 → **155 green** (8 geography tests added).
**v2.6.1 signature standard:** the canonical signature was updated to Charles's own
template (left as an edited draft 2026-06-24): a leading `--` delimiter and labelled
`Website:` / `Email Address:` lines (the v2.3 block had stripped these), founder name
"Founder, MotionX". The website keeps the full `https://` scheme so Gmail stores q=https.
`SIGNATURE_BANNED` no longer bans `website:` / `email address:` / the founder address;
still bans the public alias in the founder sig, "Available Worldwide", bare `http://`,
link-tracker wrappers, social handles, and "Based in". The postal address + opt-out remain
a separately-injected compliance footer (opt-out kept for CAN-SPAM; postal never in repo).
`signature.html` mirrors the new block. Operating policy bumped 2.7 → 2.8.

## v2.9 (operating) + engine v2.7 — Artifact Readback Integrity (2026-07-02)
**Why (all traced to live evidence found in the 2026-07-02 audit):**
1. batch20/21 drafts — and ~38 messages already SENT to prospects — carried a
   `google.com/url?q=https://…&ust=…` redirect wrapper as the VISIBLE `Website:` line.
   Canary drafts (2026-07-02, 4 controlled creates) isolated the cause: since
   ~2026-06-30 21:30–22:15 PDT the Gmail CONNECTOR rewrites any url/domain in the
   submitted plaintext into the wrapper at ingest (scheme-less input additionally
   downgrades to q=http). Plaintext-only drafts therefore ship the visible wrapper.
   The old readback check passed it because it only rejected `q=http://`. The v2.9
   protocol requires supplying `htmlBody` via `render_html()` (the composer loads the
   html part, so what Charles reviews/sends is the clean anchor) and gates readback
   with `check_readback_artifact(plain, price, html_supplied=True)`.
2. A lone wrong `$` amount with `optional_price=None` passed `check_offer_and_price`.
3. `label_thread` failed connector-side across batches 19–21, leaving labels as prose
   "PENDING" notes with no retry mechanism.
4. The batch13 `ERR_NETWORK_CHANGED` retry created a duplicate Gmail draft — draft
   creation had no pre-create live-Gmail dedupe or intent journaling.

**Engine v2.7 (`preflight.py`, POLICY_VERSION 2.6 → 2.7):**
- New `check_readback_artifact(stored_plaintext, expected_price)` — MANDATORY
  post-creation gate on the plaintext read back from Gmail: fails on the
  `google.com/url` wrapper in plaintext (`READBACK_ARTIFACT_DEFECT`), `q=http://`
  downgrade, missing canonical domain, unsubstituted postal placeholder, missing
  opt-out line, missing `MOTIONX · <address>` footer line, or a stored `$` amount that
  differs from the offer price.
- `check_gmail_readback_link(stored_body, is_plaintext=True)` strengthened: the wrapper
  is tolerated only for `is_plaintext=False` (htmlBody anchor href).
- `check_offer_and_price` hardened: a lone `$` amount must equal the selected offer's
  configured price even when `optional_price` is unset.
- Runs pass `policy_version="2.7"`. Tests: 155 → **170 green** (15 added: readback
  clean/wrapper/downgrade/placeholder/opt-out/footer/price ±, the `html_supplied`
  tolerated-`q=https` vs still-failing-`q=http`/wrong-destination variants, and
  lone-price hardening).

**Operating policy 2.8 → 2.9 (SKILL.md):**
- Step 8 gains item 0: live-Gmail idempotency check (`list_drafts to:` +
  `in:sent to:<recipient> newer_than:90d`) + an intent row appended BEFORE
  `create_draft` (no blind create-retries), and item 2 gains the `pending_labels`
  retry queue in `state.json` (labels are state, not prose notes).
- Documented the previously code-only engine gates (2.6 geography, 2.7 readback) in a
  dedicated section; fixed four stale load-bearing literals (pass `policy_version=2.7`,
  Step 8 v2.6.1 signature block, Step 7 word window 90–125/75–140, packet records the
  config policy version instead of a hardcoded "2.4"); resolved the Step 1
  decline-vs-suppression contradiction (polite declines are labelled, never suppressed;
  suppression = explicit opt-out or bounce only).
- `config.json`: versions bumped (policy 2.9 / engine 2.7), v2.3-era signature fields
  replaced with the v2.6.1 reality (they contradicted `preflight.py` — the old
  `signature_banned_tokens` banned `Website:`/`Email Address:`/the founder address that
  the canonical signature now requires), `subject_words_max` aligned to the engine's
  long-standing 2–6, `READBACK_ARTIFACT_DEFECT` added to failure codes, stale
  continuous-improvement note corrected.
- No gate weakened; no threshold lowered; offers/prices/positioning unchanged.
