import type { ProjectType } from "./contact";

export type Service = {
  index: string;
  title: string;
  description: string;
  bestFor: string;
  outputs: string[];
  formType: ProjectType;
  cta: string;
};

export const servicesIntro = {
  label: "(04) — Services",
  heading: "What we build, end to end.",
} as const;

export const serviceDetailLabels = {
  bestFor: "Best fit",
  outputs: "Typical outputs",
} as const;

export const services: Service[] = [
  {
    index: "01",
    title: "Product Films",
    description:
      "Motion-led product stories shaped through direction, available assets, sound, and post-production.",
    bestFor:
      "A product with usable footage or product assets that needs one cinematic visual anchor.",
    outputs: [
      "Asset and footage plan",
      "Motion direction and edit",
      "Sound and social cutdown plan",
    ],
    formType: "Product Film",
    cta: "Discuss a product film",
  },
  {
    index: "02",
    title: "Motion-First Websites",
    description:
      "Responsive sites paced around the product’s moving visual language.",
    bestFor:
      "A product brand whose website should carry the same visual language as its launch.",
    outputs: [
      "Responsive launch sections",
      "Motion rules",
      "Conversion path",
    ],
    formType: "Motion-First Website",
    cta: "Discuss a motion-first website",
  },
  {
    index: "03",
    title: "Product Launch Pages",
    description:
      "One focused product story leading to one primary action.",
    bestFor: "One product, one audience, and one primary action.",
    outputs: [
      "Product story flow",
      "CTA hierarchy",
      "Basic SEO metadata",
    ],
    formType: "Product Launch Page",
    cta: "Discuss a launch page",
  },
  {
    index: "04",
    title: "Campaign Content Systems",
    description:
      "Motion, campaign frames, and format rules built from one direction.",
    bestFor:
      "A launch that needs a coherent family of channel-ready assets, whether or not a new film or site is part of the scope.",
    outputs: [
      "Platform-ready motion",
      "Campaign frames",
      "Visual system notes",
    ],
    formType: "Campaign Content System",
    cta: "Discuss a campaign system",
  },
];

/** The film + website pairing is the studio's signature engagement. */
export const servicesLede =
  "Start with one output, or connect film and web under one direction.";

/** The connected film + website engagement is the clearest expression of MOTIONX. */
export const signatureEngagement = {
  label: "Signature engagement",
  title: "Film + Website Launch System",
  formType: "Film + Website Launch System",
  cta: "Discuss the launch system",
} as const;

export type LaunchStage = {
  index: string;
  title: string;
  outputs: string[];
};

export const launchSystemIntro = {
  label: "(03) — MOTIONX System Study",
  conceptLabel: "Concept",
  heading: "One visual idea. Built from film to launch.",
  body: "Not three disconnected services — one creative direction, everywhere the product appears.",
  outputsLabel: "Connected outputs",
} as const;

export const launchSystem: LaunchStage[] = [
  {
    index: "01",
    title: "Product Film",
    outputs: ["Hero film frame", "Lighting and surface language", "Sound and pacing cues"],
  },
  {
    index: "02",
    title: "Motion-First Website",
    outputs: ["Launch-page sections", "Interaction rhythm", "CTA and scroll direction"],
  },
  {
    index: "03",
    title: "Campaign System",
    outputs: ["9:16 and 16:9 cutdowns", "Campaign frames", "Visual system notes"],
  },
];

export const launchSystemCta = {
  label: "Complete system study",
  primary: "View the System Study",
  primaryHref: "/system-study",
} as const;

export type ProcessStep = {
  index: string;
  title: string;
  description: string;
  checkpoint: {
    label: string;
    body: string;
  };
};

export const processIntro = {
  label: "(05) — Process",
  heading: "A clear path, matched to the scope.",
  body: "Four stages; deliverables flex with the selected scope.",
} as const;

export const processSteps: ProcessStep[] = [
  {
    index: "01",
    title: "Discover",
    description:
      "Define the product, audience, goal, assets, and selected outputs.",
    checkpoint: {
      label: "Decision",
      body: "Fixed scope and quote",
    },
  },
  {
    index: "02",
    title: "Direct",
    description:
      "Set the concept, key frames, typography, pacing, and motion rules.",
    checkpoint: {
      label: "Direction",
      body: "One approved visual system",
    },
  },
  {
    index: "03",
    title: "Build",
    description:
      "Produce the selected outputs as one coherent system.",
    checkpoint: {
      label: "Output",
      body: "Film, page, assets, or connected set",
    },
  },
  {
    index: "04",
    title: "Launch",
    description:
      "Test and prepare each output for its intended context.",
    checkpoint: {
      label: "Delivery",
      body: "Platform-ready files; responsive site when included",
    },
  },
];
