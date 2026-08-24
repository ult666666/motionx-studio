# -*- coding: utf-8 -*-
"""Safety scanner for agentic-ops reports and handoffs.

Reuses the battle-tested redaction/masking in
`outreach/visual_cold_open/safety.py` when importable, and extends it with:
  * Gmail OAuth-token / client-secret JSON content detection.
  * A raw `OPENAI_API_KEY=<value>` assignment guard.
  * A handoff guard that FAILS if the "Codex should execute" block tells Codex to
    *send* email (as opposed to "create draft only").
  * Email local-part masking for human reports.

Every generated report and handoff is passed through `scan_report` /
`scan_handoff` before it is written; a finding raises `ScanError`.

Pure stdlib.
"""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass, field
from typing import List

# ── Reuse visual_cold_open/safety.py when available (single source of truth) ────
_VCO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visual_cold_open"
)
if _VCO_DIR not in sys.path:
    sys.path.insert(0, _VCO_DIR)

try:  # pragma: no cover - exercised indirectly
    import safety as _vco_safety  # type: ignore

    _redact = _vco_safety.redact_secrets
    _contains_secret = _vco_safety.contains_secret_material
    mask_draft_id = _vco_safety.mask_draft_id
    mask_recipient = _vco_safety.mask_recipient
    assert_not_send = _vco_safety.assert_not_send
    SendForbiddenError = _vco_safety.SendForbiddenError
except Exception:  # pragma: no cover - defensive fallback if layout changes
    _vco_safety = None

    _FALLBACK_SECRET_PATTERNS = [
        re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),
        re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),
        re.compile(r"ya29\.[0-9A-Za-z_\-]+"),
        re.compile(r"[0-9]+-[0-9a-z]{20,}\.apps\.googleusercontent\.com"),
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ]

    class SendForbiddenError(RuntimeError):
        pass

    def _redact(text: str) -> str:
        out = text or ""
        for pat in _FALLBACK_SECRET_PATTERNS:
            out = pat.sub("[REDACTED]", out)
        return out

    def _contains_secret(text: str) -> bool:
        return bool(text) and any(p.search(text) for p in _FALLBACK_SECRET_PATTERNS)

    def mask_draft_id(draft_id: str) -> str:
        d = (draft_id or "").strip()
        if not d:
            return ""
        if len(d) <= 6:
            return d[0] + "***" if len(d) > 1 else "***"
        return f"{d[:4]}***{d[-2:]}"

    def mask_recipient(email: str) -> str:
        email = (email or "").strip()
        if "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        if not local:
            return "***@" + domain
        return f"{local[0]}***@{domain}"

    def assert_not_send(op_name: str) -> None:
        low = (op_name or "").lower()
        for tok in ("send", "schedule", "trash", "delete", "insert"):
            if tok in low:
                raise SendForbiddenError(f"Refused forbidden Gmail op {op_name!r}")


# ── Additional agentic-ops patterns ─────────────────────────────────────────────
# Gmail OAuth token / OAuth-client-secret JSON content (never allowed in a report).
_GMAIL_TOKEN_PATTERNS = [
    re.compile(r'"refresh_token"\s*:\s*"[^"]+"'),
    re.compile(r'"client_secret"\s*:\s*"[^"]+"'),
    re.compile(r'"access_token"\s*:\s*"[^"]+"'),
    re.compile(r'"installed"\s*:\s*\{'),
    re.compile(r'"auth_uri"\s*:\s*"https://accounts\.google\.com/o/oauth2/auth"'),
    re.compile(r'"token_uri"\s*:\s*"https://oauth2\.googleapis\.com/token"'),
    re.compile(r"\brefresh_token\b\s*[:=]\s*\S+"),
    re.compile(r"\bclient_secret\b\s*[:=]\s*\S+"),
    re.compile(r'GOCSPX-[A-Za-z0-9_\-]{6,}'),
]

# A raw assignment of the OpenAI key with a real-looking value.
_OPENAI_ASSIGN = re.compile(r"OPENAI_API_KEY\s*=\s*['\"]?(sk-[A-Za-z0-9_\-]{12,})")

# "Send email" imperatives / mailbox-mutating ops that must never appear as an
# EXECUTION action (matched case-insensitively via substring).
_SEND_ACTION_TOKENS = (
    "send email", "send the email", "send emails", "send drafts", "send draft",
    "send it", "send them", "messages.send", "drafts.send", "gmail send",
    "send_email", "sendmessage", "send message", "schedule send", "schedule the send",
    "actually send", "hit send", "press send",
    # mailbox-mutating send-equivalents (messages.insert injects as if received)
    "messages.insert", "drafts.insert", "messages().send", "drafts().send",
    "messages().insert", ".send(", ".insert(",
    # natural-language send synonyms
    "deliver the email", "transmit the email", "dispatch the email", "fire off",
    "blast out", "email it to", "email them",
)


@dataclass
class ScanFinding:
    kind: str          # secret | gmail-token | openai-key | send-as-action | draft-id | inside-repo
    detail: str


@dataclass
class ScanResult:
    findings: List[ScanFinding] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.findings

    def messages(self) -> List[str]:
        return [f"[{f.kind}] {f.detail}" for f in self.findings]


class ScanError(RuntimeError):
    """Raised when a report/handoff fails the safety scan."""

    def __init__(self, result: "ScanResult"):
        self.result = result
        super().__init__("Safety scan failed:\n  " + "\n  ".join(result.messages()))


def redact_secrets(text: str) -> str:
    return _redact(text or "")


def contains_secret_material(text: str) -> bool:
    return _contains_secret(text or "")


def contains_gmail_token_content(text: str) -> bool:
    return any(p.search(text or "") for p in _GMAIL_TOKEN_PATTERNS)


def contains_openai_key_assignment(text: str) -> bool:
    return bool(_OPENAI_ASSIGN.search(text or ""))


def find_send_as_action(execute_text: str) -> List[str]:
    """Return send tokens that appear in an EXECUTION block (order-preserving)."""
    low = (execute_text or "").lower()
    return [tok for tok in _SEND_ACTION_TOKENS if tok in low]


def scan_report(text: str) -> ScanResult:
    """Scan a human report for anything that must never be written."""
    res = ScanResult()
    if contains_secret_material(text):
        res.findings.append(ScanFinding("secret", "secret-looking value (API key / OAuth token / PEM)"))
    if contains_gmail_token_content(text):
        res.findings.append(ScanFinding("gmail-token", "Gmail OAuth token / client-secret JSON content"))
    if contains_openai_key_assignment(text):
        res.findings.append(ScanFinding("openai-key", "raw OPENAI_API_KEY=<value> assignment"))
    return res


def assert_report_safe(text: str) -> None:
    res = scan_report(text)
    if not res.ok:
        raise ScanError(res)


def _extract_execute_block(handoff_text: str) -> str:
    """Return the text of the 'Codex should execute:' section only.

    The section runs until the next 'Codex must NOT:' header (or end of text), so a
    prohibition like 'Codex must NOT: send email' is deliberately NOT scanned as an
    execution action.
    """
    m = re.search(
        r"Codex should execute:(.*?)(?:^\s*Codex must NOT:|\Z)",
        handoff_text or "",
        flags=re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    return m.group(1) if m else ""


def scan_handoff(handoff_text: str) -> ScanResult:
    """Scan a Codex handoff: secrets + Gmail-token content + send-as-execution."""
    res = scan_report(handoff_text)
    execute_block = _extract_execute_block(handoff_text)
    for tok in find_send_as_action(execute_block):
        res.findings.append(
            ScanFinding("send-as-action",
                        f"handoff EXECUTE block instructs a send action ({tok!r}); "
                        f"must be 'create draft only'")
        )
    return res


def assert_handoff_safe(handoff_text: str) -> None:
    res = scan_handoff(handoff_text)
    if not res.ok:
        raise ScanError(res)
