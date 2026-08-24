/**
 * Client-safe media-delivery configuration. The site ships each film as an
 * ordered source ladder — a smaller mobile derivative selected natively by the
 * browser through `<source media>`, then the approved full-resolution web copy
 * as the fallback — so no JavaScript viewport branching is involved and the
 * choice is made once at load time.
 *
 * Mobile derivatives are re-encoded from the approved public web copies (never
 * from the `hf_2026*` masters) and preserve the exact edit and footage
 * exclusions. `scripts/asset-integrity.mjs` enforces their stream contracts.
 */

/** Browsers matching this condition get the mobile derivative. 768px and up
 *  (tablet/desktop) keep the full-resolution web copy. */
export const MOBILE_MEDIA_CONDITION = "(max-width: 767px)";

/**
 * The hero's silent Agentic Trading concept teaser (no audio track by design —
 * no captions). The mobile source is a purpose-built 9:16 reframe of the same
 * approved beats; the full narrated film remains a separate portfolio asset.
 */
export const heroReelMedia = {
  src: "/videos/agentic-trading-hero.7dfc19e34a48.mp4",
  mobileSrc: "/videos/agentic-trading-hero-mobile.971b3f3dde67.mp4",
  poster: "/posters/agentic-trading-hero.2b41aa4ef05c.webp",
  mobilePoster: "/posters/agentic-trading-hero-mobile.850d5c58d577.webp",
  width: 1920,
  height: 1080,
} as const;
