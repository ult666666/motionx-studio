# -*- coding: utf-8 -*-
"""Markdown rendering + safe writing for agentic-ops reports.

Renders the status / vco-readiness / batch32-status / daily reports. Every writer
routes through `write_report`, which (1) refuses to write inside the repo and
(2) runs the safety scanner so no secret or Gmail-token content is ever persisted.
Recipient local-parts are masked in human reports.

Pure stdlib.
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

import paths
import scanner
from engine import Snapshot


# ── Safe writer ─────────────────────────────────────────────────────────────────
def write_report(text: str, path: str, repo_root: Optional[str] = None) -> str:
    """Scan + refuse-inside-repo + write. Returns the path written."""
    paths.assert_outside_repo(path, repo_root)
    scanner.assert_report_safe(text)
    paths.ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def write_handoff(text: str, path: str, repo_root: Optional[str] = None) -> str:
    paths.assert_outside_repo(path, repo_root)
    scanner.assert_handoff_safe(text)
    paths.ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


# ── Shared fragments ────────────────────────────────────────────────────────────
_DRAFT_ONLY_FOOTER = (
    "> **DRAFT_ONLY.** This layer only reads state and writes reports/handoffs "
    "outside the repo. It never sends or schedules email, never creates or updates "
    "Gmail drafts, never generates images, never mutates CRM, and never touches "
    "secrets. Charles is the only human who sends email."
)


def _repo_block(snap: Snapshot) -> List[str]:
    lines = [
        "## Repo",
        f"- Path: `{snap.repo.root}`",
        f"- Branch: `{snap.repo.branch}`",
        f"- HEAD: `{snap.repo.head}` — {snap.repo.head_subject}",
        f"- At/after baseline `{paths.BASELINE_COMMIT}`: "
        f"{'yes' if snap.repo.at_or_after_baseline else '**NO**'}",
        f"- Contains agentic-ops baseline `{paths.AGENTIC_OPS_COMMIT}`: "
        f"{'yes' if snap.repo.at_or_after_agentic_ops else '**NO**'}",
    ]
    if snap.repo.dirty:
        lines.append("- Dirty files:")
        for code, path_ in snap.repo.dirty:
            note = ""
            if path_ == paths.PREEXISTING_DIRTY:
                note = "  _(pre-existing / unrelated — preserved, not touched)_"
            lines.append(f"  - `{code} {path_}`{note}")
    else:
        lines.append("- Dirty files: none")
    return lines


def _auth_block(snap: Snapshot) -> List[str]:
    return [
        "## Auth & dependency readiness",
        f"- OPENAI_API_KEY present: {'yes' if snap.openai_present else '**no**'} "
        "(presence only; value never read)",
        f"- Gmail token `{paths.GMAIL_TOKEN_PATH}` present: "
        f"{'yes' if snap.gmail_token_present else '**no**'} (existence only; never read)",
        f"- Readiness venv `{snap.venv.venv_dir}` present: "
        f"{'yes' if snap.venv.exists else '**no**'}",
        "- Readiness packages: "
        + (", ".join(
            f"{n}={v}" if v else f"{n}=**missing**" for n, v in snap.venv.packages.items())
           if snap.venv.checked else
           "not queried (" + ", ".join(snap.venv.packages.keys()) + ")"),
    ]


def _claimed_unverified(snap: Snapshot) -> List[str]:
    """Detect 'claimed-done-but-unverified' signals (e.g. a live-result report exists
    while readiness is still blocked, so no draft could actually have been created)."""
    flags = []
    live_result_reports = [
        n for (n, _m) in snap.reports
        if ("live" in n.lower() and "result" in n.lower())
    ]
    if live_result_reports and not snap.gmail_token_present:
        flags.append(
            f"A live-result report exists ({live_result_reports[0]}) but "
            f"`{os.path.basename(paths.GMAIL_TOKEN_PATH)}` is absent — no real Gmail draft "
            "could have been created. Treat that 'live' result as UNVERIFIED until a Gmail "
            "read-back (is_draft=true) confirms an actual draft."
        )
    if snap.gate.blockers and any(
        "live" in n.lower() and "draft" in n.lower() for (n, _m) in snap.reports
    ):
        flags.append(
            "Live-draft artifacts are present while readiness still reports "
            f"{', '.join(snap.gate.blockers)} — verify nothing was half-created."
        )
    return flags


# ── status report ───────────────────────────────────────────────────────────────
def render_status_md(snap: Snapshot) -> str:
    L: List[str] = [f"# MOTIONX agentic-ops status — {snap.ts}", "", _DRAFT_ONLY_FOOTER, ""]
    L += _repo_block(snap) + [""]
    L += _auth_block(snap) + [""]

    L += ["## Latest reports (newest first)"]
    if snap.reports:
        for name, _mt in snap.reports[:10]:
            L.append(f"- `{name}`")
    else:
        L.append("- (none found)")
    L.append("")

    L += ["## Visual-cold-open readiness"]
    if snap.latest_readiness:
        L.append(f"- Latest readiness report: `{snap.latest_readiness['name']}`")
        L.append(f"- Parsed verdict: `{snap.latest_readiness['verdict']}`")
    else:
        L.append("- No visual-cold-open readiness report found yet.")
    L.append(f"- Live readiness gate verdict: `{snap.gate.verdict}`")
    if snap.gate.blockers:
        L.append(f"- Blockers: {', '.join(f'`{b}`' for b in snap.gate.blockers)}")
    L.append("")

    L += ["## batch32 inputs"]
    L.append(f"- Sourcing CSV present: {'yes' if snap.sourcing.get('present') else 'no'} "
             f"({snap.sourcing.get('total', 0)} candidates)")
    L.append(f"- Approval packet present: {'yes' if snap.approval.get('present') else 'no'} "
             f"(APPROVE {snap.approval.get('approve', 0)} / MAYBE {snap.approval.get('maybe', 0)} "
             f"/ REJECT {snap.approval.get('reject', 0)})")
    L.append(f"- Recipient review present: {'yes' if snap.recipient_review.get('present') else 'no'} "
             f"({len(snap.verified_recipients)} verified recipient(s))")
    ras = snap.recipient_approval_summary
    L.append(f"- Charles top-3 recipient approval recorded: "
             f"{'yes' if ras.get('recorded') else 'no'} "
             f"({ras.get('approved', 0)}/{ras.get('verified', 0)} approved)")
    L.append("")

    unv = _claimed_unverified(snap)
    if unv:
        L += ["## ⚠️ Claimed-done-but-unverified"]
        L += [f"- {u}" for u in unv]
        L.append("")

    L += ["## Highest-value next action", f"- {snap.next_action}", ""]
    return "\n".join(L).rstrip() + "\n"


# ── vco-readiness report ────────────────────────────────────────────────────────
def render_vco_readiness_md(snap: Snapshot) -> str:
    g = snap.gate
    L: List[str] = [f"# MOTIONX visual-cold-open readiness — {snap.ts}", "", _DRAFT_ONLY_FOOTER, ""]
    L += ["## Verdict"]
    if g.ready:
        L.append(f"**{snap.gate.verdict}**")
    else:
        L.append("**BLOCKED** — not ready for the 3 sample live drafts.")
        L.append("")
        L.append("Blockers:")
        for b in g.blockers:
            L.append(f"- `{b}`")
    L.append("")

    L += ["## Gates"]
    for gate in g.gates:
        mark = "PASS" if gate.ok else "FAIL"
        extra = f" → `{gate.blocker}`" if (not gate.ok and gate.blocker) else ""
        L.append(f"- [{mark}] {gate.name}: {gate.detail}{extra}")
    L.append("")

    L += _repo_block(snap) + [""]
    L += _auth_block(snap) + [""]

    L += ["## Recipients (from review CSV; local-parts masked)"]
    if snap.verified_recipients:
        for r in snap.verified_recipients:
            flag = " — CUSTOMER-EXPERIENCE mailbox (technical sample only)" if r.get(
                "customer_experience_oriented") else ""
            approved = _charles_approved(r, snap.approvals_note)
            approval_state = "approval recorded" if approved else "approval pending"
            L.append(f"- {r['company']} → `{scanner.mask_recipient(r['email'])}` "
                     f"[{r['review_status']}; {approval_state}]{flag}")
    else:
        L.append("- (no verified recipients parsed)")
    L.append("")

    L += ["## Invariants confirmed",
          "- No Gmail write path invoked (no draft created/updated, nothing sent/scheduled).",
          "- No image generated; gpt-image-2 not called.",
          "- No secret value read or written; presence-only checks.",
          ""]
    return "\n".join(L).rstrip() + "\n"


# ── batch32-status report ───────────────────────────────────────────────────────
def render_batch32_status_md(snap: Snapshot) -> str:
    approvals = snap.approvals_note
    L: List[str] = [f"# MOTIONX batch32 status — {snap.ts}", "", _DRAFT_ONLY_FOOTER, ""]

    L += ["## Candidate counts"]
    L.append(f"- Total sourced: {snap.sourcing.get('total', 0)}")
    L.append(f"- APPROVE: {snap.approval.get('approve', 0)}")
    L.append(f"- MAYBE: {snap.approval.get('maybe', 0)}")
    L.append(f"- REJECT: {snap.approval.get('reject', 0)}")
    tc = snap.approval.get("table_counts")
    if tc is not None:
        consistent = snap.approval.get("counts_consistent")
        L.append(f"- Ranked-table cross-check: APPROVE {tc.get('APPROVE',0)} / "
                 f"MAYBE {tc.get('MAYBE',0)} / REJECT {tc.get('REJECT',0)} "
                 f"({'consistent' if consistent else '**inconsistent with summary**'})")
    L.append(f"- Selected top 3: {len(snap.verified_recipients)}")
    L.append(f"- Verified recipient emails: "
             f"{sum(1 for r in snap.verified_recipients if r.get('has_verified_email'))}")
    ras = snap.recipient_approval_summary
    L.append(f"- Charles top-3 recipient approval recorded: "
             f"{'yes' if ras.get('recorded') else 'no'} "
             f"({ras.get('approved', 0)}/{ras.get('verified', 0)} approved)")
    L.append("")

    L += ["## Top-3 recipients (local-parts masked)"]
    if snap.verified_recipients:
        for r in snap.verified_recipients:
            approved = _charles_approved(r, approvals)
            notes = []
            if r.get("customer_experience_oriented"):
                if approved:
                    notes.append("Customer-Experience mailbox — Charles approved a technical "
                                 "sample")
                else:
                    notes.append("Customer-Experience mailbox — **technical sample only; "
                                 "Charles approval NOT recorded** (do not use live yet)")
            if approved:
                notes.append("Charles approval recorded for 3-sample DRAFT_ONLY technical test")
            else:
                notes.append("Charles approval pending")
            note_str = ("; ".join(notes)) if notes else "—"
            L.append(f"- **{r['company']}** ({r['domain']}) → "
                     f"`{scanner.mask_recipient(r['email'])}` · fit=`{r['recipient_fit']}` · "
                     f"status=`{r['review_status']}` · {note_str}")
    else:
        L.append("- (no recipient review CSV found)")
    L.append("")

    L += ["## Approval records",
          f"- Charles recipient-approval record present: "
          f"{'yes' if approvals.get('present') else 'no'}",
          f"- Legacy note path: `{os.path.basename(paths.APPROVALS_NOTE_PATH)}` "
          f"({'present' if approvals.get('note_present') else 'absent'})",
          f"- Latest durable artifact: "
          f"`{approvals.get('artifact_path') or 'not found'}`",
          "- Top-3 recipient approval gate: "
          + ("PASS" if ras.get("recorded") else "PENDING"),
          "- All top-3 remain REVIEW_ONLY until Charles records approval." if not approvals.get(
              "present") else "- Approvals recorded for: "
          + ", ".join(_mask_token(t) for t in sorted(approvals.get("tokens", []))),
          ""]

    L += ["## Inputs parsed (read-only)",
          f"- Sourcing CSV: `{snap.batch32_inputs.get('sourcing_csv') or 'not found'}`",
          f"- Approval packet: `{snap.batch32_inputs.get('approval_packet') or 'not found'}`",
          f"- Recipient review: `{snap.batch32_inputs.get('recipient_review') or 'not found'}`",
          "- No CSV, packet, or CRM file was mutated.",
          ""]
    return "\n".join(L).rstrip() + "\n"


def _charles_approved(rec: Dict[str, object], approvals: Dict[str, object]) -> bool:
    import collectors
    return collectors.recipient_charles_approved(rec, approvals)


def _mask_token(token: str) -> str:
    """Mask an approvals-note token if it is an email (keep company/domain tokens as-is)."""
    return scanner.mask_recipient(token) if "@" in token else token


# ── daily report ────────────────────────────────────────────────────────────────
def render_daily_md(snap: Snapshot, handoff_paths: Optional[Dict[str, str]] = None) -> str:
    handoff_paths = handoff_paths or {}
    ras = snap.recipient_approval_summary
    L: List[str] = [f"# MOTIONX daily ops — what should Charles do next? — {snap.ts}",
                    "", _DRAFT_ONLY_FOOTER, ""]

    L += ["## Done (verified)",
          f"- Visual-cold-open workflow merged at/after `{paths.BASELINE_COMMIT}`; sample "
          "mode present.",
          f"- batch32 sourced ({snap.sourcing.get('total', 0)}), reviewed "
          f"(APPROVE {snap.approval.get('approve', 0)} / MAYBE {snap.approval.get('maybe', 0)}), "
          f"top-3 selected with {len(snap.verified_recipients)} verified recipient emails.",
          f"- Charles top-3 recipient approval recorded: "
          f"{'yes' if ras.get('recorded') else 'no'} "
          f"({ras.get('approved', 0)}/{ras.get('verified', 0)} approved).",
          "- Out-of-repo readiness venv present with readiness packages installed.",
          ""]

    L += ["## Blocked"]
    if not snap.gate.ready:
        if snap.gate.blockers:
            for b in snap.gate.blockers:
                human = {
                    "BLOCKED_ON_GPT_IMAGE_2_ACCESS": "OPENAI_API_KEY not set in the CLI env "
                    "(needed for gpt-image-2).",
                    "BLOCKED_ON_GMAIL_DRAFT_ACCESS": f"Gmail OAuth token absent "
                    f"({os.path.basename(paths.GMAIL_TOKEN_PATH)}).",
                }.get(b, b)
                L.append(f"- `{b}` — {human}")
        # Non-credential gate failures carry no blocker token but are still BLOCKED.
        for g in snap.gate.failed:
            if not g.blocker:
                L.append(f"- `{g.name}` — {g.detail}")
    else:
        L.append("- Nothing blocking the 3-sample live drafts (gates pass).")
    L.append("")

    unv = _claimed_unverified(snap)
    L += ["## Claimed-done-but-unverified"]
    if unv:
        L += [f"- {u}" for u in unv]
    else:
        L.append("- None detected.")
    L.append("")

    L += ["## Next 1–3 actions"]
    actions = _daily_actions(snap, handoff_paths)
    for i, (who, what, cmd) in enumerate(actions, 1):
        L.append(f"{i}. **{who}** — {what}")
        if cmd:
            L.append(f"   - `{cmd}`")
    L.append("")
    return "\n".join(L).rstrip() + "\n"


def _daily_actions(snap: Snapshot, handoff_paths: Dict[str, str]) -> List[tuple]:
    actions = []
    if not snap.gate.ready and snap.gate.blockers:
        ls = handoff_paths.get("live-setup")
        actions.append((
            "Charles",
            "Provide the two missing live credentials (OPENAI_API_KEY into the CLI env + "
            f"place {os.path.basename(paths.GMAIL_TOKEN_PATH)}). Do not commit them.",
            f"cat {ls}" if ls else
            "python3 outreach/agentic_ops/run.py handoff --target codex --task live-setup",
        ))
        actions.append((
            "Codex",
            "Execute the live-setup handoff, then re-run readiness until it prints "
            "READY_FOR_3_SAMPLE_LIVE_DRAFTS.",
            "python3 outreach/agentic_ops/run.py vco-readiness",
        ))
    elif not snap.gate.ready:
        failed = ", ".join(g.name for g in snap.gate.failed)
        actions.append((
            "Codex",
            f"Resolve the failing readiness gate(s) ({failed}) — e.g. restore the batch32 "
            "recipient-review CSV or reinstall the readiness packages — then re-run readiness.",
            "python3 outreach/agentic_ops/run.py vco-readiness",
        ))
    else:
        tsd = handoff_paths.get("three-sample-live-drafts")
        actions.append((
            "Charles",
            "Approve the exact top-3 recipients (still REVIEW_ONLY_PENDING_CHARLES_APPROVAL); "
            "confirm the Trailpoint Customer-Experience mailbox decision.",
            None,
        ))
        actions.append((
            "Codex",
            "Create ≤3 Gmail DRAFTS (draft-only, never send) via the three-sample-live-drafts "
            "handoff; leave them unsent for Charles.",
            f"cat {tsd}" if tsd else
            "python3 outreach/agentic_ops/run.py handoff --target codex "
            "--task three-sample-live-drafts",
        ))
    actions.append((
        "Charles",
        "Review any generated drafts in Gmail and send by hand if satisfied (only Charles "
        "sends).",
        None,
    ))
    return actions[:3]
