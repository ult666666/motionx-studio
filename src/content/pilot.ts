import type { ProjectType } from "./contact";

/**
 * ─────────────────────────────────────────────────────────────────────────
 *  MOTIONX — PILOT LAUNCH OFFERS
 * ─────────────────────────────────────────────────────────────────────────
 *  Introductory pilot pricing. EDIT PRICES HERE — the /pilot page
 *  and the home-page callout both read from this file.
 *
 *  A base offer's `formType` must match one of the contact form's project-type
 *  options so its CTA can pre-select the right package. The referral-only add-on
 *  has no form type. `getPilotInquiryHref` also adds the base offer id as explicit
 *  pilot intent (see contact-form.tsx).
 * ─────────────────────────────────────────────────────────────────────────
 */

export type UsdPrice = `$${string}`;

type PilotScope = {
  id: string;
  title: string;
  deliverable: string;
  /** One short line on who the offer is for. */
  audience?: string;
  /** Bulleted inclusions (optional). */
  includes?: string[];
  originalPrice: UsdPrice;
  pilotPrice: UsdPrice;
  /** Small editorial label, e.g. "Signature engagement" or "Add-on". */
  label?: string;
  /** A factual included-extra note shown in the scope column (optional). */
  bonus?: string;
  /** Give the studio's signature connected engagement more visual space. */
  featured?: boolean;
};

/** A selectable pilot package. Only base packages own a contact-form type. */
export type PilotBaseOffer = PilotScope & {
  /** Pre-selects this value in the contact form when the CTA is used. */
  formType: ProjectType;
};

/** The campaign extension is referral-only and can never masquerade as a base. */
export type PilotAddOnOffer = PilotScope & {
  formType?: never;
};

export const CAMPAIGN_ADD_ON_ID = "campaign-add-on";

export const pilotAddOnCopy = {
  marker: "ADD",
  selectorLabel: "Build the paired scope",
  selectorLegend: "Choose the base package",
  selectorHint:
    "The campaign add-on extends one pilot package — choose a base so both stay on the same inquiry.",
  selectedLabel: "Selected base",
  combinedTotalLabel: "Base + add-on total",
  readyCta: "Continue with base + add-on",
  disabledCta: "Choose a base package first",
  handoffNote: "Both scopes stay visible in your contact brief.",
};

export const pilotReferralCopy = {
  selectedLabel: "Selected pilot",
  baseLabel: "Base package",
  addOnLabel: "Add-on",
  draftBaseLabel: "Pilot package",
  draftAddOnLabel: "Add-on",
};

export const pilotMeta = {
  eyebrow: "Pilot Launch · Introductory Rates",
  heading: "Introductory pilot pricing, clearly scoped.",
  primaryCta: "Review Pilot Scope",
  intro:
    "Introductory rates while the studio builds its portfolio. Every inquiry is read personally, scoped to the actual launch, and quoted before production begins.",
  packagesLabel: "Production slate",
  packagesHeading: "Choose the closest starting scope.",
  packagesIntro:
    "Clear starting points, not one-size-fits-all promises. The final quote follows your product, deliverables, and timeline.",
  detailGroups: [
    {
      title: "What is not included",
      items: [
        "Ad spend, media buying, influencer outreach, or ongoing channel management.",
        "On-location camera crews or travel unless they are discussed and scoped separately.",
        "Unsupported product claims, regulated claims, or legal/compliance review.",
        "Backend contact automation unless it is separately scoped after the pilot.",
      ],
    },
    {
      title: "What happens next",
      items: [
        "Choose the closest package and continue to the contact form.",
        "Your inquiry opens as a Gmail draft for you to review and send.",
        "Charles replies personally with scope questions and a fixed quote.",
      ],
    },
  ],
  termsLabel: "Pilot terms",
  termsHeading: "Introductory rate. Professional scope.",
  termsLines: [
    "A focused launch consultation is included before scope is finalized.",
    "Only the deliverables listed in the selected package are included; additions are quoted separately.",
    "Product-film work is remote-first; any live-action capture or travel must be agreed separately.",
  ],
  disclaimer:
    "Pilot pricing is introductory and final scope may affect the quoted price.",
};

/** Home-page callout linking to /pilot. Copy lives here (not hard-coded in the
 *  component) so it stays in sync with the offer terms above. */
export const pilotCallout = {
  label: "Pilot Pricing",
  heading: "A focused way to start with MOTIONX.",
  cta: "View Pilot Offers",
};

export const pilotBaseOffers = [
  {
    id: "product-film",
    title: "Product Film",
    deliverable: "15–20 second motion-design-led product film",
    audience: "For one product with usable footage or assets and one focused launch moment.",
    originalPrice: "$699",
    pilotPrice: "$399",
    bonus: "One social cutdown included",
    formType: "Product Film",
  },
  {
    id: "motion-first-website",
    title: "Motion-First Website",
    deliverable: "Custom responsive one-page launch website",
    audience: "For a launch that needs a real site, not a template.",
    includes: [
      "Responsive design",
      "CTA setup",
      "Basic deployment",
      "Basic SEO & metadata",
    ],
    originalPrice: "$1,290",
    pilotPrice: "$699",
    formType: "Motion-First Website",
  },
  {
    id: "launch-system",
    title: "Film + Website Launch System",
    deliverable: "The complete connected launch — film, site, and direction",
    audience: "For a serious launch where the film and site must feel like one.",
    includes: [
      "15–20 second product film",
      "Motion-first launch website",
      "Connected visual direction",
      "Responsive deployment",
      "One social cutdown",
    ],
    originalPrice: "$1,990",
    pilotPrice: "$999",
    label: "Signature engagement",
    featured: true,
    formType: "Film + Website Launch System",
  },
] satisfies PilotBaseOffer[];

/** Base-only alias used by contact referral resolution. */
export const pilotOffers = pilotBaseOffers;

export const campaignAddOnOffer = {
  id: CAMPAIGN_ADD_ON_ID,
  title: "Campaign Content Add-On",
  deliverable: "Social cutdowns, platform variations, and launch assets",
  audience: "Add platform-ready cuts to any package above.",
  originalPrice: "$390",
  pilotPrice: "$190",
  label: "Add-on",
} satisfies PilotAddOnOffer;

/** One comparison list: the core deliverable first, then every factual extra. */
export function getPilotIncludedScope(offer: PilotBaseOffer): string[] {
  return [
    offer.deliverable,
    ...(offer.includes ?? []),
    ...(offer.bonus ? [offer.bonus] : []),
  ];
}

const wholeUsd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

function parseWholeUsd(price: UsdPrice): number {
  if (!/^\$\d{1,3}(?:,\d{3})*$/.test(price)) {
    throw new Error(`Invalid whole-dollar pilot price: ${price}`);
  }
  return Number(price.slice(1).replaceAll(",", ""));
}

/** Exact display total derived from the two centralized pilot price strings. */
export function getPilotAddOnTotal(
  baseOffer: Pick<PilotBaseOffer, "pilotPrice">,
  addOn: Pick<PilotAddOnOffer, "pilotPrice"> = campaignAddOnOffer,
): string {
  return wholeUsd.format(
    parseWholeUsd(baseOffer.pilotPrice) + parseWholeUsd(addOn.pilotPrice),
  );
}

/**
 * Pilot intent is explicit rather than inferred from `type` alone. General
 * service and case-study CTAs can share the same project type without
 * accidentally inheriting pilot pricing or a pilot email subject.
 */
export function getPilotInquiryHref(
  offer: Pick<PilotBaseOffer, "id" | "formType">,
) {
  const params = new URLSearchParams({
    type: offer.formType,
    pilot: offer.id,
  });
  return `/?${params.toString()}#contact`;
}

export function getPilotAddOnInquiryHref(
  baseOffer: Pick<PilotBaseOffer, "id" | "formType">,
) {
  const canonicalBase = pilotBaseOffers.find(
    (offer) =>
      offer.id === baseOffer.id && offer.formType === baseOffer.formType,
  );
  if (!canonicalBase) {
    throw new Error("A campaign add-on inquiry requires a base pilot offer.");
  }

  const params = new URLSearchParams({
    type: canonicalBase.formType,
    pilot: canonicalBase.id,
    addon: CAMPAIGN_ADD_ON_ID,
  });
  return `/?${params.toString()}#contact`;
}

export type PilotReferral = {
  baseOffer: PilotBaseOffer;
  addOn: PilotAddOnOffer | null;
};

/**
 * Resolve only an exact, truthful pilot referral. The add-on is never accepted
 * as a standalone package, and any duplicate, unknown, or unpaired add-on
 * marker rejects the complete pilot context rather than guessing intent.
 */
export function getPilotReferralFromParams(
  params: URLSearchParams,
): PilotReferral | null {
  const types = params.getAll("type");
  const pilotIds = params.getAll("pilot");
  const addOnIds = params.getAll("addon");

  if (types.length !== 1 || pilotIds.length !== 1 || addOnIds.length > 1) {
    return null;
  }

  const baseOffer = pilotBaseOffers.find(
    (offer) => offer.id === pilotIds[0] && offer.formType === types[0],
  );
  if (!baseOffer) return null;

  if (addOnIds.length === 0) {
    return { baseOffer, addOn: null };
  }

  if (addOnIds[0] !== CAMPAIGN_ADD_ON_ID) {
    return null;
  }

  return { baseOffer, addOn: campaignAddOnOffer };
}
