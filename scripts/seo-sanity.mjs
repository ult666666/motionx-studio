#!/usr/bin/env node
/**
 * MOTIONX SEO/schema sanity guard.
 *
 * Source-level checks for expected routes, route metadata, and truthful
 * structured data fields. It is intentionally deterministic and fast.
 */
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
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
    return /\.(ts|tsx)$/.test(entry) ? [rel] : [];
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

const layout = read("src/app/layout.tsx");
const pilot = read("src/app/pilot/page.tsx");
const systemStudyPage = read("src/app/system-study/page.tsx");
const projectPage = read("src/app/work/[slug]/page.tsx");
const sitemap = read("src/app/sitemap.ts");
const robots = read("src/app/robots.ts");
const projects = read("src/content/projects.ts");
const site = read("src/content/site.ts");

check(layout.includes("metadataBase: new URL(site.url)"), "Root metadata must use the centralized site.url.");
check(layout.includes('alternates: { canonical: "/" }'), "Home canonical metadata must be present.");
check(layout.includes('"@type": "Organization"'), "Root JSON-LD must include Organization.");
check(layout.includes('"@type": "WebSite"'), "Root JSON-LD must include WebSite.");
check(layout.includes(".replace(/</g"), "JSON-LD output must escape '<' before injection.");

check(pilot.includes('title: "Pilot Launch'), "Pilot page must define a unique metadata title.");
check(pilot.includes('alternates: { canonical: "/pilot" }'), "Pilot page must define a canonical route.");
check(pilot.includes("/og/og-image.jpg"), "Pilot page must keep the shared JPEG OG card.");
check(existsSync(path.join(root, "public/og/og-image.jpg")), "Shared OG card file must exist.");

// Next metadata is shallow-merged per top-level key: any page-level
// openGraph/twitter must restate type, siteName, url, image and card, or the
// route silently drops them (this shipped once on /pilot). The metadata guard
// checks the built output; these source checks catch the mistake pre-build.
for (const [name, source, ogType] of [
  ["Pilot", pilot, 'type: "website"'],
  ["System Study", systemStudyPage, 'type: "article"'],
  ["Work", projectPage, 'type: "article"'],
]) {
  check(source.includes(ogType), `${name} page openGraph must restate its og:type.`);
  check(/siteName:\s*(site\.name|")/.test(source), `${name} page openGraph must restate siteName.`);
  check(source.includes("url:"), `${name} page openGraph must restate its url.`);
  check(/images:\s*\[/.test(source), `${name} page openGraph must restate its images.`);
  check(source.includes('card: "summary_large_image"'), `${name} page twitter block must restate the card type.`);
  check(/twitter:\s*{[\s\S]*?images:/.test(source), `${name} page twitter block must restate its image.`);
}

check(systemStudyPage.includes('title: `${systemStudy.name} System Study`'), "System Study must define a unique metadata title.");
check(systemStudyPage.includes('alternates: { canonical: "/system-study" }'), "System Study must define a canonical route.");
check(systemStudyPage.includes('"@type": "CreativeWork"'), "System Study must include truthful CreativeWork JSON-LD.");
check(systemStudyPage.includes("systemStudy.disclosure"), "System Study metadata/schema must preserve its concept disclosure.");
check(systemStudyPage.includes("/og/system-study.jpg"), "System Study must keep its dedicated JPEG OG card.");
check(existsSync(path.join(root, "public/og/system-study.jpg")), "System Study OG card file must exist.");

check(projectPage.includes("export async function generateMetadata"), "Work pages must generate route metadata.");
check(projectPage.includes("export const dynamicParams = false"), "Work pages must reject slugs outside generated concept routes.");
check(projectPage.includes('alternates: { canonical: `/work/${project.slug}` }'), "Work pages must define canonical routes.");
check(projectPage.includes('"@type": "CreativeWork"'), "Work pages must include truthful CreativeWork JSON-LD.");
check(projectPage.includes("project.disclosure"), "CreativeWork description must include the concept disclosure.");
check(projectPage.includes("project.metaDescription"), "Work-page metadata must use a concept-forward centralized description.");
check(projectPage.includes("Concept Study"), "Work-page search and social titles must identify concept work.");

for (const route of [
  'url: site.url',
  'url: `${site.url}/pilot`',
  'url: `${site.url}/system-study`',
  'url: `${site.url}/work/${p.slug}`',
]) {
  check(sitemap.includes(route), `Sitemap is missing expected route expression: ${route}`);
}
check(robots.includes('allow: "/"'), "Robots must allow public indexing.");
check(robots.includes('sitemap: `${site.url}/sitemap.xml`'), "Robots must point at the centralized sitemap URL.");
check(!sitemap.includes("lastModified"), "Sitemap must not invent a fresh modification date on every build.");

const slugs = [...projects.matchAll(/slug:\s*"([^"]+)"/g)].map((m) => m[1]);
const projectBlocks = extractProjectBlocks(projects);
check(projectBlocks.length === slugs.length, "SEO sanity must parse every project entry.");
for (const block of projectBlocks) {
  const slug = /slug:\s*"([^"]+)"/.exec(block)?.[1] ?? "unknown";
  const poster = /poster:\s*"([^"]+)"/.exec(block)?.[1];
  const metaDescription = /metaDescription:\s*"([^"]+)"/.exec(block)?.[1];

  check(Boolean(poster), `Project ${slug} should define a source-visible poster.`);
  check(
    Boolean(metaDescription) && /self-initiated/i.test(metaDescription) && /concept/i.test(metaDescription),
    `Project ${slug} should define concept-forward search/social metadata.`,
  );
  if (!poster) continue;

  check(poster.startsWith("/"), `Project ${slug} poster must use a root-relative public path.`);
  check(
    existsSync(path.join(root, "public", poster.replace(/^\//, ""))),
    `Project ${slug} poster file is missing: ${poster}`,
  );
}

const sourceText = walk("src").map((file) => `${file}\n${read(file)}`).join("\n");
const forbiddenSchemaFields = [
  "PostalAddress",
  "telephone",
  "foundingDate",
  "numberOfEmployees",
  "aggregateRating",
  '"review"',
  '"award"',
  '"awards"',
];
for (const field of forbiddenSchemaFields) {
  check(!sourceText.includes(field), `SEO/schema source must not include unsupported field: ${field}`);
}

check(!sourceText.includes("daichunyu666@gmail.com"), "SEO metadata/schema must not expose the private backup Gmail address.");
check(!sourceText.includes("motionx.studio"), "SEO metadata/schema must not introduce an invented domain.");
check(site.includes('social: [] as ReadonlyArray<SocialLink>'), "SEO sameAs must stay absent until real social profiles exist.");

if (failures.length > 0) {
  console.error("MOTIONX SEO sanity check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`MOTIONX SEO sanity check passed (${checks} checks).`);
