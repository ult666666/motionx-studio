---
description: Safe live-credential setup assistant for MOTIONX outreach - no drafts, no sends, no images
allowed-tools: Bash(python3 outreach/agentic_ops/run.py credentials-setup*), Read
---

# MOTIONX credentials setup

Run the safe agentic-ops credentials setup assistant.

## Verify only
```bash
python3 outreach/agentic_ops/run.py credentials-setup --verify-only
```

## Charles local setup
- OpenAI key: Charles runs `--interactive --write-openai-key`; input is hidden and written only to `~/.motionx-outreach/secrets.env`.
- Gmail OAuth: place Desktop App credentials at `~/.motionx-outreach/gmail_credentials.json`, then run `--setup-gmail-oauth`.

## Safety rules
- Do NOT paste real secrets into chat.
- Do NOT print token/key contents.
- Do NOT create/update Gmail drafts, send, schedule, generate images, run full batch32, or mutate CRM.
- Outputs stay under `~/.motionx-outreach/`.
