#!/usr/bin/env node
/**
 * MOTIONX verification gate:
 * content integrity -> asset integrity -> SEO sanity -> typecheck -> lint -> build
 * -> metadata guard (built HTML/sitemap/robots) -> privacy guard (browser
 * artifacts) -> e2e.
 *
 * Refuses to run while anything holds port 3939 — `next build` corrupts `.next`
 * if `next dev` is live (see CLAUDE.md gotchas). The e2e step then boots the
 * newly built production server via playwright.config.ts.
 *
 * This automates the mechanical gate only; a real browser pass (desktop + mobile,
 * console, overflow, reduced motion) is still required for visual changes.
 */
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { connect } from "node:net";

const PORT = 3939;

// The gate must validate against the same Node major that CI and the deploy
// build use (.nvmrc / setup-node are both pinned). A stray system Node would
// silently certify a different runtime.
try {
  const pinnedMajor = parseInt(readFileSync(".nvmrc", "utf8").trim(), 10);
  const runningMajor = parseInt(process.versions.node.split(".")[0], 10);
  if (Number.isInteger(pinnedMajor) && runningMajor !== pinnedMajor) {
    console.error(
      `✗ Node ${process.versions.node} does not match the pinned major in .nvmrc (${pinnedMajor}). ` +
        "Use the project environment (export PATH=/opt/anaconda3/envs/motionx/bin:$PATH).",
    );
    process.exit(1);
  }
} catch {
  // No .nvmrc — nothing to enforce.
}
// Give metadata, sitemap, and Open Graph URLs a deterministic origin during
// the production build. A real deploy-provided value still wins.
const gateSiteUrl = process.env.NEXT_PUBLIC_SITE_URL ?? `http://localhost:${PORT}`;

// In CI the gate certifies a release, so it fails closed unless the build
// origin is exactly the production origin — otherwise CI would happily
// certify localhost (or a preview origin) canonical/OG/JSON-LD/sitemap URLs.
// The expected origin is intentionally hard-coded HERE (the verification
// contract must be independent); application code stays environment-driven.
// NOTE on log hygiene: raw URL env values are never echoed — a signed preview
// URL or credential-bearing value must not leak into logs. Diagnostics show at
// most the credential-free `origin`.
const PRODUCTION_ORIGIN = "https://madebymotionx.com";
if (process.env.CI) {
  const raw = process.env.NEXT_PUBLIC_SITE_URL ?? "";
  const fail = (reason) => {
    console.error(`✗ CI gate: NEXT_PUBLIC_SITE_URL ${reason}.`);
    console.error(`  CI must build with exactly ${PRODUCTION_ORIGIN}.`);
    process.exit(1);
  };
  if (!raw.trim()) fail("is missing or empty");
  let parsed;
  try {
    parsed = new URL(raw);
  } catch {
    fail("is not a parseable URL (value withheld from logs)");
  }
  if (parsed.protocol !== "https:") fail(`is not HTTPS (origin: ${parsed.origin})`);
  if (parsed.username || parsed.password) fail("contains credentials (value withheld from logs)");
  if (parsed.pathname !== "/" || parsed.search || parsed.hash) {
    fail(`carries a path, query, or hash (origin: ${parsed.origin})`);
  }
  if (
    /^(localhost|127\.|0\.0\.0\.0|\[?::1)/.test(parsed.hostname) ||
    parsed.hostname.endsWith(".vercel.app")
  ) {
    fail(`points at a local/preview origin (${parsed.origin})`);
  }
  if (parsed.origin !== PRODUCTION_ORIGIN) {
    fail(`is ${parsed.origin}, not the production origin`);
  }
}

// Every gate run (not only CI) needs a parseable origin — fail cleanly and
// without echoing the raw value instead of crashing inside the build.
let gateSiteOrigin;
try {
  gateSiteOrigin = new URL(gateSiteUrl).origin;
} catch {
  console.error(
    "✗ gate: NEXT_PUBLIC_SITE_URL is not a parseable URL (value withheld from logs).",
  );
  process.exit(1);
}

const gateEnv = {
  ...process.env,
  NEXT_PUBLIC_SITE_URL: gateSiteUrl,
  NEXT_TELEMETRY_DISABLED: process.env.NEXT_TELEMETRY_DISABLED ?? "1",
};

// The gate certifies the `.next` artifact it is about to build. An ambient
// PLAYWRIGHT_BASE_URL would disable Playwright's local production server and
// silently point the e2e step at an external or stale deployment — strip it.
// External/live runs stay supported via the standalone `playwright test` /
// `browser:verify` commands with PLAYWRIGHT_BASE_URL set explicitly.
if ("PLAYWRIGHT_BASE_URL" in gateEnv) {
  // Never echo the value — ambient targets can carry signed tokens/credentials.
  console.log(
    "━━ gate: ignoring an ambient PLAYWRIGHT_BASE_URL (value withheld from logs) — " +
      "the gate only ever tests the build it just produced.",
  );
  delete gateEnv.PLAYWRIGHT_BASE_URL;
}
if ("PLAYWRIGHT_BASE_URL" in gateEnv) {
  console.error("✗ gate self-check failed: PLAYWRIGHT_BASE_URL survived sanitization.");
  process.exit(1);
}
console.log(
  `━━ gate: e2e target = local production server on port ${PORT} (freshly built .next) ` +
    `| metadata origin = ${gateSiteOrigin}`,
);

// Probe both loopback families — `next dev -H ::1` (or an IPv6 resolution of
// localhost) would otherwise dodge the corruption guard.
const probe = (host) =>
  new Promise((resolve) => {
    const sock = connect({ port: PORT, host });
    sock.once("connect", () => {
      sock.destroy();
      resolve(true);
    });
    sock.once("error", () => resolve(false));
    sock.setTimeout(1500, () => {
      sock.destroy();
      resolve(false);
    });
  });

const portInUse = (await Promise.all([probe("127.0.0.1"), probe("::1")])).some(
  Boolean,
);

if (portInUse) {
  console.error(
    `✗ Port ${PORT} is in use — stop the dev server before running the gate ` +
      "(building while `next dev` is live corrupts .next).",
  );
  process.exit(1);
}

const steps = [
  ["content-integrity", "node scripts/content-integrity.mjs"],
  ["asset-integrity", "node scripts/asset-integrity.mjs"],
  ["seo-sanity", "node scripts/seo-sanity.mjs"],
  ["typecheck", "./node_modules/.bin/tsc --noEmit"],
  ["lint", "npm run lint"],
  ["build", "./node_modules/.bin/next build"],
  // Validate the built HTML/sitemap/robots metadata contracts (route matrix,
  // 404 isolation, JSON-LD origins) against real output, not source strings.
  ["metadata-guard", "node scripts/metadata-guard.mjs"],
  // Scan the freshly built browser-delivered artifacts for protected
  // non-public addresses before anything exercises them.
  ["privacy-guard", "node scripts/privacy-guard.mjs"],
  // The build above is the artifact being shipped. Exercise it directly so
  // the gate cannot pass dev-only behavior or flake on parallel cold compiles.
  // PLAYWRIGHT_PRODUCTION rides the env object, not a POSIX-only prefix.
  [
    "e2e",
    "./node_modules/.bin/playwright test",
    { PLAYWRIGHT_PRODUCTION: "1" },
  ],
];

for (const [name, cmd, extraEnv] of steps) {
  console.log(`\n━━ gate: ${name} ━━`);
  try {
    execSync(cmd, { stdio: "inherit", env: { ...gateEnv, ...extraEnv } });
  } catch {
    console.error(`\n✗ Gate failed at: ${name}`);
    process.exit(1);
  }
}

console.log(
  "\n✓ Gate passed (content integrity, asset integrity, SEO sanity, typecheck, lint, build, metadata guard, privacy guard, e2e " +
    `against the local production build on port ${PORT}, metadata origin ${gateSiteUrl}). Still required for visual ` +
    "changes: a real browser pass — desktop + mobile, console, overflow, reduced motion.",
);
