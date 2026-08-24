# MOTIONX agentic-ops runbook

A small, tested, **stdlib-only** oversight layer that lets Charles and Codex quickly
check project/outreach readiness, generate next-action reports, and produce
Codex-ready handoffs — **while live credentials are still pending**. It automates the
*watching*, not the *doing*.

> **DRAFT_ONLY.** This layer only **reads** state and **writes reports/handoffs
> outside the repo**. It never sends or schedules email, never creates or updates
> Gmail drafts, never generates images, never runs the live visual-cold-open
> workflow, never mutates the CRM, and never touches secrets. **Charles is the only
> human who sends email.**

Code lives in `outreach/agentic_ops/` (flat modules, same convention as
`outreach/visual_cold_open/`). Tests: `outreach/tests/test_agentic_ops.py`.

---

## What it does

| Command | What it reports | Output file (under `~/.motionx-outreach/`) |
|---|---|---|
| `status` | repo (branch/HEAD/baseline/dirty), auth+dep readiness (presence only), latest reports, latest VCO readiness verdict, claimed-done-but-unverified flags, highest-value next action | `reports/motionx_ops_status_<stamp>.md` |
| `vco-readiness` | no-write gate for the 3 sample live drafts; prints `READY_FOR_3_SAMPLE_LIVE_DRAFTS` **only if every gate passes**, else the exact blockers | `reports/vco_readiness_<stamp>.md` |
| `batch32-status` | sourced / APPROVE / MAYBE / REJECT counts, top-3, verified-email count, Trailpoint Customer-Experience flag | `reports/batch32_status_<stamp>.md` |
| `ledger` | appends workflow/evidence JSONL and writes a markdown ledger: VCO/agentic status, batch32 state, approval state, credential presence, readiness, next action | `ledger/motionx_workflow_ledger.jsonl` + `reports/motionx_workflow_ledger_<stamp>.md` |
| `context-pack` | concise future-Codex context pack: HEAD/dirty files, commands, blockers, report/handoff paths, may/must-not rules, next task | `handoffs/codex_context_pack_<stamp>.md` |
| `credentials-setup` | safe setup/check assistant for OPENAI_API_KEY and Gmail OAuth; default/`--verify-only` are no-write checks; interactive writes stay outside repo | `reports/credentials_setup_<stamp>.md` |
| `live-setup-checklist` | human checklist: OpenAI key, packages, Gmail credentials JSON, Gmail token, account status, approval state, readiness, next command | `reports/live_setup_checklist_<stamp>.md` |
| `handoff` | a self-contained Codex handoff (exact 8-field format) | `handoffs/<task>_<stamp>.txt` |
| `daily-report` | "what should Charles do next?" — done / blocked / unverified / next 1–3 actions with the right agent + generated handoff paths | `reports/motionx_daily_ops_<stamp>.md` |
| `record-batch32-top3-approval` | explicit Charles approval capture for the exact top-3 technical sample recipients; requires `--charles-approved-top3` | `approvals/batch32_top3_recipient_approval_<stamp>.md` + `charles_recipient_approvals.txt` |

## What it does NOT do

- Does **not** send/schedule email, or call any `messages.send` / `drafts.send` /
  `messages.insert` / any `*.send` endpoint.
- Does **not** create or update Gmail drafts, or archive/delete/label/trash anything.
- Does **not** generate images or call gpt-image-2.
- Does **not** run the live visual-cold-open workflow or run batch32.
- Does **not** mutate `leads.csv`, `state.json`, `candidate-queue.csv`, `suppression.csv`,
  the review-packet queue, or any CRM file.
- Does **not** read, print, write, or commit `OPENAI_API_KEY`, Gmail OAuth tokens,
  `client_secret` / `refresh_token`, or the postal address (presence-only checks).
- Does **not** touch `outreach/self-improvement.md` (pre-existing, unrelated).
- Does **not** modify global `~/.claude` settings or enable any hook.

## Command examples

```bash
# One command to see the whole picture:
python3 outreach/agentic_ops/run.py status

# Is the 3-sample live-draft path ready? (no writes, no drafts, no images)
python3 outreach/agentic_ops/run.py vco-readiness

# Batch32 candidate + recipient counts and flags:
python3 outreach/agentic_ops/run.py batch32-status

# Append evidence ledger + write a markdown ledger report:
python3 outreach/agentic_ops/run.py ledger

# Generate a future Codex context pack:
python3 outreach/agentic_ops/run.py context-pack

# Check credentials without prompts or writes:
python3 outreach/agentic_ops/run.py credentials-setup --verify-only

# Human checklist for live setup:
python3 outreach/agentic_ops/run.py live-setup-checklist

# Produce a Codex-ready handoff for later live setup:
python3 outreach/agentic_ops/run.py handoff --target codex --task live-setup

# Produce manual-visuals handoffs:
python3 outreach/agentic_ops/run.py handoff --target codex --task one-paste-chatgpt-visual-pack
python3 outreach/agentic_ops/run.py handoff --target codex --task collect-chatgpt-downloads
python3 outreach/agentic_ops/run.py handoff --target codex --task manual-visual-preview-with-collected-images
python3 outreach/agentic_ops/run.py handoff --target codex --task manual-visual-prompt-pack
python3 outreach/agentic_ops/run.py handoff --target codex --task manual-visual-import
python3 outreach/agentic_ops/run.py handoff --target codex --task manual-visual-live-drafts

# The daily "what next" report (also generates the relevant handoff):
python3 outreach/agentic_ops/run.py daily-report
```

Handoff tasks: `live-setup`, `three-sample-live-drafts`, `credentials-setup`,
`batch32-normalized-draft-dry-run`, `batch32-visual-dry-run`,
`batch32-full-live-drafts-after-review`, `crm-gmail-reconcile`, `source-next-20`,
`one-paste-chatgpt-visual-pack`, `collect-chatgpt-downloads`,
`manual-visual-preview-with-collected-images`, `manual-visual-prompt-pack`,
`manual-visual-import`, `manual-visual-live-drafts`.
`batch32-draft-dry-run` remains a compatibility alias for
`batch32-normalized-draft-dry-run`.

Project slash commands (in `.claude/commands/`): `/motionx-status`, `/vco-readiness`,
`/batch32-status`, `/codex-handoff-live-setup`, `/motionx-daily`.

## Where reports go

Everything is written **outside the repo** under `~/.motionx-outreach/`:
- reports → `~/.motionx-outreach/reports/`
- handoffs → `~/.motionx-outreach/handoffs/`
- ledger → `~/.motionx-outreach/ledger/`
- approvals → `~/.motionx-outreach/approvals/`
- credentials → `~/.motionx-outreach/secrets.env`, `gmail_credentials.json`,
  `gmail_token.json` (all outside repo)

The CLI refuses to write inside the repo tree (`assert_outside_repo`), and scans every
report/handoff for secrets before writing (`scanner`). Recipient local-parts are masked
in human reports (e.g. `s***@trailpoint.example`).

## How to read statuses

- **`READY_FOR_3_SAMPLE_LIVE_DRAFTS`** — every readiness gate passed; the 3 sample live
  drafts can be created (draft-only) *after* Charles approves the recipients.
- **`BLOCKED_ON_GPT_IMAGE_2_ACCESS`** — `OPENAI_API_KEY` is not set in the CLI
  environment (gpt-image-2 unreachable).
- Manual-visuals one-paste prompt-pack, collect-downloads, import, and preview modes do
  **not** need `OPENAI_API_KEY`; that blocker applies only to API image generation, not
  to Charles's GPT-5.5 Pro Chat manual-image workflow.
- **`BLOCKED_ON_GMAIL_DRAFT_ACCESS`** — the Gmail OAuth token
  (`~/.motionx-outreach/gmail_token.json`) is absent.
- **Claimed-done-but-unverified** — e.g. a "live result" report exists while readiness is
  still blocked, so no real Gmail draft could have been created. Treat as unverified until
  a Gmail read-back (`is_draft=true`) confirms an actual draft.
- **Trailpoint Customer-Experience flag** — `support@trailpoint.example` is a customer-service mailbox,
  not marketing/press; it is approved only for a **technical sample**, and only once
  Charles's approval is recorded (see below).

## How Codex should use generated handoffs

1. Read the whole handoff `.txt` (it is self-contained: Objective / Verified current
   state / Source of truth / Already done / Codex should execute / Codex must NOT /
   Verification required / Risks).
2. Do exactly what "Codex should execute" says, in order, and nothing in "Codex must NOT".
3. The execute block is always **draft-only / read-only** — it never instructs a send.
   Leave every draft unsent for Charles.
4. Prove completion via "Verification required" before reporting done.

## Recording Charles's recipient approvals

The top-3 recipients start as `REVIEW_ONLY_PENDING_CHARLES_APPROVAL`. To let
`batch32-status` show a recipient as approved (e.g. the Trailpoint Customer-Experience mailbox
for a technical sample), run:

```bash
python3 outreach/agentic_ops/run.py record-batch32-top3-approval --charles-approved-top3
```

This writes a durable approval artifact under
`~/.motionx-outreach/approvals/batch32_top3_recipient_approval_<stamp>.md` and updates:

```
~/.motionx-outreach/charles_recipient_approvals.txt
```

The artifact records only these exact top-3 approvals for the technical 3-sample
DRAFT_ONLY test. It does **not** authorize sending, full batch32, guessed recipients, or
Gmail draft creation before OpenAI/Gmail readiness passes. Absent approval files = no
approvals recorded (the safe default).

## Enabling the hook templates later

Optional defense-in-depth lives in `outreach/agentic_ops/hook_templates/` and is **not
enabled**. See `hook_templates/HOOKS-RUNBOOK.md`. In short: read `agentic_ops_guard.py`,
merge the `hooks` block from `settings.hooks.template.json` into project
`.claude/settings.json`, make the guard path absolute, and remove the `_TEMPLATE_*` keys.
The guard blocks `git push` / `git reset --hard` / `git clean -fd` / `rm -rf`, Gmail send
paths, and secret exposure, and warns on in-repo artifacts / `self-improvement.md` touches.

## Live prerequisites still needed (for the 3 sample live drafts)

The setup assistant helps Charles provision/check these without creating drafts:
- `OPENAI_API_KEY` in `~/.motionx-outreach/secrets.env` or the CLI environment
  (gpt-image-2 access). To enter it locally without printing it:

  ```bash
  python3 outreach/agentic_ops/run.py credentials-setup --interactive --write-openai-key
  ```

  The prompt is hidden, the key is never echoed, `MOTIONX_POSTAL_ADDRESS` is preserved,
  duplicate `OPENAI_API_KEY` entries are collapsed, and `secrets.env` is chmod `600`.
- Google OAuth Desktop App credentials JSON at
  `~/.motionx-outreach/gmail_credentials.json`. If missing, download a Desktop App
  credentials JSON with Gmail API enabled and place it there.
- Gmail OAuth token at `~/.motionx-outreach/gmail_token.json` (compose scope). Once
  `gmail_credentials.json` exists, run:

  ```bash
  python3 outreach/agentic_ops/run.py credentials-setup --setup-gmail-oauth
  ```

  Use `--no-browser` if the OAuth helper supports it. Use `--force-refresh-token` only
  when intentionally replacing an existing token.
- Gmail account verified as **`charles@madebymotionx.com`**.
- **Charles's explicit approval** for the exact recipients (top-3 remain review-only until
  then; Trailpoint CX-mailbox needs a specific technical-sample approval).

Verify without creating drafts:

```bash
python3 outreach/agentic_ops/run.py credentials-setup --verify-only
python3 outreach/agentic_ops/run.py live-setup-checklist
python3 outreach/agentic_ops/run.py vco-readiness
```

Use `python3 outreach/agentic_ops/run.py handoff --target codex --task live-setup` to
generate the setup handoff, then re-run `vco-readiness` until it prints
`READY_FOR_3_SAMPLE_LIVE_DRAFTS`.

Do not proceed to `three-sample-live-drafts` until `vco-readiness` is ready. The
setup/checklist commands do **not** create Gmail drafts, call Gmail message/draft write
paths, generate GPT images, run full batch32, or mutate CRM.

## Reminder

Outreach is **DRAFT_ONLY**. This layer never sends. Only Charles sends email, by hand.
