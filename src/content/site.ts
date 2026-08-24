/**
 * ─────────────────────────────────────────────────────────────────────────
 *  MOTIONX — CENTRAL SITE CONFIGURATION
 * ─────────────────────────────────────────────────────────────────────────
 *  Single source of truth for all editable company information. Change brand
 *  name, contact, navigation and reusable copy HERE — components read from
 *  this file so you never have to hunt through markup.
 *
 *  ▸ `contact.email` drives the contact section, footer, Gmail compose and
 *    mailto fallback.
 *  ▸ `social` is intentionally EMPTY. Add { label, href } objects only when a
 *    real, active profile exists — the UI renders it conditionally and hides
 *    the row entirely while the array is empty.
 *  ▸ `url` comes from NEXT_PUBLIC_SITE_URL (set it in production), falling back
 *    to http://localhost:3000 in development. No invented domain is hard-coded.
 *  ▸ Everything here is plain data, safe to expose to the browser (no secrets).
 * ─────────────────────────────────────────────────────────────────────────
 */

import {
  availabilityLabel,
  brandName,
  footerNavLinks,
  footerTagline,
  navLinks,
  primaryCtaLabel,
} from "./chrome";

export type SocialLink = { label: string; href: string };

const founder = "Charles Dai";

export const site = {
  name: brandName,
  founder,
  availability: availabilityLabel,

  /** Production base URL — set NEXT_PUBLIC_SITE_URL when you have a domain.
   *  Normalized to a clean origin so a trailing slash (or stray path) in the
   *  deploy environment can never produce doubled separators in canonical,
   *  OG, JSON-LD, robots, or sitemap URLs. */
  url: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").origin,
  tagline: "Product Films & Motion-First Websites",
  positioning:
    "A motion-first creative studio building product films, motion-first websites, launch pages, and campaign systems.",
  description:
    "MOTIONX creates cinematic product films, motion-first websites, product launch pages, and campaign content systems for ambitious products and brands.",

  /** CONTACT
   *  `email` — the PUBLIC address shown on the site + used by the contact form,
   *  Gmail compose and mailto. It is the alias that forwards to the founder
   *  mailbox. Only public values may live in this file: `site` is serialized
   *  into build artifacts, and the post-build privacy guard fails the gate if
   *  a non-public address reaches them. Operational addresses are documented
   *  in CLAUDE.md (never shipped), not here.
   */
  contact: {
    email: "hello@madebymotionx.com",
  },

  /** SOCIAL — empty by design. Add real profiles only; UI hides when empty. */
  social: [] as ReadonlyArray<SocialLink>,

  /** Primary navigation + header CTA label live in ./chrome (client-safe)
   *  and are re-exposed here so server code keeps one `site` surface. */
  nav: navLinks,
  footerNav: footerNavLinks,

  cta: {
    primary: primaryCtaLabel,
    secondary: "View Selected Work",
  },

  hero: {
    eyebrow: "MOTION-FIRST CREATIVE STUDIO",
    /** Rendered as two deliberate lines in the component. */
    headlineLines: ["From first frame", "to final click."],
    sub: "We create the cinematic product film, then carry the same visual world into the website, launch page, and campaign system around it.",
    screening: {
      label: "Now screening",
      title: "Agentic Trading",
      href: "/work/agentic-trading",
      linkLabel: "Open the Agentic Trading case study",
      status: "Self-initiated concept film",
      disclosure:
        "Fictional system and market data. No live trading product, performance result, or financial advice is implied.",
    },
  },

  studioIntro: {
    /** Numbered section eyebrow — keep the (0n) scheme in sync across sections. */
    label: "(01) — Studio",
    /** Rendered as two masked lines in the component — keep the line breaks
     *  intentional (they control the headline's shape). */
    statementLines: [
      "One visual direction.",
      "Across key launch surfaces.",
    ],
    /** Who the studio is for — named plainly so the right visitor knows it's
     *  for them within the first screens. */
    audienceLabel: "Made for",
    audience:
      "Founders and independent brands across consumer products, beauty and wellness, and lifestyle.",
  },

  studio: {
    /** Numbered section eyebrow — keep the (0n) scheme in sync across sections. */
    label: "(06) — Studio",
    /** Rendered as a deliberate two-line brand statement in the component. */
    headingLines: ["Small studio.", "Large visual impact."],
    body: "MOTIONX is an independent studio led by Charles Dai. Film, sound, design, and frontend — one direction from first frame to launch.",
    note: "Remote-first and deliberately focused; an on-location camera crew or recurring travel is not a standard MOTIONX service.",
    /** Honest studio facts only — no invented team, location, or credentials. */
    facts: [
      { label: "Led by", value: founder },
      { label: "Discipline", value: "Motion Design + Frontend" },
      { label: "Delivery", value: "Remote-first" },
    ],
    standardsLabel: "Quality standards",
  },

  trustStandards: [
    {
      label: "Clear provenance",
      body: "Self-initiated work is labeled as concept work, so what it is — and isn’t — stays clear.",
    },
    {
      label: "Founder-led delivery",
      body: "Charles directs and builds every engagement — decisions and execution never change hands.",
    },
    {
      label: "Accessible motion",
      body: "Motion respects reduced-motion and data-saver preferences, with poster fallbacks where they matter.",
    },
    {
      label: "Defined scope",
      body: "One short scope conversation sets the outputs and a fixed quote before production begins.",
    },
  ],

  faq: [
    {
      question: "Can I start with one service?",
      answer:
        "Yes. A product film, motion-first website, launch page, or campaign system can each be scoped on its own. Film and website together remain the studio’s signature engagement.",
    },
    {
      question: "Is the work shown client work?",
      answer:
        "The current portfolio pieces and AURA System Study are self-initiated concept work. They demonstrate the studio’s direction and craft without implying a client relationship or commercial result.",
    },
    {
      question: "Does MOTIONX provide on-location filming?",
      answer:
        "MOTIONX is a remote-first motion-design and web studio, not an on-location camera crew. Product films are built around available footage, product assets, motion design, sound, and post-production. Live-action capture or travel must be discussed and arranged separately before scope is agreed.",
    },
  ],

  closing: {
    headline: "Let’s build your launch.",
    body: "Tell us what you’re launching, who it’s for, and what you need. Charles replies personally.",
  },

  /** Post-submit expectations shown beside the contact form. Honest process
   *  copy only — never claim a message was sent. */
  contactNext: {
    label: "What happens next",
    summary: "A short scope call confirms the selected outputs and fixed quote.",
  },

  /** Mono header strip above the contact form — edit-suite framing, factual
   *  values only (label + the real availability line). */
  contactBrief: {
    label: "Project brief",
  },

  footerTagline,
} as const;

export type Site = typeof site;

/** True when at least one real social profile is configured. */
export const hasSocial = site.social.length > 0;
