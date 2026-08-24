#!/usr/bin/env node
/**
 * MOTIONX post-build metadata guard.
 *
 * Validates the metadata contracts of the actual `.next/server/app` output —
 * prerendered route HTML, the 404, sitemap.xml, and robots.txt — instead of
 * trusting source substrings. Runs in the gate after `next build`, before the
 * privacy guard and e2e.
 *
 * The expected origin is the same normalized NEXT_PUBLIC_SITE_URL the build
 * used (localhost fallback for ordinary local runs). Production-origin
 * strictness (HTTPS, no localhost/loopback/preview hosts) is enforced whenever
 * CI is set or the configured origin IS the production origin — in CI the gate
 * separately fails closed unless the origin is exactly production, so CI
 * always certifies the strict contract.
 *
 * Node built-ins only; the HTML "parsing" is tag-level regex over Next's
 * deterministic serialized head output, not a general HTML parser.
 */
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const appDir = path.join(root, ".next", "server", "app");
const failures = [];
let checks = 0;

const PRODUCTION_ORIGIN = "https://madebymotionx.com";
const BRAND = "MOTIONX";
let expectedOrigin;
try {
  expectedOrigin = new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ).origin;
} catch {
  // Never echo the raw value — it could carry credentials or signed tokens.
  console.error(
    "MOTIONX metadata guard failed:\n- NEXT_PUBLIC_SITE_URL is not a parseable URL (value withheld from output).",
  );
  process.exit(1);
}
const strict = Boolean(process.env.CI) || expectedOrigin === PRODUCTION_ORIGIN;

function check(condition, message) {
  checks += 1;
  if (!condition) failures.push(message);
}

function read(relative) {
  const absolute = path.join(appDir, relative);
  if (!existsSync(absolute)) {
    failures.push(
      `Expected build output ${path.join(".next/server/app", relative)} is missing — the guard cannot certify this build.`,
    );
    return null;
  }
  return readFileSync(absolute, "utf8");
}

const decodeEntities = (value) =>
  value
    .replaceAll("&amp;", "&")
    .replaceAll("&quot;", '"')
    .replaceAll("&#x27;", "'")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">");

/** All <meta> contents for a property/name, in order. */
function metas(html, attribute, key) {
  const pattern = new RegExp(
    `<meta[^>]*\\b${attribute}="${key.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}"[^>]*>`,
    "g",
  );
  return [...html.matchAll(pattern)].map((match) => {
    const content = match[0].match(/\bcontent="([^"]*)"/);
    return content ? decodeEntities(content[1]) : "";
  });
}

function canonicals(html) {
  return [...html.matchAll(/<link[^>]*\brel="canonical"[^>]*>/g)].map((match) => {
    const href = match[0].match(/\bhref="([^"]*)"/);
    return href ? decodeEntities(href[1]) : "";
  });
}

const stripTrailingSlash = (value) => value.replace(/\/$/, "");

/** Credential/query/fragment-free display form so failure output can never
 *  echo tokens embedded in a bad URL value. */
function redactUrl(value) {
  try {
    const parsed = new URL(value);
    return `${parsed.origin}${parsed.pathname}`;
  } catch {
    return "<unparseable URL, value withheld>";
  }
}

/** Shared URL hygiene for any URL-bearing metadata value. */
function checkUrlHygiene(value, where) {
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    check(false, `${where}: value is not an absolute URL (withheld from output).`);
    return;
  }
  check(
    stripTrailingSlash(parsed.origin) === expectedOrigin,
    `${where}: origin is ${parsed.origin}, expected ${expectedOrigin}.`,
  );
  check(!parsed.username && !parsed.password, `${where}: URL carries credentials.`);
  check(!parsed.search && !parsed.hash, `${where}: URL carries a query or hash.`);
  check(!parsed.pathname.includes("//"), `${where}: URL has a doubled path slash.`);
  if (strict) {
    check(parsed.protocol === "https:", `${where}: not HTTPS (${redactUrl(value)}).`);
    check(
      !/^(localhost|127\.|0\.0\.0\.0|\[?::1)/.test(parsed.hostname) &&
        !parsed.hostname.endsWith(".vercel.app"),
      `${where}: local/preview host in production metadata (${redactUrl(value)}).`,
    );
  }
}

/* ── Route matrix ─────────────────────────────────────────────────── */

const ROUTES = [
  { file: "index.html", route: "/", ogType: "website", image: "/og/og-image.jpg", concept: false },
  { file: "pilot.html", route: "/pilot", ogType: "website", image: "/og/og-image.jpg", concept: false },
  { file: "system-study.html", route: "/system-study", ogType: "article", image: "/og/system-study.jpg", concept: true },
  { file: "work/renewal.html", route: "/work/renewal", ogType: "article", image: "/og/renewal.jpg", concept: true },
  { file: "work/liquid-signal.html", route: "/work/liquid-signal", ogType: "article", image: "/og/liquid-signal.jpg", concept: true },
  { file: "work/furia.html", route: "/work/furia", ogType: "article", image: "/og/furia.jpg", concept: true },
  { file: "work/agentic-trading.html", route: "/work/agentic-trading", ogType: "article", image: "/og/agentic-trading.jpg", concept: true },
];

for (const spec of ROUTES) {
  const html = read(spec.file);
  if (html === null) continue;
  const where = spec.route;
  const expectedUrl =
    spec.route === "/" ? expectedOrigin : `${expectedOrigin}${spec.route}`;

  const canonical = canonicals(html);
  check(canonical.length === 1, `${where}: expected exactly 1 canonical, found ${canonical.length}.`);
  if (canonical.length === 1) {
    check(
      stripTrailingSlash(canonical[0]) === expectedUrl,
      `${where}: canonical is ${redactUrl(canonical[0])}, expected ${expectedUrl}.`,
    );
    checkUrlHygiene(canonical[0], `${where} canonical`);
  }

  const ogUrl = metas(html, "property", "og:url");
  check(ogUrl.length === 1, `${where}: expected exactly 1 og:url, found ${ogUrl.length}.`);
  if (ogUrl.length === 1) {
    check(
      stripTrailingSlash(ogUrl[0]) === expectedUrl,
      `${where}: og:url is ${redactUrl(ogUrl[0])}, expected ${expectedUrl}.`,
    );
    checkUrlHygiene(ogUrl[0], `${where} og:url`);
  }

  check(
    metas(html, "property", "og:site_name")[0] === BRAND,
    `${where}: og:site_name must be ${BRAND}.`,
  );
  check(
    metas(html, "property", "og:type")[0] === spec.ogType,
    `${where}: og:type must be ${spec.ogType}.`,
  );

  const ogImage = metas(html, "property", "og:image");
  check(ogImage.length === 1, `${where}: expected exactly 1 og:image, found ${ogImage.length}.`);
  if (ogImage.length === 1) {
    check(
      ogImage[0] === `${expectedOrigin}${spec.image}`,
      `${where}: og:image is ${redactUrl(ogImage[0])}, expected ${expectedOrigin}${spec.image}.`,
    );
    checkUrlHygiene(ogImage[0], `${where} og:image`);
  }
  check(metas(html, "property", "og:image:width")[0] === "1200", `${where}: og:image:width must be 1200.`);
  check(metas(html, "property", "og:image:height")[0] === "630", `${where}: og:image:height must be 630.`);
  const alt = metas(html, "property", "og:image:alt")[0] ?? "";
  check(alt.trim().length > 0 && alt.includes(BRAND), `${where}: og:image:alt must be nonempty, truthful brand alt text.`);

  check(
    metas(html, "name", "twitter:card")[0] === "summary_large_image",
    `${where}: twitter:card must be summary_large_image.`,
  );
  const twitterImage = metas(html, "name", "twitter:image");
  check(
    twitterImage[0] === `${expectedOrigin}${spec.image}`,
    `${where}: twitter:image is ${redactUrl(twitterImage[0])}, expected ${expectedOrigin}${spec.image}.`,
  );
  if (twitterImage[0]) checkUrlHygiene(twitterImage[0], `${where} twitter:image`);

  // Public routes must never ship a noindex (nor its "none" alias), and
  // concept routes must stay concept-forward in search/social copy.
  const robotsTokens = metas(html, "name", "robots").flatMap((value) =>
    value.split(",").map((token) => token.trim().toLowerCase()),
  );
  check(!robotsTokens.includes("noindex"), `${where}: public route must not be noindexed.`);
  check(!robotsTokens.includes("none"), `${where}: public route must not carry robots "none".`);
  const description = metas(html, "name", "description")[0] ?? "";
  check(description.trim().length > 0, `${where}: meta description must be present.`);
  if (spec.concept) {
    check(/concept/i.test(description), `${where}: description must stay concept-forward.`);
    const title = decodeEntities(html.match(/<title>([^<]*)<\/title>/)?.[1] ?? "");
    check(/concept|system study/i.test(title), `${where}: title must identify concept work.`);
  }

  // JSON-LD: parse every block; every URL-bearing string must use the
  // configured origin (schema.org context URLs excepted).
  const jsonLdBlocks = [
    ...html.matchAll(
      /<script type="application\/ld\+json">([\s\S]*?)<\/script>/g,
    ),
  ].map((match) => match[1]);
  const parsed = [];
  for (const block of jsonLdBlocks) {
    try {
      const value = JSON.parse(block);
      // A block may hold one entity, an array of entities, or an @graph.
      const entities = Array.isArray(value)
        ? value
        : Array.isArray(value?.["@graph"])
          ? value["@graph"]
          : [value];
      parsed.push(...entities);
    } catch {
      check(false, `${where}: unparseable JSON-LD block.`);
    }
  }
  const types = parsed.map((entry) => entry["@type"]);
  if (spec.route === "/") {
    check(types.includes("Organization"), "/: JSON-LD must retain Organization.");
    check(types.includes("WebSite"), "/: JSON-LD must retain WebSite.");
  }
  if (spec.concept) {
    const creative = parsed.find((entry) => entry["@type"] === "CreativeWork");
    check(Boolean(creative), `${where}: JSON-LD must retain CreativeWork.`);
    if (creative) {
      check(
        /concept/i.test(String(creative.description ?? "")),
        `${where}: CreativeWork description must stay concept-forward.`,
      );
    }
  }
  const walk = (node, trail) => {
    if (typeof node === "string") {
      if (/^https?:\/\//.test(node) && !node.startsWith("https://schema.org")) {
        checkUrlHygiene(node, `${where} JSON-LD ${trail}`);
      }
      return;
    }
    if (Array.isArray(node)) {
      node.forEach((item, index) => walk(item, `${trail}[${index}]`));
      return;
    }
    if (node && typeof node === "object") {
      for (const [key, value] of Object.entries(node)) {
        if (key === "@context") continue;
        walk(value, trail ? `${trail}.${key}` : key);
      }
    }
  };
  parsed.forEach((entry, index) => walk(entry, `#${index}`));
}

/* ── 404 isolation ────────────────────────────────────────────────── */

const notFound = read("_not-found.html");
if (notFound !== null) {
  const robotsTokens = metas(notFound, "name", "robots").flatMap((value) =>
    value.split(",").map((token) => token.trim().toLowerCase()),
  );
  check(robotsTokens.includes("noindex"), "404: must carry at least one noindex directive.");
  // "index", "all", and an empty directive all permit indexing.
  for (const permissive of ["index", "all", ""]) {
    check(
      !robotsTokens.includes(permissive),
      `404: must not carry a robots directive permitting indexing ("${permissive || "empty"}").`,
    );
  }
  check(canonicals(notFound).length === 0, "404: must not ship a canonical.");
  // The 404 must carry NO share metadata at all — every Open Graph property
  // and every Twitter tag, not merely the URL/image fields.
  const ogTags = [...notFound.matchAll(/<meta[^>]*\bproperty="og:([^"]*)"[^>]*>/g)].map(
    (match) => match[1],
  );
  check(
    ogTags.length === 0,
    `404: must not ship Open Graph metadata (found og:${ogTags.join(", og:")}).`,
  );
  const twitterTags = [
    ...notFound.matchAll(/<meta[^>]*\bname="twitter:([^"]*)"[^>]*>/g),
  ].map((match) => match[1]);
  check(
    twitterTags.length === 0,
    `404: must not ship Twitter metadata (found twitter:${twitterTags.join(", twitter:")}).`,
  );
}

/* ── Sitemap + robots ─────────────────────────────────────────────── */

const sitemap = read("sitemap.xml.body");
if (sitemap !== null) {
  const locs = [...sitemap.matchAll(/<loc>([^<]*)<\/loc>/g)].map((match) =>
    stripTrailingSlash(decodeEntities(match[1])),
  );
  const expectedSet = ROUTES.map((spec) =>
    spec.route === "/" ? expectedOrigin : `${expectedOrigin}${spec.route}`,
  );
  check(
    locs.length === new Set(locs).size,
    "sitemap: contains duplicate <loc> entries.",
  );
  check(
    locs.length === expectedSet.length &&
      expectedSet.every((url) => locs.includes(url)),
    `sitemap: <loc> set is [${locs.join(", ")}], expected exactly the ${expectedSet.length} public URLs [${expectedSet.join(", ")}].`,
  );
  for (const loc of locs) checkUrlHygiene(loc, "sitemap <loc>");
}

const robots = read("robots.txt.body");
if (robots !== null) {
  const lines = robots.split(/\r?\n/).map((line) => line.trim());
  check(lines.includes("Allow: /"), "robots.txt: must contain `Allow: /`.");
  // Host/Sitemap are validated as exact, unique LINES — substring matching
  // would accept e.g. a host of `${expectedOrigin}.evil`.
  const hostLines = lines.filter((line) => line.startsWith("Host:"));
  check(
    hostLines.length === 1 && hostLines[0] === `Host: ${expectedOrigin}`,
    `robots.txt: must declare exactly one Host line equal to \`Host: ${expectedOrigin}\` (found: ${hostLines.join(" | ") || "none"}).`,
  );
  const sitemapLines = lines.filter((line) => line.startsWith("Sitemap:"));
  check(
    sitemapLines.length === 1 &&
      sitemapLines[0] === `Sitemap: ${expectedOrigin}/sitemap.xml`,
    `robots.txt: must declare exactly one Sitemap line equal to \`Sitemap: ${expectedOrigin}/sitemap.xml\` (found: ${sitemapLines.join(" | ") || "none"}).`,
  );
  if (strict) {
    check(
      !/localhost|127\.0\.0\.1|::1|\.vercel\.app|http:\/\//.test(robots),
      "robots.txt: contains a local/preview/non-HTTPS reference.",
    );
  }
}

if (failures.length > 0) {
  console.error("MOTIONX metadata guard failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(
  `MOTIONX metadata guard passed (${checks} checks against built output; origin ${expectedOrigin}${strict ? ", production-strict" : ""}).`,
);
