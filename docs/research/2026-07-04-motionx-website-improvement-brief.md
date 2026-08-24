# MOTIONX Website Improvement Brief - 2026-07-04

## Current Site State

- Repo: `/Users/prince/Desktop/MotionX`
- Starting branch: `main`
- Starting HEAD: `3750f6d78966f62f4be725102636ce2dbd77668f` (`fix: disable prefetch for home section anchors`)
- Working branch for this pass: `motionx/research-driven-upgrade-20260704`
- Existing unrelated dirty work at preflight: `outreach/self-improvement.md`
- Additional pre-existing untracked local file observed at preflight: `Icon\r`
- Public production URL: `https://madebymotionx.com`
- Production deploy previously verified by user: `dpl_3Wa6jy1b9PWomQx2QQzk85WBAryr`
- Current routes: `/`, `/pilot`, `/work/renewal`, `/work/liquid-signal`

## Production Inspection

Read-only production browser verification was run against `PLAYWRIGHT_BASE_URL=https://madebymotionx.com` on 2026-07-04.

Observed result:

- Existing `browser:verify` passed against production after sandbox launch approval.
- Desktop and mobile screenshots were generated for all four routes.
- Console/page error checks passed.
- Horizontal overflow checks passed.
- Reduced-motion home kept the hero video paused on the poster frame.
- Hero playback passed for a normal-motion visitor.
- Normal and pilot contact subject checks passed.

Production screenshots inspected:

- `test-results/browser-verify/desktop-home.png`
- `test-results/browser-verify/mobile-home.png`
- `test-results/browser-verify/desktop-pilot.png`
- `test-results/browser-verify/mobile-pilot.png`
- `test-results/browser-verify/desktop-work-renewal.png`
- `test-results/browser-verify/desktop-work-liquid-signal.png`
- `test-results/browser-verify/reduced-motion-home.png`

## Current Strengths

- The first viewport communicates the core offer without fake proof: film, website, launch page, campaign system.
- The visual identity is distinctive and consistent: dark cinematic base, electric blue/magenta accents, large Geist display type, portfolio video as proof.
- The contact flow is honest: Gmail draft only, no "message sent" claim, public `hello@madebymotionx.com` only.
- Concept-work labeling is already present across selected work, project modal, and work-detail routes.
- Production browser checks show no obvious runtime, overflow, console, or reduced-motion blocker.
- The local gate already includes content integrity, typecheck, lint, build, and e2e.
- The hero reel uses `preload="none"`, poster-first behavior, and reduced-motion/data-saver gating.

## Current Gaps

- The integrated launch offer is clear, but the Launch System can state the operating sequence more concretely.
- Services can include short deliverable examples so they feel less abstract without inventing outcomes.
- Work-detail pages disclose concept status, but they can do more to teach buyers what to evaluate in concept work.
- Pilot packages show prices and inclusions, but the page can clarify what buyers get, what happens next, and what is outside scope.
- Honest trust-building can be stronger through first-party standards: no fake proof, concept labeling, reduced-motion support, performance-aware media, and manual review.
- SEO is adequate, but there is no dedicated sanity check for truthful metadata/schema and expected routes.
- Asset safety relies mostly on docs; a deterministic check can protect master videos, public derivatives, posters, and hero-size budget.
- The `.claude` and `.agents` website-upgrade skill copies have drifted; the Claude copy contains known pitfalls not present in the agent copy.

## Implementation Candidates

- Add centralized `trustStandards` and `faq` content and render them inside existing Studio/Contact sections.
- Add `launchSystemSequence` and service example fields in `src/content/services.ts`; render them without changing homepage section order.
- Add `conceptStudyNotes` to each project and render concise "Concept study notes" on work-detail pages and project modals.
- Add pilot page detail groups for "what you get", "what is not included", and "what happens next".
- Add truth-safe WebSite JSON-LD and CreativeWork JSON-LD for work-detail pages with concept wording.
- Add `scripts/seo-sanity.mjs` and `npm run seo:check`.
- Add `scripts/asset-integrity.mjs`, `docs/asset-integrity.md`, and `npm run assets:check`.
- Fold deterministic `seo:check` and `assets:check` into `npm run gate`.
- Extend e2e coverage for new visible content and data-saver hero behavior.
- Update AGENTS, CLAUDE, README, and mirrored website-upgrade skill files with the new checks.

## Deferred / Backlog Candidates

- Service-specific pages should wait until each page has distinct examples, visuals, FAQs, and proof-safe copy. Thin pages would dilute quality.
- More persuasive case studies need new first-party artifacts: process stills, before/after storyboards, campaign mockups, production notes, or a behind-the-system reel.
- Testimonials, clients, awards, metrics, press, locations, social links, and case-study results must remain absent unless Charles has real proof.
- Real backend contact delivery should remain backlog until Charles decides the operational tradeoff; the current Gmail-draft flow is honest and working.
- Pilot scarcity/bonus wording should get Charles review because "first three" requires manual tracking.

## Source URLs Consulted

- W3C WCAG 2.2: `https://www.w3.org/TR/WCAG22/`
  - Supports keyboard access, focus visibility, target size, status messages, motion sensitivity, labels, and robust accessibility requirements.
- Vercel Web Interface Guidelines: `https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md`
  - Supports UI audit focus on accessibility, focus states, forms, navigation, motion preferences, responsive layout, and performance.
- web.dev Core Web Vitals: `https://web.dev/articles/vitals`
  - Supports LCP, INP, and CLS budgets.
- web.dev Video Performance: `https://web.dev/learn/performance/video-performance`
  - Supports poster-first video, `preload="none"`, `preload="metadata"`, and poster priority guidance.
- Next.js `generateMetadata`: `https://nextjs.org/docs/app/api-reference/functions/generate-metadata`
  - Supports route-specific metadata in the App Router.
- Next.js sitemap file convention: `https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap`
  - Supports generated route sitemap structure.
- Next.js Link component: `https://nextjs.org/docs/app/api-reference/components/link`
  - Supports preserving intentional prefetch behavior.
- Next.js JSON-LD guide: `https://nextjs.org/docs/app/guides/json-ld`
  - Supports native JSON-LD script rendering and escaping.
- Google Search structured data intro: `https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data`
  - Supports using accurate structured data that follows general and type-specific guidelines.
- Google Search documentation updates, FAQ rich result removal: `https://developers.google.com/search/updates#removing-faq-rich-result`
  - Supports not prioritizing FAQ schema as a Google rich-result tactic after FAQ rich results were removed.
- Schema.org Organization: `https://schema.org/Organization`
  - Supports using Organization without inventing address, awards, ratings, or sameAs profiles.
- Schema.org CreativeWork: `https://schema.org/CreativeWork`
  - Supports truthful concept-project markup for the work routes.
- Schema.org FAQPage: `https://schema.org/FAQPage`
  - Supports understanding FAQ schema availability, though Google rich-result value is currently reduced.
- Premium studio references reviewed lightly for pattern calibration only:
  - `https://resn.co.nz/`
  - `https://www.instrument.com/`
  - `https://www.buildinamsterdam.com/`

## Working Principle

The safe direction is not a redesign. The site already has a strong cinematic identity. The highest-leverage pass is to make the offer, proof interpretation, buyer path, and future guardrails more concrete while preserving honesty and restraint.
