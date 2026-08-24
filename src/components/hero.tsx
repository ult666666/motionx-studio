import Link from "next/link";
import { site } from "@/content/site";
import { HeroReel } from "./hero-reel";
import { StartProjectLink } from "./start-project-link";

/**
 * Server-rendered hero shell. All first-screen copy is static HTML; the
 * background teaser + play/pause control live in the HeroReel client island and
 * the primary CTA's scroll contract in StartProjectLink. Entrances are the
 * CSS-only hero-enter/hero-line treatments, so nothing here waits on
 * hydration.
 */
export function Hero() {
  const lines = site.hero.headlineLines;

  return (
    <section
      id="top"
      className="relative flex min-h-[100svh] w-full items-end overflow-clip bg-ink"
    >
      <HeroReel label={site.hero.screening.title} />

      {/* One clear thesis over the moving visual world. Screening provenance is
          attached to the media below instead of competing with the headline. */}
      <div className="shell relative z-10 w-full pb-44 pt-32 md:pb-40">
        <div className="max-w-3xl">
          <p
            className="hero-enter label over-media mb-6 text-accent-soft"
            style={{ animationDelay: "50ms" }}
          >
            {site.hero.eyebrow}
          </p>

          <h1 className="display text-[clamp(2.6rem,6vw,5rem)] text-ivory">
            {lines.map((line, i) => (
              <span
                key={i}
                style={{ display: "block", overflow: "hidden", paddingBottom: "0.04em" }}
              >
                <span
                  className="hero-line__inner block will-change-transform"
                  style={{ animationDelay: `${180 + i * 80}ms` }}
                >
                  {line}
                </span>
              </span>
            ))}
          </h1>

          <p
            className="hero-supporting-copy hero-enter over-media mt-7 max-w-lg text-pretty text-base leading-relaxed text-gray md:text-lg"
            style={{ animationDelay: "420ms" }}
          >
            {site.hero.sub}
          </p>

          <div
            className="hero-enter mt-9 flex flex-wrap items-center gap-x-6 gap-y-3"
            style={{ animationDelay: "500ms" }}
          >
            <StartProjectLink className="group inline-flex min-h-12 items-center justify-center gap-2 rounded-full cta-primary px-7 py-3.5 text-sm font-medium transition-colors duration-300">
              {site.cta.primary}
              <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">→</span>
            </StartProjectLink>
            <a
              href="#work"
              className="group link-underline inline-flex min-h-11 items-center gap-2 px-1 py-2 text-sm font-medium text-gray hover:text-ivory"
            >
              {site.cta.secondary}
              <span
                aria-hidden
                className="transition-transform duration-300 group-hover:translate-y-0.5"
              >
                ↓
              </span>
            </a>
          </div>
        </div>
      </div>

      {/* Media caption rail — project context, provenance, and claim boundary
          stay attached to the footage they qualify. */}
      <div className="absolute inset-x-0 bottom-0 z-10 border-y border-white/10 bg-ink/78 backdrop-blur-md">
        <div className="shell flex min-h-32 flex-col justify-center gap-3 py-4 pr-20 md:min-h-24 md:flex-row md:items-center md:gap-6 md:py-5 md:pr-28">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
            <span className="label shrink-0 text-accent-soft">
              {site.hero.screening.label}
            </span>
            <span aria-hidden className="hidden h-px w-5 bg-white/20 sm:block" />
            <Link
              href={site.hero.screening.href}
              prefetch={false}
              aria-label={site.hero.screening.linkLabel}
              className="group/screening link-underline inline-flex min-h-11 items-center gap-2 text-sm font-medium text-ivory"
            >
              {site.hero.screening.title}
              <span
                aria-hidden
                className="transition-transform duration-300 group-hover/screening:translate-x-0.5 motion-reduce:transition-none"
              >
                →
              </span>
            </Link>
            <span className="concept-mark">{site.hero.screening.status}</span>
          </div>
          <p className="max-w-2xl text-pretty text-xs leading-relaxed text-gray md:ml-auto md:max-w-xl md:text-right">
            {site.hero.screening.disclosure}
          </p>
        </div>
      </div>
    </section>
  );
}
