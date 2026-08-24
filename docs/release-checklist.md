# MOTIONX Release Checklist

## Before Commit

- [ ] Confirm branch and HEAD.
- [ ] Confirm dirty unrelated files are not staged.
- [ ] Confirm `outreach/self-improvement.md` is untouched and unstaged.
- [ ] Confirm root `hf_2026*.mp4` masters were not modified.
- [ ] Run `npm run content:check`.
- [ ] Run `npm run assets:check`.
- [ ] Run `npm run seo:check`.
- [ ] Run `npm run gate`.
- [ ] Run `npm run browser:verify` against local preview.
- [ ] Inspect desktop/mobile screenshots, long-page captures, and `evidence.json`
      (`serverMode` is DETECTED from the served artifact's build marker;
      `PLAYWRIGHT_PRODUCTION=1` makes the run fail if a dev build is detected).
- [ ] Run `npm run metadata:check` against the production build (the gate runs it
      automatically after `next build`) — route metadata matrix, 404 isolation,
      sitemap/robots contracts.
- [ ] If `/system-study` visuals or copy changed, regenerate its social card with
      `npm run og:system-study` and re-inspect the JPEG.
- [ ] Confirm no fake proof, no private emails, no unsupported health claims, and no weakened concept labels.

## Before Push or Deploy

Only after Charles explicitly approves:

- [ ] Review final diff.
- [ ] Confirm no secrets, DNS, Vercel settings, Gmail, CRM, or outreach automation changes.
- [ ] Confirm no service pages were added without real content depth.
- [ ] Confirm the read-only `Website Quality` GitHub check is green.
- [ ] Push only the intended branch/commit set.
- [ ] Let Vercel deploy from git integration if approved.

## Post-Deploy Verification

- [ ] `https://madebymotionx.com/`
- [ ] `https://madebymotionx.com/pilot`
- [ ] `https://madebymotionx.com/system-study`
- [ ] `https://madebymotionx.com/work/renewal`
- [ ] `https://madebymotionx.com/work/liquid-signal`
- [ ] `https://madebymotionx.com/work/furia`
- [ ] `https://madebymotionx.com/work/agentic-trading`
- [ ] `PLAYWRIGHT_BASE_URL=https://madebymotionx.com npm run test:e2e`
- [ ] `PLAYWRIGHT_BASE_URL=https://madebymotionx.com npm run browser:verify`
- [ ] Curl 200 checks for all public routes.
- [ ] Screenshot inspection on desktop and mobile.

## Always Out Of Scope Unless Explicitly Requested

- DNS
- Vercel settings
- Cloudflare
- secrets and env files
- billing/IAM/API keys
- Gmail/CRM
- deployment automation
- outreach workflow edits
