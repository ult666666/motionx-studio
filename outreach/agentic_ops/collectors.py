# -*- coding: utf-8 -*-
"""Read-only collectors: repo state, auth/venv readiness, batch32 parsing.

Everything here READS. Nothing mutates git, CRM, Gmail, or secrets. Secret *values*
are never returned — only presence booleans. Functions accept overridable
directories/paths/env so tests can drive them with fixtures.

Pure stdlib.
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import paths

# ── Status tokens (mirror outreach/visual_cold_open/config.py:STATUS; a test in
# test_agentic_ops.py asserts these stay identical to the source of truth) ───────
BLOCKED_ON_GPT_IMAGE_2_ACCESS = "BLOCKED_ON_GPT_IMAGE_2_ACCESS"
BLOCKED_ON_GMAIL_DRAFT_ACCESS = "BLOCKED_ON_GMAIL_DRAFT_ACCESS"
# The task-defined ready verdict (emitted only when every readiness gate passes).
READY_FOR_3_SAMPLE_LIVE_DRAFTS = "READY_FOR_3_SAMPLE_LIVE_DRAFTS"


# ── Repo state ──────────────────────────────────────────────────────────────────
@dataclass
class RepoState:
    root: str
    branch: str
    head: str
    head_subject: str
    recent: List[str] = field(default_factory=list)
    dirty: List[Tuple[str, str]] = field(default_factory=list)   # (code, path)
    at_or_after_baseline: bool = False
    at_or_after_agentic_ops: bool = False
    baseline: str = paths.BASELINE_COMMIT

    @property
    def preexisting_dirty_present(self) -> bool:
        return any(p == paths.PREEXISTING_DIRTY for _, p in self.dirty)

    @property
    def other_dirty(self) -> List[Tuple[str, str]]:
        return [(c, p) for c, p in self.dirty if p != paths.PREEXISTING_DIRTY]


def _git(root: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", root, *args], capture_output=True, text=True, timeout=20
    )


def collect_repo_state(root: Optional[str] = None) -> RepoState:
    root = root or paths.repo_root()
    branch = _git(root, "branch", "--show-current").stdout.strip()
    head = _git(root, "rev-parse", "--short", "HEAD").stdout.strip()
    head_subject = _git(root, "log", "-1", "--pretty=%s").stdout.strip()
    recent = [
        ln for ln in _git(root, "log", "--oneline", "-5").stdout.splitlines() if ln.strip()
    ]
    dirty: List[Tuple[str, str]] = []
    for ln in _git(root, "status", "--porcelain").stdout.splitlines():
        if not ln.strip():
            continue
        code, _, path = ln[:2], ln[2], ln[3:]
        dirty.append((code.strip() or ln[:2], path.strip()))
    anc = _git(root, "merge-base", "--is-ancestor", paths.BASELINE_COMMIT, "HEAD")
    agentic_anc = _git(root, "merge-base", "--is-ancestor", paths.AGENTIC_OPS_COMMIT, "HEAD")
    return RepoState(
        root=root, branch=branch, head=head, head_subject=head_subject,
        recent=recent, dirty=dirty, at_or_after_baseline=(anc.returncode == 0),
        at_or_after_agentic_ops=(agentic_anc.returncode == 0),
    )


# ── Auth / dependency presence (presence only; never reads secret contents) ─────
def openai_key_present(env: Optional[Dict[str, str]] = None) -> bool:
    env = os.environ if env is None else env
    return bool((env.get("OPENAI_API_KEY") or "").strip())


def gmail_token_present(token_path: str = paths.GMAIL_TOKEN_PATH) -> bool:
    # Existence check ONLY — the file is never opened or read.
    return os.path.isfile(token_path)


@dataclass
class VenvStatus:
    venv_dir: str
    exists: bool
    python_path: str = ""
    packages: Dict[str, Optional[str]] = field(default_factory=dict)  # name -> version|None
    checked: bool = False   # whether we could actually query pip

    @property
    def missing_packages(self) -> List[str]:
        return [n for n, v in self.packages.items() if not v]


def venv_status(
    venv_dir: str = paths.VENV_DIR,
    required: Tuple[str, ...] = paths.READINESS_PACKAGES,
    run_pip: bool = True,
) -> VenvStatus:
    """Report venv existence and installed versions of the readiness packages.

    Uses the venv's own python (`-m pip list`). Read-only. Never installs anything.
    """
    py = os.path.join(venv_dir, "bin", "python")
    exists = os.path.isdir(venv_dir) and os.path.isfile(py)
    st = VenvStatus(venv_dir=venv_dir, exists=exists,
                    python_path=py if exists else "",
                    packages={n: None for n in required})
    if not exists or not run_pip:
        return st
    try:
        out = subprocess.run(
            [py, "-m", "pip", "list", "--format=freeze"],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode == 0:
            installed = {}
            for ln in out.stdout.splitlines():
                if "==" in ln:
                    name, ver = ln.split("==", 1)
                    installed[name.strip().lower()] = ver.strip()
            for n in required:
                st.packages[n] = installed.get(n.lower())
            st.checked = True
    except (OSError, subprocess.SubprocessError):
        pass
    return st


# ── Reports listing + latest readiness parse ────────────────────────────────────
def list_reports(reports_dir: str = paths.REPORTS_DIR, limit: int = 12) -> List[Tuple[str, float]]:
    return list_files(reports_dir, limit=limit)


def list_handoffs(handoffs_dir: str = paths.HANDOFFS_DIR, limit: int = 12) -> List[Tuple[str, float]]:
    return list_files(handoffs_dir, limit=limit)


def list_files(directory: str, limit: int = 12) -> List[Tuple[str, float]]:
    if not os.path.isdir(directory):
        return []
    entries = []
    for name in os.listdir(directory):
        full = os.path.join(directory, name)
        try:
            entries.append((name, os.path.getmtime(full)))
        except OSError:
            continue
    entries.sort(key=lambda t: t[1], reverse=True)
    return entries[:limit]


def latest_readiness_report(reports_dir: str = paths.REPORTS_DIR) -> Optional[Dict[str, str]]:
    """Find the newest visual_cold_open_*.md readiness report and extract a verdict."""
    if not os.path.isdir(reports_dir):
        return None
    candidates = [
        n for n in os.listdir(reports_dir)
        if n.startswith(paths.VCO_READINESS_PREFIX) and n.endswith(".md")
    ]
    if not candidates:
        return None
    candidates.sort(
        key=lambda n: os.path.getmtime(os.path.join(reports_dir, n)), reverse=True
    )
    name = candidates[0]
    full = os.path.join(reports_dir, name)
    verdict = "UNKNOWN"
    try:
        with open(full, "r", encoding="utf-8") as fh:
            text = fh.read()
        tokens = re.findall(
            r"\b(READY_FOR_[A-Z0-9_]+|BLOCKED_ON_[A-Z0-9_]+|DRY_RUN_OK|PREFLIGHT_OK|"
            r"SAMPLE_PREVIEW_WRITTEN|VERIFIED_DRAFT_ONLY)\b",
            text,
        )
        if tokens:
            # Prefer a blocker if present, else the first status token seen.
            blockers = [t for t in tokens if t.startswith("BLOCKED_ON_")]
            verdict = blockers[0] if blockers else tokens[0]
    except OSError:
        pass
    return {"name": name, "path": full, "verdict": verdict}


# ── batch32 parsing (read-only) ─────────────────────────────────────────────────
def _newest_matching(reports_dir: str, prefix: str, suffix: str = "") -> Optional[str]:
    if not os.path.isdir(reports_dir):
        return None
    matches = [
        n for n in os.listdir(reports_dir)
        if n.startswith(prefix) and (not suffix or n.endswith(suffix))
    ]
    if not matches:
        return None
    matches.sort(key=lambda n: os.path.getmtime(os.path.join(reports_dir, n)), reverse=True)
    return os.path.join(reports_dir, matches[0])


def find_batch32_inputs(reports_dir: str = paths.REPORTS_DIR) -> Dict[str, Optional[str]]:
    return {
        "sourcing_csv": _newest_matching(reports_dir, paths.BATCH32_SOURCING_PREFIX, ".csv"),
        "approval_packet": _newest_matching(reports_dir, paths.BATCH32_APPROVAL_PREFIX, ".md"),
        "recipient_review": _newest_matching(reports_dir, paths.BATCH32_RECIPIENT_PREFIX, ".csv"),
    }


def parse_sourcing_csv(path: Optional[str]) -> Dict[str, object]:
    if not path or not os.path.isfile(path):
        return {"present": False, "total": 0, "rows": []}
    with open(path, "r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {"present": True, "total": len(rows), "rows": rows, "path": path}


def parse_approval_packet(path: Optional[str]) -> Dict[str, object]:
    """Parse APPROVE/MAYBE/REJECT counts from the packet's Decision Summary, and
    cross-check against the ranked markdown table."""
    if not path or not os.path.isfile(path):
        return {"present": False, "approve": 0, "maybe": 0, "reject": 0, "total": 0}
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    summary = {"APPROVE": 0, "MAYBE": 0, "REJECT": 0}
    for m in re.finditer(r"[-*]\s*`?(APPROVE|MAYBE|REJECT)`?\s*:\s*(\d+)", text):
        summary[m.group(1)] = int(m.group(2))
    # Cross-check by counting ranked table rows: | <rank> | <DECISION> | ...
    table_counts = {"APPROVE": 0, "MAYBE": 0, "REJECT": 0}
    for m in re.finditer(r"^\|\s*\d+\s*\|\s*(APPROVE|MAYBE|REJECT)\s*\|", text, re.MULTILINE):
        table_counts[m.group(1)] += 1
    summary_total = sum(summary.values())
    table_total = sum(table_counts.values())
    return {
        "present": True,
        "approve": summary["APPROVE"],
        "maybe": summary["MAYBE"],
        "reject": summary["REJECT"],
        "total": summary_total,
        "table_counts": table_counts,
        "table_total": table_total,
        "counts_consistent": (summary_total == table_total and summary == table_counts),
        "path": path,
    }


# Local parts that read as customer-service mailboxes rather than marketing/press.
_CX_LOCAL_PARTS = frozenset({"support", "help", "care", "service", "customercare"})


def classify_recipient(row: Dict[str, str]) -> Dict[str, object]:
    """Normalize one recipient-review row and flag customer-experience mailboxes."""
    email = (row.get("recipient_email") or "").strip()
    fit = (row.get("recipient_fit") or "").strip()
    review_status = (row.get("recipient_review_status") or "").strip()
    decision = (row.get("decision") or "").strip().upper()
    local = email.split("@", 1)[0].lower() if "@" in email else ""
    cx_by_fit = "customer_experience" in fit.lower() or "customer experience" in fit.lower()
    cx_by_local = local in _CX_LOCAL_PARTS
    return {
        "company": (row.get("company") or "").strip(),
        "domain": (row.get("domain") or "").strip(),
        "email": email,
        "recipient_fit": fit,
        "decision": decision,
        "review_status": review_status,
        "has_verified_email": bool(email and "@" in email),
        "customer_experience_oriented": bool(cx_by_fit or cx_by_local),
        "pending_charles_approval": "PENDING" in review_status.upper()
        or "REVIEW_ONLY" in review_status.upper(),
    }


def parse_recipient_review(path: Optional[str]) -> Dict[str, object]:
    if not path or not os.path.isfile(path):
        return {"present": False, "rows": [], "recipients": []}
    with open(path, "r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    recipients = [classify_recipient(r) for r in rows]
    return {"present": True, "rows": rows, "recipients": recipients, "path": path}


def _latest_approval_artifact(approvals_dir: str) -> Optional[str]:
    return _newest_matching(
        approvals_dir, paths.BATCH32_TOP3_APPROVAL_PREFIX, ".md"
    )


def _tokens_from_approval_text(text: str) -> set:
    tokens = set()
    for email in re.findall(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b", text or ""):
        email_l = email.lower()
        tokens.add(email_l)
        if "@" in email_l:
            tokens.add(email_l.split("@", 1)[1])
    for line in (text or "").splitlines():
        raw = line.strip().lstrip("-*").strip()
        if not raw or raw.startswith("#"):
            continue
        if "approved for 3-sample DRAFT_ONLY technical test" not in raw:
            continue
        # Accept either em dash or ASCII hyphen separators; the artifact writer uses
        # ASCII, but older operator notes may use either form.
        first = re.split(r"\s+[—-]\s+", raw, maxsplit=1)[0].strip()
        if first:
            tokens.add(first.lower())
    return tokens


def read_charles_approvals(
    path: str = paths.APPROVALS_NOTE_PATH,
    approvals_dir: str = paths.APPROVALS_DIR,
) -> Dict[str, object]:
    """Read optional operator records of Charles's per-recipient approvals.

    Supported inputs:
      * charles_recipient_approvals.txt: one company/domain/email token per line.
      * approvals/batch32_top3_recipient_approval_*.md: durable approval artifact.

    Absent files mean no approvals recorded (safe default). Only operator-authored
    text is read; no CRM/Gmail/secrets files are opened here.
    """
    tokens = set()
    sources: List[str] = []
    note_present = False

    if os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        tokens.add(line.lower())
            sources.append(path)
            note_present = True
        except OSError:
            pass

    artifact = _latest_approval_artifact(approvals_dir)
    if artifact and os.path.isfile(artifact):
        try:
            with open(artifact, "r", encoding="utf-8") as fh:
                artifact_text = fh.read()
            tokens.update(_tokens_from_approval_text(artifact_text))
            sources.append(artifact)
        except OSError:
            artifact = None

    return {
        "present": bool(sources),
        "tokens": tokens,
        "paths": sources,
        "path": sources[0] if sources else "",
        "note_present": note_present,
        "artifact_path": artifact or "",
    }


def recipient_charles_approved(rec: Dict[str, object], approvals: Dict[str, object]) -> bool:
    if not approvals.get("present"):
        return False
    toks = approvals.get("tokens", set())
    for key in ("company", "domain", "email"):
        val = str(rec.get(key, "")).lower()
        if val and val in toks:
            return True
    return False


def recipient_approval_summary(
    recipients: List[Dict[str, object]], approvals: Dict[str, object]
) -> Dict[str, object]:
    verified = [r for r in recipients if r.get("has_verified_email")]
    approved = [r for r in verified if recipient_charles_approved(r, approvals)]
    pending = [r for r in verified if not recipient_charles_approved(r, approvals)]
    return {
        "verified": len(verified),
        "approved": len(approved),
        "pending": len(pending),
        "recorded": bool(verified) and not pending,
        "pending_companies": [str(r.get("company", "")) for r in pending],
        "approved_companies": [str(r.get("company", "")) for r in approved],
    }
