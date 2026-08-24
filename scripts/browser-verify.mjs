#!/usr/bin/env node
/**
 * Real-browser visual/behavior pass for MOTIONX visual changes.
 *
 * Run with a local server already available:
 *   npm run dev -- -p 3939
 *   npm run browser:verify
 *
 * Screenshots are written under ignored test-results/browser-verify/.
 */
import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { execFileSync, spawn } from "node:child_process";
import path from "node:path";
import { chromium } from "playwright";

// The target must be a bare, credential-free origin. Signed preview URLs or
// query tokens are unsupported, are never echoed to logs, and must never reach
// the uploaded evidence — only the validated origin is used anywhere.
const rawBaseUrl = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3939";
let parsedBaseUrl;
try {
  parsedBaseUrl = new URL(rawBaseUrl);
} catch {
  console.error(
    "browser-verify: PLAYWRIGHT_BASE_URL is not a parseable URL (value withheld from logs).",
  );
  process.exit(1);
}
if (
  parsedBaseUrl.username ||
  parsedBaseUrl.password ||
  parsedBaseUrl.search ||
  parsedBaseUrl.hash ||
  parsedBaseUrl.pathname !== "/"
) {
  console.error(
    "browser-verify: PLAYWRIGHT_BASE_URL must be a bare origin — credentials, paths, query strings, and fragments are unsupported (value withheld from logs).",
  );
  process.exit(1);
}
const baseURL = parsedBaseUrl.origin;
const outDir = path.join(process.cwd(), "test-results", "browser-verify");
const routes = [
  "/",
  "/pilot",
  "/system-study",
  "/work/renewal",
  "/work/liquid-signal",
  "/work/furia",
  "/work/agentic-trading",
];
const publicEmail = "hello@madebymotionx.com";
const documentedBreakpoints = [1440, 1280, 1024, 768, 430, 390, 375];
const fullPageRoutes = new Set(routes);

mkdirSync(outDir, { recursive: true });

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function cleanName(name) {
  if (name === "/") return "home";
  return name.replace(/^\//, "").replaceAll("/", "-");
}

async function exercisePage(page) {
  await page.evaluate(async () => {
    const root = document.documentElement;

    const settle = () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      );
    const step = Math.max(320, Math.floor(window.innerHeight * 0.8));
    for (let y = 0; y <= root.scrollHeight; y += step) {
      const target = Math.min(y, root.scrollHeight - window.innerHeight);
      window.scrollTo({ top: target, behavior: "instant" });
      await settle();
      if (Math.abs(window.scrollY - target) > 2) {
        throw new Error(`Instant visual-verification scroll missed ${target}px.`);
      }
    }
    window.scrollTo({ top: 0, behavior: "instant" });
    await settle();
    if (Math.abs(window.scrollY) > 2) {
      throw new Error("Visual verification did not return to the top of the page.");
    }
  });
  await page.waitForTimeout(120);
}

async function waitForHeroEntrance(page, preferenceLabel) {
  await page.waitForFunction(() =>
    Array.from(
      document.querySelectorAll("#top .hero-enter, #top .hero-line__inner"),
    ).every((element) =>
      element.getAnimations().every((animation) => animation.playState === "finished"),
    ),
  );
  const cta = await page.locator('section#top a[href="#contact"]').evaluate((element) => {
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return {
      text: element.textContent?.replace(/\s+/g, " ").trim(),
      opacity: Number(style.opacity),
      visibility: style.visibility,
      color: style.color,
      backgroundColor: style.backgroundColor,
      width: rect.width,
      height: rect.height,
    };
  });
  assert(cta.text?.includes("Start a Project"), `${preferenceLabel} hero CTA lost its label.`);
  assert(
    cta.opacity > 0.99 && cta.visibility === "visible" && cta.width > 0 && cta.height > 0,
    `${preferenceLabel} hero CTA is not visibly rendered.`,
  );
  assert(
    cta.color !== cta.backgroundColor,
    `${preferenceLabel} hero CTA text has no contrast against its background.`,
  );
}

async function waitForScrollToSettle(page) {
  await page.evaluate(
    () =>
      new Promise((resolve) => {
        let previous = window.scrollY;
        let stableFrames = 0;
        const sample = () => {
          const current = window.scrollY;
          stableFrames = Math.abs(current - previous) < 0.5 ? stableFrames + 1 : 0;
          previous = current;
          if (stableFrames >= 8) resolve(undefined);
          else requestAnimationFrame(sample);
        };
        requestAnimationFrame(sample);
      }),
  );
}

async function updateHashWithTrackedWebsiteDiff(fingerprint) {
  await new Promise((resolve, reject) => {
    const child = spawn(
      "git",
      ["diff", "--binary", "HEAD", "--", ".", ":(exclude)outreach/**"],
      { cwd: process.cwd(), stdio: ["ignore", "pipe", "pipe"] },
    );
    let stderr = "";
    child.stdout.on("data", (chunk) => fingerprint.update(chunk));
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    child.once("error", reject);
    child.once("close", (code) => {
      if (code === 0) resolve(undefined);
      else reject(new Error(stderr.trim() || `git diff exited with ${code}`));
    });
  });
}

async function collectPage(context, route, viewportName) {
  const page = await context.newPage();
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(String(error)));

  await page.goto(new URL(route, baseURL).toString(), { waitUntil: "domcontentloaded" });
  // Wait for the client bundles and route hydration before exercising the
  // page; screenshots and console evidence should represent settled UI.
  await page.waitForLoadState("networkidle");
  await exercisePage(page);

  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  assert(overflow <= 0, `${viewportName} ${route} has horizontal overflow: ${overflow}px`);

  const screenshot = path.join(outDir, `${viewportName}-${cleanName(route)}.png`);
  await page.screenshot({ path: screenshot });
  const fullPageScreenshot = fullPageRoutes.has(route)
    ? path.join(outDir, `${viewportName}-${cleanName(route)}-full.png`)
    : null;
  if (fullPageScreenshot) {
    await page.screenshot({ path: fullPageScreenshot, fullPage: true });
  }
  const viewport = page.viewportSize();
  await page.close();

  return {
    route,
    viewportName,
    width: viewport?.width,
    height: viewport?.height,
    overflow,
    screenshots: [screenshot, ...(fullPageScreenshot ? [fullPageScreenshot] : [])],
    errors,
  };
}

async function verifyScreenshots(browser) {
  const captures = [];
  for (const viewport of [
    { name: "desktop", width: 1440, height: 1000 },
    { name: "mobile", width: 390, height: 844 },
  ]) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
    });
    for (const route of routes) {
      captures.push(await collectPage(context, route, viewport.name));
    }
    await context.close();
  }

  const consoleErrors = captures.flatMap((capture) =>
    capture.errors.map((error) => `${capture.viewportName} ${capture.route}: ${error}`),
  );
  assert(consoleErrors.length === 0, `Console/page errors:\n${consoleErrors.join("\n")}`);
  return captures;
}

async function verifyLayoutMatrix(browser) {
  const evidence = [];
  for (const width of documentedBreakpoints.filter(
    (breakpoint) => ![1440, 390].includes(breakpoint),
  )) {
    const height = width >= 768 ? 900 : 844;
    const context = await browser.newContext({ viewport: { width, height } });
    for (const route of routes) {
      const page = await context.newPage();
      const errors = [];
      page.on("console", (message) => {
        if (message.type() === "error") errors.push(message.text());
      });
      page.on("pageerror", (error) => errors.push(String(error)));
      await page.goto(new URL(route, baseURL).toString(), {
        waitUntil: "domcontentloaded",
      });
      await page.waitForLoadState("networkidle");
      const overflow = await page.evaluate(
        () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
      );
      const mobileToggleVisible = await page
        .locator('button[aria-controls="mobile-menu"]')
        .isVisible();
      assert(overflow <= 0, `${width}px ${route} has horizontal overflow: ${overflow}px`);
      assert(
        mobileToggleVisible === (width < 768),
        `${width}px ${route} rendered the wrong navigation mode.`,
      );
      assert(
        errors.length === 0,
        `${width}px ${route} console/page errors:\n${errors.join("\n")}`,
      );
      evidence.push({ width, height, route, overflow, mobileToggleVisible, errors });
      await page.close();
    }
    await context.close();
  }
  return evidence;
}

async function verifyHeroVideo(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => {
    const video = document.querySelector("section#top video");
    return video instanceof HTMLVideoElement && video.currentTime > 0;
  }, null, { timeout: 8000 });

  const portfolioVideo = page.locator("#work video").first();
  await portfolioVideo.scrollIntoViewIfNeeded();
  await page.waitForFunction(() => {
    const video = document.querySelector("#work video");
    return video instanceof HTMLVideoElement && !video.paused && video.currentTime > 0;
  }, null, { timeout: 8000 });
  assert(
    (await portfolioVideo.evaluate((video) => video.preload)) === "metadata",
    "Normal portfolio video should restore its requested metadata preload.",
  );
  assert(
    (await page.locator("#work video").count()) === 1,
    "Selected Work should mount exactly one active film.",
  );
  await page
    .locator("#work")
    .getByRole("button", { name: "Preview film: Liquid Signal" })
    .click();
  await page.waitForFunction(() => {
    const panel = document.querySelector("#selected-work-panel");
    const video = panel?.querySelector("video");
    return (
      panel?.querySelector("h3")?.textContent?.trim() === "Liquid Signal" &&
      video instanceof HTMLVideoElement &&
      video.currentSrc.endsWith("/videos/liquid-signal.c24f676131a6.mp4") &&
      video.currentTime > 0
    );
  }, null, { timeout: 8000 });
  assert(
    new URL(page.url()).hash === "#work-liquid-signal",
    "Selected Work selection should be URL-addressable.",
  );
  await context.close();
}

async function verifyBlockedPortfolioPlayback(page, preferenceLabel, mediaRequests) {
  const video = page.locator("#work video").first();
  await video.scrollIntoViewIfNeeded();
  await page.waitForTimeout(500);

  const blockedState = await video.evaluate((element) => ({
    paused: element.paused,
    currentTime: element.currentTime,
    preload: element.preload,
  }));
  assert(blockedState.paused, `${preferenceLabel} portfolio video should remain paused.`);
  assert(
    blockedState.currentTime <= 0.01,
    `${preferenceLabel} portfolio video should stay on the poster frame.`,
  );
  assert(
    blockedState.preload === "none",
    `${preferenceLabel} portfolio video should keep preload="none".`,
  );
  assert(
    mediaRequests.length === 0,
    `${preferenceLabel} requested MP4 media before explicit play: ${mediaRequests.join(", ")}`,
  );

  await page.locator("#work").getByRole("button", { name: "Play video" }).first().click();
  await page.waitForFunction(() => {
    const video = document.querySelector("#work video");
    return video instanceof HTMLVideoElement && !video.paused && video.currentTime > 0;
  }, null, { timeout: 8000 });
  assert(
    (await video.evaluate((element) => element.preload)) === "none",
    `${preferenceLabel} manual playback should not opt back into eager preload.`,
  );
  assert(
    mediaRequests.some((request) =>
      request.endsWith("/videos/renewal-botanical-mobile.5bbade5a0a0e.mp4"),
    ),
    `${preferenceLabel} manual play at 390px should request the MOBILE portfolio variant.`,
  );
  assert(
    !mediaRequests.some((request) =>
      request.endsWith("/videos/renewal-botanical.d503303f4c24.mp4"),
    ),
    `${preferenceLabel} manual play at 390px must not fetch the desktop copy.`,
  );
}

async function verifyReducedMotion(browser) {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  const errors = [];
  const mediaRequests = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname;
    if (pathname.endsWith(".mp4")) mediaRequests.push(pathname);
  });

  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  // Let the below-fold client boundaries hydrate before Playwright captures a
  // screenshot. Capturing during progressive hydration temporarily touches
  // form-control styles (caret hiding), which creates a test-induced React
  // attribute warning that never occurs during normal browsing.
  await page.waitForTimeout(1800);
  await waitForHeroEntrance(page, "Reduced-motion");
  await page.getByRole("link", { name: "View Selected Work" }).click({ trial: true });
  const heroState = await page.locator("section#top video").evaluate((video) => ({
    paused: video.paused,
    currentTime: video.currentTime,
    preload: video.preload,
  }));
  assert(heroState.paused, "Reduced-motion hero video should remain paused.");
  assert(heroState.currentTime <= 0.01, "Reduced-motion hero video should stay on the poster frame.");
  assert(heroState.preload === "none", "Reduced-motion hero video should keep preload=\"none\".");
  await page.screenshot({ path: path.join(outDir, "reduced-motion-home.png") });
  await verifyBlockedPortfolioPlayback(page, "Reduced-motion", mediaRequests);
  assert(errors.length === 0, `Reduced-motion console/page errors:\n${errors.join("\n")}`);
  await context.close();
}

async function verifySaveData(browser) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  await context.addInitScript(() => {
    const descriptor = {
      configurable: true,
      value: { saveData: true },
    };
    try {
      Object.defineProperty(navigator, "connection", descriptor);
    } catch {
      Object.defineProperty(Navigator.prototype, "connection", descriptor);
    }
  });

  const page = await context.newPage();
  const errors = [];
  const mediaRequests = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("request", (request) => {
    const pathname = new URL(request.url()).pathname;
    if (pathname.endsWith(".mp4")) mediaRequests.push(pathname);
  });

  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  // Match the screenshot pass: wait for progressive hydration before capture.
  await page.waitForTimeout(1800);
  await waitForHeroEntrance(page, "Save-Data");
  const heroState = await page.locator("section#top video").evaluate((video) => ({
    paused: video.paused,
    currentTime: video.currentTime,
    preload: video.preload,
  }));
  assert(heroState.paused, "Save-Data hero video should remain paused.");
  assert(heroState.currentTime <= 0.01, "Save-Data hero video should stay on the poster frame.");
  assert(heroState.preload === "none", "Save-Data hero video should keep preload=\"none\".");
  await page.screenshot({ path: path.join(outDir, "save-data-home.png") });
  await verifyBlockedPortfolioPlayback(page, "Save-Data", mediaRequests);
  assert(errors.length === 0, `Save-Data console/page errors:\n${errors.join("\n")}`);
  await context.close();
}

async function verifyMobileContactLanding(browser) {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await context.newPage();
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(String(error)));

  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1800);
  await page.locator("section#top").getByRole("link", { name: "Start a Project" }).click();
  await page.waitForFunction(() => document.activeElement?.id === "contact-heading");
  await waitForScrollToSettle(page);

  const landing = await page.locator("#contact").evaluate((section) => {
    const form = section.querySelector("form");
    const firstInput = section.querySelector("#contact-name");
    const formColumn = form?.parentElement;
    const supportingDetails = formColumn?.nextElementSibling;
    const inputRect = firstInput?.getBoundingClientRect();
    const sectionRect = section.getBoundingClientRect();
    const headerHeight = document.querySelector("header")?.getBoundingClientRect().height ?? 0;
    return {
      formBeforeDetails: Boolean(
        formColumn &&
          supportingDetails &&
          supportingDetails.textContent?.includes("What happens next"),
      ),
      firstInputInViewport: Boolean(
        inputRect &&
          inputRect.top >= headerHeight &&
          inputRect.bottom <= window.innerHeight - 24,
      ),
      sectionLandedBelowHeader:
        sectionRect.top >= headerHeight - 4 && sectionRect.top <= headerHeight + 48,
    };
  });
  assert(
    landing.formBeforeDetails,
    "Mobile contact form should precede supporting details in DOM order.",
  );
  assert(landing.firstInputInViewport, "Mobile contact landing should expose the first required input.");
  assert(
    landing.sectionLandedBelowHeader,
    "Mobile contact section should settle directly beneath the fixed header.",
  );
  await page.screenshot({ path: path.join(outDir, "mobile-contact-landing.png") });
  assert(errors.length === 0, `Mobile contact console/page errors:\n${errors.join("\n")}`);
  await context.close();
}

async function verifyNavigationAndContact(browser) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await context.route(/mail\.google\.com/, (route) =>
    route.fulfill({ status: 200, contentType: "text/html", body: "ok" }),
  );

  async function submitCompose(activeContext, activePage) {
    const submit = activePage
      .locator("#contact")
      .getByRole("button", { name: "Continue in Gmail" });
    await submit.scrollIntoViewIfNeeded();
    const popupPromise = activeContext.waitForEvent("page", { timeout: 10000 }).catch(() => null);
    await submit.click();
    const popup = await popupPromise;
    if (popup) {
      const params = new URL(popup.url()).searchParams;
      await popup.close();
      return params;
    }

    if (activePage.url().includes("mail.google.com")) {
      return new URL(activePage.url()).searchParams;
    }

    const status = await activePage.getByRole("status").innerText().catch(() => "");
    throw new Error(`Gmail compose did not open. Contact status: ${status}`);
  }

  const page = await context.newPage();
  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1800);
  await page
    .getByRole("navigation", { name: "Primary" })
    .getByRole("link", { name: "Start a Project" })
    .click();
  await page.waitForFunction(() => document.activeElement?.id === "contact-heading");

  await page.locator("#contact-name").fill("Visual Check");
  await page.locator("#contact-email").fill("visual@example.com");
  await page.locator("#contact-message").fill("Checking the browser verification path.");
  const params = await submitCompose(context, page);
  assert(params.get("to") === publicEmail, "Gmail compose must target the public hello@ address.");
  assert(
    params.get("su")?.startsWith("MOTIONX Project Inquiry"),
    "Normal contact should use the non-pilot inquiry subject.",
  );
  await context.close();

  const pilotContext = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  await pilotContext.route(/mail\.google\.com/, (route) =>
    route.fulfill({ status: 200, contentType: "text/html", body: "ok" }),
  );
  const pilot = await pilotContext.newPage();
  await pilot.goto(
    new URL(
      "/?type=Film%20%2B%20Website%20Launch%20System&pilot=launch-system#contact",
      baseURL,
    ).toString(),
    { waitUntil: "domcontentloaded" },
  );
  await pilot.locator("#contact select").first().waitFor({ state: "visible" });
  await pilot.waitForFunction(
    () => document.querySelector("#contact select")?.value === "Film + Website Launch System",
  );
  await pilot.locator("#contact-name").fill("Pilot Check");
  await pilot.locator("#contact-email").fill("pilot@example.com");
  await pilot.locator("#contact-message").fill("Checking the pilot browser verification path.");
  const pilotParams = await submitCompose(pilotContext, pilot);
  const pilotSubject = pilotParams.get("su") ?? "";
  assert(
    pilotSubject.startsWith("MOTIONX Pilot Project Inquiry"),
    "Pilot referral should use the pilot inquiry subject.",
  );
  await pilotContext.close();
}

/**
 * DETECT the served artifact's build mode from the rendered application
 * (layout.tsx bakes `data-motionx-env` into <body> at build/render time)
 * instead of trusting a caller-provided label. PLAYWRIGHT_PRODUCTION=1 is an
 * EXPECTATION: verification fails when production evidence was requested but
 * the served artifact is a development build.
 */
async function detectServerMode(browser) {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  const raw = await page.evaluate(() => document.body.dataset.motionxEnv ?? "");
  await context.close();
  return raw === "production" || raw === "development" ? raw : "unknown";
}

const browser = await chromium.launch({ headless: true });
try {
  const detectedServerMode = await detectServerMode(browser);
  const expectedProduction = process.env.PLAYWRIGHT_PRODUCTION === "1";
  assert(
    !expectedProduction || detectedServerMode === "production",
    `Production evidence was requested (PLAYWRIGHT_PRODUCTION=1) but the served artifact reports "${detectedServerMode}".`,
  );

  const captures = await verifyScreenshots(browser);
  const layoutMatrix = await verifyLayoutMatrix(browser);
  await verifyHeroVideo(browser);
  await verifyReducedMotion(browser);
  await verifySaveData(browser);
  await verifyMobileContactLanding(browser);
  await verifyNavigationAndContact(browser);

  let revision = process.env.GITHUB_SHA ?? "unknown";
  let websiteStatus = [];
  let websiteDiffSha256 = null;
  if (revision === "unknown") {
    try {
      revision = execFileSync("git", ["rev-parse", "HEAD"], {
        cwd: process.cwd(),
        encoding: "utf8",
      }).trim();
    } catch {
      // Evidence remains useful outside a Git checkout.
    }
  }
  try {
    websiteStatus = execFileSync(
      "git",
      ["status", "--porcelain", "--", ".", ":(exclude)outreach/**"],
      { cwd: process.cwd(), encoding: "utf8" },
    )
      .trimEnd()
      .split("\n")
      .filter(Boolean);

    if (websiteStatus.length > 0) {
      const fingerprint = createHash("sha256");
      await updateHashWithTrackedWebsiteDiff(fingerprint);
      const untracked = execFileSync(
        "git",
        [
          "ls-files",
          "--others",
          "--exclude-standard",
          "-z",
          "--",
          ".",
          ":(exclude)outreach/**",
        ],
        { cwd: process.cwd(), encoding: "utf8" },
      )
        .split("\0")
        .filter(Boolean)
        .sort();
      for (const file of untracked) {
        fingerprint.update(file);
        fingerprint.update(readFileSync(path.join(process.cwd(), file)));
      }
      websiteDiffSha256 = fingerprint.digest("hex");
    }
  } catch (error) {
    if (revision !== "unknown") {
      throw new Error(
        `Could not fingerprint the verified website state: ${
          error instanceof Error ? error.message : String(error)
        }`,
      );
    }
    // Non-Git environments still get route and browser evidence.
  }
  const screenshots = captures.flatMap((capture) => capture.screenshots);
  const evidencePath = path.join(outDir, "evidence.json");
  writeFileSync(
    evidencePath,
    `${JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        // DETECTED from the rendered artifact's build marker — not a caller
        // label. serverModeExpected records what the caller asked for.
        serverMode: detectedServerMode,
        serverModeExpected: expectedProduction ? "production" : "unspecified",
        revision,
        websiteWorkingTree: {
          dirty: websiteStatus.length > 0,
          status: websiteStatus,
          diffSha256: websiteDiffSha256,
        },
        baseURL,
        browser: { name: "chromium", version: browser.version() },
        routes,
        documentedBreakpoints,
        captures: captures.map((capture) => ({
          ...capture,
          screenshots: capture.screenshots.map((screenshot) =>
            path.relative(process.cwd(), screenshot),
          ),
        })),
        layoutMatrix,
        checks: [
          "instant below-fold traversal and full-page route captures",
          "hero and portfolio playback",
          "reduced-motion and Save-Data hero CTA visibility",
          "reduced-motion poster-only network policy",
          "Save-Data poster-only network policy",
          "mobile contact landing",
          "normal and pilot Gmail subjects",
        ],
      },
      null,
      2,
    )}\n`,
  );

  console.log("Browser verification passed.");
  console.log("Screenshots:");
  for (const screenshot of screenshots) console.log(`- ${screenshot}`);
  console.log(`- ${path.join(outDir, "reduced-motion-home.png")}`);
  console.log(`- ${path.join(outDir, "save-data-home.png")}`);
  console.log(`- ${path.join(outDir, "mobile-contact-landing.png")}`);
  console.log(`Evidence: ${evidencePath}`);
} finally {
  await browser.close();
}
