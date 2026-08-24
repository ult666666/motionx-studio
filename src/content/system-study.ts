/**
 * MOTIONX SYSTEM STUDY — a self-owned, clearly labeled concept used to prove
 * how one visual direction can travel from a film frame into web and campaign
 * formats. It is not client work and makes no commercial-result claim.
 */

export type SystemStudyStage = {
  index: string;
  title: string;
  description: string;
  carries: string[];
  visual: "film" | "website" | "campaign";
};

export const systemStudy = {
  slug: "system-study",
  name: "AURA",
  eyebrow: "MOTIONX System Study",
  title: "One visual world, tested across the launch.",
  metaDescription:
    "A self-initiated MOTIONX concept study showing one visual direction across a product-film frame, responsive launch page, and campaign formats.",
  intro:
    "A self-owned concept study: chrome, electric light, ivory type, and controlled motion, held coherent from film frame to responsive page to campaign formats.",
  disclosure:
    "Self-initiated concept study. AURA is not a real client or commercial product, and no launch result, customer relationship, or product claim is implied.",
  prototype: {
    label: "Responsive HTML/CSS prototype",
    chromeLabel: "AURA · responsive concept",
    navigationLabel: "AURA concept",
    breakdownLabel: "System breakdown",
    conceptLabel: "AURA · Concept study",
    interactionLabel: "Inspect the page logic",
    activeLabel: "Active principle",
    headline: "Designed to be seen.",
    body: "A live page built from the same surfaces, contrast, and pacing as the film frame.",
    cta: "Explore the breakdown",
    principles: [
      {
        label: "Focal hierarchy",
        body: "One object, one headline, and one clear first action.",
      },
      {
        label: "Responsive translation",
        body: "The same visual order holds as the composition narrows.",
      },
      {
        label: "Single-action path",
        body: "The page reveals the breakdown without competing routes.",
      },
    ],
  },
  stages: [
    {
      index: "01",
      title: "Film-frame direction",
      description:
        "A cinematic frame establishes the reflective object, electric rim light, dark atmosphere, and deliberate focal hierarchy.",
      carries: ["Chrome surface language", "Blue-magenta light", "Measured visual pace"],
      visual: "film",
    },
    {
      index: "02",
      title: "Responsive launch page",
      description:
        "The same world becomes real HTML and CSS: restrained chrome, large ivory type, focused navigation, and one clear action path.",
      carries: ["Responsive composition", "CTA hierarchy", "Motion-ready page rhythm"],
      visual: "website",
    },
    {
      index: "03",
      title: "Campaign format system",
      description:
        "The same object, type, and light travel across vertical, square, and wide placements without changing direction.",
      carries: ["9:16 social frame", "1:1 campaign tile", "Wide launch banner"],
      visual: "campaign",
    },
  ] satisfies SystemStudyStage[],
  method: {
    label: "What this proves",
    heading: "The value is continuity, not asset count.",
    body: "The study is intentionally small — one object, one lighting system, one type hierarchy — to show a launch can expand across formats without being redesigned at every handoff.",
  },
  cta: {
    eyebrow: "Build the real launch",
    heading: "Have one product that needs one clear visual direction?",
    body: "Share the product, the audience, and the launch moment — MOTIONX scopes the film, page, or connected system around it.",
    primary: "Discuss a Launch System",
    formType: "Film + Website Launch System",
    secondary: "View Pilot Offers",
    secondaryHref: "/pilot#launch-system",
  },
} as const;
