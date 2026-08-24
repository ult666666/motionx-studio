# MOTIONX — Website-Development Skill Stack: Install Manifest

This file records the provenance and audit status of every Claude Code skill
installed at **project scope** (`.claude/skills/`) for MOTIONX website work.

- **Installed:** 2026-06-19
- **Branch:** `chore/install-website-skills`
- **Scope:** project-local only (NOT installed in `~/.claude/skills/`)
- **Audit workspace (temporary, outside repo, not committed):** `/tmp/motionx-skill-audit/`

> The pre-existing `motionx-outreach` skill is unrelated to website work and was
> **not** modified, renamed, or touched by this installation. It is intentionally
> omitted from the per-skill table below except for the note at the end.

No credentials, tokens, cookies, or private data are recorded in this file.

---

## Installed skills

### 1. frontend-design
- **Source repository:** https://github.com/anthropics/skills
- **Source type:** Anthropic (official)
- **Pinned commit:** `57546260929473d4e0d1c1bb75297be2fdfa1949` (default branch `main`, `--depth 1` clone)
- **Upstream path:** `skills/frontend-design`
- **Local path:** `.claude/skills/frontend-design/`
- **License:** Apache License 2.0 (`LICENSE.txt` included)
- **Executable scripts:** None (SKILL.md + LICENSE only)
- **Runtime dependencies:** None
- **Audit result:** PASS — guidance-only Markdown, no scripts, no network, no path issues.
- **Update procedure:** Re-clone the repo, diff `skills/frontend-design`, re-copy, bump the commit hash above.
- **Removal procedure:** `rm -rf .claude/skills/frontend-design/`.

### 2. webapp-testing
- **Source repository:** https://github.com/anthropics/skills
- **Source type:** Anthropic (official)
- **Pinned commit:** `57546260929473d4e0d1c1bb75297be2fdfa1949` (default branch `main`, `--depth 1` clone)
- **Upstream path:** `skills/webapp-testing`
- **Local path:** `.claude/skills/webapp-testing/`
- **License:** Apache License 2.0 (`LICENSE.txt` included)
- **Executable scripts:** Yes — `scripts/with_server.py` (starts a local dev server,
  polls `localhost` for readiness, runs a command, tears it down) and Python
  examples under `examples/`. Reviewed: no external network, no secret/home-dir access.
- **Runtime dependencies:** Python 3 + Playwright (`pip install playwright` and a
  browser via `playwright install`). Required only when actually running browser tests.
- **Audit result:** PASS — `subprocess`/`socket` usage is local dev-server orchestration only.
- **Update procedure:** Re-clone the repo, diff `skills/webapp-testing`, re-copy, bump the commit hash above.
- **Removal procedure:** `rm -rf .claude/skills/webapp-testing/`.

### 3. web-design-guidelines
- **Source repository:** https://github.com/vercel-labs/agent-skills
- **Source type:** Vercel (official, `vercel-labs`)
- **Pinned commit:** `f8a72b9603728bb92a217a879b7e62e43ad76c81` (default branch `main`, `--depth 1` clone)
- **Upstream path:** `skills/web-design-guidelines`
- **Local path:** `.claude/skills/web-design-guidelines/`
- **License:** Not declared per-skill; governed by the `vercel-labs/agent-skills` repo
  (sibling Vercel skills declare MIT). No separate LICENSE file shipped in the skill folder.
- **Executable scripts:** None (single `SKILL.md`, Web Interface Guidelines checklist).
- **Runtime dependencies:** None.
- **Audit result:** PASS — review checklist only, no scripts, no network.
- **Update procedure:** Re-clone the repo, diff `skills/web-design-guidelines`, re-copy, bump the commit hash.
- **Removal procedure:** `rm -rf .claude/skills/web-design-guidelines/`.

### 4. react-best-practices  (internal skill name: `vercel-react-best-practices`)
- **Source repository:** https://github.com/vercel-labs/agent-skills
- **Source type:** Vercel (official, `vercel-labs`)
- **Pinned commit:** `f8a72b9603728bb92a217a879b7e62e43ad76c81` (default branch `main`, `--depth 1` clone)
- **Upstream path:** `skills/react-best-practices`
- **Local path:** `.claude/skills/react-best-practices/`
- **License:** MIT (declared in SKILL.md frontmatter)
- **Executable scripts:** None — `SKILL.md` + `AGENTS.md` + `README.md` + `metadata.json`
  + ~50 Markdown rule files under `rules/`. All guidance content.
- **Runtime dependencies:** None.
- **Audit result:** PASS — Markdown rules only, no scripts, no network. All `rules/*.md`
  referenced by SKILL.md are present (verified).
- **Update procedure:** Re-clone the repo, diff `skills/react-best-practices`, re-copy, bump the commit hash.
- **Removal procedure:** `rm -rf .claude/skills/react-best-practices/`.

### 5. ui-ux-pro-max  (third-party — security-audited before install)
- **Source repository:** https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- **Source type:** Third-party (Next Level Builder)
- **Pinned release tag:** `v2.5.0` → commit `07f4ef3ac2568c25a3b0c8ef5165a86abc3e56e4`
  (latest stable tagged release; a pinned tag was used rather than a moving branch)
- **Upstream path:** `.claude/skills/ui-ux-pro-max` (SKILL.md) + `src/ui-ux-pro-max/{scripts,data}`
- **Local path:** `.claude/skills/ui-ux-pro-max/`
- **License:** MIT (Copyright (c) 2024 Next Level Builder; `LICENSE` included)
- **Executable scripts:** Yes — `scripts/search.py` (read-only CSV reference search,
  invoked by the SKILL.md), `scripts/core.py` (TF-IDF search engine), and
  `scripts/design_system.py` (token/markdown generator). `data/` holds CSV reference
  databases + a `_sync_all.py` maintenance helper.
- **Runtime dependencies:** Python 3 **standard library only** (no pip packages). Verified
  by import scan: `csv, re, pathlib, math, collections, argparse, sys, io, json, os, datetime`.
- **Audit result:** PASS (with one structural fix applied). Findings:
  - No npm `postinstall`/`preinstall` lifecycle scripts in the bundled CLI.
  - No telemetry/analytics; no reads of `.env`, SSH keys, keychain, browser profiles,
    Gmail, Cloudflare, Vercel, or any unrelated project/home-directory files.
  - The bundled `cli/` installer fetches GitHub release archives over the
    **unauthenticated** public GitHub API (no token reads). It was **NOT used** — the
    skill was copied directly from the pinned tag instead.
  - `search.py`/`core.py` are read-only. `design_system.py` can write files only when
    `persist=True`, which its CLI entrypoint never sets; it defaults to CWD with no path
    traversal. **No generator script was run against the MOTIONX site.** (`search.py`
    was run once with a harmless query only to validate self-containment.)
  - **Structural fix:** upstream ships `scripts/` and `data/` as relative *symlinks*
    into `src/ui-ux-pro-max/`. These were **dereferenced into real directories** on
    install so the skill is fully self-contained with **no broken symlinks**.
- **Update procedure:** Clone the repo, `git checkout <new stable tag>`, copy `SKILL.md`
  and dereference `src/ui-ux-pro-max/{scripts,data}` via `cp -RL` into the skill folder,
  then bump the tag/commit above. Do not introduce symlinks.
- **Removal procedure:** `rm -rf .claude/skills/ui-ux-pro-max/`.

### 6. motionx-website-upgrade  (local router skill — authored here, not from a repo)
- **Source:** Authored in-repo for MOTIONX (no external source).
- **Source type:** Local / first-party.
- **Local path:** `.claude/skills/motionx-website-upgrade/`
- **License:** N/A (project-internal).
- **Executable scripts:** None.
- **Runtime dependencies:** None (orchestrates the five skills above + project `npm` scripts).
- **Audit result:** N/A (authored locally).
- **Update procedure:** Edit `.claude/skills/motionx-website-upgrade/SKILL.md`.
- **Removal procedure:** `rm -rf .claude/skills/motionx-website-upgrade/`.

---

## Not modified
- `.claude/skills/motionx-outreach/` — the MOTIONX client-outreach skill. **Unrelated to
  website work; deliberately left untouched.** Do not edit it as part of website tasks.
