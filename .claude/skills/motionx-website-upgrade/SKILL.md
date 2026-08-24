---
name: motionx-website-upgrade
description: Central workflow for improving the MOTIONX website. Use when designing, redesigning, reviewing, auditing, testing, or improving any part of the MOTIONX Next.js site (pages, sections, components, layout, typography, motion, accessibility, performance). Routes work through frontend-design, ui-ux-pro-max, react-best-practices, web-design-guidelines, and webapp-testing while preserving the established MOTIONX design system. Does NOT cover the motionx-outreach skill, CRM, email/DNS, or deployment.
---

# MOTIONX Website Upgrade — Router Workflow

The single workflow for MOTIONX **website** improvements. It sequences the installed
website-development skills so design intent, implementation quality, guideline
compliance, and real browser verification all happen — in order — without losing the
studio's established visual identity.

**Scope:** the Next.js site only (`src/`, `public/`, content in `src/content/*`).
**Out of scope (do not touch under this skill):** the `motionx-outreach` skill, the
outreach CRM (`~/.motionx-outreach/`), Gmail, Cloudflare/DNS, Vercel deploys, pricing,
public business claims, and production secrets — unless the user *explicitly* asks.
Do not stage, commit, reset, stash, clean, delete, or overwrite unrelated dirty files
such as `outreach/self-improvement.md`.

**Golden rule:** existing MOTIONX decisions in `CLAUDE.md` and `src/content/*` override
every generic recommendation from any skill below. Skills are advisors, not authorities.

---

## Step 1 — Understand (always first)
- Read `CLAUDE.md` end-to-end (positioning, section order, visual rules, animation/video
  rules, content-integrity rules, gotchas).
- Inspect the design system and content: `src/app/globals.css` (`@theme` tokens),
  `src/content/site.ts`, `src/content/projects.ts`, `src/content/services.ts`,
  `src/content/pilot.ts`, and the relevant `src/components/*`.
- State the **business goal** of the requested change in one sentence.
- Preserve the established MOTIONX identity (dark/futuristic first; electric-blue accent;
  Geist type; cinematic, restrained motion). **Do not auto-redesign the whole site** —
  scope to what was asked.

## Step 2 — Design
- Use **`frontend-design`** for intentional visual direction: hierarchy, typography,
  layout, spacing, motion character, and distinctive (non-templated) implementation.
- Use **`ui-ux-pro-max`** *only as a design-reference system* — query it for patterns,
  palettes, product-type reasoning, and UX guidelines
  (`python3 .claude/skills/ui-ux-pro-max/scripts/search.py "<query>"`). Treat output as a
  menu, not a mandate; do not blindly apply every recommendation, and never run its
  generator (`design_system.py --persist`) against the site.
- Reconcile against the MOTIONX system: reject anything that fights the palette, the
  restraint rules (no glassmorphism pile-ups / gradient blobs / floating-card soup), or
  the proof-before-explanation section order. **MOTIONX overrides generic advice.**

## Step 3 — Implement
- Work within the existing Next.js 15 / React 19 / Tailwind v4 architecture. Keep editable
  copy/config in `src/content/*`; add design tokens in `@theme` in `globals.css` (no JS
  Tailwind config).
- Use **`react-best-practices`** for React/Next.js structure and performance decisions
  (rendering, re-renders, data fetching, bundle, hydration).
- Avoid unnecessary dependencies and generic component-library aesthetics. Match the
  surrounding code's idioms, comment density, and naming.

## Step 4 — Audit
- Use **`web-design-guidelines`** to review the changed UI for: accessibility, keyboard
  support, focus states, forms, touch targets/interactions, responsive layout, motion
  preferences (`prefers-reduced-motion`), image handling, typography, navigation/active
  state, and performance-related UI issues.

## Step 5 — Run & visually verify (never skip for visible changes)
- Use **`webapp-testing`** (Playwright) — or the harness `preview_*` tools — to actually
  exercise the site. Dev server runs on **port 3939** (`.claude/launch.json`,
  conda env `motionx`): `next dev -p 3939`.
- Open the real affected pages (`/`, `/work/[slug]`, `/pilot`) and:
  - Capture **desktop and mobile** screenshots (before/after for significant visual change).
  - Test navigation and the contact form flow (it must never claim "message sent").
  - Check the browser **console** for errors/hydration warnings.
  - Check for **horizontal overflow** at mobile widths.
  - Verify **reduced-motion** behavior (transforms collapse to fades).
  - Confirm animations, the hero reel, and portfolio videos still play.
- **Do not claim success from typecheck/lint/build alone.** Visual proof is required.

## Step 6 — Quality gate (before declaring done)
```bash
npm run gate   # content:check → assets:check → seo:check → typecheck → lint → build → e2e
```
- Do not run `next build` while `next dev` is live (corrupts `.next`; fix with
  `rm -rf .next` + restart dev). The gate script guards this automatically.
- Then re-verify the affected pages in the browser. For significant visual changes,
  produce **before/after notes + screenshots**.

## Step 7 — Production safety
- **Do not deploy** automatically. Only deploy if the user explicitly asks.
- Do not alter domain, DNS, email, outreach automation, pricing, public business claims,
  or production secrets unless specifically requested.
- Honor MOTIONX content-integrity rules: no fabricated clients/testimonials/metrics, no
  invented location/domain/social, projects stay labelled "concept".

---

## Known pitfalls (each of these shipped as a real bug — check them, don't rediscover them)

1. **Reduced-motion hydration.** Anything rendered in the server HTML must NOT
   branch its markup on `motion/react`'s `useReducedMotion` (it resolves the real
   preference on the first client paint). The intro loader did `return null` on the
   reduced flag and left reduced-motion visitors a permanent full-screen overlay.
   Use `@/hooks/use-reduced-motion` (false on server + first render) and express
   reduced motion through `transition` only.
2. **Occlusion is invisible to `toBeVisible()`.** A stale full-screen layer passes
   every visibility assertion. Verify interactivity with `click({ trial: true })`
   or `document.elementFromPoint` — the e2e suite's reduced-motion test now does this.
3. **Next metadata shallow-merge.** A page-level `openGraph`/`twitter` object
   REPLACES the layout's — restate `images`, `siteName`, `type` or the page silently
   loses its share card (/pilot did).
4. **Share cards are JPEG, 1200×630, in `public/og/`** — WebP previews don't render
   on LinkedIn/WhatsApp. The Renewal card may only use ginkgo frames (~0–1.6s,
   center-band crop) — never the third-party pharma packaging or its captions.
5. **Video web copies:** re-encode from the `hf_` masters with the CRF-23 envelope in
   CLAUDE.md; portfolio films must keep their AAC audio (`-c:a copy` — `-an` silently
   breaks the mute toggle), only the hero reel is silent. Never ship a raw master.
6. **WebKit doesn't focus `<button>` on mouse click** — test focus-restore contracts
   with keyboard activation (`.focus()` + `press("Enter")`) so they hold cross-engine.
7. **Copy lives in `src/content/*`.** If a component hard-codes a sentence that also
   exists in a content file, the content file is dead and the copies WILL drift
   (the pilot callout drifted into a false scarcity claim this way).

### Skill quick-reference
| Need | Skill |
|------|-------|
| Visual direction, typography, distinctive design | `frontend-design` |
| Pattern/palette/UX reference database | `ui-ux-pro-max` (reference only) |
| React/Next.js implementation & performance | `react-best-practices` |
| Accessibility / UX guideline audit | `web-design-guidelines` |
| Real browser run, screenshots, console, overflow | `webapp-testing` |

The `motionx-outreach` skill is unrelated to this workflow and must not be modified here.
