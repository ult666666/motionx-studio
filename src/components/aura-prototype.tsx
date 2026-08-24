"use client";

import { useState } from "react";
import { systemStudy } from "@/content/system-study";
import { cn } from "@/lib/utilities";
import { ChromeObject } from "./system-study-visuals";

/**
 * The site's one deliberate interactive demonstration. Each control exposes
 * one existing design principle on the same composition; it never invents a
 * product state or result. The initial server render remains complete and the
 * visual changes use only opacity/transform so reduced-motion can snap safely.
 */
export function AuraPrototype() {
  const [activeIndex, setActiveIndex] = useState(0);
  const active = systemStudy.prototype.principles[activeIndex];

  return (
    <article className="relative border border-line bg-ink shadow-[0_35px_100px_-55px_#6d7cff88]">
      {/* Registration corners — the edit-suite framing idiom: the accent
          leads top-left, the other three stay hairline-quiet. */}
      <span
        aria-hidden
        className="absolute -left-px -top-px z-10 h-2 w-2 border-l border-t border-accent"
      />
      <span
        aria-hidden
        className="absolute -right-px -top-px z-10 h-2 w-2 border-r border-t border-line"
      />
      <span
        aria-hidden
        className="absolute -bottom-px -left-px z-10 h-2 w-2 border-b border-l border-line"
      />
      <span
        aria-hidden
        className="absolute -bottom-px -right-px z-10 h-2 w-2 border-b border-r border-line"
      />
      <div className="flex items-center gap-2 border-b border-line bg-soft/80 px-4 py-3 md:px-6">
        <span aria-hidden className="h-2 w-2 rounded-full bg-line" />
        <span aria-hidden className="h-2 w-2 rounded-full bg-line" />
        <span aria-hidden className="h-2 w-2 rounded-full bg-line" />
        <span className="ml-2 border-l border-line pl-3 font-mono text-[0.62rem] uppercase tracking-[0.18em] text-gray-dim">
          {systemStudy.prototype.chromeLabel}
        </span>
      </div>

      <div className="relative min-h-[34rem] overflow-hidden px-6 py-7 sm:min-h-[38rem] md:px-10 md:py-9 lg:min-h-[42rem] lg:px-14">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              "radial-gradient(45% 55% at 73% 42%, #171b3a, transparent 70%), radial-gradient(35% 45% at 20% 85%, #d65bd610, transparent 70%)",
          }}
        />

        {/* These overlays are schematic composition guides, not analytics. */}
        <div aria-hidden className="pointer-events-none absolute inset-0">
          <div
            className={cn(
              "absolute right-[8%] top-[19%] aspect-square w-[38%] rounded-full border border-accent-soft/35 opacity-0 transition-[opacity,transform] duration-300 motion-reduce:transition-none",
              activeIndex === 0 && "scale-100 opacity-100",
              activeIndex !== 0 && "scale-90",
            )}
          />
          <div
            className={cn(
              "absolute inset-x-5 bottom-32 top-20 opacity-0 transition-opacity duration-300 motion-reduce:transition-none sm:inset-x-8 md:inset-x-12",
              activeIndex === 1 && "opacity-100",
            )}
          >
            <span className="absolute inset-0 border border-accent-soft/30" />
            <span className="absolute inset-y-[12%] left-[10%] right-[10%] border border-dashed border-white/15" />
            <span className="absolute inset-y-0 left-1/2 w-px bg-white/10" />
          </div>
          <div
            className={cn(
              "absolute bottom-[9.2rem] left-8 right-8 h-px origin-left scale-x-75 bg-gradient-to-r from-accent via-accent-soft/70 to-transparent opacity-0 transition-[opacity,transform] duration-300 motion-reduce:transition-none md:left-14 md:right-[44%]",
              activeIndex === 2 && "scale-x-100 opacity-100",
            )}
          />
        </div>

        <nav
          className="relative flex items-center justify-between"
          aria-label={systemStudy.prototype.navigationLabel}
        >
          <span className="font-mono text-sm font-semibold tracking-[0.25em] text-ivory">
            AURA
          </span>
          <a
            href="#system-breakdown"
            className="inline-flex min-h-11 items-center rounded-full border border-white/20 px-4 py-2 text-xs font-medium text-ivory transition-colors hover:border-white/50 hover:bg-white/5"
          >
            {systemStudy.prototype.breakdownLabel}
          </a>
        </nav>

        <div className="relative grid min-h-[27rem] items-center gap-10 pt-10 md:grid-cols-12 lg:min-h-[31rem]">
          <div className="md:col-span-7">
            <p className="label mb-5 text-accent-soft">
              {systemStudy.prototype.conceptLabel}
            </p>
            <h2
              id="prototype-heading"
              className="display max-w-3xl text-balance text-[clamp(2.6rem,7vw,6.5rem)] text-ivory"
            >
              {systemStudy.prototype.headline}
            </h2>
            <p className="mt-6 max-w-lg text-pretty text-base leading-relaxed text-gray md:text-lg">
              {systemStudy.prototype.body}
            </p>
            <a
              href="#system-breakdown"
              className={cn(
                "group mt-8 inline-flex min-h-12 items-center gap-2 rounded-full cta-primary px-6 py-3 text-sm font-medium transition-[background-color,color,box-shadow] duration-300 motion-reduce:transition-none",
                activeIndex === 2 && "shadow-[0_0_0_5px_rgb(109_124_255_/_0.14)]",
              )}
            >
              {systemStudy.prototype.cta}
              <span
                aria-hidden
                className="transition-transform duration-300 group-hover:translate-x-0.5 motion-reduce:transition-none"
              >
                →
              </span>
            </a>
          </div>
          <div className="flex items-center justify-center md:col-span-5">
            <div
              className={cn(
                "scale-[1.35] transition-[opacity,transform] duration-300 motion-reduce:transition-none sm:scale-[1.6] lg:scale-[2]",
                activeIndex === 0 && "drop-shadow-[0_0_2rem_rgb(109_124_255_/_0.22)]",
                activeIndex === 1 && "opacity-75 sm:scale-[1.48] lg:scale-[1.85]",
              )}
            >
              <ChromeObject size={1.3} />
            </div>
          </div>
        </div>

        <div className="relative border border-line bg-line">
          <p className="label bg-soft/85 px-4 py-3 text-gray-dim">
            {systemStudy.prototype.interactionLabel}
          </p>
          <ol className="grid gap-px sm:grid-cols-3">
            {systemStudy.prototype.principles.map((principle, index) => {
              const selected = activeIndex === index;
              return (
                <li key={principle.label} className="bg-soft/85">
                  <button
                    type="button"
                    aria-pressed={selected}
                    aria-labelledby={`aura-principle-${index}-label`}
                    aria-describedby={`aura-principle-${index}-description`}
                    onClick={() => setActiveIndex(index)}
                    className={cn(
                      "group/principle grid min-h-16 w-full grid-cols-[2rem_1fr] items-center gap-x-3 border-l-2 px-4 py-3 text-left transition-[background-color,border-color] duration-300 motion-reduce:transition-none",
                      selected
                        ? "border-accent bg-accent/[0.055]"
                        : "border-transparent hover:border-white/20 hover:bg-white/[0.025]",
                    )}
                  >
                    <span
                      className={cn(
                        "font-mono text-xs tabular-nums transition-colors duration-300 motion-reduce:transition-none",
                        selected
                          ? "text-accent-soft"
                          : "text-gray-dim group-hover/principle:text-gray",
                      )}
                    >
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span
                      id={`aura-principle-${index}-label`}
                      className="flex items-start justify-between gap-3 text-sm font-medium text-ivory"
                    >
                      {principle.label}
                      {/* Square-edged arming dash — the playhead grammar,
                          not a status dot. */}
                      <span
                        aria-hidden
                        className={cn(
                          "mt-2 h-px w-4 shrink-0 origin-left bg-accent-soft transition-[opacity,transform] duration-300 motion-reduce:transition-none",
                          selected ? "scale-x-100 opacity-100" : "scale-x-50 opacity-0",
                        )}
                      />
                    </span>
                    <span
                      id={`aura-principle-${index}-description`}
                      className="sr-only"
                    >
                      {principle.body}
                    </span>
                  </button>
                </li>
              );
            })}
          </ol>
          <div className="grid gap-3 border-t border-line bg-soft/85 px-4 py-4 sm:grid-cols-[8rem_1fr] sm:items-baseline">
            <p className="label text-gray-dim">
              {systemStudy.prototype.activeLabel}
            </p>
            {/* Keyed so the settle replays per principle; the sr-only live
                region below stays unkeyed and announces the change. */}
            <p
              key={activeIndex}
              className="settle-enter text-pretty text-sm leading-relaxed text-gray"
            >
              {active.body}
            </p>
          </div>
          <p className="sr-only" aria-live="polite">
            {systemStudy.prototype.activeLabel}: {active.label}
          </p>
        </div>
      </div>
    </article>
  );
}
