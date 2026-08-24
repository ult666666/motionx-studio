# -*- coding: utf-8 -*-
"""MOTIONX visual-cold-open — no-API-cost manual visuals workflow.

This module keeps the human-in-the-loop path separate from the gpt-image-2 path:
Codex writes copy + GPT-5.5 Pro Chat prompt packs, Charles manually creates one image
per prompt in ChatGPT, and Codex later validates local image files and optionally
creates DRAFT_ONLY Gmail drafts with those manual attachments.

No function here calls OpenAI APIs, mutates CRM files, sends email, schedules email,
or touches Gmail unless the explicit live-drafts-with-manual-images mode passes every
draft-only gate.
"""
from __future__ import annotations

import csv
import datetime
import html as _html
import os
import re
import shutil
import struct
import urllib.parse
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import brief as vco_brief
import config as vco_config
import copy_integration as vco_copy
import image_qa as vco_qa
import mime_builder
import safety
import sample_copy as vco_sample_copy
import sample_source as vco_sample_src
from gmail_draft import GmailApiUnavailable


MANUAL_MODES = (
    "prompt-pack",
    "chatgpt-bulk-pack",
    "collect-downloads",
    "import-images",
    "preview-with-images",
    "live-drafts-with-manual-images",
)

SUPPORTED_EXTS = ("png", "jpg", "jpeg", "webp")
MAX_MANUAL_IMAGE_BYTES = 25 * 1024 * 1024
MIN_MANUAL_IMAGE_BYTES = 256

MANIFEST_COLUMNS = [
    "index",
    "company",
    "domain",
    "candidate_id",
    "decision",
    "rank",
    "expected_image_filename",
    "prompt_file",
    "email_preview_file",
    "brief_file",
    "recipient_email",
    "recipient_status",
    "image_status",
    "draft_status",
]

IMPORT_REPORT_COLUMNS = [
    "batch_id",
    "index",
    "company",
    "domain",
    "candidate_id",
    "expected_image_filename",
    "actual_image_filename",
    "image_status",
    "draft_status",
    "recipient_status",
    "width",
    "height",
    "mime_type",
    "file_size_bytes",
    "notes",
]

PREVIEW_REPORT_COLUMNS = [
    "batch_id",
    "index",
    "company",
    "domain",
    "candidate_id",
    "expected_image_filename",
    "actual_image_filename",
    "image_status",
    "draft_status",
    "recipient_status",
    "body_says_attached",
    "final_email_file",
    "attachment_check_file",
    "raw_mime_file",
    "notes",
]

LIVE_REPORT_COLUMNS = [
    "batch_id",
    "index",
    "company",
    "domain",
    "candidate_id",
    "safe_recipient_identifier",
    "expected_image_filename",
    "actual_image_filename",
    "image_status",
    "draft_status",
    "draft_id",
    "gmail_draft_confirmed",
    "body_says_attached",
    "sent_or_scheduled",
    "notes",
]

COLLECT_REPORT_COLUMNS = [
    "batch_id",
    "index",
    "company",
    "domain",
    "candidate_id",
    "expected_image_filename",
    "download_source_path",
    "copied_image_path",
    "source_created_or_modified_at",
    "image_status",
    "copy_status",
    "width",
    "height",
    "mime_type",
    "file_size_bytes",
    "notes",
]


@dataclass
class ManualImageCheck:
    row: dict
    expected_filename: str
    actual_path: str = ""
    image_status: str = "MISSING"
    width: int = 0
    height: int = 0
    mime_type: str = ""
    file_size_bytes: int = 0
    failures: List[str] = field(default_factory=list)
    uncertainty_flags: List[str] = field(default_factory=list)

    @property
    def accepted(self) -> bool:
        return self.image_status == "ACCEPTED"

    @property
    def actual_filename(self) -> str:
        return os.path.basename(self.actual_path) if self.actual_path else ""

    @property
    def notes(self) -> str:
        bits = list(self.failures) + list(self.uncertainty_flags)
        return "; ".join(bits)


@dataclass
class ManualPromptEntry:
    row: dict
    item: dict
    brief: "vco_brief.VisualBrief"


@dataclass
class DownloadCandidate:
    path: str
    ts: float

    @property
    def basename(self) -> str:
        return os.path.basename(self.path)

    @property
    def stamp(self) -> str:
        return datetime.datetime.fromtimestamp(self.ts).isoformat(timespec="seconds")


def run_manual_visuals(cfg, gmail_backend, today: str, now: str) -> int:
    """Dispatch the selected manual-visuals mode."""
    mode = cfg.manual_visuals_mode
    if mode == "prompt-pack":
        return run_prompt_pack(cfg, now)
    if mode == "chatgpt-bulk-pack":
        return run_chatgpt_bulk_pack(cfg, now)
    if mode == "collect-downloads":
        return run_collect_downloads(cfg, now)
    if mode == "import-images":
        return run_import_images(cfg, now)
    if mode == "preview-with-images":
        return run_preview_with_images(cfg, now)
    if mode == "live-drafts-with-manual-images":
        return run_live_drafts_with_manual_images(cfg, gmail_backend, now)
    raise ValueError(f"unknown manual visuals mode: {mode!r}")


# ── prompt pack ────────────────────────────────────────────────────────────────
def run_prompt_pack(cfg, now: str) -> int:
    workspace = manual_workspace(cfg)
    _assert_outside_repo(workspace, cfg.repo_root)
    _assert_outside_repo(cfg.reports_dir, cfg.repo_root)
    paths = _manual_dirs(workspace)
    for d in paths.values():
        os.makedirs(d, exist_ok=True)
    _write_placeholder(os.path.join(paths["images_ready"], "PLACE_IMAGES_HERE.txt"),
                       workspace, cfg.batch_id)

    try:
        candidates = vco_sample_src.load_candidates(
            cfg.approval_packet_path, cfg.candidate_csv_path)
    except vco_sample_src.SampleParseError as exc:
        print(f"BLOCKED_ON_APPROVAL_PACKET_PARSE: {safety.redact_secrets(str(exc))}")
        return 1

    selected, skipped = _select_manual_candidates(candidates, cfg.limit)
    rows: List[dict] = []
    for idx, cand, item, brief, prompt in selected:
        slug = slugify(cand.company)
        stem = f"{idx:02d}_{slug}"
        expected_image = f"{stem}_manual_visual.png"
        prompt_rel = f"prompts/{stem}_prompt.txt"
        email_rel = f"email_previews/{stem}_email.txt"
        brief_rel = f"briefs/{stem}_brief.md"

        manual_prompt = build_manual_chat_prompt(item, brief)
        _write_text(os.path.join(workspace, prompt_rel), manual_prompt)
        _write_email_preview(os.path.join(workspace, email_rel), item)
        _write_brief_md(os.path.join(workspace, brief_rel), item, brief, manual_prompt)

        recipient_email = (item.get("recipient_email") or "").strip()
        row = {
            "index": f"{idx:02d}",
            "company": cand.company,
            "domain": cand.domain,
            "candidate_id": item.get("lead_id", ""),
            "decision": cand.decision.upper(),
            "rank": str(cand.rank),
            "expected_image_filename": expected_image,
            "prompt_file": prompt_rel,
            "email_preview_file": email_rel,
            "brief_file": brief_rel,
            "recipient_email": recipient_email,
            "recipient_status": _recipient_status(recipient_email),
            "image_status": "WAITING_FOR_CHARLES",
            "draft_status": "NOT_CREATED",
        }
        rows.append(row)

    manifest_path = os.path.join(workspace, "manifest.csv")
    _write_dict_csv(manifest_path, MANIFEST_COLUMNS, rows)
    readme_path = os.path.join(workspace, "README_FOR_CHARLES.md")
    _write_charles_readme(readme_path, cfg, workspace, rows)

    prompt_report = _write_prompt_pack_report(cfg, rows, skipped, now, workspace)
    print(f"manual prompt pack: {workspace}")
    print(f"manifest: {manifest_path}")
    print(f"README_FOR_CHARLES: {readme_path}")
    print(f"prompt-pack report: {prompt_report}")
    print("No OpenAI API call is used in manual-visuals prompt-pack mode.")
    return 0


def run_chatgpt_bulk_pack(cfg, now: str) -> int:
    """Write a one-paste GPT-5.5 Pro Chat prompt pack for all selected candidates."""
    workspace = manual_workspace(cfg)
    _assert_outside_repo(workspace, cfg.repo_root)
    _assert_outside_repo(cfg.reports_dir, cfg.repo_root)
    paths = _manual_dirs(workspace)
    for d in paths.values():
        os.makedirs(d, exist_ok=True)
    _write_placeholder(os.path.join(paths["images_ready"], "PLACE_COLLECTED_IMAGES_HERE.txt"),
                       workspace, cfg.batch_id)
    _write_placeholder(os.path.join(paths["images_downloaded"], "DOWNLOADS_ARE_COPIED.txt"),
                       workspace, cfg.batch_id)

    try:
        candidates = vco_sample_src.load_candidates(
            cfg.approval_packet_path, cfg.candidate_csv_path)
    except vco_sample_src.SampleParseError as exc:
        print(f"BLOCKED_ON_APPROVAL_PACKET_PARSE: {safety.redact_secrets(str(exc))}")
        return 1

    selected, skipped = _select_manual_candidates(candidates, cfg.limit)
    rows: List[dict] = []
    entries: List[ManualPromptEntry] = []
    for idx, cand, item, brief, _prompt in selected:
        slug = slugify(cand.company)
        stem = f"{idx:02d}_{slug}"
        expected_image = f"{stem}_manual_visual.png"
        prompt_rel = f"prompts/{stem}_prompt.txt"
        email_rel = f"email_previews/{stem}_email.txt"
        brief_rel = f"briefs/{stem}_brief.md"

        manual_prompt = build_manual_chat_prompt(item, brief)
        _write_text(os.path.join(workspace, prompt_rel), manual_prompt)
        _write_email_preview(os.path.join(workspace, email_rel), item)
        _write_brief_md(os.path.join(workspace, brief_rel), item, brief, manual_prompt)

        recipient_email = (item.get("recipient_email") or "").strip()
        row = {
            "index": f"{idx:02d}",
            "company": cand.company,
            "domain": cand.domain,
            "candidate_id": item.get("lead_id", ""),
            "decision": cand.decision.upper(),
            "rank": str(cand.rank),
            "expected_image_filename": expected_image,
            "prompt_file": prompt_rel,
            "email_preview_file": email_rel,
            "brief_file": brief_rel,
            "recipient_email": recipient_email,
            "recipient_status": _recipient_status(recipient_email),
            "image_status": "WAITING_FOR_CHATGPT_DOWNLOAD",
            "draft_status": "NOT_CREATED",
        }
        rows.append(row)
        entries.append(ManualPromptEntry(row=row, item=item, brief=brief))

    manifest_path = os.path.join(workspace, "manifest.csv")
    _write_dict_csv(manifest_path, MANIFEST_COLUMNS, rows)

    master_prompt = build_bulk_chatgpt_prompt(entries, total=len(entries))
    master_md = os.path.join(workspace, "CHATGPT_ONE_PASTE_ALL_IMAGES.md")
    master_txt = os.path.join(workspace, "CHATGPT_ONE_PASTE_ALL_IMAGES.txt")
    _write_text(master_md, master_prompt)
    _write_text(master_txt, master_prompt)

    chunk_paths = []
    for chunk in _chunks(entries, 5):
        if not chunk:
            continue
        first = chunk[0].row.get("index", "01")
        last = chunk[-1].row.get("index", first)
        name = f"CHATGPT_BATCH_{first}_{last}.txt"
        path = os.path.join(workspace, name)
        _write_text(path, build_bulk_chatgpt_prompt(chunk, total=len(entries), chunk=True))
        chunk_paths.append(path)

    copy_helper = os.path.join(workspace, "copy_master_prompt.sh")
    _write_copy_master_helper(copy_helper, master_txt)
    readme_path = os.path.join(workspace, "README_FOR_CHARLES.md")
    _write_bulk_charles_readme(readme_path, cfg, workspace, rows, master_txt, chunk_paths)

    prompt_report = _write_bulk_pack_report(cfg, rows, skipped, now, workspace,
                                            master_txt, chunk_paths)
    print(f"one-paste ChatGPT prompt pack: {workspace}")
    print(f"manifest: {manifest_path}")
    print(f"README_FOR_CHARLES: {readme_path}")
    print(f"master prompt: {master_txt}")
    for path in chunk_paths:
        print(f"chunk prompt: {path}")
    print(f"copy helper: {copy_helper}")
    print(f"prompt-pack report: {prompt_report}")
    print("No OpenAI API call is used in manual-visuals chatgpt-bulk-pack mode.")
    return 0


def _select_manual_candidates(candidates, limit: int):
    selected = []
    skipped = []
    next_idx = 1
    for cand in sorted(candidates, key=lambda c: c.rank):
        if cand.decision.upper() != "APPROVE":
            continue
        item = cand.to_item()
        brief = vco_brief.build_brief(item)
        if brief.fabrication_findings:
            skipped.append((cand, "fabrication in brief: " + "; ".join(brief.fabrication_findings)))
            continue
        api_prompt = vco_brief.build_image_prompt(brief)
        prompt_fab = vco_brief.prompt_is_clean(api_prompt)
        if prompt_fab:
            skipped.append((cand, "fabrication in prompt: " + "; ".join(prompt_fab)))
            continue
        try:
            subject, plain, html = vco_sample_copy.build_sample_bodies(
                item, vco_config.POSTAL_PLACEHOLDER, attached=False)
            vco_copy.assert_attachment_language_consistent(plain, attached=False)
            vco_copy.assert_attachment_language_consistent(html, attached=False)
            body_fab = vco_brief.scan_fabrication(subject, plain)
        except Exception as exc:
            skipped.append((cand, f"email preview failed: {exc}"))
            continue
        if body_fab:
            skipped.append((cand, "fabrication in email preview: " + "; ".join(body_fab)))
            continue
        selected.append((next_idx, cand, item, brief, api_prompt))
        next_idx += 1
        if len(selected) >= max(0, limit):
            break
    return selected, skipped


def build_manual_chat_prompt(item: dict, brief: "vco_brief.VisualBrief") -> str:
    company = brief.company_name
    domain = (item.get("domain") or "").strip()
    verified = brief.one_verified_detail or "No extra detail is verified; keep this generic."
    source_notes = (item.get("source_urls") or item.get("verified_source_notes") or "").strip()
    return "\n".join([
        f"Create one horizontal 3-panel rough concept board for {company}.",
        "",
        "Use GPT-5.5 Pro Chat image generation manually. Create one image only for this candidate.",
        "The output should be a single image, not separate files.",
        "",
        "Company/product context:",
        f"- Company: {company}",
        f"- Domain: {domain or '(not recorded)'}",
        f"- Product/category: {brief.product_or_category}",
        f"- Verified product/company detail: {verified}",
        f"- Source/evidence notes: {source_notes or '(none recorded in the CSV)'}",
        "",
        "MOTIONX context:",
        "- MOTIONX is a motion-first creative studio.",
        "- This is a speculative outreach visual, not final client work.",
        "- Do not imply MOTIONX has already worked with this company.",
        "",
        "Guardrails:",
        "- No fake metrics, testimonials, awards, customers, or press logos.",
        "- No invented product features beyond the verified detail above.",
        "- No claims of prior MOTIONX work.",
        "- Minimal text only; use generic placeholder text if any text is needed.",
        "",
        "Three frames:",
        f"1. Opening product/world frame: {brief.frame1}",
        f"2. Motion or interaction moment: {brief.frame2}",
        f"3. Website, launch-page, or campaign extension: {brief.frame3}",
        "",
        "Visual style:",
        "Premium cinematic lighting, product-led composition, clean modern digital surfaces, "
        "subtle motion-design cues, rough concept-board feel, horizontal storyboard layout.",
        "",
        "Final instruction: create exactly one image for this one candidate.",
        "",
    ])


def build_bulk_chatgpt_prompt(entries: List[ManualPromptEntry], total: int,
                              chunk: bool = False) -> str:
    """Build the master or fallback chunk prompt for GPT-5.5 Pro Chat."""
    if not entries:
        return "\n".join([
            "GPT-5.5 Pro Chat visual batch for MOTIONX.",
            "",
            "No candidates were selected. Do not generate images.",
            "",
        ])
    first = entries[0].row.get("index", "01")
    last = entries[-1].row.get("index", first)
    title = "FALLBACK CHUNK PROMPT" if chunk else "MASTER ONE-PASTE PROMPT"
    lines = [
        f"{title} - MOTIONX GPT-5.5 Pro Chat visual batch",
        "",
        "You are generating rough speculative concept-board images for MOTIONX outreach.",
        "Do not ask clarifying questions.",
        "Generate exactly one image per candidate.",
        "Generate images sequentially in the manifest order provided below.",
        "Do not combine multiple companies into one image.",
        "Do not skip candidates.",
        "Use only verified details provided in this prompt.",
        "No fake metrics, testimonials, awards, customers, press logos, prior-work claims, "
        "or invented product features.",
        "Minimal text only; use generic placeholder text if any text is needed.",
        "Every image is a rough speculative concept board, not final client work.",
        "Style: premium cinematic, motion-first, product-led, clean modern digital surfaces.",
        "Format for every generated asset: one horizontal image with three clearly separated "
        "frames.",
        "",
        "Before each image, print exactly these three lines:",
        f"IMAGE [index]/{total}",
        "EXPECTED_FILENAME: [filename]",
        "COMPANY: [company]",
        "",
        "Then generate one horizontal 3-panel rough concept board image for that candidate.",
        "",
        "If image generation limits are reached, stop cleanly and say exactly:",
        "CONTINUE_FROM: [next index]",
        "",
        f"This prompt covers manifest candidates {first}-{last} of {total}.",
        "",
        "CANDIDATES",
        "",
    ]
    for entry in entries:
        row = entry.row
        brief = entry.brief
        item = entry.item
        idx = row.get("index", "")
        verified = brief.one_verified_detail or "No extra detail is verified; keep this generic."
        guardrails = [
            "Use only the verified detail above.",
            "Do not imply MOTIONX has already worked with this company.",
            "Do not add fake metrics, testimonials, awards, customers, press logos, or claims.",
            "Do not invent product features, materials, customer outcomes, or medical claims.",
            "Keep any text minimal and generic.",
        ]
        lines.extend([
            f"CANDIDATE {idx}/{total}",
            f"index: {idx}",
            f"expected filename: {row.get('expected_image_filename', '')}",
            f"company: {row.get('company', '')}",
            f"domain: {row.get('domain', '') or '(not recorded)'}",
            f"category: {brief.product_or_category}",
            f"verified detail: {verified}",
            f"source/evidence notes: "
            f"{(item.get('source_urls') or item.get('verified_source_notes') or '').strip() or '(none recorded)'}",
            f"Frame 1: {brief.frame1}",
            f"Frame 2: {brief.frame2}",
            f"Frame 3: {brief.frame3}",
            "guardrails:",
        ])
        lines.extend(f"- {g}" for g in guardrails)
        lines.extend([
            "",
            "When you reach this candidate in sequence, print:",
            f"IMAGE {idx}/{total}",
            f"EXPECTED_FILENAME: {row.get('expected_image_filename', '')}",
            f"COMPANY: {row.get('company', '')}",
            "Then generate exactly one image for this candidate.",
            "",
        ])
    lines.extend([
        "Final reminder:",
        "Generate the candidates in the order above. One candidate, one image.",
        "If you cannot continue because of image limits, do not summarize or restart. Say:",
        "CONTINUE_FROM: [next index]",
        "",
    ])
    return "\n".join(lines)


def _chunks(items: List[ManualPromptEntry], size: int) -> List[List[ManualPromptEntry]]:
    return [items[i:i + size] for i in range(0, len(items), max(1, size))]


def _write_email_preview(path: str, item: dict) -> None:
    subject, plaintext, html = vco_sample_copy.build_sample_bodies(
        item, vco_config.POSTAL_PLACEHOLDER, attached=False)
    vco_copy.assert_attachment_language_consistent(plaintext, attached=False)
    vco_copy.assert_attachment_language_consistent(html, attached=False)
    _write_text(path, "SUBJECT: " + subject + "\n\n" + plaintext)


def _write_brief_md(path: str, item: dict, brief, manual_prompt: str) -> None:
    flags = list(brief.uncertainty_flags) + list(item.get("uncertainty_flags", []))
    lines = [
        f"# Manual visual brief - {brief.company_name}",
        "",
        f"- Company: {brief.company_name}",
        f"- Domain: {item.get('domain', '')}",
        f"- Category: {brief.product_or_category}",
        f"- Verified detail: {brief.one_verified_detail or '(none verified)'}",
        f"- Decision source: {item.get('decision_source', '')}",
        "",
        "## Frames",
        f"1. {brief.frame1}",
        f"2. {brief.frame2}",
        f"3. {brief.frame3}",
        "",
        "## Uncertainty Flags",
    ]
    lines.extend([f"- {f}" for f in flags] or ["- (none)"])
    lines.extend(["", "## GPT-5.5 Pro Chat Prompt", "", "```text", manual_prompt, "```", ""])
    _write_text(path, "\n".join(lines))


def _write_charles_readme(path: str, cfg, workspace: str, rows: List[dict]) -> None:
    import_cmd = (
        "python3 outreach/visual_cold_open/run_batch.py \\\n"
        "  --visual-cold-open \\\n"
        "  --manual-visuals import-images \\\n"
        f"  --manual-image-dir {os.path.join(workspace, 'images_ready')} \\\n"
        f"  --manual-manifest {os.path.join(workspace, 'manifest.csv')} \\\n"
        f"  --batch-id {cfg.batch_id}"
    )
    lines = [
        f"# MOTIONX manual visual prompt pack - {cfg.batch_id}",
        "",
        "This workflow avoids OpenAI API image costs because Charles is manually using "
        "ChatGPT image generation in the UI.",
        "",
        "## Steps",
        "",
        "1. Open the prompt files in `prompts/`.",
        "2. Paste each prompt into GPT-5.5 Pro Chat.",
        "3. Generate exactly one image per prompt.",
        "4. Save each image using the exact expected filename from `manifest.csv`.",
        f"5. Put finished images into `{os.path.join(workspace, 'images_ready')}/`.",
        "6. Do not rename company slugs manually except to match the expected filename.",
        "7. After images are saved, run the import command below.",
        "",
        "Do not run all prompts at once if the chat UI struggles. Recommended chunks are "
        "4 batches of 5 or 5 batches of 4.",
        "",
        "## Import Command",
        "",
        "```bash",
        import_cmd,
        "```",
        "",
        "## Expected Files",
        "",
        "| index | company | expected image filename | prompt |",
        "|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['index']} | {row['company']} | `{row['expected_image_filename']}` | "
            f"`{row['prompt_file']}` |")
    lines.append("")
    _write_text(path, "\n".join(lines))


def _write_copy_master_helper(path: str, master_txt: str) -> None:
    script = "\n".join([
        "#!/bin/sh",
        "set -eu",
        f"pbcopy < {shell_quote(master_txt)}",
        'printf "%s\\n" "Now paste into GPT-5.5 Pro Chat."',
        "",
    ])
    _write_text(path, script)
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def _write_bulk_charles_readme(path: str, cfg, workspace: str, rows: List[dict],
                               master_txt: str, chunk_paths: List[str]) -> None:
    collect_cmd = (
        "python3 outreach/visual_cold_open/run_batch.py \\\n"
        "  --visual-cold-open \\\n"
        "  --manual-visuals collect-downloads \\\n"
        f"  --manual-manifest {os.path.join(workspace, 'manifest.csv')} \\\n"
        "  --download-dir ~/Downloads \\\n"
        f"  --manual-image-dir {os.path.join(workspace, 'images_ready')} \\\n"
        f"  --batch-id {cfg.batch_id}"
    )
    import_cmd = (
        "python3 outreach/visual_cold_open/run_batch.py \\\n"
        "  --visual-cold-open \\\n"
        "  --manual-visuals import-images \\\n"
        f"  --manual-image-dir {os.path.join(workspace, 'images_ready')} \\\n"
        f"  --manual-manifest {os.path.join(workspace, 'manifest.csv')} \\\n"
        f"  --batch-id {cfg.batch_id}"
    )
    preview_cmd = import_cmd.replace("--manual-visuals import-images",
                                     "--manual-visuals preview-with-images")
    lines = [
        f"# MOTIONX one-paste ChatGPT visual batch - {cfg.batch_id}",
        "",
        "This workflow avoids OpenAI API billing because Charles generates images in the "
        "ChatGPT UI. It is still not true programmatic ChatGPT automation: Charles must "
        "paste the prompt, wait for generation, and download the files from the UI.",
        "",
        "## Primary one-paste flow",
        "",
        f"1. Run `{os.path.join(workspace, 'copy_master_prompt.sh')}` or open "
        f"`{master_txt}` and copy it.",
        "2. Paste once into GPT-5.5 Pro Chat.",
        "3. Let ChatGPT generate one image per candidate in manifest order.",
        "4. If ChatGPT prints `CONTINUE_FROM: NN`, paste the matching fallback chunk prompt "
        "instead of restarting from the top.",
        "5. Download every generated image from the ChatGPT UI to `~/Downloads`.",
        "6. Run `collect-downloads`; it maps the newest downloads to manifest rows in order, "
        "copies them into `images_ready/`, renames them to the expected filenames, and QA's "
        "the result.",
        "7. Run `preview-with-images` for final local previews. Run live Gmail draft mode "
        "only as a separate explicit step if Gmail OAuth exists.",
        "",
        "Gmail OAuth is only needed for automatic draft attachment. It is not needed for "
        "prompt generation, image collection, import, or local previews.",
        "",
        "## Clipboard Helper",
        "",
        "```bash",
        os.path.join(workspace, "copy_master_prompt.sh"),
        "```",
        "",
        "## Collect Downloads",
        "",
        "```bash",
        collect_cmd,
        "```",
        "",
        "## Import And Preview",
        "",
        "```bash",
        import_cmd,
        "",
        preview_cmd,
        "```",
        "",
        "## Prompt Files",
        "",
        f"- Master: `{master_txt}`",
    ]
    for p in chunk_paths:
        lines.append(f"- Fallback chunk: `{p}`")
    lines.extend([
        "",
        "## Expected Files",
        "",
        "| index | company | expected image filename |",
        "|---:|---|---|",
    ])
    for row in rows:
        lines.append(
            f"| {row['index']} | {row['company']} | `{row['expected_image_filename']}` |")
    lines.extend([
        "",
        "## DRAFT_ONLY Reminder",
        "",
        "No email is sent or scheduled by this workflow. Only Charles sends email by hand.",
        "",
    ])
    _write_text(path, "\n".join(lines))


# ── collect downloads ─────────────────────────────────────────────────────────
def run_collect_downloads(cfg, now: str) -> int:
    rows = _read_manifest_limited(cfg)
    image_dir = _resolve_image_dir(cfg)
    workspace = _workspace_from_manifest(cfg)
    download_dir = os.path.abspath(os.path.expanduser(cfg.download_dir))
    _assert_outside_repo(image_dir, cfg.repo_root)
    _assert_outside_repo(cfg.reports_dir, cfg.repo_root)
    os.makedirs(image_dir, exist_ok=True)

    candidates, unsupported = _recent_download_images(download_dir, cfg.download_since_minutes)
    needed = len(rows)
    if len(candidates) < needed:
        collect_rows = _collect_blocked_rows(
            cfg, rows, "NEEDS_CHARLES_REVIEW",
            f"found {len(candidates)} supported recent image(s), need {needed}",
        )
        if unsupported:
            collect_rows[0]["notes"] = (collect_rows[0]["notes"] + "; unsupported recent "
                                        "file(s): " + ", ".join(unsupported[:8]))
        csv_path, md_path = write_collect_report(cfg, collect_rows, now)
        mapping_csv, mapping_md = _write_workspace_collect_reports(workspace, collect_rows)
        review_index = _write_review_index(workspace, collect_rows)
        _write_needs_charles_review(workspace, collect_rows)
        print("NEEDS_CHARLES_REVIEW: downloaded image count mismatch")
        print(f"collect report: {md_path}")
        print(f"collect csv: {csv_path}")
        print(f"workspace mapping: {mapping_md}")
        print(f"workspace mapping csv: {mapping_csv}")
        print(f"review index: {review_index}")
        print("No Gmail draft was created in collect-downloads mode.")
        return 1

    newest = sorted(candidates, key=lambda c: (c.ts, c.basename), reverse=True)[:needed]
    selected = sorted(newest, key=lambda c: (c.ts, c.basename))
    collect_rows: List[dict] = []
    checks: List[ManualImageCheck] = []
    for row, cand in zip(rows, selected):
        expected = os.path.basename(row.get("expected_image_filename", "").strip())
        dest = _collect_destination(image_dir, expected)
        base = _base_collect_row(cfg, row, cand, dest)
        if not expected:
            base.update(image_status="NEEDS_CHARLES_REVIEW", copy_status="BLOCKED",
                        notes="manifest row has no expected_image_filename")
            collect_rows.append(base)
            continue
        if os.path.exists(dest) and not cfg.allow_overwrite:
            base.update(image_status="NEEDS_CHARLES_REVIEW", copy_status="BLOCKED",
                        notes="destination exists; pass --allow-overwrite to replace it")
            collect_rows.append(base)
            continue
        if cfg.collect_dry_run:
            base.update(image_status="PLANNED", copy_status="DRY_RUN",
                        notes="dry run: file not copied")
            collect_rows.append(base)
            continue
        try:
            shutil.copy2(cand.path, dest)
        except OSError as exc:
            base.update(image_status="NEEDS_CHARLES_REVIEW", copy_status="FAILED_COPY",
                        notes=f"copy failed: {exc}")
            collect_rows.append(base)
            continue
        check = ManualImageCheck(row=row, expected_filename=expected, actual_path=dest)
        _validate_manual_image_file(check)
        check.image_status = "ACCEPTED" if not check.failures else "FAILED_QA"
        checks.append(check)
        base.update(
            copied_image_path=dest,
            image_status=check.image_status,
            copy_status="COPIED",
            width=str(check.width or ""),
            height=str(check.height or ""),
            mime_type=check.mime_type,
            file_size_bytes=str(check.file_size_bytes or ""),
            notes=check.notes,
        )
        collect_rows.append(base)

    ignored = max(0, len(candidates) - needed)
    if ignored and collect_rows:
        note = f"ignored {ignored} older supported recent image(s)"
        collect_rows[-1]["notes"] = (collect_rows[-1].get("notes", "") + "; " + note).strip("; ")
    if unsupported and collect_rows:
        note = "unsupported recent file(s) ignored: " + ", ".join(unsupported[:8])
        collect_rows[-1]["notes"] = (collect_rows[-1].get("notes", "") + "; " + note).strip("; ")

    csv_path, md_path = write_collect_report(cfg, collect_rows, now)
    mapping_csv, mapping_md = _write_workspace_collect_reports(workspace, collect_rows)
    review_index = _write_review_index(workspace, collect_rows)
    if any(r.get("image_status") != "ACCEPTED" for r in collect_rows):
        _write_failed_qa_marker(workspace, collect_rows)
    accepted = sum(1 for r in collect_rows if r.get("image_status") == "ACCEPTED")
    failed = sum(1 for r in collect_rows if r.get("image_status") == "FAILED_QA")
    blocked = sum(1 for r in collect_rows if r.get("image_status") == "NEEDS_CHARLES_REVIEW")
    print(f"collect downloads: accepted={accepted} failed_qa={failed} needs_review={blocked}")
    print(f"collect report: {md_path}")
    print(f"collect csv: {csv_path}")
    print(f"workspace mapping: {mapping_md}")
    print(f"workspace mapping csv: {mapping_csv}")
    print(f"review index: {review_index}")
    print("No Gmail draft was created in collect-downloads mode.")
    return 0 if failed == 0 and blocked == 0 else 1


def _recent_download_images(download_dir: str, since_minutes: int) -> Tuple[List[DownloadCandidate],
                                                                            List[str]]:
    if not os.path.isdir(download_dir):
        return [], [f"download directory not found: {download_dir}"]
    cutoff = datetime.datetime.now().timestamp() - max(0, since_minutes) * 60
    supported: List[DownloadCandidate] = []
    unsupported: List[str] = []
    for name in os.listdir(download_dir):
        path = os.path.join(download_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            ts = _file_event_ts(path)
        except OSError:
            continue
        if ts < cutoff:
            continue
        ext = _ext(path)
        if ext in SUPPORTED_EXTS:
            supported.append(DownloadCandidate(path=path, ts=ts))
        elif ext:
            unsupported.append(name)
    return supported, unsupported


def _file_event_ts(path: str) -> float:
    st = os.stat(path)
    created = getattr(st, "st_birthtime", 0) or 0
    return max(created, st.st_mtime)


def _base_collect_row(cfg, row: dict, cand: DownloadCandidate, dest: str) -> dict:
    return {
        "batch_id": cfg.batch_id,
        "index": row.get("index", ""),
        "company": row.get("company", ""),
        "domain": row.get("domain", ""),
        "candidate_id": row.get("candidate_id", ""),
        "expected_image_filename": row.get("expected_image_filename", ""),
        "download_source_path": cand.path,
        "copied_image_path": dest,
        "source_created_or_modified_at": cand.stamp,
        "image_status": "PLANNED",
        "copy_status": "PLANNED",
        "width": "",
        "height": "",
        "mime_type": "",
        "file_size_bytes": "",
        "notes": "",
    }


def _collect_destination(image_dir: str, expected_filename: str) -> str:
    expected = os.path.basename(expected_filename or "").strip()
    return os.path.join(image_dir, expected)


def _collect_blocked_rows(cfg, rows: List[dict], status: str, notes: str) -> List[dict]:
    out = []
    for row in rows:
        out.append({
            "batch_id": cfg.batch_id,
            "index": row.get("index", ""),
            "company": row.get("company", ""),
            "domain": row.get("domain", ""),
            "candidate_id": row.get("candidate_id", ""),
            "expected_image_filename": row.get("expected_image_filename", ""),
            "download_source_path": "",
            "copied_image_path": "",
            "source_created_or_modified_at": "",
            "image_status": status,
            "copy_status": "BLOCKED",
            "width": "",
            "height": "",
            "mime_type": "",
            "file_size_bytes": "",
            "notes": notes,
        })
    return out


def _write_workspace_collect_reports(workspace: str, rows: List[dict]) -> Tuple[str, str]:
    csv_path = os.path.join(workspace, "DOWNLOAD_COLLECT_MAPPING.csv")
    md_path = os.path.join(workspace, "DOWNLOAD_COLLECT_MAPPING.md")
    _write_dict_csv(csv_path, COLLECT_REPORT_COLUMNS, rows)
    _write_collect_summary(md_path, "manual visual download collection", rows)
    return csv_path, md_path


def _write_needs_charles_review(workspace: str, rows: List[dict]) -> str:
    path = os.path.join(workspace, "NEEDS_CHARLES_REVIEW")
    _write_text(path, "\n".join([
        "Downloaded image count mismatch. No files were copied.",
        "Review DOWNLOAD_COLLECT_MAPPING.md and download the missing ChatGPT images.",
        "",
    ]))
    return path


def _write_failed_qa_marker(workspace: str, rows: List[dict]) -> str:
    failed = [r for r in rows if r.get("image_status") != "ACCEPTED"]
    path = os.path.join(workspace, "FAILED_QA")
    lines = ["One or more collected images failed QA or need review.", ""]
    for row in failed:
        lines.append(f"- {row.get('index', '')} {row.get('company', '')}: "
                     f"{row.get('image_status', '')} - {row.get('notes', '')}")
    lines.append("")
    _write_text(path, "\n".join(lines))
    return path


def _write_review_index(workspace: str, rows: List[dict]) -> str:
    path = os.path.join(workspace, "IMAGE_REVIEW_INDEX.html")
    lines = [
        "<!doctype html>",
        "<meta charset=\"utf-8\">",
        "<title>MOTIONX manual visual image review</title>",
        "<style>",
        "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;margin:24px;"
        "background:#111;color:#eee}",
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #333;"
        "padding:8px;vertical-align:top}img{max-width:220px;max-height:140px;"
        "object-fit:contain;background:#222}.status{font-weight:700}",
        "</style>",
        "<h1>MOTIONX manual visual image review</h1>",
        "<table>",
        "<thead><tr><th>index</th><th>company</th><th>expected filename</th>"
        "<th>actual copied filename</th><th>image path</th><th>status</th>"
        "<th>notes</th><th>thumbnail</th></tr></thead>",
        "<tbody>",
    ]
    for row in rows:
        copied = row.get("copied_image_path", "")
        thumb = ""
        if copied and os.path.exists(copied):
            thumb = f"<img src=\"{_file_uri(copied)}\" alt=\"{_html.escape(row.get('company', 'image'))}\">"
        lines.append(
            "<tr>"
            f"<td>{_html.escape(row.get('index', ''))}</td>"
            f"<td>{_html.escape(row.get('company', ''))}</td>"
            f"<td>{_html.escape(row.get('expected_image_filename', ''))}</td>"
            f"<td>{_html.escape(os.path.basename(copied) if copied else '')}</td>"
            f"<td>{_html.escape(copied)}</td>"
            f"<td class=\"status\">{_html.escape(row.get('image_status', ''))}</td>"
            f"<td>{_html.escape(row.get('notes', ''))}</td>"
            f"<td>{thumb}</td>"
            "</tr>"
        )
    lines.extend(["</tbody>", "</table>", ""])
    _write_text(path, "\n".join(lines))
    return path


def _file_uri(path: str) -> str:
    return "file://" + urllib.parse.quote(os.path.abspath(path))


# ── import / QA ────────────────────────────────────────────────────────────────
def run_import_images(cfg, now: str) -> int:
    rows = _read_manifest_limited(cfg)
    image_dir = _resolve_image_dir(cfg)
    _assert_outside_repo(image_dir, cfg.repo_root)
    _assert_outside_repo(cfg.reports_dir, cfg.repo_root)
    checks = check_manual_images(rows, image_dir)
    csv_path, md_path = write_import_report(cfg, checks, now)
    accepted = sum(1 for c in checks if c.accepted)
    missing = sum(1 for c in checks if c.image_status == "MISSING")
    failed = sum(1 for c in checks if c.image_status == "FAILED_QA")
    print(f"manual image import: accepted={accepted} missing={missing} failed_qa={failed}")
    print(f"import report: {md_path}")
    print(f"import csv: {csv_path}")
    print("No Gmail draft was created in import-images mode.")
    return 0 if failed == 0 and missing == 0 else 1


def check_manual_images(rows: List[dict], image_dir: str) -> List[ManualImageCheck]:
    os.makedirs(os.path.abspath(os.path.expanduser(image_dir)), exist_ok=True)
    image_dir = os.path.abspath(os.path.expanduser(image_dir))
    expected_stems: Dict[str, List[dict]] = {}
    for row in rows:
        stem = _stem(row.get("expected_image_filename", ""))
        expected_stems.setdefault(stem, []).append(row)

    used_actual: Dict[str, List[str]] = {}
    checks: List[ManualImageCheck] = []
    for row in rows:
        expected = row.get("expected_image_filename", "").strip()
        check = ManualImageCheck(row=row, expected_filename=expected)
        stem = _stem(expected)
        if len(expected_stems.get(stem, [])) > 1:
            check.image_status = "FAILED_QA"
            check.failures.append("duplicate expected image filename/stem in manifest")
            checks.append(check)
            continue

        actual, failures = _find_manual_image(image_dir, expected)
        check.failures.extend(failures)
        if not actual:
            check.image_status = "FAILED_QA" if failures else "MISSING"
            checks.append(check)
            continue

        check.actual_path = actual
        used_actual.setdefault(os.path.basename(actual).lower(), []).append(row.get("index", ""))
        if len(used_actual[os.path.basename(actual).lower()]) > 1:
            check.failures.append("one image file maps to more than one manifest row")

        _validate_manual_image_file(check)
        check.image_status = "ACCEPTED" if not check.failures else "FAILED_QA"
        checks.append(check)
    return checks


def _find_manual_image(image_dir: str, expected_filename: str) -> Tuple[str, List[str]]:
    failures: List[str] = []
    expected_filename = os.path.basename(expected_filename or "").strip()
    if not expected_filename:
        return "", ["manifest row has no expected_image_filename"]
    expected_ext = _ext(expected_filename)
    if expected_ext and expected_ext not in SUPPORTED_EXTS:
        failures.append(f"manifest expects unsupported extension .{expected_ext}")
    stem = _stem(expected_filename)

    candidates: List[str] = []
    exact = os.path.join(image_dir, expected_filename)
    if os.path.isfile(exact) and _ext(exact) in SUPPORTED_EXTS:
        candidates.append(exact)
    if not candidates:
        for ext in SUPPORTED_EXTS:
            p = os.path.join(image_dir, f"{stem}.{ext}")
            if os.path.isfile(p):
                candidates.append(p)
    # If Charles saved an unsupported extension for the expected stem, report it as a QA
    # failure instead of a plain missing file.
    unsupported = []
    for name in os.listdir(image_dir):
        if _stem(name) == stem and os.path.isfile(os.path.join(image_dir, name)):
            if _ext(name) not in SUPPORTED_EXTS:
                unsupported.append(name)
    if unsupported:
        failures.append("unsupported image extension for expected stem: " + ", ".join(unsupported))

    unique = sorted(set(candidates))
    if len(unique) > 1:
        return "", failures + ["duplicate filename collision: multiple supported images match"]
    return (unique[0] if unique else ""), failures


def _validate_manual_image_file(check: ManualImageCheck) -> None:
    path = check.actual_path
    ext = _ext(path)
    if ext not in SUPPORTED_EXTS:
        check.failures.append(f"unsupported extension .{ext}")
        return
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError as exc:
        check.failures.append(f"file unreadable: {exc}")
        return
    check.file_size_bytes = len(data)
    if len(data) < MIN_MANUAL_IMAGE_BYTES:
        check.failures.append(f"file is too small to be a plausible render ({len(data)} bytes)")
    if len(data) > MAX_MANUAL_IMAGE_BYTES:
        check.failures.append(f"file is too large for email attachment ({len(data)} bytes)")
    sniffed = vco_qa.sniff_format(data)
    ext_for_magic = "jpg" if ext == "jpeg" else ext
    if sniffed not in ("png", "jpg", "webp"):
        check.failures.append(f"file content is {sniffed or 'unknown'} and is not supported")
        sniffed = ext_for_magic
    elif sniffed != ext_for_magic:
        check.uncertainty_flags.append(
            f"file content is {sniffed} but filename extension is .{ext}; "
            "kept exact expected manifest filename")
    try:
        width, height = _image_dimensions(data, sniffed)
        check.width = width
        check.height = height
    except Exception as exc:
        check.failures.append(str(exc))
    else:
        if width < vco_config.MIN_IMAGE_WIDTH or height < vco_config.MIN_IMAGE_HEIGHT:
            check.failures.append(
                f"dimensions {width}x{height} below minimum "
                f"{vco_config.MIN_IMAGE_WIDTH}x{vco_config.MIN_IMAGE_HEIGHT}")
        if width <= height:
            check.uncertainty_flags.append(
                f"asset is not clearly horizontal ({width}x{height}); expected a wide board")
    check.mime_type = vco_qa.mime_for_format(sniffed)
    check.uncertainty_flags.append(
        "in-image text was not machine-inspected; Charles must confirm there are no fake "
        "metrics, testimonials, awards, customers, press logos, or prior-work claims")


def _image_dimensions(data: bytes, fmt: str) -> Tuple[int, int]:
    if fmt == "png":
        return vco_qa.png_dimensions(data)
    if fmt == "jpg":
        return _jpeg_dimensions(data)
    if fmt == "webp":
        return _webp_dimensions(data)
    raise ValueError(f"unsupported image format: {fmt}")


def _jpeg_dimensions(data: bytes) -> Tuple[int, int]:
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        raise ValueError("not a valid JPEG (SOI marker missing)")
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xD8, 0xD9):
            continue
        if i + 2 > len(data):
            break
        seg_len = struct.unpack(">H", data[i:i + 2])[0]
        if seg_len < 2 or i + seg_len > len(data):
            break
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
            if seg_len < 7:
                break
            height, width = struct.unpack(">HH", data[i + 3:i + 7])
            return width, height
        i += seg_len
    raise ValueError("JPEG dimensions not found")


def _webp_dimensions(data: bytes) -> Tuple[int, int]:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("not a valid WEBP (RIFF/WEBP header missing)")
    chunk = data[12:16]
    if chunk == b"VP8X":
        if len(data) < 30:
            raise ValueError("WEBP VP8X header too short")
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if chunk == b"VP8 ":
        if len(data) < 30 or data[23:26] != b"\x9d\x01\x2a":
            raise ValueError("WEBP VP8 frame header missing")
        width = struct.unpack("<H", data[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", data[28:30])[0] & 0x3FFF
        return width, height
    if chunk == b"VP8L":
        if len(data) < 25 or data[20] != 0x2F:
            raise ValueError("WEBP VP8L header missing")
        b0, b1, b2, b3 = data[21], data[22], data[23], data[24]
        width = 1 + (((b1 & 0x3F) << 8) | b0)
        height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        return width, height
    raise ValueError(f"WEBP chunk {chunk!r} not supported for dimension parsing")


# ── local previews ─────────────────────────────────────────────────────────────
def run_preview_with_images(cfg, now: str) -> int:
    rows = _read_manifest_limited(cfg)
    image_dir = _resolve_image_dir(cfg)
    checks = check_manual_images(rows, image_dir)
    workspace = _workspace_from_manifest(cfg)
    final_dir = os.path.join(workspace, "final_previews")
    _assert_outside_repo(final_dir, cfg.repo_root)
    os.makedirs(final_dir, exist_ok=True)
    preview_rows = _write_final_previews(cfg, rows, checks, final_dir, live=False)
    csv_path, md_path = write_preview_report(cfg, preview_rows, now)
    print(f"final previews: {final_dir}")
    print(f"preview report: {md_path}")
    print(f"preview csv: {csv_path}")
    print("No Gmail draft was created in preview-with-images mode.")
    return 0 if all(r["image_status"] == "ACCEPTED" for r in preview_rows) else 1


def _write_final_previews(cfg, rows: List[dict], checks: List[ManualImageCheck],
                          final_dir: str, live: bool) -> List[dict]:
    by_index = {c.row.get("index", ""): c for c in checks}
    out_rows: List[dict] = []
    for row in rows:
        idx = row.get("index", "")
        company = row.get("company", "unknown")
        slug = slugify(company)
        stem = f"{idx}_{slug}"
        check = by_index.get(idx) or ManualImageCheck(row=row, expected_filename="")
        attached = check.accepted
        subject, plaintext = _final_plaintext_from_preview(cfg, row, attached)
        body_says = "yes" if attached else "no"
        vco_copy.assert_attachment_language_consistent(plaintext, attached=attached)
        final_email = os.path.join(final_dir, f"{stem}_final_email.txt")
        attach_check = os.path.join(final_dir, f"{stem}_attachment_check.txt")
        raw_path = ""
        _write_text(final_email, "SUBJECT: " + subject + "\n\n" + plaintext)
        if attached:
            raw_path = os.path.join(final_dir, f"{stem}_draft.raw.b64url")
            attachment = _attachment_tuple(check)
            raw = mime_builder.build_raw(
                from_addr=cfg.expected_account,
                to_addr=row.get("recipient_email") or "REDACTED@dry-run.local",
                subject=subject,
                plaintext=plaintext,
                html=_html_from_plaintext(plaintext),
                attachment=attachment,
            )
            _write_text(raw_path, raw)
        _write_text(attach_check, _attachment_check_text(row, check, attached, live))
        out_rows.append({
            "batch_id": cfg.batch_id,
            "index": idx,
            "company": company,
            "domain": row.get("domain", ""),
            "candidate_id": row.get("candidate_id", ""),
            "expected_image_filename": row.get("expected_image_filename", ""),
            "actual_image_filename": check.actual_filename,
            "image_status": check.image_status,
            "draft_status": "LOCAL_PREVIEW_READY" if attached else "BLOCKED",
            "recipient_status": row.get("recipient_status", ""),
            "body_says_attached": body_says,
            "final_email_file": final_email,
            "attachment_check_file": attach_check,
            "raw_mime_file": raw_path,
            "notes": check.notes,
        })
    return out_rows


def _final_plaintext_from_preview(cfg, row: dict, attached: bool) -> Tuple[str, str]:
    preview_path = _resolve_manifest_relative(cfg, row.get("email_preview_file", ""))
    if not os.path.exists(preview_path):
        subject = f"Rough visual thought for {row.get('company', 'your team')}"
        body = vco_config.POSTAL_PLACEHOLDER
    else:
        text = _read_text(preview_path)
        subject, body = _split_subject_body(text, row.get("company", "your team"))
    if attached:
        body = _insert_attachment_sentence(body)
    else:
        vco_copy.assert_attachment_language_consistent(body, attached=False)
    return subject, body


def _split_subject_body(text: str, company: str) -> Tuple[str, str]:
    if text.startswith("SUBJECT: "):
        head, sep, rest = text.partition("\n\n")
        return head.replace("SUBJECT: ", "", 1).strip(), rest if sep else ""
    return f"Rough visual thought for {company}", text


def _insert_attachment_sentence(body: str) -> str:
    if vco_copy.body_mentions_attachment(body):
        return body
    marker = "\n\n--\n"
    idx = body.find(marker)
    if idx == -1:
        return body.rstrip() + "\n\n" + vco_copy.ATTACHMENT_SENTENCE + "\n"
    return body[:idx] + "\n\n" + vco_copy.ATTACHMENT_SENTENCE + body[idx:]


def _attachment_tuple(check: ManualImageCheck) -> Tuple[str, bytes, str]:
    with open(check.actual_path, "rb") as fh:
        data = fh.read()
    filename = os.path.basename(check.actual_path) or check.expected_filename
    ext = _ext(check.actual_path)
    fmt = vco_qa.sniff_format(data) or ("jpg" if ext == "jpeg" else ext)
    return filename, data, vco_qa.mime_for_format(fmt)


def _html_from_plaintext(plaintext: str) -> str:
    return '<div dir="auto">' + _html.escape(plaintext).replace("\n", "<br>") + "</div>"


def _attachment_check_text(row: dict, check: ManualImageCheck, attached: bool,
                           live: bool) -> str:
    lines = [
        f"Company: {row.get('company', '')}",
        f"Expected image: {row.get('expected_image_filename', '')}",
        f"Actual image: {check.actual_path or '(none)'}",
        f"Image status: {check.image_status}",
        f"Attachment language included: {'yes' if attached else 'no'}",
        f"Mode: {'live draft gate' if live else 'local preview only'}",
        "Sent or scheduled: no",
    ]
    if check.failures:
        lines.append("Failures:")
        lines.extend(f"- {f}" for f in check.failures)
    if check.uncertainty_flags:
        lines.append("Uncertainty flags:")
        lines.extend(f"- {f}" for f in check.uncertainty_flags)
    return "\n".join(lines) + "\n"


# ── live Gmail drafts ──────────────────────────────────────────────────────────
def run_live_drafts_with_manual_images(cfg, gmail_backend, now: str) -> int:
    if not cfg.is_live:
        print("ERROR: live-drafts-with-manual-images requires --live-drafts.",)
        return 2
    rows = _read_manifest_limited(cfg)
    image_dir = _resolve_image_dir(cfg)
    checks = check_manual_images(rows, image_dir)
    workspace = _workspace_from_manifest(cfg)
    final_dir = os.path.join(workspace, "final_previews")
    os.makedirs(final_dir, exist_ok=True)
    _write_final_previews(cfg, rows, checks, final_dir, live=True)

    blockers: List[str] = []
    token = os.path.abspath(os.path.expanduser(cfg.gmail_token_path or ""))
    if not cfg.gmail_token_path or not os.path.exists(token):
        blockers.append("BLOCKED_ON_GMAIL_DRAFT_ACCESS: Gmail OAuth token not found")
    if not vco_config.postal_resolved(cfg.postal_address):
        blockers.append("BLOCKED_ON_GMAIL_DRAFT_ACCESS: postal address unresolved")

    account_verified = False
    if not blockers:
        try:
            acct = gmail_backend.verify_account()
            safety.assert_expected_account(acct, cfg.expected_account)
            account_verified = True
        except (GmailApiUnavailable, safety.WrongAccountError,
                safety.SendForbiddenError) as exc:
            blockers.append("BLOCKED_ON_GMAIL_DRAFT_ACCESS: "
                            + safety.redact_secrets(str(exc)))

    live_rows: List[dict] = []
    check_by_index = {c.row.get("index", ""): c for c in checks}
    if blockers:
        for row in rows:
            check = check_by_index.get(row.get("index", ""))
            live_rows.append(_blocked_live_row(cfg, row, check, "; ".join(blockers)))
        csv_path, md_path = write_live_report(cfg, live_rows, now)
        print("BLOCKED_ON_GMAIL_DRAFT_ACCESS")
        print(f"final previews: {final_dir}")
        print(f"live report: {md_path}")
        print(f"live csv: {csv_path}")
        print("No real Gmail draft was created.")
        return 1

    for row in rows:
        check = check_by_index.get(row.get("index", ""))
        if not check or not check.accepted:
            live_rows.append(_blocked_live_row(cfg, row, check, "manual image missing or failed QA"))
            continue
        recipient = (row.get("recipient_email") or "").strip()
        if row.get("recipient_status") != "VERIFIED" or not _looks_like_email(recipient):
            live_rows.append(_blocked_live_row(
                cfg, row, check, vco_config.STATUS["BLOCKED_ON_RECIPIENT_UNVERIFIED"]))
            continue

        duplicate_note = _duplicate_draft_note(gmail_backend, row)
        if duplicate_note:
            live_rows.append(_blocked_live_row(cfg, row, check, duplicate_note))
            continue

        subject, plaintext = _final_plaintext_from_preview(cfg, row, attached=True)
        vco_copy.assert_attachment_language_consistent(plaintext, attached=True)
        raw = mime_builder.build_raw(
            from_addr=cfg.expected_account,
            to_addr=recipient,
            subject=subject,
            plaintext=plaintext,
            html=_html_from_plaintext(plaintext),
            attachment=_attachment_tuple(check),
        )
        try:
            resp = gmail_backend.create_draft(raw)
        except safety.SendForbiddenError as exc:
            live_rows.append(_blocked_live_row(cfg, row, check, f"send guard tripped: {exc}"))
            continue
        draft_id = (resp or {}).get("id", "")
        verdict = gmail_backend.verify_draft_only(draft_id)
        observed_sent = bool(verdict.get("is_sent"))
        draft_only = bool(verdict.get("draft_only"))
        live_rows.append({
            "batch_id": cfg.batch_id,
            "index": row.get("index", ""),
            "company": row.get("company", ""),
            "domain": row.get("domain", ""),
            "candidate_id": row.get("candidate_id", ""),
            "safe_recipient_identifier": safety.mask_recipient(recipient),
            "expected_image_filename": row.get("expected_image_filename", ""),
            "actual_image_filename": check.actual_filename,
            "image_status": "ACCEPTED",
            "draft_status": "GMAIL_DRAFT_CREATED" if draft_only else "BLOCKED",
            "draft_id": safety.mask_draft_id(draft_id),
            "gmail_draft_confirmed": "yes" if draft_only else "no",
            "body_says_attached": "yes",
            "sent_or_scheduled": "yes" if observed_sent else "no",
            "notes": ("draft-only verified" if draft_only
                      else f"draft-only NOT confirmed labels={verdict.get('label_ids')}"),
        })

    csv_path, md_path = write_live_report(cfg, live_rows, now)
    print(f"final previews: {final_dir}")
    print(f"live report: {md_path}")
    print(f"live csv: {csv_path}")
    if any(r.get("sent_or_scheduled") == "yes" for r in live_rows):
        raise RuntimeError("INVARIANT VIOLATION: Gmail read-back showed SENT label")
    created = sum(1 for r in live_rows if r.get("draft_status") == "GMAIL_DRAFT_CREATED")
    print(f"Gmail drafts created: {created} (DRAFT_ONLY)")
    print("No email was sent or scheduled.")
    return 0 if created else 1


def _blocked_live_row(cfg, row: dict, check: Optional[ManualImageCheck], notes: str) -> dict:
    return {
        "batch_id": cfg.batch_id,
        "index": row.get("index", ""),
        "company": row.get("company", ""),
        "domain": row.get("domain", ""),
        "candidate_id": row.get("candidate_id", ""),
        "safe_recipient_identifier": safety.mask_recipient(row.get("recipient_email", "")),
        "expected_image_filename": row.get("expected_image_filename", ""),
        "actual_image_filename": check.actual_filename if check else "",
        "image_status": check.image_status if check else "MISSING",
        "draft_status": "BLOCKED",
        "draft_id": "",
        "gmail_draft_confirmed": "no",
        "body_says_attached": "yes" if check and check.accepted else "no",
        "sent_or_scheduled": "no",
        "notes": notes,
    }


def _duplicate_draft_note(gmail_backend, row: dict) -> str:
    probe = getattr(gmail_backend, "active_draft_exists", None)
    if not callable(probe):
        return ""
    try:
        if probe(row):
            return "duplicate active draft already exists"
    except Exception as exc:
        return f"duplicate draft check failed closed: {exc}"
    return ""


# ── reports ───────────────────────────────────────────────────────────────────
def write_import_report(cfg, checks: List[ManualImageCheck], now: str) -> Tuple[str, str]:
    rows = []
    for c in checks:
        rows.append({
            "batch_id": cfg.batch_id,
            "index": c.row.get("index", ""),
            "company": c.row.get("company", ""),
            "domain": c.row.get("domain", ""),
            "candidate_id": c.row.get("candidate_id", ""),
            "expected_image_filename": c.expected_filename,
            "actual_image_filename": c.actual_filename,
            "image_status": c.image_status,
            "draft_status": c.row.get("draft_status", "NOT_CREATED"),
            "recipient_status": c.row.get("recipient_status", ""),
            "width": str(c.width or ""),
            "height": str(c.height or ""),
            "mime_type": c.mime_type,
            "file_size_bytes": str(c.file_size_bytes or ""),
            "notes": c.notes,
        })
    stamp = _stamp_from_now(now)
    csv_path = os.path.join(cfg.reports_dir, f"manual_visual_import_{cfg.batch_id}_{stamp}.csv")
    md_path = os.path.join(cfg.reports_dir, f"manual_visual_import_{cfg.batch_id}_{stamp}.md")
    _write_dict_csv(csv_path, IMPORT_REPORT_COLUMNS, rows)
    _write_summary(md_path, "manual visual import", cfg.batch_id, rows, "image_status")
    return csv_path, md_path


def write_collect_report(cfg, rows: List[dict], now: str) -> Tuple[str, str]:
    stamp = _stamp_from_now(now)
    csv_path = os.path.join(cfg.reports_dir, f"manual_visual_collect_downloads_"
                            f"{cfg.batch_id}_{stamp}.csv")
    md_path = os.path.join(cfg.reports_dir, f"manual_visual_collect_downloads_"
                           f"{cfg.batch_id}_{stamp}.md")
    _write_dict_csv(csv_path, COLLECT_REPORT_COLUMNS, rows)
    _write_collect_summary(md_path, "manual visual download collection", rows)
    return csv_path, md_path


def write_preview_report(cfg, rows: List[dict], now: str) -> Tuple[str, str]:
    stamp = _stamp_from_now(now)
    csv_path = os.path.join(cfg.reports_dir, f"manual_visual_preview_{cfg.batch_id}_{stamp}.csv")
    md_path = os.path.join(cfg.reports_dir, f"manual_visual_preview_{cfg.batch_id}_{stamp}.md")
    _write_dict_csv(csv_path, PREVIEW_REPORT_COLUMNS, rows)
    _write_summary(md_path, "manual visual final previews", cfg.batch_id, rows, "draft_status")
    return csv_path, md_path


def write_live_report(cfg, rows: List[dict], now: str) -> Tuple[str, str]:
    stamp = _stamp_from_now(now)
    csv_path = os.path.join(cfg.reports_dir, f"manual_visual_live_drafts_{cfg.batch_id}_{stamp}.csv")
    md_path = os.path.join(cfg.reports_dir, f"manual_visual_live_drafts_{cfg.batch_id}_{stamp}.md")
    _write_dict_csv(csv_path, LIVE_REPORT_COLUMNS, rows)
    _write_summary(md_path, "manual visual live drafts", cfg.batch_id, rows, "draft_status")
    return csv_path, md_path


def _write_prompt_pack_report(cfg, rows: List[dict], skipped: List[tuple], now: str,
                              workspace: str) -> str:
    os.makedirs(cfg.reports_dir, exist_ok=True)
    stamp = _stamp_from_now(now)
    path = os.path.join(cfg.reports_dir, f"manual_visual_prompt_pack_{cfg.batch_id}_{stamp}.md")
    lines = [
        f"# MOTIONX manual visual prompt pack - {cfg.batch_id}",
        "",
        f"- Workspace: {workspace}",
        f"- Candidates in manifest: {len(rows)}",
        f"- Skipped unsafe/ineligible candidates: {len(skipped)}",
        "- OpenAI API calls: no",
        "- Gmail writes: no",
        "- Sent or scheduled: no",
        "",
        "## Manifest Rows",
        "",
        "| index | company | domain | expected image | recipient status |",
        "|---:|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r['index']} | {r['company']} | {r['domain']} | "
                     f"{r['expected_image_filename']} | {r['recipient_status']} |")
    if skipped:
        lines.extend(["", "## Skipped"])
        for cand, why in skipped:
            lines.append(f"- {cand.company}: {safety.redact_secrets(why)}")
    _write_text(path, "\n".join(lines) + "\n")
    return path


def _write_bulk_pack_report(cfg, rows: List[dict], skipped: List[tuple], now: str,
                            workspace: str, master_txt: str,
                            chunk_paths: List[str]) -> str:
    os.makedirs(cfg.reports_dir, exist_ok=True)
    stamp = _stamp_from_now(now)
    path = os.path.join(cfg.reports_dir, f"manual_visual_chatgpt_bulk_pack_"
                        f"{cfg.batch_id}_{stamp}.md")
    lines = [
        f"# MOTIONX one-paste ChatGPT visual pack - {cfg.batch_id}",
        "",
        f"- Workspace: {workspace}",
        f"- Candidates in manifest: {len(rows)}",
        f"- Skipped unsafe/ineligible candidates: {len(skipped)}",
        f"- Master prompt: {master_txt}",
        f"- Fallback chunk prompts: {len(chunk_paths)}",
        "- OpenAI API calls: no",
        "- OPENAI_API_KEY required: no",
        "- Gmail writes: no",
        "- Sent or scheduled: no",
        "",
        "## Chunk Prompts",
    ]
    lines.extend([f"- `{p}`" for p in chunk_paths] or ["- (none)"])
    lines.extend([
        "",
        "## Manifest Rows",
        "",
        "| index | company | domain | expected image | recipient status |",
        "|---:|---|---|---|---|",
    ])
    for r in rows:
        lines.append(f"| {r['index']} | {r['company']} | {r['domain']} | "
                     f"{r['expected_image_filename']} | {r['recipient_status']} |")
    if skipped:
        lines.extend(["", "## Skipped"])
        for cand, why in skipped:
            lines.append(f"- {cand.company}: {safety.redact_secrets(why)}")
    _write_text(path, "\n".join(lines) + "\n")
    return path


def _write_summary(path: str, title: str, batch_id: str, rows: List[dict],
                   count_key: str) -> None:
    counts: Dict[str, int] = {}
    for row in rows:
        counts[row.get(count_key, "unknown")] = counts.get(row.get(count_key, "unknown"), 0) + 1
    lines = [
        f"# MOTIONX {title} - {batch_id}",
        "",
        f"- Rows: {len(rows)}",
        "- OpenAI API calls: no",
        "- Sent or scheduled: no",
        "",
        "## Status Breakdown",
    ]
    for k in sorted(counts):
        lines.append(f"- `{k}`: {counts[k]}")
    lines.extend(["", "## Rows", "", "| index | company | status | notes |", "|---:|---|---|---|"])
    for row in rows:
        notes = safety.redact_secrets(str(row.get("notes", "")))[:160]
        lines.append(f"| {row.get('index', '')} | {row.get('company', '')} | "
                     f"{row.get(count_key, '')} | {notes} |")
    lines.append("")
    _write_text(path, "\n".join(lines))


def _write_collect_summary(path: str, title: str, rows: List[dict]) -> None:
    counts: Dict[str, int] = {}
    for row in rows:
        status = row.get("image_status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    lines = [
        f"# MOTIONX {title}",
        "",
        f"- Rows: {len(rows)}",
        "- OpenAI API calls: no",
        "- Gmail writes: no",
        "- Sent or scheduled: no",
        "- Original downloads moved/deleted: no",
        "",
        "## Status Breakdown",
    ]
    for k in sorted(counts):
        lines.append(f"- `{k}`: {counts[k]}")
    lines.extend([
        "",
        "## Mapping",
        "",
        "| index | company | expected filename | source download | copied path | status | notes |",
        "|---:|---|---|---|---|---|---|",
    ])
    for row in rows:
        lines.append(
            f"| {row.get('index', '')} | {row.get('company', '')} | "
            f"{row.get('expected_image_filename', '')} | "
            f"{row.get('download_source_path', '')} | {row.get('copied_image_path', '')} | "
            f"{row.get('image_status', '')} | "
            f"{safety.redact_secrets(str(row.get('notes', '')))[:160]} |")
    lines.append("")
    _write_text(path, "\n".join(lines))


# ── path / CSV helpers ────────────────────────────────────────────────────────
def manual_workspace(cfg) -> str:
    root = cfg.manual_root_dir or vco_config.DEFAULT_MANUAL_VISUALS_DIR
    return os.path.abspath(os.path.expanduser(os.path.join(root, cfg.batch_id or "manual-visuals")))


def _manual_dirs(workspace: str) -> Dict[str, str]:
    return {
        "workspace": workspace,
        "prompts": os.path.join(workspace, "prompts"),
        "email_previews": os.path.join(workspace, "email_previews"),
        "briefs": os.path.join(workspace, "briefs"),
        "images_downloaded": os.path.join(workspace, "images_downloaded"),
        "images_ready": os.path.join(workspace, "images_ready"),
        "final_previews": os.path.join(workspace, "final_previews"),
    }


def _resolve_manifest_path(cfg) -> str:
    if cfg.manual_manifest_path:
        return os.path.abspath(os.path.expanduser(cfg.manual_manifest_path))
    return os.path.join(manual_workspace(cfg), "manifest.csv")


def _workspace_from_manifest(cfg) -> str:
    return os.path.dirname(_resolve_manifest_path(cfg))


def _resolve_image_dir(cfg) -> str:
    if cfg.manual_image_dir:
        return os.path.abspath(os.path.expanduser(cfg.manual_image_dir))
    return os.path.join(_workspace_from_manifest(cfg), "images_ready")


def _resolve_manifest_relative(cfg, rel_path: str) -> str:
    if not rel_path:
        return ""
    if os.path.isabs(rel_path):
        return os.path.abspath(os.path.expanduser(rel_path))
    return os.path.join(_workspace_from_manifest(cfg), rel_path)


def _read_manifest_limited(cfg) -> List[dict]:
    path = _resolve_manifest_path(cfg)
    if not os.path.exists(path):
        raise FileNotFoundError(f"manual manifest not found: {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    missing = [c for c in MANIFEST_COLUMNS if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError("manual manifest missing required columns: " + ", ".join(missing))
    return rows[: max(0, cfg.limit)]


def _write_dict_csv(path: str, columns: List[str], rows: List[dict]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            clean = {k: safety.redact_secrets("" if v is None else str(v))
                     for k, v in row.items()}
            if "sent_or_scheduled" in columns:
                clean["sent_or_scheduled"] = clean.get("sent_or_scheduled", "no") or "no"
            writer.writerow(clean)


def _write_text(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(safety.redact_secrets(text))


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _write_placeholder(path: str, workspace: str, batch_id: str) -> None:
    _write_text(path, "\n".join([
        "Place Charles-generated images for this batch in this directory.",
        f"Batch: {batch_id}",
        f"Workspace: {workspace}",
        "Use the exact filenames listed in manifest.csv.",
        "",
    ]))


def _assert_outside_repo(path: str, repo_root: str) -> None:
    if not repo_root:
        return
    ap = os.path.abspath(os.path.expanduser(path))
    rp = os.path.abspath(os.path.expanduser(repo_root))
    if ap == rp or ap.startswith(rp + os.sep):
        raise ValueError(f"manual-visuals output must be outside the repo: {ap}")


def _stamp_from_now(now: str) -> str:
    try:
        dt = datetime.datetime.fromisoformat(now)
        return dt.strftime("%Y-%m-%d_%H%M")
    except ValueError:
        core = (now or "")[:16]
        return core.replace("T", "_").replace(":", "")


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_") or "candidate"


def _recipient_status(email: str) -> str:
    return "VERIFIED" if _looks_like_email(email) else "UNVERIFIED"


def _looks_like_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", (email or "").strip()))


def _ext(path: str) -> str:
    return os.path.splitext(path or "")[1].lower().lstrip(".")


def _stem(path: str) -> str:
    return os.path.splitext(os.path.basename(path or "").lower())[0]


def shell_quote(value: str) -> str:
    return "'" + (value or "").replace("'", "'\"'\"'") + "'"
