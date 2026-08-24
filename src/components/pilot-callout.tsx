import Link from "next/link";
import { pilotCallout } from "@/content/pilot";
import { Reveal } from "./reveal";

/**
 * Restrained pilot-launch callout linking to /pilot. Editorial, not a loud
 * promo banner — keeps the premium feel while announcing pilot pricing.
 * Copy comes from `pilotCallout` in src/content/pilot.ts (single source).
 */
export function PilotCallout() {
  return (
    <section className="scroll-mt-20 border-t border-line bg-soft py-10 md:py-12">
      <div className="shell">
        {/* Same restrained accent-band language as the Services signature
            engagement row: one accent edge + a ≤4% tonal field, never a
            promotional banner. */}
        <Reveal as="div" className="signature-band flex flex-col gap-5 border-y border-accent/30 border-l-2 border-l-accent bg-accent/[0.035] px-5 py-6 md:flex-row md:items-center md:justify-between md:gap-8 md:px-6">
          <div className="flex flex-col gap-2 md:flex-row md:items-baseline md:gap-8">
            <p className="label shrink-0 text-accent-soft">{pilotCallout.label}</p>
            <h2 className="display max-w-2xl text-balance text-[clamp(1.5rem,3vw,2.25rem)] text-ivory">
              {pilotCallout.heading}
            </h2>
          </div>
          <Link
            href="/pilot"
            className="group link-underline inline-flex min-h-11 shrink-0 items-center gap-3 self-start text-sm font-medium text-ivory hover:text-accent-soft md:self-auto [--underline-rest:var(--color-line)]"
          >
            {pilotCallout.cta}
            <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-1">→</span>
          </Link>
        </Reveal>
      </div>
    </section>
  );
}
