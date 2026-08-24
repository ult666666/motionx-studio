# -*- coding: utf-8 -*-
"""Workflow/evidence ledger + Codex context-pack generation.

Everything here is no-write with respect to Gmail/OpenAI/CRM: it reads the already
available snapshot, latest report/handoff filenames, and writes only out-of-repo
evidence under ~/.motionx-outreach/.

Pure stdlib.
"""
from __future__ import annotations

import json
import os
from typing import Dict, List

import collectors
import paths
import render
import scanner
from engine import Snapshot


AVAILABLE_COMMANDS = [
    "python3 outreach/agentic_ops/run.py status",
    "python3 outreach/agentic_ops/run.py vco-readiness",
    "python3 outreach/agentic_ops/run.py batch32-status",
    "python3 outreach/agentic_ops/run.py ledger",
    "python3 outreach/agentic_ops/run.py context-pack",
    "python3 outreach/agentic_ops/run.py credentials-setup --verify-only",
    "python3 outreach/agentic_ops/run.py live-setup-checklist",
    "python3 outreach/agentic_ops/run.py handoff --target codex --task live-setup",
    "python3 outreach/agentic_ops/run.py daily-report",
]

CODEX_MAY_DO = [
    "inspect repo/report state",
    "run no-write readiness/status/ledger/context-pack commands",
    "write source/docs/tests in an isolated worktree when explicitly tasked",
    "write reports, ledgers, handoffs, and approval records outside the repo",
    "create/update Gmail drafts only in a future explicit DRAFT_ONLY task after readiness passes",
]

CODEX_MUST_NOT = [
    "send or schedule emails",
    "create/update Gmail drafts during status, ledger, context-pack, or readiness checks",
    "call Gmail or OpenAI live APIs from agentic-ops",
    "mutate CRM, leads.csv, candidate queues, suppression lists, or Gmail state",
    "print, write, or commit secrets",
    "touch outreach/self-improvement.md",
    "push, reset, stash, clean, or enable global hooks",
    "guess recipient emails or invent prospect facts",
]


def _file_entries(directory: str, entries: List[tuple]) -> List[Dict[str, object]]:
    out = []
    for name, mtime in entries:
        out.append({"name": name, "path": os.path.join(directory, name), "mtime": mtime})
    return out


def _workflow_status(snap: Snapshot) -> Dict[str, object]:
    root = snap.repo.root
    visual_dir = os.path.join(root, "outreach", "visual_cold_open")
    agentic_dir = os.path.join(root, "outreach", "agentic_ops")
    return {
        "visual_cold_open": {
            "built": os.path.isdir(visual_dir),
            "merged": snap.repo.at_or_after_baseline,
            "tested": os.path.isfile(os.path.join(root, "outreach", "tests", "test_visual_sample.py")),
            "evidence": "outreach/tests/test_visual_sample.py",
        },
        "agentic_ops": {
            "built": os.path.isdir(agentic_dir),
            "merged": snap.repo.at_or_after_agentic_ops,
            "tested": os.path.isfile(os.path.join(root, "outreach", "tests", "test_agentic_ops.py")),
            "evidence": "outreach/tests/test_agentic_ops.py",
        },
    }


def build_ledger_entry(snap: Snapshot) -> Dict[str, object]:
    reports = _file_entries(snap.reports_dir, collectors.list_reports(snap.reports_dir))
    handoffs = _file_entries(snap.handoffs_dir, collectors.list_handoffs(snap.handoffs_dir))
    ras = snap.recipient_approval_summary
    return {
        "ts": snap.ts,
        "repo": {
            "root": snap.repo.root,
            "branch": snap.repo.branch,
            "head": snap.repo.head,
            "head_subject": snap.repo.head_subject,
            "dirty": [f"{code} {path_}" for code, path_ in snap.repo.dirty],
            "preexisting_dirty_preserved": snap.repo.preexisting_dirty_present,
        },
        "workflows": _workflow_status(snap),
        "batch32": {
            "sourced": bool(snap.sourcing.get("present")),
            "sourced_count": snap.sourcing.get("total", 0),
            "approval_packet_present": bool(snap.approval.get("present")),
            "approve": snap.approval.get("approve", 0),
            "maybe": snap.approval.get("maybe", 0),
            "reject": snap.approval.get("reject", 0),
            "recipient_review_present": bool(snap.recipient_review.get("present")),
            "verified_top3_count": len(snap.verified_recipients),
            "charles_top3_approval_recorded": bool(ras.get("recorded")),
            "charles_top3_approved_count": ras.get("approved", 0),
            "charles_top3_pending_count": ras.get("pending", 0),
            "vssl_customer_experience_flag": any(
                r.get("company") == "Trailpoint" and r.get("customer_experience_oriented")
                for r in snap.verified_recipients
            ),
        },
        "auth_presence": {
            "openai_api_key_present": snap.openai_present,
            "gmail_token_present": snap.gmail_token_present,
        },
        "readiness": {
            "verdict": snap.gate.verdict,
            "ready": snap.gate.ready,
            "blockers": list(snap.gate.blockers),
            "failed_gates": [g.name for g in snap.gate.failed],
        },
        "next_action": snap.next_action,
        "latest_reports": reports,
        "latest_handoffs": handoffs,
    }


def render_ledger_md(entry: Dict[str, object]) -> str:
    batch = entry["batch32"]
    auth = entry["auth_presence"]
    readiness = entry["readiness"]
    workflows = entry["workflows"]
    repo = entry["repo"]
    lines = [
        f"# MOTIONX workflow ledger - {entry['ts']}",
        "",
        "> DRAFT_ONLY evidence ledger. Reads state and writes this report/JSONL outside "
        "the repo. No Gmail, OpenAI, CRM, draft, send, or schedule operation occurs.",
        "",
        "## Repo",
        f"- Path: `{repo['root']}`",
        f"- Branch: `{repo['branch']}`",
        f"- HEAD: `{repo['head']}` - {repo['head_subject']}",
        f"- Dirty files: {', '.join(f'`{d}`' for d in repo['dirty']) if repo['dirty'] else 'none'}",
        "",
        "## Workflow status",
    ]
    for name in ("visual_cold_open", "agentic_ops"):
        wf = workflows[name]
        lines.append(
            f"- {name}: built={'yes' if wf['built'] else 'no'}, "
            f"merged={'yes' if wf['merged'] else 'no'}, "
            f"tested={'yes' if wf['tested'] else 'no'} (`{wf['evidence']}`)"
        )
    lines += [
        "",
        "## Batch32",
        f"- Sourced: {'yes' if batch['sourced'] else 'no'} ({batch['sourced_count']} rows)",
        f"- Approval packet: {'yes' if batch['approval_packet_present'] else 'no'} "
        f"(APPROVE {batch['approve']} / MAYBE {batch['maybe']} / REJECT {batch['reject']})",
        f"- Top-3 recipient review file exists: "
        f"{'yes' if batch['recipient_review_present'] else 'no'}",
        f"- Charles top-3 approval recorded: "
        f"{'yes' if batch['charles_top3_approval_recorded'] else 'no'} "
        f"({batch['charles_top3_approved_count']}/"
        f"{batch['verified_top3_count']} approved)",
        f"- Trailpoint Customer-Experience technical-sample flag: "
        f"{'yes' if batch['vssl_customer_experience_flag'] else 'no'}",
        "",
        "## Readiness",
        f"- OPENAI_API_KEY present: {'yes' if auth['openai_api_key_present'] else 'no'}",
        f"- Gmail OAuth token present: {'yes' if auth['gmail_token_present'] else 'no'}",
        f"- Verdict: `{readiness['verdict']}`",
        f"- Blockers: "
        f"{', '.join(f'`{b}`' for b in readiness['blockers']) if readiness['blockers'] else 'none'}",
        f"- Failed gates: "
        f"{', '.join(f'`{g}`' for g in readiness['failed_gates']) if readiness['failed_gates'] else 'none'}",
        "",
        "## Next action",
        f"- {entry['next_action']}",
        "",
        "## Latest reports",
    ]
    reports = entry["latest_reports"]
    lines += [f"- `{r['path']}`" for r in reports[:8]] if reports else ["- (none)"]
    lines += ["", "## Latest handoffs"]
    handoffs = entry["latest_handoffs"]
    lines += [f"- `{h['path']}`" for h in handoffs[:8]] if handoffs else ["- (none)"]
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_ledger(snap: Snapshot) -> Dict[str, str]:
    entry = build_ledger_entry(snap)
    jsonl_path = os.path.join(snap.crm_dir, "ledger", paths.WORKFLOW_LEDGER_BASENAME)
    report_path = os.path.join(snap.reports_dir, f"motionx_workflow_ledger_{snap.ts}.md")
    paths.assert_outside_repo(jsonl_path, snap.repo.root)
    paths.ensure_dir(os.path.dirname(jsonl_path))
    line = json.dumps(entry, sort_keys=True)
    scanner.assert_report_safe(line)
    with open(jsonl_path, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    report_text = render_ledger_md(entry)
    render.write_report(report_text, report_path, snap.repo.root)
    return {"jsonl": jsonl_path, "report": report_path}


def _bullets(items: List[str]) -> List[str]:
    return [f"- {item}" for item in items]


def render_context_pack_md(snap: Snapshot) -> str:
    reports = _file_entries(snap.reports_dir, collectors.list_reports(snap.reports_dir))
    handoffs = _file_entries(snap.handoffs_dir, collectors.list_handoffs(snap.handoffs_dir))
    ras = snap.recipient_approval_summary
    dirty = [f"{code} {path_}" for code, path_ in snap.repo.dirty]
    lines = [
        f"# MOTIONX Codex context pack - {snap.ts}",
        "",
        "Use this to start a future bounded Codex session. It contains no secrets and "
        "does not authorize Gmail/OpenAI/CRM writes.",
        "",
        "## Current repo",
        f"- Root: `{snap.repo.root}`",
        f"- Branch: `{snap.repo.branch}`",
        f"- HEAD: `{snap.repo.head}` - {snap.repo.head_subject}",
        f"- Dirty files: {', '.join(f'`{d}`' for d in dirty) if dirty else 'none'}",
        "",
        "## Available commands",
    ]
    lines += [f"- `{cmd}`" for cmd in AVAILABLE_COMMANDS]
    lines += [
        "",
        "## Current blockers",
    ]
    if snap.gate.blockers:
        lines += [f"- `{b}`" for b in snap.gate.blockers]
    else:
        lines.append("- No credential blocker tokens currently emitted.")
    other_failed = [g.name for g in snap.gate.failed if not g.blocker]
    if other_failed:
        lines.append("- Other failed readiness gates: " + ", ".join(f"`{g}`" for g in other_failed))
    lines += [
        "",
        "## Batch32 approval state",
        f"- Recipient review file present: {'yes' if snap.recipient_review.get('present') else 'no'}",
        f"- Charles top-3 approval recorded: {'yes' if ras.get('recorded') else 'no'} "
        f"({ras.get('approved', 0)}/{ras.get('verified', 0)} approved)",
        "- Trailpoint remains Customer-Experience oriented and technical-sample-only.",
        "",
        "## Latest report paths",
    ]
    lines += [f"- `{r['path']}`" for r in reports[:8]] if reports else ["- (none)"]
    lines += ["", "## Latest handoff paths"]
    lines += [f"- `{h['path']}`" for h in handoffs[:8]] if handoffs else ["- (none)"]
    lines += [
        "",
        "## What Codex may do",
    ]
    lines += _bullets(CODEX_MAY_DO)
    lines += [
        "",
        "## What Codex must not do",
    ]
    lines += _bullets(CODEX_MUST_NOT)
    lines += [
        "",
        "## Next recommended task",
        f"- {snap.next_action}",
        "",
        "## One-line rerun commands",
        "- `python3 outreach/agentic_ops/run.py status`",
        "- `python3 outreach/agentic_ops/run.py vco-readiness`",
        "- `python3 outreach/agentic_ops/run.py batch32-status`",
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_context_pack(snap: Snapshot) -> str:
    text = render_context_pack_md(snap)
    path = os.path.join(snap.handoffs_dir, f"{paths.CONTEXT_PACK_PREFIX}{snap.ts}.md")
    return render.write_handoff(text, path, snap.repo.root)
