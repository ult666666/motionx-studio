# MOTIONX Website Upgrade Release Readiness - 2026-07-03

## Release Candidate

- Branch: `motionx/website-agentic-upgrade-20260703`
- Website upgrade HEAD before this readiness note: `765301b748ca5fa980080d1793c406bf81a5e40c`
- Base comparison: `main...HEAD`
- Production inspected read-only: `https://madebymotionx.com`
- Production was not changed, pushed, or deployed during this pass.

## Commits In Scope

Website release candidate commits:

1. `8d27be98d8b73f3d145a1892bdc02253206186e7` - `feat: harden MOTIONX website integrity gates`
2. `765301b748ca5fa980080d1793c406bf81a5e40c` - `feat: polish MOTIONX website visual QA`

Readiness packet commit, if present after this file is committed:

- `docs: record MOTIONX website release readiness`

## Branch Diff Summary

Pre-readiness-note `main...HEAD` summary:

```text
AGENTS.md                          |   3 +
CLAUDE.md                          |  38 ++++---
README.md                          |  24 ++++-
e2e/motionx.spec.ts                |  55 ++++++++++-
next.config.ts                     |   2 +
package.json                       |   2 +
scripts/browser-verify.mjs         | 197 +++++++++++++++++++++++++++++++++++++
scripts/content-integrity.mjs      | 137 ++++++++++++++++++++++++++
scripts/gate.mjs                   |   5 +-
src/app/globals.css                |   9 ++
src/app/work/[slug]/page.tsx       |   6 ++
src/components/contact-section.tsx |  24 ++++-
src/components/hero.tsx            |   2 +-
src/components/project-modal.tsx   |   6 ++
src/content/projects.ts            |   6 ++
src/content/site.ts                |  12 +--
16 files changed, 497 insertions(+), 31 deletions(-)
```

Changed files:

```text
AGENTS.md
CLAUDE.md
README.md
e2e/motionx.spec.ts
next.config.ts
package.json
scripts/browser-verify.mjs
scripts/content-integrity.mjs
scripts/gate.mjs
src/app/globals.css
src/app/work/[slug]/page.tsx
src/components/contact-section.tsx
src/components/hero.tsx
src/components/project-modal.tsx
src/content/projects.ts
src/content/site.ts
```

## Product And Website Changes

- Tightened homepage positioning around the full MOTIONX offer: product films, motion-first websites, product launch pages, and campaign content systems.
- Preserved the proof-before-explanation IA: Hero, Studio thesis, Selected Work, MOTIONX System Study, Services, Pilot Callout, Process, Studio, Contact, Footer.
- Strengthened concept-work labeling and public disclosure on both work-detail routes and the project modal.
- Kept both projects explicitly labeled as concept work. No client relationship, commercial result, product-efficacy claim, or commissioned brand work is implied.
- Improved contact behavior and copy so regular inquiries and pilot referrals use distinct subjects while still requiring Charles to send any email manually.
- Polished hero service-note readability and disabled the local Next dev indicator so browser verification screenshots are not obstructed.

## Agentic Workflow Upgrades

- Added `npm run content:check` via `scripts/content-integrity.mjs`.
- Updated `npm run gate` so content-integrity runs before typecheck, lint, build, and e2e.
- Added `npm run browser:verify` via `scripts/browser-verify.mjs`.
- Expanded Playwright coverage for:
  - route health
  - navigation and mobile menu behavior
  - project modal focus/keyboard behavior
  - pilot-to-contact preselection
  - regular vs pilot inquiry subjects
  - public email and private-address integrity
  - no horizontal overflow at mobile widths
  - reduced-motion behavior
  - hero reel poster/playback behavior
- Updated AGENTS, CLAUDE, and README runbooks to document the new gates and verification expectations.

## Content-Integrity Guarantees

Verified by source guard and browser checks:

- Public email remains `hello@madebymotionx.com`.
- Founder direct email and backup Gmail are not exposed in public UI.
- `site.social` remains empty unless a real active profile exists.
- `site.url` remains environment-driven, not hard-coded to an invented domain.
- Both project entries remain `concept: true`.
- Both project entries keep public disclosure text.
- Work pages and modal surfaces show concept disclosures.
- No fake clients, testimonials, awards, press, production credits, offices, team members, statistics, conversion numbers, or social profiles were added.
- Botanical work does not claim product efficacy or a client relationship.

## Validation Evidence

Final local verification commands run on this branch:

```text
npm run content:check
PASS - MOTIONX content-integrity check passed (103 checks).

npm run gate
PASS - content-integrity, typecheck, lint, build, and e2e passed.
PASS - e2e summary: 53 passed, 3 skipped.
NOTE - `next lint` printed the expected Next.js 16 deprecation notice, with no warnings or errors.

python3 .agents/skills/webapp-testing/scripts/with_server.py --server "npm run dev -- -p 3939" --port 3939 --timeout 120 -- npm run browser:verify
PASS - Browser verification passed.
PASS - Desktop/mobile screenshots regenerated.
PASS - Console/page errors, overflow checks, reduced motion, hero playback, and normal-vs-pilot contact subject checks passed.
```

## Browser Screenshot Artifacts

Refreshed local artifacts:

```text
test-results/browser-verify/desktop-home.png
test-results/browser-verify/mobile-home.png
test-results/browser-verify/desktop-pilot.png
test-results/browser-verify/mobile-pilot.png
test-results/browser-verify/desktop-work-renewal.png
test-results/browser-verify/desktop-work-liquid-signal.png
test-results/browser-verify/mobile-work-renewal.png
test-results/browser-verify/mobile-work-liquid-signal.png
test-results/browser-verify/reduced-motion-home.png
```

Screenshots manually inspected for this packet:

- `desktop-home.png`
- `mobile-home.png`
- `desktop-pilot.png`
- `mobile-pilot.png`
- `desktop-work-renewal.png`
- `desktop-work-liquid-signal.png`
- `reduced-motion-home.png`

Observed local result:

- Hero hierarchy and primary CTA are clear on desktop and mobile.
- Pilot page is readable on desktop and mobile.
- Work-detail pages show explicit concept disclosure labels and disclosure body copy.
- Reduced-motion home remains usable and the hero video stays paused on the poster frame.
- No local dev overlay obstructs screenshots.

## Production Comparison Notes

Production URLs inspected read-only:

```text
https://madebymotionx.com/
https://madebymotionx.com/pilot
https://madebymotionx.com/work/renewal
https://madebymotionx.com/work/liquid-signal
```

HTTP status:

```text
200 https://madebymotionx.com/ text/html; charset=utf-8
200 https://madebymotionx.com/pilot text/html; charset=utf-8
200 https://madebymotionx.com/work/renewal text/html; charset=utf-8
200 https://madebymotionx.com/work/liquid-signal text/html; charset=utf-8
```

Read-only production Playwright sweep:

- Desktop and mobile routes returned 200.
- Console/page errors: none.
- Horizontal overflow: 0 on inspected desktop and mobile viewports.
- Public email present: yes.
- Private founder email exposed: no.
- Backup Gmail exposed: no.
- Work routes still label projects as `Concept Project`.

Important live-vs-local differences:

- Production is behind this branch.
- Production home has older hero/service wording and a shorter service note.
- Production work-detail pages identify projects as concept work, but do not show the new explicit `Concept disclosure` label and disclosure body on the detail pages.
- Production does not include the new source-level content-integrity guard, browser-verification script, expanded e2e coverage, or runbook updates.
- Production remains usable and has no obvious runtime blocker, but deployment of this branch improves content-integrity clarity and repeatable verification.

## Deployment Readiness Checklist

- [x] Local release candidate branch confirmed.
- [x] Dirty outreach file confirmed unrelated and excluded.
- [x] `npm run content:check` passed.
- [x] `npm run gate` passed.
- [x] `npm run browser:verify` passed.
- [x] Local screenshots refreshed and inspected.
- [x] Production inspected read-only.
- [x] No secrets, DNS, Vercel settings, billing, IAM, Gmail, or CRM touched.
- [x] No push or deploy performed.
- [ ] Charles final taste review.
- [ ] Charles approval to merge/push/deploy.
- [ ] Post-deploy production verification on `/`, `/pilot`, `/work/renewal`, and `/work/liquid-signal`.

## Deployment Notes

Expected deployment path, after Charles approves:

1. Confirm worktree only has intended release changes plus any unrelated local notes.
2. Merge or fast-forward the website release branch into `main`.
3. Push `main` to GitHub.
4. Let Vercel git integration deploy.
5. Run production verification:

```bash
PLAYWRIGHT_BASE_URL=https://madebymotionx.com npm run test:e2e
```

6. Manually inspect:

```text
https://madebymotionx.com/
https://madebymotionx.com/pilot
https://madebymotionx.com/work/renewal
https://madebymotionx.com/work/liquid-signal
```

Do not change DNS or Vercel project settings for this release.

## Rollback Plan

If deployed through a PR merge:

1. Revert the merge commit on `main`.
2. Push `main`.
3. Let Vercel redeploy the reverted state.
4. Re-run production verification on the four public routes.

If deployed as a fast-forward of this branch:

1. Revert the release commits on `main`, newest first:

```bash
git revert <readiness-doc-commit-if-in-main>
git revert 765301b748ca5fa980080d1793c406bf81a5e40c
git revert 8d27be98d8b73f3d145a1892bdc02253206186e7
```

2. Push `main`.
3. Let Vercel redeploy.
4. Re-run production verification.

Emergency fallback:

- Use Vercel's previous successful deployment rollback/redeploy control only if git revert is too slow for the incident.
- Do not change DNS for this rollback.

## Charles Manual Review Required

- Overall visual taste on desktop and mobile.
- Whether the explicit concept-disclosure presentation feels right for public launch.
- Whether the pilot pricing and bonus language should remain as written.
- Contact form tone and Gmail handoff copy.
- Production post-deploy pass after the branch is actually deployed.

## Intentionally Out Of Scope

- No push.
- No deployment.
- No DNS or Vercel settings changes.
- No secrets, billing, IAM, API keys, or environment changes.
- No Gmail, CRM, or email workflow changes.
- No new clients, testimonials, awards, metrics, locations, press, team members, social links, or proof.
- No relabeling concept work as client work.
- No redesign from scratch.

## Outreach File Note

`outreach/self-improvement.md` is an unrelated outreach operational-notes file. It was present as a dirty working-tree file before this readiness pass, was inspected in earlier MOTIONX work, and is not part of this website release. It must remain untouched, unstaged, and uncommitted for this packet.

