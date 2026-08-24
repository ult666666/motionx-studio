# -*- coding: utf-8 -*-
"""Codex-ready handoff generation.

Every handoff uses the EXACT 8-field format (labels + order fixed):

    Objective:
    Verified current state:
    Source of truth:
    Already done:
    Codex should execute:
    Codex must NOT:
    Verification required:
    Risks / unknowns:

Handoffs are self-contained and reflect the live snapshot at generation time. The
"Codex should execute" block is always draft-only / read-only; it never instructs a
send (the safety scanner enforces this before a handoff is written).

Pure stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

import paths
import scanner
import collectors
from engine import Snapshot

# Field labels, in the exact required order.
FIELDS: List[str] = [
    "Objective",
    "Verified current state",
    "Source of truth",
    "Already done",
    "Codex should execute",
    "Codex must NOT",
    "Verification required",
    "Risks / unknowns",
]

TASKS: List[str] = [
    "live-setup",
    "three-sample-live-drafts",
    "credentials-setup",
    "batch32-normalized-draft-dry-run",
    "batch32-visual-dry-run",
    "batch32-full-live-drafts-after-review",
    "crm-gmail-reconcile",
    "source-next-20",
    "batch32-draft-dry-run",
    "one-paste-chatgpt-visual-pack",
    "collect-chatgpt-downloads",
    "manual-visual-preview-with-collected-images",
    "manual-visual-prompt-pack",
    "manual-visual-import",
    "manual-visual-live-drafts",
]


@dataclass
class Handoff:
    task: str
    objective: str
    verified_current_state: str
    source_of_truth: str
    already_done: str
    codex_should_execute: str
    codex_must_not: str
    verification_required: str
    risks_unknowns: str

    def as_ordered(self) -> List[tuple]:
        return [
            ("Objective", self.objective),
            ("Verified current state", self.verified_current_state),
            ("Source of truth", self.source_of_truth),
            ("Already done", self.already_done),
            ("Codex should execute", self.codex_should_execute),
            ("Codex must NOT", self.codex_must_not),
            ("Verification required", self.verification_required),
            ("Risks / unknowns", self.risks_unknowns),
        ]

    def render(self) -> str:
        out = []
        for label, value in self.as_ordered():
            value = (value or "").rstrip("\n")
            if "\n" in value:
                out.append(f"{label}:")
                out.append(value)
            else:
                out.append(f"{label}: {value}")
            out.append("")   # blank line between fields
        return "\n".join(out).rstrip() + "\n"


def _bullets(items: List[str]) -> str:
    return "\n".join(f"  - {it}" for it in items)


def _numbered(items: List[str]) -> str:
    return "\n".join(f"  {i}. {it}" for i, it in enumerate(items, 1))


# Prohibitions common to every DRAFT_ONLY handoff.
_COMMON_MUST_NOT = [
    "Send or schedule any email (no messages.send, drafts.send, messages.insert, or any *.send).",
    "Archive, delete, trash, or relabel any Gmail message/thread/draft.",
    "Mutate CRM/state files (leads.csv, state.json, candidate-queue.csv, suppression.csv, outcome-log.csv).",
    "Touch outreach/self-improvement.md (pre-existing, unrelated dirty file — leave it).",
    "Print, echo, write, or commit OPENAI_API_KEY, Gmail OAuth tokens, client_secret, "
    "refresh_token, or the postal address.",
    "git push, git reset --hard, git clean -fd, or weaken any DRAFT_ONLY guard.",
]


def _repo_line(snap: Snapshot) -> str:
    return (f"repo `{snap.repo.root}` on `{snap.repo.branch}` at HEAD `{snap.repo.head}` "
            f"(at/after baseline {paths.BASELINE_COMMIT}: "
            f"{'yes' if snap.repo.at_or_after_baseline else 'NO'}); checked {snap.ts}")


def _blocker_line(snap: Snapshot) -> str:
    b = snap.gate.blockers
    return (", ".join(b) if b else "none — all readiness gates pass")


def _recipient_lines(snap: Snapshot) -> List[str]:
    lines = []
    for r in snap.verified_recipients:
        flag = " [CUSTOMER-EXPERIENCE MAILBOX — technical sample only]" if r.get(
            "customer_experience_oriented") else ""
        appr = (
            "approval recorded"
            if collectors.recipient_charles_approved(r, snap.approvals_note)
            else "PENDING Charles approval"
        )
        lines.append(f"{r['company']} ({r['domain']}) → {scanner.mask_recipient(r['email'])} "
                     f"[{appr}]{flag}")
    return lines or ["(no verified recipients parsed)"]


# ── Individual handoff builders ─────────────────────────────────────────────────
def _live_setup(snap: Snapshot) -> Handoff:
    return Handoff(
        task="live-setup",
        objective=(
            "Provision the two missing live credentials so the visual-cold-open "
            "3-sample DRAFT path becomes READY — WITHOUT creating any draft or sending "
            "anything. Success = `vco-readiness` prints "
            f"{snap.gate.verdict if snap.gate.ready else 'READY_FOR_3_SAMPLE_LIVE_DRAFTS'}."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. "
            f"Out-of-repo venv present: {'yes' if snap.venv.exists else 'NO'}. "
            f"OPENAI_API_KEY present: {'yes' if snap.openai_present else 'NO'}. "
            f"gmail_token.json present: {'yes' if snap.gmail_token_present else 'NO'}. "
            f"Blockers now: {_blocker_line(snap)}."
        ),
        source_of_truth=(
            "Local CLI environment (OPENAI_API_KEY) + the file "
            f"{paths.GMAIL_TOKEN_PATH} (Gmail OAuth token). Readiness truth: "
            "`python3 outreach/agentic_ops/run.py vco-readiness`."
        ),
        already_done=(
            "Readiness venv exists with openai + google-api-python-client + google-auth + "
            "google-auth-oauthlib installed (out-of-repo). Top-3 recipients verified from "
            "official company sources. Sample dry-run path validated. Nothing live remains "
            "except these two credentials. The credentials-setup assistant can prepare/check "
            "them without creating drafts or generating images."
        ),
        codex_should_execute=_numbered([
            "Run `python3 outreach/agentic_ops/run.py live-setup-checklist` and read the "
            "generated checklist path.",
            "If OPENAI_API_KEY is missing, have Charles run "
            "`python3 outreach/agentic_ops/run.py credentials-setup --interactive "
            "--write-openai-key` locally; the prompt is hidden and the value is written "
            "only to ~/.motionx-outreach/secrets.env.",
            "If Gmail OAuth is missing, have Charles place the Google OAuth Desktop App "
            "credentials JSON at ~/.motionx-outreach/gmail_credentials.json, then run "
            "`python3 outreach/agentic_ops/run.py credentials-setup --setup-gmail-oauth`.",
            "Re-run `python3 outreach/agentic_ops/run.py vco-readiness` and confirm the "
            "verdict flips to READY_FOR_3_SAMPLE_LIVE_DRAFTS with zero blockers.",
        ]),
        codex_must_not=_bullets([
            "Create, update, or send any Gmail draft in this setup task (setup only).",
            "Generate any image / call gpt-image-2.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "`python3 outreach/agentic_ops/run.py vco-readiness` prints "
            "READY_FOR_3_SAMPLE_LIVE_DRAFTS and lists no BLOCKED_ON_* tokens; "
            "the generated vco_readiness_*.md report shows OPENAI + Gmail-token gates PASS."
        ),
        risks_unknowns=(
            "Gmail token must be for charles@madebymotionx.com with the compose scope, or "
            "draft creation will fail account verification. OpenAI key must have gpt-image-2 "
            "access. Neither secret may be logged or committed."
        ),
    )


def _credentials_setup(snap: Snapshot) -> Handoff:
    return Handoff(
        task="credentials-setup",
        objective=(
            "Use the safe credentials setup assistant to prepare/check local OpenAI and "
            "Gmail OAuth prerequisites for later DRAFT_ONLY visual drafting, then prove "
            "readiness with no Gmail drafts and no image generation."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. OPENAI_API_KEY present: "
            f"{'yes' if snap.openai_present else 'NO'}. Gmail OAuth token present: "
            f"{'yes' if snap.gmail_token_present else 'NO'}. Blockers: {_blocker_line(snap)}."
        ),
        source_of_truth=(
            f"OpenAI key storage: {paths.SECRETS_ENV_PATH} or the current CLI environment. "
            f"Gmail Desktop credentials JSON: {paths.GMAIL_CREDENTIALS_PATH}. Gmail token: "
            f"{paths.GMAIL_TOKEN_PATH}. Readiness truth is "
            "`python3 outreach/agentic_ops/run.py vco-readiness`."
        ),
        already_done=(
            "Agentic-ops and visual-cold-open are merged. batch32 top-3 recipient review "
            "exists, and Charles approval can be recorded separately under "
            "~/.motionx-outreach/approvals/."
        ),
        codex_should_execute=_numbered([
            "Run `python3 outreach/agentic_ops/run.py credentials-setup --verify-only` to "
            "check current credential presence without prompting or writing.",
            "If the OpenAI key is missing, have Charles run "
            "`python3 outreach/agentic_ops/run.py credentials-setup --interactive "
            "--write-openai-key`; do not ask him to paste the key into chat.",
            "If the Gmail credentials JSON is missing, have Charles download a Google OAuth "
            "Desktop App credentials JSON with Gmail API enabled and place it at "
            "~/.motionx-outreach/gmail_credentials.json.",
            "If the Gmail token is missing and the credentials JSON exists, run "
            "`python3 outreach/agentic_ops/run.py credentials-setup --setup-gmail-oauth`.",
            "Run `python3 outreach/agentic_ops/run.py live-setup-checklist`, then "
            "`python3 outreach/agentic_ops/run.py vco-readiness`.",
        ]),
        codex_must_not=_bullets([
            "Create or update Gmail drafts in this credential setup task.",
            "Generate images.",
            "Run `--verify-live-openai` unless Charles explicitly asks for a live OpenAI "
            "models.retrieve preflight.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "`credentials_setup_*.md` and `live_setup_checklist_*.md` are written outside "
            "the repo, contain no secret values, and show credential presence/status only. "
            "`vco-readiness` shows PASS or lists the exact remaining blockers; no live "
            "draft/image operation occurred."
        ),
        risks_unknowns=(
            "OAuth scope and OpenAI model access may still be insufficient even when files "
            "are present; the readiness gate only proves local presence until live drafting "
            "is explicitly authorized."
        ),
    )


def _three_sample_live_drafts(snap: Snapshot) -> Handoff:
    csv_path = snap.batch32_inputs.get("recipient_review") or "(recipient review CSV not found)"
    return Handoff(
        task="three-sample-live-drafts",
        objective=(
            "Create AT MOST 3 Gmail DRAFTS (draft-only, never sent) for the approved top-3 "
            "batch32 candidates using the visual-cold-open --sample-only live-draft path, so "
            "Charles can review and send them by hand."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Readiness blockers now: {_blocker_line(snap)}. "
            "Top-3 verified recipients (local-parts masked here; exact addresses in the "
            "recipient review CSV):\n" + _bullets(_recipient_lines(snap))
        ),
        source_of_truth=(
            f"Recipient review CSV: {csv_path} (exact addresses + recipient_fit + review "
            "status). Approval packet + sourcing CSV under "
            f"{snap.reports_dir}. Draft state of record: Gmail drafts for "
            "charles@madebymotionx.com."
        ),
        already_done=(
            "Candidates sourced, approved (APPROVE), de-duplicated against CRM + read-only "
            "Gmail; recipient emails verified from official pages; sample copy + brief "
            "validated in dry-run. Do NOT re-source or re-verify."
        ),
        codex_should_execute=_numbered([
            "First run `python3 outreach/agentic_ops/run.py vco-readiness`; proceed only if "
            "it prints READY_FOR_3_SAMPLE_LIVE_DRAFTS.",
            "Confirm Charles has explicitly approved these exact recipients (the review CSV "
            "still marks them REVIEW_ONLY_PENDING_CHARLES_APPROVAL until he does).",
            "For Trailpoint, use support@trailpoint.example ONLY if Charles approved a technical sample "
            "to a Customer-Experience mailbox; otherwise skip Trailpoint and use the next approved "
            "candidate.",
            "Run the visual-cold-open sample workflow in --sample-only --live-drafts with "
            "--limit 3 so it creates (drafts.create) up to three Gmail DRAFTS with the "
            "gpt-image-2 cold-open attachment — draft-only.",
            "Leave every draft UNSENT in Gmail for Charles's manual review; write the run "
            "report under ~/.motionx-outreach/reports/.",
        ]),
        codex_must_not=_bullets([
            "Exceed 3 drafts (MAX_SAMPLE_DRAFTS is a hard cap).",
            "Run full batch32 or treat this top-3 test as full-batch authorization.",
            "Send or schedule any of the drafts — Charles is the only human who sends.",
            "Use Trailpoint's Customer-Experience mailbox without recorded Charles approval.",
            "Fabricate product claims not present on the official page.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Each created draft is confirmed draft-only via the read-back check "
            "(is_draft=true, is_sent=false); the run report lists ≤3 "
            "DRAFT_CREATED_WITH_ATTACHMENT rows and zero send/schedule operations; masked "
            "draft ids only in any report."
        ),
        risks_unknowns=(
            "Recipient approval state can change — re-confirm before drafting. gpt-image-2 QA "
            "may reject an image (then the draft is created without attachment, not sent). "
            "Trailpoint CX-mailbox suitability is Charles's call."
        ),
    )


def _batch32_normalized_draft_dry_run(snap: Snapshot) -> Handoff:
    return Handoff(
        task="batch32-normalized-draft-dry-run",
        objective=(
            "Regenerate batch32 normalized draft previews in dry-run mode only, proving "
            "copy/data shape without Gmail, OpenAI, CRM mutation, or live outreach."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. batch32 inputs present: sourcing="
            f"{'yes' if snap.sourcing.get('present') else 'no'}, approval packet="
            f"{'yes' if snap.approval.get('present') else 'no'}, recipient review="
            f"{'yes' if snap.recipient_review.get('present') else 'no'}."
        ),
        source_of_truth=(
            f"batch32 sourcing/approval/recipient-review files under {snap.reports_dir}; "
            "normalized outreach workflow source in `outreach/`."
        ),
        already_done=(
            "batch32 sourcing and review artifacts already exist. Do not re-source or edit "
            "the original CSVs; this is a dry-run preview validation only."
        ),
        codex_should_execute=_numbered([
            "Locate the existing normalized dry-run command in the outreach runbook/source.",
            "Run the normalized draft dry-run only against batch32 inputs with outputs under "
            "~/.motionx-outreach/.",
            "Inspect the generated preview/report columns for status, recipient, source, and "
            "fabrication-safety fields.",
            "Write a short report path summary for Charles.",
        ]),
        codex_must_not=_bullets([
            "Use any live-draft flag.",
            "Create/update Gmail drafts or images.",
            "Edit leads.csv, candidate queues, source CSVs, or CRM statuses.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Dry-run exits 0, outputs are outside the repo, generated rows are preview-only, "
            "and every row states no live Gmail or OpenAI operation occurred."
        ),
        risks_unknowns=(
            "The normalized dry-run command may have changed; inspect local source first and "
            "use the repo's current interface rather than inventing flags."
        ),
    )


def _batch32_visual_dry_run(snap: Snapshot) -> Handoff:
    return Handoff(
        task="batch32-visual-dry-run",
        objective=(
            "Run the batch32 visual-cold-open sample workflow in dry-run preview mode only "
            "(no images, no Gmail) for up to the top 3 approved candidates."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Top-3 recipient review parsed with "
            f"{len(snap.verified_recipients)} verified recipient(s). Charles approval gate: "
            f"{'recorded' if snap.recipient_approval_summary.get('recorded') else 'pending'}."
        ),
        source_of_truth=(
            f"Approval packet: {snap.batch32_inputs.get('approval_packet') or 'not found'}. "
            f"Sourcing CSV: {snap.batch32_inputs.get('sourcing_csv') or 'not found'}. "
            "`outreach/visual_cold_open/run_batch.py` is the workflow source."
        ),
        already_done=(
            "Visual-cold-open sample mode exists and is capped at 3 outputs. This handoff is "
            "for a dry-run preview refresh only."
        ),
        codex_should_execute=_numbered([
            "Run the visual-cold-open sample workflow with `--sample-only`, "
            "`--source batch32-approval-packet`, and `--limit 3`.",
            "Keep it dry-run: do not pass `--live-drafts` and do not pass image-generation "
            "flags.",
            "Confirm the CSV/markdown sample report and local previews are under "
            "~/.motionx-outreach/.",
        ]),
        codex_must_not=_bullets([
            "Generate GPT images.",
            "Create/update Gmail drafts.",
            "Guess missing recipients.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "The sample report shows at most 3 SAMPLE_PREVIEW_WRITTEN rows, no attachment "
            "language unless an attachment exists, and sent_or_scheduled=no for every row."
        ),
        risks_unknowns=(
            "Dry-run copy may drift if templates changed; report the diff for Charles rather "
            "than treating it as automatic approval."
        ),
    )


def _manual_visual_prompt_pack(snap: Snapshot) -> Handoff:
    return Handoff(
        task="manual-visual-prompt-pack",
        objective=(
            "Create a no-API-cost manual visual prompt pack for batch32: draft copy, "
            "visual briefs, GPT-5.5 Pro Chat prompts, manifest, and Charles instructions "
            "under ~/.motionx-outreach/manual-visuals/."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Manual visuals do not need OPENAI_API_KEY. "
            f"Batch32 approval packet: {snap.batch32_inputs.get('approval_packet') or 'not found'}. "
            f"Sourcing CSV: {snap.batch32_inputs.get('sourcing_csv') or 'not found'}."
        ),
        source_of_truth=(
            "Manual visual workflow source: `outreach/visual_cold_open/run_batch.py` "
            "with `--manual-visuals prompt-pack`. Outputs live under "
            "~/.motionx-outreach/manual-visuals/<batch_id>/ and reports under "
            "~/.motionx-outreach/reports/."
        ),
        already_done=(
            "Visual-cold-open, sample approval-packet ingestion, and agentic-ops are merged. "
            "The direct API image path remains blocked by cost/access policy, so this task "
            "uses ChatGPT UI generation by Charles instead."
        ),
        codex_should_execute=_numbered([
            "Run the manual prompt-pack command with `--manual-visuals prompt-pack`, "
            "`--source batch32-approval-packet`, the batch32 approval packet, sourcing CSV, "
            "`--limit 20`, and a timestamped `--batch-id`.",
            "Confirm `README_FOR_CHARLES.md`, `manifest.csv`, `prompts/`, "
            "`email_previews/`, `briefs/`, and `images_ready/PLACE_IMAGES_HERE.txt` exist "
            "under ~/.motionx-outreach/manual-visuals/<batch_id>/.",
            "Confirm manifest rows use safe stable expected filenames and show "
            "`WAITING_FOR_CHARLES` / `NOT_CREATED` before images exist.",
            "Report the workspace path and the next import command for Charles.",
        ]),
        codex_must_not=_bullets([
            "Call OpenAI image APIs or require OPENAI_API_KEY for this manual prompt pack.",
            "Create or update Gmail drafts.",
            "Guess recipient addresses.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Prompt pack exits 0; outputs are outside the repo; prompt files include GPT-5.5 "
            "Pro Chat instructions; reports say OpenAI API calls=no and Gmail writes=no."
        ),
        risks_unknowns=(
            "Charles still needs to manually generate and save the images exactly as named "
            "in the manifest before import/preview/live draft steps can proceed."
        ),
    )


def _one_paste_chatgpt_visual_pack(snap: Snapshot) -> Handoff:
    return Handoff(
        task="one-paste-chatgpt-visual-pack",
        objective=(
            "Create the near-zero-manual batch32 visual workspace: one master GPT-5.5 "
            "Pro Chat prompt for all selected prospects, fallback 5-candidate chunks, "
            "manifest, briefs, local copy previews, and Charles instructions."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Manual ChatGPT visuals do not need OPENAI_API_KEY. "
            f"Batch32 approval packet: {snap.batch32_inputs.get('approval_packet') or 'not found'}. "
            f"Sourcing CSV: {snap.batch32_inputs.get('sourcing_csv') or 'not found'}."
        ),
        source_of_truth=(
            "Manual visual workflow source: `outreach/visual_cold_open/run_batch.py` "
            "with `--manual-visuals chatgpt-bulk-pack`. Outputs live under "
            "~/.motionx-outreach/manual-visuals/<batch_id>/ and reports under "
            "~/.motionx-outreach/reports/."
        ),
        already_done=(
            "Manual prompt-pack/import/preview/live-draft modes already exist and are "
            "DRAFT_ONLY. This task upgrades the prompt creation step so Charles can use "
            "one ChatGPT paste plus fallback chunks instead of one prompt per company."
        ),
        codex_should_execute=_numbered([
            "Run `--manual-visuals chatgpt-bulk-pack` with `--source "
            "batch32-approval-packet`, the batch32 approval packet, sourcing CSV, "
            "`--limit 20`, and a timestamped `--batch-id`.",
            "Confirm the workspace contains `README_FOR_CHARLES.md`, `manifest.csv`, "
            "`CHATGPT_ONE_PASTE_ALL_IMAGES.md`, `CHATGPT_ONE_PASTE_ALL_IMAGES.txt`, "
            "`CHATGPT_BATCH_01_05.txt`, `CHATGPT_BATCH_06_10.txt`, "
            "`CHATGPT_BATCH_11_15.txt`, `CHATGPT_BATCH_16_20.txt`, `prompts/`, "
            "`email_previews/`, `briefs/`, `images_downloaded/`, `images_ready/`, "
            "and `final_previews/`.",
            "Confirm the master prompt includes every selected candidate, expected "
            "filename, verified detail, three frame directions, guardrails, and "
            "`CONTINUE_FROM` recovery instructions.",
            "Report the workspace, master prompt, chunk prompt, and copy-helper paths.",
        ]),
        codex_must_not=_bullets([
            "Call OpenAI image APIs or require OPENAI_API_KEY.",
            "Automate or scrape the ChatGPT browser UI.",
            "Create or update Gmail drafts in this pack-only task.",
            "Invent recipient addresses, company facts, product claims, metrics, or prior "
            "MOTIONX relationships.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Bulk pack exits 0; all outputs are outside the repo; reports state OpenAI API "
            "calls=no, OPENAI_API_KEY required=no, Gmail writes=no, and sent_or_scheduled=no."
        ),
        risks_unknowns=(
            "Charles still needs to paste into ChatGPT and download the generated images. "
            "The ChatGPT UI is not a terminal API, so this remains user-side generation, "
            "not programmatic automation."
        ),
    )


def _collect_chatgpt_downloads(snap: Snapshot) -> Handoff:
    return Handoff(
        task="collect-chatgpt-downloads",
        objective=(
            "Collect Charles-downloaded ChatGPT images from a local downloads folder, map "
            "the newest supported files to manifest rows, copy/rename them into "
            "images_ready, QA them, and write a review index."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Gmail token present: "
            f"{'yes' if snap.gmail_token_present else 'NO'}; not needed for collection. "
            "Manual visuals do not need OPENAI_API_KEY."
        ),
        source_of_truth=(
            "Manual workspace `manifest.csv` under ~/.motionx-outreach/manual-visuals/"
            "<batch_id>/ and downloaded image files in ~/Downloads or the provided "
            "`--download-dir`."
        ),
        already_done=(
            "The one-paste ChatGPT bulk pack creates the manifest and expected stems. "
            "Charles downloads the generated images from ChatGPT; Codex performs local "
            "collection and QA only."
        ),
        codex_should_execute=_numbered([
            "Run `--manual-visuals collect-downloads` with the exact `--manual-manifest`, "
            "`--download-dir`, `--manual-image-dir`, and `--batch-id`.",
            "Confirm the collector selects the newest N supported png/jpg/jpeg/webp files "
            "and maps them to manifest rows in index order.",
            "Confirm originals remain in the downloads folder and copied files land in "
            "`images_ready/` without overwriting existing files unless "
            "`--allow-overwrite` was explicitly passed.",
            "Inspect `DOWNLOAD_COLLECT_MAPPING.md`, `DOWNLOAD_COLLECT_MAPPING.csv`, "
            "`IMAGE_REVIEW_INDEX.html`, and the report under ~/.motionx-outreach/reports/.",
        ]),
        codex_must_not=_bullets([
            "Delete, move, or rename files in ~/Downloads.",
            "Overwrite an existing accepted image without `--allow-overwrite`.",
            "Call OpenAI APIs, create Gmail drafts, or mutate CRM files.",
            "Guess missing images when counts do not line up; fail closed for Charles review.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Collector report lists one row per manifest candidate, accepted rows have "
            "copied paths and QA metadata, count mismatches create NEEDS_CHARLES_REVIEW, "
            "and no Gmail/OpenAI/CRM operation occurred."
        ),
        risks_unknowns=(
            "The collector maps by download time, so Charles should download generated "
            "images in manifest order. No OCR/vision is used; Charles must visually inspect "
            "the image content for stray text or invented claims."
        ),
    )


def _manual_visual_preview_with_collected_images(snap: Snapshot) -> Handoff:
    return Handoff(
        task="manual-visual-preview-with-collected-images",
        objective=(
            "Create attachment-ready local previews from images collected into "
            "images_ready, without Gmail writes."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Manual preview mode is local-only and does not need "
            "OPENAI_API_KEY or Gmail OAuth."
        ),
        source_of_truth=(
            "Manual `manifest.csv`, `email_previews/`, and `images_ready/` under "
            "~/.motionx-outreach/manual-visuals/<batch_id>/."
        ),
        already_done=(
            "The download collector copies and QA's ChatGPT images into images_ready. "
            "Import/preview modes already enforce attachment language only when an image "
            "exists."
        ),
        codex_should_execute=_numbered([
            "Run `--manual-visuals import-images` with the collected `images_ready/` "
            "directory and manifest; continue only for ACCEPTED rows.",
            "Run `--manual-visuals preview-with-images` with the same manifest, image "
            "directory, and batch id.",
            "Confirm `final_previews/` contains final email previews, attachment checks, "
            "and raw MIME previews only for accepted-image rows.",
            "Report preview CSV/markdown paths and the final_previews directory.",
        ]),
        codex_must_not=_bullets([
            "Create or update Gmail drafts in preview mode.",
            "Use attachment language for a row without an accepted image.",
            "Call OpenAI APIs or mutate CRM files.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Preview report shows LOCAL_PREVIEW_READY only for accepted images, "
            "body_says_attached=yes only when a file exists, and no Gmail/OpenAI operation "
            "occurred."
        ),
        risks_unknowns=(
            "Preview files are still local review artifacts. Gmail OAuth is needed only for "
            "a later explicit DRAFT_ONLY draft-attachment task."
        ),
    )


def _manual_visual_import(snap: Snapshot) -> Handoff:
    return Handoff(
        task="manual-visual-import",
        objective=(
            "Validate Charles-generated manual visual files against a manual prompt-pack "
            "manifest and write import reports, without Gmail writes or CRM mutation."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Gmail token present: "
            f"{'yes' if snap.gmail_token_present else 'NO'}; not needed for import-only."
        ),
        source_of_truth=(
            "Manual workspace manifest.csv + images_ready/ directory under "
            "~/.motionx-outreach/manual-visuals/<batch_id>/. Import reports are written "
            "under ~/.motionx-outreach/reports/."
        ),
        already_done=(
            "Prompt-pack mode creates the manifest and expected filenames. Charles creates "
            "the actual images in GPT-5.5 Pro Chat and places them in images_ready/."
        ),
        codex_should_execute=_numbered([
            "Run `--manual-visuals import-images` with the exact manifest path, image "
            "directory, and batch id from the prompt pack.",
            "Confirm PNG, JPG/JPEG, and WEBP files with plausible dimensions pass; missing, "
            "unsupported, duplicate, unreadable, or implausible files fail closed.",
            "Write and report the manual_visual_import_<batch_id>_<stamp>.md and .csv paths.",
            "Keep this import-only run local: no Gmail draft operation and no CRM update.",
        ]),
        codex_must_not=_bullets([
            "Create or update Gmail drafts in import-only mode.",
            "Call OpenAI APIs.",
            "Modify manifest source facts or CRM statuses.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Import report lists one row per manifest candidate, image_status is ACCEPTED "
            "only after QA passes, and no Gmail/OpenAI operation occurred."
        ),
        risks_unknowns=(
            "No OCR/vision is used; Charles must visually check the generated image for "
            "stray text or invented claims."
        ),
    )


def _manual_visual_live_drafts(snap: Snapshot) -> Handoff:
    return Handoff(
        task="manual-visual-live-drafts",
        objective=(
            "Create DRAFT_ONLY Gmail drafts with accepted Charles-generated manual images, "
            "only for verified recipients and only after the explicit live manual command."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Gmail OAuth token present: "
            f"{'yes' if snap.gmail_token_present else 'NO'}. Manual visuals do not need "
            "OPENAI_API_KEY; Gmail OAuth is needed only for automated draft attachment."
        ),
        source_of_truth=(
            "Manual manifest + images_ready/ under ~/.motionx-outreach/manual-visuals/; "
            "Gmail draft store for charles@madebymotionx.com; final reports under "
            "~/.motionx-outreach/reports/."
        ),
        already_done=(
            "Manual import/preview can validate images and write final local previews without "
            "Gmail. Live creation is separately gated by --live-drafts, Gmail OAuth, account "
            "verification, accepted image QA, and verified recipient email."
        ),
        codex_should_execute=_numbered([
            "Run `--manual-visuals import-images` first and proceed only for ACCEPTED rows.",
            "Run `--manual-visuals preview-with-images` and confirm attachment language "
            "appears only when a manual image is present.",
            "Run `--manual-visuals live-drafts-with-manual-images --live-drafts` with the "
            "manifest, image directory, Gmail token path, and explicit batch id.",
            "Confirm every created Gmail item reads back as DRAFT and not SENT; report final "
            "masked draft ids and any blocked rows.",
        ]),
        codex_must_not=_bullets([
            "Proceed without `--live-drafts` and Gmail OAuth for the Charles mailbox.",
            "Create a Gmail draft for a row without an accepted image or verified recipient.",
            "Use attachment language when no image is attached.",
            "Call OpenAI APIs.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Final report lists GMAIL_DRAFT_CREATED only for rows with accepted images and "
            "verified recipients; Gmail draft confirmation is yes; sent_or_scheduled=no; no "
            "OpenAI API call occurred."
        ),
        risks_unknowns=(
            "If Gmail OAuth is absent, the workflow writes final local previews and reports "
            "BLOCKED_ON_GMAIL_DRAFT_ACCESS. Verified recipient emails may still be absent "
            "for many batch32 candidates."
        ),
    )


def _batch32_full_live_drafts_after_review(snap: Snapshot) -> Handoff:
    return Handoff(
        task="batch32-full-live-drafts-after-review",
        objective=(
            "After Charles separately reviews and approves a full-batch plan, create Gmail "
            "DRAFTS for approved batch32 recipients only, DRAFT_ONLY and never released by "
            "automation."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Current readiness verdict: {snap.gate.verdict}. "
            f"Current blockers: {_blocker_line(snap)}. Top-3 approval state: "
            f"{'recorded' if snap.recipient_approval_summary.get('recorded') else 'pending'}."
        ),
        source_of_truth=(
            "Full-batch authorization must come from a separate Charles approval artifact; "
            f"batch32 source files live under {snap.reports_dir}; Gmail is only the draft "
            "store."
        ),
        already_done=(
            "This repository only records top-3 technical-sample approval so far. That does "
            "not authorize full batch32."
        ),
        codex_should_execute=_numbered([
            "Verify a separate full-batch Charles approval artifact exists outside the repo.",
            "Run `python3 outreach/agentic_ops/run.py vco-readiness`; continue only if it "
            "prints READY_FOR_3_SAMPLE_LIVE_DRAFTS or the future full-batch gate equivalent.",
            "Run the approved DRAFT_ONLY live-draft workflow with explicit limits from the "
            "approval artifact.",
            "Leave every Gmail draft in draft state for Charles's manual review.",
        ]),
        codex_must_not=_bullets([
            "Treat the top-3 technical-sample approval as full-batch authorization.",
            "Proceed without a separate full-batch approval artifact.",
            "Release, schedule, archive, label, trash, or delete Gmail messages.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Each touched Gmail item is verified as draft-only, generated reports list the "
            "explicit approval artifact and limit used, and no automated release operation "
            "occurred."
        ),
        risks_unknowns=(
            "This handoff is intentionally future-gated. As of now, credential readiness and "
            "full-batch authorization may both be absent."
        ),
    )


def _crm_gmail_reconcile(snap: Snapshot) -> Handoff:
    return Handoff(
        task="crm-gmail-reconcile",
        objective=(
            "Produce a read-only reconciliation between the CRM (leads.csv / state.json) and "
            "Gmail draft/label state so drift (missing labels, orphan drafts, stale statuses) "
            "is visible — without changing either side."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. CRM lives under {snap.crm_dir} (leads.csv, state.json, "
            "activity-log.csv, outcome-log.csv). Outreach is DRAFT_ONLY / TEST mode; the "
            "Gmail connector can read + create drafts but cannot send."
        ),
        source_of_truth=(
            f"CRM: files under {snap.crm_dir}. Gmail: read-only search/threads/labels for "
            "charles@madebymotionx.com (MOTIONX/Outreach label)."
        ),
        already_done=(
            "Prior reconciliations exist under ~/.motionx-outreach/reports/ "
            "(crm_gmail_reconciliation_*.md). Reuse their structure; only compute the delta "
            "since the latest one."
        ),
        codex_should_execute=_numbered([
            "Snapshot leads.csv + state.json (row counts, statuses) read-only.",
            "Read-only Gmail: list threads/drafts under the MOTIONX/Outreach label and "
            "collect message ids (no mutation).",
            "Diff the two: flag CRM rows with no matching Gmail draft/thread, Gmail drafts "
            "with no CRM row, and status mismatches.",
            "Write a reconciliation report (masked recipient local-parts, masked draft ids) "
            "under ~/.motionx-outreach/reports/crm_gmail_reconciliation_<stamp>.md + .csv.",
        ]),
        codex_must_not=_bullets([
            "Write back to the CRM or to Gmail (report only; Charles decides fixes).",
            "Apply or remove any Gmail label as part of reconciliation.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "The report enumerates exact counts on both sides and every mismatch, and states "
            "that no CRM/Gmail mutation occurred; a re-run produces the same delta."
        ),
        risks_unknowns=(
            "Gmail search windows (newer_than) can miss old threads; note the window used. "
            "Draft ids are sensitive — mask them. Label taxonomy may have changed."
        ),
    )


def _source_next_20(snap: Snapshot) -> Handoff:
    return Handoff(
        task="source-next-20",
        objective=(
            "Source the next 20 outreach candidates (review-only) with dedup against CRM and "
            "read-only Gmail, producing a sourcing CSV + approval packet for Charles — no "
            "drafts, no sends, no CRM writes."
        ),
        verified_current_state=(
            f"{_repo_line(snap)}. Latest batch32 sourcing produced "
            f"{snap.sourcing.get('total', 0)} candidates; approval packet: "
            f"{snap.approval.get('approve', 0)} APPROVE / {snap.approval.get('maybe', 0)} "
            f"MAYBE / {snap.approval.get('reject', 0)} REJECT."
        ),
        source_of_truth=(
            f"CRM dedup: leads.csv + candidate-queue.csv under {snap.crm_dir}. Prior batches: "
            "batch32_sourcing_candidates_*.csv and approval packet under "
            f"{snap.reports_dir}. Read-only Gmail domain search for prior contact."
        ),
        already_done=(
            "batch32 (20 candidates) is fully sourced, reviewed, and top-3 selected. Do NOT "
            "re-source batch32 companies; exclude every domain already in leads.csv / "
            "candidate-queue.csv / prior sourcing CSVs."
        ),
        codex_should_execute=_numbered([
            "Build an exclude-set from leads.csv, candidate-queue.csv, suppression.csv, and "
            "all prior batch3x sourcing CSVs.",
            "Identify 20 new motion-suited product brands NOT in the exclude-set; for each "
            "capture the official site, category, a verified on-site observation, the visual "
            "cold-open angle, and a public contact path.",
            "Run a read-only Gmail domain search per candidate to confirm no prior contact "
            "(record message-id count only).",
            "Write batch33_sourcing_candidates_<stamp>.csv + .md and a candidate approval "
            "packet under ~/.motionx-outreach/reports/ — review-only.",
        ]),
        codex_must_not=_bullets([
            "Create drafts or send email for any sourced candidate.",
            "Add candidates to leads.csv/candidate-queue.csv (approval packet only; Charles "
            "promotes).",
            "Invent contact evidence or product claims not visible on the official site.",
        ] + _COMMON_MUST_NOT),
        verification_required=(
            "Exactly 20 candidates, each with an official URL + verified observation + dedup "
            "result; zero overlap with the exclude-set; the packet totals APPROVE+MAYBE+"
            "REJECT = 20."
        ),
        risks_unknowns=(
            "Company facts drift — verify on the live official page at source time. Some "
            "brands only expose a contact form (no public email); note that rather than "
            "guessing an address."
        ),
    )


_BUILDERS: Dict[str, Callable[[Snapshot], Handoff]] = {
    "live-setup": _live_setup,
    "credentials-setup": _credentials_setup,
    "three-sample-live-drafts": _three_sample_live_drafts,
    "batch32-normalized-draft-dry-run": _batch32_normalized_draft_dry_run,
    "batch32-visual-dry-run": _batch32_visual_dry_run,
    "one-paste-chatgpt-visual-pack": _one_paste_chatgpt_visual_pack,
    "collect-chatgpt-downloads": _collect_chatgpt_downloads,
    "manual-visual-preview-with-collected-images": _manual_visual_preview_with_collected_images,
    "manual-visual-prompt-pack": _manual_visual_prompt_pack,
    "manual-visual-import": _manual_visual_import,
    "manual-visual-live-drafts": _manual_visual_live_drafts,
    "batch32-full-live-drafts-after-review": _batch32_full_live_drafts_after_review,
    "crm-gmail-reconcile": _crm_gmail_reconcile,
    "source-next-20": _source_next_20,
    "batch32-draft-dry-run": _batch32_normalized_draft_dry_run,
}


def build_handoff(task: str, snap: Snapshot) -> Handoff:
    if task not in _BUILDERS:
        raise KeyError(f"unknown handoff task {task!r}; valid tasks: {', '.join(TASKS)}")
    return _BUILDERS[task](snap)


def render_handoff(task: str, snap: Snapshot) -> str:
    """Build, safety-scan, and render a handoff to text. Raises ScanError if unsafe."""
    text = build_handoff(task, snap).render()
    scanner.assert_handoff_safe(text)   # fail-closed: never emit a send-as-action or a secret
    return text
