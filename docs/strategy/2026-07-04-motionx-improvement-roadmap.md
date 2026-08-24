# MOTIONX Improvement Roadmap - 2026-07-04

## Executive Diagnosis

- MOTIONX has a strong first impression: the hero immediately feels cinematic and premium.
- The current positioning is directionally right: one product world carried from film into site, launch, and campaign.
- The strongest low-risk improvement is specificity, not redesign: show the sequence, deliverables, and buyer path more concretely.
- Concept work is honestly labeled, but work-detail pages can better explain what the concepts demonstrate.
- Trust should come from first-party standards and direct-founder process, not fake logos, testimonials, metrics, or scarcity.
- The contact flow is unusually honest and should remain Gmail-draft-only until a real backend is explicitly chosen.
- The pilot page is clear visually, but it needs a stronger "what you get / what is not included / what happens next" structure.
- SEO basics exist; the next safe step is truthful structured data and a deterministic sanity check, not thin service pages.
- Accessibility and motion/video behavior are already strong; add a data-saver test and keep reduced-motion verification.
- Asset safety deserves an automated guard because video files are central and easy to damage accidentally.
- Workflow files need mirror cleanup so Codex and Claude follow the same website safety rules.
- The backlog should separate items requiring new assets or Charles taste/business decisions from safe local implementation.

## Prioritized Roadmap

| Priority | Recommendation | Why it matters | Evidence/source | Risk | Likely files | Acceptance criteria |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | Preserve branch and dirty-file safety | Prevents losing unrelated outreach notes | User brief, AGENTS/CLAUDE | Low | Git state only | `outreach/self-improvement.md` and `Icon\r` untouched/uncommitted |
| P1 | Add research and roadmap docs | Keeps decisions auditable | Research brief and production inspection | Low | `docs/research/*`, `docs/strategy/*` | Docs include state, gaps, sources, acceptance criteria |
| P1 | Add asset integrity check | Prevents accidental master-video damage or direct master references | CLAUDE video rules, web.dev video performance | Low | `scripts/asset-integrity.mjs`, `package.json`, docs | `npm run assets:check` passes and is in gate |
| P1 | Add SEO sanity check | Guards truthful metadata/schema and expected route coverage | Next metadata/sitemap docs, Google structured data | Low | `scripts/seo-sanity.mjs`, `package.json` | `npm run seo:check` passes and is deterministic |
| P1 | Expand content integrity | Blocks fake proof, private email exposure, concept regressions, unsupported health claims | AGENTS/CLAUDE, WCAG/status honesty | Medium | `scripts/content-integrity.mjs` | No false positives on current truthful content |
| P2 | Make Launch System sequence explicit | Clarifies film -> web -> launch -> campaign integrated offer | Live inspection, site positioning | Low | `src/content/services.ts`, `src/components/launch-system.tsx` | Sequence understandable in one glance |
| P2 | Add service deliverable examples | Reduces abstraction without fake proof | Live inspection, premium studio pattern calibration | Low | `src/content/services.ts`, `src/components/services.tsx` | Each service has concrete examples |
| P2 | Strengthen pilot page structure | Helps buyers self-qualify and understand next steps | Live pilot inspection | Medium | `src/content/pilot.ts`, `src/app/pilot/page.tsx` | Visible what-you-get, not-included, next-step content |
| P2 | Add first-party trust standards and FAQ | Builds trust honestly | WCAG, web.dev, contact-flow rules | Medium | `src/content/site.ts`, `src/components/studio-section.tsx`, `src/components/contact-section.tsx` | No fake proof; FAQ matches visible content |
| P3 | Add concept-study notes | Makes concept work more persuasive while more transparent | Project-page inspection | Medium | `src/content/projects.ts`, `src/app/work/[slug]/page.tsx`, `src/components/project-modal.tsx` | Notes visible, concept disclosure preserved |
| P4 | Add truthful JSON-LD | Improves machine readability without inventing business facts | Next JSON-LD, Google structured data, Schema.org | Medium | `src/app/layout.tsx`, `src/app/work/[slug]/page.tsx` | No address/phone/awards/social/proof fields |
| P5 | Extend tests | Prevents regressions in new content and data-saver behavior | Existing e2e/a11y structure | Medium | `e2e/motionx.spec.ts` | E2E covers new content and saveData poster behavior |
| P6 | Update workflow docs and mirrored skills | Keeps future agents aligned | AGENTS mirror rule | Low | `AGENTS.md`, `CLAUDE.md`, `.agents/*`, `.claude/*`, README | Same safety-critical rules appear in both workflow skill copies |

## Section-by-Section Improvements

### Hero

- Keep the current cinematic hero and headline.
- Preserve `preload="none"`, poster-first behavior, and reduced-motion/data-saver poster fallback.
- No new claim needed unless future user testing shows the subline still feels abstract.

### Studio Intro

- Preserve the thesis and audience clarity.
- Avoid adding visual clutter; the section already acts as a bridge from hero to proof.

### Selected Work

- Keep both projects visibly labeled `Concept Project`.
- Preserve proof-before-explanation flow.
- Deeper explanatory content belongs on work-detail pages and modal details.

### Launch System

- Add a compact sequence that shows how the product world travels from framing to film direction, web interactions, launch page/story, and campaign formats.
- Keep the current three-output visual system rather than adding more mockup noise.

### Services

- Add concise deliverable examples under each service.
- Avoid turning services into card soup or generic agency copy.

### Pilot Callout

- Keep the callout restrained.
- Leave scarcity-adjacent bonus wording for Charles review; do not add countdowns or urgency mechanics.

### Process

- Current four-step process is clear.
- Future improvement: add buyer input/review expectations only if it can stay concise.

### Studio

- Add first-party quality standards: concept labels, no fake claims, performance-aware media, reduced motion, direct founder review.
- Present as craft standards, not defensive disclaimers.

### Contact

- Current Gmail-draft explanation is strong.
- Add FAQ items for buyer doubts: video-only, concept status, Gmail handoff, launch-page build, starting inputs.

### Footer

- Keep minimal.
- Do not add fake social links, location, phone, or "trusted by" proof.

### `/pilot`

- Add structured content for what buyers get, what is not included, and what happens next.
- Do not change pricing or package terms without Charles approval.
- Keep all offer copy centralized in `src/content/pilot.ts`.

### `/work/[slug]`

- Add "Concept study notes" with what to look for, system thinking, film-to-page extension, campaign extension potential, and concept-vs-real boundaries.
- Add truthful CreativeWork JSON-LD with concept/internal description.

## Honest Trust-Building Ideas

Can add now:

- Quality standards based on real implementation: reduced-motion support, data-saver poster behavior, concept labels, public-contact-only, performance-aware videos.
- Direct-founder process: Charles reads and responds personally; no account layer.
- Clear contact handoff: Gmail draft must be reviewed and sent by the visitor.
- Concept-study notes explaining how to judge the work.

Can add after creating real assets:

- Behind-the-system breakdowns with storyboards, production notes, campaign variants, and launch page excerpts.
- Founder process video or screen-recorded walkthrough.
- Real client work, testimonials, metrics, awards, or press only when proof exists.
- Published technical note on responsible cinematic video delivery.

## Workflow / System Improvements

- Docs: add research brief, roadmap, SEO strategy, asset integrity, performance budgets, release checklist, Codex handoff template, and backlog.
- Scripts: add deterministic `seo:check` and `assets:check`; expand `content:check`.
- Tests: assert new visible content, concept notes, and data-saver hero behavior.
- Verification: keep `npm run gate` plus `npm run browser:verify` as required.
- CI/backlog: document conservative validation workflow rather than adding deployment automation.
- Content integrity: preserve concept labels, disclosures, public email, no fake proof, no medical/health/product-efficacy claims.
- Asset integrity: protect `hf_2026*.mp4` masters and public video/poster references.
- Skill mirror consistency: update `.agents` and `.claude` website-upgrade skills together.

## SEO / Content Strategy

- Metadata: keep unique route titles/descriptions for home, pilot, and work pages.
- Schema: use truthful Organization/WebSite at layout and CreativeWork on concept work routes. Do not add address, phone, founding date, employee count, awards, reviews, sameAs, or client fields without proof.
- Service pages: defer until each page has distinct examples, visuals, FAQs, and proof-safe copy. Do not publish thin `/services/*` pages now.
- Case studies: deepen current concept pages first; real service pages can link to them later.
- FAQs: visible FAQ is useful for conversion. FAQ schema is optional and not high priority because Google removed FAQ rich-result display in 2026.
- Content hubs: defer until MOTIONX has real first-party breakdowns or process essays.

## Do-Not-Do List

- Do not push or deploy in this pass.
- Do not touch DNS, Vercel settings, Cloudflare, secrets, billing, IAM, Gmail, CRM, or outreach automation.
- Do not stage or commit `outreach/self-improvement.md` or `Icon\r`.
- Do not add fake clients, testimonials, awards, metrics, press, scarcity, countdowns, quotes, physical location, social profiles, team members, or production credits.
- Do not relabel concept work as client work.
- Do not imply Renewal or Liquid Signal were commissioned by any real company/product.
- Do not add unsupported medical, health, clinical, therapeutic, product-efficacy, or performance claims.
- Do not expose `charles@madebymotionx.com` or the private backup Gmail in public UI.
- Do not delete, rename, move, overwrite, or recompress `hf_2026*.mp4` masters.
- Do not add a backend contact form in this pass.
- Do not add service pages if they would be thin or generic.
- Do not broaden the visual system into generic agency cards, gradient blobs, or fake proof modules.
