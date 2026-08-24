# MOTIONX Performance Budgets

## Core Web Vitals Targets

Use these as release-review targets:

- LCP: 2.5 seconds or less
- INP: 200 milliseconds or less
- CLS: 0.1 or less

Source: `https://web.dev/articles/vitals`

## Video Budgets

- Agentic hero teaser stays poster-first and `preload="none"`.
- Hero teaser targets: under 3 MiB desktop and 1.2 MB mobile.
- Public portfolio derivative target: under 16 MiB each.
- Mobile viewports (≤767px) receive dedicated derivatives via the native
  `<source media>` ladder (no JS viewport branching): hero 720x1280 ≤ 1.2 MB,
  Renewal 720x1280 ≤ 2.5 MB, Liquid Signal 960x540 ≤ 4.5 MB, FURIA 960x540
  ≤ 5.0 MB, and Agentic Trading 960x540 ≤ 5.0 MiB. Combined worst-case
  sequential homepage media is 14.96 MiB on mobile against 48.78 MiB on
  desktop (−69.3%). These totals assume a visitor deliberately switches through
  every film; the page mounts only one portfolio player at a time.
- FURIA carries the largest ceiling because it runs 30s — twice the other
  films — at a *lower* bitrate than either (1.3 Mbps mobile, 4.0 Mbps desktop).
  Length, not quality, is what moved the number. These are worst-case totals,
  not load cost: every portfolio clip is poster-first at `preload="none"`, and
  reduced-motion and Save-Data visitors fetch no MP4 at all.
- If every ladder candidate fails, the player shows the accessible
  "Video unavailable" state; a single failed candidate falls through silently.
- Portfolio pages may use `preload="metadata"` for the actual work video.
- Reduced-motion users stay on poster unless they explicitly interact.
- Data-saver users stay on poster.
- Browser verification must observe zero portfolio MP4 requests before explicit play
  in both reduced-motion and Save-Data modes, then observe the selected request after play.
- The e2e gate also asserts the zero-MP4 network contract directly (reduced-motion and
  Save-Data home tests), so this policy is enforced on every gate run, not only in the
  manual browser-verify pass.
- Do not reference root `hf_2026*.mp4` masters in public UI.

Source: `https://web.dev/learn/performance/video-performance`

## Layout Stability

- Preserve explicit video width/height and aspect-ratio containers.
- Keep poster images present for all video surfaces.
- Avoid dynamic content that changes fixed-format UI dimensions after load.
- Browser verification must check mobile horizontal overflow.

## Release Checks

Required before declaring visual changes done:

```bash
npm run gate
npm run browser:verify
```

Inspect `test-results/browser-verify/evidence.json` and the desktop/mobile long-page
captures in addition to the command exit status. `evidence.json` records `serverMode`
as DETECTED from the rendered artifact's build marker (`<body data-motionx-env>`),
not from a caller label; `PLAYWRIGHT_PRODUCTION=1` is an expectation that fails
the run if the served artifact is a development build. The `Website Quality` CI workflow runs the same pass against
the gate's production build and uploads the evidence as an artifact.

Also available individually:

```bash
npm run assets:check
npm run seo:check
npm run content:check
```
