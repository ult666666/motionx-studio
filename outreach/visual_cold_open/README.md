# outreach/visual_cold_open

Optional gpt-image-2 **visual cold-open** + Gmail **image-attachment** layer around the
existing normalized DRAFT_ONLY outreach workflow. It changes no existing gate and
**never sends or schedules email**.

**Operator guide:** [`../VISUAL-COLD-OPEN-RUNBOOK.md`](../VISUAL-COLD-OPEN-RUNBOOK.md)

## Modules
| File | Responsibility |
|---|---|
| `config.py` | defaults, paths (all outside repo), status taxonomy, postal resolution, sample cap |
| `safety.py` | send-tripwire, account/secret guards, recipient + draft-id masking |
| `brief.py` | visual brief + gpt-image-2 prompt + fabrication guard |
| `sample_source.py` | approval-packet + sourcing-CSV ingestion; top-N APPROVE selection |
| `sample_copy.py` | short "Rough visual thought for …" sample note (attachment copy iff attached) |
| `image_client.py` | gpt-image-2 client (lazy `openai`), b64 decode, fail-closed |
| `image_qa.py` | pure-stdlib PNG QA (signature/dims), fabrication scan |
| `copy_integration.py` | attachment sentence woven in *iff* an image is attached |
| `mime_builder.py` | multipart RFC 2822 MIME → base64URL `message.raw` |
| `gmail_draft.py` | `drafts.create/update/get` only (Gmail API); no send method |
| `report.py` | CSV report + MD summary + dedicated activity log (masked, scrubbed) |
| `run_batch.py` | CLI orchestrator; dry-run default, `--live-drafts` for Gmail writes |

## Run (from repo root)
```bash
# dry-run (no images, no Gmail)
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open \
  --prospect-source ~/.motionx-outreach/_batch31_drafts.json --batch-id batch31-visual

# sample-only: at most 3 previews/drafts from the top APPROVE approval-packet rows
python3 outreach/visual_cold_open/run_batch.py --visual-cold-open --sample-only \
  --source batch32-approval-packet \
  --approval-packet ~/.motionx-outreach/reports/batch32_candidate_approval_packet_2026-07-08_0842.md \
  --candidate-csv ~/.motionx-outreach/reports/batch32_sourcing_candidates_2026-07-07_2134.csv \
  --limit 3 --generate-images-in-dry-run --batch-id batch32_vco_samples

# tests (all mocked; no real API)
for t in image_client brief_prompt mime gmail_draft report cli sample; do
  python3 outreach/tests/test_visual_$t.py; done
```

### Sample-only mode
`--sample-only` ingests the batch32 **approval packet** (the APPROVE/MAYBE decision +
rank) joined with the **sourcing CSV** (verified observation + motion angle), selects
the top-N **APPROVE** rows by rank (N capped at `MAX_SAMPLE_DRAFTS` = 3; MAYBE used only
as a fallback when too few APPROVE rows exist), and writes a short founder-to-founder
note per candidate. It never guesses a recipient: a candidate with only a public contact
*page* (no verified email) blocks the live-draft path (`BLOCKED_ON_RECIPIENT_UNVERIFIED`)
and a local preview is written instead. Blocked-image runs still emit the brief + prompt
+ preview (`BLOCKED_ON_GPT_IMAGE_2_ACCESS`). Section-12 report:
`~/.motionx-outreach/reports/batch32_vco_sample_run_<YYYY-MM-DD_HHMM>.{csv,md}`.
