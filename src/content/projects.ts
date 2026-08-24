import type { ProjectType } from "./contact";

/**
 * PROJECTS — portfolio case studies.
 *
 * Every entry is clearly labelled as a CONCEPT PROJECT. Do not add fake client
 * names, commercial results, quotes, or production credits here.
 *
 * To swap a video: replace the file in /public/videos and update `video`,
 * `poster`, `width`, `height`, and `orientation` below.
 */

export type Project = {
  slug: string;
  title: string;
  index: string;
  category: string;
  concept: boolean;
  duration: string;
  /** Real film length in whole seconds (matches the published web copies —
   *  probed, not invented). Feeds the edit-suite TRT readouts. */
  durationSeconds: number;
  orientation: "portrait" | "landscape";
  width: number;
  height: number;
  video: string;
  /** Smaller derivative for mobile viewports — selected natively through the
   *  `<source media>` ladder (see src/content/media.ts). Re-encoded from the
   *  approved web copy, same edit, same footage exclusions. */
  videoMobile: string;
  poster: string;
  /** Truthful English WebVTT captions for the film's audible content. Use an
   *  exact transcript where speech exists and conservative descriptions for
   *  verified non-dialogue sound; wording/timing stays subject to Charles's
   *  review (see docs/asset-integrity.md). */
  captions: string;
  /** Optional editorial still used only on the full case-study route. All
   *  visible copy stays centralized here, and the mobile derivative preserves
   *  the same composition at a smaller transfer size. */
  artFrame?: {
    src: string;
    mobileSrc: string;
    width: number;
    height: number;
    alt: string;
    label: string;
    caption: string;
  };
  /** light accents bled into the section, per visual world */
  accent: string;
  /** One line on what this concept piece demonstrates to a prospective client. */
  demonstrates: string;
  /** Public disclosure that protects concept-work integrity. */
  disclosure: string;
  /** Concise, concept-forward description for search and social previews. */
  metaDescription: string;
  /** Contextual conversion path shown only after the project proof. */
  inquiry: {
    /** Must match a project type in the contact form. */
    formType: ProjectType;
    eyebrow: string;
    heading: string;
    body: string;
    cta: string;
  };
  summary: string;
  objective: string;
  approach: string;
  deliverables: string[];
  conceptStudyNotes: {
    title: string;
    body: string;
  }[];
  tags: string[];
};

export const selectedWorkIntro = {
  label: "(02) — Selected Work",
  heading: "Selected Work",
  body: "Four self-initiated concept studies.",
  caseStudyCta: "View full case study",
} as const;

export const projects: Project[] = [
  {
    slug: "renewal",
    title: "Renewal",
    index: "01",
    category: "Product Film · Botanical Visual Direction · Concept Project",
    concept: true,
    duration: "15 seconds",
    durationSeconds: 15,
    orientation: "portrait",
    width: 1080,
    height: 1920,
    video: "/videos/renewal-botanical.d503303f4c24.mp4",
    videoMobile: "/videos/renewal-botanical-mobile.5bbade5a0a0e.mp4",
    poster: "/posters/renewal.2f7a5aad01b8.webp",
    captions: "/captions/renewal-botanical.e611670510fd.en.vtt",
    accent: "#C7A24B",
    demonstrates:
      "How a product film sets a calm, premium mood before a single word is said.",
    disclosure:
      "Self-initiated concept study. No client relationship, commercial result, or product-efficacy claim is implied.",
    metaDescription:
      "Self-initiated MOTIONX concept study—no client relationship or commercial result implied—exploring a warm, sensory botanical product film.",
    inquiry: {
      formType: "Product Film",
      eyebrow: "For your product",
      heading: "Build a product world people can feel.",
      body: "Tell MOTIONX what you’re launching, who it needs to reach, and the mood the film should carry.",
      cta: "Start a product film",
    },
    summary:
      "A warm, sensory product film: botanical ingredients, luminous imagery, and a feeling of natural renewal.",
    objective:
      "Give a botanical product a calm, premium presence — natural light, glass, and golden liquid carry the story. No hard sell.",
    approach:
      "Soft directional lighting, organic green-and-gold grading, and slow, deliberate camera moves. Reflective surfaces and shallow depth keep the product luminous and the mood unhurried.",
    deliverables: [
      "Vertical 9:16 master",
      "Social-ready cutdowns",
      "Product hero frames",
      "Color & sound treatment",
    ],
    conceptStudyNotes: [
      {
        title: "What this concept demonstrates",
        body: "A quiet product world can feel premium before copy has to explain anything: light, texture, pacing, and sound carry the first impression.",
      },
      {
        title: "System thinking",
        body: "The warm botanical palette, soft reflections, and slow camera language could extend into a landing page, detail crops, and social frames without changing direction.",
      },
      {
        title: "Film-to-page extension",
        body: "The film suggests a page paced by calm reveals, large product frames, quiet interface chrome, and one clear CTA.",
      },
      {
        title: "Campaign extension potential",
        body: "The same world could support short cutdowns, launch stills, ingredient-style frames, and quiet product hero loops.",
      },
      {
        title: "What is concept vs real",
        body: "This is a self-authored visual study. It does not imply a client relationship, commercial result, product efficacy, or endorsement from any real product shown.",
      },
    ],
    tags: [
      "Art Direction",
      "Product Visualization",
      "AI-Assisted Production",
      "Motion Design",
      "Sound Design",
    ],
  },
  {
    slug: "liquid-signal",
    title: "Liquid Signal",
    index: "02",
    category: "Motion Identity · 3D Visual Exploration · Concept Project",
    concept: true,
    duration: "15 seconds",
    durationSeconds: 15,
    orientation: "landscape",
    width: 1920,
    height: 1080,
    video: "/videos/liquid-signal.c24f676131a6.mp4",
    videoMobile: "/videos/liquid-signal-mobile.499b4ad7198a.mp4",
    poster: "/posters/liquid-signal.cdfb416c6c9d.webp",
    captions: "/captions/liquid-signal.34ac9c980cef.en.vtt",
    accent: "#6D7CFF",
    demonstrates:
      "How a motion identity can be designed to interrupt a feed and resolve into a confident brand moment.",
    disclosure:
      "Self-initiated concept study. No client relationship, commercial result, or commissioned brand work is implied.",
    metaDescription:
      "Self-initiated MOTIONX concept study—no client relationship or commercial result implied—exploring liquid metal, kinetic type, and motion identity.",
    inquiry: {
      formType: "Film + Website Launch System",
      eyebrow: "For your launch",
      heading: "Carry one motion language across the whole launch.",
      body: "Tell MOTIONX what you’re launching and where the visual system needs to work — film, web, and campaign.",
      cta: "Start a launch system",
    },
    summary:
      "An electric motion study — liquid metal, refractive glass, kinetic type, and a high-impact brand reveal.",
    objective:
      "Explore a motion identity with maximum kinetic energy — a reveal designed to interrupt a feed and resolve into a confident metallic logo lockup.",
    approach:
      "Liquid-chrome simulation, refractive glass, and electric blue-magenta lighting drive toward a crystalline build-up before resolving into a polished metallic wordmark.",
    deliverables: [
      "Horizontal 16:9 master",
      "Logo reveal sting",
      "Looping identity bumper",
      "Color & sound treatment",
    ],
    conceptStudyNotes: [
      {
        title: "What this concept demonstrates",
        body: "A motion identity can create impact first, then resolve into a confident brand moment that feels built for launch surfaces.",
      },
      {
        title: "System thinking",
        body: "Chrome, refraction, electric blue, magenta, and kinetic type form a compact visual language that can move across film, web, and campaign formats.",
      },
      {
        title: "Film-to-page extension",
        body: "The energy suggests a launch page with dark cinematic framing, sharp type transitions, controlled glow, and interaction cues derived from the reveal.",
      },
      {
        title: "Campaign extension potential",
        body: "The same system could become a short logo sting, looping identity bumper, widescreen hero, and vertical launch teaser.",
      },
      {
        title: "What is concept vs real",
        body: "This is a self-initiated motion study, not commissioned brand work, and it makes no claim about a real client, launch, or commercial outcome.",
      },
    ],
    tags: [
      "Motion Identity",
      "3D Direction",
      "Abstract Simulation",
      "Logo Reveal",
      "Sound Design",
    ],
  },
  {
    slug: "furia",
    title: "Furia",
    index: "03",
    category: "Product Film · Automotive Motion Direction · Concept Project",
    concept: true,
    duration: "30 seconds",
    durationSeconds: 30,
    orientation: "landscape",
    width: 1920,
    height: 1080,
    video: "/videos/furia.286ebdadbddd.mp4",
    videoMobile: "/videos/furia-mobile.b39c4813f6bb.mp4",
    poster: "/posters/furia.ed1339cb90bc.webp",
    captions: "/captions/furia.d7d68405aded.en.vtt",
    accent: "#EF4436",
    demonstrates:
      "How a launch film builds tension across thirty seconds and still lands a legible product name.",
    disclosure:
      "Self-initiated spec concept film for an invented model name. Not commissioned, licensed, sponsored, or endorsed by Ferrari S.p.A. or any vehicle manufacturer. The vehicle is an AI-generated design that borrows real supercar cues; no client relationship, commercial result, or vehicle performance claim is implied.",
    metaDescription:
      "Self-initiated MOTIONX concept study—no client relationship or commercial result implied, and unaffiliated with any vehicle manufacturer—exploring a thirty-second automotive launch film.",
    inquiry: {
      formType: "Product Film",
      eyebrow: "For your launch",
      heading: "Give a launch thirty seconds that hold.",
      body: "Tell MOTIONX what you’re launching, the energy it has to carry, and where the film needs to run.",
      cta: "Start a product film",
    },
    summary:
      "A hyper-kinetic automotive launch film built on wet asphalt, tunnel light, and a hard resolve to a single product name.",
    objective:
      "Sustain thirty seconds of escalating tension — twice a typical launch cut — and still resolve into a calm, legible title card.",
    approach:
      "Low, close camera work across reflective bodywork, tunnel light trails as the pacing device, and an ember-and-signal-red palette held against near-black. Sound design carries the build; the picture never explains itself.",
    deliverables: [
      "Horizontal 16:9 master",
      "Vertical 9:16 cutdown",
      "Title-card end frame",
      "Color & sound treatment",
    ],
    conceptStudyNotes: [
      {
        title: "What this concept demonstrates",
        body: "Thirty seconds can hold tension without a voiceover or spec list when the cut keeps escalating and the ending resolves rather than stops.",
      },
      {
        title: "System thinking",
        body: "Signal red, ember highlights, wet near-black asphalt, and converging tunnel light form a compact visual language that survives being moved onto other surfaces.",
      },
      {
        title: "Film-to-page extension",
        body: "The pacing suggests a launch page built on dark full-bleed frames, a single accent red used sparingly, and specification detail revealed only after the first held moment.",
      },
      {
        title: "Campaign extension potential",
        body: "The same world supports a vertical cutdown, short loops cut from the tunnel run, detail frames of the bodywork, and a title-card end frame for static placements.",
      },
      {
        title: "What is concept vs real",
        body: "This is a self-authored spec film for an invented model name, not commissioned brand work. It is not affiliated with, licensed by, or endorsed by Ferrari S.p.A. or any vehicle manufacturer, the vehicle is an AI-generated design rather than a real production car, and no client relationship, commercial outcome, or vehicle performance claim is implied.",
      },
    ],
    tags: [
      "Art Direction",
      "Automotive Visualization",
      "AI-Assisted Production",
      "Motion Design",
      "Sound Design",
    ],
  },
  {
    slug: "agentic-trading",
    title: "Agentic Trading",
    index: "04",
    category: "Brand Film · Character Motion · Fintech Motion System · Concept Project",
    concept: true,
    duration: "30 seconds",
    durationSeconds: 30,
    orientation: "landscape",
    width: 1920,
    height: 1080,
    video: "/videos/agentic-trading.344a87357144.mp4",
    videoMobile: "/videos/agentic-trading-mobile.4610f3f19a82.mp4",
    poster: "/posters/agentic-trading.e09753d24951.webp",
    captions: "/captions/agentic-trading.66d344306cb2.en.vtt",
    artFrame: {
      src: "/images/work/agentic-trading/strategy-board-1920.79064a62aeea.webp",
      mobileSrc: "/images/work/agentic-trading/strategy-board-960.70da7ef150bb.webp",
      width: 1920,
      height: 815,
      alt: "MOTIONX mascot beside a glass chessboard in a fictional strategy scene",
      label: "Strategy frame",
      caption:
        "Fictional systems-thinking concept frame. No live market data, working trading product, or performance result is shown.",
    },
    accent: "#C9FF45",
    demonstrates:
      "How an abstract systems idea becomes a character story without losing its decision logic.",
    disclosure:
      "Self-initiated concept brand film for a fictional trading product. All market data, tickers, scores, and depicted product behavior are fictional. No client relationship, live trading system, performance result, or financial advice is implied.",
    metaDescription:
      "Self-initiated MOTIONX concept film—no client relationship, live trading system, performance result, or financial advice implied—using fictional data to explore a character-led fintech motion system.",
    inquiry: {
      formType: "Product Film",
      eyebrow: "For your product",
      heading: "Turn a complex system into a story people can follow.",
      body: "Tell MOTIONX what your product does, what must stay accurate, and where the launch film needs to run.",
      cta: "Start a brand film",
    },
    summary:
      "A high-tempo concept film that turns research, scoring, and human review into a character-led visual story for a fictional agentic-trading system.",
    objective:
      "Translate an abstract research-to-decision workflow into a fast, readable thirty-second concept without presenting the fictional system as a real product or investment tool.",
    approach:
      "A chrome mascot carries the film through research, verification, scoring, and a human-review resolve. Modular interface frames, electric-lime signals, and a sixty-frame-per-second camera rhythm keep the process legible across widescreen and vertical cuts.",
    deliverables: [
      "Horizontal 16:9 film",
      "Vertical 9:16 campaign cut",
      "Captioned sound-on web version",
      "Silent homepage teaser",
    ],
    conceptStudyNotes: [
      {
        title: "What this concept demonstrates",
        body: "A complex, abstract workflow can become a readable story when one character carries the audience through each decision stage.",
      },
      {
        title: "System thinking",
        body: "The mascot, modular interface frames, research-verification-proposal sequence, and electric-lime signals form one repeatable visual grammar rather than a collection of isolated shots.",
      },
      {
        title: "Film-to-page extension",
        body: "The same direction could become a launch page that reveals the process one stage at a time, keeps exact product facts in deterministic interface layers, and ends with one human decision point.",
      },
      {
        title: "Campaign extension potential",
        body: "The supplied widescreen and vertical cuts show how the character, interface rhythm, and scoring moments can hold together across homepage, social, and campaign placements.",
      },
      {
        title: "What is concept vs real",
        body: "This is a self-initiated concept film for a fictional system, not a working trading product or commissioned client project. All market data, tickers, scores, and product behavior shown are fictional; no performance result or financial advice is implied.",
      },
    ],
    tags: [
      "Art Direction",
      "Character Motion",
      "AI-Assisted Production",
      "Interface Motion",
      "Sound Design",
    ],
  },
];

/** Honest bridge from motion proof to the studio's self-owned web proof. */
export const projectToSystemBridge = {
  label: "See how film direction extends to web",
  href: "/system-study",
} as const;

export const projectNavigationCopy = {
  collectionEyebrow: "Selected work",
  collectionLabel: "Back to all projects",
  nextEyebrow: "Next project",
  nextCta: "Open next case study",
  caseIndexLabel: "Case index",
  onThisPageLabel: "On this page",
  filmAnchor: "Watch the film",
  breakdownAnchor: "Read the breakdown",
  inquiryAnchor: "Discuss a project",
  whatThisShows: "What this shows",
  outputScope: "Concept output scope",
  conceptNotesLabel: "Concept study notes",
  previewFilm: "Preview film",
  openCaseStudy: "Open case study",
  /** Prefix announced politely when the edit-bay swaps the active project. */
  nowViewing: "Now viewing",
  /** Total-running-time prefix for the edit-suite index readouts. */
  trtLabel: "TRT",
} as const;

/** Edit-suite TRT display ("TRT 00:15") from the real film length. */
export function getProjectTrt(project: Pick<Project, "durationSeconds">): string {
  const m = Math.floor(project.durationSeconds / 60);
  const s = project.durationSeconds % 60;
  return `${projectNavigationCopy.trtLabel} ${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

export function getProject(slug: string): Project | undefined {
  return projects.find((p) => p.slug === slug);
}

/** The explicit concept marker/disclosure carries provenance in UI contexts. */
export function getProjectCapabilityLabel(category: string): string {
  return category.replace(/\s*·\s*Concept Project\s*$/i, "");
}

/** The visible provenance marker is sourced from each centralized category. */
export function getProjectConceptLabel(category: string): string {
  return category.split(" · ").at(-1) ?? category;
}

export function getAdjacentProjects(slug: string) {
  const i = projects.findIndex((p) => p.slug === slug);
  if (i === -1) return { prev: undefined, next: undefined };
  const prev = projects[(i - 1 + projects.length) % projects.length];
  const next = projects[(i + 1) % projects.length];
  return { prev, next };
}

export function getProjectInquiryHref(project: Pick<Project, "inquiry">) {
  return `/?type=${encodeURIComponent(project.inquiry.formType)}#contact`;
}
