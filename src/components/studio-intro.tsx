import { site } from "@/content/site";
import { MaskedLines, Reveal } from "./reveal";

/**
 * Compact studio thesis — promise before proof. Asymmetric editorial layout,
 * capped height so it creates anticipation for Selected Work rather than
 * pausing the site on a full screen of black.
 */
export function StudioIntro() {
  return (
    <section className="relative overflow-clip border-t border-line bg-soft py-14 md:py-16">
      {/* subtle blue-shift wash for tonal separation from the hero */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-80"
        style={{
          background:
            "radial-gradient(60% 80% at 85% 30%, #6d7cff10, transparent 70%)",
        }}
      />
      <div className="shell relative grid gap-x-12 gap-y-8 md:grid-cols-12 md:items-end">
        <div className="md:col-span-8">
          <Reveal as="p" className="label mb-5 text-accent-soft">
            {site.studioIntro.label}
          </Reveal>
          <h2 className="display text-balance text-[clamp(1.85rem,4.4vw,3.6rem)] text-ivory">
            <MaskedLines lines={[...site.studioIntro.statementLines]} />
          </h2>
        </div>

        <div className="md:col-span-4">
          <Reveal as="div" className="relative pt-5">
            {/* Drawn accent rule stands in for the old static border-t;
                the un-gated state is fully drawn. */}
            <div
              aria-hidden
              className="rule-draw-x absolute inset-x-0 top-0 h-px bg-gradient-to-r from-accent/70 to-transparent"
            />
            <p className="label mb-2 text-gray-dim">{site.studioIntro.audienceLabel}</p>
            <p className="text-pretty text-sm leading-relaxed text-ivory">
              {site.studioIntro.audience}
            </p>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
