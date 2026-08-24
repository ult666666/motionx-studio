# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — reports & activity log.

Writes a per-prospect CSV report, a markdown summary, and appends to a DEDICATED
visual activity log (its own header — it never touches the existing 13-column
~/.motionx-outreach/activity-log.csv, to avoid corrupting that schema). All rows are
scrubbed of secret-looking material and use a masked recipient identifier; the
`sent_or_scheduled` column is hard-wired to "no".
"""
from __future__ import annotations

import csv
import os as _os
import sys as _sys
from typing import List

_VCO_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _VCO_DIR not in _sys.path:
    _sys.path.insert(0, _VCO_DIR)

import safety  # noqa: E402

REPORT_COLUMNS = [
    "batch_id",
    "company",
    "safe_recipient_identifier",
    "source_record_id",
    "duplicate_check_result",
    "draft_id",
    "draft_action",           # created | updated | skipped | blocked
    "visual_status",          # generated | attached | failed_generation | failed_qa | not_created
    "attachment_filename",
    "attachment_path",
    "body_says_attached",     # yes | no
    "gpt_image_model_used",
    "gpt_image_size",
    "fabrication_check_passed",  # yes | no
    "gmail_draft_confirmed",     # yes | no
    "sent_or_scheduled",         # ALWAYS no
    "notes",
]

ACTIVITY_COLUMNS = [
    "timestamp", "batch_id", "mode", "source_record_id", "company",
    "safe_recipient_identifier", "status", "draft_action", "visual_status",
    "draft_id", "gmail_draft_confirmed", "sent_or_scheduled", "notes",
]

# Section-12 sample-run report schema (one row per sample candidate).
SAMPLE_REPORT_COLUMNS = [
    "sample_id",
    "company",
    "domain",
    "selected_from",
    "decision_source",
    "draft_status",              # gmail_draft_created | local_preview | blocked
    "gmail_draft_id",            # masked/partial if created; else empty
    "visual_status",
    "image_model",
    "image_path",
    "attachment_status",         # attached | none | blocked
    "body_says_attached",        # yes | no
    "fabrication_check_passed",  # yes | no
    "gmail_draft_confirmed",     # yes | no
    "sent_or_scheduled",         # ALWAYS no
    "notes",
]


def _scrub_row(row: dict) -> dict:
    clean = {}
    for k, v in row.items():
        s = "" if v is None else str(v)
        clean[k] = safety.redact_secrets(s)
    # Hard invariant: this workflow never sends or schedules.
    clean["sent_or_scheduled"] = "no"
    # A report/log never carries a full Gmail draft id verbatim (mask centrally, so a
    # raw id in either the id columns OR a free-text notes column is caught).
    for idk in ("draft_id", "gmail_draft_id"):
        if clean.get(idk):
            clean[idk] = safety.mask_draft_id(clean[idk])
    return clean


def write_report_csv(path: str, rows: List[dict]) -> str:
    _os.makedirs(_os.path.dirname(_os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=REPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(_scrub_row(row))
    return path


def append_activity_log(path: str, rows: List[dict], timestamp: str) -> str:
    _os.makedirs(_os.path.dirname(_os.path.abspath(path)), exist_ok=True)
    exists = _os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ACTIVITY_COLUMNS, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        for row in rows:
            out = {"timestamp": timestamp}
            out.update(row)
            writer.writerow(_scrub_row(out))
    return path


def write_sample_report_csv(path: str, rows: List[dict]) -> str:
    """Write the section-12 sample-run CSV (scrubbed; sent_or_scheduled hard-wired 'no')."""
    _os.makedirs(_os.path.dirname(_os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SAMPLE_REPORT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(_scrub_row(row))
    return path


def write_sample_summary_md(path: str, batch_id: str, mode: str, rows: List[dict],
                            preflight_notes: List[str], blockers: List[str]) -> str:
    """Human-readable markdown for a --sample-only run (section-12 deliverable)."""
    _os.makedirs(_os.path.dirname(_os.path.abspath(path)), exist_ok=True)
    created = sum(1 for r in rows if r.get("draft_status") == "gmail_draft_created")
    previews = sum(1 for r in rows if r.get("draft_status") == "local_preview")
    blocked = sum(1 for r in rows if str(r.get("draft_status", "")).startswith("blocked"))
    attached = sum(1 for r in rows if r.get("body_says_attached") == "yes")
    lines = [
        f"# MOTIONX visual cold-open — SAMPLE run — {batch_id}",
        "",
        f"- **Mode:** {mode} (DRAFT_ONLY — no email was sent or scheduled)",
        f"- **Sample candidates:** {len(rows)}",
        f"- **Gmail drafts created:** {created}",
        f"- **Local previews written:** {previews}",
        f"- **Blocked:** {blocked}",
        f"- **Bodies with attachment language:** {attached}",
        "",
    ]
    if blockers:
        lines.append("## Blockers")
        for b in blockers:
            lines.append(f"- {safety.redact_secrets(b)}")
        lines.append("")
    if preflight_notes:
        lines.append("## Preflight")
        for n in preflight_notes:
            lines.append(f"- {safety.redact_secrets(n)}")
        lines.append("")
    lines.append("## Per-sample")
    lines.append("")
    lines.append("| sample | company | domain | draft status | visual status | "
                 "attachment | attached copy | fabrication ok | sent/sched |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {r.get('sample_id','')} | {r.get('company','')} | {r.get('domain','')} | "
            f"{r.get('draft_status','')} | {r.get('visual_status','')} | "
            f"{r.get('attachment_status','')} | {r.get('body_says_attached','')} | "
            f"{r.get('fabrication_check_passed','')} | {r.get('sent_or_scheduled','no')} |")
    lines.append("")
    lines.append("_No email was sent or scheduled. Only Charles may review and send._")
    content = "\n".join(lines) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def write_summary_md(path: str, batch_id: str, mode: str, rows: List[dict],
                     preflight_notes: List[str]) -> str:
    _os.makedirs(_os.path.dirname(_os.path.abspath(path)), exist_ok=True)
    counts: dict = {}
    for row in rows:
        st = row.get("visual_status", "unknown")
        counts[st] = counts.get(st, 0) + 1
    attached = sum(1 for r in rows if r.get("body_says_attached") == "yes")
    lines = []
    lines.append(f"# MOTIONX visual cold-open — {batch_id}")
    lines.append("")
    lines.append(f"- **Mode:** {mode}")
    lines.append(f"- **Prospects processed:** {len(rows)}")
    lines.append(f"- **Drafts with attachment language:** {attached}")
    lines.append(f"- **Sent or scheduled:** no (this workflow is DRAFT_ONLY)")
    lines.append("")
    lines.append("## Visual status breakdown")
    for st in sorted(counts):
        lines.append(f"- `{st}`: {counts[st]}")
    lines.append("")
    if preflight_notes:
        lines.append("## Preflight")
        for n in preflight_notes:
            lines.append(f"- {safety.redact_secrets(n)}")
        lines.append("")
    lines.append("## Per-prospect")
    lines.append("")
    lines.append("| company | draft action | visual status | attached | draft id | notes |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(
            f"| {r.get('company','')} | {r.get('draft_action','')} | "
            f"{r.get('visual_status','')} | {r.get('body_says_attached','')} | "
            f"{r.get('draft_id','')} | {safety.redact_secrets(str(r.get('notes','')))[:80]} |"
        )
    lines.append("")
    lines.append("_No email was sent or scheduled. Only Charles may review and send._")
    content = "\n".join(lines) + "\n"
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path
