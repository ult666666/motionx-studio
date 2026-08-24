# MOTIONX — Outreach kit

Reusable, manual-review materials for founding-client pilot outreach. **Nothing
here is sent automatically.** Personalize, review, and send yourself.

## Two layers
1. **Manual kit** (this folder's `*.md` templates + `signature.html`) — for hand
   outreach.
2. **Automated research/drafting system** — the `motionx-outreach` skill
   (`.claude/skills/motionx-outreach/SKILL.md`) + the `MOTIONX High-Touch Client
   Outreach` routine. It researches, qualifies, and prepares **review-ready Gmail
   drafts**. It is **DRAFT_ONLY** (the connected Gmail connector has no send
   tool) and runs in **TEST** mode. Config: `config.json`. Method/voice/scoring/
   policy: `research-thesis-framework.md`, `personalization-rubric.md`,
   `tone-guide.md`, `qualification-rubric.md`, `suppression-policy.md`. Each
   qualified prospect requires a written account thesis + a review packet
   (≥9/10 personalization) before any draft. Persistent CRM, suppression, outcome
   log, and review packets live OUTSIDE this repo at `~/.motionx-outreach/`.
   Every draft is gated by the deterministic validator `preflight.py` (per-draft) and,
   for multi-draft runs, `batch_preflight()` (whole-batch diversity) and
   `batch_voice_preflight()` (whole-batch AI-voice / human-cadence); a draft reaches
   Gmail only when ALL return PASS. Tests: `tests/test_preflight.py`. Policy history:
   `CHANGELOG.md` (current: **operating policy v2.9 / engine v2.7 — Artifact Readback Integrity**).

> The automated system supersedes the older `01-cold-outreach.md` /
> `02-follow-up.md` wording (those use blacklisted phrases like "I came across").
> Keep the templates for reference, but the skill generates fresh, per-business copy.

## Files
- `signature.html` — Gmail signature for `charles@madebymotionx.com` (install steps inside).
- `01-cold-outreach.md` — main founder cold-email template.
- `02-follow-up.md` — short follow-up (send ~4–6 business days later, no reply only).
- `motionx-film-thumb.jpg` — 600×338 email-safe studio-reel thumbnail with a play
  button. Insert as an **image linked to** https://madebymotionx.com — do **not**
  embed autoplaying video in email.

## Addresses
- **Founder / direct outreach:** `charles@madebymotionx.com` (send cold emails from here)
- **Public website contact:** `hello@madebymotionx.com` (the site's contact form + footer)

## Turning a template into a Gmail draft/template
1. Gmail → **Settings → Advanced → Templates → Enable** (optional, for reuse).
2. Compose a new email, paste a template, fill the `[…]` placeholders.
3. To save for reuse: **⋮ (more) → Templates → Save draft as template**.

## Honesty rules (keep these)
No guaranteed results, no fake scarcity/countdowns, no invented clients or
metrics. Pilot pricing is introductory — final scope may affect the quote.
