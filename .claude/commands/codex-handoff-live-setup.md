---
description: Generate the Codex-ready "live-setup" handoff (provision OPENAI_API_KEY + Gmail token) — writes handoff outside repo
allowed-tools: Bash(python3 outreach/agentic_ops/run.py handoff*), Read
---

# Codex handoff — live setup

Generate the self-contained **live-setup** Codex handoff and print its path.

## What this does
- Builds a handoff (exact 8-field Codex format) describing how to provision the two missing
  live credentials so the 3 sample drafts become READY:
  - `OPENAI_API_KEY` exported into the CLI environment (gpt-image-2 access),
  - the Gmail OAuth token placed at `~/.motionx-outreach/gmail_token.json`.
- The handoff is **setup + verification only** — it explicitly forbids creating drafts,
  sending, generating images, or committing secrets, and is safety-scanned before it is
  written (a send-as-execution instruction or a secret would abort the write).
- Writes `~/.motionx-outreach/handoffs/live-setup_<stamp>.txt` (OUTSIDE the repo).

## Run
```bash
python3 outreach/agentic_ops/run.py handoff --target codex --task live-setup
```

Other available handoffs: `three-sample-live-drafts`, `credentials-setup`,
`batch32-normalized-draft-dry-run`, `batch32-visual-dry-run`,
`batch32-full-live-drafts-after-review`, `crm-gmail-reconcile`, `source-next-20`
(swap `--task`).

## Safety rules (do not violate)
- Generating a handoff does NOT execute it. Do NOT run any live Gmail/OpenAI operation here.
- Do NOT paste real secret values into the handoff or anywhere — the handoff tells Charles
  *how* to provide them, never contains them.
- Do NOT create Gmail drafts, send, or schedule. Outreach is DRAFT_ONLY; only Charles sends.
- The handoff is written OUTSIDE the repo.
