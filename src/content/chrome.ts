/**
 * Client-safe site chrome — the few public values needed by always-hydrated
 * UI (navigation, error boundary). Client components import THIS module, never
 * the full `site` object: a broad client import serializes every string in
 * `site.ts` into shared browser chunks, which is how a non-public address once
 * leaked into public JavaScript. `site.ts` composes these same values back
 * into the central `site` surface for server code, so nothing is duplicated.
 */

export const brandName = "MOTIONX";

export const availabilityLabel = "Available Worldwide";

const workLink = { label: "Work", href: "/#work" } as const;
const servicesLink = { label: "Services", href: "/#services" } as const;
const processLink = { label: "Process", href: "/#process" } as const;
const studioLink = { label: "Studio", href: "/#studio" } as const;
const pilotLink = { label: "Pilot", href: "/pilot" } as const;

/** Concise primary navigation. Home-section links are absolute so they also
 *  work from /pilot, /system-study, and /work/[slug]. Process and Studio stay
 *  available in the footer without competing with the header's core choices. */
export const navLinks = [workLink, servicesLink, pilotLink] as const;

/** Complete secondary navigation for the footer. */
export const footerNavLinks = [
  workLink,
  servicesLink,
  processLink,
  studioLink,
  pilotLink,
] as const;

export const primaryCtaLabel = "Start a Project";

/** Desktop-header HUD readout for the active section. The (0n) indices
 *  mirror the homepage section eyebrows in site.ts / services.ts /
 *  projects.ts — keep both in sync if sections are ever reordered. Keys are
 *  the nav `activeHref` values; anything unlisted falls back to the
 *  availability line as the idle status. */
export const sectionReadout: Readonly<Record<string, string>> = {
  "/#work": "(02) — Work",
  "/#services": "(04) — Services",
  "/pilot": "Pilot — Introductory rates",
};

export const footerTagline =
  "Product Films · Motion-First Websites · Launch Pages · Campaign Systems";
