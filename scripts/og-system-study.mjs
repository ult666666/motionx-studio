#!/usr/bin/env node
/**
 * Regenerate the dedicated /system-study social card from the page's own
 * rendered header (the AURA visuals are pure CSS/SVG, so the card is captured
 * from the live route rather than extracted from a film).
 *
 * Run with a local server already available on port 3939:
 *   npm run og:system-study
 *
 * Output: public/og/system-study.jpg (1200x630 JPEG — the format LinkedIn/
 * WhatsApp/iMessage crawlers reliably preview). The capture emulates reduced
 * motion so every entrance renders in its final state, and keeps the page's
 * visible "Concept" provenance inside the frame.
 */
import path from "node:path";
import { chromium } from "playwright";

const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3939";
const outFile = path.join(process.cwd(), "public", "og", "system-study.jpg");

const browser = await chromium.launch();
try {
  const context = await browser.newContext({
    // deviceScaleFactor stays 1: the crawler contract is exactly 1200x630.
    viewport: { width: 1200, height: 630 },
    deviceScaleFactor: 1,
    reducedMotion: "reduce",
  });
  const page = await context.newPage();
  await page.goto(`${baseURL}/system-study`, { waitUntil: "load" });
  // Frame the card: drop site navigation chrome and the back link (they read
  // as UI, not a share card) and rebalance the top padding. The eyebrow's
  // visible "Concept" mark stays inside the frame — provenance is part of
  // the card, not just its alt text.
  await page.addStyleTag({
    content: [
      "body > header { display: none !important; }",
      'main header a[href="/#launch-system"] { display: none !important; }',
      // 5.25rem keeps the cut-off top of the disclosure block below the fold
      // so the frame ends on the intro line, not sliced text.
      "main { padding-top: 5.25rem !important; }",
    ].join("\n"),
  });
  await page.evaluate(() => document.fonts.ready);
  // Let CSS transitions/entrances settle even under reduced motion.
  await page.evaluate(
    () =>
      new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve)),
      ),
  );
  await page.screenshot({
    path: outFile,
    type: "jpeg",
    quality: 88,
    clip: { x: 0, y: 0, width: 1200, height: 630 },
  });
  console.log(`Wrote ${path.relative(process.cwd(), outFile)}`);
} finally {
  await browser.close();
}
