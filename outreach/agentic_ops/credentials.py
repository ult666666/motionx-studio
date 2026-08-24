# -*- coding: utf-8 -*-
"""Safe credentials setup assistant for MOTIONX agentic-ops.

This module performs setup-only checks/writes for later DRAFT_ONLY live drafting:
  * OPENAI_API_KEY can be written to ~/.motionx-outreach/secrets.env only via an
    explicit interactive path. The key is never printed or returned.
  * Gmail OAuth can mint ~/.motionx-outreach/gmail_token.json only when the desktop
    credentials JSON already exists and --setup-gmail-oauth is explicitly requested.

No Gmail message/draft API is wired here. No image generation is wired here. Optional
OpenAI live verification uses the visual layer's cheap models.retrieve preflight only
when explicitly requested by the operator.
"""
from __future__ import annotations

import base64
import json
import os
import re
import shlex
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import paths
import scanner

GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"
MISSING_GMAIL_CREDENTIALS_INSTRUCTION = (
    "Download a Google OAuth Desktop App credentials JSON with Gmail API enabled and "
    "place it at ~/.motionx-outreach/gmail_credentials.json."
)


@dataclass
class CredentialState:
    crm_dir: str
    secrets_env_path: str
    gmail_credentials_path: str
    gmail_token_path: str
    openai_env_present: bool
    openai_secrets_env_present: bool
    openai_package_present: Optional[bool]
    gmail_credentials_present: bool
    gmail_token_present: bool
    gmail_account_verified: str = "unknown"  # yes | no | unknown
    gmail_account_detail: str = "not checked"
    openai_live_verified: str = "not requested"  # pass | fail | not requested | skipped
    openai_live_detail: str = ""

    @property
    def openai_present(self) -> bool:
        return self.openai_env_present or self.openai_secrets_env_present


@dataclass
class CredentialSetupResult:
    state: CredentialState
    mode: str
    actions: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    wrote_secrets_env: bool = False
    wrote_gmail_token: bool = False
    chmod_paths: List[str] = field(default_factory=list)
    report_path: str = ""

    @property
    def ok(self) -> bool:
        return not self.errors


def _path(crm_dir: str, basename: str) -> str:
    return os.path.join(crm_dir, basename)


def secrets_env_path(crm_dir: str) -> str:
    return _path(crm_dir, os.path.basename(paths.SECRETS_ENV_PATH))


def gmail_credentials_path(crm_dir: str) -> str:
    return _path(crm_dir, os.path.basename(paths.GMAIL_CREDENTIALS_PATH))


def gmail_token_path(crm_dir: str) -> str:
    return _path(crm_dir, os.path.basename(paths.GMAIL_TOKEN_PATH))


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


def _env_key_present_in_text(text: str, key: str) -> bool:
    for line in (text or "").splitlines():
        m = re.match(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m or m.group(1) != key:
            continue
        value = m.group(2).strip().strip("'").strip('"')
        if value:
            return True
    return False


def openai_key_present_in_secrets_env(path: str) -> bool:
    return _env_key_present_in_text(_read_text(path), "OPENAI_API_KEY")


def _package_present(venv, package: str) -> Optional[bool]:
    if not venv.checked:
        return None
    return bool(venv.packages.get(package))


def build_state(
    *,
    crm_dir: str = paths.CRM_DIR,
    env: Optional[Dict[str, str]] = None,
    venv=None,
    account_status: str = "unknown",
    account_detail: str = "not checked",
) -> CredentialState:
    env = os.environ if env is None else env
    senv = secrets_env_path(crm_dir)
    gcreds = gmail_credentials_path(crm_dir)
    gtoken = gmail_token_path(crm_dir)
    return CredentialState(
        crm_dir=crm_dir,
        secrets_env_path=senv,
        gmail_credentials_path=gcreds,
        gmail_token_path=gtoken,
        openai_env_present=bool((env.get("OPENAI_API_KEY") or "").strip()),
        openai_secrets_env_present=openai_key_present_in_secrets_env(senv),
        openai_package_present=_package_present(venv, "openai") if venv is not None else None,
        gmail_credentials_present=os.path.isfile(gcreds),
        gmail_token_present=os.path.isfile(gtoken),
        gmail_account_verified=account_status,
        gmail_account_detail=account_detail,
    )


def _set_mode_600(path: str) -> None:
    os.chmod(path, 0o600)


def _key_line(openai_key: str) -> str:
    return "OPENAI_API_KEY=" + shlex.quote(openai_key.strip()) + "\n"


def write_openai_key_to_secrets_env(
    openai_key: str,
    path: str,
    *,
    chmod: Callable[[str, int], None] = os.chmod,
) -> bool:
    """Insert/replace OPENAI_API_KEY in secrets.env, preserving all other entries.

    Returns True when the file was written. The key value is never returned.
    """
    key = (openai_key or "").strip()
    if not key:
        raise ValueError("OPENAI_API_KEY was empty; nothing written")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    old_lines = []
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as fh:
            old_lines = fh.readlines()
    new_lines: List[str] = []
    replaced = False
    for line in old_lines:
        if re.match(r"^\s*(?:export\s+)?OPENAI_API_KEY\s*=", line):
            if not replaced:
                new_lines.append(_key_line(key))
                replaced = True
            continue
        new_lines.append(line)
    if not replaced:
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines[-1] += "\n"
        new_lines.append(_key_line(key))
    with open(path, "w", encoding="utf-8") as fh:
        fh.writelines(new_lines)
    chmod(path, 0o600)
    return True


def prompt_openai_key(prompt_fn: Callable[[str], str]) -> str:
    return (prompt_fn("OPENAI_API_KEY (input hidden; value will not be printed): ") or "").strip()


def _token_json_from_credentials(creds) -> str:
    to_json = getattr(creds, "to_json", None)
    if callable(to_json):
        return to_json()
    if isinstance(creds, dict):
        return json.dumps(creds)
    raise ValueError("OAuth flow returned credentials without to_json()")


def _email_from_jwt(id_token: str) -> str:
    try:
        parts = (id_token or "").split(".")
        if len(parts) < 2:
            return ""
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
        return str(data.get("email") or data.get("emailAddress") or "")
    except Exception:
        return ""


def account_status_from_credentials(creds, expected: str = paths.SENDING_MAILBOX) -> tuple:
    candidates = []
    for attr in ("account_email", "email", "emailAddress"):
        val = getattr(creds, attr, "")
        if val:
            candidates.append(str(val))
    if isinstance(creds, dict):
        for key in ("account_email", "email", "emailAddress"):
            if creds.get(key):
                candidates.append(str(creds[key]))
        if creds.get("id_token"):
            candidates.append(_email_from_jwt(str(creds["id_token"])))
    token = getattr(creds, "id_token", "")
    if token:
        candidates.append(_email_from_jwt(str(token)))
    email = next((c for c in candidates if c), "")
    if not email:
        return "unknown", "OAuth token minted; account email unavailable from credentials"
    if email.strip().lower() == expected.lower():
        return "yes", f"verified as {scanner.mask_recipient(email)}"
    return "no", f"connected account was {scanner.mask_recipient(email)}; expected {expected}"


def _default_flow_factory():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow  # lazy optional dependency
    except Exception as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "google-auth-oauthlib is not installed; install readiness packages before OAuth setup"
        ) from exc
    return InstalledAppFlow


def run_gmail_oauth_flow(
    credentials_path: str,
    token_path: str,
    *,
    no_browser: bool = False,
    flow_factory=None,
    chmod: Callable[[str, int], None] = os.chmod,
) -> tuple:
    """Run Gmail compose OAuth and write the authorized-user token outside the repo."""
    if not os.path.isfile(credentials_path):
        raise FileNotFoundError(MISSING_GMAIL_CREDENTIALS_INSTRUCTION)
    factory = flow_factory or _default_flow_factory()
    flow = factory.from_client_secrets_file(credentials_path, [GMAIL_COMPOSE_SCOPE])
    if no_browser and hasattr(flow, "run_console"):
        creds = flow.run_console()
    else:
        run_local_server = getattr(flow, "run_local_server")
        try:
            creds = run_local_server(port=0, open_browser=not no_browser)
        except TypeError:
            creds = run_local_server(port=0)
    token_json = _token_json_from_credentials(creds)
    scanner.assert_report_safe("token file path only; contents withheld")
    os.makedirs(os.path.dirname(token_path), exist_ok=True)
    with open(token_path, "w", encoding="utf-8") as fh:
        fh.write(token_json)
    chmod(token_path, 0o600)
    return creds, account_status_from_credentials(creds)


def _load_openai_key_from_secrets_env(path: str) -> str:
    # Used only for the explicit --verify-live-openai path; never printed.
    for line in _read_text(path).splitlines():
        m = re.match(r"^\s*(?:export\s+)?OPENAI_API_KEY\s*=\s*(.*)$", line)
        if m:
            return m.group(1).strip().strip("'").strip('"')
    return ""


def run_openai_preflight_if_requested(state: CredentialState, verify_live_openai: bool) -> tuple:
    if not verify_live_openai:
        return "not requested", ""
    key = os.environ.get("OPENAI_API_KEY", "").strip() or _load_openai_key_from_secrets_env(
        state.secrets_env_path
    )
    if not key:
        return "skipped", "OPENAI_API_KEY not present"
    try:
        import sys
        vco_dir = paths.visual_cold_open_dir()
        if vco_dir not in sys.path:
            sys.path.insert(0, vco_dir)
        import image_client  # type: ignore
        client = image_client.GptImageClient(api_key=key)
        result = client.preflight()
        return ("pass" if result.get("ok") else "fail"), scanner.redact_secrets(
            str(result.get("detail", ""))
        )
    except Exception as exc:  # pragma: no cover - depends on optional deps/network
        return "fail", scanner.redact_secrets(str(exc))


def run_setup(
    *,
    crm_dir: str,
    repo_root: str,
    venv=None,
    env: Optional[Dict[str, str]] = None,
    interactive: bool = False,
    write_openai_key: bool = False,
    setup_gmail_oauth: bool = False,
    verify_only: bool = False,
    no_browser: bool = False,
    force_refresh_token: bool = False,
    verify_live_openai: bool = False,
    prompt_fn: Optional[Callable[[str], str]] = None,
    flow_factory=None,
    chmod: Callable[[str, int], None] = os.chmod,
) -> CredentialSetupResult:
    if verify_only and (write_openai_key or setup_gmail_oauth or force_refresh_token):
        state = build_state(crm_dir=crm_dir, env=env, venv=venv)
        return CredentialSetupResult(
            state=state,
            mode="verify-only",
            errors=["--verify-only cannot be combined with write/setup flags"],
        )
    state = build_state(crm_dir=crm_dir, env=env, venv=venv)
    result = CredentialSetupResult(
        state=state,
        mode="verify-only" if verify_only else ("interactive" if interactive else "dry-run"),
    )

    if not write_openai_key:
        result.actions.append("OPENAI_API_KEY: presence check only; no write attempted")
    elif not interactive:
        result.errors.append("--write-openai-key requires --interactive so input can be hidden")
    else:
        prompt_fn = prompt_fn or __import__("getpass").getpass
        key = prompt_openai_key(prompt_fn)
        try:
            write_openai_key_to_secrets_env(key, state.secrets_env_path, chmod=chmod)
            result.wrote_secrets_env = True
            result.chmod_paths.append(state.secrets_env_path)
            result.actions.append("OPENAI_API_KEY written to secrets.env (value withheld)")
        except Exception as exc:
            result.errors.append(scanner.redact_secrets(str(exc)))

    if not setup_gmail_oauth:
        result.actions.append("Gmail OAuth: presence check only; no OAuth flow attempted")
        if not state.gmail_credentials_present:
            result.warnings.append(MISSING_GMAIL_CREDENTIALS_INSTRUCTION)
    else:
        if not state.gmail_credentials_present:
            result.warnings.append(MISSING_GMAIL_CREDENTIALS_INSTRUCTION)
        elif state.gmail_token_present and not force_refresh_token:
            result.actions.append("Gmail OAuth token already present; skipped refresh")
        else:
            try:
                creds, account = run_gmail_oauth_flow(
                    state.gmail_credentials_path,
                    state.gmail_token_path,
                    no_browser=no_browser,
                    flow_factory=flow_factory,
                    chmod=chmod,
                )
                del creds  # never retain credentials beyond this local setup step
                result.wrote_gmail_token = True
                result.chmod_paths.append(state.gmail_token_path)
                result.actions.append("Gmail OAuth token written (contents withheld)")
                state.gmail_account_verified, state.gmail_account_detail = account
            except Exception as exc:
                result.errors.append(scanner.redact_secrets(str(exc)))

    refreshed = build_state(
        crm_dir=crm_dir, env=env, venv=venv,
        account_status=state.gmail_account_verified,
        account_detail=state.gmail_account_detail,
    )
    live_status, live_detail = run_openai_preflight_if_requested(refreshed, verify_live_openai)
    refreshed.openai_live_verified = live_status
    refreshed.openai_live_detail = live_detail
    result.state = refreshed
    return result


def yes_no(value: Optional[bool]) -> str:
    if value is None:
        return "unknown"
    return "yes" if value else "no"


def next_setup_command(state: CredentialState) -> str:
    if not state.openai_present:
        return "python3 outreach/agentic_ops/run.py credentials-setup --interactive --write-openai-key"
    if not state.gmail_credentials_present:
        return "Place ~/.motionx-outreach/gmail_credentials.json, then rerun live-setup-checklist"
    if not state.gmail_token_present:
        return "python3 outreach/agentic_ops/run.py credentials-setup --setup-gmail-oauth"
    return "python3 outreach/agentic_ops/run.py vco-readiness"


def command_not_to_run_yet(state: CredentialState, readiness_ready: bool) -> str:
    if readiness_ready:
        return "(none blocked by readiness; still follow the three-sample-live-drafts handoff)"
    return (
        "python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --sample-only "
        "--live-drafts"
    )


def render_setup_report(result: CredentialSetupResult, readiness_verdict: str = "BLOCKED") -> str:
    st = result.state
    lines = [
        f"# MOTIONX credentials setup - {paths.timestamp()}",
        "",
        "> DRAFT_ONLY setup assistant. This report contains presence/status only. It does "
        "not include OPENAI_API_KEY, Gmail token JSON, refresh_token, client_secret, or "
        "access_token values.",
        "",
        "## Mode",
        f"- Mode: `{result.mode}`",
        f"- Secrets env: `{st.secrets_env_path}`",
        f"- Gmail credentials JSON: `{st.gmail_credentials_path}`",
        f"- Gmail token: `{st.gmail_token_path}`",
        "",
        "## Credential status",
        f"- OPENAI_API_KEY present in CLI env: {yes_no(st.openai_env_present)}",
        f"- OPENAI_API_KEY present in secrets.env: {yes_no(st.openai_secrets_env_present)}",
        f"- openai package present in venv: {yes_no(st.openai_package_present)}",
        f"- Gmail credentials JSON present: {yes_no(st.gmail_credentials_present)}",
        f"- Gmail token present: {yes_no(st.gmail_token_present)}",
        f"- Gmail account verified: {st.gmail_account_verified}",
        f"- Gmail account detail: {st.gmail_account_detail}",
        f"- OpenAI live preflight: {st.openai_live_verified}",
    ]
    if st.openai_live_detail:
        lines.append(f"- OpenAI live preflight detail: {st.openai_live_detail}")
    lines += ["", "## Actions"]
    lines += [f"- {a}" for a in result.actions] or ["- (none)"]
    if result.wrote_secrets_env:
        lines.append("- secrets.env permissions set to 0600")
    if result.wrote_gmail_token:
        lines.append("- gmail_token.json permissions set to 0600")
    if result.warnings:
        lines += ["", "## Warnings"]
        lines += [f"- {w}" for w in result.warnings]
    if result.errors:
        lines += ["", "## Errors"]
        lines += [f"- {e}" for e in result.errors]
    lines += [
        "",
        "## Readiness",
        f"- Current readiness verdict: `{readiness_verdict}`",
        f"- Exact next command: `{next_setup_command(st)}`",
        f"- Exact command NOT to run yet if blocked: `{command_not_to_run_yet(st, readiness_verdict != 'BLOCKED')}`",
        "",
        "## Invariants",
        "- No Gmail draft was created, updated, sent, scheduled, archived, deleted, or labelled.",
        "- No GPT image was generated.",
        "- No CRM file was mutated.",
        "- No secret value was printed in this report.",
        "",
    ]
    return "\n".join(lines)


def render_live_setup_checklist(state: CredentialState, snap) -> str:
    ras = snap.recipient_approval_summary
    readiness_ready = snap.gate.ready
    lines = [
        f"# MOTIONX live setup checklist - {snap.ts}",
        "",
        "> DRAFT_ONLY checklist. Presence/status only; no secrets, no Gmail writes, no "
        "OpenAI image generation, no CRM mutation.",
        "",
        "## Checklist",
        f"- OpenAI key present: {yes_no(state.openai_present)}",
        f"- openai package present in venv: {yes_no(state.openai_package_present)}",
        f"- Gmail credentials JSON present: {yes_no(state.gmail_credentials_present)}",
        f"- Gmail token present: {yes_no(state.gmail_token_present)}",
        f"- Gmail account verified: {state.gmail_account_verified}",
        f"- top-3 recipient approval recorded: {yes_no(ras.get('recorded'))}",
        f"- readiness verdict: `{snap.gate.verdict}`",
        "",
        "## Next command",
        f"- `{next_setup_command(state)}`",
        "",
        "## Do not run yet if blocked",
        f"- `{command_not_to_run_yet(state, readiness_ready)}`",
        "",
        "## Current blockers",
    ]
    if snap.gate.blockers:
        lines += [f"- `{b}`" for b in snap.gate.blockers]
    else:
        lines.append("- none")
    lines += [
        "",
        "## Invariants",
        "- Checklist generation did not prompt for secrets.",
        "- Checklist generation did not call Gmail or OpenAI.",
        "- Checklist generation did not mutate CRM.",
        "",
    ]
    return "\n".join(lines)
