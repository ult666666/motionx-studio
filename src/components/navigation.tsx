"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type MouseEvent,
} from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  availabilityLabel,
  brandName,
  navLinks,
  primaryCtaLabel,
  sectionReadout,
} from "@/content/chrome";
import {
  cn,
  focusSectionHeading,
  scrollToContact,
  shouldInterceptLinkActivation,
} from "@/lib/utilities";
import { Logotype } from "./logotype";

const HOME_LINKS = navLinks.filter((item) => item.href.startsWith("/#"));

/**
 * Where the engine supports root scroll timelines, CSS drives the header
 * playhead (.nav-playhead in globals.css) and the rAF loop must not write the
 * transform — the two would double-drive it. This string must stay
 * character-identical to the @supports condition in globals.css. Evaluated
 * lazily so the module stays SSR-safe.
 */
const supportsScrollDrivenPlayhead = () =>
  typeof CSS !== "undefined" && CSS.supports("animation-timeline: scroll(root)");

export function Navigation() {
  const pathname = usePathname();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [activeHref, setActiveHref] = useState<string | null>(null);
  const toggleRef = useRef<HTMLButtonElement>(null);
  const dialogCloseRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLSpanElement>(null);
  const restoreToggleOnCloseRef = useRef(true);
  const pendingSectionFocusRef = useRef<string | null>(null);

  const closeMenu = useCallback(
    ({
      restoreToggle,
      sectionId = null,
    }: {
      restoreToggle: boolean;
      sectionId?: string | null;
    }) => {
      restoreToggleOnCloseRef.current = restoreToggle;
      pendingSectionFocusRef.current = sectionId;
      setOpen(false);
    },
    [],
  );

  const handleMenuLinkActivation = (
    event: MouseEvent<HTMLAnchorElement>,
    href: string,
  ) => {
    if (!shouldInterceptLinkActivation(event)) return;

    if (pathname === "/" && href.startsWith("/#")) {
      closeMenu({ restoreToggle: false, sectionId: href.slice(2) });
      return;
    }

    // Activating the already-current page is equivalent to dismissing the
    // dialog. A real cross-route navigation must retain control of route focus.
    closeMenu({ restoreToggle: pathname === href });
  };

  // One frame owns all scroll-derived navigation state. Read layout first,
  // then write the playhead transform so active-section tracking never follows
  // an interleaved DOM write from a second scroll loop.
  useEffect(() => {
    let frame = 0;
    const cssPlayhead = supportsScrollDrivenPlayhead();
    const update = () => {
      frame = 0;
      const scrollY = window.scrollY;
      const viewportHeight = window.innerHeight;
      const nextScrolled = scrollY > 24;
      const max = document.documentElement.scrollHeight - viewportHeight;
      const progress = max > 0 ? Math.min(1, Math.max(0, scrollY / max)) : 0;
      let nextActive: string | null;

      if (pathname === "/") {
        const readingLine = 80 + viewportHeight * 0.24;
        nextActive = null;
        for (const item of HOME_LINKS) {
          const id = item.href.split("#")[1];
          const section = document.getElementById(id);
          if (!section) continue;
          const rect = section.getBoundingClientRect();
          if (rect.top <= readingLine && rect.bottom > readingLine) {
            nextActive = item.href;
          }
        }
      } else {
        nextActive =
          pathname === "/pilot"
            ? "/pilot"
            : pathname.startsWith("/work/")
              ? "/#work"
              : null;
      }

      if (!cssPlayhead && progressRef.current) {
        progressRef.current.style.transform = `scaleX(${progress})`;
      }
      setScrolled((current) =>
        current === nextScrolled ? current : nextScrolled,
      );
      setActiveHref((current) =>
        current === nextActive ? current : nextActive,
      );
    };
    const requestUpdate = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", requestUpdate, { passive: true });
    window.addEventListener("resize", requestUpdate, { passive: true });
    if (pathname === "/") {
      window.addEventListener("hashchange", requestUpdate);
    }
    return () => {
      window.removeEventListener("scroll", requestUpdate);
      window.removeEventListener("resize", requestUpdate);
      window.removeEventListener("hashchange", requestUpdate);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, [pathname]);

  // Preserve any pre-existing body style while the mobile navigation owns the
  // viewport. This also prevents background content moving under the overlay.
  useEffect(() => {
    if (!open) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open]);

  // The overlay behaves as a modal navigation surface. Keep the persistent
  // header visible, but remove its trigger and the page content from focus and
  // the accessibility tree while the dialog-owned close control is active.
  useEffect(() => {
    if (!open) return;
    const background = Array.from(
      document.querySelectorAll<HTMLElement>(
        'body > a[href="#content"], main, footer',
      ),
    ).map((element) => ({ element, inert: element.inert }));
    background.forEach(({ element }) => {
      element.inert = true;
    });
    return () => {
      background.forEach(({ element, inert }) => {
        element.inert = inert;
      });
    };
  }, [open]);

  // Move focus to the dialog-owned close control on open. Escape and explicit
  // dismissal restore the persistent toggle; navigation either focuses a
  // same-page destination heading or leaves focus to the incoming route.
  useEffect(() => {
    if (!open) return;
    const toggle = toggleRef.current;
    const timer = window.setTimeout(
      () => dialogCloseRef.current?.focus(),
      20,
    );
    return () => {
      window.clearTimeout(timer);
      const sectionId = pendingSectionFocusRef.current;
      pendingSectionFocusRef.current = null;

      if (sectionId) {
        // Let the Link complete its hash update and the inert cleanup commit
        // before moving focus into the destination section.
        window.requestAnimationFrame(() => focusSectionHeading(sectionId));
      } else if (restoreToggleOnCloseRef.current) {
        toggle?.focus();
      }
    };
  }, [open]);

  // Escape closes; Tab remains inside the aria-modal dialog.
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        closeMenu({ restoreToggle: true });
        return;
      }
      if (event.key !== "Tab") return;
      const nodes = Array.from(
        menuRef.current?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      );
      if (nodes.length === 0) return;
      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [closeMenu, open]);

  // A menu opened in portrait must not keep the page locked after resizing to
  // the desktop navigation.
  useEffect(() => {
    const desktop = window.matchMedia("(min-width: 768px)");
    const closeOnDesktop = (event: MediaQueryListEvent) => {
      if (event.matches) {
        // The mobile toggle becomes display:none at this breakpoint, so it is
        // not a valid restoration target after a rotation/resize.
        closeMenu({ restoreToggle: false });
      }
    };
    desktop.addEventListener("change", closeOnDesktop);
    return () => desktop.removeEventListener("change", closeOnDesktop);
  }, [closeMenu]);

  const currentState = (href: string) => {
    if (activeHref !== href) return undefined;
    return pathname === href ? ("page" as const) : ("location" as const);
  };

  return (
    <>
      <header
        inert={open ? true : undefined}
        className={cn(
          // Blur stays a class-based snap by contract (transition-property
          // must never include backdrop-filter); only the colours interpolate,
          // now on the cinematic curve.
          "fixed inset-x-0 top-0 z-50 transition-[background-color,border-color] duration-500 ease-cinematic",
          // Open state matches the dialog's bg-ink/98 exactly — a lighter
          // header over the menu panel reads as a translucency seam with
          // page copy ghosting through the top band.
          open
            ? "border-b border-line bg-ink/98 backdrop-blur-xl"
            : scrolled
              ? "border-b border-line bg-ink/88 backdrop-blur-xl"
              : "border-b border-transparent bg-transparent",
        )}
      >
        <nav
          className="shell flex h-16 items-center justify-between md:h-20"
          aria-label="Primary"
        >
          <Link
            href="/#top"
            prefetch={false}
            className="text-xl md:text-2xl"
            aria-label={`${brandName} — home`}
          >
            <Logotype />
          </Link>

          {/* HUD readout: the active section as edit-suite telemetry, idle
              state is the real availability line. Decorative — the links
              below carry the accessible aria-current state. */}
          <span
            aria-hidden
            className="label pointer-events-none hidden text-gray-dim transition-colors duration-500 lg:block"
          >
            {(activeHref && sectionReadout[activeHref]) ?? availabilityLabel}
          </span>

          <ul className="hidden items-center gap-7 md:flex">
            {navLinks.map((item) => {
              const current = currentState(item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    prefetch={false}
                    aria-current={current}
                    className={cn(
                      "group/nav relative inline-flex min-h-11 items-center py-2",
                      "label transition-colors duration-300 hover:text-ivory",
                      current ? "text-ivory" : "text-gray",
                    )}
                  >
                    {/* Drawn underline expresses the existing aria-current
                        state; hover previews it at reduced presence. Absolute,
                        so the 44px target and header height never change. */}
                    <span
                      aria-hidden
                      className={cn(
                        "absolute inset-x-0 bottom-1 h-px origin-left bg-accent-soft transition-[transform,opacity] duration-500 ease-cinematic motion-reduce:transition-none",
                        current
                          ? "scale-x-100 opacity-100"
                          : "scale-x-0 opacity-40 group-hover/nav:scale-x-50 group-focus-visible/nav:scale-x-50",
                      )}
                    />
                    {item.label}
                  </Link>
                </li>
              );
            })}
            <li>
              <Link
                href="/#contact"
                prefetch={false}
                onClick={(event) => {
                  if (!shouldInterceptLinkActivation(event)) return;
                  scrollToContact(event);
                }}
                className="group inline-flex min-h-11 items-center gap-2 rounded-full border border-line cta-primary px-5 py-2.5 text-sm font-medium transition-colors duration-300"
              >
                {primaryCtaLabel}
                <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">→</span>
              </Link>
            </li>
          </ul>

          <button
            ref={toggleRef}
            type="button"
            onClick={() => {
              restoreToggleOnCloseRef.current = true;
              pendingSectionFocusRef.current = null;
              setOpen(true);
            }}
            disabled={open}
            className={cn(
              "relative z-50 flex h-11 w-11 items-center justify-center rounded-full border border-line text-ivory md:hidden",
              open && "invisible pointer-events-none",
            )}
            aria-expanded={open}
            aria-controls="mobile-menu"
            aria-label="Open menu"
          >
            <span className="relative block h-3 w-5">
              <span
                className="absolute left-0 top-0 block h-px w-5 bg-ivory"
              />
              <span
                className="absolute left-0 top-1.5 block h-px w-5 bg-ivory"
              />
              <span
                className="absolute left-0 top-3 block h-px w-5 bg-ivory"
              />
            </span>
          </button>
        </nav>

        <span
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -bottom-px h-px overflow-hidden bg-transparent motion-reduce:hidden"
        >
          <span
            ref={progressRef}
            className="nav-playhead block h-full origin-left scale-x-0 bg-gradient-to-r from-accent via-accent-soft to-magenta will-change-transform"
          />
        </span>
      </header>

      {open && (
        <div
          ref={menuRef}
          id="mobile-menu"
          role="dialog"
          aria-modal="true"
          aria-labelledby="mobile-menu-title"
          className="menu-overlay-enter fixed inset-0 top-16 z-40 overflow-y-auto overscroll-contain bg-ink/98 backdrop-blur-xl md:hidden [padding-bottom:max(2rem,env(safe-area-inset-bottom))]"
        >
          <nav
            aria-labelledby="mobile-menu-title"
            className="shell flex min-h-full flex-col pt-6"
          >
            <div className="flex min-h-12 items-center justify-between gap-4 border-b border-line pb-3">
              <p id="mobile-menu-title" className="label text-gray-dim">
                Navigate the studio
              </p>
              <button
                ref={dialogCloseRef}
                type="button"
                onClick={() => closeMenu({ restoreToggle: true })}
                aria-label="Close navigation"
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border border-line text-ivory transition-colors hover:bg-white/5"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden>
                  <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
                </svg>
              </button>
            </div>
            <ul>
              {navLinks.map((item, index) => {
                const current = currentState(item.href);
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      prefetch={false}
                      aria-current={current}
                      onClick={(event) =>
                        handleMenuLinkActivation(event, item.href)
                      }
                      className="group grid min-h-16 grid-cols-[minmax(0,1fr)_auto] items-center gap-3 border-b border-line py-4"
                    >
                      {/* The masked rise animates only this inner span — the
                          link row itself stays static and hit-testable from
                          the first frame. */}
                      <span className="block overflow-hidden">
                        <span
                          className={cn(
                            "menu-item-enter display block text-[2rem]",
                            current ? "text-accent-soft" : "text-ivory",
                          )}
                          style={{ "--menu-i": index } as React.CSSProperties}
                        >
                          {item.label}
                        </span>
                      </span>
                      <span aria-hidden className="text-sm text-gray transition-transform duration-300 group-hover:translate-x-1">
                        →
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>

            <div className="menu-cta-enter mt-auto pt-8">
              {/* Edit-suite metadata rail — closes the panel's empty band and
                  gives the mobile menu the same HUD language as the desktop
                  header. Decorative and non-focusable, so the dialog's
                  focus-trap query is untouched. */}
              <div
                aria-hidden
                className="mb-5 flex items-center justify-between gap-4 border-t border-line pt-5"
              >
                <span className="label border-l border-accent/60 pl-3 text-gray">
                  {brandName}
                </span>
                <span className="label text-gray-dim">{availabilityLabel}</span>
              </div>
              <Link
                href="/#contact"
                prefetch={false}
                onClick={(event) => {
                  if (!shouldInterceptLinkActivation(event)) return;
                  closeMenu({ restoreToggle: false });
                  scrollToContact(event);
                }}
                className="flex min-h-12 w-full items-center justify-center rounded-full bg-ivory px-6 py-4 text-base font-medium text-ink"
              >
                {primaryCtaLabel}
              </Link>
            </div>
          </nav>
        </div>
      )}
    </>
  );
}
