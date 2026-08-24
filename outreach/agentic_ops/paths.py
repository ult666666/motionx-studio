# -*- coding: utf-8 -*-
"""Centralized paths + tiny helpers for the agentic-ops layer.

Every output path resolves OUTSIDE the git repo (under ~/.motionx-outreach/).
`assert_outside_repo` is the structural guard that refuses to write a report or
handoff into the repo tree by mistake.

Pure stdlib. No secrets are ever read here.
"""
from __future__ import annotations

import os
import subprocess
from datetime import datetime

# ── Immutable facts (mirror outreach/visual_cold_open/config.py; do not drift) ──
BASELINE_COMMIT = "29f3ddf"                       # visual-cold-open merge baseline
AGENTIC_OPS_COMMIT = "b3dbfb7"                    # agentic-ops merge baseline
SENDING_MAILBOX = "charles@madebymotionx.com"
REQUIRED_IMAGE_MODEL = "gpt-image-2"

# ── Out-of-repo state root (all outputs land here) ──────────────────────────────
CRM_DIR = os.path.expanduser("~/.motionx-outreach")
REPORTS_DIR = os.path.join(CRM_DIR, "reports")
HANDOFFS_DIR = os.path.join(CRM_DIR, "handoffs")
LEDGER_DIR = os.path.join(CRM_DIR, "ledger")
APPROVALS_DIR = os.path.join(CRM_DIR, "approvals")
VENV_DIR = os.path.join(CRM_DIR, "venvs", "visual-cold-open")
GMAIL_TOKEN_PATH = os.path.join(CRM_DIR, "gmail_token.json")
GMAIL_CREDENTIALS_PATH = os.path.join(CRM_DIR, "gmail_credentials.json")
SECRETS_ENV_PATH = os.path.join(CRM_DIR, "secrets.env")

# Optional operator note recording Charles's per-recipient approvals (see runbook).
APPROVALS_NOTE_PATH = os.path.join(CRM_DIR, "charles_recipient_approvals.txt")

# Readiness packages expected in the out-of-repo venv (names only, no versions pinned
# here — the readiness check reports whatever is installed).
READINESS_PACKAGES = (
    "openai",
    "google-api-python-client",
    "google-auth",
    "google-auth-oauthlib",
)

# The single file the outreach workstream leaves dirty and unrelated; always preserved.
PREEXISTING_DIRTY = "outreach/self-improvement.md"

# Batch32 input-file basename prefixes (newest match wins).
BATCH32_SOURCING_PREFIX = "batch32_sourcing_candidates_"
BATCH32_APPROVAL_PREFIX = "batch32_candidate_approval_packet_"
BATCH32_RECIPIENT_PREFIX = "batch32_top3_recipient_review_"
BATCH32_TOP3_APPROVAL_PREFIX = "batch32_top3_recipient_approval_"
VCO_READINESS_PREFIX = "visual_cold_open_"
CONTEXT_PACK_PREFIX = "codex_context_pack_"
WORKFLOW_LEDGER_BASENAME = "motionx_workflow_ledger.jsonl"


def _this_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def repo_root() -> str:
    """Best-effort repo root: `git rev-parse --show-toplevel`, else path arithmetic.

    Read-only. Falls back to three levels up from this file
    (<root>/outreach/agentic_ops/paths.py) if git is unavailable.
    """
    here = _this_dir()
    try:
        out = subprocess.run(
            ["git", "-C", here, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=15,
        )
        top = out.stdout.strip()
        if out.returncode == 0 and top:
            return top
    except (OSError, subprocess.SubprocessError):
        pass
    return os.path.dirname(os.path.dirname(here))


def visual_cold_open_dir(root: str | None = None) -> str:
    return os.path.join(root or repo_root(), "outreach", "visual_cold_open")


def timestamp(now: datetime | None = None) -> str:
    """Report/handoff filename stamp: YYYY-MM-DD_HHMM (matches existing reports)."""
    return (now or datetime.now()).strftime("%Y-%m-%d_%H%M")


def is_within(path: str, root: str) -> bool:
    """True if `path` is inside `root` (after normalization)."""
    path_abs = os.path.abspath(path)
    root_abs = os.path.abspath(root)
    try:
        common = os.path.commonpath([path_abs, root_abs])
    except ValueError:
        return False
    return common == root_abs


def assert_outside_repo(path: str, root: str | None = None) -> None:
    """Refuse to write into the repo tree. Structural guard for report/handoff sinks."""
    root = root or repo_root()
    if is_within(path, root):
        raise ValueError(
            f"Refusing to write {path!r}: it is inside the repo {root!r}. "
            f"Agentic-ops outputs must live OUTSIDE the repo (under {CRM_DIR})."
        )


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path
