import { processIntro, processSteps } from "@/content/services";
import { MaskedLines, Reveal } from "./reveal";

/**
 * Server-rendered process. A CSS view timeline draws the edit-suite playhead
 * where supported; the full line is the resilient fallback and reduced-motion
 * state, so content never waits on hydration.
 */
export function Process() {
  return (
    <section id="process" className="relative scroll-mt-20 border-t border-line bg-ink py-16 md:py-24">
      <div className="shell">
        <div className="mb-9 flex flex-col gap-4 md:mb-12 md:flex-row md:items-end md:justify-between">
          <div className="max-w-3xl">
            <Reveal as="p" className="label mb-5 text-accent-soft">
              {processIntro.label}
            </Reveal>
            <h2 className="display text-balance text-[clamp(2rem,5vw,3.75rem)] text-ivory">
              <MaskedLines lines={[processIntro.heading]} />
            </h2>
          </div>
          <p className="max-w-sm text-pretty text-sm leading-relaxed text-gray md:text-right">
            {processIntro.body}
          </p>
        </div>

        <div className="process-sequence relative">
          <div className="absolute left-0 top-2 hidden h-[calc(100%-1rem)] w-px bg-line md:block">
            <div className="process-progress absolute left-0 top-0 h-full w-px origin-top bg-gradient-to-b from-accent to-magenta" />
          </div>

          {/* Mobile keeps a static rail so the sequence reads as one timeline
              at every breakpoint; desktop swaps it for the drawn playhead. */}
          <ol className="border-l border-line pl-5 md:border-l-0 md:pl-12">
            {processSteps.map((step) => (
              <li
                key={step.index}
                className="relative grid gap-3 border-b border-line py-5 last:border-b-0 md:grid-cols-12 md:items-center md:gap-6 md:py-6"
              >
                {/* Marker arms (line → accent) as the drawn playhead passes;
                    the static base stays armed for every fallback path. */}
                <span
                  aria-hidden
                  className="process-marker absolute -left-12 top-1/2 hidden h-2.5 w-2.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent ring-4 ring-ink md:block"
                />
                <span className="label text-accent-soft md:col-span-1">{step.index}</span>
                <h3 className="display text-2xl text-ivory md:col-span-3 md:text-3xl">
                  {step.title}
                </h3>
                <p className="max-w-xl text-pretty text-sm leading-relaxed text-gray md:col-span-5 md:text-base">
                  {step.description}
                </p>
                {/* Label sits above the value, not inline before it. Inline,
                    the value wrapped back to the paragraph's left edge and ran
                    underneath the label — "DIRECTION One approved visual /
                    system" — which read as a typesetting mistake. Stacking also
                    matches the label-above-value pairs in the Studio section. */}
                <p className="border-l border-accent/35 pl-4 text-sm leading-relaxed text-ivory md:col-span-3">
                  <span className="label mb-1.5 block text-accent-soft">
                    {step.checkpoint.label}
                  </span>
                  <span>{step.checkpoint.body}</span>
                </p>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </section>
  );
}
