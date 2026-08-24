"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utilities";
import { VideoPlayer } from "./video-player";

type EditBayItem = {
  slug: string;
  title: string;
  index: string;
  capability: string;
  conceptLabel: string;
  duration: string;
  /** Server-composed edit-suite readout, e.g. "TRT 00:15". */
  trt: string;
  orientation: "portrait" | "landscape";
  width: number;
  height: number;
  video: string;
  videoMobile: string;
  poster: string;
  captions: string;
  accent: string;
  demonstrates: string;
};

const HASH_PREFIX = "#work-";

function slugFromHash(hash: string, items: ReadonlyArray<EditBayItem>) {
  if (!hash.startsWith(HASH_PREFIX)) return null;
  try {
    const slug = decodeURIComponent(hash.slice(HASH_PREFIX.length));
    return items.some((item) => item.slug === slug) ? slug : null;
  } catch {
    return null;
  }
}

/**
 * One active film at a time: a compact edit-suite index changes a single media
 * stage. Preview controls and canonical case-study links stay separate so the
 * interaction never changes meaning after hydration. Each preview selection is
 * recorded in the hash so browser Back/Forward restores the active project.
 */
export function SelectedWorkEditBay({
  items,
  nowViewingLabel,
  previewLabel,
  openCaseStudyLabel,
  caseStudyCta,
}: {
  items: ReadonlyArray<EditBayItem>;
  nowViewingLabel: string;
  previewLabel: string;
  openCaseStudyLabel: string;
  caseStudyCta: string;
}) {
  const firstSlug = items[0]?.slug ?? "";
  const [activeSlug, setActiveSlug] = useState(firstSlug);

  useEffect(() => {
    const syncFromLocation = () => {
      const slug = slugFromHash(window.location.hash, items);
      setActiveSlug(slug ?? firstSlug);
    };

    syncFromLocation();
    window.addEventListener("popstate", syncFromLocation);
    window.addEventListener("hashchange", syncFromLocation);
    window.addEventListener("motionx:locationchange", syncFromLocation);
    return () => {
      window.removeEventListener("popstate", syncFromLocation);
      window.removeEventListener("hashchange", syncFromLocation);
      window.removeEventListener("motionx:locationchange", syncFromLocation);
    };
  }, [firstSlug, items]);

  const active = items.find((item) => item.slug === activeSlug) ?? items[0];
  if (!active) return null;

  const selectProject = (slug: string) => {
    const destinationHash = `#work-${slug}`;
    if (window.location.hash !== destinationHash) {
      const url = new URL(window.location.href);
      url.hash = destinationHash;
      history.pushState(
        history.state,
        "",
        `${url.pathname}${url.search}${url.hash}`,
      );
    }
    setActiveSlug(slug);
    window.dispatchEvent(new Event("motionx:locationchange"));
  };

  return (
    <div className="grid gap-6 lg:grid-cols-12 lg:gap-8">
      <div className="lg:sticky lg:top-28 lg:col-span-4 lg:self-start">
        <ol className="grid gap-px border border-line bg-line">
          {items.map((item) => {
            const isActive = item.slug === active.slug;
            return (
              <li
                id={`work-${item.slug}`}
                key={item.slug}
                className="min-w-0 scroll-mt-28 bg-ink"
              >
                <div
                  className={cn(
                    "group relative grid min-h-14 grid-cols-[minmax(0,1fr)_3.5rem] transition-colors duration-300 lg:min-h-32 lg:grid-cols-1 lg:grid-rows-[1fr_auto]",
                    isActive ? "bg-panel" : "hover:bg-white/[0.035]",
                  )}
                >
                  {/* Scale lives in classes (not inline style) so the partial
                      hover/focus arming cue can compose with the active state;
                      only the per-project colour stays inline. */}
                  <span
                    aria-hidden
                    className={cn(
                      "absolute inset-y-0 left-0 w-0.5 origin-bottom transition-transform duration-300 motion-reduce:transition-none",
                      isActive
                        ? "scale-y-100"
                        : "scale-y-0 group-hover:scale-y-[0.28] group-focus-within:scale-y-[0.28]",
                    )}
                    style={{ backgroundColor: item.accent }}
                  />
                  <button
                    type="button"
                    onClick={() => selectProject(item.slug)}
                    aria-controls="selected-work-panel"
                    aria-pressed={isActive}
                    aria-label={`${previewLabel}: ${item.title}`}
                    className={cn(
                      "relative flex min-h-14 min-w-0 items-center gap-3 px-4 py-2 text-left transition-colors lg:block lg:min-h-16 lg:px-5 lg:py-4",
                      isActive ? "text-ivory" : "text-gray group-hover:text-ivory",
                    )}
                  >
                    <span className="flex min-w-0 flex-1 items-center gap-3 lg:block">
                      <span className="label shrink-0 text-accent-soft lg:hidden">
                        {item.index}
                      </span>
                      <span className="min-w-0 flex-1 truncate text-sm font-medium lg:hidden">
                        {item.title}
                      </span>
                      {isActive && (
                        <span className="label shrink-0 whitespace-nowrap text-ivory lg:hidden">
                          {nowViewingLabel}
                        </span>
                      )}

                      <span className="hidden lg:block">
                        <span className="flex items-start justify-between gap-2">
                          <span className="label block text-accent-soft">
                            {item.index}
                          </span>
                          <span
                            className={cn(
                              "label shrink-0 transition-colors",
                              isActive ? "text-ivory" : "text-gray-dim",
                            )}
                          >
                            {isActive ? nowViewingLabel : previewLabel}
                          </span>
                        </span>
                        <span
                          className="mt-2 block truncate text-sm font-medium"
                        >
                          {item.title}
                        </span>
                        <span className="label mt-2 block tabular-nums text-gray-dim">
                          {item.trt}
                        </span>
                      </span>
                    </span>
                  </button>
                  <Link
                    href={`/work/${item.slug}`}
                    prefetch={false}
                    className="relative flex min-h-14 items-center justify-center border-l border-line px-2 py-2 text-xs text-gray-dim transition-colors hover:bg-white/[0.035] hover:text-ivory lg:min-h-11 lg:justify-between lg:border-l-0 lg:border-t lg:px-5"
                    aria-label={`${openCaseStudyLabel}: ${item.title}`}
                  >
                    <span className="hidden lg:inline">{openCaseStudyLabel}</span>
                    <span aria-hidden>↗</span>
                  </Link>
                </div>
              </li>
            );
          })}
        </ol>
      </div>

      <div className="min-w-0 lg:col-span-8">
        <p role="status" aria-live="polite" aria-atomic="true" className="sr-only">
          {nowViewingLabel} {active.title}
        </p>

        <article
          id="selected-work-panel"
          className="min-w-0"
          aria-labelledby={`selected-work-title-${active.slug}`}
          style={{ ["--project-accent" as string]: active.accent }}
        >
          {/* Keyed remount preserves the muted/CC reset contracts; the enter
              classes sit on the two children so the stage settles first and
              the meta grid follows 90ms later. */}
          <div key={active.slug}>
          <div className="selected-work-panel relative border border-line bg-panel p-2 sm:p-3">
          {/* Ambient light cast by the active film onto the stage — sits
              behind the header/media (both positioned) and follows the
              registered accent cross-fade between films. */}
          <span
            aria-hidden
            className="stage-ambient pointer-events-none absolute inset-0"
          />
          {/* Registration corners — active accent leads top-left, the other
              three stay hairline-quiet. */}
          <span
            aria-hidden
            className="absolute -left-px -top-px h-2 w-2 border-l border-t border-[var(--project-accent)]"
          />
          <span
            aria-hidden
            className="absolute -right-px -top-px h-2 w-2 border-r border-t border-line"
          />
          <span
            aria-hidden
            className="absolute -bottom-px -left-px h-2 w-2 border-b border-l border-line"
          />
          <span
            aria-hidden
            className="absolute -bottom-px -right-px h-2 w-2 border-b border-r border-line"
          />
          <div className="relative flex flex-wrap items-center justify-between gap-3 border-b border-line px-2 pb-3 pt-1 sm:px-3 sm:pb-4 sm:pt-2">
            <p className="label leading-relaxed text-gray-dim">
              {nowViewingLabel} · {active.index} ·{" "}
              <span className="text-ivory">{active.title}</span>
            </p>
            <span className="concept-mark">{active.conceptLabel}</span>
          </div>
          <div
            className={cn(
              "relative mx-auto mt-2 sm:mt-3",
              active.orientation === "portrait" && "max-w-[360px]",
            )}
          >
            <VideoPlayer
              label={active.title}
              src={active.video}
              mobileSrc={active.videoMobile}
              poster={active.poster}
              captionsSrc={active.captions}
              width={active.width}
              height={active.height}
              rounded={false}
              telemetry
            />
          </div>
        </div>

        <div className="selected-work-panel-meta mt-6 grid gap-6 border-b border-line pb-6 sm:grid-cols-12 sm:gap-8">
          <div className="sm:col-span-7">
            <span className="label">{active.index}</span>
            <h3
              id={`selected-work-title-${active.slug}`}
              className="display mt-3 text-[clamp(2.25rem,5vw,4rem)] text-ivory"
            >
              {active.title}
            </h3>
            <p className="label mt-4 text-[var(--project-accent)]">
              {active.capability}
            </p>
            <p className="label mt-2.5 tabular-nums text-gray-dim">{active.trt}</p>
          </div>

          <div className="flex flex-col items-start justify-end sm:col-span-5 sm:items-end sm:text-right">
            <p className="max-w-sm text-pretty text-sm leading-relaxed text-gray sm:text-base">
              {active.demonstrates}
            </p>
            <Link
              href={`/work/${active.slug}`}
              prefetch={false}
              className="group link-underline mt-5 inline-flex min-h-11 items-center gap-2 px-1 py-2 text-sm font-medium text-ivory [--underline-from:var(--project-accent)] [--underline-to:var(--project-accent)]"
            >
              {caseStudyCta}
              <span
                aria-hidden
                className="transition-transform duration-300 group-hover:translate-x-1"
              >
                →
              </span>
            </Link>
          </div>
          </div>
          </div>
        </article>
      </div>
    </div>
  );
}
