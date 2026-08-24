#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the agentic-ops automation layer. Pure stdlib. NO real Gmail/OpenAI/CRM.

Run: python3 outreach/tests/test_agentic_ops.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ops_bootstrap as boot  # noqa: E402

import paths           # noqa: E402
import scanner         # noqa: E402
import collectors      # noqa: E402
import engine          # noqa: E402
import handoffs        # noqa: E402
import ledger          # noqa: E402
import approvals       # noqa: E402
import credentials     # noqa: E402
import render          # noqa: E402
import run as cli      # noqa: E402

REPO_ROOT = boot.REPO_ROOT
OPS_DIR = os.path.join(REPO_ROOT, "outreach", "agentic_ops")


# ── helpers ─────────────────────────────────────────────────────────────────────
def _snap(crm_dir, *, openai=False, gmail=False, approved=False):
    boot.seed_crm(crm_dir)
    venv_dir = boot.fake_venv(crm_dir)
    if gmail:
        with open(os.path.join(crm_dir, "gmail_token.json"), "w") as fh:
            fh.write("{}")   # existence only; contents never read by collectors
    if approved:
        approvals.write_batch32_top3_approval(crm_dir, REPO_ROOT, "2026-01-01_0000")
    env = {"OPENAI_API_KEY": "sk-testtesttesttest"} if openai else {}
    return engine.build_snapshot(
        repo_root=REPO_ROOT, crm_dir=crm_dir, env=env,
        venv_dir=venv_dir, run_pip=False,
    )


# ── 1. status report generation with fake fixture files ─────────────────────────
def test_status_report_generation_with_fixtures():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        text = render.render_status_md(snap)
        assert "MOTIONX agentic-ops status" in text
        assert "## Repo" in text and "## Auth & dependency readiness" in text
        assert "Highest-value next action" in text
        # writes under the temp reports dir (outside repo)
        path = render.write_report(
            text, os.path.join(snap.reports_dir, f"motionx_ops_status_{snap.ts}.md"),
            REPO_ROOT)
        assert os.path.isfile(path)


# ── 2 & 3. missing creds produce the exact blocker tokens ───────────────────────
def test_missing_openai_key_blocks_gpt_image_2():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d, openai=False, gmail=True)
        assert collectors.BLOCKED_ON_GPT_IMAGE_2_ACCESS in snap.gate.blockers
        assert not snap.gate.ready


def test_missing_gmail_token_blocks_draft_access():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d, openai=True, gmail=False)
        assert collectors.BLOCKED_ON_GMAIL_DRAFT_ACCESS in snap.gate.blockers
        assert not snap.gate.ready


def test_both_creds_present_makes_ready():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d, openai=True, gmail=True, approved=True)
        assert snap.gate.ready, snap.gate.failed
        assert snap.gate.verdict == collectors.READY_FOR_3_SAMPLE_LIVE_DRAFTS


def test_creds_present_but_recipient_approval_pending_blocks_readiness():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d, openai=True, gmail=True, approved=False)
        assert not snap.gate.ready
        failed = {g.name for g in snap.gate.failed}
        assert "top3_recipient_approval_recorded" in failed
        assert collectors.BLOCKED_ON_GPT_IMAGE_2_ACCESS not in snap.gate.blockers
        assert collectors.BLOCKED_ON_GMAIL_DRAFT_ACCESS not in snap.gate.blockers


def test_blocker_constants_match_vco_config():
    import config as vco_config  # visual_cold_open source of truth
    assert collectors.BLOCKED_ON_GPT_IMAGE_2_ACCESS == \
        vco_config.STATUS["BLOCKED_ON_GPT_IMAGE_2_ACCESS"]
    assert collectors.BLOCKED_ON_GMAIL_DRAFT_ACCESS == \
        vco_config.STATUS["BLOCKED_ON_GMAIL_DRAFT_ACCESS"]


# ── 4. recipient CSV parsing for Northwind / Trailpoint / Fieldmark ─────────────────────
def test_recipient_csv_parsing_matador_vssl_fieldmark():
    with tempfile.TemporaryDirectory() as d:
        reports = boot.seed_crm(d)
        path = os.path.join(reports, "batch32_top3_recipient_review_2026-01-01_0000.csv")
        parsed = collectors.parse_recipient_review(path)
        companies = {r["company"] for r in parsed["recipients"]}
        assert {"Northwind Gear", "Trailpoint", "Fieldmark"} <= companies
        by = {r["company"]: r for r in parsed["recipients"]}
        assert by["Northwind Gear"]["email"] == "marketing@northwindgear.example"
        assert by["Trailpoint"]["email"] == "support@trailpoint.example"
        assert by["Fieldmark"]["email"] == "info@fieldmark.example"
        assert all(r["has_verified_email"] for r in parsed["recipients"])


# ── 5. Trailpoint support mailbox flagged customer-experience oriented ────────────────
def test_vssl_support_flagged_customer_experience():
    row = {"company": "Trailpoint", "domain": "trailpoint.example",
           "recipient_email": "support@trailpoint.example",
           "recipient_fit": "customer_experience_only_review_recommended",
           "recipient_review_status": "REVIEW_ONLY_PENDING_CHARLES_APPROVAL",
           "decision": "APPROVE"}
    rec = collectors.classify_recipient(row)
    assert rec["customer_experience_oriented"] is True
    # Marketing/press mailbox is NOT flagged CX.
    matador = collectors.classify_recipient({
        "company": "Northwind Gear", "recipient_email": "marketing@northwindgear.example",
        "recipient_fit": "marketing_press_inquiries",
        "recipient_review_status": "REVIEW_ONLY_PENDING_CHARLES_APPROVAL", "decision": "APPROVE"})
    assert matador["customer_experience_oriented"] is False


def test_vssl_flag_appears_in_batch32_report_and_pending_approval():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        text = render.render_batch32_status_md(snap)
        assert "Customer-Experience mailbox" in text
        assert "Charles approval NOT recorded" in text   # no approval note present
        assert "APPROVE: 2" in text and "MAYBE: 1" in text and "REJECT: 0" in text


def test_agents_md_files_codex_safe():
    root_agents = os.path.join(REPO_ROOT, "AGENTS.md")
    outreach_agents = os.path.join(REPO_ROOT, "outreach", "AGENTS.md")
    for path in (root_agents, outreach_agents):
        assert os.path.isfile(path), f"missing {path}"
        text = open(path, encoding="utf-8").read()
        for tok in ("DRAFT_ONLY", "Do not send", "secrets", "outreach/self-improvement.md"):
            assert tok in text, f"{os.path.basename(path)} missing {tok!r}"
        assert "messages.send" in text and "drafts.send" in text


def test_approval_artifact_parsed_and_reflected_in_reports_and_readiness():
    with tempfile.TemporaryDirectory() as d:
        written = approvals.write_batch32_top3_approval(d, REPO_ROOT, "2026-01-01_0000")
        assert os.path.isfile(written["artifact"]) and os.path.isfile(written["note"])
        snap = _snap(d, openai=True, gmail=True, approved=False)
        ras = snap.recipient_approval_summary
        assert ras["recorded"] is True and ras["approved"] == 3 and ras["pending"] == 0
        assert snap.gate.ready, snap.gate.failed
        batch = render.render_batch32_status_md(snap)
        ready = render.render_vco_readiness_md(snap)
        assert "Top-3 recipient approval gate: PASS" in batch
        assert "Charles approved a technical sample" in batch
        assert "approval recorded" in ready
        assert "support@trailpoint.example" not in batch
        assert "s***@trailpoint.example" in batch


# ── 6. handoff output uses the exact Codex handoff format ───────────────────────
def test_handoff_exact_format_all_tasks():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        for task in handoffs.TASKS:
            text = handoffs.render_handoff(task, snap)
            idx = -1
            for label in handoffs.FIELDS:
                pos = text.find(label + ":")
                assert pos != -1, f"{task}: missing field {label!r}"
                assert pos > idx, f"{task}: field {label!r} out of order"
                idx = pos


def test_required_handoff_tasks_available():
    required = {
        "live-setup",
        "three-sample-live-drafts",
        "credentials-setup",
        "batch32-normalized-draft-dry-run",
        "batch32-visual-dry-run",
        "batch32-full-live-drafts-after-review",
        "crm-gmail-reconcile",
        "source-next-20",
        "one-paste-chatgpt-visual-pack",
        "collect-chatgpt-downloads",
        "manual-visual-preview-with-collected-images",
        "manual-visual-prompt-pack",
        "manual-visual-import",
        "manual-visual-live-drafts",
    }
    assert required <= set(handoffs.TASKS)


def test_handoff_execute_block_never_says_send():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        for task in handoffs.TASKS:
            text = handoffs.build_handoff(task, snap).render()
            execute = scanner._extract_execute_block(text)
            assert scanner.find_send_as_action(execute) == [], \
                f"{task}: execute block contains a send action"
            # 'Codex must NOT' legitimately contains 'send' — ensure it's outside execute.
            assert "must NOT" not in execute


# ── 7. no secret-looking values appear in generated reports ─────────────────────
def test_no_secrets_in_generated_reports():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d, openai=True, gmail=True, approved=True)
        for renderer in (render.render_status_md, render.render_vco_readiness_md,
                         render.render_batch32_status_md):
            text = renderer(snap)
            assert not scanner.contains_secret_material(text)
            assert not scanner.contains_gmail_token_content(text)
            assert not scanner.contains_openai_key_assignment(text)
            scanner.assert_report_safe(text)   # must not raise
        context = ledger.render_context_pack_md(snap)
        ledger_text = ledger.render_ledger_md(ledger.build_ledger_entry(snap))
        for text in (context, ledger_text):
            assert not scanner.contains_secret_material(text)
            assert not scanner.contains_gmail_token_content(text)
            assert not scanner.contains_openai_key_assignment(text)
            assert "support@trailpoint.example" not in text
            assert "marketing@northwindgear.example" not in text
            scanner.assert_handoff_safe(text)
        cstate = credentials.build_state(crm_dir=d, venv=snap.venv, env={})
        setup = credentials.CredentialSetupResult(state=cstate, mode="dry-run")
        cred_report = credentials.render_setup_report(setup, snap.gate.verdict)
        checklist = credentials.render_live_setup_checklist(cstate, snap)
        for text in (cred_report, checklist):
            assert not scanner.contains_secret_material(text)
            assert not scanner.contains_gmail_token_content(text)
            assert not scanner.contains_openai_key_assignment(text)
            scanner.assert_report_safe(text)


def test_scanner_rejects_injected_secret_and_token():
    assert scanner.contains_secret_material("key sk-abcdef0123456789")
    assert scanner.contains_gmail_token_content('{"refresh_token": "1//xyz"}')
    assert scanner.contains_gmail_token_content('"client_secret": "GOCSPX-abc"')
    assert scanner.contains_gmail_token_content(
        '{"installed": {"auth_uri": "https://accounts.google.com/o/oauth2/auth"}}'
    )
    try:
        scanner.assert_report_safe("leaked sk-abcdef0123456789012345")
        assert False, "expected ScanError"
    except scanner.ScanError:
        pass


# ── 8. no Gmail write/send actions are invoked ──────────────────────────────────
def test_scanner_blocks_send_as_execution_action():
    bad = ("Objective: x\nCodex should execute:\n  1. send email to the prospect\n"
           "Codex must NOT:\n  - nothing\n")
    res = scanner.scan_handoff(bad)
    assert not res.ok and any(f.kind == "send-as-action" for f in res.findings)
    try:
        scanner.assert_handoff_safe(bad)
        assert False, "expected ScanError"
    except scanner.ScanError:
        pass


def test_send_prohibition_in_must_not_is_allowed():
    ok = ("Objective: x\nCodex should execute:\n  1. create draft only (drafts.create)\n"
          "Codex must NOT:\n  - send email; drafts.send; messages.send\n")
    scanner.assert_handoff_safe(ok)   # must NOT raise


def test_ops_source_invokes_no_gmail_send_path():
    """Static audit: the agentic-ops package must not WIRE UP any Gmail API.

    We look for genuine invocation signatures (a Gmail service, the vco Gmail backend,
    an .execute() call) — NOT string mentions like "drafts.send", which appear
    legitimately as scanner detection patterns and as handoff prohibition text.
    """
    forbidden = ("googleapiclient", "gmail_draft", "GmailBackend", ".users()",
                 "build('gmail'", 'build("gmail"', ".execute()", "gmail_send")
    for name in os.listdir(OPS_DIR):
        if not name.endswith(".py"):
            continue
        with open(os.path.join(OPS_DIR, name), encoding="utf-8") as fh:
            src = fh.read()
        for tok in forbidden:
            assert tok not in src, f"{name} wires up a Gmail API path ({tok!r})"


def test_assert_not_send_guard_holds():
    for op in ("messages.send", "drafts.send", "messages.insert", "drafts.trash"):
        try:
            scanner.assert_not_send(op)
            assert False, f"{op} should be forbidden"
        except scanner.SendForbiddenError:
            pass


# ── 9. hook templates exist but are not auto-enabled ────────────────────────────
def test_hook_templates_exist_but_not_enabled():
    ht = os.path.join(OPS_DIR, "hook_templates")
    for f in ("agentic_ops_guard.py", "settings.hooks.template.json", "HOOKS-RUNBOOK.md"):
        assert os.path.isfile(os.path.join(ht, f)), f"missing hook template {f}"
    # template JSON is inert (notice key + placeholder path, not a live config)
    with open(os.path.join(ht, "settings.hooks.template.json"), encoding="utf-8") as fh:
        tpl = fh.read()
    assert "_TEMPLATE_NOTICE" in tpl and "/ABSOLUTE/PATH/TO/" in tpl
    # no committed settings.json anywhere in the repo wires the guard in
    for base, _dirs, files in os.walk(os.path.join(REPO_ROOT, ".claude")):
        for f in files:
            if f.endswith(".json") and "settings" in f:
                with open(os.path.join(base, f), encoding="utf-8") as fh:
                    assert "agentic_ops_guard" not in fh.read(), \
                        f"{f} auto-enables the guard hook"


# ── 10. CLI writes reports OUTSIDE the repo ─────────────────────────────────────
def test_write_report_refuses_inside_repo():
    inside = os.path.join(REPO_ROOT, "outreach", "reports", "x.md")
    try:
        render.write_report("hi", inside, REPO_ROOT)
        assert False, "expected refusal to write inside repo"
    except ValueError:
        pass


def test_cli_status_writes_report_outside_repo():
    with tempfile.TemporaryDirectory() as d:
        boot.seed_crm(d)
        boot.fake_venv(d)
        rc = cli.main(["status", "--crm-dir", d, "--repo-root", REPO_ROOT, "--no-pip"])
        assert rc == 0
        reports = os.path.join(d, "reports")
        produced = [f for f in os.listdir(reports) if f.startswith("motionx_ops_status_")]
        assert produced, "no status report written"
        for f in produced:
            full = os.path.join(reports, f)
            assert not paths.is_within(full, REPO_ROOT)   # outside the repo
            assert paths.is_within(full, d)


def test_ledger_and_context_pack_write_outside_repo():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d, approved=True)
        out = ledger.write_ledger(snap)
        ctx = ledger.write_context_pack(snap)
        assert os.path.isfile(out["jsonl"]) and os.path.isfile(out["report"])
        assert os.path.isfile(ctx)
        for full in (out["jsonl"], out["report"], ctx):
            assert not paths.is_within(full, REPO_ROOT)
            assert paths.is_within(full, d)
            text = open(full, encoding="utf-8").read()
            assert not scanner.contains_secret_material(text)
            assert not scanner.contains_gmail_token_content(text)
            assert "support@trailpoint.example" not in text


def test_credentials_setup_dry_run_writes_no_secrets():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        result = credentials.run_setup(crm_dir=d, repo_root=REPO_ROOT, venv=snap.venv,
                                       env={}, verify_only=True)
        assert result.ok
        assert not result.wrote_secrets_env
        assert not result.wrote_gmail_token
        assert not os.path.exists(os.path.join(d, "secrets.env"))
        text = credentials.render_setup_report(result, snap.gate.verdict)
        scanner.assert_report_safe(text)
        assert "OPENAI_API_KEY=" not in text


def test_openai_key_write_preserves_postal_and_dedupes_and_chmods():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "secrets.env")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("MOTIONX_POSTAL_ADDRESS='123 Test St'\n")
            fh.write("OPENAI_API_KEY=old\n")
            fh.write("OPENAI_API_KEY=older\n")
        credentials.write_openai_key_to_secrets_env("sk-testtesttesttest", path)
        text = open(path, encoding="utf-8").read()
        assert "MOTIONX_POSTAL_ADDRESS='123 Test St'" in text
        assert text.count("OPENAI_API_KEY=") == 1
        assert credentials.openai_key_present_in_secrets_env(path)
        assert oct(os.stat(path).st_mode & 0o777) == "0o600"


def test_credentials_setup_write_requires_interactive():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        result = credentials.run_setup(crm_dir=d, repo_root=REPO_ROOT, venv=snap.venv,
                                       write_openai_key=True, interactive=False)
        assert not result.ok
        assert any("--write-openai-key requires --interactive" in e for e in result.errors)
        assert not os.path.exists(os.path.join(d, "secrets.env"))


def test_credentials_setup_interactive_hidden_write_uses_prompt_function():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        result = credentials.run_setup(
            crm_dir=d, repo_root=REPO_ROOT, venv=snap.venv,
            write_openai_key=True, interactive=True,
            prompt_fn=lambda prompt: "sk-testtesttesttest",
        )
        assert result.ok
        assert result.wrote_secrets_env
        assert credentials.openai_key_present_in_secrets_env(os.path.join(d, "secrets.env"))


def test_missing_gmail_credentials_message_and_token_detection():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        result = credentials.run_setup(crm_dir=d, repo_root=REPO_ROOT, venv=snap.venv,
                                       setup_gmail_oauth=True)
        assert result.ok
        assert credentials.MISSING_GMAIL_CREDENTIALS_INSTRUCTION in result.warnings
        assert not result.state.gmail_credentials_present
        assert not result.state.gmail_token_present
        token = os.path.join(d, "gmail_token.json")
        with open(token, "w", encoding="utf-8") as fh:
            fh.write("{}")
        state = credentials.build_state(crm_dir=d, venv=snap.venv)
        assert state.gmail_token_present


class _FakeCreds:
    account_email = "charles@madebymotionx.com"

    def to_json(self):
        return '{"token": "redacted-test-token"}'


class _FakeFlow:
    used_no_browser = False

    @classmethod
    def from_client_secrets_file(cls, path, scopes):
        assert scopes == [credentials.GMAIL_COMPOSE_SCOPE]
        return cls()

    def run_local_server(self, port=0, open_browser=True):
        self.used_no_browser = not open_browser
        return _FakeCreds()


def test_oauth_flow_mocked_writes_token_and_verifies_account():
    with tempfile.TemporaryDirectory() as d:
        creds_path = os.path.join(d, "gmail_credentials.json")
        token_path = os.path.join(d, "gmail_token.json")
        with open(creds_path, "w", encoding="utf-8") as fh:
            fh.write('{"installed": {"client_id": "test"}}')
        creds, account = credentials.run_gmail_oauth_flow(
            creds_path, token_path, no_browser=True, flow_factory=_FakeFlow
        )
        assert isinstance(creds, _FakeCreds)
        assert account[0] == "yes"
        assert os.path.isfile(token_path)
        assert oct(os.stat(token_path).st_mode & 0o777) == "0o600"


def test_live_setup_checklist_writes_outside_repo():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d, approved=True)
        state = credentials.build_state(crm_dir=d, venv=snap.venv, env={})
        text = credentials.render_live_setup_checklist(state, snap)
        path = render.write_report(
            text, os.path.join(d, "reports", f"live_setup_checklist_{snap.ts}.md"),
            REPO_ROOT,
        )
        assert os.path.isfile(path)
        assert not paths.is_within(path, REPO_ROOT)
        assert "Gmail account verified: unknown" in text
        assert "readiness verdict" in text


def test_cli_all_commands_smoke_no_write_in_repo():
    with tempfile.TemporaryDirectory() as d:
        boot.seed_crm(d)
        boot.fake_venv(d)
        for argv in (
            ["status"], ["vco-readiness"], ["batch32-status"], ["ledger"],
            ["context-pack"], ["credentials-setup", "--verify-only"],
            ["live-setup-checklist"], ["daily-report"],
            ["handoff", "--target", "codex", "--task", "live-setup"],
            ["handoff", "--target", "codex", "--task", "credentials-setup"],
            ["handoff", "--target", "codex", "--task", "one-paste-chatgpt-visual-pack"],
            ["handoff", "--target", "codex", "--task", "collect-chatgpt-downloads"],
        ):
            rc = cli.main(argv + ["--crm-dir", d, "--repo-root", REPO_ROOT, "--no-pip"])
            assert rc == 0, f"{argv} returned {rc}"
        # nothing was written inside the repo tree
        for base, _dirs, files in os.walk(os.path.join(REPO_ROOT, "outreach")):
            for f in files:
                assert not f.startswith(("motionx_ops_status_", "vco_readiness_",
                                         "batch32_status_", "motionx_daily_ops_")), \
                    f"report leaked into repo: {f}"


def test_record_approval_cli_writes_only_outside_repo_and_enables_gate():
    with tempfile.TemporaryDirectory() as d:
        boot.seed_crm(d)
        boot.fake_venv(d)
        rc = cli.main(["record-batch32-top3-approval", "--charles-approved-top3",
                       "--crm-dir", d, "--repo-root", REPO_ROOT, "--no-pip"])
        assert rc == 0
        assert os.path.isdir(os.path.join(d, "approvals"))
        assert os.path.isfile(os.path.join(d, "charles_recipient_approvals.txt"))
        snap = engine.build_snapshot(repo_root=REPO_ROOT, crm_dir=d, env={},
                                     venv_dir=os.path.join(d, "venvs", "visual-cold-open"),
                                     run_pip=False)
        assert snap.recipient_approval_summary["recorded"] is True
        assert paths.is_within(os.path.join(d, "approvals"), d)
        assert not paths.is_within(os.path.join(d, "approvals"), REPO_ROOT)


# ── 11. pre-existing dirty outreach/self-improvement.md is preserved ────────────
def test_self_improvement_recognized_and_bucketed():
    from collectors import RepoState
    rs = RepoState(root=REPO_ROOT, branch="b", head="h", head_subject="s",
                   dirty=[("M", "outreach/self-improvement.md"), ("??", "outreach/agentic_ops/")])
    assert rs.preexisting_dirty_present
    assert ("M", "outreach/self-improvement.md") not in rs.other_dirty
    assert paths.PREEXISTING_DIRTY == "outreach/self-improvement.md"


def test_cli_run_never_touches_self_improvement_md():
    si = os.path.join(REPO_ROOT, "outreach", "self-improvement.md")
    if not os.path.exists(si):   # present in worktree; guard if layout changes
        return
    before = os.stat(si).st_mtime_ns
    with tempfile.TemporaryDirectory() as d:
        boot.seed_crm(d)
        boot.fake_venv(d)
        for argv in (["status"], ["batch32-status"], ["daily-report"]):
            cli.main(argv + ["--crm-dir", d, "--repo-root", REPO_ROOT, "--no-pip"])
    assert os.stat(si).st_mtime_ns == before, "self-improvement.md was modified"


# ── extra coverage: parsing counts + masking + outside-repo handoffs ────────────
def test_batch32_counts_and_crosscheck():
    with tempfile.TemporaryDirectory() as d:
        reports = boot.seed_crm(d, n_sourced=5, approve=3, maybe=2, reject=1)
        sourcing = collectors.parse_sourcing_csv(
            os.path.join(reports, "batch32_sourcing_candidates_2026-01-01_0000.csv"))
        approval = collectors.parse_approval_packet(
            os.path.join(reports, "batch32_candidate_approval_packet_2026-01-01_0000.md"))
        assert sourcing["total"] == 5
        assert approval["approve"] == 3 and approval["maybe"] == 2 and approval["reject"] == 1
        assert approval["counts_consistent"] is True


def test_reports_mask_recipient_local_parts():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        text = render.render_batch32_status_md(snap)
        assert "support@trailpoint.example" not in text      # full local part never shown
        assert "s***@trailpoint.example" in text
        assert "marketing@northwindgear.example" not in text


def test_handoffs_written_outside_repo_and_scanned():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap(d)
        for task in handoffs.TASKS:
            text = handoffs.render_handoff(task, snap)
            p = os.path.join(snap.handoffs_dir, f"{task}_{snap.ts}.txt")
            render.write_handoff(text, p, REPO_ROOT)
            assert os.path.isfile(p) and not paths.is_within(p, REPO_ROOT)


# ── review-fix regressions ──────────────────────────────────────────────────────
def _snap_no_recipient_csv(crm_dir, *, openai=True, gmail=True):
    """Both creds present + venv, but NO recipient-review CSV -> a non-credential gate
    fails with ready=False and blockers==[] (the review-found contradiction case)."""
    reports = os.path.join(crm_dir, "reports")
    os.makedirs(reports, exist_ok=True)
    boot.write_sourcing_csv(reports)
    boot.write_approval_packet(reports)
    venv_dir = boot.fake_venv(crm_dir)
    if gmail:
        with open(os.path.join(crm_dir, "gmail_token.json"), "w") as fh:
            fh.write("{}")
    env = {"OPENAI_API_KEY": "sk-testtesttesttest"} if openai else {}
    return engine.build_snapshot(repo_root=REPO_ROOT, crm_dir=crm_dir, env=env,
                                 venv_dir=venv_dir, run_pip=False)


def test_non_credential_block_never_recommends_creating_drafts():
    with tempfile.TemporaryDirectory() as d:
        snap = _snap_no_recipient_csv(d)
        assert not snap.gate.ready and snap.gate.blockers == []
        na = snap.next_action
        assert "non-credential" in na and "three-sample" not in na
        # daily-report must NOT emit a three-sample-live-drafts handoff while BLOCKED
        rc = cli.main(["daily-report", "--crm-dir", d, "--repo-root", REPO_ROOT, "--no-pip"])
        assert rc == 0
        hd = os.path.join(d, "handoffs")
        made = os.listdir(hd) if os.path.isdir(hd) else []
        assert not any("three-sample-live-drafts" in f for f in made), made
        daily = render.render_daily_md(snap, {})
        assert "Nothing blocking" not in daily
        assert "recipient_review_present" in daily


def test_scanner_flags_messages_insert_execute_action():
    bad = ("Objective: x\nCodex should execute:\n"
           "  1. Use svc.users().messages().insert to backfill the sent copy.\n"
           "Codex must NOT:\n  - x\n")
    execute = scanner._extract_execute_block(bad)
    assert scanner.find_send_as_action(execute), "messages.insert must be flagged"
    try:
        scanner.assert_handoff_safe(bad)
        assert False, "expected ScanError"
    except scanner.ScanError:
        pass


def test_guard_blocks_fluent_gmail_send_form():
    G = os.path.join(REPO_ROOT, "outreach", "agentic_ops", "hook_templates",
                     "agentic_ops_guard.py")
    for cmd in ("svc.users().messages().send(userId='me', body=b).execute()",
                "gmail.users().drafts().send(userId='me')",
                "svc.users().messages().insert(userId='me')"):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}})
        p = subprocess.run([sys.executable, G], input=payload, capture_output=True, text=True)
        assert p.returncode == 2, f"fluent send not blocked: {cmd} -> rc={p.returncode}"


def test_approvals_note_email_token_is_masked_in_report():
    with tempfile.TemporaryDirectory() as d:
        boot.seed_crm(d)
        with open(os.path.join(d, "charles_recipient_approvals.txt"), "w") as fh:
            fh.write("support@trailpoint.example\ntrailpoint.example\n")
        venv = boot.fake_venv(d)
        snap = engine.build_snapshot(repo_root=REPO_ROOT, crm_dir=d, env={},
                                     venv_dir=venv, run_pip=False)
        text = render.render_batch32_status_md(snap)
        assert "Approvals recorded for:" in text
        assert "support@trailpoint.example" not in text     # email token masked
        assert "s***@trailpoint.example" in text
        assert "trailpoint.example" in text                 # domain token kept as-is


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
