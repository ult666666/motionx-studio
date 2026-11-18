import { writeFile } from "node:fs/promises";
import { test, type Request } from "@playwright/test";

export function isDesktopFilm(path: string) {
  return /\/(agentic-trading-hero|renewal-botanical|liquid-signal|furia|agentic-trading)\.[0-9a-f]{12}\.mp4$/.test(path);
}

declare global {
  interface Window {
    mediaSelectionEvents: unknown[];
  }
}

// Runs in the test page before application code. Keep events in the browser so
// the media-selection sequence does not wait for a Playwright round trip.
function observeMediaSelection() {
  const events: unknown[] = [];
  window.mediaSelectionEvents = events;
  const ids = new WeakMap<Element, number>();
  let nextId = 1;
  function id(element: Element) {
    if (!ids.has(element)) ids.set(element, nextId++);
    return ids.get(element);
  }

  function record(type: string, video: HTMLVideoElement, source?: HTMLSourceElement) {
    events.push({
      at: performance.timeOrigin + performance.now(),
      type,
      video: id(video),
      source: source && id(source),
      label: video.getAttribute("aria-label"),
      connected: video.isConnected,
      viewport: { width: innerWidth, height: innerHeight },
      src: video.getAttribute("src"),
      currentSrc: video.currentSrc,
      networkState: video.networkState,
      readyState: video.readyState,
      error: video.error && { code: video.error.code, message: video.error.message },
      candidates: Array.from(video.querySelectorAll("source"), (candidate) => ({
        id: id(candidate),
        src: candidate.getAttribute("src"),
        media: candidate.media,
        matches: !candidate.media || matchMedia(candidate.media).matches,
      })),
    });
  }

  // Listen on the video itself so events from a replaced, detached player are
  // still distinguishable from events on its successor. Source errors do not bubble.
  const watched = new WeakSet<HTMLVideoElement>();
  function watch(video: HTMLVideoElement) {
    if (watched.has(video)) return;
    watched.add(video);
    for (const type of ["loadstart", "abort", "emptied", "error", "loadedmetadata", "playing"]) {
      video.addEventListener(type, (event) => {
        if (event.target === video) record(type, video);
        if (event.target instanceof HTMLSourceElement) record(type, video, event.target);
      }, true);
    }
  }
  new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      for (const node of mutation.addedNodes) {
        if (node instanceof HTMLVideoElement) watch(node);
        else if (node instanceof Element) node.querySelectorAll("video").forEach(watch);
      }
    }
  }).observe(document, { childList: true, subtree: true });

  // A native loadstart alone cannot show whether script restarted selection.
  const nativeLoad = HTMLMediaElement.prototype.load;
  HTMLMediaElement.prototype.load = function () {
    if (this instanceof HTMLVideoElement) {
      watch(this);
      record("load()", this);
    }
    return nativeLoad.call(this);
  };
}

export const mediaTest = test.extend<{ mp4Requests: string[] }>({
  mp4Requests: async ({ page }, runTest, testInfo) => {
    await page.addInitScript(observeMediaSelection);
    const paths: string[] = [];
    const requestIds = new Map<Request, number>();
    const network: object[] = [];
    page.on("request", (request) => {
      const path = new URL(request.url()).pathname;
      if (!path.endsWith(".mp4")) return;
      const id = paths.push(path);
      requestIds.set(request, id);
      network.push({ at: Date.now(), type: "request", id, path, range: request.headers().range ?? null });
    });
    page.on("response", (response) => {
      const id = requestIds.get(response.request());
      if (!id) return;
      const headers = response.headers();
      network.push({
        at: Date.now(), type: "response", id, status: response.status(),
        contentRange: headers["content-range"] ?? null,
        contentLength: headers["content-length"] ?? null,
      });
    });
    page.on("requestfailed", (request) => {
      const id = requestIds.get(request);
      if (id) network.push({ at: Date.now(), type: "requestfailed", id, failure: request.failure()?.errorText });
    });

    await runTest(paths);
    if (paths.some(isDesktopFilm)) {
      const events = await page.evaluate(() => window.mediaSelectionEvents)
        .catch((error) => ({ unavailable: String(error) }));
      const path = testInfo.outputPath("media-selection.json");
      await writeFile(path, JSON.stringify({ events, network }, null, 2));
      await testInfo.attach("media-selection", { path, contentType: "application/json" });
    }
  },
});
