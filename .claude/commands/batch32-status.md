---
description: Batch32 candidate/recipient status — sourced/APPROVE/MAYBE/REJECT counts, top-3, Trailpoint CX-mailbox flag — read-only
allowed-tools: Bash(python3 outreach/agentic_ops/run.py batch32-status*), Read
---

# Batch32 status

Run the safe agentic-ops **batch32-status** command and summarize the pipeline.

## What this does (read-only)
- Parses the batch32 sourcing CSV, approval packet, and top-3 recipient review CSV under
  `~/.motionx-outreach/reports/` — **no CSV, packet, or CRM file is mutated**.
- Reports counts: total sourced, APPROVE / MAYBE / REJECT, selected top-3, and verified
  recipient-email count (with a ranked-table cross-check).
- Flags **Trailpoint `support@trailpoint.example` as a Customer-Experience mailbox** (technical sample
  only), and marks it pending unless a Charles approval record exists under
  `~/.motionx-outreach/approvals/` or `~/.motionx-outreach/charles_recipient_approvals.txt`.
- Masks recipient local-parts in the report.
- Writes `~/.motionx-outreach/reports/batch32_status_<stamp>.md`.

## Run
```bash
python3 outreach/agentic_ops/run.py batch32-status
```

## Safety rules (do not violate)
- Read-only. Do NOT mutate any CSV, the CRM, `leads.csv`, `state.json`, or the candidate queue.
- Do NOT create Gmail drafts, send, or schedule anything.
- Do NOT promote any candidate to live outreach — that is Charles's decision.
- Do NOT print or commit secrets or full private recipient addresses. Outputs stay OUTSIDE the repo.
