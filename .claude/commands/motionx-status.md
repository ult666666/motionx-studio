---
description: MOTIONX agentic-ops status snapshot (repo, auth readiness, reports, next action) — read-only, DRAFT_ONLY
allowed-tools: Bash(python3 outreach/agentic_ops/run.py status*), Read
---

# MOTIONX ops status

Run the safe agentic-ops **status** command and summarize it for Charles.

## What this does
- Reads repo state (branch, HEAD, baseline check, dirty files — `outreach/self-improvement.md`
  is recognized as a pre-existing/unrelated dirty file and preserved).
- Reports auth/dependency readiness (OPENAI_API_KEY presence only, Gmail token presence
  only, venv + readiness packages) **without reading any secret value**.
- Lists the latest reports under `~/.motionx-outreach/reports/` and the latest
  visual-cold-open readiness verdict.
- Surfaces any "claimed-done-but-unverified" signals and the single highest-value next action.
- Writes a markdown report to `~/.motionx-outreach/reports/motionx_ops_status_<stamp>.md`
  (OUTSIDE the repo).

## Run
```bash
python3 outreach/agentic_ops/run.py status
```

Then read back the printed verdict, blockers, next action, and the report path.

## Safety rules (do not violate)
- This is **read-only oversight**. Do NOT send or schedule email, create/update Gmail
  drafts, generate images, run the live visual-cold-open workflow, or mutate CRM.
- Do NOT print, write, or commit `OPENAI_API_KEY`, Gmail OAuth tokens, or the postal address.
- All outputs must stay OUTSIDE the repo (under `~/.motionx-outreach/`). The CLI enforces this.
- Outreach is DRAFT_ONLY — Charles is the only human who sends email.
