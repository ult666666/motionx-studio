# -*- coding: utf-8 -*-
"""Safe operator approval capture for batch32 top-3 recipients.

Writes only explicit Charles approval artifacts outside the repo. This does not
authorize sending, full-batch outreach, guessed recipients, or live draft creation
before readiness passes.

Pure stdlib.
"""
from __future__ import annotations

import os
from typing import Dict, List

import paths
import scanner


BATCH32_TOP3_APPROVALS: List[Dict[str, str]] = [
    {
        "company": "Northwind Gear",
        "domain": "northwindgear.example",
        "email": "marketing@northwindgear.example",
        "scope": "approved for 3-sample DRAFT_ONLY technical test",
    },
    {
        "company": "Trailpoint",
        "domain": "trailpoint.example",
        "email": "support@trailpoint.example",
        "scope": (
            "approved for 3-sample DRAFT_ONLY technical test only; "
            "customer-experience mailbox caveat acknowledged"
        ),
    },
    {
        "company": "Fieldmark",
        "domain": "fieldmark.example",
        "email": "info@fieldmark.example",
        "scope": "approved for 3-sample DRAFT_ONLY technical test",
    },
]


def render_batch32_top3_approval(ts: str) -> str:
    lines = [
        f"# batch32 top-3 recipient approval - {ts}",
        "",
        "Charles explicitly approved these exact recipients for the technical "
        "3-sample DRAFT_ONLY test:",
        "",
    ]
    for item in BATCH32_TOP3_APPROVALS:
        lines.append(f"- {item['company']} - {item['email']} - {item['scope']}.")
    lines += [
        "",
        "This approval does NOT authorize sending.",
        "This approval does NOT authorize full batch32.",
        "This approval does NOT authorize guessing any other recipients.",
        "This approval does NOT authorize Gmail draft creation until OpenAI and Gmail "
        "credentials pass readiness.",
        "Charles remains the only person who sends.",
        "",
    ]
    return "\n".join(lines)


def render_legacy_note() -> str:
    lines = [
        "# Charles-approved top-3 batch32 recipients.",
        "# Tokens only; consumed by outreach/agentic_ops. This is outside the repo.",
        "# DRAFT_ONLY technical 3-sample test; does NOT authorize sending or full batch32.",
    ]
    for item in BATCH32_TOP3_APPROVALS:
        lines += [item["company"], item["domain"], item["email"]]
    return "\n".join(lines) + "\n"


def write_batch32_top3_approval(crm_dir: str, repo_root: str, ts: str) -> Dict[str, str]:
    approval_dir = os.path.join(crm_dir, "approvals")
    artifact = os.path.join(approval_dir, f"{paths.BATCH32_TOP3_APPROVAL_PREFIX}{ts}.md")
    note = os.path.join(crm_dir, os.path.basename(paths.APPROVALS_NOTE_PATH))
    paths.assert_outside_repo(artifact, repo_root)
    paths.assert_outside_repo(note, repo_root)

    artifact_text = render_batch32_top3_approval(ts)
    note_text = render_legacy_note()
    for text in (artifact_text, note_text):
        scanner.assert_report_safe(text)

    paths.ensure_dir(approval_dir)
    with open(artifact, "w", encoding="utf-8") as fh:
        fh.write(artifact_text)
    with open(note, "w", encoding="utf-8") as fh:
        fh.write(note_text)
    return {"artifact": artifact, "note": note}
