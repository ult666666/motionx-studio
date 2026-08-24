/** Join class names, dropping falsy values. */
export function cn(...classes: Array<string | false | null | undefined>): string {
  return classes.filter(Boolean).join(" ");
}

/** Build a mailto: link with an optional subject + body. */
export function mailto(email: string, subject?: string, body?: string): string {
  const params = new URLSearchParams();
  if (subject) params.set("subject", subject);
  if (body) params.set("body", body);
  const qs = params.toString();
  // mailto encodes spaces as "+"; email clients want %20 in the body/subject.
  return `mailto:${email}${qs ? `?${qs.replace(/\+/g, "%20")}` : ""}`;
}

/**
 * Focus the contact heading once it is actually focusable. A same-route
 * handoff can race an overlay's teardown — navigation overlays restore the
 * page's `inert` background in an effect cleanup, and `focus()` inside an
 * inert subtree silently no-ops. Wait for the un-inert through rAF with a
 * bounded deadline instead of trusting a fixed timer.
 */
/**
 * Run `land` now, and again each time an `inert` attribute changes anywhere in
 * the document, until it reports that it is done.
 *
 * This replaced a `requestAnimationFrame` retry bounded by a 2s wall-clock
 * deadline. Inert teardown is an attribute mutation, not something that happens
 * "per frame", and rAF is throttled on a busy or backgrounded page — so the
 * frame loop could spend its entire budget without ever sampling the moment the
 * subtree was released, and focus would silently never land. Observing the
 * mutation reacts to the actual event instead of hoping a frame coincides with
 * it. The timeout is only a listener-leak guard, not the mechanism.
 */
function whenUninert(land: () => boolean, timeoutMs = 4000): void {
  if (land()) return;

  let settled = false;
  const finish = () => {
    if (settled) return;
    settled = true;
    observer.disconnect();
    window.clearTimeout(timer);
  };

  const observer = new MutationObserver(() => {
    if (land()) finish();
  });
  observer.observe(document.documentElement, {
    subtree: true,
    attributes: true,
    attributeFilter: ["inert"],
  });
  const timer = window.setTimeout(finish, timeoutMs);
}

function focusContactHeading(heading: HTMLElement): void {
  whenUninert(() => {
    // Detached heading: stop trying, there is nothing to focus.
    if (!heading.isConnected) return true;
    if (heading.closest("[inert]") !== null) return false;
    heading.focus({ preventScroll: true });
    return true;
  });
}

/**
 * Focus the first heading inside a homepage section after a modal navigation
 * overlay has released its inert background. Section links keep their native
 * hash scrolling; this supplies the missing keyboard/screen-reader context once
 * the link that owned focus has disappeared with the menu.
 */
export function focusSectionHeading(sectionId: string): void {
  if (typeof document === "undefined") return;

  whenUninert(() => {
    const section = document.getElementById(sectionId);
    const heading = section?.querySelector<HTMLElement>(
      "h1, h2, h3, h4, h5, h6",
    );
    if (!heading?.isConnected) return false;
    if (heading.closest("[inert]") !== null) return false;

    // Server-rendered section headings are not naturally focusable. Add the
    // programmatic-only target at the moment it is needed; it never enters the
    // ordinary Tab sequence.
    if (!heading.hasAttribute("tabindex")) {
      heading.setAttribute("tabindex", "-1");
    }
    heading.focus({ preventScroll: true });
    return true;
  });
}

/**
 * Smooth-scroll to the contact section and move keyboard focus to its heading
 * (so screen-reader / keyboard users land in context). Used by every
 * "Start a Project" CTA. Never opens an email client or submits a form.
 */
export function scrollToContact(e?: { preventDefault: () => void }): void {
  e?.preventDefault();
  if (typeof document === "undefined") return;
  const section = document.getElementById("contact");
  if (!section) {
    // Not on the home page (e.g. /pilot) — navigate home while retaining
    // attribution and any package preselection in the current query string.
    window.location.href = `/${window.location.search}#contact`;
    return;
  }
  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  section.scrollIntoView({ behavior: reduced ? "auto" : "smooth", block: "start" });
  // Update only the hash without triggering a second native jump. Keeping the
  // current pathname + query prevents UTM and pilot parameters from vanishing.
  const url = new URL(window.location.href);
  url.hash = "contact";
  history.replaceState(
    history.state,
    "",
    `${url.pathname}${url.search}${url.hash}`,
  );
  window.dispatchEvent(new Event("motionx:locationchange"));
  const heading = document.getElementById("contact-heading");
  if (heading) {
    window.setTimeout(
      () => focusContactHeading(heading),
      reduced ? 0 : 480,
    );
  }
}

type LinkActivation = {
  preventDefault: () => void;
  defaultPrevented?: boolean;
  button?: number;
  metaKey?: boolean;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
};

/** Preserve native new-tab/window/download behavior for modified clicks. */
export function shouldInterceptLinkActivation(event: LinkActivation): boolean {
  return (
    !event.defaultPrevented &&
    (event.button === undefined || event.button === 0) &&
    !event.metaKey &&
    !event.ctrlKey &&
    !event.shiftKey &&
    !event.altKey
  );
}

/**
 * Navigate a contextual Home CTA to Contact without relying on Next's
 * same-route Link handoff. This keeps attribution, removes any unrelated pilot
 * marker, updates the mounted form through its location event, and reuses the
 * focus-aware scroll contract.
 */
export function navigateToContactWithType(
  e: LinkActivation,
  type: string,
): void {
  if (!shouldInterceptLinkActivation(e)) return;
  e.preventDefault();
  if (typeof window === "undefined" || typeof document === "undefined") return;

  const url = new URL(window.location.href);
  url.pathname = "/";
  url.searchParams.set("type", type);
  url.searchParams.delete("pilot");
  url.searchParams.delete("addon");
  url.hash = "contact";
  const destination = `${url.pathname}${url.search}${url.hash}`;

  if (!document.getElementById("contact")) {
    window.location.href = destination;
    return;
  }

  history.pushState(history.state, "", destination);
  scrollToContact();
}

/**
 * Build a Gmail "compose" URL that pre-fills recipient, subject and body.
 * Opens the user's Gmail (web) compose window in a new tab.
 */
export function gmailComposeUrl(
  to: string,
  subject: string,
  body: string,
): string {
  const params = new URLSearchParams({
    view: "cm",
    fs: "1",
    to,
    su: subject,
    body,
  });
  return `https://mail.google.com/mail/?${params.toString()}`;
}

/** Legacy clipboard path — hidden textarea + execCommand. */
function legacyCopy(text: string): boolean {
  let ta: HTMLTextAreaElement | null = null;
  const previousFocus =
    document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
  try {
    ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.top = "-9999px";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    return document.execCommand("copy");
  } catch {
    return false;
  } finally {
    ta?.remove();
    // Removing the temporary textarea must not strand keyboard focus on body.
    // Restoration is best-effort and must never turn a successful copy into an
    // exception.
    if (previousFocus?.isConnected) {
      try {
        previousFocus.focus({ preventScroll: true });
      } catch {
        /* best-effort focus restoration */
      }
    }
  }
}

/**
 * Copy text to the clipboard, returning whether it succeeded. Prefers the async
 * Clipboard API (secure context) but races it against a short timeout so a
 * hung/blocked permission prompt can never leave the UI waiting — it falls back
 * to a hidden-textarea execCommand and always resolves quickly.
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  if (typeof navigator !== "undefined" && navigator.clipboard && window.isSecureContext) {
    try {
      await Promise.race([
        navigator.clipboard.writeText(text),
        new Promise((_, reject) => setTimeout(() => reject(new Error("clipboard-timeout")), 700)),
      ]);
      return true;
    } catch {
      /* fall through to legacy path */
    }
  }
  return legacyCopy(text);
}
