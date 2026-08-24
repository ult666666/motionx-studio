import { readFileSync } from "node:fs";
import { test, expect } from "@playwright/test";

type VercelConfig = {
  headers: Array<{
    headers: Array<{ key: string; value: string }>;
  }>;
};

const vercel = JSON.parse(
  readFileSync("vercel.json", "utf8"),
) as VercelConfig;
const csp = vercel.headers
  .flatMap((entry) => entry.headers)
  .find((header) => header.key.toLowerCase() === "content-security-policy")
  ?.value;

test("production CSP permits every route and core interaction", async ({
  context,
  page,
  browserName,
}) => {
  test.skip(
    process.env.PLAYWRIGHT_PRODUCTION !== "1",
    "The deployment CSP intentionally excludes the unsafe-eval required by next dev.",
  );
  expect(csp, "vercel.json must define Content-Security-Policy").toBeTruthy();
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(message.text());
  });
  page.on("pageerror", (error) => errors.push(String(error)));

  await context.route("**/*", async (route) => {
    if (route.request().resourceType() !== "document") {
      await route.continue();
      return;
    }
    const response = await route.fetch();
    await route.fulfill({
      response,
      headers: {
        ...response.headers(),
        "content-security-policy": csp ?? "",
      },
    });
  });

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Open menu" }).click();
  await expect(page.locator("#mobile-menu")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator("#mobile-menu")).toBeHidden();

  await page.setViewportSize({ width: 1280, height: 800 });
  const work = page.locator("#work");
  await work.scrollIntoViewIfNeeded();
  await work
    .getByRole("button", { name: "Preview film: Liquid Signal" })
    .click();
  await expect(work.locator("article h3")).toHaveText("Liquid Signal");
  await expect(work.locator("video")).toHaveCount(1);

  const submit = page.locator("#contact").getByRole("button", {
    name: "Continue in Gmail",
  });
  await submit.scrollIntoViewIfNeeded();
  await submit.click();
  await expect(page.getByText("Please enter your name.")).toBeVisible();

  // The contact→Gmail compose flow must survive the CSP (CLAUDE.md requires
  // exercising it whenever the policy is tested). Chromium-only: headless
  // WebKit can't model the transient target=_blank popup.
  if (browserName === "chromium") {
    // Registered after the CSP-injection route so it wins for this origin.
    await context.route(/mail\.google\.com/, (r) =>
      r.fulfill({ status: 200, contentType: "text/html", body: "ok" }),
    );
    await page.locator("#contact-name").fill("CSP Check");
    await page.locator("#contact-email").fill("csp@example.com");
    await page.locator("#contact-message").fill("Verify the compose flow under CSP.");
    const popupPromise = context.waitForEvent("page");
    await submit.click();
    const popup = await popupPromise;
    expect(popup.url()).toContain("mail.google.com");
    await popup.close();
    await expect(page.getByText(/ready in Gmail/i)).toBeVisible();
  }

  for (const route of [
    "/pilot",
    "/system-study",
    "/work/renewal",
    "/work/liquid-signal",
    "/work/furia",
    "/work/agentic-trading",
  ]) {
    await page.goto(route);
    await expect(page.locator("main")).toBeVisible();
  }

  expect(errors, errors.join("\n")).toEqual([]);
});
