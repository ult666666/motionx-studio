import { hasSocial, site } from "@/content/site";
import { ContactForm } from "./contact-form";
import { CopyEmailButton } from "./copy-email-button";
import { MaskedLines } from "./reveal";

/**
 * Server-rendered contact shell: pitch, supporting details, and FAQ are static
 * HTML available before hydration (including the #contact-heading focus target
 * used by every "Start a Project" CTA). The form itself is the ContactForm
 * client island; the rail's copy control is its own tiny island.
 */
export function ContactSection() {
  const email = site.contact.email;

  return (
    <section id="contact" className="relative scroll-mt-20 overflow-clip border-t border-line bg-ink py-16 md:py-24">
      {/* electric accent wash */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-60"
        style={{
          background:
            "radial-gradient(45% 50% at 80% 0%, #6d7cff1f, transparent 70%), radial-gradient(40% 45% at 10% 100%, #d65bd614, transparent 70%)",
        }}
      />
      <div className="shell relative grid gap-x-12 gap-y-10 md:grid-cols-12">
        {/* Pitch leads the mobile source order and anchors the left desktop rail. */}
        <div className="md:col-span-5 md:col-start-1 md:row-start-1">
          <p className="label mb-5 text-accent-soft">(07) — Contact</p>
          {/* id + tabIndex stay on the h2 itself — the focus handoff and the
              no-JS "build your launch" contract both bind to this node. The
              masked entrance wraps real server-rendered text. */}
          <h2
            id="contact-heading"
            tabIndex={-1}
            className="display text-balance text-[clamp(2.25rem,5.5vw,4.25rem)] text-ivory"
          >
            <MaskedLines lines={[site.closing.headline]} />
          </h2>
          <p className="mt-6 max-w-md text-pretty text-base leading-relaxed text-gray">
            {site.closing.body}
          </p>
        </div>

        {/* Form comes before supporting details on mobile; it remains the right desktop rail. */}
        <div className="md:col-span-6 md:col-start-7 md:row-span-2 md:row-start-1">
          {/* Edit-suite brief header — a SIBLING before the form (never a
              wrapper: browser-verify derives the form column from the form's
              parent). Desktop-only so the mobile landing keeps #contact-name
              inside the first viewport. */}
          <div
            aria-hidden
            className="mb-4 hidden items-center justify-between border-b border-line pb-3 md:flex"
          >
            <span className="label border-l border-accent/60 pl-3 text-gray">
              {site.contactBrief.label}
            </span>
            <span className="label text-gray-dim">{site.availability}</span>
          </div>
          <ContactForm email={email} />
        </div>

        {/* Supporting details follow the form on mobile and complete the left desktop rail. */}
        <div className="space-y-5 border-t border-line pt-7 md:col-span-5 md:col-start-1 md:row-start-2">
          <div className="grid grid-cols-2 gap-5">
            <div>
              <p className="label mb-2">Email</p>
              <div className="flex flex-col items-start gap-2">
                {/* Selectable plain-text address */}
                <span className="select-all break-all text-sm text-ivory">{email}</span>
                <CopyEmailButton email={email} />
              </div>
            </div>

            <div>
              <p className="label mb-2">Availability</p>
              <p className="flex items-center gap-2 text-sm text-ivory">
                <span
                  aria-hidden
                  className="inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-accent shadow-[0_0_6px_rgba(109,124,255,0.8)]"
                />
                {site.availability}
              </p>
            </div>
          </div>

          <div>
            <p className="label mb-2">{site.contactNext.label}</p>
            <p className="text-sm leading-relaxed text-gray">
              {site.contactNext.summary}
            </p>
          </div>

          {hasSocial && (
            <div>
              <p className="label mb-2">Social</p>
              <span className="flex flex-wrap gap-4 text-sm">
                {site.social.map((s) => (
                  <a
                    key={s.label}
                    href={s.href}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex min-h-11 items-center text-ivory transition-colors hover:text-accent-soft"
                  >
                    {s.label}
                  </a>
                ))}
              </span>
            </div>
          )}

          <div className="border-t border-line pt-6">
            <p className="label mb-4 text-accent-soft">FAQ</p>
            <div className="border-t border-line">
              {site.faq.map((item) => (
                <details key={item.question} className="group details-unfold border-b border-line">
                  <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-4 py-3 text-left text-sm font-medium text-ivory [&::-webkit-details-marker]:hidden">
                    <span>{item.question}</span>
                    <span
                      aria-hidden
                      className="shrink-0 text-base text-accent-soft transition-transform duration-300 group-open:rotate-45 motion-reduce:transition-none"
                    >
                      +
                    </span>
                  </summary>
                  <p className="pb-4 pr-8 text-pretty text-sm leading-relaxed text-gray">
                    {item.answer}
                  </p>
                </details>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
