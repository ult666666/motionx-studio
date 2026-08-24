# Agentic-ops hook templates (NOT enabled)

These are **templates only**. Nothing here is wired into any `settings.json`. The
agentic-ops CLI does not need them — they are optional defense-in-depth that Charles
can enable later. Enabling them is a manual, explicit step.

## Files

- `agentic_ops_guard.py` — a stdlib-only Claude Code **PreToolUse** hook.
  - **Blocks** (exit 2): `git push`, `git reset --hard`, `git clean -fd`, `rm -rf`;
    Gmail send paths (`messages.send`, `drafts.send`, `messages.insert`, `gmail send`,
    `send_email`); secret exposure (literal `sk-…` keys, `refresh_token` / `client_secret`
    material, reading/committing `gmail_token.json` / `secrets.env` / `client_secret*.json`).
  - **Warns** (exit 0 + stderr): a generated report/asset pointed **inside** the repo
    instead of `~/.motionx-outreach/`; any command or edit that references
    `outreach/self-improvement.md`.
  - Fails **open** on unparseable input (`FAIL_OPEN = True`) so it can never brick a
    session. Flip to `False` to fail closed once trusted.
- `settings.hooks.template.json` — the `hooks` block to merge into a `settings.json`.
  It is deliberately **not** a usable config on its own (note the `_TEMPLATE_NOTICE` key
  and the `/ABSOLUTE/PATH/TO/...` placeholder).

## How to enable later (manual, explicit)

1. Read `agentic_ops_guard.py` and confirm you agree with every rule.
2. (Optional) Dry-run it by hand:
   ```bash
   echo '{"tool_name":"Bash","tool_input":{"command":"git push origin main"}}' \
     | python3 outreach/agentic_ops/hook_templates/agentic_ops_guard.py; echo "exit=$?"
   # -> BLOCK: git push is forbidden ...   exit=2
   ```
3. Copy the `hooks` object from `settings.hooks.template.json` into **project**
   `.claude/settings.json` (recommended — keeps it scoped to this repo) or, only if you
   really want it everywhere, `~/.claude/settings.json`.
4. Replace `/ABSOLUTE/PATH/TO/MotionX` with this repo's real absolute path.
5. Remove the `_TEMPLATE_NOTICE` / `_WHAT_IT_DOES` keys (they are documentation, not config).
6. Restart Claude Code (or re-open the project) so the hook is picked up.

## How to disable

Remove the `PreToolUse` entry you added from the `settings.json` you edited. No other
file references the guard, so deleting the entry fully disables it.

## Why this is not auto-enabled

Global hooks change behavior for every session and every project. The task that created
this layer explicitly must **not** modify global `~/.claude` settings or enable hooks
globally. So these ship as inert templates; enabling is Charles's call.
