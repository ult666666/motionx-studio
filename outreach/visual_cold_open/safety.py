# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — safety guards.

Central, defensive protections that make it hard to accidentally send email, leak a
secret, or point at the wrong Gmail account. Every Gmail operation in this package
routes through `assert_not_send`.
"""
from __future__ import annotations

import re
from typing import Iterable

# Any endpoint / method name containing one of these is a SEND path and is forbidden.
FORBIDDEN_SEND_TOKENS = (
    "send",          # messages.send, drafts.send, .send(...)
    "schedule",      # scheduled send
    "trash",         # not a send, but destructive Gmail mutation — also forbidden here
    "delete",        # this workflow never deletes messages/drafts programmatically
    "insert",        # messages.insert can inject into the mailbox as if received
)

# Endpoints this workflow is allowed to touch (draft lifecycle + read-back only).
ALLOWED_DRAFT_OPS = frozenset({
    "drafts.create", "drafts.update", "drafts.get", "drafts.list",
})

# Regexes for material that must NEVER be logged or written to the repo/reports.
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{12,}"),                     # OpenAI-style key
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),                    # Google API key
    re.compile(r"ya29\.[0-9A-Za-z_\-]+"),                      # Google OAuth token
    re.compile(r"[0-9]+-[0-9a-z]{20,}\.apps\.googleusercontent\.com"),  # client id
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),         # PEM
]


class SendForbiddenError(RuntimeError):
    """Raised whenever any code attempts a Gmail send/schedule/destructive op."""


class WrongAccountError(RuntimeError):
    """Raised when the Gmail account is not the expected outreach mailbox."""


def assert_not_send(op_name: str) -> None:
    """Fail closed if `op_name` names a send/schedule/destructive endpoint.

    This is the workflow's last line of defence: even if a future edit wired a send
    call, routing it through here turns it into a hard error instead of an email.
    """
    low = (op_name or "").lower()
    for tok in FORBIDDEN_SEND_TOKENS:
        if tok in low:
            raise SendForbiddenError(
                f"Refused forbidden Gmail operation {op_name!r}: this DRAFT_ONLY "
                f"workflow must never call a *{tok}* endpoint."
            )


def assert_allowed_draft_op(op_name: str) -> None:
    """Whitelist check: only the draft-lifecycle ops are permitted."""
    assert_not_send(op_name)
    if op_name not in ALLOWED_DRAFT_OPS:
        raise SendForbiddenError(
            f"Refused Gmail operation {op_name!r}: not in the allowed draft-op "
            f"whitelist {sorted(ALLOWED_DRAFT_OPS)}."
        )


def assert_expected_account(actual: str, expected: str) -> None:
    if (actual or "").strip().lower() != (expected or "").strip().lower():
        raise WrongAccountError(
            f"Gmail account mismatch: connected as {actual!r} but expected "
            f"{expected!r}. Refusing to operate on the wrong mailbox."
        )


def redact_secrets(text: str) -> str:
    """Return `text` with any secret-looking material replaced by [REDACTED]."""
    if not text:
        return text
    out = text
    for pat in _SECRET_PATTERNS:
        out = pat.sub("[REDACTED]", out)
    return out


def contains_secret_material(text: str) -> bool:
    if not text:
        return False
    return any(p.search(text) for p in _SECRET_PATTERNS)


def any_contains_secret(values: Iterable[str]) -> bool:
    return any(contains_secret_material(str(v)) for v in values if v is not None)


def mask_draft_id(draft_id: str) -> str:
    """Partially mask a Gmail draft id for reports (keep head/tail, hide the middle).

    Reports never carry a full draft id verbatim. A short id is fully masked.
    """
    d = (draft_id or "").strip()
    if not d:
        return ""
    if len(d) <= 6:
        return d[0] + "***" if len(d) > 1 else "***"
    return f"{d[:4]}***{d[-2:]}"


def mask_recipient(email: str) -> str:
    """A safe recipient identifier for reports/logs — masks the mailbox local part
    but keeps the domain (the company), e.g. 'jane@studio.com' -> 'j***@studio.com'.
    Avoids writing a full private mailbox address into a report row.
    """
    email = (email or "").strip()
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if not local:
        return "***@" + domain
    head = local[0]
    return f"{head}***@{domain}"
