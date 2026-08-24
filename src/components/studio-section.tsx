import { site } from "@/content/site";
import { MaskedLines, Reveal } from "./reveal";

export function StudioSection() {
  return (
    <section id="studio" className="relative scroll-mt-20 overflow-clip border-t border-line bg-soft py-16 md:py-24">
      {/* quiet accent wash — tonal separation, same register as the intro */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(50% 65% at 12% 18%, #6d7cff0e, transparent 70%)",
        }}
      />
      <div className="shell relative grid gap-10 md:grid-cols-12 md:gap-10">
        <div className="md:col-span-5">
          <Reveal as="p" className="label mb-5 text-accent-soft">
            {site.studio.label}
          </Reveal>
          <h2 className="display text-balance text-[clamp(2.25rem,4.8vw,3.75rem)] text-ivory">
            <MaskedLines lines={[...site.studio.headingLines]} />
          </h2>
        </div>

        <div className="md:col-span-6 md:col-start-7">
          <Reveal as="p" className="text-pretty text-base leading-relaxed text-ivory md:text-lg">
            {site.studio.body}
          </Reveal>
          <Reveal as="p" className="mt-4 text-pretty text-sm leading-relaxed text-gray md:text-base">
            {site.studio.note}
          </Reveal>

          <Reveal
            as="div"
            variant="soft"
            className="mt-7 grid grid-cols-3 gap-4 border-t border-line pt-6"
          >
            {site.studio.facts.map((fact) => (
              <div key={fact.label} className="border-l border-line pl-3 md:pl-4">
                <p className="label mb-2">{fact.label}</p>
                <p className="text-sm text-ivory">{fact.value}</p>
              </div>
            ))}
          </Reveal>

          <Reveal as="div" variant="soft" className="mt-7 border-t border-line pt-6">
            <p className="label mb-4 text-accent-soft">{site.studio.standardsLabel}</p>
            <ul className="flex flex-wrap gap-x-5 gap-y-2">
              {site.trustStandards.map((standard) => (
                <li
                  key={standard.label}
                  className="border-l border-accent/35 pl-3 text-sm text-gray"
                >
                  {standard.label}
                </li>
              ))}
            </ul>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
