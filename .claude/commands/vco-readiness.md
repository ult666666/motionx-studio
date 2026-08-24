---
description: Visual-cold-open 3-sample live-draft readiness gate — no-write check, prints READY or exact blockers
allowed-tools: Bash(python3 outreach/agentic_ops/run.py vco-readiness*), Read
---

# Visual-cold-open readiness

Run the safe agentic-ops **vco-readiness** gate and report the verdict.

## What this does
- No-write readiness check for the 3 sample **live drafts**:
  - repo at/after baseline `29f3ddf`,
  - out-of-repo venv present with readiness packages installed,
  - `OPENAI_API_KEY` presence only (no value),
  - Gmail token presence only (no contents),
  - top-3 recipient review CSV parsed,
  - confirms no Gmail write path is invoked.
- Prints `READY_FOR_3_SAMPLE_LIVE_DRAFTS` **only if every gate passes**; otherwise prints the
  exact blockers (`BLOCKED_ON_GPT_IMAGE_2_ACCESS`, `BLOCKED_ON_GMAIL_DRAFT_ACCESS`).
- Writes `~/.motionx-outreach/reports/vco_readiness_<stamp>.md`.

## Run
```bash
python3 outreach/agentic_ops/run.py vco-readiness
```

## Safety rules (do not violate)
- **No images are generated. No Gmail drafts are created. Nothing is sent or scheduled.**
- Do NOT run the live visual-cold-open workflow from this command — this is a readiness
  check only.
- Do NOT print, write, or commit any secret. Presence-only checks.
- Outputs stay OUTSIDE the repo. Outreach is DRAFT_ONLY.
