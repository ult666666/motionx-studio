---
description: MOTIONX daily ops report — done / blocked / unverified / next 1-3 actions with the right agent + generated handoff paths
allowed-tools: Bash(python3 outreach/agentic_ops/run.py daily-report*), Read
---

# MOTIONX daily ops

Run the safe agentic-ops **daily-report** command and relay "what should Charles do next?".

## What this does
- Produces a compact daily report:
  - what is **done** (verified),
  - what is **blocked** (with the exact blocker + human explanation),
  - **claimed-done-but-unverified** signals,
  - the **next 1–3 actions**, each with the agent that should do it (Charles vs Codex) and
    the exact command / generated handoff path.
- Generates the relevant Codex handoff (`live-setup` when blocked, else
  `three-sample-live-drafts`) under `~/.motionx-outreach/handoffs/` and references its path.
- Writes `~/.motionx-outreach/reports/motionx_daily_ops_<stamp>.md`.

## Run
```bash
python3 outreach/agentic_ops/run.py daily-report
```

## Safety rules (do not violate)
- Read + report + write-handoff-outside-repo only. Do NOT send/schedule email, create/update
  Gmail drafts, generate images, run the live workflow, or mutate CRM.
- Do NOT print or commit secrets or private postal/recipient data.
- All outputs stay OUTSIDE the repo. Outreach is DRAFT_ONLY — only Charles sends email.
