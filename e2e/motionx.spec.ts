import { test, expect, type Page } from "@playwright/test";

const PUBLIC_EMAIL = "hello@madebymotionx.com";
const WORK_PROJECT_TITLES = {
  renewal: "Renewal",
  "liquid-signal": "Liquid Signal",
  furia: "Furia",
  "agentic-trading": "Agentic Trading",
} as const;
type WorkSlug = keyof typeof WORK_PROJECT_TITLES;

function workPreview(page: Page, slug: WorkSlug) {
  return page
    .locator("#work")
    .getByRole("button", { name: `Preview film: ${WORK_PROJECT_TITLES[slug]}` });
}

/**
 * Next logs its own recovery from an aborted RSC prefetch through
 * `console.error`, so it lands in the error channel despite not being a fault.
 * These tests navigate faster than a person does; against a remote base URL the
 * added latency leaves a prefetch in flight when the next navigation cancels
 * it, and WebKit surfaces the cancellation as `TypeError: Load failed`. Next
 * then falls back to a browser navigation and the route loads normally —
 * verified by hand on WebKit against production: a user-paced visit logs zero
 * errors, and clicking through to /system-study renders correctly.
 *
 * Matching is deliberately narrow — it requires Next's own fallback sentence,
 * so a genuine RSC or network failure without that recovery still fails.
 */
const ABORTED_PREFETCH =
  /Failed to fetch RSC payload for .*\. Falling back to browser navigation/;

/** Collect console + page errors so a test can assert the page is clean. */
function trackErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error" && !ABORTED_PREFETCH.test(m.text())) errors.push(m.text());
  });
  page.on("pageerror", (e) => errors.push(String(e)));
  return errors;
}

test.describe("Core routes", () => {
  test("homepage loads with title and single h1", async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto("/");
    await expect(page).toHaveTitle(/MOTIONX/);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.locator("h1")).toContainText("final click");
    expect(errors, errors.join("\n")).toHaveLength(0);
  });

  test("the hero screening links directly to its canonical case study", async ({
    page,
  }) => {
    await page.goto("/");
    await expect(
      page.getByRole("link", {
        name: "Open the Agentic Trading case study",
      }),
    ).toHaveAttribute("href", "/work/agentic-trading");
  });

  test("core marketing content remains readable without JavaScript", async ({
    browser,
    baseURL,
  }) => {
    const context = await browser.newContext({ javaScriptEnabled: false });
    const page = await context.newPage();
    try {
      await page.goto(`${baseURL}/`);
      await expect(page.locator("h1")).toContainText("final click");
      await expect(page.locator("#work").getByText("Selected Work", { exact: true }).first()).toBeVisible();
      await expect(page.locator("#services").getByText("What we build, end to end.")).toBeVisible();
      await expect(page.locator("#contact-heading")).toContainText("build your launch");

      await page.goto(`${baseURL}/system-study`);
      await expect(page.locator("h1")).toContainText("One visual world");
      await expect(page.getByText("Concept disclosure", { exact: true })).toBeVisible();
      for (const label of [
        "Focal hierarchy",
        "Responsive translation",
        "Single-action path",
      ]) {
        await expect(page.getByText(label, { exact: true })).toBeVisible();
      }
    } finally {
      await context.close();
    }
  });

  test("pilot page loads with prices", async ({ page }) => {
    await page.goto("/pilot");
    await expect(page.locator("h1")).toContainText("pilot pricing");
    await expect(page.getByText("$399").first()).toBeVisible();
    await expect(page.getByText("$999").first()).toBeVisible();
  });

  test("pilot offers show who each is for", async ({ page }) => {
    await page.goto("/pilot");
    // Each offer leads with an audience hook so a prospect can self-identify.
    await expect(
      page.getByText(
        "For one product with usable footage or assets and one focused launch moment.",
      ),
    ).toBeVisible();
    await expect(
      page.getByText("For a serious launch where the film and site must feel like one."),
    ).toBeVisible();
  });

  test("each pilot comparison leads its scope with the core deliverable", async ({
    page,
  }) => {
    await page.goto("/pilot");
    for (const [id, deliverable] of [
      ["product-film", "15–20 second motion-design-led product film"],
      ["motion-first-website", "Custom responsive one-page launch website"],
      [
        "launch-system",
        "The complete connected launch — film, site, and direction",
      ],
    ] as const) {
      const scopeItems = page.locator(`#${id} ul li`);
      await expect(scopeItems.first()).toHaveText(deliverable);
    }
  });

  test("pilot page explains scope and next steps", async ({ page }) => {
    await page.goto("/pilot");
    await expect(page.getByText("What is not included")).toBeVisible();
    await expect(page.getByText("What happens next").first()).toBeVisible();
    await expect(page.getByText(/Gmail draft for you to review and send/i)).toBeVisible();
    await expect(
      page.getByText(/On-location camera crews or travel unless they are discussed/i),
    ).toBeVisible();
  });

  test("pilot page presents the signature engagement without scarcity claims", async ({ page }) => {
    await page.goto("/pilot");
    await expect(page.getByText("Signature engagement", { exact: true })).toBeVisible();
    await expect(page.locator("body")).not.toContainText(
      /best value|first three|priority booking/i,
    );
  });

  test("home states who the studio is for", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText(/beauty (?:&|and) wellness/i).first()).toBeVisible();
    await expect(page.getByText(/independent studio led by Charles Dai/i)).toBeVisible();
    await expect(
      page.getByText(/an on-location camera crew or recurring travel is not a standard/i),
    ).toBeVisible();
    await expect(
      page.getByText("Does MOTIONX provide on-location filming?"),
    ).toBeVisible();
  });

  test("home explains the integrated launch system and honest standards", async ({ page }) => {
    await page.goto("/");
    const launchSystem = page.locator("#launch-system");
    await expect(
      launchSystem.getByText("Production sequence", { exact: true }),
    ).toHaveCount(0);
    await expect(launchSystem.getByText("Product Film", { exact: true })).toBeVisible();
    await expect(
      launchSystem.getByText("Motion-First Website", { exact: true }),
    ).toBeVisible();
    await expect(launchSystem.getByText("Campaign System", { exact: true })).toBeVisible();
    await expect(launchSystem.getByText("Campaign frames")).toBeVisible();
    await expect(launchSystem.getByRole("link")).toHaveCount(1);
    await expect(
      page.locator("#services").getByText("Best fit", { exact: true }),
    ).toHaveCount(4);
    await expect(
      page.getByText(
        "A product with usable footage or product assets that needs one cinematic visual anchor.",
        { exact: true },
      ),
    ).toBeVisible();
    await expect(page.getByText("Quality standards")).toBeVisible();
    await expect(page.getByText("Clear provenance")).toBeVisible();
    await expect(page.getByText("Can I start with one service?")).toBeVisible();
    await expect(page.locator("#process ol > li")).toHaveCount(4);
    await expect(page.locator("#contact details")).toHaveCount(3);
    const footerLinks = page
      .getByRole("navigation", { name: "Footer" })
      .getByRole("link");
    await expect(footerLinks).toHaveCount(5);
    await expect(footerLinks).toHaveText([
      "Work",
      "Services",
      "Process",
      "Studio",
      "Pilot",
    ]);
    for (const [index, href] of [
      "/#work",
      "/#services",
      "/#process",
      "/#studio",
      "/pilot",
    ].entries()) {
      await expect(footerLinks.nth(index)).toHaveAttribute("href", href);
    }
  });

  test("system study keeps its concept disclosure and inquiry path visible", async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto("/system-study");
    await expect(page.locator("h1")).toContainText("One visual world");
    await expect(page.getByText("Concept disclosure", { exact: true })).toBeVisible();
    await expect(page.getByText(/AURA is not a real client or commercial product/i)).toBeVisible();
    for (const label of [
      "Focal hierarchy",
      "Responsive translation",
      "Single-action path",
    ]) {
      await expect(page.getByText(label, { exact: true })).toBeVisible();
    }
    for (const stage of [
      "Film-frame direction",
      "Responsive launch page",
      "Campaign format system",
    ]) {
      await expect(page.getByText(stage, { exact: true })).toBeVisible();
    }
    const prototype = page.locator("article").filter({
      has: page.locator("#prototype-heading"),
    });
    await expect(
      prototype
        .locator("p")
        .filter({ hasText: /^One object, one headline, and one clear first action\.$/ }),
    ).toBeVisible();
    const principleControls = prototype.getByRole("button");
    await expect(principleControls).toHaveCount(3);
    const focalControl = prototype.getByRole("button", {
      name: /Focal hierarchy/i,
    });
    const responsiveControl = prototype.getByRole("button", {
      name: /Responsive translation/i,
    });
    const actionControl = prototype.getByRole("button", {
      name: /Single-action path/i,
    });
    await expect(focalControl).toHaveAccessibleName("Focal hierarchy");
    await expect(focalControl).toHaveAccessibleDescription(
      "One object, one headline, and one clear first action.",
    );
    await expect(focalControl).toHaveAttribute("aria-pressed", "true");
    await responsiveControl.click();
    await expect(responsiveControl).toHaveAttribute("aria-pressed", "true");
    await expect(focalControl).toHaveAttribute("aria-pressed", "false");
    await actionControl.focus();
    await page.keyboard.press("Space");
    await expect(actionControl).toHaveAttribute("aria-pressed", "true");
    await expect(prototype.locator('[aria-live="polite"]')).toHaveText(
      "Active principle: Single-action path",
    );

    const cta = page.getByRole("link", {
      name: "Discuss a Launch System",
      exact: true,
    });
    await cta.scrollIntoViewIfNeeded();
    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute(
      "href",
      "/?type=Film%20%2B%20Website%20Launch%20System#contact",
    );
    expect(errors, errors.join("\n")).toHaveLength(0);
  });

  test("case-study routes load cleanly", async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto("/work/renewal");
    await expect(page.locator("h1")).toContainText("Renewal");
    await expect(page.getByText(/Self-initiated concept study/i)).toBeVisible();
    await expect(page.locator("header").getByText("Concept Project", { exact: true })).toHaveCount(0);
    let notesDetails = page
      .locator("#case-breakdown details")
      .filter({ hasText: "Concept study notes" });
    await expect(notesDetails.locator("summary")).toBeVisible();
    await expect(
      notesDetails.getByText("What is concept vs real", { exact: true }),
    ).not.toBeVisible();
    await notesDetails.locator("summary").click();
    await expect(
      notesDetails.getByText("What is concept vs real", { exact: true }),
    ).toBeVisible();
    await expect(page.getByText("What this shows", { exact: true })).toBeVisible();
    await expect(page.getByText("Concept output scope", { exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: /Back to work/i })).toHaveAttribute(
      "href",
      "/#work-renewal",
    );
    const caseIndex = page.getByRole("complementary", { name: "Case index" });
    await expect(caseIndex.getByRole("link", { name: "Watch the film" })).toHaveAttribute(
      "href",
      "#case-film",
    );
    await expect(
      caseIndex.getByRole("link", { name: "Read the breakdown" }),
    ).toHaveAttribute("href", "#case-breakdown");
    await expect(
      caseIndex.getByRole("link", { name: "Discuss a project" }),
    ).toHaveAttribute("href", "#case-inquiry");
    let projectNavigation = page.getByRole("navigation", {
      name: "Project navigation",
    });
    await expect(projectNavigation.getByText("Previous", { exact: true })).toHaveCount(0);
    await expect(projectNavigation.getByText(/^Next project/)).toBeVisible();
    await expect(
      projectNavigation.getByRole("link", { name: /Back to all projects/i }),
    ).toHaveAttribute("href", "/#work-renewal");
    await expect(projectNavigation.locator('a[href="/work/liquid-signal"]')).toContainText(
      "Liquid Signal",
    );
    await expect(
      projectNavigation
        .locator('a[href="/work/liquid-signal"]')
        .getByText("Concept Project", { exact: true }),
    ).toBeVisible();
    await expect(projectNavigation.locator('a[href="/work/liquid-signal"] img')).toHaveCount(1);
    await page.goto("/work/liquid-signal");
    await expect(page.locator("h1")).toContainText("Liquid Signal");
    await expect(page.getByText(/Self-initiated concept study/i)).toBeVisible();
    await expect(page.locator("header").getByText("Concept Project", { exact: true })).toHaveCount(0);
    notesDetails = page
      .locator("#case-breakdown details")
      .filter({ hasText: "Concept study notes" });
    await expect(notesDetails.locator("summary")).toBeVisible();
    await expect(
      notesDetails.getByText("What is concept vs real", { exact: true }),
    ).not.toBeVisible();
    projectNavigation = page.getByRole("navigation", { name: "Project navigation" });
    await expect(projectNavigation.getByText("Previous", { exact: true })).toHaveCount(0);
    await expect(projectNavigation.getByText(/^Next project/)).toBeVisible();
    expect(errors, errors.join("\n")).toHaveLength(0);
  });

  test("the portrait case uses a desktop proof split and a mobile reading stack", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto("/work/renewal");
    const header = page.locator("article > div.mt-8 > header");
    const film = page.locator("#case-film");
    const desktopHeader = await header.boundingBox();
    const desktopFilm = await film.boundingBox();
    expect(desktopHeader).not.toBeNull();
    expect(desktopFilm).not.toBeNull();
    expect(desktopFilm?.x ?? 0).toBeGreaterThan(
      (desktopHeader?.x ?? 0) + (desktopHeader?.width ?? 0),
    );

    await page.setViewportSize({ width: 390, height: 844 });
    const mobileHeader = await header.boundingBox();
    const mobileFilm = await film.boundingBox();
    expect(mobileHeader).not.toBeNull();
    expect(mobileFilm).not.toBeNull();
    expect(mobileFilm?.y ?? 0).toBeGreaterThanOrEqual(
      (mobileHeader?.y ?? 0) + (mobileHeader?.height ?? 0),
    );
  });

  test("Agentic Trading keeps its fictional-data and advice boundaries visible", async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto("/work/agentic-trading");

    await expect(page.locator("h1")).toHaveText("Agentic Trading");
    await expect(page.getByText("Concept disclosure", { exact: true })).toBeVisible();
    await expect(
      page.getByText(/All market data, tickers, scores, and depicted product behavior are fictional/i),
    ).toBeVisible();
    await expect(page.getByText(/No client relationship, live trading system/i)).toBeVisible();
    await expect(
      page.getByText(/performance result, or financial advice is implied/i),
    ).toBeVisible();

    const video = page.locator("main video");
    await expect(video).toHaveAttribute(
      "poster",
      "/posters/agentic-trading.e09753d24951.webp",
    );
    await expect(video.locator("source").last()).toHaveAttribute(
      "src",
      "/videos/agentic-trading.344a87357144.mp4",
    );
    await expect(video.locator("track")).toHaveAttribute(
      "src",
      "/captions/agentic-trading.66d344306cb2.en.vtt",
    );
    const strategyFrame = page.getByRole("img", {
      name: /mascot beside a glass chessboard/i,
    });
    await expect(strategyFrame).toBeVisible();
    await expect
      .poll(() => strategyFrame.evaluate((image: HTMLImageElement) => image.currentSrc))
      .toMatch(/\/images\/work\/agentic-trading\/strategy-board-1920\.79064a62aeea\.webp$/);
    await expect(
      page.getByText(/No live market data, working trading product, or performance result is shown/i),
    ).toBeVisible();
    expect(errors, errors.join("\n")).toHaveLength(0);
  });

  test("Agentic Trading selects the smaller editorial still on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/work/agentic-trading");
    const strategyFrame = page.getByRole("img", {
      name: /mascot beside a glass chessboard/i,
    });
    await expect
      .poll(() => strategyFrame.evaluate((image: HTMLImageElement) => image.currentSrc))
      .toMatch(/\/images\/work\/agentic-trading\/strategy-board-960\.70da7ef150bb\.webp$/);
  });

  test("public pages preserve concept labels and hide private addresses", async ({ page }) => {
    for (const path of [
      "/",
      "/pilot",
      "/system-study",
      "/work/renewal",
      "/work/liquid-signal",
      "/work/furia",
      "/work/agentic-trading",
    ]) {
      await page.goto(path);
      const bodyText = await page.locator("body").innerText();
      expect(bodyText).not.toContain("charles@madebymotionx.com");
      expect(bodyText).not.toContain("daichunyu666@gmail.com");
    }
    await page.goto("/");
    await expect(page.getByText("Concept Project").first()).toBeVisible();
    await page.goto("/work/renewal");
    await expect(page.getByText("Concept Project").first()).toBeVisible();
  });

  test("core URLs return ok responses", async ({ request }) => {
    for (const path of [
      "/",
      "/pilot",
      "/system-study",
      "/work/renewal",
      "/work/liquid-signal",
      "/work/furia",
      "/work/agentic-trading",
      "/robots.txt",
      "/sitemap.xml",
      "/favicon.ico",
      "/icon.svg",
      "/apple-icon.png",
    ]) {
      const res = await request.get(path);
      expect(res.ok(), `${path} -> ${res.status()}`).toBeTruthy();
    }
  });

  test("unknown route returns 404", async ({ request }) => {
    const res = await request.get("/no-such-page");
    expect(res.status()).toBe(404);
  });

  test("rendered metadata stays canonical, parseable, and truthful", async ({ page }) => {
    test.setTimeout(60_000);
    const expectedOrigin = new URL(
      process.env.NEXT_PUBLIC_SITE_URL ??
        process.env.PLAYWRIGHT_BASE_URL ??
        "http://localhost:3000",
    ).origin;
    const strip = (value: string) => value.replace(/\/$/, "");
    const matrix = [
      { route: "/", ogType: "website", image: "/og/og-image.jpg", concept: false },
      { route: "/pilot", ogType: "website", image: "/og/og-image.jpg", concept: false },
      { route: "/system-study", ogType: "article", image: "/og/system-study.jpg", concept: true },
      { route: "/work/renewal", ogType: "article", image: "/og/renewal.jpg", concept: true },
      { route: "/work/liquid-signal", ogType: "article", image: "/og/liquid-signal.jpg", concept: true },
      { route: "/work/furia", ogType: "article", image: "/og/furia.jpg", concept: true },
      { route: "/work/agentic-trading", ogType: "article", image: "/og/agentic-trading.jpg", concept: true },
    ] as const;

    for (const spec of matrix) {
      await page.goto(spec.route);
      const expectedUrl =
        spec.route === "/" ? expectedOrigin : `${expectedOrigin}${spec.route}`;

      const canonical = page.locator('link[rel="canonical"]');
      await expect(canonical, `${spec.route} canonical count`).toHaveCount(1);
      expect(strip((await canonical.getAttribute("href")) ?? "")).toBe(expectedUrl);

      const ogUrl = page.locator('meta[property="og:url"]');
      await expect(ogUrl, `${spec.route} og:url count`).toHaveCount(1);
      expect(strip((await ogUrl.getAttribute("content")) ?? "")).toBe(expectedUrl);

      await expect(page.locator('meta[property="og:site_name"]')).toHaveAttribute(
        "content",
        "MOTIONX",
      );
      await expect(page.locator('meta[property="og:type"]')).toHaveAttribute(
        "content",
        spec.ogType,
      );

      const ogImage = page.locator('meta[property="og:image"]');
      await expect(ogImage, `${spec.route} og:image count`).toHaveCount(1);
      await expect(ogImage).toHaveAttribute("content", `${expectedOrigin}${spec.image}`);
      await expect(page.locator('meta[property="og:image:width"]')).toHaveAttribute("content", "1200");
      await expect(page.locator('meta[property="og:image:height"]')).toHaveAttribute("content", "630");
      const alt = (await page.locator('meta[property="og:image:alt"]').getAttribute("content")) ?? "";
      expect(alt, `${spec.route} og:image:alt`).toContain("MOTIONX");

      await expect(page.locator('meta[name="twitter:card"]')).toHaveAttribute(
        "content",
        "summary_large_image",
      );
      await expect(page.locator('meta[name="twitter:image"]')).toHaveAttribute(
        "content",
        `${expectedOrigin}${spec.image}`,
      );

      if (spec.concept) {
        await expect(page.locator('meta[name="description"]')).toHaveAttribute(
          "content",
          /concept/i,
        );
        await expect(page.locator('meta[property="og:description"]')).toHaveAttribute(
          "content",
          /concept/i,
        );
      }

      // JSON-LD: every block parses; every URL-bearing field (nested creator,
      // publisher, image, isPartOf, …) uses the configured origin. A block may
      // hold one entity or an array of entities — flatten before typing.
      const jsonLd = (
        await page.locator('script[type="application/ld+json"]').allTextContents()
      ).flatMap((value) => {
        const parsed = JSON.parse(value) as unknown;
        return Array.isArray(parsed) ? parsed : [parsed];
      });
      if (spec.route === "/") {
        expect(jsonLd.some((entry) => entry["@type"] === "Organization")).toBe(true);
        expect(jsonLd.some((entry) => entry["@type"] === "WebSite")).toBe(true);
      }
      if (spec.concept) {
        const creative = jsonLd.find((entry) => entry["@type"] === "CreativeWork");
        expect(creative, `${spec.route} CreativeWork`).toBeTruthy();
        expect(String(creative?.description ?? "")).toMatch(/concept/i);
      }
      const schemaUrls: string[] = [];
      const collect = (node: unknown) => {
        if (typeof node === "string") {
          if (/^https?:\/\//.test(node) && !node.startsWith("https://schema.org")) {
            schemaUrls.push(node);
          }
        } else if (Array.isArray(node)) {
          node.forEach(collect);
        } else if (node && typeof node === "object") {
          for (const [key, value] of Object.entries(node)) {
            if (key !== "@context") collect(value);
          }
        }
      };
      jsonLd.forEach(collect);
      for (const value of schemaUrls) {
        expect(
          strip(new URL(value).origin),
          `${spec.route} JSON-LD URL ${value}`,
        ).toBe(expectedOrigin);
      }
    }

    for (const route of [
      "/work/renewal",
      "/work/liquid-signal",
      "/work/furia",
      "/work/agentic-trading",
    ]) {
      await page.goto(route);
      await expect(page.locator('meta[name="description"]')).toHaveAttribute(
        "content",
        /self-initiated.*concept.*no client relationship/i,
      );
      await expect(page.locator('meta[property="og:title"]')).toHaveAttribute(
        "content",
        /Concept Study/i,
      );
      await expect(page.locator('meta[property="og:description"]')).toHaveAttribute(
        "content",
        /self-initiated.*concept.*no client relationship/i,
      );
      await expect(page.locator('meta[name="twitter:description"]')).toHaveAttribute(
        "content",
        /self-initiated.*concept.*no client relationship/i,
      );
    }

    // Sitemap: the exact, duplicate-free set of public URLs in the route matrix.
    const sitemap = await (await page.request.get("/sitemap.xml")).text();
    const locs = [...sitemap.matchAll(/<loc>([^<]*)<\/loc>/g)].map((match) =>
      strip(match[1]),
    );
    const expectedLocs = matrix.map((spec) =>
      spec.route === "/" ? expectedOrigin : `${expectedOrigin}${spec.route}`,
    );
    expect(new Set(locs).size).toBe(locs.length);
    expect([...locs].sort()).toEqual([...expectedLocs].sort());

    // robots.txt: allow-all with the configured Host + sitemap.
    const robotsTxt = await (await page.request.get("/robots.txt")).text();
    expect(robotsTxt).toContain("Allow: /");
    expect(robotsTxt).toContain(`Host: ${expectedOrigin}`);
    expect(robotsTxt).toContain(`Sitemap: ${expectedOrigin}/sitemap.xml`);

    // 404 isolation: noindex policy, and no inherited canonical/share metadata.
    await page.goto("/no-such-page");
    const robotsTokens = (
      await page
        .locator('meta[name="robots"]')
        .evaluateAll((elements) =>
          elements.map((element) => element.getAttribute("content") ?? ""),
        )
    ).flatMap((value) => value.split(",").map((token) => token.trim().toLowerCase()));
    expect(robotsTokens, "404 must carry noindex").toContain("noindex");
    expect(robotsTokens, "404 must not permit indexing").not.toContain("index");
    await expect(page.locator('link[rel="canonical"]')).toHaveCount(0);
    await expect(page.locator('meta[property="og:url"]')).toHaveCount(0);
    await expect(page.locator('meta[property="og:image"]')).toHaveCount(0);
    await expect(page.locator('meta[name="twitter:image"]')).toHaveCount(0);
  });
});

test.describe("Design system", () => {
  // `.label` lives in @layer utilities alongside Tailwind's generated colour
  // utilities. A plain `color` declaration there ties on specificity and wins
  // on source order, which silently flattened 46 `text-accent-soft` eyebrows to
  // dim grey sitewide. The default is now a zero-specificity `:where(.label)`.
  // Assert the rendered colour, not the class list — the class list was always
  // correct; only the computed value was wrong.
  test("accent labels keep their colour utility", async ({ page }) => {
    await page.goto("/");
    const eyebrow = page.locator("#top p.label").first();
    await expect(eyebrow).toHaveClass(/text-accent-soft/);
    // --color-accent-soft (#8A96FF). If `.label` reclaims `color`, this reads
    // as --color-gray-dim (#82828A) instead.
    await expect(eyebrow).toHaveCSS("color", "rgb(138, 150, 255)");

    // A label with no colour utility must still fall back to the dim default.
    const plain = page
      .locator(".label")
      .filter({ hasNotText: /^$/ })
      .and(page.locator(':not([class*="text-accent"]):not([class*="text-ivory"]):not([class*="text-gray"])'))
      .first();
    if (await plain.count()) {
      await expect(plain).toHaveCSS("color", "rgb(130, 130, 138)");
    }
  });

  // `.link-underline` draws its gradient layer from 0% to 100% on hover. If a
  // future utility or Tailwind change swallows the background-size pair, the
  // drawn-underline signature dies silently everywhere at once — assert the
  // computed value, mirroring the .label incident pattern.
  test("drawn underline reaches full width on hover", async ({ page }) => {
    await page.goto("/");
    const link = page.locator("#top a.link-underline[href='#work']");
    await expect(link).toBeVisible();
    const resting = await link.evaluate(
      (el) => getComputedStyle(el).backgroundSize,
    );
    // The production minifier normalizes the authored `0%` to `0px`; both
    // mean a zero-width first (gradient) layer.
    expect(/^0(%|px)/.test(resting)).toBe(true);
    await link.hover();
    await expect
      .poll(
        () => link.evaluate((el) => getComputedStyle(el).backgroundSize),
        { timeout: 3000 },
      )
      .toMatch(/^100%/);
  });

  // The registered --project-accent must resolve to the ACTIVE film's accent
  // on the persistent edit-bay panel (it grades between films via a custom
  // property transition; unsupported engines snap — either way the settled
  // value must be the new film's colour).
  test("edit-bay panel accent follows the active film", async ({ page }) => {
    await page.goto("/#work");
    const panel = page.locator("#selected-work-panel");
    // Default active film is Renewal (#C7A24B).
    await expect
      .poll(() =>
        panel.evaluate((el) =>
          getComputedStyle(el).getPropertyValue("--project-accent").trim(),
        ),
      )
      .toBe("rgb(199, 162, 75)");
    await page
      .getByRole("button", { name: "Preview film: Liquid Signal" })
      .click();
    // Liquid Signal is the electric blue #6D7CFF.
    await expect
      .poll(
        () =>
          panel.evaluate((el) =>
            getComputedStyle(el).getPropertyValue("--project-accent").trim(),
          ),
        { timeout: 3000 },
      )
      .toBe("rgb(109, 124, 255)");
  });

  // Fail-open contract for the scroll-drawn rules: under reduced motion the
  // gated hidden state must not exist — the footer slate rule renders fully
  // drawn (no transform) even in engines that support view timelines.
  test("drawn rules are complete under reduced motion", async ({ browser }) => {
    const context = await browser.newContext({ reducedMotion: "reduce" });
    const page = await context.newPage();
    await page.goto("/");
    const rule = page.locator("footer .rule-draw-x").first();
    await expect(rule).toHaveCSS("transform", "none");
    await context.close();
  });
});

test.describe("Navigation", () => {
  test("desktop nav keeps three primary destinations plus the project action", async ({
    page,
  }) => {
    await page.goto("/");
    const primary = page.getByRole("navigation", { name: "Primary" });
    const destinations = primary.locator('ul a:not([href="/#contact"])');

    await expect(destinations).toHaveCount(3);
    await expect(destinations).toHaveText(["Work", "Services", "Pilot"]);
    await expect(primary.getByRole("link", { name: "Process" })).toHaveCount(0);
    await expect(primary.getByRole("link", { name: "Studio" })).toHaveCount(0);
    await expect(
      primary.getByRole("link", { name: "Start a Project" }),
    ).toBeVisible();
  });

  test("desktop nav anchor scrolls to a section", async ({ page }) => {
    await page.goto("/");
    await page.getByRole("navigation", { name: "Primary" }).getByRole("link", { name: "Work" }).click();
    await expect(page).toHaveURL(/#work$/);
    await expect(page.locator("#work")).toBeInViewport({ ratio: 0 });
  });

  test("mobile menu opens, navigates, and closes", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const toggle = page.getByRole("button", { name: "Open menu" });
    await toggle.click();
    const persistentToggle = page.locator(
      'header button[aria-controls="mobile-menu"]',
    );
    await expect(persistentToggle).toBeHidden();
    await expect(persistentToggle).toBeDisabled();
    const menu = page.locator("#mobile-menu");
    await expect(menu).toBeVisible();
    await expect(menu).toHaveAttribute("role", "dialog");
    await expect(menu).toHaveAttribute("aria-modal", "true");
    await expect(page.locator("header")).toHaveAttribute("inert", "");
    await expect(page.locator("main")).toHaveAttribute("inert", "");
    await expect(page.locator("footer")).toHaveAttribute("inert", "");
    await expect(page.locator('body > a[href="#content"]')).toHaveAttribute(
      "inert",
      "",
    );
    const dialogClose = menu.getByRole("button", { name: "Close navigation" });
    await expect(page.getByRole("button", { name: /^Close/ })).toHaveCount(1);
    await expect(dialogClose).toBeVisible();
    await expect(dialogClose).toBeFocused();
    const destinations = menu.locator("ul").getByRole("link");
    await expect(destinations).toHaveCount(3);
    for (const label of ["Work", "Services", "Pilot"]) {
      await expect(menu.getByRole("link", { name: label, exact: true })).toBeVisible();
    }
    await expect(menu.getByRole("link", { name: "Process" })).toHaveCount(0);
    await expect(menu.getByRole("link", { name: "Studio" })).toHaveCount(0);
    await expect(
      menu.getByRole("link", { name: "Start a Project" }),
    ).toBeVisible();
    const servicesLink = menu.getByRole("link", { name: "Services" });
    await servicesLink.focus();
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/#services$/);
    await expect(menu).toBeHidden();
    await expect(page.locator("main")).not.toHaveAttribute("inert", "");
    await expect(page.locator("#services h2")).toBeFocused();
  });

  test("mobile menu marks the current route with aria-current", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/pilot");
    await page.getByRole("button", { name: "Open menu" }).click();
    const menu = page.locator("#mobile-menu");
    await expect(menu).toBeVisible();
    await expect(menu.getByRole("link", { name: "Pilot" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    await expect(menu.getByRole("link", { name: "Work" })).not.toHaveAttribute(
      "aria-current",
      /.*/,
    );

    await page.goto("/work/renewal");
    await page.getByRole("button", { name: "Open menu" }).click();
    await expect(
      page.locator("#mobile-menu").getByRole("link", { name: "Work" }),
    ).toHaveAttribute("aria-current", "location");
  });

  test("mobile menu returns focus to the toggle when closed with Escape", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const toggle = page.getByRole("button", { name: "Open menu" });
    await toggle.click();
    await expect(page.locator("#mobile-menu")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.locator("#mobile-menu")).toBeHidden();
    // Focus must land back on the toggle, not be lost to <body>.
    await expect(page.getByRole("button", { name: "Open menu" })).toBeFocused();
  });

  test("mobile menu returns focus to the toggle when closed explicitly", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const toggle = page.getByRole("button", { name: "Open menu" });
    await toggle.focus();
    await page.keyboard.press("Enter");
    const close = page.getByRole("button", { name: "Close navigation" });
    await expect(close).toBeFocused();
    await page.keyboard.press("Enter");
    await expect(page.locator("#mobile-menu")).toBeHidden();
    await expect(toggle).toBeFocused();
  });

  test("cross-route mobile navigation does not restore the stale menu toggle", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const toggle = page.getByRole("button", { name: "Open menu" });
    await toggle.focus();
    await page.keyboard.press("Enter");
    await expect(
      page.getByRole("button", { name: "Close navigation" }),
    ).toBeFocused();
    const pilot = page.locator("#mobile-menu").getByRole("link", { name: "Pilot" });
    await pilot.focus();
    await expect(pilot).toBeFocused();
    await Promise.all([
      page.waitForURL(/\/pilot$/),
      pilot.press("Enter"),
    ]);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.getByRole("button", { name: "Open menu" })).not.toBeFocused();
  });

  test("'Start a Project' focuses the contact heading without opening email", async ({
    page,
    context,
  }) => {
    await page.goto("/");
    await page
      .getByRole("navigation", { name: "Primary" })
      .getByRole("link", { name: "Start a Project" })
      .click();
    await expect(page).toHaveURL(/#contact$/);
    // Generous on purpose. The contract is "focus lands on the heading", not
    // "within N ms" — and the implementation deliberately waits out the smooth
    // scroll first, so a tight ceiling here measures the runner rather than the
    // behaviour. Landing exactly once is asserted separately, below.
    await expect
      .poll(() => page.evaluate(() => document.activeElement?.id), { timeout: 8000 })
      .toBe("contact-heading");
    // scrollToContact must never open a compose tab or submit anything.
    expect(context.pages()).toHaveLength(1);
  });

  test("contact focus waits for an inert background to release, then fires once", async ({ page }) => {
    await page.goto("/");
    // Deterministically reproduce an overlay-teardown race: hold the contact
    // heading's ancestor inert well past the original 480ms focus timer.
    await page.evaluate(() => {
      const main = document.getElementById("content");
      if (!main) throw new Error("missing #content");
      main.inert = true;
      const tracker = window as unknown as { __contactFocusCount: number };
      tracker.__contactFocusCount = 0;
      document.getElementById("contact-heading")?.addEventListener("focus", () => {
        tracker.__contactFocusCount += 1;
      });
    });

    // Trigger the real Start-a-Project contract from the header, which sits
    // outside the inert subtree.
    await page
      .getByRole("navigation", { name: "Primary" })
      .getByRole("link", { name: "Start a Project" })
      .click();

    // Past the original timer: focus must not have force-landed on (or been
    // swallowed by) the still-inert heading.
    await page.waitForTimeout(700);
    expect(
      await page.evaluate(
        () => (window as unknown as { __contactFocusCount: number }).__contactFocusCount,
      ),
    ).toBe(0);

    // Release the inert ancestor — the bounded rAF retry must now complete.
    await page.evaluate(() => {
      const main = document.getElementById("content");
      if (main) main.inert = false;
    });
    await expect
      .poll(() => page.evaluate(() => document.activeElement?.id), { timeout: 8000 })
      .toBe("contact-heading");
    // The real contract: it lands, and it lands exactly once. A ceiling on how
    // fast is not part of it, so the timeout above is deliberately loose while
    // this count stays exact.
    expect(
      await page.evaluate(
        () => (window as unknown as { __contactFocusCount: number }).__contactFocusCount,
      ),
    ).toBe(1);
  });

  test("scroll-to-contact preserves attribution on Home and across routes", async ({ page }) => {
    const startProject = () =>
      page
        .getByRole("navigation", { name: "Primary" })
        .getByRole("link", { name: "Start a Project" });

    await page.goto("/?utm_source=portfolio&utm_campaign=contact-test#top");
    await startProject().click();
    await page.waitForURL((url) => url.pathname === "/" && url.hash === "#contact");
    let url = new URL(page.url());
    expect(url.searchParams.get("utm_source")).toBe("portfolio");
    expect(url.searchParams.get("utm_campaign")).toBe("contact-test");

    // The no-contact-section branch navigates home instead of dropping the
    // current route's attribution parameters.
    await page.goto("/pilot?utm_source=pilot&utm_content=header-cta#launch-system");
    await startProject().click();
    await page.waitForURL((next) => next.pathname === "/" && next.hash === "#contact");
    url = new URL(page.url());
    expect(url.searchParams.get("utm_source")).toBe("pilot");
    expect(url.searchParams.get("utm_content")).toBe("header-cta");
  });

  test("same-page service referral updates contact without pilot context", async ({
    page,
  }) => {
    await page.goto(
      "/?utm_source=system-study&pilot=product-film&addon=campaign-add-on",
    );
    const cta = page
      .locator("#services")
      .getByRole("link", { name: "Discuss the launch system", exact: true });
    await cta.scrollIntoViewIfNeeded();
    await cta.click();

    await page.waitForURL((url) =>
      url.hash === "#contact" &&
      url.searchParams.get("type") === "Film + Website Launch System",
    );
    expect(new URL(page.url()).searchParams.get("utm_source")).toBe("system-study");
    expect(new URL(page.url()).searchParams.get("pilot")).toBeNull();
    expect(new URL(page.url()).searchParams.get("addon")).toBeNull();
    const form = page.locator("#contact form");
    await expect(form.locator('select[name="project-type"]')).toHaveValue(
      "Film + Website Launch System",
    );
    await expect(form.getByText("Selected pilot", { exact: true })).toHaveCount(0);
  });

  test("contextual links preserve modified-click browser behavior", async ({ page }) => {
    await page.goto("/");
    const link = page
      .locator("#services")
      .getByRole("link", { name: "Discuss the launch system", exact: true });
    await link.scrollIntoViewIfNeeded();

    const preventedByApp = await link.evaluate((element) => {
      let observed = true;
      document.addEventListener(
        "click",
        (event) => {
          observed = event.defaultPrevented;
          // Stop the browser's new-tab action after observing whether the
          // application preserved the native modified-click behavior.
          event.preventDefault();
        },
        { once: true },
      );
      element.dispatchEvent(
        new MouseEvent("click", {
          bubbles: true,
          cancelable: true,
          button: 0,
          metaKey: true,
        }),
      );
      return observed;
    });

    expect(preventedByApp).toBe(false);
    expect(new URL(page.url()).searchParams.has("type")).toBe(false);
  });
});

test.describe("Selected Work edit bay", () => {
  const caseIndexLink = (page: Page, slug: WorkSlug) =>
    page
      .locator("#work")
      .getByRole("link", { name: `Open case study: ${WORK_PROJECT_TITLES[slug]}` });

  test("keeps one active film and restores selections through browser history", async ({ page }) => {
    await page.goto("/");
    const work = page.locator("#work");
    await work.scrollIntoViewIfNeeded();
    await expect(work.locator("video")).toHaveCount(1);
    await expect(work.locator("article h3")).toHaveText("Renewal");

    const status = work.getByRole("status").filter({ hasText: "Now viewing" }).first();
    await expect(status).toHaveCount(1);
    await status.evaluate((element) => {
      element.setAttribute("data-persistent-node", "true");
    });

    const liquidPreview = workPreview(page, "liquid-signal");
    await liquidPreview.focus();
    await liquidPreview.press("Enter");
    await expect(page).toHaveURL(/#work-liquid-signal$/);
    await expect(work.locator("article h3")).toHaveText("Liquid Signal");
    await expect(work.locator("video")).toHaveCount(1);
    await expect(work.locator("video")).toHaveAttribute(
      "poster",
      "/posters/liquid-signal.cdfb416c6c9d.webp",
    );
    await expect(liquidPreview).toHaveAttribute("aria-pressed", "true");
    await expect(liquidPreview).toBeFocused();
    await expect(status).toHaveAttribute("data-persistent-node", "true");

    await workPreview(page, "agentic-trading").click();
    await expect(work.locator("article h3")).toHaveText("Agentic Trading");
    await page.goBack();
    await expect(page).toHaveURL(/#work-liquid-signal$/);
    await expect(work.locator("article h3")).toHaveText("Liquid Signal");
  });

  test("deep links select the matching project and keep canonical navigation", async ({ page }) => {
    await page.goto("/#work-agentic-trading");
    const work = page.locator("#work");
    await expect(work.locator("article h3")).toHaveText("Agentic Trading");
    await expect(workPreview(page, "agentic-trading")).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    await expect(work.getByRole("link", { name: "View full case study" })).toHaveAttribute(
      "href",
      "/work/agentic-trading",
    );
  });

  test("the four index entries remain real case-study links", async ({ page }) => {
    await page.goto("/");
    const work = page.locator("#work");
    for (const slug of Object.keys(WORK_PROJECT_TITLES) as WorkSlug[]) {
      await expect(caseIndexLink(page, slug)).toHaveAttribute("href", `/work/${slug}`);
    }
    await expect(work.getByRole("dialog")).toHaveCount(0);
  });

  test("malformed work hashes fail safely to the default preview", async ({ page }) => {
    const errors = trackErrors(page);
    await page.goto("/#work-%E0%A4%A");
    await expect(page.locator("#selected-work-panel h3")).toHaveText("Renewal");
    await expect(workPreview(page, "renewal")).toHaveAttribute("aria-pressed", "true");
    expect(errors, errors.join("\n")).toHaveLength(0);
  });

  test("mobile index is a compact, touch-sized cue sheet", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const previews = page.locator("#work ol button[aria-controls='selected-work-panel']");
    const links = page.locator('#work ol a[href^="/work/"]');
    await expect(previews).toHaveCount(4);
    await expect(links).toHaveCount(4);
    const boxes = await previews.evaluateAll((elements) =>
      elements.map((element) => {
        const rect = element.getBoundingClientRect();
        return { x: Math.round(rect.x), y: Math.round(rect.y), height: rect.height };
      }),
    );
    expect(boxes.every((box) => box.height >= 44)).toBe(true);
    expect(new Set(boxes.map((box) => box.x)).size).toBe(1);
    for (let index = 1; index < boxes.length; index += 1) {
      expect(boxes[index].y).toBeGreaterThan(boxes[index - 1].y);
    }
    const caseLinkBoxes = await links.evaluateAll((elements) =>
      elements.map((element) => {
        const rect = element.getBoundingClientRect();
        return { y: Math.round(rect.y), height: rect.height };
      }),
    );
    expect(caseLinkBoxes.every((box) => box.height >= 44)).toBe(true);
    expect(caseLinkBoxes.map((box) => box.y)).toEqual(boxes.map((box) => box.y));
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
  });

  test("mobile case studies lead with the proof and collapse utility detail", async ({
    page,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/work/agentic-trading");

    const breakdown = page.locator("#case-breakdown");
    const proofLabel = breakdown.getByText("What this shows", { exact: true });
    const caseDetails = breakdown.locator("details").filter({ hasText: "Case index" });
    const caseSummary = caseDetails.locator("summary");
    const notesDetails = breakdown
      .locator("details")
      .filter({ hasText: "Concept study notes" });

    await expect(proofLabel).toBeVisible();
    await expect(caseSummary).toBeVisible();
    const proofBox = await proofLabel.boundingBox();
    const summaryBox = await caseSummary.boundingBox();
    expect(proofBox?.y).toBeLessThan(summaryBox?.y ?? 0);

    await expect(
      caseDetails.getByRole("link", { name: "Watch the film" }),
    ).not.toBeVisible();
    await caseSummary.click();
    await expect(
      caseDetails.getByRole("link", { name: "Watch the film" }),
    ).toBeVisible();

    await expect(
      notesDetails.getByText("What is concept vs real", { exact: true }),
    ).not.toBeVisible();
    await notesDetails.locator("summary").click();
    await expect(
      notesDetails.getByText("What is concept vs real", { exact: true }),
    ).toBeVisible();
  });

  test("case-study inquiry CTA carries the matching context into contact", async ({ page }) => {
    await page.goto("/work/liquid-signal");
    const cta = page.getByRole("link", { name: "Start a launch system" });
    await cta.scrollIntoViewIfNeeded();
    await expect(cta).toHaveAttribute(
      "href",
      "/?type=Film%20%2B%20Website%20Launch%20System#contact",
    );
    await cta.click();
    await expect(page).toHaveURL(/\?type=Film(?:%20|\+)%2B(?:%20|\+)Website.*#contact$/);
    await expect(page.locator('select[name="project-type"]')).toHaveValue(
      "Film + Website Launch System",
    );
    const form = page.locator("#contact form");
    await expect(form.getByText("Selected pilot", { exact: true })).toHaveCount(0);
    const mailtoHref = await form
      .getByRole("link", { name: "Open default mail app" })
      .getAttribute("href");
    const decodedMailto = decodeURIComponent(mailtoHref ?? "");
    expect(decodedMailto).toContain("MOTIONX Project Inquiry");
    expect(decodedMailto).not.toContain("MOTIONX Pilot Project Inquiry");
  });
});

test.describe("Pilot → contact preselection", () => {
  test("featured offer shows its summary and clears stale pilot context", async ({ page }) => {
    await page.goto("/pilot");
    // Scope to the card by content, not a positional index — survives reordering
    // or additions in the pilot.ts single source.
    await page
      .locator("article", { hasText: "Film + Website Launch System" })
      .getByRole("link", { name: "Start this project" })
      .click();
    await expect(page).toHaveURL(/\/\?type=.*#contact/);
    await expect.poll(() => new URL(page.url()).searchParams.get("pilot")).toBe(
      "launch-system",
    );
    const form = page.locator("#contact form");
    const select = form.locator('select[name="project-type"]');
    const summary = form
      .locator('[aria-live="polite"]')
      .filter({ hasText: "Selected pilot" });
    await expect(select).toHaveValue("Film + Website Launch System");
    await expect(summary).toBeVisible();
    await expect(summary.getByText("Film + Website Launch System", { exact: true })).toBeVisible();
    await expect(summary.getByText("$999", { exact: true })).toBeVisible();
    await expect(
      summary.getByText("The complete connected launch — film, site, and direction"),
    ).toBeVisible();

    // Choosing a non-pilot type removes the URL authority for pilot pricing;
    // neither the summary nor a later subject may inherit stale pilot state.
    await select.selectOption("Not sure yet");
    await expect.poll(() => new URL(page.url()).searchParams.get("type")).toBeNull();
    await expect.poll(() => new URL(page.url()).searchParams.get("pilot")).toBeNull();
    await expect(summary).toHaveCount(0);
    await expect(select).toHaveValue("Not sure yet");
    const mailtoHref = await form
      .getByRole("link", { name: "Open default mail app" })
      .getAttribute("href");
    expect(decodeURIComponent(mailtoHref ?? "")).not.toContain(
      "MOTIONX Pilot Project Inquiry",
    );
  });

  test("campaign add-on requires a base package and preserves both scopes", async ({
    page,
  }) => {
    await page.goto("/pilot");
    const baseChoices = page.getByRole("group", {
      name: "Choose the base package",
    });
    await expect(baseChoices.getByRole("radio")).toHaveCount(3);
    await expect(
      page.getByRole("button", { name: "Choose a base package first" }),
    ).toBeDisabled();

    for (const [name, total] of [
      [/Product Film/, "$589"],
      [/Film \+ Website Launch System/, "$1,189"],
      [/Motion-First Website/, "$889"],
    ] as const) {
      await baseChoices.getByRole("radio", { name }).check();
      await expect(page.getByText("Base + add-on total", { exact: true })).toBeVisible();
      await expect(page.getByText(total, { exact: true })).toBeVisible();
    }
    const pairedCta = page.getByRole("link", {
      name: "Continue with base + add-on",
      exact: true,
    });
    const href = await pairedCta.getAttribute("href");
    const destination = new URL(href ?? "", page.url());
    expect(destination.searchParams.get("type")).toBe("Motion-First Website");
    expect(destination.searchParams.get("pilot")).toBe("motion-first-website");
    expect(destination.searchParams.get("addon")).toBe("campaign-add-on");

    await pairedCta.click();
    await expect(page.locator('select[name="project-type"]')).toHaveValue(
      "Motion-First Website",
    );
    const form = page.locator("#contact form");
    const summary = form
      .locator('[aria-live="polite"]')
      .filter({ hasText: "Selected pilot" });
    await expect(summary).toBeVisible();
    await expect(summary.getByText("Base package", { exact: true })).toBeVisible();
    await expect(
      summary.getByText("Motion-First Website", { exact: true }),
    ).toBeVisible();
    await expect(summary.getByText("Add-on", { exact: true })).toBeVisible();
    await expect(
      summary.getByText("Campaign Content Add-On", { exact: true }),
    ).toBeVisible();

    const mailtoHref = await form
      .getByRole("link", { name: "Open default mail app" })
      .getAttribute("href");
    const decodedMailto = decodeURIComponent(mailtoHref ?? "");
    expect(decodedMailto).toContain(
      "Pilot package: Motion-First Website — $699",
    );
    expect(decodedMailto).toContain(
      "Add-on: Campaign Content Add-On — $190",
    );

    // A manual project-type edit removes the complete referral, including the
    // paired add-on, while keeping the user's new selection.
    await form
      .locator('select[name="project-type"]')
      .selectOption("Not sure yet");
    await expect.poll(() => new URL(page.url()).searchParams.get("type")).toBeNull();
    await expect.poll(() => new URL(page.url()).searchParams.get("pilot")).toBeNull();
    await expect.poll(() => new URL(page.url()).searchParams.get("addon")).toBeNull();
    await expect(summary).toHaveCount(0);
  });

  test("malformed or unpaired campaign add-ons fail closed", async ({ page }) => {
    for (const path of [
      "/?type=Product%20Film&addon=campaign-add-on#contact",
      "/?type=Product%20Film&pilot=product-film&addon=unknown#contact",
      "/?type=Campaign%20Content%20Add-On&pilot=campaign-add-on#contact",
      "/?type=Product%20Film&type=Motion-First%20Website&pilot=product-film#contact",
      "/?type=Product%20Film&pilot=product-film&pilot=launch-system#contact",
      "/?type=Product%20Film&pilot=product-film&addon=campaign-add-on&addon=campaign-add-on#contact",
    ]) {
      await page.goto(path);
      const form = page.locator("#contact form");
      await expect(
        form.getByText("Selected pilot", { exact: true }),
      ).toHaveCount(0);
      const mailtoHref = await form
        .getByRole("link", { name: "Open default mail app" })
        .getAttribute("href");
      const decodedMailto = decodeURIComponent(mailtoHref ?? "");
      expect(decodedMailto).toContain("MOTIONX Project Inquiry");
      expect(decodedMailto).not.toContain("MOTIONX Pilot Project Inquiry");
      expect(decodedMailto).not.toContain("Pilot package:");
      expect(decodedMailto).not.toContain(
        "Add-on: Campaign Content Add-On — $190",
      );
    }
  });

  test("changing between pilot-compatible types never infers a new offer", async ({ page }) => {
    test.setTimeout(45_000);
    await page.goto("/?type=Product%20Film&pilot=product-film#contact");
    const form = page.locator("#contact form");
    const select = form.locator('select[name="project-type"]');
    const summary = form
      .locator('[aria-live="polite"]')
      .filter({ hasText: "Selected pilot" });

    await expect(select).toHaveValue("Product Film", { timeout: 15_000 });
    await expect(summary).toBeVisible();

    // A website pilot exists, but selecting its project type is not the same as
    // explicitly choosing that offer on /pilot.
    await select.selectOption("Motion-First Website");
    await expect.poll(() => new URL(page.url()).searchParams.get("type")).toBeNull();
    await expect.poll(() => new URL(page.url()).searchParams.get("pilot")).toBeNull();
    await expect(select).toHaveValue("Motion-First Website");
    await expect(summary).toHaveCount(0);

    const mailtoHref = await form
      .getByRole("link", { name: "Open default mail app" })
      .getAttribute("href");
    const decodedMailto = decodeURIComponent(mailtoHref ?? "");
    expect(decodedMailto).toContain("Motion-First Website");
    expect(decodedMailto).not.toContain("MOTIONX Pilot Project Inquiry");
  });
});

test.describe("Contact flow", () => {
  test("required controls expose native semantics and default mail is available first", async ({
    page,
  }) => {
    await page.goto("/#contact");
    for (const selector of ["#contact-name", "#contact-email", "#contact-message"]) {
      const field = page.locator(selector);
      await expect(field).toHaveJSProperty("required", true);
      await expect(field).toHaveAttribute("aria-required", "true");
    }
    await expect(page.getByLabel(/^Name/)).toHaveAttribute(
      "id",
      "contact-name",
    );
    await expect(page.getByLabel(/^Email/)).toHaveAttribute(
      "id",
      "contact-email",
    );

    // A non-Gmail visitor gets a direct fallback before attempting Gmail; the
    // post-attempt troubleshooting helper remains absent in the clean state.
    const defaultMail = page.getByRole("link", { name: "Open default mail app" });
    await expect(defaultMail).toBeVisible();
    await expect(defaultMail).toHaveAttribute("href", /^mailto:hello@madebymotionx\.com/);
    await expect(page.getByText("Having trouble?")).toHaveCount(0);
    await expect(
      page.locator('select[name="project-type"] option[value="Campaign Content Add-On"]'),
    ).toHaveCount(0);
  });

  test("history removal resets URL preselection but preserves an explicit choice", async ({
    page,
  }) => {
    await page.goto("/#services");
    const select = page.locator('select[name="project-type"]');
    const productFilmCta = page.getByRole("link", {
      name: "Discuss a product film",
      exact: true,
    });

    // Use the real client-side referral path. Dispatching a synthetic popstate
    // immediately after goto can race WebKit hydration because the select is
    // already present in the server-rendered HTML.
    await productFilmCta.click();
    await expect(select).toHaveValue("Product Film");

    await page.goBack();
    await expect(select).toHaveValue("Not sure yet");

    await productFilmCta.click();
    await expect(select).toHaveValue("Product Film");
    await select.selectOption("Motion-First Website");
    await expect.poll(() => new URL(page.url()).searchParams.get("type")).toBeNull();

    await page.goBack();
    await expect(select).toHaveValue("Motion-First Website");
  });

  test("required fields validate", async ({ page }) => {
    await page.goto("/#contact");
    const submit = page.locator("#contact").getByRole("button", { name: "Continue in Gmail" });
    await submit.scrollIntoViewIfNeeded();
    await submit.click();
    await expect(page.getByText("Please enter your name.")).toBeVisible();
    await expect(page.getByText("Please enter your email.")).toBeVisible();
    await expect(page.getByText("Tell us a little about the project.")).toBeVisible();
  });

  test("valid submit prepares a Gmail draft to the public address, no false sent state", async ({
    page,
    context,
    browserName,
  }) => {
    // Headless WebKit treats the transient target=_blank Gmail anchor as a
    // same-tab navigation rather than a popup, so this submit flow can only be
    // modelled on Chromium. The compose behaviour itself is engine-independent;
    // the public address is also covered cross-engine by the copy-email test.
    test.skip(browserName === "webkit", "WebKit headless can't model the Gmail popup");

    // Stub Gmail so the popup keeps its requested URL (aborting would replace it
    // with a chrome-error page) and no real network request is made.
    await context.route(/mail\.google\.com/, (r) =>
      r.fulfill({ status: 200, contentType: "text/html", body: "ok" }),
    );
    await page.goto("/#contact");
    // The "Having trouble?" helper must be absent until an attempt is made.
    await expect(page.getByText("Having trouble?")).toHaveCount(0);

    await page.locator("#contact-name").fill("Test Founder");
    await page.locator('#contact input[type="email"]').fill("founder@example.com");
    await page.locator("#contact textarea").fill("We are launching a new product and need a film + site.");

    const popupPromise = context.waitForEvent("page");
    await page.getByRole("button", { name: "Continue in Gmail" }).click();
    const popup = await popupPromise;
    const url = popup.url();
    const params = new URL(url).searchParams;
    const subject = params.get("su") ?? "";
    expect(url).toContain("mail.google.com");
    expect(params.get("to")).toBe(PUBLIC_EMAIL);
    expect(subject).toContain("MOTIONX Project Inquiry");
    expect(subject).not.toContain("MOTIONX Pilot Project Inquiry");
    await popup.close();

    // Honest status — ready, not "sent".
    await expect(page.getByText(/ready in Gmail/i)).toBeVisible();
    await expect(page.getByText(/message sent|has been sent|successfully sent/i)).toHaveCount(0);

    // Helper now offers assistance (not an error): visible, with the mail-app
    // fallback, and — since this was a success not a caught error — the full
    // inline brief <pre> is NOT shown. It dismisses on demand.
    await expect(page.getByText("Having trouble?")).toBeVisible();
    await expect(page.getByRole("link", { name: "Open default mail app" })).toBeVisible();
    await expect(page.locator("#contact pre")).toHaveCount(0);
    await page.getByRole("button", { name: "Dismiss helper" }).click();
    await expect(page.getByText("Having trouble?")).toBeHidden();
    await expect(
      page.getByRole("button", { name: "Continue in Gmail" }),
    ).toBeFocused();
  });

  test("pilot referral uses the pilot inquiry subject", async ({
    page,
    context,
    browserName,
  }) => {
    test.skip(browserName === "webkit", "WebKit headless can't model the Gmail popup");

    await context.route(/mail\.google\.com/, (r) =>
      r.fulfill({ status: 200, contentType: "text/html", body: "ok" }),
    );
    await page.goto(
      "/?type=Film%20%2B%20Website%20Launch%20System&pilot=launch-system#contact",
    );

    // Fill and submit straight away — like browser autofill, this can outrace
    // the mount-time preselection effect. Pilot intent and project type are
    // re-derived from the URL at submit time, so the subject must still be the
    // pilot subject without awaiting the select's preselected value first.
    await page.locator("#contact-name").fill("Pilot Founder");
    await page.locator("#contact-email").fill("pilot@example.com");
    await page.locator("#contact-message").fill("We need a connected film and website launch.");

    const popupPromise = context.waitForEvent("page");
    await page.getByRole("button", { name: "Continue in Gmail" }).click();
    const popup = await popupPromise;
    const subject = new URL(popup.url()).searchParams.get("su") ?? "";
    expect(subject).toContain("MOTIONX Pilot Project Inquiry");
    expect(subject).toContain("Film + Website Launch System");
    await popup.close();
  });

  test("paired campaign add-on is written into the Gmail draft body", async ({
    page,
    context,
    browserName,
  }) => {
    test.skip(browserName === "webkit", "WebKit headless can't model the Gmail popup");

    await context.route(/mail\.google\.com/, (r) =>
      r.fulfill({ status: 200, contentType: "text/html", body: "ok" }),
    );
    await page.goto(
      "/?type=Product%20Film&pilot=product-film&addon=campaign-add-on#contact",
    );
    await page.locator("#contact-name").fill("Add-On Founder");
    await page.locator("#contact-email").fill("addon@example.com");
    await page
      .locator("#contact-message")
      .fill("We need a product film and paired campaign formats.");

    const popupPromise = context.waitForEvent("page");
    await page.getByRole("button", { name: "Continue in Gmail" }).click();
    const popup = await popupPromise;
    const params = new URL(popup.url()).searchParams;
    expect(params.get("su")).toContain("MOTIONX Pilot Project Inquiry");
    expect(params.get("body")).toContain(
      "Pilot package: Product Film — $399",
    );
    expect(params.get("body")).toContain(
      "Add-on: Campaign Content Add-On — $190",
    );
    await popup.close();
  });

  test("a mismatched pilot marker never claims a package", async ({ page }) => {
    // Valid type + a pilot id whose formType doesn't match: the guarded
    // invariant (offer.id AND offer.formType must both match) must yield a
    // normal inquiry with no package summary.
    await page.goto("/?type=Product%20Film&pilot=launch-system#contact");
    await expect(page.locator('select[name="project-type"]')).toHaveValue("Product Film");
    const form = page.locator("#contact form");
    await expect(form.getByText("Selected pilot", { exact: true })).toHaveCount(0);
    const mailtoHref = await form
      .getByRole("link", { name: "Open default mail app" })
      .getAttribute("href");
    const decodedMailto = decodeURIComponent(mailtoHref ?? "");
    expect(decodedMailto).toContain("MOTIONX Project Inquiry");
    expect(decodedMailto).not.toContain("Pilot");
  });

  test("a genuine compose failure shows the inline brief and resets on edit", async ({ page }) => {
    // Force the transient compose anchor to throw — the only path that counts
    // as a real failure (window.open null returns were a false negative).
    // Install after navigation on the exact transient-anchor boundary. WebKit
    // exposes HTMLAnchorElement.click as effectively unforgeable here, so a
    // prototype replacement does not intercept the production call.
    await page.goto("/?type=Product%20Film#contact");
    // The server renders the default option; this URL-driven value is applied
    // by the contact island's mount effect, so observing it proves hydration
    // completed before controlled inputs are filled.
    await expect(page.locator('select[name="project-type"]')).toHaveValue(
      "Product Film",
    );
    await page.evaluate(() => {
      const body = document.body;
      const originalAppendChild = body.appendChild.bind(body);
      Object.defineProperty(body, "appendChild", {
        configurable: true,
        value: (node: Node) => {
          if (
            node instanceof HTMLAnchorElement &&
            node.href.includes("mail.google.com")
          ) {
            throw new Error("compose blocked (test)");
          }
          return originalAppendChild(node);
        },
      });

      const probe = document.createElement("a");
      probe.href = "https://mail.google.com/mail/?view=cm";
      try {
        body.appendChild(probe);
        throw new Error("Gmail compose failure seam was not installed");
      } catch (error) {
        if (!(error instanceof Error) || error.message !== "compose blocked (test)") {
          throw error;
        }
      }
    });
    await page.locator("#contact-name").fill("Error Path");
    await page.locator("#contact-email").fill("error@example.com");
    await page.locator("#contact-message").fill("Exercise the caught-error branch.");
    await page.getByRole("button", { name: "Continue in Gmail" }).click();

    // Honest error status — still never claims anything was sent.
    await expect(page.getByText(/Gmail could not be opened automatically/i)).toBeVisible();
    await expect(page.getByText("Having trouble?")).toBeVisible();
    // A genuine caught error is the one state that shows the brief inline.
    const brief = page.locator("#contact pre");
    await expect(brief).toBeVisible();
    await expect(brief).toHaveAttribute("tabindex", "0");
    await expect(brief).toHaveAttribute("aria-label", "Prepared project brief");
    await brief.focus();
    await expect(brief).toBeFocused();
    await expect(brief).toContainText("MOTIONX Project Inquiry");
    await expect(brief).toContainText("Exercise the caught-error branch.");
    await expect(page.getByRole("button", { name: "Try Gmail again" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Copy prepared message" })).toBeVisible();

    // Any edit resets the helper/error state for a clean next attempt.
    await page.locator("#contact-name").fill("Error Path Again");
    await expect(page.getByText("Having trouble?")).toHaveCount(0);
    await expect(page.locator("#contact pre")).toHaveCount(0);
  });

  test("copy email address copies the public address", async ({ page, browserName }) => {
    // Chromium-only: WebKit headless has no clipboard permissions, so its copy
    // path falls back to a 700ms-raced execCommand whose 2.2s "Email copied"
    // flash can expire under parallel-suite load before the assertion polls —
    // a pure timing flake with no real signal (the read-back was always
    // Chromium-only). Chromium covers the full contract including the actual
    // clipboard contents.
    test.skip(browserName === "webkit", "clipboard requires Chromium permissions");
    await page.goto("/#contact");
    await page.getByRole("button", { name: "Copy email address" }).click();
    await expect(page.getByText("Email copied").first()).toBeVisible();
    const clip = await page.evaluate(() => navigator.clipboard.readText());
    expect(clip).toBe(PUBLIC_EMAIL);

    // The supporting rail's copy control is its own island with its own polite
    // live region — its confirmation must not depend on the form island.
    await page.locator("#contact").getByRole("button", { name: "Copy", exact: true }).click();
    await expect(page.locator('#contact span[role="status"]')).toHaveText(/Email copied/);
    expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(PUBLIC_EMAIL);
  });

  test("legacy clipboard fallback restores focus to its initiating control", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      Object.defineProperty(Navigator.prototype, "clipboard", {
        configurable: true,
        get: () => undefined,
      });
      Object.defineProperty(Document.prototype, "execCommand", {
        configurable: true,
        value: () => true,
      });
    });
    await page.goto("/#contact");

    const copy = page.getByRole("button", { name: "Copy email address" });
    await copy.focus();
    await page.keyboard.press("Enter");

    // The confirmation replaces the button label, so re-query its new
    // accessible name while proving that the same control retained focus.
    await expect(
      page.getByRole("button", { name: "Email copied ✓" }),
    ).toBeFocused();
    await expect(page.getByText("Email copied").first()).toBeVisible();
  });
});

test.describe("Responsive & resilience", () => {
  test("390px hero keeps its supporting-copy height through the font swap", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    // Isolate font geometry from the intentional hero entrance translation;
    // otherwise WebKit can sample the two boxes at different animation frames.
    await page.emulateMedia({ reducedMotion: "reduce" });
    let releaseFonts = () => {};
    const fontsReleased = new Promise<void>((resolve) => {
      releaseFonts = resolve;
    });
    await page.route("**/*.woff2", async (route) => {
      await fontsReleased;
      await route.continue();
    });

    await page.goto("/", { waitUntil: "domcontentloaded" });
    const supportingCopy = page.locator("#top .hero-supporting-copy");
    const fallbackBox = await supportingCopy.boundingBox();
    releaseFonts();
    await page.evaluate(async () => {
      await document.fonts.ready;
    });
    const resolvedBox = await supportingCopy.boundingBox();

    expect(fallbackBox?.height).toBeGreaterThanOrEqual(103.5);
    expect(
      Math.abs((resolvedBox?.height ?? 0) - (fallbackBox?.height ?? 0)),
    ).toBeLessThanOrEqual(0.5);
    expect(Math.abs((resolvedBox?.y ?? 0) - (fallbackBox?.y ?? 0))).toBeLessThanOrEqual(0.5);
  });

  for (const width of [375, 390, 430]) {
    test(`no horizontal overflow at ${width}px (all routes)`, async ({ page }) => {
      await page.setViewportSize({ width, height: 844 });
      for (const path of [
        "/",
        "/pilot",
        "/system-study",
        "/work/renewal",
        "/work/liquid-signal",
        "/work/furia",
        "/work/agentic-trading",
      ]) {
        await page.goto(path);
        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
        );
        expect(overflow, `${path} @ ${width}px overflow`).toBeLessThanOrEqual(0);
      }
    });
  }

  test("reduced-motion home loads cleanly with content visible", async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce" });
    const page = await ctx.newPage();
    const errors = trackErrors(page);
    const mp4Requests: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname.endsWith(".mp4")) {
        mp4Requests.push(request.url());
      }
    });
    await page.goto("/");
    await expect(page.locator("h1")).toBeVisible();
    // `toBeVisible` ignores occlusion — a stale full-screen overlay (e.g. the
    // intro loader failing to dismiss) once passed it. A trial click runs the
    // full actionability checks, so anything covering the hero CTA fails here.
    await page
      .getByRole("link", { name: "View Selected Work" })
      .click({ trial: true, timeout: 5000 });
    // Reduced motion is also the "disallowed" hero branch: the reel must stay a
    // static poster (paused, never advanced) rather than autoplay.
    const heroVideo = page.locator("section#top video");
    await expect(heroVideo).toHaveJSProperty("paused", true);
    await expect(heroVideo).toHaveJSProperty("currentTime", 0);
    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow).toBeLessThanOrEqual(0);
    expect(errors, errors.join("\n")).toHaveLength(0);
    // Poster-only policy is a network contract, not just element state: no
    // media bytes may move for a reduced-motion visitor who never presses play.
    expect(mp4Requests, mp4Requests.join("\n")).toHaveLength(0);
    await ctx.close();
  });

  test("reduced-motion portfolio stays manual but can still be played", async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce" });
    const page = await ctx.newPage();
    await page.goto("/");
    const renewal = page.locator("#selected-work-panel");
    await renewal.scrollIntoViewIfNeeded();
    const video = renewal.locator("video");

    await expect(video).toHaveJSProperty("preload", "none");
    await page.waitForTimeout(900);
    await expect(video).toHaveJSProperty("paused", true);
    await expect(video).toHaveJSProperty("currentTime", 0);

    await renewal.getByRole("button", { name: "Play video" }).click();
    await expect
      .poll(() => video.evaluate((element: HTMLVideoElement) => element.currentTime), {
        timeout: 8000,
      })
      .toBeGreaterThan(0);
    await ctx.close();
  });

  test("normal visitors still get in-view portfolio autoplay", async ({ page }) => {
    await page.goto("/");
    // Wait until the first-load overlay no longer intercepts interactions.
    await page
      .getByRole("link", { name: "View Selected Work" })
      .click({ trial: true, timeout: 5000 });
    const renewal = page.locator("#selected-work-panel");
    await renewal.scrollIntoViewIfNeeded();
    const video = renewal.locator("video");
    await expect(video).toHaveJSProperty("preload", "metadata");
    await expect
      .poll(() => video.evaluate((element: HTMLVideoElement) => element.currentTime), {
        timeout: 8000,
      })
      .toBeGreaterThan(0);
  });

  test("switching the edit bay discards the previous audio owner", async ({ page }) => {
    await page.goto("/");
    const panel = page.locator("#selected-work-panel");
    const renewalVideo = panel.locator("video");

    await panel.scrollIntoViewIfNeeded();
    await panel.getByRole("button", { name: "Unmute video — Renewal" }).click();
    await expect(renewalVideo).toHaveJSProperty("muted", false);

    await workPreview(page, "liquid-signal").click();
    await expect(panel.locator("h3")).toHaveText("Liquid Signal");
    await expect(panel.locator("video")).toHaveCount(1);
    await expect(panel.locator("video")).toHaveJSProperty("muted", true);
    await expect(panel.getByRole("button", { name: "Unmute video — Liquid Signal" })).toBeVisible();
  });

  test("portfolio autoplay waits until the configured visible fraction", async ({ page }) => {
    test.setTimeout(45_000);
    await page.goto("/");
    const renewal = page.locator("#selected-work-panel");
    const video = renewal.locator("video");
    await expect(video).toHaveJSProperty("preload", "metadata", {
      timeout: 15_000,
    });

    // Reveal only a thin strip of the player. `isIntersecting` is true here,
    // but the 45% playback threshold has not been reached.
    await video.evaluate((element) => {
      document.documentElement.style.scrollBehavior = "auto";
      const absoluteTop = element.getBoundingClientRect().top + window.scrollY;
      window.scrollTo(0, absoluteTop - window.innerHeight + 10);
    });
    await page.waitForTimeout(600);

    const visibleRatio = await video.evaluate((element) => {
      const rect = element.getBoundingClientRect();
      const visible = Math.max(
        0,
        Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0),
      );
      return visible / rect.height;
    });
    expect(visibleRatio).toBeGreaterThan(0);
    expect(visibleRatio).toBeLessThan(0.45);
    await expect(video).toHaveJSProperty("paused", true);
    expect(
      await video.evaluate((element: HTMLVideoElement) => element.currentTime),
    ).toBeLessThanOrEqual(0.01);

    await video.evaluate((element) =>
      element.scrollIntoView({ behavior: "auto", block: "center" }),
    );
    await expect
      .poll(() => video.evaluate((element: HTMLVideoElement) => element.currentTime), {
        timeout: 8000,
      })
      .toBeGreaterThan(0);
  });

  test("hero teaser stays a poster until allowed, then plays", async ({ page }) => {
    await page.goto("/");
    const video = page.locator("section#top video");
    const poster = page.locator("section#top picture img");
    await expect
      .poll(() => poster.evaluate((image: HTMLImageElement) => image.currentSrc))
      .toMatch(/\/posters\/agentic-trading-hero\.2b41aa4ef05c\.webp$/);
    await expect(video).not.toHaveAttribute("poster", /.+/);
    // preload="none" keeps the heavy mp4 off the critical path.
    await expect(video).toHaveJSProperty("preload", "none");
    // It should begin playing for a normal (non-reduced) visitor.
    await expect
      .poll(async () => page.locator("section#top video").evaluate((v: HTMLVideoElement) => v.currentTime), {
        timeout: 8000,
      })
      .toBeGreaterThan(0);
  });

  test("data-saver visitors keep the hero teaser on the poster", async ({ browser }) => {
    const ctx = await browser.newContext();
    await ctx.addInitScript(() => {
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
    const page = await ctx.newPage();
    const errors = trackErrors(page);
    const mp4Requests: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname.endsWith(".mp4")) {
        mp4Requests.push(request.url());
      }
    });
    await page.goto("/");
    await page.waitForTimeout(1200);
    const heroVideo = page.locator("section#top video");
    await expect(heroVideo).toHaveJSProperty("paused", true);
    await expect(heroVideo).toHaveJSProperty("currentTime", 0);
    expect(errors, errors.join("\n")).toHaveLength(0);
    // Save-Data visitors must not fetch a single media byte without opting in.
    expect(mp4Requests, mp4Requests.join("\n")).toHaveLength(0);
    await ctx.close();
  });

  test("opted-out visitors get media elements with no source candidates at all", async ({
    browser,
  }) => {
    // The structural half of the poster-only contract, and the reason it holds
    // where `preload="none"` does not. That attribute is a hint: CI's WebKit
    // fetches the mp4 regardless, so reduced-motion and Save-Data visitors were
    // spending bytes while the element still reported paused/currentTime 0.
    // An element with zero <source> children has nothing any engine can fetch,
    // so assert the absence directly rather than trusting the hint.
    for (const optOut of ["reduced-motion", "save-data"] as const) {
      const ctx = await browser.newContext(
        optOut === "reduced-motion" ? { reducedMotion: "reduce" } : {},
      );
      if (optOut === "save-data") {
        await ctx.addInitScript(() => {
          const descriptor = { configurable: true, value: { saveData: true } };
          try {
            Object.defineProperty(navigator, "connection", descriptor);
          } catch {
            Object.defineProperty(Navigator.prototype, "connection", descriptor);
          }
        });
      }
      const page = await ctx.newPage();
      await page.goto("/");
      await page.waitForTimeout(1200);

      const sourceCount = await page.evaluate(
        () => document.querySelectorAll("video source").length,
      );
      expect(sourceCount, `${optOut}: video <source> candidates`).toBe(0);

      // Arming on an explicit press is the other half — the contract must not
      // be implemented by simply breaking playback for these visitors.
      const panel = page.locator("#selected-work-panel");
      await panel.scrollIntoViewIfNeeded();
      await panel.getByRole("button", { name: "Play video" }).click();
      await expect
        .poll(
          () =>
            panel
              .locator("video")
              .evaluate((v: HTMLVideoElement) => v.currentTime),
          { timeout: 10_000 },
        )
        .toBeGreaterThan(0);

      await ctx.close();
    }
  });

  test("a failed film shows the unavailable notice instead of dead controls", async ({ page }) => {
    await page.route("**/*.mp4", (route) => route.abort());
    await page.goto("/");
    const renewal = page.locator("#selected-work-panel");
    await renewal.scrollIntoViewIfNeeded();
    // Every ladder candidate fails → the poster stays, the failure is stated,
    // and the no-op controls are gone.
    await expect(
      renewal.getByRole("status").filter({ hasText: /Video unavailable/ }),
    ).toBeVisible({ timeout: 10_000 });
    await expect(renewal.getByRole("button", { name: /Play video/ })).toHaveCount(0);
    await expect(renewal.locator("video")).toHaveAttribute(
      "poster",
      /renewal\.[0-9a-f]{12}\.webp/,
    );
  });
});

test.describe("Responsive media delivery", () => {
  /** Collect requested .mp4 pathnames for the page's lifetime. */
  function trackMp4(page: Page): string[] {
    const requests: string[] = [];
    page.on("request", (request) => {
      const pathname = new URL(request.url()).pathname;
      if (pathname.endsWith(".mp4")) requests.push(pathname);
    });
    return requests;
  }

  test("390px selects only the mobile derivatives across every surface", async ({ page }) => {
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 390, height: 844 });
    const requests = trackMp4(page);
    await page.goto("/");
    await expect
      .poll(() =>
        page
          .locator("section#top picture img")
          .evaluate((image: HTMLImageElement) => image.currentSrc),
      )
      .toMatch(/\/posters\/agentic-trading-hero-mobile\.850d5c58d577\.webp$/);
    await expect
      .poll(
        () => page.locator("section#top video").evaluate((v: HTMLVideoElement) => v.currentTime),
        { timeout: 8000 },
      )
      .toBeGreaterThan(0);
    for (const slug of Object.keys(WORK_PROJECT_TITLES) as WorkSlug[]) {
      if (slug !== "renewal") {
        await workPreview(page, slug).click();
      }
      const article = page.locator("#selected-work-panel");
      await article.scrollIntoViewIfNeeded();
      await expect
        .poll(
          () => article.locator("video").evaluate((v: HTMLVideoElement) => v.currentTime),
          { timeout: 10_000 },
        )
        .toBeGreaterThan(0);
    }
    expect(requests.some((p) => p.endsWith("/agentic-trading-hero-mobile.971b3f3dde67.mp4"))).toBe(true);
    expect(requests.some((p) => p.endsWith("/renewal-botanical-mobile.5bbade5a0a0e.mp4"))).toBe(true);
    expect(requests.some((p) => p.endsWith("/liquid-signal-mobile.499b4ad7198a.mp4"))).toBe(true);
    expect(requests.some((p) => p.endsWith("/furia-mobile.b39c4813f6bb.mp4"))).toBe(true);
    expect(requests.some((p) => p.endsWith("/agentic-trading-mobile.4610f3f19a82.mp4"))).toBe(true);
    // In one stable mobile session, NO desktop copy may be requested.
    const desktopRequests = requests.filter((p) =>
      /\/(agentic-trading-hero|renewal-botanical|liquid-signal|furia|agentic-trading)\.[0-9a-f]{12}\.mp4$/.test(p),
    );
    expect(desktopRequests, desktopRequests.join("\n")).toEqual([]);
  });

  test("1440px selects only the desktop web copies", async ({ page }) => {
    test.setTimeout(60_000);
    await page.setViewportSize({ width: 1440, height: 900 });
    const requests = trackMp4(page);
    await page.goto("/");
    await expect
      .poll(
        () => page.locator("section#top video").evaluate((v: HTMLVideoElement) => v.currentTime),
        { timeout: 8000 },
      )
      .toBeGreaterThan(0);
    for (const slug of Object.keys(WORK_PROJECT_TITLES) as WorkSlug[]) {
      if (slug !== "renewal") {
        await workPreview(page, slug).click();
      }
      const article = page.locator("#selected-work-panel");
      await article.scrollIntoViewIfNeeded();
      await expect
        .poll(
          () => article.locator("video").evaluate((v: HTMLVideoElement) => v.currentTime),
          { timeout: 10_000 },
        )
        .toBeGreaterThan(0);
    }
    expect(requests.some((p) => p.endsWith("/agentic-trading-hero.7dfc19e34a48.mp4"))).toBe(true);
    expect(requests.some((p) => p.endsWith("/renewal-botanical.d503303f4c24.mp4"))).toBe(true);
    expect(requests.some((p) => p.endsWith("/liquid-signal.c24f676131a6.mp4"))).toBe(true);
    expect(requests.some((p) => p.endsWith("/furia.286ebdadbddd.mp4"))).toBe(true);
    expect(requests.some((p) => p.endsWith("/agentic-trading.344a87357144.mp4"))).toBe(true);
    const mobileRequests = requests.filter((p) => /-mobile\.[0-9a-f]{12}\.mp4$/.test(p));
    expect(mobileRequests, mobileRequests.join("\n")).toEqual([]);
  });

  test("reduced-motion explicit play selects the viewport-appropriate variant", async ({ browser }) => {
    const ctx = await browser.newContext({
      reducedMotion: "reduce",
      viewport: { width: 390, height: 844 },
    });
    const page = await ctx.newPage();
    const requests = trackMp4(page);
    await page.goto("/");
    const renewal = page.locator("#selected-work-panel");
    await renewal.scrollIntoViewIfNeeded();
    await page.waitForTimeout(900);
    // Poster-only policy first: zero media bytes before explicit play.
    expect(requests).toEqual([]);
    await renewal.getByRole("button", { name: /Play video/ }).click();
    await expect.poll(() => requests.length, { timeout: 8000 }).toBeGreaterThan(0);
    expect(
      requests.every((p) => p.endsWith("/renewal-botanical-mobile.5bbade5a0a0e.mp4")),
      requests.join("\n"),
    ).toBe(true);
    await ctx.close();
  });

  test("a failed mobile candidate falls through to the desktop copy without the failure state", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.route("**/*-mobile.*.mp4", (route) => route.abort());
    await page.goto("/");
    const renewal = page.locator("#selected-work-panel");
    await renewal.scrollIntoViewIfNeeded();
    const video = renewal.locator("video");
    await expect
      .poll(() => video.evaluate((v: HTMLVideoElement) => v.currentSrc), { timeout: 10_000 })
      .toMatch(/\/renewal-botanical\.d503303f4c24\.mp4$/);
    // The ladder still has a healthy candidate — no unavailable state.
    await expect(
      renewal.getByRole("status").filter({ hasText: /Video unavailable/ }),
    ).toHaveCount(0);
    await expect
      .poll(() => video.evaluate((v: HTMLVideoElement) => v.currentTime), { timeout: 8000 })
      .toBeGreaterThan(0);
  });

  test("edit-bay navigation swaps to the responsive source for the viewport", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/");
    const panel = page.locator("#selected-work-panel");
    await panel.scrollIntoViewIfNeeded();
    let video = panel.locator("video");
    await expect
      .poll(() => video.evaluate((v: HTMLVideoElement) => v.currentSrc), { timeout: 10_000 })
      .toMatch(/\/renewal-botanical-mobile\.5bbade5a0a0e\.mp4$/);
    await workPreview(page, "liquid-signal").click();
    await expect(panel.locator("h3")).toHaveText("Liquid Signal");
    video = panel.locator("video");
    await expect
      .poll(() => video.evaluate((v: HTMLVideoElement) => v.currentSrc), { timeout: 10_000 })
      .toMatch(/\/liquid-signal-mobile\.499b4ad7198a\.mp4$/);
  });
});

test.describe("Captions", () => {
  test("portfolio players expose an English captions track and CC control; the silent hero has neither", async ({ page }) => {
    await page.goto("/");
    const renewal = page.locator("#selected-work-panel");
    await renewal.scrollIntoViewIfNeeded();
    const track = renewal.locator("video track");
    await expect(track).toHaveCount(1);
    await expect(track).toHaveAttribute("kind", "captions");
    await expect(track).toHaveAttribute("srclang", "en");
    await expect(track).toHaveAttribute("label", "English");
    await expect(page.locator("section#top video track")).toHaveCount(0);
    await expect(
      page.locator("section#top").getByRole("button", { name: /captions/i }),
    ).toHaveCount(0);

    // Keyboard toggle: label carries the accessible state; the text track
    // switches between disabled and showing, independent of mute.
    const cc = renewal.getByRole("button", { name: /Show captions/ });
    await cc.focus();
    await page.keyboard.press("Enter");
    await expect(renewal.getByRole("button", { name: /Hide captions/ })).toBeVisible();
    await expect
      .poll(() =>
        renewal.locator("video").evaluate((v: HTMLVideoElement) => v.textTracks[0]?.mode),
      )
      .toBe("showing");
    await expect(renewal.locator("video")).toHaveJSProperty("muted", true);
    await page.keyboard.press("Enter");
    await expect(renewal.getByRole("button", { name: /Show captions/ })).toBeVisible();
    await expect
      .poll(() =>
        renewal.locator("video").evaluate((v: HTMLVideoElement) => v.textTracks[0]?.mode),
      )
      .toBe("disabled");
  });

  test("canonical work routes ship the captions track and CC control", async ({ page }) => {
    for (const [route, file] of [
      ["/work/renewal", "renewal-botanical"],
      ["/work/liquid-signal", "liquid-signal"],
      ["/work/furia", "furia"],
      ["/work/agentic-trading", "agentic-trading"],
    ] as const) {
      await page.goto(route);
      const track = page.locator("main video track");
      await expect(track).toHaveCount(1);
      await expect(track).toHaveAttribute("kind", "captions");
      await expect(track).toHaveAttribute(
        "src",
        new RegExp(`/captions/${file}\\.[0-9a-f]{12}\\.en\\.vtt$`),
      );
      await expect(page.getByRole("button", { name: /Show captions/ })).toBeVisible();
    }
  });

  test("edit-bay project changes reset captions to their default-off state", async ({ page }) => {
    await page.goto("/");
    const panel = page.locator("#selected-work-panel");
    await panel.scrollIntoViewIfNeeded();
    await panel.getByRole("button", { name: /Show captions/ }).click();
    await expect(panel.getByRole("button", { name: /Hide captions/ })).toBeVisible();
    await workPreview(page, "liquid-signal").click();
    await expect(panel.locator("h3")).toHaveText("Liquid Signal");
    // The player remounts per project: CC returns to its predictable default.
    await expect(panel.getByRole("button", { name: /Show captions/ })).toBeVisible();
    await expect(panel.getByRole("button", { name: /Hide captions/ })).toHaveCount(0);
    await expect
      .poll(() =>
        panel.locator("video").evaluate((v: HTMLVideoElement) => v.textTracks[0]?.mode),
      )
      .toBe("disabled");
  });

  test("caption tracks never violate the poster-only media policy", async ({ browser }) => {
    const ctx = await browser.newContext({ reducedMotion: "reduce" });
    const page = await ctx.newPage();
    const mp4Requests: string[] = [];
    page.on("request", (request) => {
      if (new URL(request.url()).pathname.endsWith(".mp4")) {
        mp4Requests.push(request.url());
      }
    });
    await page.goto("/");
    const renewal = page.locator("#selected-work-panel");
    await renewal.scrollIntoViewIfNeeded();
    await page.waitForTimeout(900);
    expect(mp4Requests, mp4Requests.join("\n")).toHaveLength(0);
    await ctx.close();
  });
});
