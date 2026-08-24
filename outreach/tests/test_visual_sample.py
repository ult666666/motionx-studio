#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for --sample-only mode: approval-packet ingestion, top-3 APPROVE selection,
the section-10 sample copy, and the blocked-access paths. NO real API/Gmail calls.

Run: python3 outreach/tests/test_visual_sample.py
"""
import csv
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _vco_bootstrap  # noqa: E402
import run_batch  # noqa: E402
import config as vco_config  # noqa: E402
import safety  # noqa: E402
import sample_source as ss  # noqa: E402
import sample_copy as sc  # noqa: E402
import image_client as ic  # noqa: E402
import copy_integration as ci  # noqa: E402


# ── fixtures ──────────────────────────────────────────────────────────────────────
PACKET_MD = """\
# Batch Approval Packet

## Ranked Candidates
| Rank | Decision | Company | Domain | Category | Contact | Why | Visual | Risk |
|---:|---|---|---|---|---|---|---|---|
| 1 | APPROVE | Alpha Gear | `alphagear.com` | Packable gear | High | k | v | none |
| 2 | APPROVE | Beta Kit | `betakit.co` | Modular tools | High | k | v | none |
| 3 | APPROVE | Gamma Co | `gammaco.com` | Design objects | High | k | v | none |
| 4 | APPROVE | Delta Goods | `deltagoods.com` | Pantry goods | High | k | v | none |
| 5 | MAYBE | Epsilon Studio | `epsilon.studio` | Lighting | Medium | k | v | flag |
"""

CSV_TEXT = (
    "candidate_id,company,domain,official_website,category,verified_observation,"
    "why_motionx_relevant,possible_angle,public_contact_evidence,source_urls,"
    "risk_uncertainty_flags,duplicate_check_result,status_recommendation\n"
    "X001,Alpha Gear,alphagear.com,https://alphagear.com/,Packable gear,"
    "Official site sells packable bags and travel gear with a compact-to-use story.,"
    "Packability is kinetic.,Film one item from pouch to use.,"
    "Official contact path available.,https://alphagear.com/ ; https://alphagear.com/contact,"
    "keep it bounded.,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n"
    "X002,Beta Kit,betakit.co,https://betakit.co/,Modular tools,"
    "Official site sells compact modular tool kits with nested parts.,"
    "Mechanical reveals.,One-kit film cylinder opened.,"
    "Official contact path available.,https://betakit.co/,"
    "official wording only.,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n"
    "X003,Gamma Co,gammaco.com,https://gammaco.com/,Design objects,"
    "Official site sells tactile design objects with polished photography.,"
    "Handling moments.,Motion-first product film for one object.,"
    "Official contact path available.,https://gammaco.com/,"
    "restrained.,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n"
    "X004,Delta Goods,deltagoods.com,https://deltagoods.com/,Pantry goods,"
    "Official site sells single-origin pantry goods.,"
    "Sensory motion.,Short pantry film.,"
    "Official contact path available.,https://deltagoods.com/,"
    "avoid claims.,CLEAR,SOURCE_CANDIDATE_REVIEW_ONLY\n"
)

# A CSV that verifies a recipient email for one company (exercises the live path).
CSV_WITH_RECIPIENT = CSV_TEXT.replace(
    "candidate_id,company,domain",
    "recipient_email,candidate_id,company,domain").replace(
    "X001,Alpha Gear,alphagear.com", "team@alphagear.com,X001,Alpha Gear,alphagear.com").replace(
    "X002,Beta Kit,betakit.co", ",X002,Beta Kit,betakit.co").replace(
    "X003,Gamma Co,gammaco.com", ",X003,Gamma Co,gammaco.com").replace(
    "X004,Delta Goods,deltagoods.com", ",X004,Delta Goods,deltagoods.com")


class AccessBlockedClient:
    """gpt-image-2 client stand-in that fails closed (no key / no access)."""
    def __init__(self):
        self.calls = []

    def preflight(self):
        return {"ok": False, "detail": "OPENAI_API_KEY is not set"}

    def generate(self, prompt, size="1536x1024", quality="medium", image_format="png"):
        self.calls.append(prompt)
        raise ic.ImageAccessError("OPENAI_API_KEY is not set")


def _fixtures(d, csv_text=CSV_TEXT):
    pkt = os.path.join(d, "packet.md")
    csvp = os.path.join(d, "cands.csv")
    with open(pkt, "w", encoding="utf-8") as fh:
        fh.write(PACKET_MD)
    with open(csvp, "w", encoding="utf-8") as fh:
        fh.write(csv_text)
    return pkt, csvp


def _dirs(d):
    return ["--report-path", os.path.join(d, "reports"),
            "--asset-dir", os.path.join(d, "assets")]


def _sample_args(pkt, csvp, d, *extra):
    return (["--visual-cold-open", "--sample-only", "--source", "batch32-approval-packet",
             "--approval-packet", pkt, "--candidate-csv", csvp,
             "--batch-id", "batchtest_vco_samples"] + _dirs(d) + list(extra))


def _read_sample_report(d):
    reports = os.path.join(d, "reports")
    fs = [f for f in os.listdir(reports)
          if f.startswith("batch32_vco_sample_run_") and f.endswith(".csv")]
    assert fs, "a sample-run CSV must be written"
    with open(os.path.join(reports, fs[0]), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ── parsing / selection ─────────────────────────────────────────────────────────
def test_parse_approval_packet():
    cands = ss.parse_approval_packet(PACKET_MD)
    assert len(cands) == 5
    assert cands[0].rank == 1 and cands[0].company == "Alpha Gear"
    assert cands[0].domain == "alphagear.com"
    assert [c.decision for c in cands] == ["APPROVE"] * 4 + ["MAYBE"]


def test_top3_approve_selection_excludes_maybe():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d)
        cands = ss.load_candidates(pkt, csvp)
        top3 = ss.select_top_approve(cands, 3)
        assert [c.company for c in top3] == ["Alpha Gear", "Beta Kit", "Gamma Co"]
        assert all(c.decision == "APPROVE" for c in top3)
        assert top3[0].verified_observation.startswith("Official site sells packable")
        assert top3[0].selected_from == "batch32-approval-packet+sourcing-csv"


def test_maybe_fallback_only_when_few_approve():
    md = "\n".join(l for l in PACKET_MD.splitlines()
                   if not (l.startswith("| 2 ") or l.startswith("| 3 ") or l.startswith("| 4 ")))
    cands = ss.parse_approval_packet(md)  # 1 APPROVE + 1 MAYBE
    chosen = ss.select_top_approve(cands, 3)
    assert len(chosen) == 2  # only 1 APPROVE + 1 MAYBE fallback available
    assert chosen[0].decision == "APPROVE" and chosen[1].decision == "MAYBE"
    assert any("fallback" in f for f in chosen[1].uncertainty_flags)


_AMBIG_PACKET = """\
## Ranked Candidates
| Rank | Decision | Company | Domain | Category |
|---:|---|---|---|---|
| 1 | APPROVE | Acme Rockets Co | `{domain}` | Rockets |
"""
_AMBIG_CSV = (
    "candidate_id,company,domain,official_website,category,verified_observation,"
    "why_motionx_relevant,possible_angle,public_contact_evidence,source_urls,"
    "risk_uncertainty_flags,duplicate_check_result,status_recommendation\n"
    "A1,Acme Anvils,acme.com,https://acme.com/,Anvils,"
    "Official site sells heavy iron anvils.,x,y,contact,url,r,CLEAR,S\n"
    "A2,Acme Rockets,acme.io,https://acme.io/,Rockets,"
    "Official site sells model rockets.,x,y,contact,url,r,CLEAR,S\n"
)


def test_csv_join_exact_domain_wins_over_ambiguous_root():
    # Packet company name does not _norm-match a CSV company key, and two CSV rows
    # share the TLD-stripped root 'acme'. The candidate's EXACT domain must still bind
    # to its OWN row — never the other company's verified observation.
    cands = ss.parse_approval_packet(_AMBIG_PACKET.format(domain="acme.io"))
    idx = ss.parse_candidate_csv(_AMBIG_CSV)
    ss._enrich_from_csv(cands[0], idx)
    assert cands[0].verified_observation == "Official site sells model rockets."
    assert "anvil" not in cands[0].verified_observation.lower(), "must NOT misattribute"


def test_csv_join_ambiguous_root_falls_through_not_misattributed():
    # Candidate domain 'acme.co' has no exact CSV row; the root 'acme' is ambiguous
    # (acme.com vs acme.io) so it is dropped — the candidate gets NO observation
    # rather than an arbitrary first row's.
    cands = ss.parse_approval_packet(_AMBIG_PACKET.format(domain="acme.co"))
    idx = ss.parse_candidate_csv(_AMBIG_CSV)
    assert "d:acme" not in idx, "ambiguous root must be dropped fail-closed"
    ss._enrich_from_csv(cands[0], idx)
    assert cands[0].verified_observation == ""
    assert any("no matching CSV row" in f for f in cands[0].uncertainty_flags)


def test_parse_failure_raises():
    with tempfile.TemporaryDirectory() as d:
        pkt = os.path.join(d, "empty.md")
        with open(pkt, "w", encoding="utf-8") as fh:
            fh.write("# no table here\n")
        try:
            ss.load_candidates(pkt, "")
        except ss.SampleParseError:
            return
        assert False, "empty packet must raise SampleParseError"


# ── sample copy honesty ──────────────────────────────────────────────────────────
def test_sample_copy_no_attachment_language_unless_attached():
    item = {"business_name": "Alpha Gear", "domain": "alphagear.com",
            "verified_observation": "Official site sells packable bags."}
    _, plain_no, html_no = sc.build_sample_bodies(item, "PL", attached=False)
    assert ci._ATTACHMENT_SENTINEL not in plain_no.lower()
    assert ci._ATTACHMENT_SENTINEL not in html_no.lower()
    _, plain_yes, _ = sc.build_sample_bodies(item, "PL", attached=True)
    assert ci.ATTACHMENT_SENTENCE in plain_yes


def test_sample_copy_uses_team_greeting_without_first_name():
    item = {"business_name": "Alpha Gear", "verified_observation": "Official site sells x."}
    _, plain, _ = sc.build_sample_bodies(item, "PL", attached=False)
    assert plain.startswith("Hi Alpha Gear team —")


def test_sample_subject_shape():
    item = {"business_name": "Alpha Gear", "verified_observation": "x"}
    subj, _, _ = sc.build_sample_bodies(item, "PL", attached=False)
    assert subj == "Rough visual thought for Alpha Gear"


# ── end-to-end sample runs ───────────────────────────────────────────────────────
def test_sample_dry_run_writes_previews_no_gmail():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d)
        gm = _vco_bootstrap.FakeGmailBackend()
        rc = run_batch.main(_sample_args(pkt, csvp, d, "--limit", "3"),
                            image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        assert rc == 0
        assert gm.created == [] and gm.updated == [], "dry-run sample must not write Gmail"
        rows = _read_sample_report(d)
        assert len(rows) == 3
        assert [r["company"] for r in rows] == ["Alpha Gear", "Beta Kit", "Gamma Co"]
        assert all(r["sent_or_scheduled"] == "no" for r in rows)
        assert all(r["draft_status"] == "local_preview" for r in rows)
        assert all(r["body_says_attached"] == "no" for r in rows)  # no image generated
        # preview files exist and carry no attachment language
        assets = os.path.join(d, "assets")
        previews = [f for f in os.listdir(assets) if f.startswith("sample_")]
        assert len(previews) == 3
        for p in previews:
            assert ci._ATTACHMENT_SENTINEL not in open(
                os.path.join(assets, p), encoding="utf-8").read().lower()
        # brief + prompt artifacts written
        assert any(f.startswith("brief_") for f in os.listdir(assets))
        assert any(f.startswith("prompt_") for f in os.listdir(assets))
        assert any(f.startswith("visualbrief_") for f in os.listdir(assets))


def test_sample_limit_capped_at_max():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d)
        gm = _vco_bootstrap.FakeGmailBackend()
        # ask for 10 — must be capped at MAX_SAMPLE_DRAFTS (3)
        rc = run_batch.main(_sample_args(pkt, csvp, d, "--limit", "10"),
                            image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        assert rc == 0
        rows = _read_sample_report(d)
        assert len(rows) == vco_config.MAX_SAMPLE_DRAFTS == 3


def test_sample_dry_run_with_images_attaches_but_no_gmail():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d)
        gm = _vco_bootstrap.FakeGmailBackend()
        os.environ["OPENAI_API_KEY"] = "sk-not-used-by-fake"
        try:
            rc = run_batch.main(
                _sample_args(pkt, csvp, d, "--limit", "3", "--generate-images-in-dry-run"),
                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert gm.created == [], "dry-run must not write Gmail even with images"
        rows = _read_sample_report(d)
        assert all(r["body_says_attached"] == "yes" for r in rows)
        assert all(r["attachment_status"] == "attached" for r in rows)
        assets = os.path.join(d, "assets")
        assert any(f.endswith(".raw.b64url") for f in os.listdir(assets))
        assert any(f.startswith("motionx_visual_cold_open_") for f in os.listdir(assets))


def test_sample_image_access_blocked_path():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d)
        gm = _vco_bootstrap.FakeGmailBackend()
        client = AccessBlockedClient()
        rc = run_batch.main(
            _sample_args(pkt, csvp, d, "--limit", "3", "--generate-images-in-dry-run"),
            image_client=client, gmail_backend=gm)
        assert rc == 0
        assert gm.created == []
        rows = _read_sample_report(d)
        assert len(rows) == 3
        for r in rows:
            assert r["visual_status"] == "blocked_access"
            assert r["body_says_attached"] == "no", "no attachment => no attached language"
            assert r["attachment_status"] == "blocked"
        # briefs + prompts still written (the deliverable when access is blocked)
        assets = os.path.join(d, "assets")
        assert sum(1 for f in os.listdir(assets) if f.startswith("prompt_")) == 3
        # previews carry no attachment language
        for f in os.listdir(assets):
            if f.startswith("sample_") and f.endswith(".txt"):
                assert ci._ATTACHMENT_SENTINEL not in open(
                    os.path.join(assets, f), encoding="utf-8").read().lower()


def test_sample_live_no_recipient_blocks_gmail():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d)  # no recipient in this CSV
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        os.environ["OPENAI_API_KEY"] = "sk-not-used"
        try:
            rc = run_batch.main(
                _sample_args(pkt, csvp, d, "--limit", "3", "--live-drafts",
                             "--postal-address", "MOTIONX Test, CA"),
                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert gm.created == [], "no verified recipient => no Gmail draft"
        rows = _read_sample_report(d)
        assert all(r["draft_status"] == "blocked_recipient" for r in rows)
        assert all(r["gmail_draft_confirmed"] == "no" for r in rows)
        assert all(r["sent_or_scheduled"] == "no" for r in rows)


def test_sample_live_image_blocked_blocks_gmail():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d, csv_text=CSV_WITH_RECIPIENT)  # Alpha has a recipient
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        rc = run_batch.main(
            _sample_args(pkt, csvp, d, "--limit", "1", "--live-drafts",
                         "--postal-address", "MOTIONX Test, CA"),
            image_client=AccessBlockedClient(), gmail_backend=gm)
        assert rc == 0
        assert gm.created == [], "no attachment (image blocked) => refuse to create a draft"
        rows = _read_sample_report(d)
        assert rows[0]["draft_status"] == "blocked_visual"
        assert rows[0]["body_says_attached"] == "no"


def test_sample_live_create_attaches_when_recipient_and_image():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d, csv_text=CSV_WITH_RECIPIENT)
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        os.environ["OPENAI_API_KEY"] = "sk-not-used"
        try:
            rc = run_batch.main(
                _sample_args(pkt, csvp, d, "--limit", "1", "--live-drafts",
                             "--postal-address", "MOTIONX Test, CA"),
                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        assert len(gm.created) == 1, "exactly one draft for the one recipient-verified candidate"
        rows = _read_sample_report(d)
        r = rows[0]
        assert r["draft_status"] == "gmail_draft_created"
        assert r["body_says_attached"] == "yes"
        assert r["gmail_draft_confirmed"] == "yes"
        assert r["sent_or_scheduled"] == "no"
        # the draft id is masked in the report (never the full id)
        assert r["gmail_draft_id"] and "***" in r["gmail_draft_id"]
        assert "draft101" not in r["gmail_draft_id"]


def test_sample_live_draft_only_false_does_not_leak_full_id():
    # When verify_draft_only returns draft_only=False, the full draft/message/thread id
    # must NOT appear in the report or activity-log notes (only masked / sanitized).
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d, csv_text=CSV_WITH_RECIPIENT)
        gm = _vco_bootstrap.FakeGmailBackend(labels=("INBOX",))  # neither DRAFT nor SENT
        os.environ["OPENAI_API_KEY"] = "sk-not-used"
        try:
            rc = run_batch.main(
                _sample_args(pkt, csvp, d, "--limit", "1", "--live-drafts",
                             "--postal-address", "MOTIONX Test, CA"),
                image_client=_vco_bootstrap.FakeImageClient(), gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0 and len(gm.created) == 1
        full_id = "draft101"  # FakeGmailBackend's first created id
        reports = os.path.join(d, "reports")
        for f in os.listdir(reports):
            blob = open(os.path.join(reports, f), encoding="utf-8").read()
            assert full_id not in blob, f"full draft id leaked into {f}"
        rows = _read_sample_report(d)
        assert rows[0]["gmail_draft_confirmed"] == "no"
        assert "***" in rows[0]["gmail_draft_id"], "id must be masked, not omitted"
        assert rows[0]["sent_or_scheduled"] == "no"


def test_sample_fabrication_blocks_before_generation_or_draft():
    with tempfile.TemporaryDirectory() as d:
        bad_csv = CSV_TEXT.replace(
            "Official site sells packable bags and travel gear with a compact-to-use story.",
            "Award-winning gear trusted by thousands of happy customers.")
        pkt, csvp = _fixtures(d, csv_text=bad_csv)
        gm = _vco_bootstrap.FakeGmailBackend(labels=("DRAFT",))
        client = _vco_bootstrap.FakeImageClient()
        os.environ["OPENAI_API_KEY"] = "sk-not-used"
        try:
            rc = run_batch.main(
                _sample_args(pkt, csvp, d, "--limit", "3", "--generate-images-in-dry-run"),
                image_client=client, gmail_backend=gm)
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
        assert rc == 0
        rows = _read_sample_report(d)
        alpha = [r for r in rows if r["company"] == "Alpha Gear"][0]
        assert alpha["fabrication_check_passed"] == "no"
        assert alpha["draft_status"] == "blocked_fabrication"
        assert gm.created == []


def test_no_send_endpoint_is_reachable():
    # structural guard: send/schedule/destructive ops are forbidden; drafts.create ok
    for bad in ("drafts.send", "messages.send", "drafts.schedule", "messages.insert",
                "drafts.trash", "drafts.delete"):
        try:
            safety.assert_not_send(bad)
        except safety.SendForbiddenError:
            continue
        assert False, f"{bad} must be forbidden"
    safety.assert_allowed_draft_op("drafts.create")  # must not raise
    safety.assert_allowed_draft_op("drafts.update")


def test_sample_report_has_section12_columns():
    with tempfile.TemporaryDirectory() as d:
        pkt, csvp = _fixtures(d)
        rc = run_batch.main(_sample_args(pkt, csvp, d, "--limit", "3"),
                            image_client=_vco_bootstrap.FakeImageClient(),
                            gmail_backend=_vco_bootstrap.FakeGmailBackend())
        assert rc == 0
        reports = os.path.join(d, "reports")
        fs = [f for f in os.listdir(reports) if f.startswith("batch32_vco_sample_run_")]
        assert any(f.endswith(".csv") for f in fs) and any(f.endswith(".md") for f in fs)
        rows = _read_sample_report(d)
        import report as vco_report
        for col in vco_report.SAMPLE_REPORT_COLUMNS:
            assert col in rows[0], f"missing report column {col}"


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    ok = 0
    for t in TESTS:
        t()
        print("PASS", t.__name__)
        ok += 1
    print(f"\n{ok}/{len(TESTS)} passed")
