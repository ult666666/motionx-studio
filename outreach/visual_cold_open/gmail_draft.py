# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — Gmail draft adapter (DRAFT_ONLY).

The MCP Gmail connector cannot attach files or update a draft, so the visual layer's
LIVE path uses the Gmail API directly (google-api-python-client + OAuth) from the CLI,
where Charles has the necessary access. This adapter exposes ONLY the draft lifecycle:

    drafts.create · drafts.update · drafts.get · drafts.list

There is deliberately NO send method. Every operation is routed through
`safety.assert_allowed_draft_op`, and any attribute whose name looks like a send /
schedule / destructive op raises `SendForbiddenError`. The real Google client is
lazily imported so unit tests run offline with an injected fake `service`.
"""
from __future__ import annotations

import os as _os
import sys as _sys
from typing import Optional

_VCO_DIR = _os.path.dirname(_os.path.abspath(__file__))
if _VCO_DIR not in _sys.path:
    _sys.path.insert(0, _VCO_DIR)

import safety  # noqa: E402

# OAuth scope note: gmail.compose is the minimal scope that permits drafts.create/
# update. (Google has no "drafts but never send" scope — the send *capability* exists
# at the scope level, so the real protection is this module never invoking a send
# endpoint. Documented as a residual risk in the runbook.)
GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"


class GmailApiUnavailable(RuntimeError):
    """Raised when the Gmail API client/credentials are not available for a live op."""


class GmailDraftBackend:
    def __init__(
        self,
        service: object = None,
        credentials_path: str = "",
        token_path: str = "",
        user_id: str = "me",
        expected_account: str = "",
    ):
        self._injected_service = service
        self._credentials_path = credentials_path
        self._token_path = token_path
        self.user_id = user_id
        self.expected_account = expected_account

    # ── service resolution ──────────────────────────────────────────────────────
    def _service(self):
        if self._injected_service is not None:
            return self._injected_service
        try:
            from google.oauth2.credentials import Credentials  # lazy
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except Exception as exc:  # pragma: no cover - environment dependent
            raise GmailApiUnavailable(
                "google-api-python-client / google-auth-oauthlib are not installed. "
                "Install them in the CLI environment for live draft operations."
            ) from exc

        creds = None
        if self._token_path and _os.path.exists(self._token_path):
            creds = Credentials.from_authorized_user_file(
                self._token_path, [GMAIL_COMPOSE_SCOPE])
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif self._credentials_path and _os.path.exists(self._credentials_path):
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_path, [GMAIL_COMPOSE_SCOPE])
                creds = flow.run_local_server(port=0)
                if self._token_path:
                    with open(self._token_path, "w", encoding="utf-8") as fh:
                        fh.write(creds.to_json())
            else:
                raise GmailApiUnavailable(
                    "No usable Gmail OAuth credentials. Provide --gmail-token and/or "
                    "--gmail-credentials pointing at approved OAuth files."
                )
        self._injected_service = build("gmail", "v1", credentials=creds,
                                       cache_discovery=False)
        return self._injected_service

    # ── send tripwire: any send/schedule/destructive attribute access fails ─────
    def __getattr__(self, name: str):
        # __getattr__ only fires for attributes not found normally, so this cannot
        # shadow the real methods below. It turns backend.send(...) etc. into an error.
        low = name.lower()
        if any(tok in low for tok in safety.FORBIDDEN_SEND_TOKENS):
            raise safety.SendForbiddenError(
                f"GmailDraftBackend has no {name!r}: this DRAFT_ONLY adapter exposes "
                f"only drafts.create/update/get/list."
            )
        raise AttributeError(name)

    # ── verified account ────────────────────────────────────────────────────────
    def verify_account(self) -> str:
        """Return the connected email address; assert it is the expected mailbox."""
        safety.assert_allowed_draft_op("drafts.list")  # read-only capability probe
        profile = self._service().users().getProfile(userId=self.user_id).execute()
        email = profile.get("emailAddress", "")
        if self.expected_account:
            safety.assert_expected_account(email, self.expected_account)
        return email

    # ── draft lifecycle (the ONLY mutations allowed) ────────────────────────────
    def create_draft(self, raw: str) -> dict:
        safety.assert_allowed_draft_op("drafts.create")
        body = {"message": {"raw": raw}}
        return self._service().users().drafts().create(
            userId=self.user_id, body=body).execute()

    def update_draft(self, draft_id: str, raw: str) -> dict:
        safety.assert_allowed_draft_op("drafts.update")
        body = {"message": {"raw": raw}}
        return self._service().users().drafts().update(
            userId=self.user_id, id=draft_id, body=body).execute()

    def get_draft(self, draft_id: str, fmt: str = "metadata") -> dict:
        safety.assert_allowed_draft_op("drafts.get")
        return self._service().users().drafts().get(
            userId=self.user_id, id=draft_id, format=fmt).execute()

    # ── draft-only verification ─────────────────────────────────────────────────
    def verify_draft_only(self, draft_id: str) -> dict:
        """Confirm a draft is a DRAFT and NOT sent. Returns a small verdict dict."""
        draft = self.get_draft(draft_id, fmt="metadata")
        message = draft.get("message", {}) or {}
        label_ids = message.get("labelIds", []) or []
        is_draft = "DRAFT" in label_ids
        is_sent = "SENT" in label_ids
        return {
            "draft_id": draft_id,
            "message_id": message.get("id", ""),
            "thread_id": message.get("threadId", ""),
            "label_ids": label_ids,
            "is_draft": is_draft,
            "is_sent": is_sent,
            "draft_only": is_draft and not is_sent,
        }
