import Link from "next/link";
import {
  launchSystem,
  launchSystemCta,
  launchSystemIntro,
} from "@/content/services";
import { MaskedLines, Reveal } from "./reveal";
import { StageCampaign, StageFilm, StageWebsite } from "./system-study-visuals";

/**
 * Homepage summary of the self-owned AURA system study. The dedicated route
 * carries the full breakdown; this section gives a fast, server-rendered proof
 * of continuity without repeating the entire case study on the homepage.
 */
export function LaunchSystem() {
  return (
    <section
      id="launch-system"
      className="relative scroll-mt-20 overflow-clip border-t border-line py-16 md:py-24"
      style={{
        background:
          "linear-gradient(180deg, var(--color-blueblack), #0a0c16 55%, var(--color-blueblack))",
      }}
    >
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-90"
        style={{
          background:
            "radial-gradient(45% 40% at 50% 0%, #6d7cff1c, transparent 70%), radial-gradient(40% 50% at 90% 100%, #d65bd610, transparent 70%)",
        }}
      />

      <div className="shell relative">
        <div className="mb-9 max-w-4xl md:mb-12">
          <Reveal as="div" className="mb-5 flex flex-wrap items-center gap-3">
            <span className="label text-accent-soft">{launchSystemIntro.label}</span>
            <span className="concept-mark">{launchSystemIntro.conceptLabel}</span>
          </Reveal>
          <h2 className="display text-balance text-[clamp(2rem,5.2vw,4rem)] text-ivory">
            <MaskedLines lines={[launchSystemIntro.heading]} />
          </h2>
          <p className="mt-6 max-w-2xl text-pretty text-base leading-relaxed text-gray md:text-lg">
            {launchSystemIntro.body}
          </p>
        </div>

        <div className="grid gap-3 sm:grid-cols-12 sm:gap-4" aria-hidden="true">
          <div className="sm:col-span-7">
            <StageFilm />
          </div>
          {/* Stacked until sm — at 390px a forced two-column split rendered
              the campaign frames ~100px wide and their type overlapped the
              chrome object. */}
          <div className="grid grid-cols-1 gap-3 sm:col-span-5 sm:grid-cols-2 sm:items-stretch sm:gap-4">
            <StageWebsite />
            <StageCampaign />
          </div>
        </div>

        <div className="mt-6">
          <p className="label mb-3 text-gray">{launchSystemIntro.outputsLabel}</p>
          {/* Continuity line — the section's whole argument is connection, so
              the drawn accent→magenta rule carries across all three outputs.
              Static fallback: fully drawn. */}
          <div
            aria-hidden
            className="rule-draw-x mb-0 h-px w-full bg-gradient-to-r from-accent via-accent-soft/70 to-magenta/80"
            style={{ ["--draw-range" as string]: "entry 20% cover 60%" }}
          />
          <ol className="grid border-b border-line sm:grid-cols-3">
            {launchSystem.map((stage) => (
              <li
                key={stage.index}
                className="border-b border-line py-4 last:border-b-0 sm:border-b-0 sm:px-5 sm:first:pl-0 sm:last:pr-0 sm:[&:not(:first-child)]:border-l"
              >
                <div className="flex items-baseline gap-3">
                  <p className="label text-accent-soft">{stage.index}</p>
                  <h3 className="text-sm font-medium text-ivory">{stage.title}</h3>
                </div>
                <p className="mt-2 text-pretty text-xs leading-relaxed text-gray-dim">
                  {stage.outputs.join(" · ")}
                </p>
              </li>
            ))}
          </ol>
        </div>

        <div className="mt-8 flex flex-col gap-4 border-t border-accent/30 pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="label text-accent-soft">{launchSystemCta.label}</p>
          <Link
            href={launchSystemCta.primaryHref}
            className="group inline-flex min-h-11 items-center justify-center gap-2 self-start rounded-full cta-primary px-6 py-3 text-sm font-medium transition-colors duration-300 sm:self-auto"
          >
            {launchSystemCta.primary}
            <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">
              →
            </span>
          </Link>
        </div>
      </div>
    </section>
  );
}
