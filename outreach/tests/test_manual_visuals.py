#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for manual-visuals mode. Pure stdlib; no real OpenAI or Gmail calls.

Run: python3 outreach/tests/test_manual_visuals.py
"""
import csv
import os
import struct
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _vco_bootstrap  # noqa: E402
import run_batch  # noqa: E402
import copy_integration as ci  # noqa: E402
import safety  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


PACKET_MD = """\
# Batch Approval Packet

## Ranked Candidates
| Rank | Decision | Company | Domain | Category | Contact | Why | Visual | Risk |
|---:|---|---|---|---|---|---|---|---|
| 1 | APPROVE | Alpha Gear | `alphagear.com` | Packable gear | High | k | v | none |
| 2 | APPROVE | Beta Kit | `betakit.co` | Modular tools | High | k | v | none |
| 3 | APPROVE | Gamma Co | `gammaco.com` | Design objects | High | k | v | none |
| 4 | APPROVE | Delta Goods | `deltagoods.com` | Pantry goods | High | k | v | none |
"""

CSV_TEXT = (
    "candidate_id,company,domain,official_website,category,verified_observation,"
    "why_motionx_relevant,possible_angle,public_contact_evidence,source_urls,"
    "risk_uncertainty_flags,duplicate_check_result,status_recommendation\n"
    "X001,Alpha Gear,alphagear.com,https://alphagear.com/,Packable gear,"
    "Official site sells packable bags and travel gear with a compact-to-use story.,"
    "Packability is kinetic.,Film one item from pouch to use.,"
    "Official contact path available.,https://alphagear.com/contact,"
    "keep it bounded.,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n"
    "X002,Beta Kit,betakit.co,https://betakit.co/,Modular tools,"
    "Official site sells compact modular tool kits with nested parts.,"
    "Mechanical reveals.,One-kit film cylinder opened.,"
    "Official contact path available.,https://betakit.co/contact,"
    "official wording only.,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n"
    "X003,Gamma Co,gammaco.com,https://gammaco.com/,Design objects,"
    "Official site sells tactile design objects with polished photography.,"
    "Handling moments.,Motion-first product film for one object.,"
    "Official contact path available.,https://gammaco.com/contact,"
    "restrained.,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n"
    "X004,Delta Goods,deltagoods.com,https://deltagoods.com/,Pantry goods,"
    "Official site sells single-origin pantry goods.,"
    "Sensory motion.,Short pantry film.,"
    "Official contact path available.,https://deltagoods.com/contact,"
    "avoid claims.,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n"
)

CSV_WITH_RECIPIENT = CSV_TEXT.replace(
    "candidate_id,company,domain",
    "recipient_email,candidate_id,company,domain").replace(
    "X001,Alpha Gear,alphagear.com", "team@alphagear.com,X001,Alpha Gear,alphagear.com").replace(
    "X002,Beta Kit,betakit.co", ",X002,Beta Kit,betakit.co").replace(
    "X003,Gamma Co,gammaco.com", ",X003,Gamma Co,gammaco.com").replace(
    "X004,Delta Goods,deltagoods.com", ",X004,Delta Goods,deltagoods.com")


class ExplodingImageClient:
    def __init__(self):
        self.calls = []

    def preflight(self):
        self.calls.append("preflight")
        raise AssertionError("manual-visuals must not preflight OpenAI")

    def generate(self, *args, **kwargs):
        self.calls.append("generate")
        raise AssertionError("manual-visuals must not generate via OpenAI API")


def _fixtures(d, csv_text=CSV_TEXT, packet_text=PACKET_MD):
    pkt = os.path.join(d, "packet.md")
    csvp = os.path.join(d, "cands.csv")
    with open(pkt, "w", encoding="utf-8") as fh:
        fh.write(packet_text)
    with open(csvp, "w", encoding="utf-8") as fh:
        fh.write(csv_text)
    return pkt, csvp


def _common_dirs(d):
    return ["--manual-root-dir", os.path.join(d, "manual"),
            "--report-path", os.path.join(d, "reports")]


def _pack_args(pkt, csvp, d, *extra):
    return (["--visual-cold-open", "--manual-visuals", "prompt-pack",
             "--source", "batch32-approval-packet",
             "--approval-packet", pkt, "--candidate-csv", csvp,
             "--batch-id", "manualtest"] + _common_dirs(d) + list(extra))


def _bulk_args(pkt, csvp, d, *extra):
    return (["--visual-cold-open", "--manual-visuals", "chatgpt-bulk-pack",
             "--source", "batch32-approval-packet",
             "--approval-packet", pkt, "--candidate-csv", csvp,
             "--batch-id", "manualtest"] + _common_dirs(d) + list(extra))


def _manifest_path(d):
    return os.path.join(d, "manual", "manualtest", "manifest.csv")


def _image_dir(d):
    return os.path.join(d, "manual", "manualtest", "images_ready")


def _run_pack(d, limit="3", csv_text=CSV_TEXT):
    pkt, csvp = _fixtures(d, csv_text=csv_text)
    client = ExplodingImageClient()
    old_key = os.environ.pop("OPENAI_API_KEY", None)
    try:
        rc = run_batch.main(_pack_args(pkt, csvp, d, "--limit", limit),
                            image_client=client,
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
    finally:
        if old_key is not None:
            os.environ["OPENAI_API_KEY"] = old_key
    assert rc == 0
    assert client.calls == []
    return _manifest_path(d)


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _latest_report(d, prefix, suffix=".csv"):
    reports = os.path.join(d, "reports")
    fs = sorted(f for f in os.listdir(reports) if f.startswith(prefix) and f.endswith(suffix))
    assert fs, f"missing report {prefix}*{suffix}"
    return os.path.join(reports, fs[-1])


def _manual_args(d, mode, *extra):
    return (["--visual-cold-open", "--manual-visuals", mode,
             "--manual-image-dir", _image_dir(d),
             "--manual-manifest", _manifest_path(d),
             "--batch-id", "manualtest"] + _common_dirs(d) + list(extra))


def _collect_args(d, downloads, *extra):
    return (["--visual-cold-open", "--manual-visuals", "collect-downloads",
             "--manual-image-dir", _image_dir(d),
             "--manual-manifest", _manifest_path(d),
             "--download-dir", downloads,
             "--batch-id", "manualtest"] + _common_dirs(d) + list(extra))


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def _write_download(path, data, ts):
    _write(path, data)
    os.utime(path, (ts, ts))


def _jpg(width=1536, height=1024, min_bytes=2048):
    sof_body = (b"\x08" + struct.pack(">HH", height, width)
                + b"\x03\x01\x11\x00\x02\x11\x00\x03\x11\x00")
    data = b"\xff\xd8" + b"\xff\xc0" + struct.pack(">H", len(sof_body) + 2) + sof_body
    data += b"\x00" * max(0, min_bytes - len(data) - 2) + b"\xff\xd9"
    return data


def _webp(width=1536, height=1024, min_bytes=2048):
    body = (b"\x00" + b"\x00\x00\x00"
            + (width - 1).to_bytes(3, "little")
            + (height - 1).to_bytes(3, "little"))
    chunk = b"VP8X" + struct.pack("<I", len(body)) + body
    data = b"RIFF" + struct.pack("<I", 4 + len(chunk)) + b"WEBP" + chunk
    return data + (b"\x00" * max(0, min_bytes - len(data)))


def _put_image_for_row(d, row, data=None, ext=None):
    expected = row["expected_image_filename"]
    stem, expected_ext = os.path.splitext(expected)
    fname = stem + "." + (ext or expected_ext.lstrip("."))
    _write(os.path.join(_image_dir(d), fname), data or _vco_bootstrap.make_png())


def _many_candidate_sources(n):
    packet_lines = [
        "# Batch Approval Packet",
        "",
        "## Ranked Candidates",
        "| Rank | Decision | Company | Domain | Category | Contact | Why | Visual | Risk |",
        "|---:|---|---|---|---|---|---|---|---|",
    ]
    csv_lines = [
        "candidate_id,company,domain,official_website,category,verified_observation,"
        "why_motionx_relevant,possible_angle,public_contact_evidence,source_urls,"
        "risk_uncertainty_flags,duplicate_check_result,status_recommendation"
    ]
    for i in range(1, n + 1):
        company = f"Company {i:02d}"
        domain = f"company{i:02d}.com"
        packet_lines.append(
            f"| {i} | APPROVE | {company} | `{domain}` | Product goods | High | k | v | none |")
        csv_lines.append(
            f"C{i:03d},{company},{domain},https://{domain}/,Product goods,"
            f"Official site shows product {i:02d} with a verified launch detail.,"
            "Motion fit.,A concise product reveal.,Official contact path available.,"
            f"https://{domain}/contact,none,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY")
    return "\n".join(packet_lines) + "\n", "\n".join(csv_lines) + "\n"


def test_prompt_pack_writes_workspace_manifest_readme_no_api_key():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="3")
        workspace = os.path.join(d, "manual", "manualtest")
        assert os.path.isdir(workspace)
        assert not workspace.startswith(REPO_ROOT)
        rows = _read_csv(manifest)
        assert len(rows) == 3
        assert [r["expected_image_filename"] for r in rows] == [
            "01_alpha_gear_manual_visual.png",
            "02_beta_kit_manual_visual.png",
            "03_gamma_co_manual_visual.png",
        ]
        readme = open(os.path.join(workspace, "README_FOR_CHARLES.md"), encoding="utf-8").read()
        assert "GPT-5.5 Pro Chat" in readme
        assert "4 batches of 5 or 5 batches of 4" in readme
        assert "avoids OpenAI API image costs" in readme
        prompt = open(os.path.join(workspace, rows[0]["prompt_file"]), encoding="utf-8").read()
        assert "Create one horizontal 3-panel rough concept board" in prompt
        assert "Create one image only for this candidate" in prompt
        email = open(os.path.join(workspace, rows[0]["email_preview_file"]), encoding="utf-8").read()
        assert ci._ATTACHMENT_SENTINEL not in email.lower()


def test_chatgpt_bulk_pack_writes_master_chunks_and_clipboard_helper_no_api_key():
    with tempfile.TemporaryDirectory() as d:
        packet, csv_text = _many_candidate_sources(12)
        pkt, csvp = _fixtures(d, csv_text=csv_text, packet_text=packet)
        client = ExplodingImageClient()
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            rc = run_batch.main(_bulk_args(pkt, csvp, d, "--limit", "12"),
                                image_client=client,
                                gmail_backend=_vco_bootstrap.FakeGmailBackend())
        finally:
            if old_key is not None:
                os.environ["OPENAI_API_KEY"] = old_key
        assert rc == 0
        assert client.calls == []
        workspace = os.path.join(d, "manual", "manualtest")
        for rel in ("README_FOR_CHARLES.md", "manifest.csv",
                    "CHATGPT_ONE_PASTE_ALL_IMAGES.md",
                    "CHATGPT_ONE_PASTE_ALL_IMAGES.txt",
                    "CHATGPT_BATCH_01_05.txt",
                    "CHATGPT_BATCH_06_10.txt",
                    "CHATGPT_BATCH_11_12.txt",
                    "copy_master_prompt.sh"):
            assert os.path.exists(os.path.join(workspace, rel)), rel
        for rel in ("prompts", "email_previews", "briefs", "images_downloaded",
                    "images_ready", "final_previews"):
            assert os.path.isdir(os.path.join(workspace, rel)), rel
        rows = _read_csv(os.path.join(workspace, "manifest.csv"))
        master = open(os.path.join(workspace, "CHATGPT_ONE_PASTE_ALL_IMAGES.txt"),
                      encoding="utf-8").read()
        assert "Generate exactly one image per candidate." in master
        assert "EXPECTED_FILENAME: [filename]" in master
        assert "CONTINUE_FROM: [next index]" in master
        assert "Do not ask clarifying questions." in master
        for row in rows:
            assert row["company"] in master
            assert row["expected_image_filename"] in master
        helper = open(os.path.join(workspace, "copy_master_prompt.sh"),
                      encoding="utf-8").read()
        assert "pbcopy" in helper
        assert "Now paste into GPT-5.5 Pro Chat." in helper


def test_import_detects_missing_images():
    with tempfile.TemporaryDirectory() as d:
        _run_pack(d, limit="2")
        rc = run_batch.main(_manual_args(d, "import-images"),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 1
        rows = _read_csv(_latest_report(d, "manual_visual_import_manualtest_"))
        assert [r["image_status"] for r in rows] == ["MISSING", "MISSING"]


def test_import_accepts_valid_png_jpg_webp():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="3")
        rows = _read_csv(manifest)
        _put_image_for_row(d, rows[0], _vco_bootstrap.make_png(), "png")
        _put_image_for_row(d, rows[1], _jpg(), "jpg")
        _put_image_for_row(d, rows[2], _webp(), "webp")
        rc = run_batch.main(_manual_args(d, "import-images"),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 0
        out = _read_csv(_latest_report(d, "manual_visual_import_manualtest_"))
        assert all(r["image_status"] == "ACCEPTED" for r in out)
        assert {r["mime_type"] for r in out} == {"image/png", "image/jpeg", "image/webp"}


def test_collect_downloads_maps_newest_images_to_manifest_order_and_keeps_originals():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="3")
        rows = _read_csv(manifest)
        downloads = os.path.join(d, "downloads")
        base = time.time() + 100
        old_path = os.path.join(downloads, "older_extra.png")
        _write_download(old_path, _vco_bootstrap.make_png(width=1200), base - 10)
        sources = []
        for i, row in enumerate(rows, start=1):
            src = os.path.join(downloads, f"chatgpt_export_{i}.png")
            data = _vco_bootstrap.make_png(width=1536 + i, height=1024)
            _write_download(src, data, base + i)
            sources.append((src, data))
        rc = run_batch.main(_collect_args(d, downloads),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 0
        for row, (src, data) in zip(rows, sources):
            dest = os.path.join(_image_dir(d), row["expected_image_filename"])
            assert os.path.exists(src), "collector must not move/delete downloads"
            assert os.path.basename(dest) == row["expected_image_filename"]
            assert open(dest, "rb").read() == data
        out = _read_csv(_latest_report(d, "manual_visual_collect_downloads_manualtest_"))
        assert [os.path.basename(r["download_source_path"]) for r in out] == [
            "chatgpt_export_1.png",
            "chatgpt_export_2.png",
            "chatgpt_export_3.png",
        ]
        assert all(r["image_status"] == "ACCEPTED" for r in out)
        assert os.path.exists(os.path.join(d, "manual", "manualtest", "IMAGE_REVIEW_INDEX.html"))
        assert os.path.exists(os.path.join(d, "manual", "manualtest", "DOWNLOAD_COLLECT_MAPPING.csv"))


def test_collect_downloads_refuses_count_mismatch_and_copies_nothing():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="2")
        rows = _read_csv(manifest)
        downloads = os.path.join(d, "downloads")
        _write_download(os.path.join(downloads, "only_one.png"), _vco_bootstrap.make_png(),
                        time.time() + 100)
        rc = run_batch.main(_collect_args(d, downloads),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 1
        workspace = os.path.join(d, "manual", "manualtest")
        assert os.path.exists(os.path.join(workspace, "NEEDS_CHARLES_REVIEW"))
        for row in rows:
            assert not os.path.exists(os.path.join(_image_dir(d), row["expected_image_filename"]))
        out = _read_csv(_latest_report(d, "manual_visual_collect_downloads_manualtest_"))
        assert all(r["image_status"] == "NEEDS_CHARLES_REVIEW" for r in out)


def test_collect_downloads_refuses_overwrite_unless_allowed():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="1")
        row = _read_csv(manifest)[0]
        existing = _vco_bootstrap.make_png(width=1536)
        _put_image_for_row(d, row, existing, "png")
        downloads = os.path.join(d, "downloads")
        replacement = _vco_bootstrap.make_png(width=1600)
        _write_download(os.path.join(downloads, "new.png"), replacement, time.time() + 100)
        rc = run_batch.main(_collect_args(d, downloads),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 1
        dest = os.path.join(_image_dir(d), row["expected_image_filename"])
        assert open(dest, "rb").read() == existing
        rc = run_batch.main(_collect_args(d, downloads, "--allow-overwrite"),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 0
        assert open(dest, "rb").read() == replacement


def test_collect_downloads_accepts_supported_formats_and_import_still_passes():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="4")
        rows = _read_csv(manifest)
        downloads = os.path.join(d, "downloads")
        payloads = [
            ("one.png", _vco_bootstrap.make_png(), "png"),
            ("two.jpg", _jpg(), "jpg"),
            ("three.jpeg", _jpg(), "jpeg"),
            ("four.webp", _webp(), "webp"),
        ]
        base = time.time() + 100
        for i, (name, data, _ext) in enumerate(payloads):
            _write_download(os.path.join(downloads, name), data, base + i)
        rc = run_batch.main(_collect_args(d, downloads),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 0
        out = _read_csv(_latest_report(d, "manual_visual_collect_downloads_manualtest_"))
        assert all(r["image_status"] == "ACCEPTED" for r in out)
        assert [os.path.basename(r["copied_image_path"]) for r in out] == [
            row["expected_image_filename"] for row in rows
        ]
        assert {r["mime_type"] for r in out} == {"image/png", "image/jpeg", "image/webp"}
        rc = run_batch.main(_manual_args(d, "import-images"),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 0


def test_collect_downloads_rejects_unsupported_downloads():
    with tempfile.TemporaryDirectory() as d:
        _run_pack(d, limit="1")
        downloads = os.path.join(d, "downloads")
        _write_download(os.path.join(downloads, "chatgpt.gif"), b"GIF89a" + b"\x00" * 2048,
                        time.time() + 100)
        rc = run_batch.main(_collect_args(d, downloads),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 1
        out = _read_csv(_latest_report(d, "manual_visual_collect_downloads_manualtest_"))
        assert out[0]["image_status"] == "NEEDS_CHARLES_REVIEW"
        assert "unsupported recent file" in out[0]["notes"]


def test_import_rejects_unsupported_file():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="1")
        row = _read_csv(manifest)[0]
        _put_image_for_row(d, row, b"GIF89a" + b"\x00" * 2048, "gif")
        rc = run_batch.main(_manual_args(d, "import-images"),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 1
        out = _read_csv(_latest_report(d, "manual_visual_import_manualtest_"))[0]
        assert out["image_status"] == "FAILED_QA"
        assert "unsupported image extension" in out["notes"]


def test_import_rejects_duplicate_expected_filename_mapping():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="2")
        rows = _read_csv(manifest)
        rows[1]["expected_image_filename"] = rows[0]["expected_image_filename"]
        with open(manifest, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        _put_image_for_row(d, rows[0], _vco_bootstrap.make_png(), "png")
        rc = run_batch.main(_manual_args(d, "import-images"),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 1
        out = _read_csv(_latest_report(d, "manual_visual_import_manualtest_"))
        assert all(r["image_status"] == "FAILED_QA" for r in out)
        assert all("duplicate expected image" in r["notes"] for r in out)


def test_preview_attachment_language_only_when_image_exists():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="2")
        rows = _read_csv(manifest)
        _put_image_for_row(d, rows[0], _vco_bootstrap.make_png(), "png")
        rc = run_batch.main(_manual_args(d, "preview-with-images"),
                            image_client=ExplodingImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 1
        final_dir = os.path.join(d, "manual", "manualtest", "final_previews")
        first = open(os.path.join(final_dir, "01_alpha_gear_final_email.txt"),
                     encoding="utf-8").read().lower()
        second = open(os.path.join(final_dir, "02_beta_kit_final_email.txt"),
                      encoding="utf-8").read().lower()
        assert ci._ATTACHMENT_SENTINEL in first
        assert ci._ATTACHMENT_SENTINEL not in second


def test_live_refuses_without_gmail_oauth_and_writes_previews():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="1", csv_text=CSV_WITH_RECIPIENT)
        row = _read_csv(manifest)[0]
        _put_image_for_row(d, row, _vco_bootstrap.make_png(), "png")
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        rc = run_batch.main(
            _manual_args(d, "live-drafts-with-manual-images", "--live-drafts",
                         "--postal-address", "MOTIONX Test, CA",
                         "--gmail-token", os.path.join(d, "missing_token.json")),
            image_client=ExplodingImageClient(), gmail_backend=gm)
        assert rc == 1
        assert gm.created == []
        live_report = open(_latest_report(d, "manual_visual_live_drafts_manualtest_", ".md"),
                           encoding="utf-8").read()
        assert "BLOCKED_ON_GMAIL_DRAFT_ACCESS" in live_report
        final = open(os.path.join(d, "manual", "manualtest", "final_previews",
                                  "01_alpha_gear_final_email.txt"),
                     encoding="utf-8").read().lower()
        assert ci._ATTACHMENT_SENTINEL in final


def test_live_refuses_without_verified_recipient():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="1")
        row = _read_csv(manifest)[0]
        _put_image_for_row(d, row, _vco_bootstrap.make_png(), "png")
        token = os.path.join(d, "gmail_token.json")
        open(token, "w", encoding="utf-8").write("{}")
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        rc = run_batch.main(
            _manual_args(d, "live-drafts-with-manual-images", "--live-drafts",
                         "--postal-address", "MOTIONX Test, CA", "--gmail-token", token),
            image_client=ExplodingImageClient(), gmail_backend=gm)
        assert rc == 1
        assert gm.created == []
        row = _read_csv(_latest_report(d, "manual_visual_live_drafts_manualtest_"))[0]
        assert row["draft_status"] == "BLOCKED"
        assert "BLOCKED_ON_RECIPIENT_UNVERIFIED" in row["notes"]


def test_live_creates_draft_only_with_verified_recipient_and_manual_image():
    with tempfile.TemporaryDirectory() as d:
        manifest = _run_pack(d, limit="1", csv_text=CSV_WITH_RECIPIENT)
        row = _read_csv(manifest)[0]
        _put_image_for_row(d, row, _vco_bootstrap.make_png(), "png")
        token = os.path.join(d, "gmail_token.json")
        open(token, "w", encoding="utf-8").write("{}")
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        rc = run_batch.main(
            _manual_args(d, "live-drafts-with-manual-images", "--live-drafts",
                         "--postal-address", "MOTIONX Test, CA", "--gmail-token", token),
            image_client=ExplodingImageClient(), gmail_backend=gm)
        assert rc == 0
        assert len(gm.created) == 1
        out = _read_csv(_latest_report(d, "manual_visual_live_drafts_manualtest_"))[0]
        assert out["draft_status"] == "GMAIL_DRAFT_CREATED"
        assert out["gmail_draft_confirmed"] == "yes"
        assert out["sent_or_scheduled"] == "no"
        assert out["body_says_attached"] == "yes"


def test_manual_reports_do_not_leak_secret_like_values():
    with tempfile.TemporaryDirectory() as d:
        os.environ["OPENAI_API_KEY"] = "not-a-real-openai-key"
        try:
            _run_pack(d, limit="1")
            run_batch.main(_manual_args(d, "import-images"),
                           image_client=ExplodingImageClient(),
                           gmail_backend=_vco_bootstrap.FakeGmailBackend())
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        for root, _dirs, files in os.walk(os.path.join(d, "reports")):
            for f in files:
                text = open(os.path.join(root, f), encoding="utf-8").read()
                assert not safety.contains_secret_material(text)


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
