#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for report/activity-log writing: expected rows, no secrets, masked email.

Run: python3 outreach/tests/test_visual_report.py
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _vco_bootstrap  # noqa: E402
import report as vco_report  # noqa: E402
import safety  # noqa: E402

ROW = {
    "batch_id": "batch31-visual",
    "company": "Basalt Vessels",
    "safe_recipient_identifier": safety.mask_recipient("hello@basaltvessels.example"),
    "source_record_id": "L0492",
    "duplicate_check_result": "unique",
    "draft_id": "r123",
    "draft_action": "updated",
    "visual_status": "attached",
    "attachment_filename": "motionx_visual_cold_open_north_drinkware_2026-07-07.png",
    "attachment_path": "/Users/x/.motionx-outreach/visual-assets/batch31-visual/x.png",
    "body_says_attached": "yes",
    "gpt_image_model_used": "gpt-image-2",
    "gpt_image_size": "1536x1024",
    "fabrication_check_passed": "yes",
    "gmail_draft_confirmed": "yes",
    "sent_or_scheduled": "no",
    "notes": "leaked key sk-abcdef1234567890 should be scrubbed",
}


def test_mask_recipient_hides_local_part():
    assert safety.mask_recipient("hello@basaltvessels.example") == "h***@basaltvessels.example"
    assert safety.mask_recipient("") == "***"


def test_report_csv_has_expected_columns_and_scrubs_secrets():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "r.csv")
        vco_report.write_report_csv(path, [ROW])
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert list(rows[0].keys()) == vco_report.REPORT_COLUMNS
        r = rows[0]
        assert r["sent_or_scheduled"] == "no"
        assert "sk-abcdef" not in r["notes"], "secret must be scrubbed"
        assert "[REDACTED]" in r["notes"]
        # full recipient email never appears
        assert "hello@basaltvessels.example" not in ",".join(r.values())


def test_sent_or_scheduled_forced_no_even_if_row_says_yes():
    bad = dict(ROW)
    bad["sent_or_scheduled"] = "yes"
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "r.csv")
        vco_report.write_report_csv(path, [bad])
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert rows[0]["sent_or_scheduled"] == "no", "invariant: never report a send"


def test_activity_log_writes_header_and_row():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "act.csv")
        vco_report.append_activity_log(path, [dict(ROW, status="DRAFT_UPDATED_WITH_ATTACHMENT")],
                                       "2026-07-07T10:00:00")
        vco_report.append_activity_log(path, [dict(ROW, status="DRAFT_UPDATED_WITH_ATTACHMENT")],
                                       "2026-07-07T10:05:00")
        with open(path, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == 2, "two appended rows, one header"
        assert rows[0]["sent_or_scheduled"] == "no"
        assert list(rows[0].keys()) == vco_report.ACTIVITY_COLUMNS


def test_summary_md_reports_no_send():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "s.md")
        vco_report.write_summary_md(path, "batch31-visual", "dry-run", [ROW], ["preflight ok"])
        text = open(path, encoding="utf-8").read()
        assert "Sent or scheduled:** no" in text
        assert "No email was sent or scheduled" in text
        assert "sk-abcdef" not in text


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
