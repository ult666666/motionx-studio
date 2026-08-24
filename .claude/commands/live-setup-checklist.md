---
description: MOTIONX live-readiness checklist - no-write credential/readiness status
allowed-tools: Bash(python3 outreach/agentic_ops/run.py live-setup-checklist*), Read
---

# MOTIONX live setup checklist

Run the no-write live setup checklist and summarize the exact remaining blockers.

```bash
python3 outreach/agentic_ops/run.py live-setup-checklist
```

This reports OpenAI key presence, venv package presence, Gmail credentials JSON presence,
Gmail token presence, Gmail account verification status, top-3 approval state, readiness
verdict, the next command to run, and the command not to run while blocked.

Safety: no prompts, no secret printing, no Gmail calls, no drafts, no sends, no images,
and no CRM mutation.
