# Outreach-Specific Codex Rules

The outreach subtree is stricter than the rest of the repo.

## Non-Negotiables

- DRAFT_ONLY: never send or schedule email. Do not send outreach from automation.
- Do not create or update Gmail drafts unless a future task explicitly authorizes a bounded
  DRAFT_ONLY draft operation and readiness gates pass.
- Never call messages.send, drafts.send, scheduled send, messages.insert, trash, delete, or
  archive/label mutation paths.
- Do not mutate CRM files: `leads.csv`, `state.json`, candidate queues, suppression lists,
  outcome logs, or source CSVs unless Charles explicitly authorizes that exact mutation.
- Do not store private recipient addresses, secrets, OAuth JSON, postal addresses, or CRM
  exports in the repo.
- Keep generated reports, ledgers, handoffs, context packs, previews, and approval records
  under `~/.motionx-outreach/`.
- Manual visual `chatgpt-bulk-pack`, `collect-downloads`, prompt-pack/import/preview
  modes are the approved lower-cost path when Charles wants to create images manually
  in GPT-5.5 Pro Chat. They must not require `OPENAI_API_KEY`, call OpenAI image APIs,
  automate/scrape ChatGPT UI, or mutate Gmail/CRM.
- Use `python3 outreach/agentic_ops/run.py credentials-setup --verify-only` and
  `python3 outreach/agentic_ops/run.py live-setup-checklist` to check live readiness
  without creating drafts, calling OpenAI image generation, or mutating Gmail.

## Content Integrity

- Use official source evidence and existing approved workflow artifacts only.
- Do not invent enrichment, recipient emails, company facts, product claims, testimonials,
  metrics, awards, relationships, prior MOTIONX work, or case studies.
- If a source is missing or ambiguous, block or mark uncertainty rather than guessing.
- Trailpoint `support@trailpoint.example` is Customer-Experience oriented and only valid for a
  Charles-approved technical sample.

## Source Of Truth

- Agentic ops source: `outreach/agentic_ops/`.
- Visual cold-open source: `outreach/visual_cold_open/`.
- Batch32 source artifacts live outside the repo under `~/.motionx-outreach/reports/`.
- Manual visual workspaces live outside the repo under
  `~/.motionx-outreach/manual-visuals/`.
- Charles approval records live outside the repo under `~/.motionx-outreach/approvals/` and
  `~/.motionx-outreach/charles_recipient_approvals.txt`.

## Verification

- Run the relevant `outreach/tests/` suites after source changes.
- Verify generated files are outside the repo.
- Verify no secrets, Gmail token JSON, refresh_token, client_secret, or raw API key values
  appear in reports, handoffs, ledgers, or context packs.
- Always preserve `outreach/self-improvement.md`.
