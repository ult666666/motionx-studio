# MOTIONX Website Backlog

## Charles Review Needed

- Decide whether the new FAQ tone feels helpful or too explanatory.
- Decide whether the concept-study notes feel persuasive enough for public concept work.
- Review whether quality standards should remain in the Studio section or move closer to Contact.
- Review future service-page appetite and whether MOTIONX has enough real assets to support them.
- Two near-identical launch-system CTAs sit ~1.5 viewports apart ("Discuss a Launch
  System" in the Launch System section, "Discuss the launch system" on the Services
  signature banner). Consider keeping only the signature-banner inquiry.
- Approve the new first-party `/system-study` social card (`public/og/system-study.jpg`,
  regenerate with `npm run og:system-study`) — it now fronts LinkedIn/WhatsApp/iMessage
  previews for that route instead of the shared brand card.
- Review the caption cues in all four `public/captions/*.en.vtt` files (wording
  AND timing). Agentic Trading contains the supplied seven-cue voiceover
  transcript; the other films use conservative, measured non-dialogue cues.
  Automation cannot certify final listening accuracy.
  Existing non-dialogue examples:
  They are deliberately conservative non-dialogue descriptions verified only
  against measured audio activity (silence detection + loudness envelope):
  Renewal — `[Sound design]` 0:00–0:07, `[Sound design continues]` 0:07–0:12,
  `[Sound design fades]` 0:12–0:14.3 (audio measured silent after ~14.36s);
  Liquid Signal — `[Sound design]` 0:00–0:09, `[Sound design continues]`
  0:09–0:12, `[Sound design intensifies]` 0:12–0:14.9 (final segment measured
  ~8.5 dB louder). Listen and adjust before any future re-edit.
- Review mobile video derivatives (`public/videos/*-mobile.<hash>.mp4`) on a real
  phone: Agentic hero 720×1280, Renewal 720×1280, Liquid Signal/FURIA/Agentic
  case films 960×540. Frame comparisons in
  `test-results/media-review/` after any browser-verify run.

## Needs New First-Party Assets

- Behind-the-system process stills for Renewal and Liquid Signal.
- Campaign format mockups derived from each concept project.
- A short founder walkthrough of how a film direction becomes web and campaign assets.
- Real launch-page excerpt or mini case study when a client launch exists.
- Dedicated Open Graph cards for any future service pages or content hubs.

## Future Website Ideas

- `/services/product-films`
- `/services/motion-first-websites`
- `/services/product-launch-pages`
- `/services/campaign-content-systems`
- `/notes/how-a-product-film-becomes-a-launch-page`
- `/notes/responsible-cinematic-video-on-the-web`
- `/work/renewal/breakdown`
- `/work/liquid-signal/breakdown`

## Acceptance Criteria For Future Service Pages

- Distinct thesis and audience per page.
- Concrete scope and deliverables.
- First-party example or visual artifact.
- No invented clients, metrics, testimonials, awards, location, or scarcity.
- Accurate metadata and Open Graph card.
- Included in sitemap and SEO sanity.
- E2E route-health and mobile-overflow coverage.

## Operational Backlog

- **`Website Quality` CI is green as of `356ecf2` (2026-08-12)** — the first
  passing run after nine consecutive failures going back to the workflow's very
  first run. It was never a flake and never a regression from a recent change;
  three separate real defects were failing it, each fixed at the source rather
  than by relaxing an assertion:
  - *Poster-only contract rested on a hint.* `preload="none"` is advisory, and
    CI's WebKit ignores it, so reduced-motion and Save-Data visitors were
    fetching the hero and Renewal mp4s while the element still reported
    `paused`/`currentTime 0`. `useMediaArming` now withholds the `<source>`
    children until playback is permitted — an element with no candidates cannot
    be fetched by any engine. A test asserts the absence directly.
  - *Font fallback only worked where Arial exists.* next/font sources Geist's
    metric-matched fallback from `local("Arial")` alone, so on a stock Linux box
    the ascent/descent/size-adjust overrides were dropped and first paint wrapped
    to a different line count — a genuine font-swap layout shift for those
    visitors. Re-declared over an Arial-compatible source list.
  - *Focus-after-scroll polled frames for a non-frame event.* The `inert` wait
    used a rAF retry against a wall-clock deadline; rAF throttles on a busy page,
    so the budget could expire without ever sampling the release and focus would
    silently never land. Now observes the `inert` mutation directly.
  - Two test ceilings (2s/3s → 8s) were loosened where they asserted *how fast*
    focus lands, which was never the contract. "Lands exactly once" is still
    asserted exactly.
- Branch protection is now unblocked — enable it once Charles has seen a green
  run land on a PR as well as on `main`.
- `npm audit` reports a moderate transitive advisory (postcss < 8.5.10 bundled
  inside next itself; affects every next release through 16.x canaries). Not
  actionable at patch level — revisit when Next ships a release that bumps its
  internal postcss.
- Consider a real contact backend only after documenting delivery ownership, spam handling, privacy expectations, and whether Gmail draft should remain as fallback.
- Add Lighthouse/PageSpeed measurement as a manual release task if performance work becomes a focus.
