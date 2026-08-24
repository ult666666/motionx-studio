# -*- coding: utf-8 -*-
"""Engine layer: readiness gate, aggregated snapshot, next-action logic.

Builds on `collectors` (raw reads). Produces the derived facts the reports and
handoffs render. No mutation, no Gmail/OpenAI calls, no secret values.

Pure stdlib.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import paths
import collectors
import scanner


# ── Readiness gate ──────────────────────────────────────────────────────────────
@dataclass
class Gate:
    name: str
    ok: bool
    detail: str
    blocker: Optional[str] = None   # exact status token when this failed gate maps to one


@dataclass
class ReadinessReport:
    gates: List[Gate] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return all(g.ok for g in self.gates)

    @property
    def blockers(self) -> List[str]:
        return [g.blocker for g in self.gates if (not g.ok) and g.blocker]

    @property
    def failed(self) -> List[Gate]:
        return [g for g in self.gates if not g.ok]

    @property
    def verdict(self) -> str:
        return collectors.READY_FOR_3_SAMPLE_LIVE_DRAFTS if self.ready else "BLOCKED"


def readiness_gate(
    repo: collectors.RepoState,
    openai_present: bool,
    gmail_token_present: bool,
    venv: collectors.VenvStatus,
    recipient_review: Dict[str, object],
    approvals_note: Dict[str, object],
) -> ReadinessReport:
    """Compute the no-write vco-readiness gate. READY only if EVERY gate passes."""
    r = ReadinessReport()

    r.gates.append(Gate(
        "repo_at_or_after_baseline", repo.at_or_after_baseline,
        f"HEAD {repo.head} {'is' if repo.at_or_after_baseline else 'is NOT'} at or "
        f"after baseline {paths.BASELINE_COMMIT}",
    ))

    r.gates.append(Gate(
        "agentic_ops_merged", repo.at_or_after_agentic_ops,
        f"HEAD {repo.head} {'contains' if repo.at_or_after_agentic_ops else 'does NOT contain'} "
        f"agentic-ops baseline {paths.AGENTIC_OPS_COMMIT}",
    ))

    r.gates.append(Gate(
        "venv_present", venv.exists,
        f"out-of-repo venv {'present' if venv.exists else 'MISSING'} at {venv.venv_dir}",
    ))

    if venv.checked:
        missing = venv.missing_packages
        r.gates.append(Gate(
            "readiness_packages_installed", not missing,
            "all readiness packages installed" if not missing
            else f"missing readiness packages: {', '.join(missing)}",
        ))
    else:
        # Could not query pip (e.g. venv missing) — surface as not-verified, non-fatal
        # only if the venv itself is present; otherwise the venv gate already failed.
        r.gates.append(Gate(
            "readiness_packages_installed", venv.exists,
            "package versions not queried (pip unavailable); "
            f"expected: {', '.join(paths.READINESS_PACKAGES)}",
        ))

    r.gates.append(Gate(
        "openai_api_key_present", openai_present,
        "OPENAI_API_KEY present in CLI environment" if openai_present
        else "OPENAI_API_KEY not set in CLI environment",
        blocker=None if openai_present else collectors.BLOCKED_ON_GPT_IMAGE_2_ACCESS,
    ))

    r.gates.append(Gate(
        "gmail_token_present", gmail_token_present,
        f"Gmail OAuth token file present at {paths.GMAIL_TOKEN_PATH}" if gmail_token_present
        else f"Gmail OAuth token file absent ({paths.GMAIL_TOKEN_PATH})",
        blocker=None if gmail_token_present else collectors.BLOCKED_ON_GMAIL_DRAFT_ACCESS,
    ))

    recips = recipient_review.get("recipients", []) if recipient_review else []
    verified = [x for x in recips if x.get("has_verified_email")]
    r.gates.append(Gate(
        "recipient_review_present", bool(recipient_review.get("present")) and len(verified) >= 1,
        f"{len(verified)} verified recipient(s) in review CSV" if recipient_review.get("present")
        else "recipient review CSV not found",
    ))

    approval_summary = collectors.recipient_approval_summary(recips, approvals_note)
    r.gates.append(Gate(
        "top3_recipient_approval_recorded", approval_summary["recorded"],
        (f"{approval_summary['approved']}/{approval_summary['verified']} verified top-3 "
         "recipient approval(s) recorded")
        if approval_summary["verified"] else
        "no verified top-3 recipients available for approval matching",
    ))

    # Confirm no Gmail write path is invoked. Agentic-ops performs ZERO Gmail
    # operations; we assert the invariant against a sentinel to prove the guard holds.
    no_write_ok = True
    try:
        scanner.assert_not_send("drafts.send")  # this MUST raise
        no_write_ok = False  # pragma: no cover - would mean the guard is broken
    except scanner.SendForbiddenError:
        no_write_ok = True
    r.gates.append(Gate(
        "no_gmail_write_path", no_write_ok,
        "DRAFT_ONLY guard intact; agentic-ops invokes no Gmail send/draft path",
    ))

    return r


# ── Aggregated snapshot ─────────────────────────────────────────────────────────
@dataclass
class Snapshot:
    ts: str
    repo: collectors.RepoState
    openai_present: bool
    gmail_token_present: bool
    venv: collectors.VenvStatus
    reports: List
    latest_readiness: Optional[Dict[str, str]]
    batch32_inputs: Dict[str, Optional[str]]
    sourcing: Dict[str, object]
    approval: Dict[str, object]
    recipient_review: Dict[str, object]
    approvals_note: Dict[str, object]
    gate: ReadinessReport
    crm_dir: str
    reports_dir: str
    handoffs_dir: str

    @property
    def next_action(self) -> str:
        return next_action(self)

    @property
    def verified_recipients(self) -> List[Dict[str, object]]:
        return [r for r in self.recipient_review.get("recipients", []) if r.get("has_verified_email")]

    @property
    def recipient_approval_summary(self) -> Dict[str, object]:
        return collectors.recipient_approval_summary(
            self.recipient_review.get("recipients", []), self.approvals_note
        )


def build_snapshot(
    *,
    repo_root: Optional[str] = None,
    crm_dir: str = paths.CRM_DIR,
    reports_dir: Optional[str] = None,
    handoffs_dir: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    gmail_token_path: Optional[str] = None,
    venv_dir: str = paths.VENV_DIR,
    run_pip: bool = True,
    now: Optional[datetime] = None,
) -> Snapshot:
    reports_dir = reports_dir or os.path.join(crm_dir, "reports")
    handoffs_dir = handoffs_dir or os.path.join(crm_dir, "handoffs")
    gmail_token_path = gmail_token_path or os.path.join(crm_dir, "gmail_token.json")

    repo = collectors.collect_repo_state(repo_root)
    openai_present = collectors.openai_key_present(env)
    tok_present = collectors.gmail_token_present(gmail_token_path)
    venv = collectors.venv_status(venv_dir, run_pip=run_pip)
    reports = collectors.list_reports(reports_dir)
    latest = collectors.latest_readiness_report(reports_dir)
    inputs = collectors.find_batch32_inputs(reports_dir)
    sourcing = collectors.parse_sourcing_csv(inputs["sourcing_csv"])
    approval = collectors.parse_approval_packet(inputs["approval_packet"])
    recipient_review = collectors.parse_recipient_review(inputs["recipient_review"])
    approvals_note = collectors.read_charles_approvals(
        os.path.join(crm_dir, os.path.basename(paths.APPROVALS_NOTE_PATH)),
        os.path.join(crm_dir, os.path.basename(paths.APPROVALS_DIR)),
    )
    gate = readiness_gate(repo, openai_present, tok_present, venv, recipient_review, approvals_note)

    return Snapshot(
        ts=paths.timestamp(now), repo=repo, openai_present=openai_present,
        gmail_token_present=tok_present, venv=venv, reports=reports,
        latest_readiness=latest, batch32_inputs=inputs, sourcing=sourcing,
        approval=approval, recipient_review=recipient_review, approvals_note=approvals_note,
        gate=gate, crm_dir=crm_dir, reports_dir=reports_dir, handoffs_dir=handoffs_dir,
    )


def next_action(snap: Snapshot) -> str:
    """The single highest-value next action, given current state."""
    if not snap.repo.at_or_after_baseline:
        return (f"Repo HEAD is not at/after baseline {paths.BASELINE_COMMIT}; "
                f"check out the visual-cold-open baseline before any readiness work.")
    if not snap.venv.exists:
        return ("Recreate the out-of-repo readiness venv and reinstall openai + "
                "google-api-python-client + google-auth + google-auth-oauthlib.")
    # Key off the whole gate, not just the credential blockers: a non-credential gate
    # (recipient CSV / packages) can fail with no blocker token, and that is still BLOCKED.
    if not snap.gate.ready:
        blockers = snap.gate.blockers
        if blockers:
            approval_tail = (
                " Top-3 recipient approval is recorded."
                if snap.recipient_approval_summary.get("recorded")
                else " Top-3 recipient approval is still pending."
            )
            return ("Provision live credentials, then re-run vco-readiness. Blockers: "
                    + ", ".join(blockers)
                    + ". Use the Codex 'live-setup' handoff (charles provides OPENAI_API_KEY "
                    "into the CLI env + places gmail_token.json)."
                    + approval_tail)
        failed = ", ".join(g.name for g in snap.gate.failed)
        return (f"Readiness is BLOCKED on non-credential gate(s): {failed}. Resolve them "
                "(e.g. restore the batch32 recipient-review CSV or reinstall the readiness "
                "packages) and re-run vco-readiness before any live drafts.")
    # Ready path
    pending = [r for r in snap.verified_recipients if r.get("pending_charles_approval")]
    if pending:
        return ("Readiness gates pass. Get Charles's explicit approval for the top-3 "
                "recipients (still REVIEW_ONLY_PENDING_CHARLES_APPROVAL), then use the "
                "Codex 'three-sample-live-drafts' handoff to create ≤3 Gmail DRAFTS "
                "(draft-only, never send).")
    return ("Readiness gates pass. Use the Codex 'three-sample-live-drafts' handoff to "
            "create ≤3 Gmail DRAFTS (draft-only, never send).")
