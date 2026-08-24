/** Public interface-state copy. Kept out of route components so even failure
 *  states follow the same centralized-content rule as the main site. */
export const interfaceCopy = {
  notFound: {
    eyebrow: "404 — Not Found",
    heading: "This frame doesn’t exist.",
    body: "The page you’re looking for was moved, renamed, or never made the final cut.",
    primary: "Back to the studio",
    secondary: "View Selected Work",
    /** Mono edit-suite status line — decorative telemetry, no claims. */
    statusLine: "NO SIGNAL · 404",
  },
  error: {
    eyebrow: "Playback interrupted",
    heading: "This page missed its cue.",
    body: "The page couldn’t finish loading. Run the scene again, or head back to the studio.",
    retry: "Try again",
    home: "Return to the studio",
    contact: "Contact MOTIONX",
    /** Mono edit-suite status line — decorative telemetry, no claims. */
    statusLine: "PLAYBACK INTERRUPTED",
  },
  media: {
    /** Shown over the poster when a film's source fails to load. Kept short
     *  so the pill never wraps inside the portrait card. */
    unavailable: "Video unavailable",
    /** Prefix for the edit-suite timecode chip; the MM:SS values themselves
     *  are computed from real playback time. */
    timecodeLabel: "TC",
  },
} as const;
