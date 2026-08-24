# -*- coding: utf-8 -*-
"""Shared path bootstrap + fixture writers for the agentic-ops tests.

Pure stdlib. Puts outreach/agentic_ops (+ visual_cold_open, outreach) on sys.path so
the flat modules import (mirrors outreach/tests/_vco_bootstrap.py).
"""
import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTREACH_DIR = os.path.dirname(_TESTS_DIR)
_OPS_DIR = os.path.join(_OUTREACH_DIR, "agentic_ops")
_VCO_DIR = os.path.join(_OUTREACH_DIR, "visual_cold_open")
for _p in (_OPS_DIR, _VCO_DIR, _OUTREACH_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

REPO_ROOT = os.path.dirname(_OUTREACH_DIR)


# ── Fixtures mirroring the real batch32 input shapes ────────────────────────────
_SOURCING_HEADER = (
    "candidate_id,company,domain,official_website,category,verified_observation,"
    "why_motionx_relevant,possible_angle,public_contact_evidence,source_urls,"
    "risk_uncertainty_flags,duplicate_check_result,status_recommendation\n"
)


def _sourcing_row(cid, company, domain):
    return (f"{cid},{company},{domain},https://{domain}/,gear,obs,why,angle,contact,"
            f"https://{domain}/,none,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n")


def write_sourcing_csv(reports_dir, n=3, stamp="2026-01-01_0000"):
    path = os.path.join(reports_dir, f"batch32_sourcing_candidates_{stamp}.csv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_SOURCING_HEADER)
        for i in range(n):
            fh.write(_sourcing_row(f"B32C{i:03d}", f"Company{i}", f"company{i}.com"))
    return path


def write_approval_packet(reports_dir, approve=2, maybe=1, reject=0, stamp="2026-01-01_0000"):
    path = os.path.join(reports_dir, f"batch32_candidate_approval_packet_{stamp}.md")
    rows = []
    rank = 1
    for _ in range(approve):
        rows.append(f"| {rank} | APPROVE | Co{rank} | `co{rank}.com` | cat | High | why | vco | none |")
        rank += 1
    for _ in range(maybe):
        rows.append(f"| {rank} | MAYBE | Co{rank} | `co{rank}.com` | cat | High | why | vco | none |")
        rank += 1
    for _ in range(reject):
        rows.append(f"| {rank} | REJECT | Co{rank} | `co{rank}.com` | cat | High | why | vco | none |")
        rank += 1
    body = (
        "# Batch32 Candidate Approval Packet\n\n"
        "## Decision Summary\n"
        f"- `APPROVE`: {approve}\n- `MAYBE`: {maybe}\n- `REJECT`: {reject}\n\n"
        "## Ranked Candidates\n"
        "| Rank | Decision | Company | Domain | Category | Contact | Why | Visual | Risk |\n"
        "|---:|---|---|---|---|---|---|---|---|\n"
        + "\n".join(rows) + "\n"
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    return path


_RECIP_HEADER = (
    "rank,decision,candidate_id,company,domain,official_website,category,recipient_email,"
    "recipient_source_url,recipient_source_context,recipient_fit,recipient_review_status\n"
)

# Mirrors the real top-3: Northwind (marketing/press), Trailpoint (customer-experience), Fieldmark.
RECIPIENTS = [
    ("1", "APPROVE", "B32C010", "Northwind Gear", "northwindgear.example",
     "marketing@northwindgear.example", "marketing_press_inquiries"),
    ("2", "APPROVE", "B32C011", "Trailpoint", "trailpoint.example",
     "support@trailpoint.example", "customer_experience_only_review_recommended"),
    ("3", "APPROVE", "B32C002", "Fieldmark", "fieldmark.example",
     "info@fieldmark.example", "press_partnerships_general"),
]


def write_recipient_review(reports_dir, stamp="2026-01-01_0000"):
    path = os.path.join(reports_dir, f"batch32_top3_recipient_review_{stamp}.csv")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_RECIP_HEADER)
        for rank, dec, cid, company, domain, email, fit in RECIPIENTS:
            fh.write(f"{rank},{dec},{cid},{company},{domain},https://{domain}/,cat,{email},"
                     f"https://{domain}/contact,ctx,{fit},REVIEW_ONLY_PENDING_CHARLES_APPROVAL\n")
    return path


def seed_crm(crm_dir, n_sourced=3, approve=2, maybe=1, reject=0):
    """Create a temp CRM dir with reports/ populated by the batch32 fixtures."""
    reports = os.path.join(crm_dir, "reports")
    os.makedirs(reports, exist_ok=True)
    write_sourcing_csv(reports, n=n_sourced)
    write_approval_packet(reports, approve=approve, maybe=maybe, reject=reject)
    write_recipient_review(reports)
    return reports


def fake_venv(crm_dir):
    """Create a minimal fake venv (bin/python) so venv.exists is True without a real venv."""
    vdir = os.path.join(crm_dir, "venvs", "visual-cold-open")
    os.makedirs(os.path.join(vdir, "bin"), exist_ok=True)
    py = os.path.join(vdir, "bin", "python")
    with open(py, "w") as fh:
        fh.write("#!/bin/sh\n")
    os.chmod(py, 0o755)
    return vdir
