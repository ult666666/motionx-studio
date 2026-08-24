#!/usr/bin/env node
/**
 * MOTIONX post-build privacy guard.
 *
 * Recursively scans the browser-delivered build artifacts — everything under
 * `.next/static` plus the prerendered HTML/RSC payloads under
 * `.next/server/app` — and fails if a protected non-public address appears in
 * anything a visitor's browser can download. Source-level checks
 * (content-integrity, seo-sanity) guard intent; this guards the actual
 * shipped bytes, so a future import graph change can't silently reintroduce
 * a leak. Runs in the gate after `next build`, before e2e.
 *
 * It also asserts the PUBLIC address is still present in at least one public
 * artifact — proving the scanner is reading the real output tree, not
 * passing vacuously against an empty directory.
 */
import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const failures = [];
let scanned = 0;

// Protected values live here (scripts are never shipped); failure output
// names the policy, not the value.
const PROTECTED = [
  { value: "charles@madebymotionx.com", name: "the non-public founder address" },
  { value: "daichunyu666@gmail.com", name: "the private backup Gmail address" },
];
const PUBLIC_EMAIL = "hello@madebymotionx.com";

// Prerendered payload extensions the browser actually receives from
// .next/server/app; the .js route bundles there execute server-side only.
const SERVER_PUBLIC_EXTENSIONS = new Set([".html", ".rsc", ".meta", ".body"]);

function walk(dir, filter) {
  const absolute = path.join(root, dir);
  if (!existsSync(absolute)) return [];
  return readdirSync(absolute).flatMap((entry) => {
    const rel = path.join(dir, entry);
    if (statSync(path.join(root, rel)).isDirectory()) return walk(rel, filter);
    return !filter || filter(rel) ? [rel] : [];
  });
}

if (!existsSync(path.join(root, ".next"))) {
  console.error("✗ privacy-guard: no .next build output — run `next build` first.");
  process.exit(1);
}

const files = [
  ...walk(".next/static"),
  ...walk(".next/server/app", (file) =>
    SERVER_PUBLIC_EXTENSIONS.has(path.extname(file)),
  ),
];

let publicEmailSeen = false;
for (const file of files) {
  const contents = readFileSync(path.join(root, file));
  scanned += 1;
  for (const { value, name } of PROTECTED) {
    if (contents.includes(value)) {
      failures.push(`${file} contains ${name}.`);
    }
  }
  if (!publicEmailSeen && contents.includes(PUBLIC_EMAIL)) {
    publicEmailSeen = true;
  }
}

if (files.length === 0) {
  failures.push("No public build artifacts were found to scan — the guard cannot certify this build.");
}
if (!publicEmailSeen) {
  failures.push(
    `The public address ${PUBLIC_EMAIL} was not found in any public artifact — either the contact surface broke or the scanner is reading the wrong tree.`,
  );
}

if (failures.length > 0) {
  console.error("MOTIONX privacy guard failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(
  `MOTIONX privacy guard passed (${scanned} public artifacts scanned; protected addresses absent, public address present).`,
);
