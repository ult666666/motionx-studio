#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — batch runner (DRAFT_ONLY, dry-run by default).

Adds an OPTIONAL gpt-image-2 visual cold-open + Gmail image-attachment layer around
the existing normalized draft workflow. It reuses the normalized workflow's selected
prospects, copy, canonical signature/footer, and duplicate awareness.

Usage (from the repo root):

  Dry-run (default — no images, no Gmail writes; shows the plan):
    python3 outreach/visual_cold_open/run_batch.py --visual-cold-open \
        --prospect-source ~/.motionx-outreach/_batch31_drafts.json \
        --batch-id batch31-visual --limit 20

  Dry-run + real image generation (writes assets outside the repo, still no Gmail):
    python3 outreach/visual_cold_open/run_batch.py --visual-cold-open \
        --prospect-source ~/.motionx-outreach/_batch31_drafts.json \
        --batch-id batch31-visual --generate-images-in-dry-run --limit 1

  Live — create NEW drafts with the image attached (only after review):
    python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --live-drafts \
        --prospect-source <undrafted_batch>.json --batch-id <id> \
        --gmail-token ~/.motionx-outreach/gmail_token.json

  Live — RETROFIT existing batch31 drafts with attachments (opt-in):
    python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --live-drafts \
        --source existing-gmail-drafts \
        --prospect-source ~/.motionx-outreach/_batch31_drafts.json \
        --manifest ~/.motionx-outreach/_batch31_created_manifest.json \
        --allow-update-existing-drafts --batch-id batch31-visual \
        --gmail-token ~/.motionx-outreach/gmail_token.json

  Manual visuals — no OpenAI API image generation:
    python3 outreach/visual_cold_open/run_batch.py --visual-cold-open \
        --manual-visuals prompt-pack --source batch32-approval-packet \
        --approval-packet <approval.md> --candidate-csv <candidates.csv> \
        --batch-id <id>

  One-paste ChatGPT visual batch — no OpenAI API image generation:
    python3 outreach/visual_cold_open/run_batch.py --visual-cold-open \
        --manual-visuals chatgpt-bulk-pack --source batch32-approval-packet \
        --approval-packet <approval.md> --candidate-csv <candidates.csv> \
        --batch-id <id>

This program NEVER sends or schedules email. See VISUAL-COLD-OPEN-RUNBOOK.md.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys

_VCO_DIR = os.path.dirname(os.path.abspath(__file__))
_OUTREACH_DIR = os.path.dirname(_VCO_DIR)
_REPO_ROOT = os.path.dirname(_OUTREACH_DIR)
for _p in (_VCO_DIR, _OUTREACH_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import config as vco_config          # noqa: E402
import safety                         # noqa: E402
import brief as vco_brief             # noqa: E402
import copy_integration as vco_copy   # noqa: E402
import sample_copy as vco_sample_copy  # noqa: E402
import sample_source as vco_sample_src  # noqa: E402
import image_client as vco_image      # noqa: E402
import image_qa as vco_qa             # noqa: E402
import manual_visuals as vco_manual    # noqa: E402
import mime_builder                   # noqa: E402
import report as vco_report           # noqa: E402
from gmail_draft import GmailDraftBackend, GmailApiUnavailable  # noqa: E402


# ── helpers ─────────────────────────────────────────────────────────────────────
def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")
    return s or "prospect"


def format_ext(image_format: str) -> str:
    ext = (image_format or "png").lower().lstrip(".")
    return "jpg" if ext == "jpeg" else ext


def attachment_filename(company: str, date_str: str, image_format: str = "png") -> str:
    return f"motionx_visual_cold_open_{slugify(company)}_{date_str}.{format_ext(image_format)}"


def _under_repo(path: str, repo_root: str) -> bool:
    ap = os.path.abspath(os.path.expanduser(path))
    rp = os.path.abspath(os.path.expanduser(repo_root))
    return ap == rp or ap.startswith(rp + os.sep)


def load_json(path: str) -> dict:
    with open(os.path.expanduser(path), "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_items(cfg: vco_config.VCOConfig) -> list:
    """Load the selected prospects, joining a manifest for the retrofit path."""
    src = load_json(cfg.prospect_source)
    items = src.get("items") if isinstance(src, dict) else src
    if not isinstance(items, list):
        raise ValueError(f"prospect source has no 'items' list: {cfg.prospect_source}")

    draft_ids: dict = {}
    if cfg.source_kind == "existing-gmail-drafts":
        if not getattr(cfg, "manifest_path", ""):
            raise ValueError("--source existing-gmail-drafts requires --manifest")
        man = load_json(cfg.manifest_path)
        man_items = man.get("items", man) if isinstance(man, dict) else man
        for mi in man_items:
            if isinstance(mi, dict) and mi.get("lead_id"):
                draft_ids[mi["lead_id"]] = mi.get("draft_id", "")

    out = []
    for it in items:
        did = draft_ids.get(it.get("lead_id", ""), "") if draft_ids else ""
        out.append((it, did))
    return out


# ── preflight ────────────────────────────────────────────────────────────────────
def run_preflight(cfg: vco_config.VCOConfig, image_client, gmail_backend) -> tuple:
    notes = []
    ok = True

    # 1. Gmail account (live only) is charles@madebymotionx.com
    if cfg.is_live:
        try:
            acct = gmail_backend.verify_account()
            notes.append(f"Gmail account verified: {safety.mask_recipient(acct)}")
        except (GmailApiUnavailable, safety.WrongAccountError, safety.SendForbiddenError) as exc:
            ok = False
            notes.append(f"BLOCKED_ON_GMAIL_API: {safety.redact_secrets(str(exc))}")

    # 2. no send endpoint will be called (structural invariant)
    notes.append("Send guard active: drafts.create/update/get only; any *send* op raises.")

    # 3. OPENAI_API_KEY present + gpt-image-2 callable (when we will generate, or when
    #    the operator explicitly asked for a preflight access check).
    will_generate = (cfg.is_live or cfg.generate_images_in_dry_run
                     or cfg.generate_test_image or cfg.mode == "preflight")
    if will_generate:
        pf = image_client.preflight()
        notes.append(f"gpt-image-2 preflight: {'OK' if pf['ok'] else 'FAILED'} — {pf['detail']}")
        if not pf["ok"]:
            ok = False
    else:
        notes.append("gpt-image-2 preflight skipped (no image generation in this dry-run).")

    # 4. prospect source exists
    if not os.path.exists(os.path.expanduser(cfg.prospect_source)):
        ok = False
        notes.append(f"BLOCKED_ON_PROSPECT_SOURCE: not found: {cfg.prospect_source}")
    else:
        notes.append(f"Prospect source present: {os.path.basename(cfg.prospect_source)}")

    # 5. output dirs are OUTSIDE the repo
    for label, d in (("assets", cfg.resolved_assets_dir()),
                     ("reports", cfg.reports_dir)):
        if _under_repo(d, cfg.repo_root):
            ok = False
            notes.append(f"REFUSED: {label} dir is inside the repo: {d}")
    if ok:
        notes.append("Output dirs are outside the repo.")

    # 6. report dir writable (only create it when it is safely outside the repo, so a
    #    misconfigured in-repo path never gets materialized)
    if _under_repo(cfg.reports_dir, cfg.repo_root):
        ok = False
        notes.append(f"REFUSED: report dir is inside the repo: {cfg.reports_dir}")
    else:
        try:
            os.makedirs(cfg.reports_dir, exist_ok=True)
            notes.append("Report directory is writable.")
        except OSError as exc:
            ok = False
            notes.append(f"Report dir not writable: {exc}")

    # 7. live mode explicitly requested for any Gmail mutation
    if cfg.is_live:
        notes.append("Live mode explicitly requested (--live-drafts).")
        if not vco_config.postal_resolved(cfg.postal_address):
            ok = False
            notes.append("BLOCKED: postal address unresolved — live drafts require the "
                         "resolved compliance footer (resolved-or-block).")
        if cfg.source_kind == "existing-gmail-drafts" and not cfg.allow_update_existing_drafts:
            ok = False
            notes.append("BLOCKED: retrofit requires --allow-update-existing-drafts.")
    else:
        notes.append("Dry-run: no Gmail draft will be created or updated.")

    return ok, notes


# ── per-prospect processing ──────────────────────────────────────────────────────
def process_prospect(cfg, image_client, gmail_backend, item, draft_id,
                     seen_leads, date_str) -> dict:
    company = item.get("business_name") or item.get("prospect_name") or "unknown"
    lead_id = item.get("lead_id", "")
    recipient = item.get("recipient_email", "")

    row = {
        "batch_id": cfg.batch_id,
        "company": company,
        "safe_recipient_identifier": safety.mask_recipient(recipient),
        "source_record_id": lead_id,
        "duplicate_check_result": "unique",
        "draft_id": draft_id or "",
        "draft_action": "skipped",
        "visual_status": "not_created",
        "attachment_filename": "",
        "attachment_path": "",
        "body_says_attached": "no",
        "gpt_image_model_used": "",
        "gpt_image_size": "",
        "fabrication_check_passed": "yes",
        "gmail_draft_confirmed": "no",
        "sent_or_scheduled": "no",
        "notes": "",
        "status": vco_config.STATUS["NOT_STARTED"],
    }

    # Duplicate / eligibility
    if lead_id and lead_id in seen_leads:
        row.update(duplicate_check_result="duplicate_in_batch", draft_action="skipped",
                   status=vco_config.STATUS["SKIPPED_DUPLICATE"],
                   notes="duplicate lead_id within batch")
        return row
    if lead_id:
        seen_leads.add(lead_id)
    if str(item.get("preflight_status", "PASS")).upper() == "FAIL":
        row.update(draft_action="skipped", status=vco_config.STATUS["SKIPPED_INELIGIBLE"],
                   notes="source item failed normalized preflight")
        return row
    if not (item.get("business_name") or item.get("prospect_name") or item.get("company")):
        row.update(draft_action="skipped", status=vco_config.STATUS["SKIPPED_INELIGIBLE"],
                   notes="no resolvable company name on the source item")
        return row
    if cfg.is_live and not recipient:
        row.update(draft_action="skipped", status=vco_config.STATUS["SKIPPED_INELIGIBLE"],
                   notes="no recipient email for live draft")
        return row

    # 1. brief + fabrication guard
    brief = vco_brief.build_brief(item)
    if brief.fabrication_findings:
        row.update(fabrication_check_passed="no", draft_action="blocked",
                   visual_status="not_created",
                   status=vco_config.STATUS["BLOCKED_ON_FABRICATION"],
                   notes="; ".join(brief.fabrication_findings)[:300])
        return row
    prompt = vco_brief.build_image_prompt(brief)
    prompt_fab = vco_brief.prompt_is_clean(prompt)
    if prompt_fab:
        row.update(fabrication_check_passed="no", draft_action="blocked",
                   status=vco_config.STATUS["BLOCKED_ON_FABRICATION"],
                   notes="; ".join(prompt_fab)[:300])
        return row

    # Persist the brief + prompt (outside the repo) for operator review.
    assets_dir = cfg.resolved_assets_dir()
    os.makedirs(assets_dir, exist_ok=True)
    brief_path = os.path.join(assets_dir, f"brief_{slugify(company)}_{date_str}.json")
    with open(brief_path, "w", encoding="utf-8") as fh:
        json.dump({"brief": brief.to_dict(), "prompt": prompt}, fh, indent=2)

    row["gpt_image_size"] = cfg.image_size

    # 2. decide whether to generate an image this run
    will_generate = cfg.is_live or cfg.generate_images_in_dry_run
    if not will_generate:
        row.update(draft_action="skipped", visual_status="planned",
                   status=vco_config.STATUS["DRY_RUN_OK"],
                   notes=f"dry-run plan only; brief+prompt written to {os.path.basename(brief_path)}"
                   + ("; ".join([""] + brief.uncertainty_flags) if brief.uncertainty_flags else ""))
        # Build a would-send preview WITHOUT attachment language (no image attached).
        _write_preview(cfg, item, company, date_str, assets_dir, attached=False,
                       attachment=None, row=row)
        return row

    # 3. generate image (with one stricter-prompt regeneration on QA failure)
    attachment = None
    attached = False
    qa = None
    attempt = 0
    max_attempts = 1 + max(0, cfg.max_image_regenerations)
    cur_prompt = prompt
    while attempt < max_attempts:
        attempt += 1
        try:
            gen = image_client.generate(cur_prompt, size=cfg.image_size,
                                        quality=cfg.image_quality,
                                        image_format=cfg.image_format)
        except (vco_image.ImageAccessError,) as exc:
            row.update(draft_action="blocked", visual_status="failed_generation",
                       status=vco_config.STATUS["BLOCKED_ON_GPT_IMAGE_2_ACCESS"],
                       notes=safety.redact_secrets(str(exc))[:300])
            return row
        except vco_image.ImageGenerationError as exc:
            row.update(draft_action="blocked", visual_status="failed_generation",
                       status=vco_config.STATUS["BLOCKED_ON_VISUAL_GENERATION"],
                       notes=safety.redact_secrets(str(exc))[:300])
            return row

        row["gpt_image_model_used"] = gen.model
        fname = attachment_filename(company, date_str, cfg.image_format)
        img_path = os.path.join(assets_dir, fname)
        vco_image.save_image_bytes(img_path, gen.data, repo_root=cfg.repo_root)

        qa = vco_qa.qa_image_file(
            path=img_path, expected_company=brief.company_name,
            manifest_company=company, brief=brief, prompt=cur_prompt,
            expected_format=cfg.image_format,
        )
        if qa.passed:
            attachment = (fname, gen.data, qa.mime_type or "image/png")
            attached = True
            row.update(attachment_filename=fname, attachment_path=img_path,
                       visual_status="generated")
            break
        else:
            # stricter prompt for the (single) regeneration
            cur_prompt = prompt + (
                "\n\nStricter: absolutely no text overlays, no logos, no numbers, no "
                "chart/graph shapes, no faces; keep all three frames purely visual."
            )

    if not attached:
        fails = "; ".join(qa.failures) if qa else "unknown QA failure"
        row.update(draft_action="skipped", visual_status="failed_qa",
                   status=vco_config.STATUS["BLOCKED_ON_VISUAL_QA"],
                   notes=("image failed QA after regeneration: " + fails)[:300])
        # No attachment → build a NON-misleading preview with no attachment language.
        _write_preview(cfg, item, company, date_str, assets_dir, attached=False,
                       attachment=None, row=row)
        return row

    # 4. build bodies WITH the attachment sentence + the raw MIME
    subject, plaintext, html = vco_copy.build_bodies(item, cfg.postal_address, attached=True)
    vco_copy.assert_attachment_language_consistent(plaintext, attached=True)
    vco_copy.assert_attachment_language_consistent(html, attached=True)
    row["body_says_attached"] = "yes"
    raw = mime_builder.build_raw(
        from_addr=cfg.expected_account, to_addr=recipient or "REDACTED@dry-run.local",
        subject=subject, plaintext=plaintext, html=html, attachment=attachment)
    # Save the raw MIME preview outside the repo for operator inspection.
    raw_path = os.path.join(assets_dir, f"draft_{slugify(company)}_{date_str}.raw.b64url")
    with open(raw_path, "w", encoding="utf-8") as fh:
        fh.write(raw)

    if not cfg.is_live:
        row.update(draft_action="skipped", visual_status="generated",
                   status=vco_config.STATUS["DRY_RUN_OK"],
                   notes=f"dry-run: image generated + QA passed; raw MIME preview at "
                         f"{os.path.basename(raw_path)}; NO Gmail write")
        return row

    # 5. LIVE — create or update the draft (never send)
    #   Retrofit mode updates the existing draft in place. If no manifest draft id is
    #   known for this lead, we do NOT silently create a new draft (that could duplicate
    #   an existing one) unless duplicate replacements were explicitly authorized.
    retrofit = (cfg.source_kind == "existing-gmail-drafts"
                and not cfg.allow_duplicate_replacement_drafts)
    if retrofit and not draft_id:
        row.update(draft_action="skipped", visual_status="generated",
                   status=vco_config.STATUS["NEEDS_CHARLES_REVIEW"],
                   notes="retrofit: no existing draft id in manifest for this lead; "
                         "not creating a duplicate (pass --allow-duplicate-replacement-"
                         "drafts to override)")
        return row
    try:
        if retrofit:
            resp = gmail_backend.update_draft(draft_id, raw)
            action = "updated"
            new_status = vco_config.STATUS["DRAFT_UPDATED_WITH_ATTACHMENT"]
        else:
            resp = gmail_backend.create_draft(raw)
            action = "created"
            new_status = vco_config.STATUS["DRAFT_CREATED_WITH_ATTACHMENT"]
    except safety.SendForbiddenError as exc:
        row.update(draft_action="blocked", visual_status="generated",
                   status=vco_config.STATUS["NEEDS_CHARLES_REVIEW"],
                   notes=f"send guard tripped (unexpected): {exc}")
        return row

    new_draft_id = (resp or {}).get("id", draft_id)
    row["draft_id"] = new_draft_id
    row["draft_action"] = action

    # 6. verify draft-only — record the OBSERVED sent signal (not a constant) so the
    #    final invariant in main() can actually catch a real delivery.
    verdict = gmail_backend.verify_draft_only(new_draft_id)
    row["_observed_sent"] = bool(verdict.get("is_sent"))
    if verdict.get("draft_only"):
        row.update(visual_status="attached", gmail_draft_confirmed="yes",
                   status=new_status,
                   notes=f"draft-only verified (labels={verdict.get('label_ids')})")
    else:
        row.update(visual_status="attached", gmail_draft_confirmed="no",
                   status=vco_config.STATUS["NEEDS_CHARLES_REVIEW"],
                   notes=(f"draft-only NOT confirmed (is_draft={verdict.get('is_draft')}, "
                          f"is_sent={verdict.get('is_sent')}, "
                          f"labels={verdict.get('label_ids')})"))
    return row


def _write_preview(cfg, item, company, date_str, assets_dir, attached, attachment, row):
    """Write a non-attached body preview (dry-run / blocked) with no misleading copy."""
    try:
        subject, plaintext, html = vco_copy.build_bodies(item, cfg.postal_address,
                                                         attached=attached)
        vco_copy.assert_attachment_language_consistent(plaintext, attached=attached)
        preview_path = os.path.join(
            assets_dir, f"preview_{slugify(company)}_{date_str}.txt")
        with open(preview_path, "w", encoding="utf-8") as fh:
            fh.write("SUBJECT: " + subject + "\n\n" + plaintext)
    except Exception as exc:  # preview is best-effort; never crash the run
        row["notes"] = (row.get("notes", "") + f" | preview_error: {exc}")[:300]


# ── sample-only mode ───────────────────────────────────────────────────────────────
def _stamp_from_now(now: str) -> str:
    """'2026-07-08T09:15:30' -> '2026-07-08_0915' for the sample-run report filename."""
    core = (now or "")[:16]                    # YYYY-MM-DDTHH:MM
    return core.replace("T", "_").replace(":", "")


def run_sample_preflight(cfg, image_client, gmail_backend) -> tuple:
    """Structural preflight for --sample-only. Gates ONLY hard-safety conditions.

    Image/Gmail access are recorded as informational notes (not hard gates) so each
    candidate can still emit a brief + prompt + local preview when access is blocked.
    """
    notes = []
    ok = True

    notes.append(f"Sample-only mode: hard cap {vco_config.MAX_SAMPLE_DRAFTS} outputs; "
                 f"effective limit {min(cfg.limit, vco_config.MAX_SAMPLE_DRAFTS)}.")
    notes.append("Send guard active: drafts.create/update/get only; any *send* op raises.")

    # approval packet present
    if not os.path.exists(os.path.expanduser(cfg.approval_packet_path)):
        ok = False
        notes.append(f"BLOCKED_ON_APPROVAL_PACKET_PARSE: not found: {cfg.approval_packet_path}")
    else:
        notes.append(f"Approval packet present: {os.path.basename(cfg.approval_packet_path)}")
    if cfg.candidate_csv_path and os.path.exists(os.path.expanduser(cfg.candidate_csv_path)):
        notes.append(f"Candidate CSV present: {os.path.basename(cfg.candidate_csv_path)}")
    else:
        notes.append("Candidate CSV not provided/found: details come from the packet only.")

    # output dirs OUTSIDE the repo
    for label, d in (("assets", cfg.resolved_assets_dir()), ("reports", cfg.reports_dir)):
        if _under_repo(d, cfg.repo_root):
            ok = False
            notes.append(f"REFUSED: {label} dir is inside the repo: {d}")
    if ok:
        notes.append("Output dirs are outside the repo.")
    if not _under_repo(cfg.reports_dir, cfg.repo_root):
        try:
            os.makedirs(cfg.reports_dir, exist_ok=True)
            notes.append("Report directory is writable.")
        except OSError as exc:
            ok = False
            notes.append(f"Report dir not writable: {exc}")

    # informational: image access (never a hard gate in sample mode)
    pf = image_client.preflight()
    notes.append(f"gpt-image-2 access: {'OK' if pf['ok'] else 'UNAVAILABLE'} — "
                 f"{safety.redact_secrets(pf['detail'])}")

    # live-only gates (Gmail account + resolved postal)
    if cfg.is_live:
        notes.append("Live mode requested (--live-drafts): Gmail draft writes will be attempted.")
        try:
            acct = gmail_backend.verify_account()
            notes.append(f"Gmail account verified: {safety.mask_recipient(acct)}")
        except (GmailApiUnavailable, safety.WrongAccountError, safety.SendForbiddenError) as exc:
            ok = False
            notes.append(f"BLOCKED_ON_GMAIL_DRAFT_ACCESS: {safety.redact_secrets(str(exc))}")
        if not vco_config.postal_resolved(cfg.postal_address):
            ok = False
            notes.append("BLOCKED: postal address unresolved — live drafts require the "
                         "resolved compliance footer (resolved-or-block).")
    else:
        notes.append("Dry-run (default): no Gmail draft will be created; local previews only.")

    return ok, notes


def _new_sample_row(cfg, item, sample_id, recipient) -> dict:
    return {
        # sample-report (section-12) fields
        "sample_id": sample_id,
        "company": item.get("business_name") or item.get("company") or "unknown",
        "domain": item.get("domain", ""),
        "selected_from": item.get("selected_from", ""),
        "decision_source": item.get("decision_source", ""),
        "draft_status": "local_preview",
        "gmail_draft_id": "",
        "visual_status": "not_created",
        "image_model": "",
        "image_path": "",
        "attachment_status": "none",
        "body_says_attached": "no",
        "fabrication_check_passed": "yes",
        "gmail_draft_confirmed": "no",
        "sent_or_scheduled": "no",
        # standard-report + activity-log fields (superset; extras ignored on write)
        "batch_id": cfg.batch_id,
        "mode": cfg.mode,
        "safe_recipient_identifier": safety.mask_recipient(recipient),
        "source_record_id": item.get("lead_id", ""),
        "duplicate_check_result": "unique",
        "draft_id": "",
        "draft_action": "skipped",
        "attachment_filename": "",
        "attachment_path": "",
        "gpt_image_model_used": "",
        "gpt_image_size": cfg.image_size,
        "notes": "",
        "status": vco_config.STATUS["NOT_STARTED"],
    }


def _write_visual_brief_md(path, item, brief, prompt) -> None:
    lines = [
        f"# Visual brief — {brief.company_name}",
        "",
        f"- **Company:** {brief.company_name}",
        f"- **Domain:** {item.get('domain','')}",
        f"- **Category:** {brief.product_or_category}",
        f"- **Verified product/company detail:** {brief.one_verified_detail or '(none verified)'}",
        f"- **Why MOTIONX fits:** {brief.why_motion_fits}",
        f"- **Selected from:** {item.get('selected_from','')}",
        f"- **Decision source:** {item.get('decision_source','')}",
        "",
        "## Frame 1 — cinematic product/world opening",
        brief.frame1,
        "",
        "## Frame 2 — motion / interaction / transformation moment",
        brief.frame2,
        "",
        "## Frame 3 — extension into launch page / website / campaign system",
        brief.frame3,
        "",
        "## Uncertainty flags",
    ]
    flags = list(brief.uncertainty_flags) + list(item.get("uncertainty_flags", []))
    lines += [f"- {f}" for f in flags] or ["- (none)"]
    lines += ["", "## gpt-image-2 prompt", "", "```", prompt, "```", ""]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def process_sample_candidate(cfg, image_client, gmail_backend, item, seen_leads,
                             date_str, idx) -> dict:
    """One sample candidate: brief → prompt → (image if access) → QA → sample copy →
    Gmail draft (live+attachment+recipient) OR local preview. Never sends."""
    sample_id = f"S{idx:02d}"
    recipient = item.get("recipient_email", "")
    company = item.get("business_name") or item.get("company") or "unknown"
    row = _new_sample_row(cfg, item, sample_id, recipient)

    # duplicate within the (tiny) sample set
    lead_id = item.get("lead_id", "")
    if lead_id and lead_id in seen_leads:
        row.update(duplicate_check_result="duplicate_in_batch", draft_action="skipped",
                   draft_status="blocked_duplicate",
                   status=vco_config.STATUS["SKIPPED_DUPLICATE"],
                   notes="duplicate candidate id within sample set")
        return row
    if lead_id:
        seen_leads.add(lead_id)

    # 1. brief + fabrication guard (field-level)
    brief = vco_brief.build_brief(item)
    if brief.fabrication_findings:
        row.update(fabrication_check_passed="no", draft_action="blocked",
                   draft_status="blocked_fabrication",
                   status=vco_config.STATUS["BLOCKED_ON_FABRICATION"],
                   notes="; ".join(brief.fabrication_findings)[:300])
        return row
    prompt = vco_brief.build_image_prompt(brief)
    prompt_fab = vco_brief.prompt_is_clean(prompt)
    if prompt_fab:
        row.update(fabrication_check_passed="no", draft_action="blocked",
                   draft_status="blocked_fabrication",
                   status=vco_config.STATUS["BLOCKED_ON_FABRICATION"],
                   notes="; ".join(prompt_fab)[:300])
        return row

    # 1b. fabrication scan of the COMPOSED sample email body (defence in depth)
    subj_probe, plain_probe, _ = vco_sample_copy.build_sample_bodies(
        item, vco_config.POSTAL_PLACEHOLDER, attached=False)
    body_fab = vco_brief.scan_fabrication(subj_probe, plain_probe)
    if body_fab:
        row.update(fabrication_check_passed="no", draft_action="blocked",
                   draft_status="blocked_fabrication",
                   status=vco_config.STATUS["BLOCKED_ON_FABRICATION"],
                   notes=("sample body fabrication: " + "; ".join(body_fab))[:300])
        return row

    # persist brief + prompt + human-readable brief (outside repo)
    assets_dir = cfg.resolved_assets_dir()
    os.makedirs(assets_dir, exist_ok=True)
    slug = slugify(company)
    with open(os.path.join(assets_dir, f"brief_{slug}_{date_str}.json"), "w",
              encoding="utf-8") as fh:
        json.dump({"brief": brief.to_dict(), "prompt": prompt,
                   "selected_from": item.get("selected_from", ""),
                   "decision_source": item.get("decision_source", "")}, fh, indent=2)
    with open(os.path.join(assets_dir, f"prompt_{slug}_{date_str}.txt"), "w",
              encoding="utf-8") as fh:
        fh.write(prompt + "\n")
    _write_visual_brief_md(
        os.path.join(assets_dir, f"visualbrief_{slug}_{date_str}.md"), item, brief, prompt)

    # 2. image generation (attempted iff live or explicitly asked in dry-run)
    attachment = None
    attached = False
    image_access_blocked = False
    will_generate = cfg.is_live or cfg.generate_images_in_dry_run
    if will_generate:
        qa = None
        attempt = 0
        max_attempts = 1 + max(0, cfg.max_image_regenerations)
        cur_prompt = prompt
        while attempt < max_attempts:
            attempt += 1
            try:
                gen = image_client.generate(cur_prompt, size=cfg.image_size,
                                            quality=cfg.image_quality,
                                            image_format=cfg.image_format)
            except vco_image.ImageAccessError as exc:
                image_access_blocked = True
                row.update(visual_status="blocked_access",
                           image_model="gpt-image-2 (access blocked)",
                           attachment_status="blocked",
                           status=vco_config.STATUS["BLOCKED_ON_GPT_IMAGE_2_ACCESS"],
                           notes=("gpt-image-2 access blocked: "
                                  + safety.redact_secrets(str(exc)))[:300])
                break
            except vco_image.ImageGenerationError as exc:
                row.update(visual_status="failed_generation",
                           attachment_status="blocked",
                           status=vco_config.STATUS["BLOCKED_ON_VISUAL_GENERATION"],
                           notes=safety.redact_secrets(str(exc))[:300])
                break
            row["gpt_image_model_used"] = gen.model
            row["image_model"] = gen.model
            fname = attachment_filename(company, date_str, cfg.image_format)
            img_path = os.path.join(assets_dir, fname)
            vco_image.save_image_bytes(img_path, gen.data, repo_root=cfg.repo_root)
            qa = vco_qa.qa_image_file(
                path=img_path, expected_company=brief.company_name,
                manifest_company=company, brief=brief, prompt=cur_prompt,
                expected_format=cfg.image_format)
            if qa.passed:
                attachment = (fname, gen.data, qa.mime_type or "image/png")
                attached = True
                row.update(attachment_filename=fname, attachment_path=img_path,
                           image_path=img_path, visual_status="generated",
                           attachment_status="attached")
                break
            cur_prompt = prompt + (
                "\n\nStricter: absolutely no text overlays, no logos, no numbers, no "
                "chart/graph shapes, no faces; keep all three frames purely visual.")
        if will_generate and not attached and not image_access_blocked and qa is not None:
            row.update(visual_status="failed_qa", attachment_status="blocked",
                       status=vco_config.STATUS["BLOCKED_ON_VISUAL_QA"],
                       notes=("image failed QA after regeneration: "
                              + "; ".join(qa.failures))[:300])
    else:
        row.update(visual_status="planned")

    # 3. compose the sample email (attachment sentence iff an image is attached)
    body_postal = cfg.postal_address if cfg.is_live else vco_config.POSTAL_PLACEHOLDER
    subject, plaintext, html = vco_sample_copy.build_sample_bodies(
        item, body_postal, attached=attached)
    vco_copy.assert_attachment_language_consistent(plaintext, attached=attached)
    row["body_says_attached"] = "yes" if attached else "no"

    # local preview (always) + raw MIME preview (only when an image is attached)
    with open(os.path.join(assets_dir, f"sample_{slug}_{date_str}.txt"), "w",
              encoding="utf-8") as fh:
        fh.write("SUBJECT: " + subject + "\n\n" + plaintext)
    if attached:
        raw = mime_builder.build_raw(
            from_addr=cfg.expected_account,
            to_addr=recipient or "REDACTED@dry-run.local",
            subject=subject, plaintext=plaintext, html=html, attachment=attachment)
        with open(os.path.join(assets_dir, f"sample_{slug}_{date_str}.raw.b64url"), "w",
                  encoding="utf-8") as fh:
            fh.write(raw)

    # 4. dry-run → a local preview is ALWAYS written (no Gmail write). draft_status is
    #    'local_preview' regardless; any image blocker stays in visual_status/status/notes.
    if not cfg.is_live:
        row.update(draft_status="local_preview", draft_action="skipped")
        if image_access_blocked or row["visual_status"] in ("failed_qa", "failed_generation"):
            row["notes"] = (row["notes"]
                            + " | local preview written outside the repo (no attachment)").strip(" |")
        else:
            row.update(status=vco_config.STATUS["SAMPLE_PREVIEW_WRITTEN"],
                       notes=(row["notes"]
                              + " | dry-run sample preview written outside the repo").strip(" |"))
        return row

    # 5. LIVE — create a Gmail DRAFT only, and only with a verified recipient + attachment
    if not recipient:
        row.update(draft_status="blocked_recipient", draft_action="blocked",
                   status=vco_config.STATUS["BLOCKED_ON_RECIPIENT_UNVERIFIED"],
                   notes=("no verified recipient email (only a public contact page); "
                          "refusing to guess an address — local preview written")[:300])
        return row
    if not attached:
        row.update(draft_status="blocked_visual", draft_action="blocked",
                   status=vco_config.STATUS["BLOCKED_ON_GMAIL_DRAFT_ACCESS"],
                   notes=("no attachment available (image blocked/failed) — refusing to "
                          "create a draft that promises a sketch; local preview written")[:300])
        return row

    live_raw = mime_builder.build_raw(
        from_addr=cfg.expected_account, to_addr=recipient,
        subject=subject, plaintext=plaintext, html=html, attachment=attachment)
    try:
        resp = gmail_backend.create_draft(live_raw)
    except safety.SendForbiddenError as exc:
        row.update(draft_status="blocked_visual", draft_action="blocked",
                   status=vco_config.STATUS["NEEDS_CHARLES_REVIEW"],
                   notes=f"send guard tripped (unexpected): {exc}")
        return row
    new_id = (resp or {}).get("id", "")
    row.update(draft_id=safety.mask_draft_id(new_id),
               gmail_draft_id=safety.mask_draft_id(new_id),
               draft_action="created", draft_status="gmail_draft_created")
    verdict = gmail_backend.verify_draft_only(new_id)
    row["_observed_sent"] = bool(verdict.get("is_sent"))
    if verdict.get("draft_only"):
        row.update(visual_status="attached", gmail_draft_confirmed="yes",
                   status=vco_config.STATUS["DRAFT_CREATED_WITH_ATTACHMENT"],
                   notes=f"draft-only verified (labels={verdict.get('label_ids')})")
    else:
        row.update(visual_status="attached", gmail_draft_confirmed="no",
                   status=vco_config.STATUS["NEEDS_CHARLES_REVIEW"],
                   notes=(f"draft-only NOT confirmed (is_draft={verdict.get('is_draft')}, "
                          f"is_sent={verdict.get('is_sent')}, "
                          f"labels={verdict.get('label_ids')})"))
    return row


def run_sample(cfg, image_client, gmail_backend, today, now) -> int:
    print("=== SAMPLE PREFLIGHT ===")
    ok, notes = run_sample_preflight(cfg, image_client, gmail_backend)
    for n in notes:
        print(" -", n)
    effective_limit = min(cfg.limit, vco_config.MAX_SAMPLE_DRAFTS)

    if not ok:
        print("\nSample preflight FAILED — no candidates processed, no Gmail writes.")
        _finalize_sample(cfg, [], notes, ["sample preflight failed — see notes"], now)
        return 1

    # ingest + select the top-N APPROVE candidates
    try:
        candidates = vco_sample_src.load_candidates(cfg.approval_packet_path,
                                                    cfg.candidate_csv_path)
        chosen = vco_sample_src.select_top_approve(candidates, effective_limit)
    except vco_sample_src.SampleParseError as exc:
        blk = f"BLOCKED_ON_APPROVAL_PACKET_PARSE: {safety.redact_secrets(str(exc))}"
        print("\n" + blk)
        _finalize_sample(cfg, [], notes, [blk], now)
        return 1
    if not chosen:
        blk = "BLOCKED_ON_APPROVAL_PACKET_PARSE: no APPROVE candidates could be selected"
        print("\n" + blk)
        _finalize_sample(cfg, [], notes, [blk], now)
        return 1

    approve_n = sum(1 for c in candidates if c.decision.upper() == "APPROVE")
    print(f"\n=== SELECTED {len(chosen)}/{effective_limit} sample candidate(s) "
          f"(APPROVE pool={approve_n}) — mode={cfg.mode} ===")

    seen: set = set()
    rows = []
    for i, cand in enumerate(chosen, start=1):
        row = process_sample_candidate(cfg, image_client, gmail_backend,
                                       cand.to_item(), seen, today, i)
        rows.append(row)
        print(f" - {row['sample_id']} {row['company']}: {row['status']} "
              f"(draft={row['draft_status']}, visual={row['visual_status']}, "
              f"attached={row['body_says_attached']})")

    blockers = sorted({r["status"] for r in rows if str(r["status"]).startswith("BLOCKED")})
    _finalize_sample(cfg, rows, notes, blockers, now)

    if any(r.get("_observed_sent") for r in rows):
        raise RuntimeError(
            "INVARIANT VIOLATION: a sample draft's message carries the SENT label — "
            "this DRAFT_ONLY workflow must never produce a sent message.")
    print("\nDONE. No email was sent or scheduled.")
    return 0


def _finalize_sample(cfg, rows, notes, blockers, now):
    for d in (cfg.reports_dir, os.path.dirname(cfg.resolved_activity_log())):
        if _under_repo(d, cfg.repo_root):
            print(f"REFUSED: not writing reports inside the repo ({d}).", file=sys.stderr)
            return
    os.makedirs(cfg.reports_dir, exist_ok=True)
    stamp = _stamp_from_now(now)
    csv_path = os.path.join(cfg.reports_dir, f"batch32_vco_sample_run_{stamp}.csv")
    md_path = os.path.join(cfg.reports_dir, f"batch32_vco_sample_run_{stamp}.md")
    vco_report.write_sample_report_csv(csv_path, rows)
    vco_report.write_sample_summary_md(md_path, cfg.batch_id, cfg.mode, rows, notes, blockers)
    # also fold sample rows into the dedicated (masked, scrubbed) visual activity log
    vco_report.append_activity_log(cfg.resolved_activity_log(), rows, now)
    print(f"\nSample report:  {csv_path}")
    print(f"Sample summary: {md_path}")
    print(f"Activity log:   {cfg.resolved_activity_log()}")


# ── argparse ─────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="visual_cold_open.run_batch",
        description="MOTIONX visual cold-open (gpt-image-2 + Gmail attachment) — DRAFT_ONLY.")
    p.add_argument("--visual-cold-open", action="store_true",
                   help="explicit opt-in to the visual cold-open mode (required)")
    p.add_argument("--image-model", default=vco_config.REQUIRED_IMAGE_MODEL,
                   help="image model (must be gpt-image-2)")
    p.add_argument("--image-size", default=vco_config.DEFAULT_IMAGE_SIZE)
    p.add_argument("--image-quality", default=vco_config.DEFAULT_IMAGE_QUALITY,
                   choices=["medium", "high"])
    p.add_argument("--image-format", default=vco_config.DEFAULT_IMAGE_FORMAT)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="default; no Gmail writes")
    mode.add_argument("--live-drafts", action="store_true",
                      help="create/update Gmail drafts with attachments (never sends)")
    # NOTE: 'live-drafts' is intentionally NOT a --mode choice. Live Gmail writes are
    # reachable ONLY via the dedicated --live-drafts flag, so there is exactly one
    # explicit door into live mode.
    p.add_argument("--mode", choices=["dry-run", "preflight"], default=None)
    p.add_argument("--source", dest="source_kind", default="drafts-json",
                   choices=["drafts-json", "existing-gmail-drafts", "batch32-approval-packet"])
    p.add_argument("--prospect-source", default="",
                   help="path to a normalized drafts.json (has 'items'); required "
                        "unless --sample-only ingests an approval packet")
    # ── sample-only mode (approval-packet ingestion) ────────────────────────────
    p.add_argument("--sample-only", action="store_true",
                   help="produce at most %d sample drafts/previews from an approval "
                        "packet (top APPROVE candidates); never the full batch"
                        % vco_config.MAX_SAMPLE_DRAFTS)
    p.add_argument("--approval-packet", dest="approval_packet_path", default="",
                   help="batch32 candidate approval packet (.md) — the decision source")
    p.add_argument("--candidate-csv", dest="candidate_csv_path", default="",
                   help="batch32 sourcing candidates (.csv) — the verified-detail source")
    # ── manual-visuals mode: no OpenAI API image generation ─────────────────
    p.add_argument("--manual-visuals", nargs="?", const="prompt-pack", default="",
                   choices=vco_manual.MANUAL_MODES,
                   help="human-in-the-loop visuals mode: prompt-pack, chatgpt-bulk-pack, "
                        "collect-downloads, import-images, preview-with-images, or "
                        "live-drafts-with-manual-images")
    p.add_argument("--manual-visuals-mode", default="", choices=vco_manual.MANUAL_MODES,
                   help="equivalent explicit mode flag for shells that prefer key/value args")
    p.add_argument("--manual-root-dir", default=vco_config.DEFAULT_MANUAL_VISUALS_DIR,
                   help="manual visual workspace root (default ~/.motionx-outreach/manual-visuals)")
    p.add_argument("--manual-image-dir", default="",
                   help="directory containing Charles-generated images for import/preview/live")
    p.add_argument("--manual-manifest", dest="manual_manifest_path", default="",
                   help="manual visuals manifest.csv from prompt-pack mode")
    p.add_argument("--download-dir", default=os.path.expanduser("~/Downloads"),
                   help="source folder for collect-downloads (default ~/Downloads)")
    p.add_argument("--download-since-minutes", type=int, default=180,
                   help="collect only image downloads newer than this many minutes "
                        "(default 180)")
    p.add_argument("--allow-overwrite", action="store_true",
                   help="allow collect-downloads to replace existing images_ready files")
    p.add_argument("--collect-dry-run", action="store_true",
                   help="plan collect-downloads mapping without copying files")
    p.add_argument("--manifest", dest="manifest_path", default="",
                   help="created_manifest.json (lead_id->draft_id) for retrofit")
    p.add_argument("--allow-update-existing-drafts", action="store_true")
    p.add_argument("--allow-duplicate-replacement-drafts", action="store_true")
    p.add_argument("--max-image-regenerations", type=int,
                   default=vco_config.DEFAULT_MAX_IMAGE_REGENERATIONS)
    p.add_argument("--batch-id", default="")
    p.add_argument("--limit", type=int, default=vco_config.DEFAULT_LIMIT)
    p.add_argument("--report-path", dest="reports_dir", default=vco_config.DEFAULT_REPORTS_DIR)
    p.add_argument("--asset-dir", dest="assets_dir", default="")
    p.add_argument("--generate-images-in-dry-run", action="store_true")
    p.add_argument("--generate-test-image", action="store_true",
                   help="generate exactly ONE test image (real API) outside the repo")
    p.add_argument("--postal-address", default="")
    p.add_argument("--gmail-credentials", dest="gmail_credentials_path", default="")
    p.add_argument("--gmail-token", dest="gmail_token_path", default="")
    p.add_argument("--expected-account", default=vco_config.SENDING_MAILBOX)
    return p


def config_from_args(ns) -> vco_config.VCOConfig:
    mode = "dry-run"
    if ns.mode:
        mode = ns.mode
    if ns.live_drafts:
        mode = "live-drafts"
    if ns.dry_run:
        mode = "dry-run"
    cfg = vco_config.VCOConfig(
        mode=mode,
        image_model=ns.image_model,
        image_size=ns.image_size,
        image_quality=ns.image_quality,
        image_format=ns.image_format,
        limit=ns.limit,
        max_image_regenerations=ns.max_image_regenerations,
        batch_id=ns.batch_id or _derive_batch_id(ns.prospect_source or ns.approval_packet_path),
        prospect_source=os.path.expanduser(ns.prospect_source),
        source_kind=ns.source_kind,
        allow_update_existing_drafts=ns.allow_update_existing_drafts,
        allow_duplicate_replacement_drafts=ns.allow_duplicate_replacement_drafts,
        generate_images_in_dry_run=ns.generate_images_in_dry_run,
        generate_test_image=ns.generate_test_image,
        sample_only=ns.sample_only,
        approval_packet_path=os.path.expanduser(ns.approval_packet_path)
        if ns.approval_packet_path else "",
        candidate_csv_path=os.path.expanduser(ns.candidate_csv_path)
        if ns.candidate_csv_path else "",
        manual_visuals_mode=ns.manual_visuals_mode or ns.manual_visuals,
        manual_root_dir=os.path.expanduser(ns.manual_root_dir),
        manual_image_dir=os.path.expanduser(ns.manual_image_dir)
        if ns.manual_image_dir else "",
        manual_manifest_path=os.path.expanduser(ns.manual_manifest_path)
        if ns.manual_manifest_path else "",
        download_dir=os.path.expanduser(ns.download_dir),
        download_since_minutes=ns.download_since_minutes,
        allow_overwrite=ns.allow_overwrite,
        collect_dry_run=ns.collect_dry_run,
        reports_dir=os.path.expanduser(ns.reports_dir),
        assets_dir=os.path.expanduser(ns.assets_dir) if ns.assets_dir else "",
        expected_account=ns.expected_account,
        postal_address=vco_config.read_postal_address(ns.postal_address),
        gmail_credentials_path=os.path.expanduser(ns.gmail_credentials_path)
        if ns.gmail_credentials_path else "",
        gmail_token_path=os.path.expanduser(ns.gmail_token_path)
        if ns.gmail_token_path else "",
        repo_root=_REPO_ROOT,
    )
    cfg.manifest_path = os.path.expanduser(ns.manifest_path) if ns.manifest_path else ""
    return cfg


def _derive_batch_id(source_path: str) -> str:
    base = os.path.basename(source_path or "")
    m = re.search(r"(batch\d+)", base)
    return (m.group(1) + "-visual") if m else "visual-cold-open"


def main(argv=None, image_client=None, gmail_backend=None) -> int:
    ns = build_parser().parse_args(argv)
    if not ns.visual_cold_open:
        print("ERROR: --visual-cold-open is required to run this mode.", file=sys.stderr)
        return 2
    manual_mode = ns.manual_visuals_mode or ns.manual_visuals
    if ns.image_model != vco_config.REQUIRED_IMAGE_MODEL:
        print(f"ERROR: this mode requires --image-model {vco_config.REQUIRED_IMAGE_MODEL} "
              f"(a downgrade needs Charles's explicit authorization).", file=sys.stderr)
        return 2
    if ns.limit < 0:
        print("ERROR: --limit must be >= 0 (a negative limit would silently drop "
              "trailing prospects).", file=sys.stderr)
        return 2
    if not manual_mode and not ns.sample_only and not ns.prospect_source:
        print("ERROR: --prospect-source is required (or use --sample-only with "
              "--approval-packet).", file=sys.stderr)
        return 2
    if (ns.sample_only and ns.source_kind == "batch32-approval-packet"
            and not ns.approval_packet_path):
        print("ERROR: --sample-only --source batch32-approval-packet requires "
              "--approval-packet PATH.", file=sys.stderr)
        return 2
    if manual_mode in ("prompt-pack", "chatgpt-bulk-pack") and not ns.approval_packet_path:
        print(f"ERROR: --manual-visuals {manual_mode} requires --approval-packet PATH.",
              file=sys.stderr)
        return 2
    if manual_mode in ("collect-downloads", "import-images", "preview-with-images",
                       "live-drafts-with-manual-images") and not ns.manual_manifest_path:
        print("ERROR: manual collect/import/preview/live modes require "
              "--manual-manifest PATH.",
              file=sys.stderr)
        return 2
    if manual_mode == "live-drafts-with-manual-images" and not ns.live_drafts:
        print("ERROR: live-drafts-with-manual-images requires --live-drafts.",
              file=sys.stderr)
        return 2

    cfg = config_from_args(ns)
    today = datetime.date.today().isoformat()
    now = datetime.datetime.now().isoformat(timespec="seconds")

    # Clients (injected in tests; lazily real otherwise). Manual-visuals modes never use
    # the image client, so no OPENAI_API_KEY is needed for those paths.
    if image_client is None and not cfg.manual_visuals_mode:
        image_client = vco_image.GptImageClient(model=cfg.image_model)
    if gmail_backend is None:
        gmail_backend = GmailDraftBackend(
            credentials_path=cfg.gmail_credentials_path,
            token_path=cfg.gmail_token_path,
            expected_account=cfg.expected_account)

    if cfg.manual_visuals_mode:
        return vco_manual.run_manual_visuals(cfg, gmail_backend, today, now)

    # Sample-only mode has its own ingestion + preflight + copy + report path. The
    # normalized workflow below is left completely unchanged (success criterion).
    if cfg.sample_only:
        return run_sample(cfg, image_client, gmail_backend, today, now)

    ok, notes = run_preflight(cfg, image_client, gmail_backend)
    print("=== PREFLIGHT ===")
    for n in notes:
        print(" -", n)
    if not ok:
        print("\nPreflight FAILED — no prospects processed, no Gmail writes.")
        _finalize(cfg, [], notes, now)
        return 1
    if cfg.mode == "preflight":
        print("\nPreflight-only mode: preflight OK. No prospects processed.")
        _finalize(cfg, [], notes, now)
        return 0

    # Test-image-only path: generate exactly one image, no drafts.
    if cfg.generate_test_image:
        return _generate_test_image(cfg, image_client, today)

    items = load_items(cfg)[: cfg.limit]
    print(f"\n=== PROCESSING {len(items)} prospect(s) — mode={cfg.mode} ===")
    seen: set = set()
    rows = []
    for item, draft_id in items:
        row = process_prospect(cfg, image_client, gmail_backend, item, draft_id, seen, today)
        rows.append(row)
        print(f" - {row['company']}: {row['status']} "
              f"(action={row['draft_action']}, visual={row['visual_status']})")

    _finalize(cfg, rows, notes, now)

    # Hard final invariant, derived from the OBSERVED Gmail label state (not a constant)
    # so it can actually catch a real delivery. Raise (not assert — survives python -O).
    if any(r.get("_observed_sent") for r in rows):
        raise RuntimeError(
            "INVARIANT VIOLATION: a processed draft's message carries the SENT label — "
            "this DRAFT_ONLY workflow must never produce a sent message.")
    print("\nDONE. No email was sent or scheduled.")
    return 0


def _generate_test_image(cfg, image_client, today) -> int:
    demo = {
        "business_name": "Test Studio", "category": "consumer product brand",
        "verified_observation": "the homepage shows a single hero product shot",
        "proposed_creative_direction": "a slow cinematic reveal of the product",
        "specific_opportunity": "a launch page that reuses the film's opening frame",
    }
    brief = vco_brief.build_brief(demo)
    prompt = vco_brief.build_image_prompt(brief)
    try:
        gen = image_client.generate(prompt, size=cfg.image_size,
                                    quality=cfg.image_quality, image_format=cfg.image_format)
    except Exception as exc:
        print("test image FAILED:", safety.redact_secrets(str(exc)), file=sys.stderr)
        return 1
    assets_dir = cfg.resolved_assets_dir()
    path = os.path.join(assets_dir,
                        f"motionx_visual_cold_open_test_{today}.{format_ext(cfg.image_format)}")
    vco_image.save_image_bytes(path, gen.data, repo_root=cfg.repo_root)
    print(f"test image written outside the repo: {path} ({gen.byte_len} bytes)")
    return 0


def _finalize(cfg, rows, notes, now):
    # Fail-closed: never write reports/logs inside the repo, even on the preflight-fail
    # path where this runs with the refused (in-repo) directory.
    for d in (cfg.reports_dir, os.path.dirname(cfg.resolved_activity_log())):
        if _under_repo(d, cfg.repo_root):
            print(f"REFUSED: not writing reports inside the repo ({d}). "
                  f"Pass --report-path pointing outside the repo.", file=sys.stderr)
            return
    os.makedirs(cfg.reports_dir, exist_ok=True)
    csv_path = os.path.join(cfg.reports_dir, f"{cfg.batch_id}_visual_cold_open_report.csv")
    md_path = os.path.join(cfg.reports_dir, f"{cfg.batch_id}_visual_cold_open_summary.md")
    vco_report.write_report_csv(csv_path, rows)
    vco_report.write_summary_md(md_path, cfg.batch_id, cfg.mode, rows, notes)
    vco_report.append_activity_log(cfg.resolved_activity_log(), rows, now)
    print(f"\nReport:  {csv_path}")
    print(f"Summary: {md_path}")
    print(f"Activity log: {cfg.resolved_activity_log()}")


if __name__ == "__main__":
    raise SystemExit(main())
