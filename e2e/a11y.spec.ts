import { test, expect, type Page, type TestInfo } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Automated accessibility gate: axe-core scan of every route.
 * Fails on serious/critical violations; anything below that is reported in
 * the assertion message when a failure occurs but does not gate.
 */

const ROUTES = [
  "/",
  "/pilot",
  "/system-study",
  "/work/renewal",
  "/work/liquid-signal",
  "/work/furia",
  "/work/agentic-trading",
  "/no-such-page",
];

// Scan under reduced motion: reveal transitions collapse to instant, so axe
// never measures colors mid-animation (ancestor opacity < 1 darkens composited
// text and produced timing-dependent contrast flakes).
test.use({ contextOptions: { reducedMotion: "reduce" } });

/** Scroll through the page so whileInView reveals fire and the full DOM is
 *  in its final, visible state before axe measures it. */
async function revealAll(page: Page) {
  await page.evaluate(async () => {
    const step = Math.max(200, window.innerHeight / 2);
    for (let y = 0; y <= document.body.scrollHeight; y += step) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 80));
    }
    window.scrollTo(0, 0);
  });
  // reduced motion makes reveals instant; a short settle is still polite
  await page.waitForTimeout(300);
}

async function scan(
  page: Page,
  testInfo: TestInfo,
  attachmentName: string,
  include?: string,
) {
  // The video-caption rule now gates for real: every audio-bearing portfolio
  // film ships an English WebVTT track. Only the hero teaser is excluded — it has
  // NO audio track by design (asset-integrity enforces zero audio streams),
  // so there is no audible content to caption.
  let builder = new AxeBuilder({ page }).exclude("section#top video");
  if (include) builder = builder.include(include);
  const results = await builder.analyze();
  await testInfo.attach(`${attachmentName}-axe`, {
    body: Buffer.from(JSON.stringify(results.violations, null, 2)),
    contentType: "application/json",
  });
  const gating = results.violations.filter((violation) =>
    ["serious", "critical"].includes(violation.impact ?? ""),
  );
  expect(
    gating,
    gating
      .map(
        (violation) =>
          `${violation.impact}: ${violation.id} — ${violation.help}\n  ${violation.nodes
            .slice(0, 4)
            .map((node) => node.target.join(" "))
            .join("\n  ")}`,
      )
      .join("\n"),
  ).toEqual([]);
}

for (const route of ROUTES) {
  test(`axe: no serious/critical violations on ${route}`, async ({ page }, testInfo) => {
    await page.goto(route);
    await revealAll(page);
    await scan(page, testInfo, route === "/" ? "home" : route.replaceAll("/", "-"));
  });
}

test("axe: menu, edit-bay, and validation states stay clean", async ({ page }, testInfo) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Open menu" }).click();
  await scan(page, testInfo, "mobile-menu", "#mobile-menu");
  await page.keyboard.press("Escape");

  await page.setViewportSize({ width: 1280, height: 800 });
  const work = page.locator("#work");
  await work.scrollIntoViewIfNeeded();
  await work
    .getByRole("button", { name: "Preview film: Agentic Trading" })
    .click();
  await expect(work.locator("article h3")).toHaveText("Agentic Trading");
  await scan(page, testInfo, "selected-work-edit-bay", "#work");

  const submit = page.locator("#contact").getByRole("button", {
    name: "Continue in Gmail",
  });
  await submit.scrollIntoViewIfNeeded();
  await submit.click();
  await scan(page, testInfo, "contact-validation", "#contact");
});

/* ── Focused interface regressions ──────────────────────────────
   These cover stable accessible naming, compositor-safe navigation state, and
   hovered contrast—contracts that a resting-state axe scan cannot fully see. */

test("contact description keeps a stable name while its count stays descriptive", async ({
  page,
}) => {
  await page.goto("/#contact");
  const description = page.locator("#contact-message");
  const label = page.locator('label[for="contact-message"]');

  await expect(description).toHaveAccessibleName("Project description");
  await expect(description).toHaveAccessibleDescription("0/2000");

  await label.click();
  await expect(description).toBeFocused();
  await description.fill("A focused launch.");

  await expect(description).toHaveAccessibleName("Project description");
  await expect(description).toHaveAccessibleDescription("17/2000");
});

test("navigation keeps its blur treatment without animating backdrop-filter", async ({
  page,
}) => {
  await page.goto("/");
  const header = page.locator("header").first();
  const primaryNavigation = page.getByRole("navigation", { name: "Primary" });

  await expect
    .poll(() =>
      header.evaluate((element) =>
        getComputedStyle(element)
          .transitionProperty.split(",")
          .map((property) => property.trim()),
      ),
    )
    .not.toContain("backdrop-filter");

  await page.evaluate(() => window.scrollTo(0, 160));
  await expect(header).toHaveClass(/backdrop-blur-xl/);
  await expect
    .poll(() =>
      header.evaluate((element) => getComputedStyle(element).backdropFilter),
    )
    .toContain("blur");

  for (const section of [
    { id: "work", link: "Work" },
    { id: "services", link: "Services" },
  ]) {
    await page.locator(`#${section.id}`).evaluate((element) =>
      element.scrollIntoView({
        behavior: "auto",
        block: "start",
      }),
    );
    await expect(
      primaryNavigation.getByRole("link", {
        name: section.link,
        exact: true,
      }),
    ).toHaveAttribute("aria-current", "location");
  }
});

function relativeLuminance(rgb: [number, number, number]): number {
  const [r, g, b] = rgb.map((channel) => {
    const c = channel / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function parseRgb(value: string): [number, number, number] {
  const match = value.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!match) throw new Error(`Unparseable computed color: ${value}`);
  return [Number(match[1]), Number(match[2]), Number(match[3])];
}

function contrastRatio(foreground: string, background: string): number {
  const fg = relativeLuminance(parseRgb(foreground));
  const bg = relativeLuminance(parseRgb(background));
  return (Math.max(fg, bg) + 0.05) / (Math.min(fg, bg) + 0.05);
}

test("primary CTA keeps WCAG AA contrast in the hovered state", async ({ page }) => {
  await page.goto("/");
  const cta = page.locator("section#top").getByRole("link", { name: "Start a Project" });
  await cta.scrollIntoViewIfNeeded();

  const resting = await cta.evaluate((element) => {
    const style = getComputedStyle(element);
    return { color: style.color, background: style.backgroundColor };
  });
  expect(contrastRatio(resting.color, resting.background)).toBeGreaterThanOrEqual(4.5);

  await cta.hover();
  // Wait out the color transition: sample until two consecutive reads agree.
  let previous = "";
  await expect
    .poll(async () => {
      const current = await cta.evaluate(
        (element) => getComputedStyle(element).backgroundColor,
      );
      const settled = current === previous;
      previous = current;
      return settled;
    })
    .toBe(true);

  const hovered = await cta.evaluate((element) => {
    const style = getComputedStyle(element);
    return { color: style.color, background: style.backgroundColor };
  });
  // The hovered background must be exactly the electric accent (#6D7CFF) —
  // not merely "different" — so the test can't pass on a broken hover or a
  // drifted palette. Every primary CTA shares the same .cta-primary pairing,
  // so this one canonical instance guards the treatment on all routes.
  expect(hovered.background).toBe("rgb(109, 124, 255)");
  expect(contrastRatio(hovered.color, hovered.background)).toBeGreaterThanOrEqual(4.5);
});

test("text selection colors keep WCAG AA contrast", async ({ page, browserName }) => {
  test.skip(
    browserName === "webkit",
    "WebKit does not expose ::selection through getComputedStyle",
  );
  await page.goto("/");
  const selection = await page.evaluate(() => {
    const style = getComputedStyle(document.body, "::selection");
    return { color: style.color, background: style.backgroundColor };
  });
  expect(contrastRatio(selection.color, selection.background)).toBeGreaterThanOrEqual(4.5);
});

test("axe: post-submit fallback helper stays clean", async ({
  page,
  context,
  browserName,
}, testInfo) => {
  test.skip(browserName === "webkit", "WebKit headless cannot model the Gmail popup");
  await context.route(/mail\.google\.com/, (route) =>
    route.fulfill({ status: 200, contentType: "text/html", body: "ok" }),
  );
  await page.goto("/#contact");
  await page.locator("#contact-name").fill("Accessibility Check");
  await page.locator("#contact-email").fill("check@example.com");
  await page.locator("#contact-message").fill("Checking the prepared-draft helper.");
  const popupPromise = context.waitForEvent("page");
  await page.getByRole("button", { name: "Continue in Gmail" }).click();
  const popup = await popupPromise;
  await popup.close();
  await scan(page, testInfo, "contact-helper", "#contact");
});
