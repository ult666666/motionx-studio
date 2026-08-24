# CLAUDE.md — MOTIONX project guide for future sessions

This file exists so future Claude Code sessions preserve the design quality and
content integrity of this site. Read it before making changes.

## What this is

A **motion-first creative studio** website (home page + proof and offer routes).
The four portfolio videos are the proof, but the studio's positioning is broader
than motion alone.

## Business positioning (keep this consistent everywhere)

MOTIONX is **not** "we make videos and also make websites." The positioning is:

> We create the moving visual world around a product — the cinematic product film —
> then **extend that same world into the website, launch page, and campaign system.**

One creative direction, delivered as connected outputs. This must be clear within
the first screen (hero: *"From first frame to final click."*) and stay consistent
across the **Launch System** section, Services, Process, and Studio copy.

Core offer (don't quietly narrow it back to motion-only): Product Films ·
Motion-First Websites · Product Launch Pages · Campaign Content Systems. "Creative
technology" is described as **methodology**, not a standalone client service.

Avoid clichés: "full-service agency", "360°/one-stop shop", "cutting-edge",
"disruptive", "we leverage", "guaranteed conversion/results".

## Section order (proof before explanation)

Hero → (01) Studio thesis → (02) Selected Work → **(03) MOTIONX System Study**
(the Launch System) → (04) Services → unnumbered Pilot Callout → (05) Process →
(06) Studio → (07) Contact → Footer. Promise → proof → integrated offer → offer
bridge → process → trust → inquiry. If you add or reorder sections, keep the
`(0n) —` eyebrow numbers in sync.

Keep the homepage as a concise edit, not a second version of every detail route:
one idea, one proof layer, and one clear action hierarchy per section. The desktop
header and mobile menu expose only Work, Services, and Pilot; the footer preserves
the complete five-destination index. Scope lists and concept notes use native
disclosures where their detail is useful but not part of the first reading path.

The Launch System is a **concept "System Study"**: one self-owned visual language
(a CSS chrome object + electric blue/magenta + ivory type) shown across a film
frame, a real HTML/CSS mini launch page ("AURA", clearly a concept), and campaign
formats. It is all CSS/SVG — no videos, no third-party product — labelled
"MOTIONX System Study · Concept". The homepage summary links to `/system-study`,
using one primary route action; `/system-study` expands the same self-owned study
into a responsive prototype and breakdown.
That route must keep the visible no-client/no-results disclosure and its compact
reasoning strip: **Focal hierarchy · Responsive translation · Single-action path**.
The three annotations are accessible `aria-pressed` controls that reveal one
composition principle at a time; the interaction uses restrained opacity/transform
changes, has a static reduced-motion state, and never claims a conversion result.
Don't reintroduce the Renewal/pharma packaging or Liquid Signal frames here.

## Stack & architecture

- **Next.js 15 (App Router) + React 19 + TypeScript**, strict mode.
- **Tailwind CSS v4** — theme tokens are defined in `src/app/globals.css` via
  `@theme { … }` (CSS-first; there is no `tailwind.config.js`).
- **Animation is CSS-only.** There is no animation library — the `motion`
  package was removed once the last `motion/react` import went away (it had sat
  in `package.json` unused, reinstalled on every CI run). Entrances, reveals,
  the process playhead and scroll-linked progress are keyframes and view
  timelines in `globals.css`; see "Animation conventions" below. Don't add a
  library back without a reason CSS genuinely cannot cover.
- **Fonts:** `geist` package (Geist Sans + Geist Mono) wired through `next/font`
  in `layout.tsx`. Local, no network fetch. Mono is used for uppercase metadata
  labels (`.label`), Sans for everything else (`.display` for headlines).
- Static export-friendly: the build prerenders all routes (`/`, `/pilot`,
  `/system-study`, `/work/[slug]`, robots, sitemap).

### File map
- `src/content/` — **the only place to edit copy/config.** `site.ts` (brand,
  contact, nav, all reusable copy), `chrome.ts` (the client-safe subset — brand
  name, concise primary nav, complete footer nav, primary CTA label, footer tagline,
  availability — imported by
  always-hydrated client UI; `site.ts` re-composes it so server code reads one
  surface), `contact.ts` (typed project/budget/timeline
  options), `projects.ts` (case studies), `services.ts` (services + `launchSystem`
  + `processSteps`), `pilot.ts` (pilot offers), `system-study.ts`
  (the AURA concept proof route), and `interface.ts` (404/runtime-error copy).
- `src/components/` — one component per section (incl. `launch-system`) + reusable
  `video-player`, `selected-work-edit-bay`, `reveal` (server-first structural
  wrappers), and `logotype`. Sections stay server-rendered with small
  client islands: `hero` is a server shell over the `hero-reel` island (video +
  play/pause), `contact-section` is a server shell over the `contact-form` island
  (all form state/pilot/Gmail logic) + `copy-email-button` (self-contained copy +
  live region), and contextual CTAs use `contact-type-link` /
  `start-project-link`. Don't fold static section copy back into a client island.
- `src/hooks/` — `use-in-view-video` (visibility-driven playback),
  `use-reduced-motion`, and `use-video-autoplay-policy` (reduced-motion/Save-Data gate).
- `src/lib/utilities.ts` — `cn`, `mailto`, `gmailComposeUrl`, `copyToClipboard`
  (Clipboard API + timeout + textarea fallback), `scrollToContact` (focus-aware),
  and `navigateToContactWithType` (same-route contextual CTA synchronization).

### Live deployment
- **Live:** https://madebymotionx.com (Vercel team `motion-x-creative`, project `motionx`).
  `www` → same project. SSL via Let's Encrypt. DNS on Cloudflare (A `@` → 76.76.21.21,
  CNAME `www` → cname.vercel-dns.com, both **DNS-only / grey cloud**).
- `NEXT_PUBLIC_SITE_URL=https://madebymotionx.com` is set in Vercel (Production).
- **Deploys are triggered by pushing `main` to GitHub** (Vercel git integration;
  `deploy.sh` wraps the CLI as a fallback). Security headers (nosniff, X-Frame-Options
  DENY, Referrer-Policy, Permissions-Policy, Content-Security-Policy) live in
  `vercel.json`. The CSP is self-only with `'unsafe-inline'` script/style (required by
  Next's inline bootstrap/flight scripts, the JSON-LD block, and Motion's inline
  styles; static export can't use nonces) + `img-src data:` for the grain texture.
  **If you tighten or extend the CSP, re-test it before shipping**: build + `next
  start`, inject the header via Playwright route interception, and exercise every
  route AND the contact→Gmail flow, Selected Work edit-bay, and mobile menu watching the console for
  "Refused to …" violations. vercel.json headers do NOT apply on `next dev`.

### Site URL & contact (no invented domain / no placeholder profiles)
- `site.url` = `new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").origin`
  — normalized to a clean origin so trailing slashes can't double path separators.
  Never hard-code a domain in application code. It feeds metadataBase, canonical, OG,
  JSON-LD, robots, sitemap. The CI gate fails closed unless the env var is exactly
  `https://madebymotionx.com` (that expectation is hard-coded in `scripts/gate.mjs`
  as an independent verification contract), and `scripts/metadata-guard.mjs`
  validates the built HTML/sitemap/robots against the configured origin.
- **`site.contact.email` is the PUBLIC address: `hello@madebymotionx.com`** (a Google
  Workspace alias forwarding to the founder mailbox). It drives the contact form,
  footer, JSON-LD, Gmail compose and mailto.
- **The founder's direct address `charles@madebymotionx.com` must NOT appear anywhere
  in website source (`src/`)** — anything there can be serialized into public build
  artifacts (it once shipped inside a shared browser chunk via a client import of the
  `site` object). It is operational documentation only (this file + `/outreach`), used
  for outreach and DMARC `rua`. Enforcement: `content:check` scans every `src/` file,
  and `scripts/privacy-guard.mjs` scans the built `.next` browser artifacts after
  every gate build.
- Never publicly display the personal backup `daichunyu666@gmail.com` (same guards).
- **Client components must not import the full `site` object.** Always-hydrated UI
  (navigation, error boundary) reads the narrow client-safe `src/content/chrome.ts`;
  islands like the contact form receive public values (e.g. the email) as serialized
  props from their server shells. `site.ts` composes the chrome values back into the
  central `site` surface, so server code still has one place to read.
- `site.social` is an **empty array** by design. UI renders it conditionally via
  `hasSocial`; never add `#`, "coming soon", or fake profiles. No location/"Based"
  field exists — only `availability: "Available Worldwide"`.

### Pilot launch
- **Offer prices live in `src/content/pilot.ts`** (single source) — edit there; the
  `/pilot` page (`src/app/pilot/page.tsx`) and the home `PilotCallout` read from it.
- Pilot CTAs use `getPilotInquiryHref` and link to
  `/?type=<formType>&pilot=<offerId>#contact`; `ContactSection` reads both values,
  pre-selects the matching project type, and shows the selected package summary. Each
  base offer's `formType` MUST match a contact form option; the add-on has no fallback
  `formType`. Removing/changing the referral must clear stale pilot context. Contact subject is
  `MOTIONX Pilot Project Inquiry — <who> · <type>`.
- The Campaign Content Add-On is never a standalone pilot. Its selector first
  requires one valid base offer, then emits the exact paired URL
  `/?type=<baseFormType>&pilot=<baseOfferId>&addon=campaign-add-on#contact`.
  The selector derives the exact combined total from the two centralized pilot prices;
  Contact shows and writes both scopes into the prepared Gmail brief. Unknown,
  duplicate, mismatched, or unpaired add-on markers fail closed to a normal inquiry.
- Keep pricing honest: no fake countdowns/scarcity/clients/metrics. Disclaimer
  ("introductory; final scope may affect the quote") must stay.
- The `/pilot` comparison is a restrained **production slate**, not a SaaS pricing
  card grid. `Film + Website Launch System` is marked "Signature engagement" via
  spacing, a tonal field, and one accent edge — never "Best Value", fake urgency,
  or a countdown. Each package leads with its core deliverable; the route keeps only
  the exclusions, next steps, and terms that are not already stated by those package
  rows. Original/pilot prices are operator-set facts; do not change them during
  design work.

### Email authentication (Cloudflare DNS)
- MX → `smtp.google.com` (Google Workspace). DKIM → `google._domainkey` TXT (active).
- SPF → `v=spf1 include:_spf.google.com ~all` (single record). DMARC → `_dmarc` TXT
  `v=DMARC1; p=none; rua=mailto:charles@madebymotionx.com; adkim=s; aspf=s; pct=100`
  (monitoring; do not jump to `p=reject` until all senders verified).
- The `hello@` alias **EXISTS and is tested** (mail to `hello@` lands in `charles@`).
  Do NOT recreate it; do NOT add a second paid user.
- Gmail **signature** named `motionX` is **installed** (content matches
  `outreach/signature.html`). Gmail **display name** target is `Charles Dai | MOTIONX`
  (Gmail → Settings → Accounts → "edit info"). These are Gmail-settings items, not code.
- The Gmail connector is authenticated as **`charles@madebymotionx.com`** (the
  Workspace mailbox). It can read mail + create drafts; it cannot change Gmail
  settings (display name/signature) or send mail.
- Project folder: **`~/Desktop/MotionX`** (the earlier accidental leading space was
  removed). The `.vercel` link + git history travel with the folder, so deploys work.

## Visual rules (do not drift from these)

**Palette** (tokens in `globals.css` — this list must stay in sync with `@theme`):
- Backgrounds: `ink #050505`, `soft #0B0B0D`, `panel #101015`, `blueblack #080A14`
  (blue-shifted near-black, used for the Launch System section's tonal variation).
- Text: `ivory #F2EFE8` (primary), `gray #A6A6AD` (secondary — brightened from the
  original #929292 to clear WCAG AA on the dark backgrounds), `gray-dim #82828A`
  (tertiary/metadata only). Hairlines: `line #20212A`.
- Accent: electric blue `accent #6D7CFF` (+ `accent-soft #8A96FF`); sparing
  chrome/magenta `magenta #D65BD6`.
- **Botanical green `#7FA64E` and gold `#C7A24B` are project-scoped** — only used
  inside the "Renewal" case study (its accent + soft background bleed). Do not use
  them as global UI colors.

**The site is dark/futuristic first.** The botanical project provides warmth and
contrast; it is the exception, not the system.

**Typography:** big tight-tracked display headlines (`.display`), small uppercase
mono metadata (`.label`), generous whitespace, strong hierarchy. Body text is
never thinner than normal weight.

**Restraint:** rounded corners are used sparingly. No gradient blobs, no
glassmorphism pile-ups, no floating-card soup, no constant animation. Animation is
cinematic (masked reveals, slow scales, scroll reveals) — not bouncy or springy.
Nothing should compete with the portfolio videos.

The recurring visual signature is a restrained **edit-suite surface**: square-edged
metadata, thin rules, one active playhead/accent, and a single media stage. It appears
in Selected Work, the AURA stage rail, and navigation progress. Reserve pills for
primary actions and media controls; concept provenance uses `.concept-mark`, and
project disciplines use `.project-tag` rather than promotional badges.

## Animation conventions

- Ordinary section copy renders immediately. `<Reveal>` is now a server-first
  structural wrapper, intentionally **not** one of dozens of identical JS fades.
  This keeps the offer readable before hydration and if JavaScript fails.
- Headline entrances use the CSS-only `<MaskedLines>` treatment. The content remains
  real server-rendered text; supporting browsers use a view timeline, other browsers
  get a short CSS entrance, and reduced-motion gets the final state immediately.
- The hero entry, active Selected Work panel, and process playhead are CSS. Do not
  re-hide core copy in a Motion `initial={{ opacity: 0 }}` state.
- Scroll-linked decorative progress should use CSS view timelines with a complete
  static fallback, so content and layout never depend on client hydration.
- Easing: `cubic-bezier(0.22, 1, 0.36, 1)` ("cinematic"). The global reduced-motion
  rule remains the final safety net.
- **Shared motion infrastructure in `globals.css` (keep its invariants):**
  `.link-underline` (drawn-underline links — two background layers, NO `color`
  declaration, converted call sites must not keep a `border-b`);
  `.rule-draw-x/-y` + `.reveal-soft` (scroll-drawn rules/entrances — the hidden
  state exists ONLY inside the `@supports (animation-timeline: view())` +
  no-preference double gate; keep `.reveal-soft` under ~6 mounts and never on
  MaskedLines); registered `@property` block at top level (`--project-accent`,
  `--reel-progress` — pseudo-element consumers need `inherits: true`).
  The reduced-motion clamp zeroes durations but NOT `animation-delay`, and it
  keeps animation fill — so any delayed or `forwards`-fill entrance must be
  authored inside `@media (prefers-reduced-motion: no-preference)` (the hero
  push-in and menu stagger are the precedents), and `::details-content` is
  unreachable by the clamp's selectors (its transition carries its own gate).
  `animation-delay` is ignored on scroll/view timelines — stagger with
  per-item `animation-range` offsets only. **`view()` timelines bind to the
  nearest ancestor scroll container, and `overflow: hidden` creates one** —
  `body` once used `overflow-x: hidden` and silently froze every scroll-driven
  animation sitewide at a static progress (the process playhead sat at 38%
  forever; the footer rule at 9%). `body` and any section that wraps a view()
  consumer (rule-draw, reveal-soft, MaskedLines, hero exit grade) must use
  `overflow-clip` / `overflow-x: clip`, never `overflow(-x): hidden`. Telemetry (hero timecode, edit-bay
  `TC` chip + playhead, loop ring) derives from REAL playback time, whole
  seconds only, `aria-hidden`, outside every live region — never fabricate
  precision or show it before playback data exists.

## Video rules

- Use `<VideoPlayer>` for portfolio clips. It handles muted autoplay, `playsInline`,
  poster + aspect-ratio box (no layout shift), in-view play / offscreen pause,
  tab-hidden pause, and accessible play + mute + CC controls.
- **Responsive delivery is a native `<source media>` ladder, not JS branching.**
  Every film offers its mobile derivative first (`media="(max-width: 767px)"`,
  condition centralized in `src/content/media.ts`) with the approved desktop web
  copy as the fallback; the browser selects once at load time. Mobile derivatives
  are re-encoded FROM the approved web copies (recipes in
  `docs/asset-integrity.md`) — same edit, same footage exclusions, never from the
  `hf_` masters. "Video unavailable" appears only after the LAST ladder candidate
  errors — a single failed candidate must fall through silently.
- **Captions:** every audio-bearing portfolio film ships truthful English WebVTT
  (`public/captions/*.en.vtt`, referenced via `project.captions`) rendering
  through a `<track kind="captions">` plus the player's CC toggle. Cues are
  exact transcripts where speech exists and conservative descriptions for
  verified non-dialogue audio — never caption a sound inferred from the visuals,
  invent dialogue, or add claims. The silent hero teaser has no captions track by design and is
  the only video excluded from the Axe `video-caption` rule (scoped exclude in
  `e2e/a11y.spec.ts`, not a global disable). Cue wording/timing changes need
  Charles's review.
- Portfolio clips also start poster-first with `preload="none"` until the browser's
  preferences are known. Reduced-motion and Save-Data visitors remain on the poster
  and never autoplay, but the explicit play and mute controls must still work. Normal
  visitors retain in-view muted autoplay and metadata preload.
- The hero uses its own background `<video>` playing the versioned
  `agentic-trading-hero.<hash>.mp4`,
  with a purpose-built 9:16 mobile reframe. The teaser has **no audio track**, so
  the hero shows a play/pause control only —
  do not add a mute toggle for a silent video.
- **Hero copy legibility is layered, and all three layers are load-bearing.**
  The teaser runs bright on its mascot beats, where the copy measured ~1:1
  against the backdrop. Protection is (1) the gradient washes in `hero-reel.tsx`,
  (2) a mobile-only copy band there — the left-to-right wash is tuned for the
  desktop composition, where copy sits in the left third, and gives almost
  nothing on the full-width 9:16 reframe, and (3) the `.over-media` text halo on
  the eyebrow and supporting copy, which darkens only the pixels around each
  glyph. The halo exists because a scrim heavy enough to protect 11px type on
  the brightest beats would flatten the frame. If the teaser is ever recut,
  re-measure: sample the backdrop under the actual glyph rects with the text
  hidden (or `color: transparent` to keep the halo) — sampling whole block boxes
  includes empty space beside the glyphs and reports the wrong number.
- **Hero teaser loads responsibly (don't revert to eager loading).** The `<video>`
  is `preload="none"` over a responsive poster `<picture>`
  (`agentic-trading-hero.<hash>.webp` desktop,
  `agentic-trading-hero-mobile.<hash>.webp` mobile)
  as the instant first paint; the video stays transparent until `playing`. The
  ~2.2 MB mp4 is never on the critical path. Playback is opted-in only *after mount*
  through the shared reactive `useVideoAutoplayAllowed` policy, which is false when
  the visitor is on a data-saver connection (`navigator.connection.saveData`) or
  prefers reduced motion, and updates if either preference changes. In those cases
  the poster is the static fallback. Do **not** add an `autoPlay` attribute or
  branch it on `useReducedMotion`: that attribute differed between SSR and the
  reduced-motion client and caused a hydration mismatch. Playback is driven by the
  in-view hook's `enabled` flag instead.
- **Never** wrap the player in another interactive element. Each Selected Work
  index entry has one real preview `<button aria-pressed>` and a separate canonical
  case-study `<Link>`; never intercept or change the link's meaning after hydration.
  Both stay outside `VideoPlayer`, so its play/mute/caption buttons remain the only
  controls over the media. Preview state is URL-addressable and restores through
  browser Back/Forward. Mobile uses a compact one-row-per-project cue sheet; desktop
  keeps that index sticky beside the single active media stage.
- Full case routes keep a compact, sticky Case index linking to `#case-film`,
  `#case-breakdown`, and `#case-inquiry`; a truth-safe “What this shows” statement;
  a neutral “Concept output scope” (never an unsupported produced-work claim); and
  a concept-labelled visual Up Next card. Both return links preserve the viewed
  project with `/#work-<slug>`. “What this shows” leads the breakdown; the Case
  index collapses on mobile, and detailed concept notes use one native collapsed
  disclosure at every breakpoint. The portrait Renewal case uses a copy/film split
  only at desktop widths.
- Only one video may play audio at a time; default is muted. `VideoPlayer`
  instances arbitrate audio ownership through one shared document event and
  expose project-specific accessible control names.
- **Web copies are re-encoded derivatives — never ship a raw `hf_` master byte-for-byte**
  (liquid-signal shipped as an untouched 26.9 MB / 14.3 Mbps master copy until Jul 2026).
  Recipe, run from the project root against the original master:
  `ffmpeg -i <hf_master>.mp4 -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 23
  -preset slow -maxrate 7000k -bufsize 14000k -c:a copy -movflags +faststart
  `/tmp/<name>.mp4` (~6 Mbps, visually transparent for these films). After
  review, publish it under `public/videos/<name>.<first-12-SHA256>.mp4`; never
  overwrite bytes behind an existing hashed URL.
  **Portfolio films keep their AAC sound-design track (`-c:a copy`)** — stripping it
  with `-an` silently turns the player's mute toggle into a no-op (this regression
  shipped briefly; every portfolio film must probe as `video + audio` streams). Only
  the hero teaser is `-an` by design.
- **FURIA is the exception to "re-encode straight from the master":** its web copy
  must be cut with the `delogo` step that removes the third-party "FERRARI"
  end-card wordmark, and it is capped at 4000k (not 7000k) because the film runs
  30s and would otherwise blow the 16 MB desktop budget. Exact recipe, coordinates,
  and rationale live in `docs/asset-integrity.md` → "FURIA third-party marks".

## Hero teaser (regenerating it)

The hero is a short, muted, looping **Agentic Trading concept teaser** derived
from the operator-supplied widescreen and vertical web builds. The complete
30-second narrated film remains in Selected Work; the hero uses only claim-light
mascot/research/resolved beats and carries visible concept/financial provenance.
Rules when rebuilding:
- Keep the `site.hero.screening` line visible. It must identify the film as a
  self-initiated concept and state that the system/data are fictional and no
  product, result, or financial advice is implied.
- Use only 4.1–7.1s, 10.5–13.5s, and 23.4–26.4s from the cleared aspect-specific
  web builds. Exclude the numeric trade-plan sequence (~17–21s) and the
  “MOTIONX Agentic Trading System” end card (~27–30s), which read as real product
  claims when separated from the project disclosure.
- Keep the two aspect versions on identical timings and transitions. Desktop is
  1920×1080; mobile is the purpose-built 720×1280 reframe. Both are 30fps,
  silent (`-an`), faststart, and 8.2s long.
- The source archive, incoming web-build, and supplied-still hashes live in
  `docs/asset-integrity.md`; never substitute an unreviewed render or crop.
- Recipe (run from the project root with the `motionx` conda ffmpeg on PATH;
  set `SOURCE` to the approved 16:9 or 9:16 incoming web build and choose the
  matching scale/output settings):

```bash
ffmpeg -y \
  -ss 4.1 -t 3.0 -i "$SOURCE" \
  -ss 10.5 -t 3.0 -i "$SOURCE" \
  -ss 23.4 -t 3.0 -i "$SOURCE" \
  -filter_complex "[0:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p[v0];[1:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p[v1];[2:v]fps=30,scale=1920:1080,setsar=1,format=yuv420p[v2];[v0][v1]xfade=transition=fade:duration=0.4:offset=2.6[x1];[x1][v2]xfade=transition=fade:duration=0.4:offset=5.2[outv]" \
  -map "[outv]" -an -c:v libx264 -profile:v high -pix_fmt yuv420p \
  -crf 27 -preset slow -maxrate 3500k -bufsize 7000k -movflags +faststart \
  /tmp/agentic-trading-hero.mp4
```

For mobile, use the approved 9:16 source, replace `scale=1920:1080` with
`scale=720:1280`, use `-crf 28 -maxrate 1200k -bufsize 2400k`, and write
`/tmp/agentic-trading-hero-mobile.mp4`. Hash each approved output, move it to a
new versioned path, and update `src/content/media.ts` plus the asset contracts.
The static poster is a deterministic crop of
the operator-supplied `hero_final.png`, not a teaser frame. Keep the exact
`crop=2560:1440:600:0,scale=1920:1080` recipe documented in
`docs/asset-integrity.md`: it excludes the source image's `SCORE 0.84` label and
baked timeline so reduced-motion/Save-Data visitors never land on numeric or
false-interactive UI.

## Contact flow rules

- No backend. Never render "Message sent" — the UI must not claim delivery.
- Public project types, budget ranges, and timelines live in `src/content/contact.ts`.
  Services, projects, and base pilot offers use its `ProjectType` union; never duplicate
  an option list inside the form. General `Campaign Content System` remains selectable,
  while `Campaign Content Add-On` is a separate referral-only pilot scope defined in
  `src/content/pilot.ts` and must never appear in the general contact select.
- Normal inquiries use subject `MOTIONX Project Inquiry — <who> · <type>`. Only pilot
  CTA referrals carrying a matching `type` + `pilot` offer id use
  `MOTIONX Pilot Project Inquiry — <who> · <type>`. Never infer pilot pricing from
  `type` alone; general service and case-study CTAs share some of those values.
- A valid `addon=campaign-add-on` is accepted only beside one exact base
  `type` + `pilot` pair. The selected-package summary and Gmail body must include
  both base and add-on; standalone, duplicate, unknown, or mismatched markers are
  ignored as pilot context rather than guessed.
- At submit time, derive both pilot intent and any valid URL project type again;
  browser autofill can make a user faster than the mount-time preselection effect.
- Primary action is **Continue in Gmail** → `gmailComposeUrl(email, subject, body)`
  opened by **clicking a transient real `<a target="_blank" rel="noopener noreferrer">`**
  (NOT `window.open`). `window.open` can return `null` even when the tab opens — that
  produced a false "Gmail didn't open" error. Only a thrown exception counts as failure.
- After an attempt: neutral confirmation ("Your project brief is ready in Gmail…"),
  plus a dismissible **"Having trouble?"** helper (Try Gmail again / Copy email /
  Copy prepared message / Open default mail app). It is assistance, not an error.
  The full brief is shown inline only on a genuine caught error.
- The helper/error state must reset on each new submit and on refresh (it's plain
  component state — don't persist it). Initial state is clean (no helper visible).
- Provide **Copy email address** (live-region confirmation, Clipboard API + timeout +
  textarea fallback) and a labelled **Open default mail app** (`mailto:`) before any
  Gmail attempt as well as in the fallback helper. Email is also selectable text.
- On mobile, the source order is pitch → required form fields → supporting details;
  company, budget, and timeline are optional progressive disclosure. The desktop
  two-rail composition remains intact. Public fields keep explicit length limits;
  the project brief shows its 2,000-character count so compose URLs remain bounded.
- "Start a Project" CTAs call `scrollToContact` — scroll + focus the contact
  heading only; never open email or submit. Preserve the current query string so
  attribution and trusted project-type preselection survive the hash update.
- Homepage service/case-study CTAs that add a `type` query must call
  `navigateToContactWithType`. It owns the URL update, pilot-marker clearing,
  location synchronization, scroll, and focus; relying on Next's same-route Link
  handoff here proved race-prone in WebKit under parallel browser load.

## Content-integrity rules (important)

- All four projects are **concept projects** and must stay labelled as such. The
  botanical clip depicts a real third-party pharmaceutical product, and FURIA is a
  spec film whose vehicle carries a real manufacturer's marks; **never claim
  MOTIONX was commissioned by either company or any real client.** Do not imply a
  project included a real commissioned website unless one is actually built and
  clearly labelled as concept work.
- **FURIA's disclosure is load-bearing, not boilerplate.** It must keep naming the
  non-affiliation with Ferrari S.p.A. outright. Never re-describe FURIA as
  unbranded, as an original marque, or as a real commission — the shield badges are
  still on the car, so any of those would make the copy untrue rather than discreet.
  Its OG card is the de-branded end card on purpose: social cards travel without the
  page's disclosure. See `docs/asset-integrity.md` → "FURIA third-party marks".
- **Agentic Trading's disclosure is also load-bearing.** It is a self-initiated
  film for a fictional system, not a live trading product. All market data,
  tickers, scores, and depicted behavior are fictional; no client relationship,
  performance result, or financial advice is implied. Its share card must keep
  visible “Concept Film”, “Fictional Data”, and “Not Financial Advice” provenance.
- Each project entry must keep a public concept disclosure (`disclosure`) explaining
  that no client relationship, commercial result, or unsupported claim is implied.
- **No fabrication:** no fake clients, testimonials, awards, team members,
  statistics, conversion numbers, production credits, or quotes. The studio is
  honestly described as small and independent.
- **No invented location, domain, or social profiles.** No "Pittsburgh"/address,
  no `motionx.studio` (or any made-up domain), no Instagram/LinkedIn placeholders.
- No unsupported medical/health claims in the botanical copy.
- All editable info (brand, email, copy) stays centralized in `src/content/*`.
  Don't scatter literals into components.
- `npm run content:check` is the source-level guard for these rules and runs first
  in `npm run gate`; update it when adding a new public content surface.

## Asset rules

- **Never delete, rename, overwrite, or recompress the original `hf_2026…*.mp4`
  files** in the project root. The web copies in `public/videos/` are derivatives.
- Public videos, posters, editorial images, and captions use content-hashed
  filenames. Their hash-matching `vercel.json` paths are cached for one year as
  immutable;
  never overwrite a published path. Render replacements outside those roots,
  publish under a new first-12-SHA-256 suffix, update centralized references and
  `scripts/asset-integrity.mjs`, then run `npm run assets:check`.
- Posters are ffmpeg-extracted WebP. Regenerate from the web copies, not the
  originals, if needed (see README).
- **Social share cards live in `public/og/` as 1200×630 JPEG** (`og-image.jpg` brand
  card + `<slug>.jpg` per project + `system-study.jpg`) — **JPEG, not WebP**:
  LinkedIn/WhatsApp/iMessage crawlers don't reliably render WebP previews. The Renewal
  card must use only the atmospheric ginkgo frames (~0–1.6s of the film, center-band
  crop to dodge the caption) — never the third-party product packaging. Liquid Signal's
  card is a mid-film frame (~7s). If a film changes, regenerate:
  `ffmpeg -ss <t> -i public/videos/<name>.<hash>.mp4 -frames:v 1 -vf "scale=1200:630:force_original_aspect_ratio=increase,crop=1200:630" -q:v 4 public/og/<slug>.jpg`.
  The `/system-study` card is captured from the rendered route itself (its AURA
  visuals are pure CSS/SVG): with a server on port 3939, run `npm run og:system-study`.
  It must keep the visible "MOTIONX SYSTEM STUDY · Concept" provenance in frame, and
  `scripts/seo-sanity.mjs` + `scripts/asset-integrity.mjs` both enforce its presence.

## Video production workflow

Use the mirrored project skill at
`.claude/skills/motionx-video-production/SKILL.md` / `.agents/skills/...` for product
films, motion design, Higgsfield CLI/MCP, Claude Fable 5, GPT-5.6, generated-footage
review, finishing, and provenance. The provider-neutral runner is
`video-production/motionx_video.py`; the only approved provider-calling surface is the
receipt-backed `video-production/higgsfield_adapter.py`. Runtime projects remain outside
the repo under `~/.motionx-production/projects/`.

- Begin plan-only. Upload/generation requires verified rights, privacy and claims;
  storyboard approval; live model/schema and cost checks; a hard credit cap; and explicit
  current-task approval. Never infer approval from a research/setup request.
- Connection contexts are separate: Codex reads `.codex/config.toml`, Claude Code reads
  `.mcp.json`, and the standalone CLI has its own OAuth/workspace state. Use the token-safe
  `video-production/higgsfield_doctor.py --live`; an OAuth-capable label is not proof of
  a completed login or a fresh-task tool handshake.
- Treat Fable 5 or GPT-5.6 as director/reviewer and Higgsfield as renderer. Use a
  deterministic compositor/NLE for exact logos, labels, legal copy, UI, prices, claims,
  typography, CTA, final edit and audio.
- Query Higgsfield models and workflows as separate surfaces and compile schema-v3 intent
  with canonical required capabilities plus structured provisional primary/fallback/
  rejected routes. After `higgsfield_doctor.py --live --record-project`, run provider-free
  `bind-route` before upload/costing to derive and exact-bind the primary live surface/job/
  invocation/schema/capabilities; never hand-copy the schema hash. Exact create and
  workflow cost arguments, provider UUID provenance, quote hash/adjustments and fresh
  approval are scope-bound; never copy universal flags between Kling, WAN, Veo, Seedance
  and Cinema workflows.
- Select a nonempty `active_shot_ids` batch and keep every provider create/tool intent at
  quantity one. Capture quotes and approved submits through the no-shell adapter: no
  local media paths, no `--wait`, immutable receipts, and a durable claim before one
  guarded local create invocation; provider-global exactly-once is not guaranteed. A
  create with no trusted job UUID remains `reconcile-required` and must never be retried.
  Automated `reconciled`/`no-job-confirmed` states are disabled; provider UI/support
  review is the final manual path.
- Terminal status polling remains blocked. If operator-downloaded bytes already exist but
  their succeeded receipt expired before ingest and no download evidence has been
  recorded, the adapter's one-time `refresh-result-status` path may perform exactly one
  same-job read. It requires the identical terminal succeeded project/shot/tool-intent/job
  tuple and result-URL hash, cannot create or retry a job, and appends no duplicate spend.
- Before upload, the adapter dry-preflights the complete schema/cost/create/argv contract
  for every active reuse target. Started upload/create recovery is local-only before
  freshness/CLI checks and requires exactly one fully trusted receipt; extra, missing or
  tampered receipts block. An expired claim-only create must be abandoned and rebound.
  Clear an unusable pre-start upload claim only with local `cancel-upload-claim`, which
  writes an immutable tombstone and archives the claim without deleting evidence; any
  started marker or receipt forbids cancellation.
- Provider upload bytes and the CLI payload use descriptor/hash-verified snapshots to
  close ordinary pathname replacement. Darwin cannot execute `/dev/fd` and lacks
  `fexecve`/`execveat`; excluding a malicious same-UID process requires privilege
  separation and remains outside the local trust boundary.
- Provider-native resource mappings are preparatory provenance only; execution is hard-
  blocked until an attested workspace-bound resource receipt exists. Finishing requires
  schema-v2 canonical provider-render/registered-asset source IDs, private hash-bound
  timeline/export artifacts under `edit/`, exact declared/used input equality, and
  overlay/audio track binding; schema v1 fails closed.
- Spectacle follows the compiler's 0–4 ladder. Levels 3–4 require both an earlier
  audience-facing non-truth product establishment and an earlier same-group level-0
  auxiliary truth plate with matching continuity; the truth plate does not itself
  establish the product. The renderer pair names its plate role/group/continuity hash;
  truth locks the clean product/camera/action/hold while spectacle matches it and stays
  behind/around the product. Level 4 appears once; every effect has an emitter, envelope,
  onset, peak and decay, never occludes the product, clears before the stable end hold, and
  keeps exact art local.
- Do not upload confidential/unreleased client assets or biometric face/voice material to
  consumer Higgsfield without explicit consent and approved data terms. Soul ID is off by
  default.
- Preserve every vendor output and its prompt/settings/job/cost/hash provenance. Never
  overwrite the root `hf_2026*.mp4` masters.
- Website promotion starts only from an operator-approved, QC-passed master and then
  follows this file's derivative, disclosure, caption, poster, social-card and gate rules.
  Generation, promotion and deployment are three separate approvals.

## Website Design and Upgrade Skills

Project-scoped Claude Code skills for website work live in `.claude/skills/`
(provenance + audit details in `.claude/skills/INSTALL-MANIFEST.md`):

- **`frontend-design`** (Anthropic) — visual direction, typography, layout, distinctive
  non-templated design. Activates when designing or reshaping UI.
- **`ui-ux-pro-max`** (third-party, audited) — design-reference database (styles,
  palettes, font pairings, UX guidelines). Use as a **reference only**, not a mandate;
  query via `scripts/search.py`. Don't run its generator against the site.
- **`react-best-practices`** (Vercel) — React/Next.js implementation + performance.
  Activates when writing/reviewing/refactoring components or data fetching.
- **`web-design-guidelines`** (Vercel) — accessibility/UX audit checklist. Activates when
  reviewing or auditing UI.
- **`webapp-testing`** (Anthropic) — Playwright browser run, screenshots, console/overflow/
  reduced-motion checks. Activates when verifying visible changes.

Route all website improvements through **`motionx-website-upgrade`** — the central
workflow that sequences these skills (Understand → Design → Implement → Audit → Run &
verify → Quality gate → Production safety).

Rules:
- **The current MOTIONX design system (this file + `src/content/*`) overrides generic
  skill advice.** Skills advise; they do not authorize drift from the palette, restraint
  rules, section order, or content-integrity rules.
- **Visual changes require browser verification** (desktop + mobile, console, overflow,
  reduced-motion). **Build/typecheck/lint success alone is insufficient** to claim done.
- The **`motionx-outreach`** skill is unrelated to website work and **must not be
  modified** during website tasks.

## Testing, preview & verification

- **Local preview / dev server runs on port 3939** (`.claude/launch.json`). The
  project's Node lives in the `motionx` conda env (`/opt/anaconda3/envs/motionx/bin`)
  and is **not** on the default PATH, so the launcher `cd`s into the project and execs
  the project-local `./node_modules/.bin/next`. To run anything by hand, prefix
  `export PATH=/opt/anaconda3/envs/motionx/bin:$PATH`. (The harness `preview_*` tools
  are sandboxed away from this project's files — drive the browser with Playwright
  against a Bash-started server instead.)
- **End-to-end tests:** `npm run test:e2e` (Playwright, `@playwright/test` +
  `playwright`, dev-only). Browsers were installed with
  `npx playwright install chromium webkit` (cached under `~/Library/Caches/ms-playwright`,
  not in the repo). The runner auto-starts a dev server on 3939 and reuses a running
  one. Point the suite elsewhere with `PLAYWRIGHT_BASE_URL=…` (e.g. a production-mode
  `next start`, or `https://madebymotionx.com`) — then no server is started. Override
  the Node path with `MOTIONX_NODE`.
- Tests are **functional only** (`e2e/motionx.spec.ts`): routes/status, nav, mobile
  menu (three primary destinations; complete footer index; `aria-current` active
  state; Escape → focus back on toggle),
  no-JavaScript content readability, Selected Work edit-bay (one active film,
  URL/hash history restoration, canonical links, responsive media and captions),
  canonical case-study paths + contextual
  inquiry links, System Study disclosure/CTA, pilot→contact preselection (incl.
  mismatched-pilot rejection and submit-time URL re-derivation), "Start a Project"
  contract (focus heading, never open email), contact validation +
  Gmail-compose-to-`hello@` + normal-vs-pilot subject handling, no-false-sent +
  "Having trouble?" helper lifecycle (incl. the genuine caught-error inline brief +
  reset-on-edit), copy-email (form + rail islands), video-failure fallback notice,
  concept-label/private-address integrity, no horizontal overflow at
  375/390/430 on ALL routes (incl. `/system-study` and `/work/*`), reduced-motion
  cleanliness + poster-only portfolio policy **as a network contract** (zero .mp4
  requests under reduced motion and Save-Data), hero-stays-poster, hero poster→play.
  `e2e/csp.spec.ts` additionally exercises the contact→Gmail compose flow under the
  production CSP. No pixel/screenshot diffing (portfolio
  video frames would make snapshots flaky).
- **`toBeVisible()` cannot detect a covering overlay** — a full-screen stale layer
  (e.g. the intro loader failing to dismiss under reduced motion) passes visibility
  checks. Assert interactivity with `click({ trial: true })` (full actionability,
  incl. "receives pointer events") when testing anything overlay-adjacent.
- **Known load-sensitive WebKit flakes (Aug 2026):** `Contact flow › history
  removal resets URL preselection…` and `Responsive & resilience › switching the
  edit bay discards the previous audio owner` have each failed ~once under heavy
  parallel machine load (the latter also once over the live-site suite), then
  passed 3/3 in isolation and in repeated full runs. If a gate fails on exactly
  one of these, re-run the single test in isolation before investigating; a
  deterministic repeat failure is a real regression. Do not add local retries —
  CI runs `failOnFlakyTests` by design, and local retries would just diverge.
- **Breakpoints verified:** 1440, 1280, 1024, 768, 430, 390, 375. All routes show
  zero horizontal overflow and zero console errors (incl. reduced motion).
- **Verification gate before shipping visual/behavioural changes:** `npm run gate`
  (runs content-integrity → asset-integrity → SEO sanity → typecheck → lint → build →
  metadata-guard (validates built HTML/sitemap/robots metadata + 404 isolation against the real output) → privacy-guard (scans built browser artifacts for non-public addresses) → test:e2e in order, and aborts if a dev server holds port 3939), **and** a real browser
  pass (desktop + mobile, console, overflow, reduced motion). A green build/typecheck/lint
  is **not** sufficient on its own.
- `npm run browser:verify` is the repeatable real-browser pass once a dev server is
  running on port 3939. It exercises every public route at 1440/1280/1024/768/
  430/390/375, writes ignored desktop/mobile and full-page screenshots for every public route plus
  `test-results/browser-verify/evidence.json`, and checks console errors, overflow,
  nav mode, reduced motion, Save-Data, media playback, and normal-vs-pilot contact
  subjects.
- `npm run assets:check` protects the root `hf_2026*.mp4` masters, public video
  derivatives, posters, OG cards, and source-visible media references. It requires
  `ffprobe`, fingerprints immutable masters, validates public stream/codec/dimension
  contracts, requires MP4 faststart, and parses social cards as 1200×630 JPEGs.
- `npm run seo:check` verifies route metadata/schema basics without inventing address,
  phone, awards, social profiles, or other unsupported business facts.
- `.github/workflows/website-quality.yml` runs the production gate in read-only,
  no-deploy CI with Node 22, ffprobe, Chromium, and WebKit. The gitignored camera
  masters are the only CI-only asset skips; all tracked public media remains enforced.
- **Production verification after deploy:** load `https://madebymotionx.com`, `/pilot`,
  `/system-study`, and each `/work/*`; confirm 200/HTTPS, canonical = real domain (the sitemap/robots use
  `NEXT_PUBLIC_SITE_URL`, which is set in Vercel — a local prod build without it falls
  back to localhost, which is expected locally), videos/posters, nav, mobile, contact
  flow, and no stale deployment. Optionally run the suite against the live URL via
  `PLAYWRIGHT_BASE_URL=https://madebymotionx.com npm run test:e2e`.

## Gotchas

- **Custom classes in `@layer utilities` can silently beat Tailwind colour
  utilities.** Tailwind generates its utilities into that same layer, and
  anything authored after them ties on specificity (0,1,0) and wins on source
  order. `.label` hard-coded `color: var(--color-gray-dim)` this way and killed
  the `text-*` colour on **55 call sites** — 46 of them `text-accent-soft`, so
  the electric-blue eyebrows that carry the brand accent rendered dim grey
  sitewide, and the mobile hero eyebrow sat at ~1:1 contrast because of it. The
  fix is a zero-specificity `:where(.label) { color: … }` default, kept as a
  separate rule; **do not fold that colour back into the `.label` block.** When
  adding any custom class here, either omit `color` or wrap it in `:where()`.
  An e2e test (`Design system › accent labels keep their colour utility`)
  asserts an accent label actually computes to the accent, so this fails loudly.
- Don't run `next build` while `next dev` is live (corrupts `.next`; dev then 500s).
  Fix with `rm -rf .next` and restart dev. `npm run gate` (content-integrity →
  asset-integrity → SEO sanity → typecheck → lint → build → metadata-guard → privacy-guard → e2e) refuses to start while
  port 3939 is in use, for exactly this reason.
- Website work may start with unrelated local dirt such as `outreach/self-improvement.md`
  or Finder metadata files. Do not stage, commit, reset, stash, clean, delete, or
  overwrite unrelated dirty files.
- **Next metadata is shallow-merged per top-level key**: a page that defines its own
  `openGraph` or `twitter` REPLACES the layout's whole object — silently dropping
  `images`, `siteName`, `type`. Any page-level `openGraph`/`twitter` must restate
  them (`/pilot`, `/system-study`, and `/work/[slug]` do; keep it that way).
- Lint runs through the ESLint CLI, scoped to website source, tests, scripts, and
  config files. Do not reintroduce deprecated `next lint` when upgrading Next.
- Tailwind v4: add design tokens in `@theme` in `globals.css`, not a JS config.
- Set `NEXT_PUBLIC_SITE_URL` in the deploy environment (not in code) so canonical/
  OG/sitemap use the real URL; it falls back to `http://localhost:3000` locally.
- Headline words that animate per-word must keep a space **between** the word
  spans (sibling text node), not trailing inside each `overflow:hidden` span —
  trailing whitespace there gets trimmed and words run together.
