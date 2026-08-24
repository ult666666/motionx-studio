# MOTIONX Visual Cold-Open — operator runbook

An **optional, additive** layer around the existing normalized DRAFT_ONLY outreach
workflow. It generates a rough 3-panel concept board per prospect with **gpt-image-2**
and attaches it to a Gmail **draft** (new or retrofitted). It changes **no existing
gate** in `preflight.py` / `SKILL.md` / `config.json`, and it **never sends or
schedules email**.

- Code: `outreach/visual_cold_open/` (pure-stdlib except lazy `openai` + Gmail API).
- Tests: `outreach/tests/test_visual_*.py` (all mocked; no real API calls).
- Everything generated (images, reports, raw drafts) is written **outside the repo**,
  by default under `~/.motionx-outreach/`.

---

## What it does (per selected prospect)

1. Reuses the prospects the normalized workflow already selected (a `*_drafts.json`).
2. Builds one **internal visual brief** from *already-verified* fields only (company,
   category, the verified observation, the proposed creative direction). It invents
   no features, clients, metrics, awards, testimonials, funding, partnerships, or any
   prior MOTIONX relationship. A fabrication guard blocks the prospect if a fabricated
   claim is detected in the brief or prompt.
3. Builds a **gpt-image-2 prompt** (rough speculative concept sketch; explicit
   "no fake metrics / testimonials / awards / customers / press logos / prior work"
   instructions; minimal text).
4. **Generates** one horizontal 3-panel PNG (default `1536x1024`, quality `medium`).
5. **QA**s the asset (PNG signature + dimensions via pure stdlib, format/MIME match,
   company match, fabrication scan, tiny-placeholder heuristic). In-image text is
   **not** machine-inspected (no OCR here) — that is flagged for human review.
6. Creates a **new Gmail draft** with the image attached, **or** updates an existing
   draft's raw MIME to add the attachment (retrofit). Uses RFC 2822 multipart MIME,
   base64URL-encoded into `message.raw`, via `drafts.create` / `drafts.update`.
7. **Verifies** the draft is DRAFT-labelled and not SENT.
8. Writes a per-prospect CSV report, a markdown summary, and a dedicated activity log.

The email body only mentions the attachment **when an image is actually attached**;
otherwise all "attached" language is removed and the prospect is marked blocked /
needs-review (a misleading draft is never created).

---

## Required environment / secrets

| What | Where | Notes |
|---|---|---|
| `OPENAI_API_KEY` | environment (or approved secret mgmt) | Never printed, never in the repo. Required for image generation / preflight. |
| `openai` SDK | `pip install openai` | Lazy-imported; only needed when generating images. |
| Gmail API client | `pip install google-api-python-client google-auth-oauthlib` | Only needed for `--live-drafts`. |
| Gmail OAuth token | `--gmail-token ~/.motionx-outreach/gmail_token.json` (+ `--gmail-credentials` for first-run consent) | Scope `gmail.compose`. Files live **outside** the repo. |
| `MOTIONX_POSTAL_ADDRESS` | `~/.motionx-outreach/secrets.env` (or `--postal-address`) | Compliance footer. Live drafts are blocked until resolved. |

> **Why a direct Gmail API path?** The MCP Gmail connector used by the normalized
> workflow cannot attach files or update a draft (`create/list/get/label` only). The
> visual layer therefore uses the Gmail API directly from the CLI for the live path.
> The connector remains the create-only path for the normalized workflow.

---

## Commands

Run from the repo root (`~/Desktop/MotionX`). `--visual-cold-open` is required.

### Dry-run (default — no images, no Gmail; shows the plan)
```bash
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open \
  --prospect-source ~/.motionx-outreach/_batch31_drafts.json \
  --batch-id batch31-visual --limit 20
```
Writes a brief + prompt + non-attached body preview per prospect, and a report — no
Gmail calls, no image generation.

### Dry-run + real image generation (assets written outside the repo; still no Gmail)
```bash
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open \
  --prospect-source ~/.motionx-outreach/_batch31_drafts.json \
  --batch-id batch31-visual --generate-images-in-dry-run --limit 1
```

### Sample-only (≤3 previews/drafts from the batch32 approval packet)
```bash
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --sample-only \
  --source batch32-approval-packet \
  --approval-packet ~/.motionx-outreach/reports/batch32_candidate_approval_packet_2026-07-08_0842.md \
  --candidate-csv ~/.motionx-outreach/reports/batch32_sourcing_candidates_2026-07-07_2134.csv \
  --limit 3 --image-model gpt-image-2 --image-size 1536x1024 --image-format png \
  --generate-images-in-dry-run --batch-id batch32_vco_samples_$(date +%Y%m%d_%H%M)
```
Selects the top-N **APPROVE** rows by rank (N capped at 3). Writes a short
"Rough visual thought for …" note + visual brief + gpt-image-2 prompt per candidate.
Dry-run writes local previews only; add `--live-drafts` (plus a resolved postal
address and a verified recipient) to create Gmail DRAFTS with the attachment. A
candidate with only a public contact *page* (no verified email) never gets a guessed
address — it blocks `BLOCKED_ON_RECIPIENT_UNVERIFIED` and a local preview is written.
Report: `~/.motionx-outreach/reports/batch32_vco_sample_run_<YYYY-MM-DD_HHMM>.{csv,md}`.

### Manual visuals (no OpenAI API image cost)
Use this when Charles wants Codex to prepare the copy + visual prompts, then manually
generate the images in GPT-5.5 Pro Chat and save them locally for validation/attachment.
These modes do **not** require `OPENAI_API_KEY` and do **not** call OpenAI APIs.

#### 1. One-paste ChatGPT visual batch (primary manual path)
```bash
python3 outreach/visual_cold_open/run_batch.py \
  --visual-cold-open \
  --manual-visuals chatgpt-bulk-pack \
  --source batch32-approval-packet \
  --approval-packet ~/.motionx-outreach/reports/batch32_candidate_approval_packet_2026-07-08_0842.md \
  --candidate-csv ~/.motionx-outreach/reports/batch32_sourcing_candidates_2026-07-07_2134.csv \
  --limit 20 \
  --batch-id batch32_one_paste_visuals_$(date +%Y%m%d_%H%M)
```
Writes the one-paste workspace outside the repo:

```
~/.motionx-outreach/manual-visuals/<batch_id>/
  README_FOR_CHARLES.md
  manifest.csv
  CHATGPT_ONE_PASTE_ALL_IMAGES.md
  CHATGPT_ONE_PASTE_ALL_IMAGES.txt
  CHATGPT_BATCH_01_05.txt
  CHATGPT_BATCH_06_10.txt
  CHATGPT_BATCH_11_15.txt
  CHATGPT_BATCH_16_20.txt
  copy_master_prompt.sh
  prompts/
  email_previews/
  briefs/
  images_downloaded/
  images_ready/
  final_previews/
```

`CHATGPT_ONE_PASTE_ALL_IMAGES.txt` is paste-ready for GPT-5.5 Pro Chat. It tells
ChatGPT to generate exactly one image per candidate, in manifest order, and to print
`IMAGE NN/TT`, `EXPECTED_FILENAME: ...`, and `COMPANY: ...` before each image. If
ChatGPT hits generation limits, it should stop with `CONTINUE_FROM: NN`.

Fallback chunk prompts are grouped in fives. They are only for cases where the ChatGPT
conversation cannot reliably finish all candidates from the master prompt.

To copy the master prompt on macOS:

```bash
~/.motionx-outreach/manual-visuals/<batch_id>/copy_master_prompt.sh
```

That helper only runs `pbcopy` and prints "Now paste into GPT-5.5 Pro Chat." It does
not call OpenAI APIs, automate the ChatGPT browser UI, or require `OPENAI_API_KEY`.

After pasting, Charles downloads each generated image from the ChatGPT UI. This is why
the workflow avoids OpenAI API billing. It is still not true programmatic ChatGPT
automation: the terminal cannot generate or download from the ChatGPT UI by itself.

#### 1b. Legacy prompt pack only (one prompt per company)
```bash
python3 outreach/visual_cold_open/run_batch.py \
  --visual-cold-open \
  --manual-visuals prompt-pack \
  --source batch32-approval-packet \
  --approval-packet ~/.motionx-outreach/reports/batch32_candidate_approval_packet_2026-07-08_0842.md \
  --candidate-csv ~/.motionx-outreach/reports/batch32_sourcing_candidates_2026-07-07_2134.csv \
  --limit 20 \
  --batch-id batch32_manual_visuals_$(date +%Y%m%d_%H%M)
```
Writes the manual workspace outside the repo:

```
~/.motionx-outreach/manual-visuals/<batch_id>/
  README_FOR_CHARLES.md
  manifest.csv
  prompts/
  email_previews/
  briefs/
  images_downloaded/
  images_ready/PLACE_IMAGES_HERE.txt
  final_previews/
```

`README_FOR_CHARLES.md` tells Charles to generate exactly one image per prompt in
GPT-5.5 Pro Chat, save each file using the exact manifest filename, and place finished
images in `images_ready/`. If the chat UI struggles, use 4 chunks of 5 or 5 chunks of 4.

#### 2. Collect downloaded ChatGPT images
```bash
python3 outreach/visual_cold_open/run_batch.py \
  --visual-cold-open \
  --manual-visuals collect-downloads \
  --manual-manifest ~/.motionx-outreach/manual-visuals/<batch_id>/manifest.csv \
  --download-dir ~/Downloads \
  --manual-image-dir ~/.motionx-outreach/manual-visuals/<batch_id>/images_ready \
  --batch-id <batch_id>
```

Collector behavior:

- Reads `manifest.csv`.
- Looks for recent `png`, `jpg`, `jpeg`, and `webp` files under `--download-dir`
  (default `~/Downloads`, default window 180 minutes).
- Selects the newest N supported image files, where N is the manifest row count.
- Maps those selected files to manifest rows in index order. Charles should download
  from ChatGPT in the same order ChatGPT generated the images.
- Copies files into `images_ready/` using the exact manifest filename; originals in
  Downloads are never moved or deleted.
- Refuses to overwrite existing files unless `--allow-overwrite` is passed.
- Fails closed with `NEEDS_CHARLES_REVIEW` if fewer than N supported downloads exist.
- Runs the same local image QA used by import/preview and marks failed rows `FAILED_QA`.
- Writes `DOWNLOAD_COLLECT_MAPPING.{csv,md}` and `IMAGE_REVIEW_INDEX.html` in the
  workspace, plus `manual_visual_collect_downloads_<batch_id>_<stamp>.{csv,md}` under
  `~/.motionx-outreach/reports/`.

If a source download's actual format differs from the manifest filename extension, QA
sniffs the file bytes, records the actual MIME type, and keeps the exact manifest
filename so later import/preview steps still match the manifest.

Collector mode never calls Gmail, never creates drafts, never calls OpenAI APIs, and
never mutates CRM.

#### 3. Import manually generated images
```bash
python3 outreach/visual_cold_open/run_batch.py \
  --visual-cold-open \
  --manual-visuals import-images \
  --manual-image-dir ~/.motionx-outreach/manual-visuals/<batch_id>/images_ready \
  --manual-manifest ~/.motionx-outreach/manual-visuals/<batch_id>/manifest.csv \
  --batch-id <batch_id>
```
Validates PNG/JPG/JPEG/WEBP files for existence, readability, supported byte format,
plausible dimensions, plausible file size, duplicate filename collisions, and
one-image-per-row mapping. It writes:
`~/.motionx-outreach/reports/manual_visual_import_<batch_id>_<YYYY-MM-DD_HHMM>.{csv,md}`.
Import-only never calls Gmail, never creates drafts, and never mutates CRM.

#### 4. Attachment-ready local previews
```bash
python3 outreach/visual_cold_open/run_batch.py \
  --visual-cold-open \
  --manual-visuals preview-with-images \
  --manual-image-dir ~/.motionx-outreach/manual-visuals/<batch_id>/images_ready \
  --manual-manifest ~/.motionx-outreach/manual-visuals/<batch_id>/manifest.csv \
  --batch-id <batch_id>
```
Writes final local previews under:

```
~/.motionx-outreach/manual-visuals/<batch_id>/final_previews/
```

Attachment language appears only for candidates whose manual image passes QA. No Gmail
call is made.

#### 5. Gmail drafts with manual images (gated)
```bash
python3 outreach/visual_cold_open/run_batch.py \
  --visual-cold-open \
  --manual-visuals live-drafts-with-manual-images \
  --manual-image-dir ~/.motionx-outreach/manual-visuals/<batch_id>/images_ready \
  --manual-manifest ~/.motionx-outreach/manual-visuals/<batch_id>/manifest.csv \
  --live-drafts \
  --gmail-token ~/.motionx-outreach/gmail_token.json \
  --batch-id <batch_id>
```
This creates Gmail **drafts only** and only when every gate passes: `--live-drafts`,
Gmail OAuth token exists, account verifies as `charles@madebymotionx.com`, postal footer
is resolved, the manual image passed QA, and the recipient email is verified in the
source CSV. If Gmail OAuth is missing, it writes `final_previews/` and a final report
with `BLOCKED_ON_GMAIL_DRAFT_ACCESS`; no real draft is created.

### Preflight only (cheap gpt-image-2 access check, no batch generation)
```bash
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --mode preflight \
  --prospect-source ~/.motionx-outreach/_batch31_drafts.json
```

### One test image only (real API, written outside the repo, no drafts)
```bash
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --generate-test-image \
  --prospect-source ~/.motionx-outreach/_batch31_drafts.json --batch-id smoke
```

### Live — create NEW drafts with the image attached (only after review)
```bash
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --live-drafts \
  --prospect-source <undrafted_batch>.json --batch-id <id> \
  --gmail-token ~/.motionx-outreach/gmail_token.json
```

### Live — RETROFIT existing batch31 drafts with attachments (opt-in)
```bash
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --live-drafts \
  --source existing-gmail-drafts \
  --prospect-source ~/.motionx-outreach/_batch31_drafts.json \
  --manifest ~/.motionx-outreach/_batch31_created_manifest.json \
  --allow-update-existing-drafts --batch-id batch31-visual \
  --gmail-token ~/.motionx-outreach/gmail_token.json
```
By default retrofit **updates** the existing draft (same draft id) rather than
creating a duplicate. Pass `--allow-duplicate-replacement-drafts` only if you
intend to create replacement drafts instead.

### Flags
`--image-model gpt-image-2` (only allowed value) · `--image-size 1536x1024` ·
`--image-quality medium|high` · `--image-format png` · `--limit 20` ·
`--max-image-regenerations 1` · `--report-path` · `--asset-dir` · `--batch-id` ·
`--postal-address` · `--expected-account charles@madebymotionx.com` ·
`--sample-only` · `--source batch32-approval-packet` · `--approval-packet` ·
`--candidate-csv` · `--manual-visuals chatgpt-bulk-pack|collect-downloads|prompt-pack|import-images|preview-with-images|live-drafts-with-manual-images` ·
`--download-dir` · `--download-since-minutes` · `--allow-overwrite` · `--collect-dry-run`.

---

## Safety invariants (enforced in code + tests)

- **DRAFT_ONLY.** No send/schedule/insert/trash/delete endpoint is ever called. The
  Gmail adapter has no send method; any attribute whose name contains `send`,
  `schedule`, `delete`, `trash`, or `insert` raises `SendForbiddenError`; every op
  routes through `safety.assert_allowed_draft_op` (whitelist:
  `drafts.create/update/get/list`). `sent_or_scheduled` in every report row is
  hard-wired to `no`.
- **gpt-image-2 only.** A different `--image-model` exits with an error; there is no
  downgrade flag.
- **Manual visuals do not use OpenAI APIs.** Any `--manual-visuals ...` mode never calls
  image generation and does not require `OPENAI_API_KEY`. `chatgpt-bulk-pack` creates
  one master ChatGPT prompt plus fallback chunks; `collect-downloads` only copies and
  QA's local files.
- **Dry-run by default.** Live Gmail writes require `--live-drafts`; retrofit also
  requires `--allow-update-existing-drafts`.
- **No fabrication.** Brief/prompt are built from verified fields; a fabrication or
  prior-relationship match blocks the prospect (`BLOCKED_ON_FABRICATION`).
- **No misleading copy.** Attachment language appears **iff** an image is attached
  (guarded by `assert_attachment_language_consistent`).
- **Nothing in the repo.** Images/reports/raw drafts write outside the repo; a write
  inside the repo is refused; `.gitignore` is a defensive backstop.
- **No secrets logged.** API keys / OAuth tokens / client secrets are redacted from
  all output; the recipient is masked in reports (`j***@domain`).
- **Right mailbox.** Live mode verifies the Gmail account is
  `charles@madebymotionx.com` (`WrongAccountError` otherwise).
- **Postal resolved-or-block.** Live drafts require a resolved `MOTIONX_POSTAL_ADDRESS`.

---

## Where things go

- Images: `~/.motionx-outreach/visual-assets/<batch_id>/motionx_visual_cold_open_<slug>_<YYYY-MM-DD>.png`
- Briefs/prompts: `~/.motionx-outreach/visual-assets/<batch_id>/brief_<slug>_<date>.json`
- Raw MIME preview (dry-run): `.../draft_<slug>_<date>.raw.b64url`
- Report CSV: `~/.motionx-outreach/reports/<batch_id>_visual_cold_open_report.csv`
- Summary: `~/.motionx-outreach/reports/<batch_id>_visual_cold_open_summary.md`
- Activity log: `~/.motionx-outreach/reports/visual-cold-open-activity-log.csv`
  (a **dedicated** log — it deliberately does **not** write into the existing
  13-column `~/.motionx-outreach/activity-log.csv`, to avoid corrupting that schema.)

## How to verify no email was sent

- Every report/summary row shows `sent_or_scheduled = no`; the run prints
  `No email was sent or scheduled.`
- The code cannot send: `grep -rniE "\.send|messages_send|drafts_send" outreach/visual_cold_open`
  returns only the guards that *reject* send.
- In Gmail, the touched threads carry the `DRAFT` label and are **not** in Sent
  (`verify_draft_only` asserts this; `gmail_draft_confirmed = yes` when confirmed).

## How to read the report

One row per prospect. Key columns: `draft_action` (created/updated/skipped/blocked),
`visual_status` (generated/attached/failed_generation/failed_qa/not_created),
`body_says_attached`, `fabrication_check_passed`, `gmail_draft_confirmed`,
`sent_or_scheduled` (always `no`), `notes` (blocker/uncertainty detail).

## Common blockers

| Symptom | Cause | Fix |
|---|---|---|
| `BLOCKED_ON_GPT_IMAGE_2_ACCESS` | `OPENAI_API_KEY` unset or `openai` not installed | export the key; `pip install openai` |
| gpt-image-2 preflight FAILED | key lacks image access / model not enabled | enable gpt-image-2 for the key |
| `BLOCKED_ON_PROSPECT_SOURCE` | `--prospect-source` path wrong | point at a valid `*_drafts.json` |
| `SKIPPED_INELIGIBLE` (0 eligible) | source items failed normalized preflight / no recipient | re-run the normalized workflow first |
| `BLOCKED_ON_GMAIL_API` | Gmail libs/creds missing, or wrong account | install libs; provide `--gmail-token`; use charles@ |
| `BLOCKED_ON_GMAIL_DRAFT_ACCESS` in manual live mode | Gmail OAuth token missing/wrong, account verification failed, or postal footer unresolved | set up Gmail OAuth for charles@ and resolve postal footer; use local previews until then |
| retrofit did nothing (exit 1) | `--allow-update-existing-drafts` missing | add the flag |
| footer shows `{{MOTIONX_POSTAL_ADDRESS}}` | postal address unresolved | set it in `secrets.env` or `--postal-address` |
| `BLOCKED_ON_VISUAL_QA` | image failed QA after one regeneration | inspect the asset; re-run or escalate to Charles |

## Residual risks

- The `gmail.compose` OAuth scope technically permits sending; the *only* protection
  is that this code never calls a send endpoint (guarded + tested). Keep it that way.
- No OCR: in-image text is not machine-verified. **A human (Charles) must look at the
  actual render** before any send to confirm no stray text/metrics/logos slipped in.

---

## Codex handoff

**Objective:** Attach a gpt-image-2 3-panel concept board to MOTIONX outreach Gmail
**drafts** (new or retrofit onto batch31's existing drafts), DRAFT_ONLY, after Charles
reviews each one. Never send.

**Verified current state (checked 2026-07-07 in this worktree):**
- Code + tests implemented on branch `feature/visual-cold-open-attachments`
  (worktree `~/Desktop/MotionX-visual-cold-open-worktree`). All 41 visual unit tests
  pass; the existing 170-check `preflight.py` suite still passes.
- Dry-run verified against a synthetic fixture (no real CRM data): report + brief +
  prompt + non-attached preview generated correctly, no Gmail calls.
- **NOT yet run against real prospects, real gpt-image-2, or real Gmail.**
  `OPENAI_API_KEY` is **not set** and `openai` / `google-api-python-client` are **not
  installed** in the current environment.

**Source of truth:** repo `outreach/visual_cold_open/` (code) + `~/.motionx-outreach/`
(prospects, drafts, manifests, secrets — outside the repo). Gmail is the draft store.

**Already done (don't redo):** module implementation, MIME/attachment builder, Gmail
draft adapter with send-tripwire, fabrication guard, QA, reports, CLI, tests, this
runbook. The normalized workflow (prospect selection, copy, preflight) is untouched.

**Codex should execute (bounded, ordered):**
1. `pip install openai google-api-python-client google-auth-oauthlib` in the CLI env.
2. `export OPENAI_API_KEY=…` (do not echo it).
3. Preflight: `--mode preflight` against `_batch31_drafts.json` → confirm gpt-image-2 OK.
4. One test image: `--generate-test-image` → eyeball the PNG under `visual-assets/`.
5. Dry-run + images on `--limit 1`, review the brief/prompt/raw preview.
6. Obtain a `gmail.compose` OAuth token for `charles@madebymotionx.com`
   (`--gmail-credentials` once to mint `--gmail-token`).
7. Live retrofit on `--limit 1` first (batch31, `--source existing-gmail-drafts
   --manifest _batch31_created_manifest.json --allow-update-existing-drafts`), then
   **have Charles open the updated draft and confirm the attachment + copy** before
   scaling to the full batch.

**Codex must NOT:** send or schedule any email; call `messages.send` / `drafts.send`;
downgrade off gpt-image-2; write assets/reports/secrets into the repo; touch the dirty
`outreach/self-improvement.md` or any unrelated file; push to remote; create drafts on
any account other than `charles@madebymotionx.com`; generate visuals implying MOTIONX
already worked with the prospect.

**Verification required:** report shows `sent_or_scheduled=no` and, for live rows,
`gmail_draft_confirmed=yes`; the updated Gmail draft is DRAFT-labelled, not in Sent,
and Charles has visually confirmed the attached board. `grep` shows no send call.

**Risks / unknowns:** real gpt-image-2 output quality (needs the human visual check —
no OCR here); `gmail.compose` scope includes send capability (mitigated only by the
code guard); the exact `openai` image kwargs may need a minor tweak for the installed
SDK version (the request dict is built defensively; adjust `image_client.generate` if
the SDK rejects a kwarg).
