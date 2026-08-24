# MOTIONX — Studio Website & Outreach Engine

[![Next.js](https://img.shields.io/badge/Next.js-App_Router-000)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-3178C6)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v4-38BDF8)](https://tailwindcss.com)
[![Playwright](https://img.shields.io/badge/e2e-Playwright-2EAD33)](https://playwright.dev)
[![Tests](https://img.shields.io/badge/outreach_suite-10%2F10_passing-brightgreen)](outreach/tests)

**Live site:** https://madebymotionx.com · **Founder:** Chunyu (Charles) Dai

Two systems in one repository:

1. **A production marketing site** — Next.js App Router, TypeScript, Tailwind v4,
   CSS-only animation (no animation library), deployed on Vercel. 46 TS/TSX
   modules, Playwright end-to-end coverage, no backend required for the contact flow.
2. **An agentic outreach engine** (`outreach/`) — 40 Python modules that research a
   prospect, draft a single cold email, and refuse to send it unless it clears a
   deterministic gate stack. 10 test modules, all passing.

### Why the outreach engine is the interesting part

It is built around the assumption that the language model will occasionally produce
something confident and wrong, and that a human should never have to catch it manually:

- **`preflight.py` is a hard gate, not a linter.** Every draft must pass a central
  validator returning `PASS`/`FAIL` plus failure codes — word-count and one-offer
  limits, URL canonicalisation, a medical/regulated-claim guard, an
  AI-and-literary-language gate, and a diagnosis-ratio rule that forces most of the
  email to be the idea rather than the critique.
- **Recipient-certainty engine.** Addressing a person by first name on a shared
  `info@`/`support@` mailbox is a failure condition unless the research packet
  justifies it.
- **Read-back integrity.** After a draft is created, the stored plaintext is read
  back from Gmail and re-checked, because the transport layer can silently rewrite
  links.
- **State-transition protection.** The drafting path is structurally incapable of
  writing `sent`, `contacted`, or `follow_up`. Sending is a separate, human decision.
- **Caps that cannot be argued with.** Max drafts per run, one follow-up maximum,
  a 90-day same-domain rule, and a suppression list.

CRM records and credentials live outside the repository by design; the engine reads
them from `~/.motionx-outreach/` and the test suite runs entirely on fixtures.

> **Note on this repository.** This is a curated public snapshot of a private working
> repository. All prospect identities in the outreach fixtures, runbooks and tests have
> been replaced with fictional companies on the reserved `.example` TLD, so nothing here
> resolves to a real business or mailbox. Behaviour is unchanged.

---

A premium, cinematic website for **MOTIONX**, a **motion-first creative studio**:
we create the product film **and** build the motion-first website, launch page,
and campaign system where it lives. Built with Next.js (App Router), TypeScript,
Tailwind CSS v4, and CSS-only animation (no animation library). Deployable to Vercel as-is.

The homepage is intentionally edited for a fast read: thesis → selected proof →
connected system → services → pilot bridge → process → trust → inquiry. Each
section has a clear primary hierarchy; deeper scope and concept notes live on the
dedicated routes or in native disclosures. The desktop header and mobile menu keep
three primary choices, while the footer keeps the complete site index.

> **Founder:** Charles Dai · **Availability:** Available Worldwide
> **Offer:** Product Films · Motion-First Websites · Product Launch Pages · Campaign Content Systems

---

## Requirements

- **Node.js 22** (pinned in `.nvmrc`) and npm.
- **`ffprobe`** — required by the asset-integrity check and full quality gate.
- Optional: **`ffmpeg`** — needed only when regenerating videos, posters, or social cards.

> This machine had no system Node/ffmpeg, so they were installed into an isolated
> conda environment named `motionx`. If `node` isn't on your `PATH`, activate it:
> ```bash
> conda activate motionx        # or: export PATH="/opt/anaconda3/envs/motionx/bin:$PATH"
> ```
> A standard Node 22 install works equally well.

## Install

```bash
npm install
```

## Run the site locally

```bash
npm run dev -- -p 3939
```

Then open **http://localhost:3939**.

### Launch command used during development

```bash
export PATH="/opt/anaconda3/envs/motionx/bin:$PATH"   # only if Node isn't already on PATH
cd ~/Desktop/MotionX
npm run dev -- -p 3939
```

## Build for production

```bash
npm run build      # optimized, statically-prerendered build
npm run start      # serve the production build locally
```

Other checks:

```bash
npm run content:check  # source-level honesty/concept/public-contact guard
npm run assets:check   # video master/derivative/poster/OG asset guard
npm run seo:check      # route metadata/schema sanity guard
npm run metadata:check # built canonical/social/JSON-LD guard
npm run privacy:check  # built browser-artifact private-address guard
npm run browser:verify # browser screenshots + console/overflow/reduced-motion pass
npm run typecheck  # tsc --noEmit
npm run lint       # eslint (next/core-web-vitals + next/typescript)
npm run test:e2e   # Playwright browser tests (functional, no pixel diffing)
npm run gate       # content → assets → SEO → types/lint → build → metadata/privacy → e2e
```

### Browser tests (Playwright)

`npm run test:e2e` runs the end-to-end suite in `e2e/` against a server on **port
3939** — it auto-starts one (`next dev`) and reuses a running one. Browsers are
installed once with `npx playwright install chromium webkit` (cached outside the
repo). Coverage: routes/status (including `/system-study`), a three-link primary
desktop/mobile menu plus the complete five-link footer, canonical case-study links +
native disclosures, AURA principle controls and
no-JavaScript readability, pilot→contact preselection + paired totals, contact validation +
Gmail-compose-to-`hello@` + no false "sent" state, normal vs pilot inquiry subjects,
concept-label/private-address integrity, copy-email, **no horizontal overflow at
375/390/430**, reduced-motion/Save-Data media behavior, and the hero poster→play
behaviour. Tests are **functional only** (no
screenshot diffing — portfolio video frames would make snapshots flaky). Point the
suite at any origin with `PLAYWRIGHT_BASE_URL=…` (e.g. a production `next start`, or
`https://madebymotionx.com`); set `MOTIONX_NODE` to override the Node path used to
start the dev server. The local **preview** server (`.claude/launch.json`) also runs
on port 3939.

> ⚠️ Don't run `npm run build` while `npm run dev` is running — the build rewrites
> `.next/` and can break the live dev server. Stop dev first, or `rm -rf .next`
> afterwards.

### Content-integrity guard

`npm run content:check` scans the source for MOTIONX-specific public-trust rules:
concept labels/disclosures on every project, public `hello@` contact, no private
backup email or founder direct address in source/built browser artifacts, no placeholder
social links, no unsupported proof phrases, visible concept-study notes, and no
unsupported medical/health claims. The full `npm run gate` runs it before asset
integrity, SEO sanity, typecheck, lint, build, built-output metadata/privacy checks,
and e2e.

### Asset and SEO guards

`npm run assets:check` fingerprints the immutable root `hf_2026…*.mp4` masters,
proves public videos are derivatives, validates exact video/audio stream contracts
with `ffprobe`, requires fast-start MP4 layout, parses social cards as genuine
1200×630 JPEGs, checks source-visible media references, and enforces local size
budgets. In a clean CI clone, only the absent gitignored masters are explicitly
skipped; every public-asset contract still runs. See `docs/asset-integrity.md`.

`npm run seo:check` verifies route metadata/schema basics, expected sitemap/robots
expressions, JSON-LD escaping, and absence of unsupported schema fields such as
address, phone, awards, reviews, ratings, employee count, and fake social profiles.

### Browser verification pass

For visual or behavioral changes, run a local server on port 3939, then run
`npm run browser:verify`. It exercises every public route at 1440, 1280, 1024, 768,
430, 390, and 375 pixels; captures desktop/mobile and full-page evidence for
every public route under
`test-results/browser-verify/`; and writes a machine-readable `evidence.json`.
The pass checks console/page errors, horizontal overflow, responsive nav state,
reduced-motion and Save-Data poster-only behavior, normal/pilot contact subjects,
and explicit video playback.

### Continuous quality (no deploy)

`.github/workflows/website-quality.yml` always runs the same production gate on
pull requests and pushes to `main` using Node 22, `ffprobe`, Chromium, and WebKit.
It has read-only repository permission, uses no secrets, performs no deployment,
and uploads the HTML Playwright report and diagnostics when available.

## Site URL / domain (no domain hard-coded)

The site does **not** assume a domain exists. The base URL comes from an
environment variable with a localhost fallback:

```
NEXT_PUBLIC_SITE_URL   (e.g. https://your-domain.com)   →  defaults to http://localhost:3000
```

It feeds `metadataBase`, canonical URLs, Open Graph URLs, JSON-LD, `robots.txt`,
and `sitemap.xml` (see `src/content/site.ts` → `url`).

- **Local:** nothing to do — it falls back to `http://localhost:3000`.
- **Vercel:** add `NEXT_PUBLIC_SITE_URL` in Project → Settings → Environment
  Variables (e.g. `https://motionx.vercel.app` or your custom domain), then redeploy.

## Deploy to Vercel

1. Push this folder to a Git repo (GitHub/GitLab/Bitbucket).
2. Import the repo at [vercel.com/new](https://vercel.com/new) — the **Next.js**
   preset is auto-detected; no config needed.
3. (Recommended) set `NEXT_PUBLIC_SITE_URL` to your deployed URL. Deploy.

---

## Where things live

```
public/
  videos/   agentic-trading-hero.<hash>.mp4  ← silent, claim-light hero teaser
            renewal-botanical.<hash>.mp4 · liquid-signal.<hash>.mp4 ·
            furia.<hash>.mp4 · agentic-trading.<hash>.mp4
                            (web-ready case-study copies; the FURIA copy is cut with the
                             wordmark-removal step — see docs/asset-integrity.md)
            *-mobile.<hash>.mp4   ← smaller ladder variants for ≤767px viewports
                            (re-encoded from the web copies; see docs/asset-integrity.md)
  captions/ <name>.<hash>.en.vtt
  posters/  <name>.<hash>.webp
  images/   work/agentic-trading/strategy-board-{1920,960}.<hash>.webp
            ← responsive concept-art stills; exact source hashes/recipes are documented
  og/       og-image.jpg · renewal.jpg · liquid-signal.jpg · furia.jpg · agentic-trading.jpg · system-study.jpg
src/
  app/         layout.tsx · page.tsx · globals.css · robots.ts · sitemap.ts
               error.tsx (branded runtime recovery)
    system-study/  expanded AURA concept proof route
    work/[slug]/   project detail pages (SSG)
  components/  navigation, hero (server shell) + hero-reel (client island),
               studio-intro, launch-system, selected-work + selected-work-edit-bay,
               video-player, services, process, studio-section,
               contact-section (server shell) + contact-form / copy-email-button
               (client islands), contact-type-link, start-project-link, footer, …
  content/     site.ts · contact.ts · interface.ts · projects.ts · services.ts ·
               pilot.ts · system-study.ts
               ← EDIT CONTENT HERE
  hooks/       use-in-view-video.ts · use-reduced-motion.ts ·
               use-video-autoplay-policy.ts
  lib/         utilities.ts   (mail links, clipboard, contact scrolling + intent sync)
```

The **original camera files** are preserved untouched in the project root
(`hf_2026…*.mp4`). Everything under `public/videos/` is a derivative. Nothing in
this project deletes, renames, or recompresses the originals.

---

## Common edits

### Change the contact email
`src/content/site.ts` → `contact.email` is the **public** address
(`hello@madebymotionx.com`, a Google Workspace alias). It drives the contact form
(Gmail compose + mailto), the copy buttons, the footer, and JSON-LD.
The founder's direct address and the personal backup Gmail address are
**operational documentation only (CLAUDE.md)** — they must never appear in `src/`,
because website source is serialized into public build artifacts. `npm run
content:check` scans the source tree and `npm run privacy:check` scans the built
`.next` browser artifacts (the gate runs both).

### Edit pilot pricing / offers
**All offer copy and prices live in `src/content/pilot.ts`.** The `/pilot` page
(`src/app/pilot/page.tsx`) and the home-page `PilotCallout` both read from it —
edit prices in one place. Each offer's `formType` must match a contact-form
project-type option so a pilot CTA can pre-select it. This applies to base offers;
the Campaign Add-On is a referral-only scope with no fallback form type and never
appears in the general contact select. Pilot links are built by
`getPilotInquiryHref` as `/?type=…&pilot=<offer-id>#contact`; the explicit offer id
prevents general service links from accidentally inheriting pilot pricing. The
campaign add-on must first be paired with one base offer; its URL adds the single
marker `addon=campaign-add-on`, and the contact summary/Gmail brief preserve both
scopes. The selector derives the displayed base-plus-add-on total from the two
central price strings. Unknown, duplicate, mismatched, or standalone add-on markers
fail closed.

### Email authentication (Cloudflare DNS)
Status: **MX** → Google (`smtp.google.com`); **DKIM** → `google._domainkey` (active);
**SPF** → `v=spf1 include:_spf.google.com ~all`; **DMARC** → monitoring
(`p=none`, `rua=mailto:charles@madebymotionx.com`). To verify after changes:
```bash
dig +short TXT madebymotionx.com            # SPF
dig +short TXT _dmarc.madebymotionx.com     # DMARC
dig +short TXT google._domainkey.madebymotionx.com   # DKIM
dig +short MX madebymotionx.com             # Google MX
```
The `hello@` alias **exists** (alternate address on the `charles@` Workspace user).
The Gmail **display name** (`Charles Dai | MOTIONX`) and **signature**
(`outreach/signature.html`) are set in Gmail settings (not in code). Outreach
templates + the email-safe reel thumbnail live in `outreach/`.

### Edit company copy / navigation / CTAs / positioning
All reusable text lives in **`src/content/site.ts`** (hero, studio statement,
studio bio, closing CTA, footer). Services, the Launch System, and the process
steps live in `src/content/services.ts`; project copy in `src/content/projects.ts`.
Inquiry option values live in `src/content/contact.ts`; add a new service CTA value
there first so the form, services, projects, and pilot offers stay type-safe.
Primary and footer navigation sets live in `src/content/chrome.ts`; keep the header
focused and the footer complete.

### Add social links (none are shown by default)
`src/content/site.ts` → `social` is an **empty array** on purpose, so no
placeholder/`#` profiles are ever shown. Add a real profile only when it exists:

```ts
social: [{ label: "Instagram", href: "https://instagram.com/yourhandle" }]
  as ReadonlyArray<SocialLink>,
```

The footer and contact section render the social row **conditionally** (`hasSocial`)
— while the array is empty the row is removed cleanly with no empty heading.

### Replace a project / hero video
1. Render the replacement outside the immutable public roots (for example,
   `/tmp/motionx-video.mp4`) and review it there.
2. Compute its SHA-256, insert the first 12 hex characters before the extension,
   and move it into `public/videos/`. Never overwrite a published hashed URL.
3. Regenerate and hash its poster the same way (see below).
4. For case studies, update the entry in `src/content/projects.ts` (`video`,
   `poster`, `width`, `height`, `orientation`). For the hero, update the
   centralized paths in `src/content/media.ts`. Update the contracts in
   `scripts/asset-integrity.mjs`, then run `npm run assets:check`.

### Regenerate the hero teaser (needs ffmpeg)
The hero uses a short, muted Agentic Trading concept teaser while the complete
narrated film remains in Selected Work. To rebuild it, use the exact claim-safe
timings and widescreen/mobile recipes in `CLAUDE.md` → "Hero teaser". Then
refresh its claim-safe poster from the operator-supplied still. This crop
deliberately excludes the source image's `SCORE 0.84` label and baked timeline:

```bash
ffmpeg -y -i /Users/prince/Downloads/hero_final.png \
  -vf "crop=2560:1440:600:0,scale=1920:1080:flags=lanczos" \
  -frames:v 1 -c:v libwebp -quality 82 -compression_level 6 \
  /tmp/agentic-trading-hero.webp
ffmpeg -y -i /Users/prince/Downloads/hero_final.png \
  -vf "crop=978:1738:2300:0,scale=1080:1920:flags=lanczos" \
  -frames:v 1 -c:v libwebp -quality 82 -compression_level 6 \
  /tmp/agentic-trading-hero-mobile.webp
```

### Regenerate case-study posters (needs ffmpeg)
```bash
ffmpeg -y -ss 9  -i public/videos/liquid-signal.c24f676131a6.mp4     -frames:v 1 -c:v libwebp -quality 82 /tmp/liquid-signal.webp
ffmpeg -y -ss 13 -i public/videos/renewal-botanical.d503303f4c24.mp4 -frames:v 1 -c:v libwebp -quality 84 /tmp/renewal.webp
```

---

## Contact flow — how it works (no backend)

There is **no server backend**, and the UI never pretends a message was sent. The
section shell (`src/components/contact-section.tsx`) renders on the server; the
inquiry form itself (`src/components/contact-form.tsx`) is a focused client island
with a robust multi-path flow:

1. **Client-side validation** — name, a valid email, and a description are required.
   Company, budget, and timeline remain optional and collapse behind one disclosure
   on mobile. Trusted service/pilot links preselect the project type; pilot links also
   show the selected package summary. A campaign add-on is valid only when paired
   with an exact base Pilot package, and both scopes remain visible in the summary
   and prepared brief.
2. **Continue in Gmail** (primary) — builds a URL-encoded Gmail *compose* link
   addressed to `contact.email` (subject `MOTIONX Project Inquiry — …`, all fields
   in the body) and opens it by clicking a transient real
   `<a target="_blank" rel="noopener noreferrer">`. It does **not** use
   `window.open()` — that can return `null` even when the tab opens, which used to
   cause a false "Gmail didn't open" error. Only a thrown exception counts as failure.
   Status message: *"Your project brief is ready in Gmail. Review it and press Send
   to complete your inquiry."* — it never claims the message was sent.
3. **"Having trouble?" helper** — appears only *after* an attempt, presented as
   assistance (not an error), and is **dismissible**. It offers **Try Gmail again**,
   **Copy email**, **Copy prepared message**, and **Open default mail app**. The full
   brief is shown inline only on a genuine caught error. The helper resets on each new
   submit and on refresh (it's plain component state — the initial state is clean).
4. **Copy email address** — copies `contact.email` and shows a live-region
   confirmation (Clipboard API with a timeout + hidden-textarea fallback).
5. **Open default mail app** — a clearly-labelled `mailto:` fallback available before
   the Gmail attempt and again in the helper. The email is also rendered as selectable text.

Every "Start a Project" CTA (hero + nav) only smooth-scrolls to the contact
section and moves focus to its heading — it never opens email or submits the form,
and it preserves query parameters such as attribution or project preselection.

### Connecting a real backend later (optional)

The form is structured so you can add real delivery without exposing secrets.
In `onSubmit` (contact-form.tsx), after `buildMessage()`, `POST` the fields
instead of (or in addition to) opening Gmail:

- **Formspree / Basin** — `fetch("https://formspree.io/f/XXXX", { method: "POST",
  headers: { Accept: "application/json", "Content-Type": "application/json" },
  body: JSON.stringify(fields) })`.
- **Resend (recommended, own backend)** — create `src/app/api/contact/route.ts`
  (a Next.js Route Handler) or a Server Action that calls the Resend SDK with
  `RESEND_API_KEY` from a **server-side** env var (never `NEXT_PUBLIC_`), then
  `fetch("/api/contact", …)` from the form. Only show a success state once that
  request actually resolves `200`.

Keep the Gmail/mailto paths as graceful fallbacks.

---

## Asset optimization performed

- A bespoke **Agentic Trading hero teaser** uses three approved claim-light
  mascot/research/resolved beats, separate widescreen and vertical reframes,
  crossfades, no audio, and faststart delivery (2.22 MB / 0.89 MB). Numeric
  trade-plan frames and the fictional-product end card are excluded.
- Web-ready case-study copies sit in `public/videos/`. Originals were
  **not** modified or recompressed.
- Replaceable videos, posters, editorial images, and captions use content-hashed
  URLs and a one-year immutable cache policy. `npm run assets:check` verifies
  both the filename hashes and the narrowly scoped `vercel.json` headers;
  Open Graph cards keep their stable names and existing cache behavior.
- Posters and editorial stills are deterministic **WebP** derivatives (video
  frames except the supplied-and-cropped Agentic hero/artwork sources). Social
  share cards are separate 1200×630 **JPEG** files for crawler compatibility.
- Aspect ratios are declared on every media frame to prevent layout shift.

## Accessibility & performance notes

- Keyboard-accessible nav, video controls, and Selected Work index with separate
  preview buttons and canonical case-study links plus URL/history restoration.
  Its mobile cue sheet uses one compact row per project; the desktop index remains
  sticky beside one media stage. Case routes include keyboard-sized return links,
  a compact anchor index, native disclosures for secondary metadata/notes, and a
  concept-labelled visual Up Next path. AURA's three reasoning controls expose one
  visual principle at a time with `aria-pressed`. The mobile menu retains its focus trap,
  Escape-to-close, destination-heading focus, and body-scroll lock/restore. CTAs
  move focus to the contact heading.
- `prefers-reduced-motion` respected throughout (no decorative autoplay; CSS
  entrances and progress motion collapse to the final state).
- Videos use `playsInline`, muted autoplay only, and pause when offscreen or when
  the tab is hidden. Portfolio clips begin poster-first with `preload="none"` until
  preferences are known; normal visitors then get in-view autoplay and metadata
  preload, while reduced-motion and Save-Data visitors remain paused until they use
  the explicit play control. The **hero teaser is
  `preload="none"` with a poster-first first paint** — the ~2.2 MB mp4 is never on the
  critical path and only loads (on play) after mount for visitors who aren't on a
  data-saver connection and don't prefer reduced motion; otherwise the poster is the
  static fallback. The hero teaser has no audio track, so it carries a play/pause
  control only.
- Core marketing copy is server-visible without waiting for Motion hydration; the
  E2E suite includes a JavaScript-disabled readability check. Motion is reserved for
  meaningful media/process state (see `CLAUDE.md` → Animation conventions).
- SEO & icons: title/description, Open Graph + Twitter cards, JSON-LD, `robots.txt`,
  `sitemap.xml` (all using `NEXT_PUBLIC_SITE_URL`), an SVG monogram favicon
  (`src/app/icon.svg`), plus a rasterized `favicon.ico` and 180×180 `apple-icon.png`
  for legacy browsers and iOS home-screen.
