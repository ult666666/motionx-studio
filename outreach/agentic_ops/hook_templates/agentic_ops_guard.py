#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MOTIONX agentic-ops PreToolUse guard — TEMPLATE (NOT enabled by default).

A single, stdlib-only Claude Code PreToolUse hook that fails CLOSED on dangerous
actions and WARNS on risky-but-allowed ones. It is a *template*: nothing wires it
into any settings.json until Charles chooses to (see HOOKS-RUNBOOK.md).

Protocol: reads the PreToolUse JSON on stdin
    {"tool_name": "...", "tool_input": {...}, ...}
Decision:
    * exit 2  + message on stderr  -> BLOCK the tool call (model sees the reason)
    * exit 0  + message on stderr  -> ALLOW but surface a WARNING
    * exit 0  (silent)             -> ALLOW

Blocks:
  * Dangerous git / fs: `git push`, `git reset --hard`, `git clean -fd`, `rm -rf`.
  * Gmail send paths: messages.send, drafts.send, gmail send, send_email, messages.insert.
  * Secret exposure: literal sk-… keys, refresh_token / client_secret material, reading or
    committing gmail_token.json / secrets.env / client_secret*.json.
Warns:
  * A generated report/asset path pointed INSIDE the repo instead of ~/.motionx-outreach/.
  * Any command / edit that references outreach/self-improvement.md.

On unparseable input this guard fails OPEN (exit 0) so it can never brick a session;
flip `FAIL_OPEN = False` to fail closed once you trust it.
"""
from __future__ import annotations

import json
import os
import re
import sys

FAIL_OPEN = True

# ── Block patterns ──────────────────────────────────────────────────────────────
_DANGEROUS_CMD = [
    (re.compile(r"\bgit\s+push\b"), "git push is forbidden (do not push from ops automation)"),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "git reset --hard is forbidden (destructive)"),
    (re.compile(r"\bgit\s+clean\s+-[a-z]*f[a-z]*d|\bgit\s+clean\s+-[a-z]*d[a-z]*f"),
     "git clean -fd is forbidden (destroys untracked files)"),
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r"),
     "rm -rf is forbidden"),
]

_GMAIL_SEND = re.compile(
    # dotted forms (messages.send) AND the google-api-python-client fluent form
    # (messages().send(...), drafts().send(...), messages().insert(...))
    r"messages\.send|drafts\.send|messages\.insert|drafts\.insert|"
    r"(?:messages|drafts)\s*\(\s*\)\s*\.\s*(?:send|insert)|"
    r"gmail\s+send|\bsend_email\b|\bsendmessage\b",
    re.IGNORECASE,
)

_SECRET_MATERIAL = [
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
    re.compile(r"ya29\.[0-9A-Za-z_\-]+"),
    re.compile(r"GOCSPX-[A-Za-z0-9_\-]{6,}"),
    re.compile(r'"?refresh_token"?\s*[:=]\s*\S+'),
    re.compile(r'"?client_secret"?\s*[:=]\s*\S+'),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

_SECRET_FILE = re.compile(r"gmail_token[^/]*\.json|secrets\.env|gmail_credentials[^/]*\.json|"
                          r"client_secret[^/]*\.json", re.IGNORECASE)

# Reading/committing a secret file (cat/less/git add/echo > …).
_SECRET_FILE_ACCESS = re.compile(
    r"(cat|less|head|tail|bat|open|git\s+add|cp|mv|scp)\s+[^\n|&;]*"
    r"(gmail_token[^/\s]*\.json|secrets\.env|client_secret[^/\s]*\.json)",
    re.IGNORECASE,
)

_SELF_IMPROVEMENT = re.compile(r"outreach/self-improvement\.md")

# Report/asset artifacts that belong OUTSIDE the repo.
_ARTIFACT_HINT = re.compile(
    r"(motionx_ops_status_|vco_readiness_|batch32_status_|motionx_daily_ops_|"
    r"visual_cold_open_|_vco_sample_run_|\.png\b)", re.IGNORECASE)


def _emit(block: bool, msg: str) -> "int":
    sys.stderr.write(("BLOCK: " if block else "WARN: ") + msg + "\n")
    return 2 if block else 0


def check_bash(cmd: str) -> int:
    for pat, msg in _DANGEROUS_CMD:
        if pat.search(cmd):
            return _emit(True, msg)
    if _GMAIL_SEND.search(cmd):
        return _emit(True, "Gmail send path detected — DRAFT_ONLY: never send/schedule/insert.")
    if _SECRET_FILE_ACCESS.search(cmd) or any(p.search(cmd) for p in _SECRET_MATERIAL):
        return _emit(True, "Secret exposure detected (token/key/secret-file) — refused.")
    warn = 0
    if _SELF_IMPROVEMENT.search(cmd):
        warn = _emit(False, "Command references outreach/self-improvement.md — leave it untouched.")
    # A generated artifact redirected into the repo tree.
    if _ARTIFACT_HINT.search(cmd) and re.search(r">\s*[^~/]|>\s*\./|--report[-\s=]|--out[-\s=]", cmd):
        if "/.motionx-outreach/" not in cmd:
            warn = _emit(False, "A generated report/asset may be pointed INSIDE the repo; "
                                "write it under ~/.motionx-outreach/ instead.")
    return warn


def check_write(tool_input: dict) -> int:
    path = str(tool_input.get("file_path", ""))
    content = str(tool_input.get("content", "") or tool_input.get("new_string", ""))
    if _SECRET_FILE.search(os.path.basename(path)):
        return _emit(True, f"Refusing to write a secret file ({path}).")
    if any(p.search(content) for p in _SECRET_MATERIAL):
        return _emit(True, "Refusing to write secret material (token/key/PEM) into a file.")
    if _SELF_IMPROVEMENT.search(path):
        return _emit(False, "Editing outreach/self-improvement.md — this file is pre-existing "
                            "and unrelated; leave it untouched.")
    if _ARTIFACT_HINT.search(os.path.basename(path)) and "/.motionx-outreach/" not in path:
        return _emit(False, f"Report/asset {path} looks like it is inside the repo; write it "
                            "under ~/.motionx-outreach/ instead.")
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0 if FAIL_OPEN else _emit(True, "Unparseable hook input; failing closed.")
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    try:
        if tool == "Bash":
            return check_bash(str(tool_input.get("command", "")))
        if tool in ("Write", "Edit", "NotebookEdit"):
            return check_write(tool_input)
    except Exception:
        return 0 if FAIL_OPEN else _emit(True, "Guard error; failing closed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
