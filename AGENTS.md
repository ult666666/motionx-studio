# AGENTS.md — MOTIONX agent entry point

This is the entry point for non-Claude agent sessions (Codex, Cursor, etc.).
Read it first, then read **`CLAUDE.md`**.

## Canonical source of truth

**`CLAUDE.md` (repo root) + `src/content/*` are authoritative.** This file is a concise
agent-facing pointer; it does not restate every rule. Before changing anything, read
`CLAUDE.md` end-to-end — it holds the full detail on positioning, section order, the
palette/visual system, animation & video rules, the hero-reel recipe, the contact flow,
pilot pricing, email/DNS facts, testing, and gotchas. `CLAUDE.md` and this file must
never contradict each other; if they ever drift, `CLAUDE.md` wins and should be fixed.

Claude Code reads `CLAUDE.md`; agents read this file. The two skill bundles mirror each
other: **`.claude/skills/`** (Claude) and **`.agents/skills/`** (agents). They must stay
consistent — any change to a safety-critical constraint must be applied to *both* copies.
Provenance/audit of the skills is in `.claude/skills/INSTALL-MANIFEST.md`.

## What this is

A **motion-first creative studio** website (Next.js 15 App Router + React 19 + TypeScript,
Tailwind v4 CSS-first, CSS-only animation). Positioning: *"We create the moving visual world
around a product — the cinematic product film — then extend that same world into the
website, launch page, and campaign system."* Tagline: **"From first frame to final click."**
Core offer: Product Films · Motion-First Websites · Product Launch Pages · Campaign Content
Systems. Live at **madebymotionx.com**. See `CLAUDE.md` for the full business/section rules.

## Non-negotiables (mirrored here so an agent sees them before reading CLAUDE.md)

- **Honesty is absolute.** No fake clients, testimonials, awards, team members, statistics,
  conversion numbers, production credits, quotes, press, or scarcity/countdowns. The studio
  is honestly small and independent.
- **Concept-label integrity.** All portfolio projects are **concept** work and must stay
  labelled as such. Never claim MOTIONX was commissioned by the real third-party
  pharmaceutical product in the botanical clip (or any real client). No unsupported
  medical/health claims. The self-owned AURA System Study, including `/system-study`,
  must also remain visibly labelled as a concept with its no-client/no-results disclosure.
- **No invented facts.** No made-up location/"Based in", no invented domain (`site.url`
  comes from `NEXT_PUBLIC_SITE_URL`), no placeholder social profiles (`site.social` is
  intentionally empty). Public contact is **`hello@madebymotionx.com`**; the founder's
  direct address **`charles@madebymotionx.com`** and the personal backup Gmail address
  (named in `CLAUDE.md`) must not appear anywhere in `src/` or built browser artifacts.
- **Content stays centralized** in `src/content/*` — don't scatter literals into components.
- **The MOTIONX design system (CLAUDE.md + `src/content/*`) overrides generic skill advice.**
  Skills advise; they do not authorize drift from the palette, restraint rules, section
  order, or content-integrity rules.
- **Assets:** never delete, rename, overwrite, or recompress the original `hf_2026…*.mp4`
  files; `public/videos/*` are derivatives.

## Website work

Route all website changes through the **`motionx-website-upgrade`** skill
(`.agents/skills/motionx-website-upgrade/SKILL.md`), which sequences frontend-design,
ui-ux-pro-max (reference only), react-best-practices, web-design-guidelines, and
webapp-testing while preserving the established design system.

- **Local dev/preview: port 3939** (`.claude/launch.json`; Node is in the `motionx` conda
  env at `/opt/anaconda3/envs/motionx/bin`, not on the default PATH). E2E: `npm run test:e2e`.
- **Visual/behavioural changes require real browser verification** (desktop + mobile,
  console, overflow, reduced motion). A green typecheck/lint/build is **not** sufficient
  on its own. See CLAUDE.md → "Testing, preview & verification".
- **Run the project gate before commit:** `npm run gate` now starts with
  `npm run content:check`, `npm run assets:check`, and `npm run seo:check` before
  typecheck, lint, build, and e2e.
- **Preserve unrelated local work:** never stage, commit, reset, stash, clean, delete,
  or overwrite `outreach/self-improvement.md` or any other unrelated dirty file during
  website work.

## Outreach is a separate workstream (do not conflate)

The **`motionx-outreach`** skill (`.agents/skills/motionx-outreach/`, mirror of
`.claude/skills/motionx-outreach/`), its CRM (`~/.motionx-outreach/`, outside the repo),
Gmail, Cloudflare/DNS, Vercel deploys, pricing, and secrets are **out of scope for website
work and must not be modified during website tasks.** Outreach is **DRAFT_ONLY** (the
connector cannot send) and runs in **TEST** mode; **only Charles sends email, by hand.**
Never expose private recipient data, postal addresses, backup emails, or credentials.

## Codex-native outreach automation

These rules apply whenever Codex works on `outreach/`, `~/.motionx-outreach/`, Gmail,
OpenAI, CRM reconciliation, batch32, visual-cold-open, or agentic-ops.

### Role boundaries

- Charles makes final decisions and is the only person who sends email.
- Codex performs bounded execution: inspection, scoped source edits, verification,
  reconciliation, no-send automation, report generation, ledger/context-pack generation,
  and handoff generation.
- Claude Code may be used for larger open-ended design/build work when available, but Codex
  must still preserve this repo's DRAFT_ONLY and no-secret safety contract.

### Outreach policy

- Outreach is DRAFT_ONLY.
- Do not send or schedule emails.
- Do not mutate Gmail except when an explicit future DRAFT_ONLY task authorizes draft
  creation/update after readiness passes.
- Never call Gmail send paths such as `messages.send`, `drafts.send`, scheduled send, or
  `messages.insert`.
- Do not run full batch32 or promote candidates unless Charles explicitly authorizes that
  exact action.
- Manual visual `chatgpt-bulk-pack`, `collect-downloads`, prompt-pack/import/preview
  modes are the approved no-OpenAI-API-cost path: Codex prepares one master ChatGPT
  prompt plus fallback chunks, Charles generates/downloads images manually in GPT-5.5
  Pro Chat, and Codex collects/imports/validates local files. `OPENAI_API_KEY` is not
  required for those manual modes.

### Content integrity

- Do not invent clients, metrics, testimonials, awards, case studies, relationships, prior
  MOTIONX work, company facts, product facts, or recipient emails.
- Use only source-of-truth data already in the repo, operator-provided context, verified
  official pages, or explicitly authorized read-only Gmail/CRM context.
- Missing information must remain missing and be reported as uncertainty.

### Secrets and private state

- Do not read, print, write, or commit secret values: `OPENAI_API_KEY`, Gmail OAuth tokens,
  `client_secret`, `refresh_token`, postal address, backup emails, or private CRM exports.
- Presence checks are allowed when performed by the existing tooling.
- The only approved local setup path for writing `OPENAI_API_KEY` is
  `python3 outreach/agentic_ops/run.py credentials-setup --interactive --write-openai-key`,
  which uses hidden input and writes outside the repo.
- Keep generated outputs outside the repo under `~/.motionx-outreach/` unless the file is
  intentional source, docs, or tests.
- Do not modify `~/.claude/settings.json` or enable hooks globally unless Charles gives a
  separate explicit instruction.

### Required preflight

From the repo root, run and inspect:

```bash
pwd
git status --short
git branch --show-current
git log --oneline -5
git worktree list
```

If the main worktree is dirty, use a linked worktree before editing. Always preserve
`outreach/self-improvement.md`. Confirm HEAD contains `b3dbfb7` or a descendant for
agentic-ops work.

### Verification style

- Prefer focused tests that prove the changed safety contract.
- Report exact commands run, pass/fail results, output paths, final branch/HEAD, dirty
  files, and remaining blockers.
- Verify generated reports/handoffs/ledgers/context packs are outside the repo and contain
  no secrets.
- Explicitly confirm no Gmail/OpenAI live calls, no sends/schedules, no draft
  creation/update, and no CRM mutation unless a future task explicitly authorizes a bounded
  DRAFT_ONLY draft operation.

### Agentic-ops commands

Use these commands for no-write oversight:

- `python3 outreach/agentic_ops/run.py status`
- `python3 outreach/agentic_ops/run.py vco-readiness`
- `python3 outreach/agentic_ops/run.py batch32-status`
- `python3 outreach/agentic_ops/run.py ledger`
- `python3 outreach/agentic_ops/run.py context-pack`
- `python3 outreach/agentic_ops/run.py credentials-setup --verify-only`
- `python3 outreach/agentic_ops/run.py live-setup-checklist`
- `python3 outreach/agentic_ops/run.py daily-report`
- `python3 outreach/agentic_ops/run.py handoff --target codex --task live-setup`
- `python3 outreach/agentic_ops/run.py handoff --target codex --task one-paste-chatgpt-visual-pack`
- `python3 outreach/agentic_ops/run.py handoff --target codex --task collect-chatgpt-downloads`
- `python3 outreach/agentic_ops/run.py handoff --target codex --task manual-visual-preview-with-collected-images`
- `python3 outreach/agentic_ops/run.py handoff --target codex --task manual-visual-prompt-pack`
- `python3 outreach/agentic_ops/run.py handoff --target codex --task manual-visual-import`
- `python3 outreach/agentic_ops/run.py handoff --target codex --task manual-visual-live-drafts`

These commands must not send email, create/update Gmail drafts, call OpenAI image
generation, or mutate CRM.
