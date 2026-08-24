#!/usr/bin/env node
/**
 * MOTIONX content-integrity guard.
 *
 * This is intentionally source-focused: it catches drift that a visual pass can
 * miss, before fake proof, private addresses, or concept-label regressions reach
 * the public site.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const failures = [];
let checks = 0;

function read(file) {
  return readFileSync(path.join(root, file), "utf8");
}

function check(condition, message) {
  checks += 1;
  if (!condition) failures.push(message);
}

function walk(dir) {
  const abs = path.join(root, dir);
  return readdirSync(abs).flatMap((entry) => {
    const rel = path.join(dir, entry);
    const full = path.join(root, rel);
    const stats = statSync(full);
    if (stats.isDirectory()) return walk(rel);
    // Every textual source format that can reach a build artifact — not just
    // TS/TSX. Binary assets (images, fonts, media) are excluded; the post-
    // build privacy guard remains the authoritative shipped-byte check.
    return /\.(ts|tsx|js|jsx|mjs|cjs|css|json|svg|md|txt|html|xml)$/.test(entry)
      ? [rel]
      : [];
  });
}

function extractProjectBlocks(source) {
  const exportIndex = source.indexOf("export const projects");
  const assignmentIndex = source.indexOf("=", exportIndex);
  const arrayStart = source.indexOf("[", assignmentIndex);
  if (exportIndex === -1 || assignmentIndex === -1 || arrayStart === -1) return [];

  const blocks = [];
  let quote = "";
  let escaped = false;
  let depth = 0;
  let blockStart = -1;

  for (let i = arrayStart + 1; i < source.length; i += 1) {
    const char = source[i];

    if (quote) {
      if (escaped) {
        escaped = false;
      } else if (char === "\\") {
        escaped = true;
      } else if (char === quote) {
        quote = "";
      }
      continue;
    }

    if (char === '"' || char === "'" || char === "`") {
      quote = char;
      continue;
    }

    if (char === "{") {
      if (depth === 0) blockStart = i;
      depth += 1;
      continue;
    }

    if (char === "}") {
      depth -= 1;
      if (depth === 0 && blockStart !== -1) {
        blocks.push(source.slice(blockStart, i + 1));
        blockStart = -1;
      }
      continue;
    }

    if (char === "]" && depth === 0) break;
  }

  return blocks;
}

const site = read("src/content/site.ts");
const chrome = read("src/content/chrome.ts");
const contact = read("src/content/contact.ts");
const services = read("src/content/services.ts");
const projects = read("src/content/projects.ts");
const pilot = read("src/content/pilot.ts");
const pilotPage = read("src/app/pilot/page.tsx");
const pilotAddOnSelector = read("src/components/pilot-add-on-selector.tsx");
const servicesSection = read("src/components/services.tsx");
const launchSystemSection = read("src/components/launch-system.tsx");
const systemStudy = read("src/content/system-study.ts");
const systemStudyPage = read("src/app/system-study/page.tsx");
const auraPrototype = read("src/components/aura-prototype.tsx");
const home = read("src/app/page.tsx");
// The hero's media/controls live in the HeroReel client island; the server
// shell (hero.tsx) carries only static copy.
const hero = read("src/components/hero-reel.tsx");
const videoPolicy = read("src/hooks/use-video-autoplay-policy.ts");
// Contact split: the server shell renders pitch/rail/FAQ, the form island owns
// the pilot/Gmail contracts.
const contactSection = read("src/components/contact-section.tsx");
const contactForm = read("src/components/contact-form.tsx");
const footer = read("src/components/footer.tsx");
const processSection = read("src/components/process.tsx");

check(
  site.includes('email: "hello@madebymotionx.com"'),
  "src/content/site.ts must keep hello@madebymotionx.com as the public email.",
);
// The founder's direct address is operational documentation (CLAUDE.md), never
// website source: anything in src/content is fair game for build serialization
// into public JavaScript, so the whole tree must stay free of it. The per-file
// scan below enforces this for every source file, including site.ts.
check(
  /social:\s*\[\]\s+as ReadonlyArray<SocialLink>/.test(site),
  "src/content/site.ts must keep social empty until real profiles exist.",
);
check(
  /export const navLinks = \[workLink, servicesLink, pilotLink\]/.test(chrome) &&
    /export const footerNavLinks = \[\s*workLink,\s*servicesLink,\s*processLink,\s*studioLink,\s*pilotLink,?\s*\]/.test(
      chrome,
    ) &&
    chrome.includes('{ label: "Work", href: "/#work" }') &&
    chrome.includes('{ label: "Services", href: "/#services" }') &&
    chrome.includes('{ label: "Process", href: "/#process" }') &&
    chrome.includes('{ label: "Studio", href: "/#studio" }') &&
    chrome.includes('{ label: "Pilot", href: "/pilot" }') &&
    site.includes("footerNav: footerNavLinks") &&
    footer.includes("site.footerNav.map"),
  "Primary navigation must stay concise while the footer preserves all five destinations.",
);

const sourceFiles = walk("src");
for (const file of sourceFiles) {
  const text = read(file);
  check(
    !text.includes("daichunyu666@gmail.com"),
    `${file} must not expose the private backup Gmail address.`,
  );
  check(
    !text.includes("charles@madebymotionx.com"),
    `${file} must not reference the founder direct address — website source is serialized into public artifacts.`,
  );
  check(
    !/(trusted by|clients include|as seen in|award[- ]winning|testimonial|conversion lift|conversion rate|case-study result|client result|press mention|featured in|rated \d|roi\b|return on investment)/i.test(text),
    `${file} contains a public-proof phrase that needs real evidence or removal.`,
  );
  check(
    !/(limited spots|spots left|countdown|ends tonight|last chance|only \d+ (spots|seats|places)|book now before|priority booking|first (three|few) (pilot )?(clients|projects))/i.test(text),
    `${file} contains scarcity/urgency language that needs explicit business proof or removal.`,
  );
  check(
    !/(instagram\.com\/(#|coming-soon|yourhandle)|linkedin\.com\/(#|in\/your)|x\.com\/(#|your)|twitter\.com\/(#|your)|href=["']#["'])/i.test(text),
    `${file} contains a likely placeholder social/profile link.`,
  );
  check(
    !/message sent|has been sent|successfully sent/i.test(text),
    `${file} must not imply the no-backend contact flow sends a message.`,
  );
}

const slugs = [...projects.matchAll(/slug:\s*"([^"]+)"/g)].map((m) => m[1]);
const expectedProjectSlugs = [
  "renewal",
  "liquid-signal",
  "furia",
  "agentic-trading",
];
const conceptTrueCount = (projects.match(/concept:\s*true/g) ?? []).length;
const conceptCategoryCount = (projects.match(/category:\s*"[^"]*Concept Project"/g) ?? []).length;
const disclosureCount = (projects.match(/disclosure:\s*"[^"]+"/g) ?? []).length;
const metaDescriptionCount = (projects.match(/metaDescription:\s*"[^"]+"/g) ?? []).length;
const conceptStudyNotesCount = (projects.match(/conceptStudyNotes:\s*\[/g) ?? []).length;
const projectBlocks = extractProjectBlocks(projects);
const requiredConceptStudyNoteTitles = [
  "What this concept demonstrates",
  "System thinking",
  "Film-to-page extension",
  "Campaign extension potential",
  "What is concept vs real",
];

check(slugs.length > 0, "src/content/projects.ts must define project entries.");
check(
  slugs.length === expectedProjectSlugs.length &&
    expectedProjectSlugs.every((slug) => slugs.includes(slug)),
  "Portfolio entries must match the four registered concept-project slugs.",
);
check(
  projectBlocks.length === slugs.length,
  "Content integrity must parse every project entry.",
);
check(
  !/concept:\s*false/.test(projects),
  "All current MOTIONX portfolio entries must remain concept work.",
);
check(
  conceptTrueCount === slugs.length,
  "Every project in src/content/projects.ts must set concept: true.",
);
check(
  conceptCategoryCount === slugs.length,
  'Every project category must include "Concept Project".',
);
check(
  disclosureCount === slugs.length,
  "Every project must include a public concept disclosure.",
);
check(
  metaDescriptionCount === slugs.length,
  "Every project must include a concept-forward metadata description.",
);
check(
  conceptStudyNotesCount === slugs.length,
  "Every project must include first-party concept-study notes.",
);
check(
  !/\b(cures?|treats?|heals?|clinically proven|clinical(?:ly)?|therapeutic|therapy|medical benefit|health benefit|proven efficacy)\b/i.test(projects),
  "Project copy must not make unsupported medical or health claims.",
);
check(
  !/\b(?:stops a feed|built to stop a feed)\b/i.test(projects),
  "Concept copy must describe intended attention design without claiming an audience result.",
);

for (const block of projectBlocks) {
  const slug = /slug:\s*"([^"]+)"/.exec(block)?.[1] ?? "unknown";
  const metaDescription = /metaDescription:\s*"([^"]+)"/.exec(block)?.[1] ?? "";
  check(
    /self-initiated/i.test(metaDescription) && /concept/i.test(metaDescription),
    `Project ${slug} metadata must identify the work as a self-initiated concept.`,
  );
  check(
    /no client relationship/i.test(metaDescription),
    `Project ${slug} metadata must not leave client provenance ambiguous.`,
  );
  for (const title of requiredConceptStudyNoteTitles) {
    check(
      block.includes(`title: "${title}"`),
      `Project ${slug} concept-study notes must include "${title}".`,
    );
  }
}

const agenticTrading = projectBlocks.find((block) =>
  block.includes('slug: "agentic-trading"'),
);
check(Boolean(agenticTrading), "Agentic Trading concept project must remain registered.");
if (agenticTrading) {
  for (const phrase of [
    "fictional trading product",
    "All market data, tickers, scores, and depicted product behavior are fictional",
    "No client relationship",
    "live trading system",
    "performance result",
    "financial advice",
  ]) {
    check(
      agenticTrading.includes(phrase),
      `Agentic Trading disclosure must retain the load-bearing phrase: ${phrase}`,
    );
  }
}
check(
  site.includes("screening:") &&
    site.includes('title: "Agentic Trading"') &&
    site.includes('href: "/work/agentic-trading"') &&
    site.includes("Fictional system and market data") &&
    site.includes("financial advice is implied") &&
    read("src/components/hero.tsx").includes("site.hero.screening.disclosure") &&
    read("src/components/hero.tsx").includes("site.hero.screening.href"),
  "The hero must visibly preserve Agentic Trading concept and financial provenance.",
);

const expectedHomeOrder = [
  "<Hero />",
  "<StudioIntro />",
  "<SelectedWork />",
  "<LaunchSystem />",
  "<Services />",
  "<PilotCallout />",
  "<Process />",
  "<StudioSection />",
  "<ContactSection />",
];
const positions = expectedHomeOrder.map((needle) => home.indexOf(needle));
check(
  positions.every((pos) => pos >= 0),
  "src/app/page.tsx must include the canonical home sections.",
);
check(
  positions.every((pos, i) => i === 0 || pos > positions[i - 1]),
  "src/app/page.tsx section order must stay proof-before-explanation with the unnumbered pilot bridge.",
);

for (const file of ["src/app/work/[slug]/page.tsx"]) {
  check(
    read(file).includes("getProjectConceptLabel(project.category)"),
    `${file} must visibly preserve the Concept Project label.`,
  );
}

check(
  projects.includes("Concept Project") &&
    read("src/components/selected-work.tsx").includes("conceptLabel") &&
    read("src/components/selected-work-edit-bay.tsx").includes("active.conceptLabel"),
  "Selected Work must visibly preserve each project's centralized Concept Project label.",
);

check(
  projects.includes('conceptNotesLabel: "Concept study notes"') &&
    (read("src/app/work/[slug]/page.tsx").match(
      /projectNavigationCopy\.conceptNotesLabel/g,
    ) ?? []).length === 1,
  "Work-detail pages must render one concise disclosure for the first-party concept-study notes.",
);
check(
  read("src/app/work/[slug]/page.tsx").includes("project.metaDescription") &&
    read("src/app/work/[slug]/page.tsx").includes("Concept Study"),
  "Work-route search and social metadata must carry explicit concept provenance.",
);
check(
  read("src/components/selected-work-edit-bay.tsx").includes("VideoPlayer") &&
    read("src/components/selected-work-edit-bay.tsx").includes("aria-pressed") &&
    read("src/components/selected-work-edit-bay.tsx").includes("history.pushState") &&
    read("src/components/selected-work-edit-bay.tsx").includes(
      'href={`/work/${item.slug}`}',
    ) &&
    !read("src/components/selected-work-edit-bay.tsx").includes(
      "shouldInterceptLinkActivation",
    ),
  "Selected Work must keep one canonical, URL-addressable active-film edit bay.",
);
check(
  ["case-film", "case-breakdown", "case-inquiry"].every((id) =>
    read("src/app/work/[slug]/page.tsx").includes(`id="${id}"`),
  ) &&
    read("src/app/work/[slug]/page.tsx").includes("project.demonstrates") &&
    read("src/app/work/[slug]/page.tsx").includes(
      "projectNavigationCopy.outputScope",
    ) &&
    read("src/app/work/[slug]/page.tsx").includes("next.poster") &&
    read("src/app/work/[slug]/page.tsx").includes(
      "getProjectConceptLabel(next.category)",
    ) &&
    read("src/app/work/[slug]/page.tsx").includes('/#work-${project.slug}'),
  "Work-detail routes must keep the case index, honest proof labels, visual Up Next card, and return hash.",
);
check(
  projects.includes("Fictional systems-thinking concept frame") &&
    read("src/app/work/[slug]/page.tsx").includes("project.artFrame.caption"),
  "Agentic Trading editorial artwork must retain a visible fictional-system boundary.",
);
check(
  site.includes("trustStandards") &&
    site.includes('standardsLabel: "Quality standards"') &&
    read("src/components/studio-section.tsx").includes("site.studio.standardsLabel"),
  "First-party trust standards must remain centralized and visible.",
);
check(
  site.includes("faq") && contactSection.includes("FAQ"),
  "FAQ content must remain centralized and visible near contact.",
);
check(
  pilot.includes("detailGroups") &&
    !pilot.includes('title: "What you get"') &&
    pilotPage.includes("Pilot scope") &&
    pilotPage.includes("pilotMeta.detailGroups.map"),
  "Pilot detail groups must stay centralized, concise, and fully rendered.",
);
check(
  pilot.includes("getPilotInquiryHref") &&
    pilot.includes("pilot: offer.id") &&
    pilotPage.includes("getPilotInquiryHref") &&
    contactForm.includes('params.get("pilot")') &&
    contactForm.includes("offer.id === pilotId && offer.formType === type"),
  "Pilot pricing/subjects must require an explicit offer id that matches the project type.",
);
check(
  pilot.includes("getPilotAddOnInquiryHref") &&
    pilot.includes("getPilotReferralFromParams") &&
    pilot.includes("addon: CAMPAIGN_ADD_ON_ID") &&
    pilot.includes("A campaign add-on inquiry requires a base pilot offer") &&
    pilot.includes("export type PilotAddOnOffer") &&
    pilot.includes("formType?: never") &&
    pilotPage.includes("PilotAddOnSelector") &&
    pilotAddOnSelector.includes("pilotBaseOffers.map") &&
    pilotAddOnSelector.includes("getPilotAddOnInquiryHref(selectedBase)") &&
    pilotAddOnSelector.includes("getPilotAddOnTotal(selectedBase, campaignAddOnOffer)") &&
    contactForm.includes('url.searchParams.delete("addon")') &&
    contactForm.includes("selectedPilotReferral.addOn"),
  "The pilot campaign add-on must stay paired to one base offer and remain visible in the contact handoff.",
);
check(
  contact.includes('"Campaign Content System"') &&
    !contact.includes('"Campaign Content Add-On"') &&
    services.includes('formType: "Campaign Content System"') &&
    pilot.includes('title: "Campaign Content Add-On"') &&
    pilot.includes("satisfies PilotAddOnOffer") &&
    !pilot
      .slice(
        pilot.indexOf("export const campaignAddOnOffer"),
        pilot.indexOf("/** One comparison list"),
      )
      .includes("formType"),
  "The campaign system must remain a general option while the pilot add-on stays referral-only and has no fallback form type.",
);
check(
  pilot.includes("getPilotIncludedScope") &&
    pilot.includes("offer.deliverable") &&
    pilotPage.includes("getPilotIncludedScope(offer)"),
  "Every pilot package comparison must list its core deliverable before extras.",
);
check(
  pilot.includes("getPilotAddOnTotal") &&
    pilot.includes("parseWholeUsd(baseOffer.pilotPrice)") &&
    pilot.includes("parseWholeUsd(addOn.pilotPrice)") &&
    pilotAddOnSelector.includes("pilotAddOnCopy.combinedTotalLabel"),
  "The paired pilot selector must derive and show an exact base-plus-add-on total from centralized prices.",
);
check(
  !services.includes("launchSystemSequence") &&
    !launchSystemSection.includes("Production sequence") &&
    !launchSystemSection.includes("ContactTypeLink") &&
    (launchSystemSection.match(/<Link/g) ?? []).length === 1 &&
    systemStudyPage.includes("systemStudy.stages.map"),
  "Homepage AURA must keep one route action and visual proof while the full System Study retains its detailed stages.",
);
check(
  /<ol className="[^"]*"/.test(processSection) &&
    processSection.includes("<li") &&
    processSection.includes("processSteps.map"),
  "The four-step homepage process must remain a semantic ordered list.",
);
check(
  servicesSection.includes("{service.bestFor}") &&
    servicesSection.indexOf("{service.bestFor}") <
      servicesSection.indexOf("<ContactTypeLink", servicesSection.indexOf("services.map")),
  "Each service must expose its best-fit guidance before the contextual inquiry CTA.",
);
check(
  contactForm.includes('from "@/content/contact"') &&
    !contactForm.includes("const PROJECT_TYPES = ["),
  "Contact options must remain centralized and shared with service/project/pilot CTAs.",
);
check(
  systemStudy.includes("Self-initiated concept study") &&
    systemStudy.includes("no launch result, customer relationship, or product claim is implied"),
  "System Study must keep an explicit no-client/no-result concept disclosure.",
);
check(
  systemStudyPage.includes("systemStudy.disclosure") &&
    systemStudyPage.includes("Concept disclosure"),
  "System Study route must visibly render the centralized concept disclosure.",
);
check(
  ["Focal hierarchy", "Responsive translation", "Single-action path"].every(
    (label) => systemStudy.includes(label),
  ) &&
    systemStudy.includes("principles") &&
    systemStudyPage.includes("<AuraPrototype />") &&
    auraPrototype.includes("principle.label") &&
    auraPrototype.includes("principle.body") &&
    auraPrototype.includes("aria-pressed") &&
    auraPrototype.includes('aria-live="polite"') &&
    auraPrototype.includes("systemStudy.prototype.interactionLabel") &&
    auraPrototype.includes("systemStudy.prototype.activeLabel") &&
    auraPrototype.includes("systemStudy.prototype.chromeLabel") &&
    auraPrototype.includes("systemStudy.prototype.breakdownLabel"),
  "System Study must keep its centralized, interactive launch-page reasoning annotations visible.",
);
check(
  systemStudyPage.includes('href={`/?type=${encodeURIComponent(systemStudy.cta.formType)}#contact`}'),
  "System Study inquiry CTA must preserve centralized form-type preselection.",
);
check(
  hero.includes('preload="none"'),
  'Hero teaser must keep preload="none".',
);
check(
  hero.includes("useVideoAutoplayAllowed") &&
    /connection\?\.saveData/.test(videoPolicy) &&
    videoPolicy.includes('addEventListener("change", sync)'),
  "Hero teaser must keep the shared, reactive data-saver/reduced-motion policy.",
);

if (failures.length > 0) {
  console.error("MOTIONX content-integrity check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`MOTIONX content-integrity check passed (${checks} checks).`);
