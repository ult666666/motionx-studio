import { defineConfig, devices } from "@playwright/test";

/**
 * MOTIONX end-to-end suite.
 *
 * Functional assertions only — no pixel/screenshot diffing (the portfolio
 * videos change frame to frame, so visual snapshots would be flaky). Tests run
 * against a server on port 3939. By default Playwright starts `next dev` and
 * reuses one if it is already running; set PLAYWRIGHT_BASE_URL to point the
 * suite at any other origin (e.g. a production-mode `next start`, or the live
 * site) without starting a server.
 */
const PORT = 3939;
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${PORT}`;
const productionMode = process.env.PLAYWRIGHT_PRODUCTION === "1";
const nodeExecutable = process.env.MOTIONX_NODE ?? process.execPath;

// Playwright executes webServer.command through a shell. Quote paths with
// spaces and reject shell-active characters because MOTIONX_NODE is a path,
// never an argument-bearing command string.
if (/[\r\n"`$]/.test(nodeExecutable)) {
  throw new Error("MOTIONX_NODE must be a plain executable path without shell-active characters.");
}
const quotedNodeExecutable = `"${nodeExecutable}"`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  // A pass-on-retry is a real race somewhere — surface it, don't conceal it.
  failOnFlakyTests: !!process.env.CI,
  reporter: process.env.CI
    ? [
        ["list"],
        ["html", { outputFolder: "playwright-report", open: "never" }],
      ]
    : [["list"]],
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [
    {
      // Clipboard permissions are Chromium-only, so they live on this project.
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        viewport: { width: 1280, height: 800 },
        permissions: ["clipboard-read", "clipboard-write"],
      },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"], viewport: { width: 1280, height: 800 } },
    },
  ],
  webServer: process.env.PLAYWRIGHT_BASE_URL
    ? undefined
    : {
        // Reuse the exact Node binary running Playwright. This preserves the
        // local conda setup while remaining portable in CI and other machines.
        // MOTIONX_NODE remains available as an explicit override.
        command: `${quotedNodeExecutable} ./node_modules/.bin/next ${productionMode ? "start" : "dev"} -p ${PORT}`,
        url: baseURL,
        // Production/gate runs must certify the freshly built artifact: if any
        // process holds port 3939 at startup, fail rather than silently reuse
        // whatever it is serving. Ordinary local dev keeps server reuse.
        reuseExistingServer: !productionMode,
        timeout: 120_000,
      },
});
