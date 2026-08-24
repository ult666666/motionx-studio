# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — configuration, defaults, paths, and status taxonomy.

This is an OPTIONAL, additive layer around the existing normalized DRAFT_ONLY
outreach workflow. It changes NO existing gate. Everything it writes lands OUTSIDE
the git repo (default under ~/.motionx-outreach/). See VISUAL-COLD-OPEN-RUNBOOK.md.

Safety invariants (enforced across the package):
  * DRAFT_ONLY — never send, never schedule, never call any *.send endpoint.
  * gpt-image-2 is the only image model for this mode (no silent downgrade).
  * Dry-run is the default; live Gmail draft ops require an explicit --live-drafts.
  * No secrets (API keys, OAuth creds, postal address) are ever written to the repo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

# ── Identity / immutable facts (mirror outreach/config.json; do not drift) ──────
SENDING_MAILBOX = "charles@madebymotionx.com"
SENDER_DISPLAY_NAME = "Charles Dai | MOTIONX"
CANONICAL_URL = "https://madebymotionx.com"
OUTREACH_LABEL = "MOTIONX/Outreach"

# The ONLY image model this mode uses. A downgrade requires Charles's explicit
# future authorization; there is deliberately NO CLI flag to bypass this.
REQUIRED_IMAGE_MODEL = "gpt-image-2"

# ── Default image parameters (medium quality chosen for cost safety) ────────────
DEFAULT_IMAGE_SIZE = "1536x1024"          # horizontal 3-panel board
DEFAULT_IMAGE_QUALITY = "medium"          # medium|high — medium is the cost-safe default
DEFAULT_IMAGE_FORMAT = "png"
DEFAULT_LIMIT = 20
DEFAULT_MAX_IMAGE_REGENERATIONS = 1

# Hard cap on how many sample drafts/previews a single --sample-only run may produce.
# This is a structural guard: even if --limit is set higher, sample mode never exceeds
# this. (This task authorizes at most 3 sample outputs.)
MAX_SAMPLE_DRAFTS = 3

# Plausible-dimension bounds for QA (a returned asset far off these is suspicious).
MIN_IMAGE_WIDTH = 512
MIN_IMAGE_HEIGHT = 384

# ── Paths (all OUTSIDE the repo) ────────────────────────────────────────────────
CRM_DIR = os.path.expanduser("~/.motionx-outreach")
DEFAULT_REPORTS_DIR = os.path.join(CRM_DIR, "reports")
DEFAULT_VISUAL_ASSETS_DIR = os.path.join(CRM_DIR, "visual-assets")
DEFAULT_MANUAL_VISUALS_DIR = os.path.join(CRM_DIR, "manual-visuals")
SECRETS_ENV_PATH = os.path.join(CRM_DIR, "secrets.env")
POSTAL_ADDRESS_ENV = "MOTIONX_POSTAL_ADDRESS"
POSTAL_PLACEHOLDER = "{{MOTIONX_POSTAL_ADDRESS}}"

# The visual layer keeps its OWN activity log so it never corrupts the existing
# 13-column ~/.motionx-outreach/activity-log.csv (a different schema). See runbook.
DEFAULT_ACTIVITY_LOG_NAME = "visual-cold-open-activity-log.csv"

# ── Status taxonomy (superset of the existing lead statuses) ────────────────────
STATUS = {
    "NOT_STARTED": "NOT_STARTED",
    "PREFLIGHT_OK": "PREFLIGHT_OK",
    "DRY_RUN_OK": "DRY_RUN_OK",
    "BLOCKED_ON_GPT_IMAGE_2_ACCESS": "BLOCKED_ON_GPT_IMAGE_2_ACCESS",
    "BLOCKED_ON_GMAIL_API": "BLOCKED_ON_GMAIL_API",
    "BLOCKED_ON_PROSPECT_SOURCE": "BLOCKED_ON_PROSPECT_SOURCE",
    "BLOCKED_ON_VISUAL_GENERATION": "BLOCKED_ON_VISUAL_GENERATION",
    "BLOCKED_ON_VISUAL_QA": "BLOCKED_ON_VISUAL_QA",
    "BLOCKED_ON_FABRICATION": "BLOCKED_ON_FABRICATION",
    "DRAFT_CREATED_WITH_ATTACHMENT": "DRAFT_CREATED_WITH_ATTACHMENT",
    "DRAFT_UPDATED_WITH_ATTACHMENT": "DRAFT_UPDATED_WITH_ATTACHMENT",
    "DRAFT_CREATED_NO_ATTACHMENT": "DRAFT_CREATED_NO_ATTACHMENT",
    "NEEDS_CHARLES_REVIEW": "NEEDS_CHARLES_REVIEW",
    "SKIPPED_DUPLICATE": "SKIPPED_DUPLICATE",
    "SKIPPED_INELIGIBLE": "SKIPPED_INELIGIBLE",
    "VERIFIED_DRAFT_ONLY": "VERIFIED_DRAFT_ONLY",
    # ── sample-mode statuses ────────────────────────────────────────────────
    "SAMPLE_PREVIEW_WRITTEN": "SAMPLE_PREVIEW_WRITTEN",
    "BLOCKED_ON_APPROVAL_PACKET_PARSE": "BLOCKED_ON_APPROVAL_PACKET_PARSE",
    "BLOCKED_ON_GMAIL_DRAFT_ACCESS": "BLOCKED_ON_GMAIL_DRAFT_ACCESS",
    "BLOCKED_ON_RECIPIENT_UNVERIFIED": "BLOCKED_ON_RECIPIENT_UNVERIFIED",
    # ── manual-visuals statuses ───────────────────────────────────────────
    "MANUAL_PROMPT_PACK_READY": "MANUAL_PROMPT_PACK_READY",
    "MANUAL_IMAGE_ACCEPTED": "MANUAL_IMAGE_ACCEPTED",
    "MANUAL_PREVIEW_READY": "MANUAL_PREVIEW_READY",
}

# Pilot offer prices (mirror outreach/config.json:offers_pilot_prices) — used only
# to keep the attachment copy honest; the body/price come from the source item.
OFFERS_PILOT_PRICES = {
    "Product Film": 399,
    "Motion-First Website": 699,
    "Film + Website Launch System": 999,
    "Campaign Content Add-On": 190,
}


@dataclass
class VCOConfig:
    """Resolved run configuration. Built by run_batch from CLI args."""
    mode: str = "dry-run"                       # dry-run | live-drafts | preflight
    image_model: str = REQUIRED_IMAGE_MODEL
    image_size: str = DEFAULT_IMAGE_SIZE
    image_quality: str = DEFAULT_IMAGE_QUALITY
    image_format: str = DEFAULT_IMAGE_FORMAT
    limit: int = DEFAULT_LIMIT
    max_image_regenerations: int = DEFAULT_MAX_IMAGE_REGENERATIONS

    batch_id: str = ""
    prospect_source: str = ""                   # path to a drafts.json / manifest
    source_kind: str = "drafts-json"            # drafts-json | existing-gmail-drafts | batch32-approval-packet

    allow_update_existing_drafts: bool = False
    allow_duplicate_replacement_drafts: bool = False
    generate_images_in_dry_run: bool = False
    generate_test_image: bool = False

    # ── sample-only mode (approval-packet ingestion) ────────────────────────
    sample_only: bool = False
    approval_packet_path: str = ""              # batch32 approval packet (.md)
    candidate_csv_path: str = ""                # batch32 sourcing candidates (.csv)

    # ── manual-visuals mode (no OpenAI API image generation) ────────────────
    manual_visuals_mode: str = ""               # prompt-pack | chatgpt-bulk-pack | ...
    manual_root_dir: str = DEFAULT_MANUAL_VISUALS_DIR
    manual_image_dir: str = ""
    manual_manifest_path: str = ""
    download_dir: str = os.path.expanduser("~/Downloads")
    download_since_minutes: int = 180
    allow_overwrite: bool = False
    collect_dry_run: bool = False

    reports_dir: str = DEFAULT_REPORTS_DIR
    assets_dir: str = ""                        # resolved to .../visual-assets/<batch_id>
    activity_log_path: str = ""

    expected_account: str = SENDING_MAILBOX
    postal_address: str = POSTAL_PLACEHOLDER    # resolved-or-placeholder (dry-run)
    gmail_credentials_path: str = ""
    gmail_token_path: str = ""

    # Populated at runtime; never printed with secrets.
    repo_root: str = ""

    def resolved_assets_dir(self) -> str:
        if self.assets_dir:
            return self.assets_dir
        return os.path.join(DEFAULT_VISUAL_ASSETS_DIR, self.batch_id or "unbatched")

    def resolved_activity_log(self) -> str:
        if self.activity_log_path:
            return self.activity_log_path
        return os.path.join(self.reports_dir, DEFAULT_ACTIVITY_LOG_NAME)

    @property
    def is_live(self) -> bool:
        return self.mode == "live-drafts"


def read_postal_address(explicit: Optional[str] = None) -> str:
    """Resolve the private postal address (compliance footer only).

    Order: explicit arg → MOTIONX_POSTAL_ADDRESS env → secrets.env → placeholder.
    NEVER logged, committed, or written into the repo. An unresolved value returns
    the placeholder, which callers treat as 'not resolved' (live drafts blocked).
    """
    if explicit and explicit.strip() and POSTAL_PLACEHOLDER not in explicit:
        return explicit.strip()
    env = os.environ.get(POSTAL_ADDRESS_ENV, "").strip()
    if env and POSTAL_PLACEHOLDER not in env:
        return env
    if os.path.exists(SECRETS_ENV_PATH):
        try:
            with open(SECRETS_ENV_PATH, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith(POSTAL_ADDRESS_ENV + "="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and POSTAL_PLACEHOLDER not in val:
                            return val
        except OSError:
            pass
    return POSTAL_PLACEHOLDER


def postal_resolved(value: str) -> bool:
    return bool(value) and POSTAL_PLACEHOLDER not in value and value.strip() != ""
