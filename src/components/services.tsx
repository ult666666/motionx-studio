import {
  services,
  serviceDetailLabels,
  servicesIntro,
  servicesLede,
  signatureEngagement,
} from "@/content/services";
import { ContactTypeLink } from "./contact-type-link";
import { MaskedLines, Reveal } from "./reveal";

export function Services() {
  return (
    <section id="services" className="relative scroll-mt-20 border-t border-line bg-soft py-16 md:py-24">
      <div className="shell">
        <div className="mb-9 flex flex-col gap-4 md:mb-12 md:flex-row md:items-end md:justify-between">
          <div className="max-w-2xl">
            <Reveal as="p" className="label mb-5 text-accent-soft">
              {servicesIntro.label}
            </Reveal>
            <Reveal as="div">
              <h2 className="display text-balance text-[clamp(2rem,5vw,3.75rem)] text-ivory">
                <MaskedLines lines={[servicesIntro.heading]} />
              </h2>
            </Reveal>
          </div>
          <Reveal as="p" className="max-w-xs text-pretty text-sm leading-relaxed text-gray md:text-right">
            {servicesLede}
          </Reveal>
        </div>

        <Reveal
          as="div"
          className="signature-band mb-9 flex flex-col gap-4 border-y border-accent/30 border-l-2 border-l-accent bg-accent/[0.035] px-5 py-5 sm:flex-row sm:items-center sm:justify-between md:mb-12 md:px-6"
        >
          <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:gap-5">
            <p className="label text-accent-soft">{signatureEngagement.label}</p>
            <h3 className="text-base font-medium text-ivory md:text-lg">
              {signatureEngagement.title}
            </h3>
          </div>
          <ContactTypeLink
            formType={signatureEngagement.formType}
            className="group link-underline inline-flex min-h-11 items-center gap-2 self-start text-sm font-medium text-ivory hover:text-accent-soft sm:self-auto [--underline-rest:transparent]"
          >
            {signatureEngagement.cta}
            <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">
              →
            </span>
          </ContactTypeLink>
        </Reveal>

        {/* Compact editorial rows. Native details keep depth available without
            making every service compete for attention at once. */}
        <div className="border-t border-line">
          {services.map((service) => (
            <Reveal
              key={service.index}
              className="group relative grid grid-cols-1 items-baseline gap-3 border-b border-line py-5 transition-colors duration-500 hover:bg-white/[0.02] md:grid-cols-12 md:gap-6 md:py-6"
            >
              {/* hover sweep — a thin accent that grows from the left edge */}
              <span
                aria-hidden
                className="absolute -top-px left-0 h-px w-full origin-left scale-x-0 bg-gradient-to-r from-accent to-magenta transition-transform duration-500 group-hover:scale-x-100"
              />
              <span className="font-mono text-base font-medium tabular-nums text-gray-dim transition-colors duration-500 group-hover:text-accent-soft md:col-span-1 md:text-lg">
                {service.index}
              </span>
              <h3 className="display text-2xl text-ivory transition-transform duration-500 group-hover:translate-x-1.5 md:col-span-3 md:text-[1.85rem]">
                {service.title}
              </h3>
              <div className="max-w-2xl md:col-span-6">
                <p className="text-pretty text-sm leading-relaxed text-gray md:text-base">
                  {service.description}
                </p>
                <p className="mt-2 text-pretty text-sm leading-relaxed text-gray">
                  <span className="label mr-3 text-accent-soft">
                    {serviceDetailLabels.bestFor}
                  </span>
                  <span>{service.bestFor}</span>
                </p>
              </div>
              <ContactTypeLink
                formType={service.formType}
                className="group/cta link-underline inline-flex min-h-11 items-center gap-2 self-start text-sm font-medium text-ivory hover:text-accent-soft md:col-span-2 md:justify-end md:text-right [--underline-rest:transparent]"
              >
                <span>{service.cta}</span>
                <span aria-hidden className="transition-transform duration-300 group-hover/cta:translate-x-1">
                  →
                </span>
              </ContactTypeLink>
              <details className="group/details details-unfold md:col-span-10 md:col-start-3">
                <summary className="inline-flex min-h-11 cursor-pointer list-none items-center gap-2 py-2 text-sm text-gray transition-colors hover:text-ivory [&::-webkit-details-marker]:hidden">
                  <span>{serviceDetailLabels.outputs}</span>
                  <span
                    aria-hidden
                    className="text-accent-soft transition-transform duration-300 group-open/details:rotate-45 motion-reduce:transition-none"
                  >
                    +
                  </span>
                </summary>
                <div className="pb-2 pt-2">
                  <ul className="flex flex-wrap gap-2">
                    {service.outputs.map((output) => (
                      <li
                        key={output}
                        className="border-l border-line px-3 py-1.5 font-mono text-[0.65rem] uppercase tracking-[0.1em] text-gray"
                      >
                        {output}
                      </li>
                    ))}
                  </ul>
                </div>
              </details>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
