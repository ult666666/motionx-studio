#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end CLI tests with injected fakes. NO real API/Gmail calls.

Proves the core safety contract:
  * dry-run never mutates Gmail
  * live-drafts requires the explicit flag
  * retrofit requires --allow-update-existing-drafts
  * --visual-cold-open is required; gpt-image-2 downgrade is rejected
  * a live create attaches the image and verifies draft-only

Run: python3 outreach/tests/test_visual_cli.py
"""
import base64
import csv
import email
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _vco_bootstrap  # noqa: E402
import run_batch  # noqa: E402
import config as vco_config  # noqa: E402
import safety  # noqa: E402
import copy_integration as ci  # noqa: E402
import image_client as ic  # noqa: E402


class WrongAccountBackend(_vco_bootstrap.FakeGmailBackend):
    def verify_account(self):
        raise safety.WrongAccountError("connected as someoneelse@gmail.com")


class RegenFakeClient:
    """Fails QA (bad bytes) for the first `bad_first` calls, then returns a valid PNG."""
    def __init__(self, bad_first=1):
        self.calls = []
        self.bad_first = bad_first
        self.good = _vco_bootstrap.make_png()

    def preflight(self):
        return {"ok": True, "detail": "ok"}

    def generate(self, prompt, size="1536x1024", quality="medium", image_format="png"):
        self.calls.append(prompt)
        data = b"ERR" if len(self.calls) <= self.bad_first else self.good
        return ic.GeneratedImage(data=data, model="gpt-image-2", size=size,
                                 quality=quality, image_format=image_format)

ITEM1 = {
    "lead_id": "L0001", "business_name": "Basalt Vessels", "prospect_name": "Basalt Vessels",
    "recipient_email": "team@example.com", "recipient_type": "generic",
    "recipient_confidence": "MEDIUM", "greeting": "Hi Basalt Vessels team,",
    "verified_observation": "the homepage centers a single hand-blown pint glass",
    "concise_interpretation": "the product carries the page",
    "central_idea": "a short film could open that same world before the launch page",
    "motionx_positioning_sentence": "I'm Charles, founder of MOTIONX.",
    "cta": "Worth a quick conversation?", "selected_offer": "Product Film",
    "subject": "Glass in motion", "optional_price": 399,
    "category": "consumer product brand", "preflight_status": "PASS",
    "proposed_creative_direction": "a slow pour revealing the mountain in the base",
    "specific_opportunity": "a launch page reusing the film's opening frame",
}
ITEM2 = dict(ITEM1, lead_id="L0002", business_name="Second Co",
             recipient_email="hi@second.example", subject="Second idea")


def _write_source(d, items):
    path = os.path.join(d, "_batch99_drafts.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"batch": "99", "items": items}, fh)
    return path


def _dirs(d):
    return ["--report-path", os.path.join(d, "reports"),
            "--asset-dir", os.path.join(d, "assets")]


def test_visual_flag_required():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        rc = run_batch.main(["--prospect-source", src] + _dirs(d),
                            image_client=_vco_bootstrap.FakeImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 2, "missing --visual-cold-open must exit 2"


def test_model_downgrade_rejected():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        rc = run_batch.main(["--visual-cold-open", "--image-model", "dall-e-3",
                             "--prospect-source", src] + _dirs(d),
                            image_client=_vco_bootstrap.FakeImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 2, "model downgrade must be rejected"


def test_dry_run_does_not_touch_gmail():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1, ITEM2])
        gm = _vco_bootstrap.FakeGmailBackend()
        rc = run_batch.main(["--visual-cold-open", "--prospect-source", src,
                             "--batch-id", "batch99-visual"] + _dirs(d),
                            image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        assert rc == 0
        assert gm.created == [] and gm.updated == [], "dry-run must not create/update drafts"
        report = os.path.join(d, "reports", "batch99-visual_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 2
        assert all(r["sent_or_scheduled"] == "no" for r in rows)
        assert all(r["gmail_draft_confirmed"] == "no" for r in rows)
        # no attachment language in a no-image dry-run
        assert all(r["body_says_attached"] == "no" for r in rows)


def test_dry_run_with_images_generates_but_no_gmail():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend()
        os.environ["OPENAI_API_KEY"] = "sk-test-not-used-by-fake"
        try:
            rc = run_batch.main(["--visual-cold-open", "--generate-images-in-dry-run",
                                 "--prospect-source", src, "--batch-id", "b"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert gm.created == [] and gm.updated == [], "dry-run must not write Gmail even with images"
        # a raw MIME preview was written outside the repo
        assets = os.path.join(d, "assets")
        raws = [f for f in os.listdir(assets) if f.endswith(".raw.b64url")]
        assert raws, "expected a raw MIME preview file"


def test_live_create_attaches_and_verifies_draft_only():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        os.environ["OPENAI_API_KEY"] = "sk-test-not-used-by-fake"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "MOTIONX Test Mailbox, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert len(gm.created) == 1, "live create must create exactly one draft"
        assert gm.updated == []
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            row = list(csv.DictReader(fh))[0]
        assert row["visual_status"] == "attached"
        assert row["body_says_attached"] == "yes"
        assert row["gmail_draft_confirmed"] == "yes"
        assert row["sent_or_scheduled"] == "no"


def test_retrofit_requires_allow_flag():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        manifest = os.path.join(d, "man.json")
        with open(manifest, "w", encoding="utf-8") as fh:
            json.dump({"items": [{"lead_id": "L0001", "draft_id": "r777"}]}, fh)
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            # without --allow-update-existing-drafts → preflight blocks, no update
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--source", "existing-gmail-drafts",
                                 "--prospect-source", src, "--manifest", manifest,
                                 "--batch-id", "b", "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
            assert rc == 1, "retrofit without allow flag must fail preflight"
            assert gm.updated == [], "no update without the allow flag"
        finally:
            os.environ.pop("OPENAI_API_KEY", None)


def test_retrofit_updates_existing_draft_with_allow_flag():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        manifest = os.path.join(d, "man.json")
        with open(manifest, "w", encoding="utf-8") as fh:
            json.dump({"items": [{"lead_id": "L0001", "draft_id": "r777"}]}, fh)
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--source", "existing-gmail-drafts",
                                 "--prospect-source", src, "--manifest", manifest,
                                 "--allow-update-existing-drafts",
                                 "--batch-id", "b", "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert gm.updated and gm.updated[0][0] == "r777", "must update the existing draft id"
        assert gm.created == [], "retrofit must not create a new draft"


def test_retrofit_missing_draft_id_does_not_create_duplicate():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])  # lead L0001
        manifest = os.path.join(d, "man.json")
        # manifest maps a DIFFERENT lead -> so L0001 has no known draft id
        with open(manifest, "w", encoding="utf-8") as fh:
            json.dump({"items": [{"lead_id": "L9999", "draft_id": "rXXX"}]}, fh)
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--source", "existing-gmail-drafts",
                                 "--prospect-source", src, "--manifest", manifest,
                                 "--allow-update-existing-drafts",
                                 "--batch-id", "b", "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert gm.created == [], "must NOT create a duplicate when no draft id is known"
        assert gm.updated == [], "must NOT update — no draft id for this lead"
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            row = list(csv.DictReader(fh))[0]
        assert row["draft_action"] == "skipped"
        assert "retrofit" in row["notes"].lower()
        # status lands in the dedicated activity log
        act = os.path.join(d, "reports", "visual-cold-open-activity-log.csv")
        with open(act, newline="", encoding="utf-8") as fh:
            arow = list(csv.DictReader(fh))[0]
        assert arow["status"] == "NEEDS_CHARLES_REVIEW"


def test_qa_failure_blocks_attachment_and_gmail():
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(fail_qa=True),
                                gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert gm.created == [] and gm.updated == [], "QA failure must block any Gmail write"
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            row = list(csv.DictReader(fh))[0]
        assert row["visual_status"] == "failed_qa"
        assert row["body_says_attached"] == "no"


def test_fabrication_blocks_before_any_generation_or_draft():
    # finding [13]
    with tempfile.TemporaryDirectory() as d:
        bad = dict(ITEM1, verified_observation="an award-winning mug trusted by thousands")
        src = _write_source(d, [bad])
        gm = _vco_bootstrap.FakeGmailBackend()
        fake = _vco_bootstrap.FakeImageClient()
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=fake, gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert fake.calls == [], "no image should be generated for a fabricated item"
        assert gm.created == [] and gm.updated == []
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            row = list(csv.DictReader(fh))[0]
        assert row["fabrication_check_passed"] == "no"
        assert row["draft_action"] == "blocked"


def test_live_unresolved_postal_blocks():
    # finding [14]
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend()
        saved = vco_config.SECRETS_ENV_PATH
        vco_config.SECRETS_ENV_PATH = os.path.join(d, "nonexistent.env")
        os.environ.pop("MOTIONX_POSTAL_ADDRESS", None)
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            vco_config.SECRETS_ENV_PATH = saved
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 1, "unresolved postal must block the live run"
        assert gm.created == [] and gm.updated == []


def test_live_wrong_account_blocks():
    # finding [15]
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = WrongAccountBackend()
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 1, "wrong Gmail account must block the live run"
        assert gm.created == [] and gm.updated == []


def test_live_create_raw_actually_contains_the_png_attachment():
    # finding [16]: decode the raw handed to create_draft and inspect it
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        png = _vco_bootstrap.make_png()
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(png_bytes=png),
                                gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0 and len(gm.created) == 1
        msg = email.message_from_bytes(base64.urlsafe_b64decode(gm.created[0].encode()))
        atts = [p for p in msg.walk() if p.get_content_disposition() == "attachment"]
        assert len(atts) == 1 and atts[0].get_content_type() == "image/png"
        assert atts[0].get_payload(decode=True) == png, "attached bytes must equal the PNG"
        texts = [p.get_payload(decode=True).decode() for p in msg.walk()
                 if p.get_content_type() == "text/plain"]
        assert any(ci.ATTACHMENT_SENTENCE in t for t in texts), "body must mention the sketch"


def test_live_empty_recipient_skipped():
    # finding [17]
    with tempfile.TemporaryDirectory() as d:
        item = dict(ITEM1, recipient_email="")
        src = _write_source(d, [item])
        gm = _vco_bootstrap.FakeGmailBackend()
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0 and gm.created == [] and gm.updated == []
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            assert list(csv.DictReader(fh))[0]["draft_action"] == "skipped"


def test_preflight_fail_item_skipped():
    # finding [18]
    with tempfile.TemporaryDirectory() as d:
        item = dict(ITEM1, preflight_status="FAIL")
        src = _write_source(d, [item])
        gm = _vco_bootstrap.FakeGmailBackend()
        fake = _vco_bootstrap.FakeImageClient()
        rc = run_batch.main(["--visual-cold-open", "--prospect-source", src,
                             "--batch-id", "b"] + _dirs(d),
                            image_client=fake, gmail_backend=gm)
        assert rc == 0 and fake.calls == [] and gm.created == []
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            assert list(csv.DictReader(fh))[0]["draft_action"] == "skipped"


def test_duplicate_lead_in_batch_skipped():
    # finding [19]
    with tempfile.TemporaryDirectory() as d:
        dup = dict(ITEM2, lead_id="L0001")  # same lead_id as ITEM1
        src = _write_source(d, [ITEM1, dup])
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0 and len(gm.created) == 1, "second (duplicate) lead must not create a draft"
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows[1]["duplicate_check_result"] == "duplicate_in_batch"


def test_regeneration_succeeds_on_second_attempt():
    # finding [20a]
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        client = RegenFakeClient(bad_first=1)
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=client, gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0 and len(client.calls) == 2, "should regenerate exactly once"
        assert "Stricter:" in client.calls[1], "regeneration prompt must be stricter"
        assert len(gm.created) == 1
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            assert list(csv.DictReader(fh))[0]["visual_status"] == "attached"


def test_no_regeneration_when_bound_zero():
    # finding [20b]
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        client = RegenFakeClient(bad_first=1)
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--max-image-regenerations", "0",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=client, gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0 and len(client.calls) == 1, "no regeneration when bound is 0"
        assert gm.created == []
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            assert list(csv.DictReader(fh))[0]["visual_status"] == "failed_qa"


def test_created_draft_not_draft_only_flags_review():
    # finding [21]: draft exists but not confirmed DRAFT-only (and NOT sent) -> review
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend(labels=("INBOX",))  # neither DRAFT nor SENT
        os.environ["OPENAI_API_KEY"] = "sk-test"
        try:
            rc = run_batch.main(["--visual-cold-open", "--live-drafts",
                                 "--prospect-source", src, "--batch-id", "b",
                                 "--postal-address", "M, CA"] + _dirs(d),
                                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            row = list(csv.DictReader(fh))[0]
        assert row["gmail_draft_confirmed"] == "no"
        assert row["sent_or_scheduled"] == "no"
        act = os.path.join(d, "reports", "visual-cold-open-activity-log.csv")
        with open(act, newline="", encoding="utf-8") as fh:
            assert list(csv.DictReader(fh))[0]["status"] == "NEEDS_CHARLES_REVIEW"


def test_sent_label_trips_hard_invariant():
    # A message observed with a SENT label is catastrophic for a DRAFT_ONLY workflow:
    # the final invariant must raise rather than silently report success.
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT", "SENT"))
        os.environ["OPENAI_API_KEY"] = "sk-test"
        raised = False
        try:
            run_batch.main(["--visual-cold-open", "--live-drafts",
                            "--prospect-source", src, "--batch-id", "b",
                            "--postal-address", "M, CA"] + _dirs(d),
                           image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        except RuntimeError as exc:
            raised = "INVARIANT VIOLATION" in str(exc)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert raised, "a SENT-labelled message must raise the hard invariant"


def test_dry_run_preview_file_has_no_attachment_language():
    # finding [22]
    with tempfile.TemporaryDirectory() as d:
        src = _write_source(d, [ITEM1])
        gm = _vco_bootstrap.FakeGmailBackend()
        rc = run_batch.main(["--visual-cold-open", "--prospect-source", src,
                             "--batch-id", "b"] + _dirs(d),
                            image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        assert rc == 0
        assets = os.path.join(d, "assets")
        previews = [f for f in os.listdir(assets) if f.startswith("preview_")]
        assert previews, "a preview file should exist"
        text = open(os.path.join(assets, previews[0]), encoding="utf-8").read().lower()
        assert ci._ATTACHMENT_SENTINEL not in text
        report = os.path.join(d, "reports", "b_visual_cold_open_report.csv")
        with open(report, newline="", encoding="utf-8") as fh:
            assert "preview_error" not in list(csv.DictReader(fh))[0]["notes"]


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
