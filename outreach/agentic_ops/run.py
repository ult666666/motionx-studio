#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MOTIONX agentic-ops CLI — safe oversight + Codex handoffs (DRAFT_ONLY).

Commands:
  status          Repo/auth/reports snapshot + highest-value next action.
  vco-readiness   No-write readiness gate for the 3 sample live drafts.
  batch32-status  Read-only batch32 candidate/recipient counts + flags.
  ledger          Append/read workflow evidence ledger (outside repo).
  context-pack    Generate a concise future-Codex context pack (outside repo).
  credentials-setup
                  Setup/check live credential prerequisites (safe, no drafts).
  live-setup-checklist
                  Human checklist for final live-readiness steps.
  handoff         Generate a Codex-ready handoff (--target codex --task <task>).
  daily-report    Compact "what should Charles do next?" report.

Every command READS state and WRITES a report/handoff OUTSIDE the repo
(default ~/.motionx-outreach/). It never sends/schedules email, never creates or
updates Gmail drafts, never generates images, never mutates CRM, never touches
secrets. See outreach/AGENTIC-OPS-RUNBOOK.md.

Run: python3 outreach/agentic_ops/run.py <command> [options]
"""
from __future__ import annotations

import argparse
import os
import sys

# Flat-module convention (mirrors outreach/visual_cold_open): ensure this dir is on
# sys.path so `import paths` etc. resolve when run directly.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import paths          # noqa: E402
import engine         # noqa: E402
import handoffs       # noqa: E402
import ledger         # noqa: E402
import approvals      # noqa: E402
import credentials    # noqa: E402
import render         # noqa: E402
import scanner        # noqa: E402


def _add_common(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--crm-dir", default=paths.CRM_DIR,
                    help="out-of-repo state root (default ~/.motionx-outreach)")
    sp.add_argument("--reports-dir", default=None,
                    help="override reports output dir (default <crm-dir>/reports)")
    sp.add_argument("--handoffs-dir", default=None,
                    help="override handoffs output dir (default <crm-dir>/handoffs)")
    sp.add_argument("--repo-root", default=None, help="override repo root")
    sp.add_argument("--no-pip", action="store_true",
                    help="skip querying the venv's pip (faster; versions unknown)")
    sp.add_argument("--print", dest="do_print", action="store_true",
                    help="also print the rendered report/handoff to stdout")


def _snapshot(args) -> engine.Snapshot:
    return engine.build_snapshot(
        repo_root=args.repo_root, crm_dir=args.crm_dir,
        reports_dir=args.reports_dir, handoffs_dir=args.handoffs_dir,
        run_pip=not args.no_pip,
    )


def _out_path(snap: engine.Snapshot, name: str) -> str:
    return os.path.join(snap.reports_dir, name)


def cmd_status(args) -> int:
    snap = _snapshot(args)
    text = render.render_status_md(snap)
    path = render.write_report(text, _out_path(snap, f"motionx_ops_status_{snap.ts}.md"),
                               snap.repo.root)
    print(f"status: verdict={snap.gate.verdict} blockers={snap.gate.blockers or 'none'}")
    print(f"next action: {snap.next_action}")
    print(f"report: {path}")
    if args.do_print:
        print("\n" + text)
    return 0


def cmd_vco_readiness(args) -> int:
    snap = _snapshot(args)
    text = render.render_vco_readiness_md(snap)
    path = render.write_report(text, _out_path(snap, f"vco_readiness_{snap.ts}.md"),
                               snap.repo.root)
    if snap.gate.ready:
        print(engine.collectors.READY_FOR_3_SAMPLE_LIVE_DRAFTS)
    else:
        print("BLOCKED")
        for b in snap.gate.blockers:
            print(b)
    print(f"report: {path}")
    if args.do_print:
        print("\n" + text)
    return 0


def cmd_batch32_status(args) -> int:
    snap = _snapshot(args)
    text = render.render_batch32_status_md(snap)
    path = render.write_report(text, _out_path(snap, f"batch32_status_{snap.ts}.md"),
                               snap.repo.root)
    print(f"batch32: sourced={snap.sourcing.get('total', 0)} "
          f"APPROVE={snap.approval.get('approve', 0)} MAYBE={snap.approval.get('maybe', 0)} "
          f"REJECT={snap.approval.get('reject', 0)} "
          f"top3={len(snap.verified_recipients)}")
    for r in snap.verified_recipients:
        if r.get("customer_experience_oriented"):
            print(f"flag: {r['company']} {scanner.mask_recipient(r['email'])} is a "
                  "Customer-Experience mailbox (technical sample only)")
    print(f"report: {path}")
    if args.do_print:
        print("\n" + text)
    return 0


def cmd_ledger(args) -> int:
    snap = _snapshot(args)
    paths_written = ledger.write_ledger(snap)
    print(f"ledger: {paths_written['jsonl']}")
    print(f"report: {paths_written['report']}")
    if args.do_print:
        with open(paths_written["report"], "r", encoding="utf-8") as fh:
            print("\n" + fh.read())
    return 0


def cmd_context_pack(args) -> int:
    snap = _snapshot(args)
    path = ledger.write_context_pack(snap)
    print(f"context-pack: {path}")
    if args.do_print:
        with open(path, "r", encoding="utf-8") as fh:
            print("\n" + fh.read())
    return 0


def cmd_record_batch32_top3_approval(args) -> int:
    if not args.charles_approved_top3:
        print("error: pass --charles-approved-top3 to record this explicit approval",
              file=sys.stderr)
        return 2
    snap = _snapshot(args)
    written = approvals.write_batch32_top3_approval(snap.crm_dir, snap.repo.root, snap.ts)
    print(f"approval: {written['artifact']}")
    print(f"approval-note: {written['note']}")
    return 0


def cmd_credentials_setup(args) -> int:
    snap = _snapshot(args)
    result = credentials.run_setup(
        crm_dir=snap.crm_dir,
        repo_root=snap.repo.root,
        venv=snap.venv,
        interactive=args.interactive,
        write_openai_key=args.write_openai_key,
        setup_gmail_oauth=args.setup_gmail_oauth,
        verify_only=args.verify_only,
        no_browser=args.no_browser,
        force_refresh_token=args.force_refresh_token,
        verify_live_openai=args.verify_live_openai,
    )
    text = credentials.render_setup_report(result, snap.gate.verdict)
    path = render.write_report(text, _out_path(snap, f"credentials_setup_{snap.ts}.md"),
                               snap.repo.root)
    print(f"credentials-setup: mode={result.mode} ok={result.ok}")
    print(f"openai_key_present: {'yes' if result.state.openai_present else 'no'}")
    print(f"gmail_credentials_json_present: "
          f"{'yes' if result.state.gmail_credentials_present else 'no'}")
    print(f"gmail_token_present: {'yes' if result.state.gmail_token_present else 'no'}")
    print(f"gmail_account_verified: {result.state.gmail_account_verified}")
    for w in result.warnings:
        print(f"warning: {w}")
    for e in result.errors:
        print(f"error: {e}", file=sys.stderr)
    print(f"report: {path}")
    if args.do_print:
        print("\n" + text)
    if result.errors:
        return 2 if any(e.startswith("--") for e in result.errors) else 1
    return 0


def cmd_live_setup_checklist(args) -> int:
    snap = _snapshot(args)
    state = credentials.build_state(crm_dir=snap.crm_dir, venv=snap.venv)
    text = credentials.render_live_setup_checklist(state, snap)
    path = render.write_report(text, _out_path(snap, f"live_setup_checklist_{snap.ts}.md"),
                               snap.repo.root)
    print(f"live-setup-checklist: verdict={snap.gate.verdict}")
    print(f"openai_key_present: {'yes' if state.openai_present else 'no'}")
    print(f"gmail_credentials_json_present: {'yes' if state.gmail_credentials_present else 'no'}")
    print(f"gmail_token_present: {'yes' if state.gmail_token_present else 'no'}")
    print(f"gmail_account_verified: {state.gmail_account_verified}")
    print(f"next command: {credentials.next_setup_command(state)}")
    print(f"report: {path}")
    if args.do_print:
        print("\n" + text)
    return 0


def cmd_handoff(args) -> int:
    if args.target != "codex":
        print(f"error: --target must be 'codex' (got {args.target!r})", file=sys.stderr)
        return 2
    if args.task not in handoffs.TASKS:
        print(f"error: --task must be one of {', '.join(handoffs.TASKS)} (got {args.task!r})",
              file=sys.stderr)
        return 2
    snap = _snapshot(args)
    text = handoffs.render_handoff(args.task, snap)
    hdir = snap.handoffs_dir
    path = os.path.join(hdir, f"{args.task}_{snap.ts}.txt")
    render.write_handoff(text, path, snap.repo.root)
    print(f"handoff: {path}")
    if args.do_print:
        print("\n" + text)
    return 0


def cmd_daily_report(args) -> int:
    snap = _snapshot(args)
    # Generate the relevant handoff(s) so the daily report can point to real paths.
    # Key off gate.ready: only recommend live drafts when EVERY gate passes; recommend
    # live-setup only for a credential blocker; otherwise (non-credential block) emit no
    # draft-creation handoff — the report explains which gate failed.
    handoff_paths = {}
    if snap.gate.ready:
        tasks = ["three-sample-live-drafts"]
    elif snap.gate.blockers:
        tasks = ["live-setup"]
    else:
        tasks = []
    for task in tasks:
        try:
            htext = handoffs.render_handoff(task, snap)
            hp = os.path.join(snap.handoffs_dir, f"{task}_{snap.ts}.txt")
            render.write_handoff(htext, hp, snap.repo.root)
            handoff_paths[task] = hp
        except Exception as exc:   # pragma: no cover - defensive; never abort the report
            print(f"warning: could not generate {task} handoff: {exc}", file=sys.stderr)
    text = render.render_daily_md(snap, handoff_paths)
    path = render.write_report(text, _out_path(snap, f"motionx_daily_ops_{snap.ts}.md"),
                               snap.repo.root)
    print(f"daily-report: verdict={snap.gate.verdict}")
    for task, hp in handoff_paths.items():
        print(f"handoff[{task}]: {hp}")
    print(f"report: {path}")
    if args.do_print:
        print("\n" + text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="motionx-agentic-ops",
        description="Safe MOTIONX agentic-ops oversight (DRAFT_ONLY; no sends, no drafts).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    for name, fn in (
        ("status", cmd_status),
        ("vco-readiness", cmd_vco_readiness),
        ("batch32-status", cmd_batch32_status),
        ("ledger", cmd_ledger),
        ("context-pack", cmd_context_pack),
        ("live-setup-checklist", cmd_live_setup_checklist),
        ("daily-report", cmd_daily_report),
    ):
        sp = sub.add_parser(name)
        _add_common(sp)
        sp.set_defaults(func=fn)

    cp = sub.add_parser("credentials-setup")
    _add_common(cp)
    cp.add_argument("--interactive", action="store_true",
                    help="allow hidden local prompts for Charles")
    cp.add_argument("--write-openai-key", action="store_true",
                    help="write OPENAI_API_KEY to ~/.motionx-outreach/secrets.env "
                    "(requires --interactive)")
    cp.add_argument("--setup-gmail-oauth", action="store_true",
                    help="run Gmail OAuth flow if gmail_credentials.json exists")
    cp.add_argument("--verify-only", action="store_true",
                    help="check credential presence only; never write")
    cp.add_argument("--no-browser", action="store_true",
                    help="avoid opening a browser when the OAuth helper supports it")
    cp.add_argument("--force-refresh-token", action="store_true",
                    help="refresh Gmail token even when one already exists")
    cp.add_argument("--verify-live-openai", action="store_true",
                    help="optional cheap gpt-image-2 models.retrieve preflight; no image generation")
    cp.set_defaults(func=cmd_credentials_setup)

    ap = sub.add_parser("record-batch32-top3-approval")
    _add_common(ap)
    ap.add_argument("--charles-approved-top3", action="store_true",
                    help="required confirmation that Charles approved the exact top-3")
    ap.set_defaults(func=cmd_record_batch32_top3_approval)

    hp = sub.add_parser("handoff")
    _add_common(hp)
    hp.add_argument("--target", default="codex", help="handoff target (only 'codex')")
    hp.add_argument("--task", required=True, choices=handoffs.TASKS,
                    help="which handoff to generate")
    hp.set_defaults(func=cmd_handoff)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
