# MOTIONX outreach — personalization rubric (fixed criteria)

Score every draft 0–10 using these fixed criteria. **Minimum to proceed: ≥ 9/10.**
Show the **point-by-point breakdown** (each criterion, sub-score, one-line reason) —
never a bare number.

> **v2.2:** a passing personalization score is **necessary but not sufficient** and
> no longer authorizes a draft by itself. Factual specificity alone over-scored the
> first two drafts. The **binding final gate is the Draft Quality Score (≥9) with
> automatic-failure conditions** (below), set by a **separate editorial pass** — the
> research writer may not be the sole final scorer.

| # | Criterion | Range |
|---|-----------|-------|
| 1 | Trigger specificity | 0–2 |
| 2 | Commercial relevance | 0–2 |
| 3 | Concept specificity | 0–2 |
| 4 | Non-transferability | 0–2 |
| 5 | Natural founder voice | 0–1 |
| 6 | Respect and restraint | 0–1 |

## 1. Trigger specificity (0–2)
- **2** — references a verified, current, specific initiative, product, service,
  campaign, event, or customer path.
- **1** — references a real business detail, but not particularly timely.
- **0** — generic compliment, company description, or industry fact.

## 2. Commercial relevance (0–2)
- **2** — connects the observation to a plausible current business objective.
- **1** — connection is possible but weak or largely assumed.
- **0** — observation has no meaningful relationship to the offer.

## 3. Concept specificity (0–2)
- **2** — the proposed creative direction could only reasonably apply to this
  business or campaign.
- **1** — partially tailored but reusable across similar businesses.
- **0** — generic "video," "website," or "content" suggestion.

## 4. Non-transferability (0–2)
Test: replace the company name, recipient name, product name, and location.
- **2** — the email stops making sense for almost every other prospect.
- **1** — could work for several similar businesses with minor edits.
- **0** — could be sent to dozens of companies unchanged.

## 5. Natural founder voice (0–1)
- **1** — sounds like one thoughtful founder writing to another person.
- **0** — sounds like sales automation, agency copy, or AI-generated praise.

## 6. Respect and restraint (0–1)
- **1** — recognizes what the business already does well and frames the
  opportunity without insulting or diagnosing the company.
- **0** — presumptuous criticism, exaggerated claims, or telling the owner their
  current work is poor.

---

## Hard relationship to other gates
- A passing score (≥9) still does NOT permit a draft unless the **account thesis**
  (research-thesis-framework.md), the **source hierarchy** (≥1 Tier 1 supporting
  the thesis), the **decision-maker fit gate**, and the **non-transferability
  gate** (≥70% reuse → reject) all pass too.
- The non-transferability rubric item (#4) and the standalone non-transferability
  gate are complementary: item #4 scores it; the gate is a hard reject at ≥70%
  reusability on body OR subject.

---

# Draft Quality Score (0–10) — the binding final gate (v2.2)

Set by a **separate editorial pass** (the recipient-empathy editor, SKILL.md Step
7c), **not** by the research writer alone. Show the point-by-point reasoning in the
review packet. **Minimum to proceed: ≥ 9/10.**

| # | Category | Range |
|---|----------|-------|
| 1 | Factual precision | 0–2 |
| 2 | Recipient fit (greeting/decision-maker certainty) | 0–2 |
| 3 | Naturalness (plain language, not over-written) | 0–2 |
| 4 | Respectfulness (no diagnosis/lecture; genuine, not setup for criticism) | 0–2 |
| 5 | Clarity & compression (one idea; passes the phone-screen test) | 0–1 |
| 6 | Signature/link/footer readiness (motionX signature present + clean; compact footer with resolved address; any link https) | 0–1 |

## Automatic-failure conditions (any one → fail, regardless of total)
Fix or reject; never draft past these:
- **Wrong or uncertain greeting** — a specific first name on a general inbox
  (`info@`/`hello@`/`contact@`/`experience@`) without a packet justification.
- **Unsupported conversion or attention claim** (no direct evidence/data).
- **Material contradiction with an official source** not reflected in the thesis.
- **Missing or malformed motionX signature or compliance footer**, or a website link
  whose destination is **`http://`** or genuinely broken. (Gmail's standard
  `google.com/url?q=https://…` tracking wrapper is expected and NOT a failure — pass
  the link via an `htmlBody` https anchor so it stays https.)
- **Product/service cannot currently support the proposed CTA.**
- **More than one central idea.**
- **Patronizing or diagnostic tone.**
- **Generic or systematically repeated subject pattern** (e.g. `A [deliverable] for
  [product]`).

These were exactly the defects the first two drafts (Lumen Aesthetics, Aster Parfum)
slipped past at a self-awarded 9–10; see `~/.motionx-outreach/tests/
sample-draft-regressions.md`.
