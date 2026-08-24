import type { Metadata } from "next";
import Link from "next/link";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { PilotAddOnSelector } from "@/components/pilot-add-on-selector";
import { Reveal } from "@/components/reveal";
import { site } from "@/content/site";
import {
  campaignAddOnOffer,
  getPilotIncludedScope,
  getPilotInquiryHref,
  pilotAddOnCopy,
  pilotBaseOffers,
  pilotMeta,
  type PilotAddOnOffer,
  type PilotBaseOffer,
} from "@/content/pilot";
import { cn } from "@/lib/utilities";

export const metadata: Metadata = {
  title: "Pilot Launch — Introductory Offers",
  description:
    "Introductory pilot pricing from MOTIONX — product films, motion-first websites, and complete launch systems. From first frame to final click.",
  alternates: { canonical: "/pilot" },
  openGraph: {
    type: "website",
    siteName: site.name,
    title: `${site.name} — Pilot Launch Offers`,
    description:
      "Introductory pricing on product films, motion-first websites, and connected launch systems.",
    url: "/pilot",
    // Page-level `openGraph`/`twitter` REPLACE the layout's whole object
    // (shallow merge), so image, siteName and type must be restated or /pilot
    // silently loses them.
    images: [
      {
        url: "/og/og-image.jpg",
        width: 1200,
        height: 630,
        alt: `${site.name} — ${site.tagline}`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: `${site.name} — Pilot Launch Offers`,
    description:
      "Introductory pricing on product films, motion-first websites, and connected launch systems.",
    images: ["/og/og-image.jpg"],
  },
};

export default function PilotPage() {
  const packages = pilotBaseOffers;
  const addOn = campaignAddOnOffer;

  return (
    <>
      <Navigation />
      <main id="content" className="bg-ink pt-28 md:pt-32">
        {/* Header */}
        <section className="border-b border-line pb-16 md:pb-20">
          <div className="shell grid gap-10 md:grid-cols-12 md:items-end md:gap-8">
            <div className="md:col-span-7">
              <Reveal as="p" className="label mb-5 text-accent-soft">
                {pilotMeta.eyebrow}
              </Reveal>
              <Reveal as="div">
                <h1 className="display max-w-4xl text-balance text-[clamp(2.4rem,6vw,4.75rem)] text-ivory">
                  {pilotMeta.heading}
                </h1>
              </Reveal>
            </div>

            <div className="md:col-span-4 md:col-start-9">
              <Reveal
                as="p"
                className="max-w-xl text-pretty text-base leading-relaxed text-gray md:text-lg"
              >
                {pilotMeta.intro}
              </Reveal>
              <Reveal
                as="div"
                className="mt-7 flex flex-col items-start gap-4 sm:flex-row sm:items-center md:flex-col md:items-start"
              >
                <Link
                  href="#pilot-packages"
                  className="group inline-flex min-h-11 items-center gap-2 rounded-full cta-primary px-7 py-3 text-sm font-medium transition-colors duration-300"
                >
                  {pilotMeta.primaryCta}
                  <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">→</span>
                </Link>
                <Link
                  href="/#work"
                  prefetch={false}
                  className="group inline-flex min-h-11 items-center gap-2 border-b border-line text-sm text-gray transition-colors duration-300 hover:border-accent-soft hover:text-ivory"
                >
                  {site.cta.secondary}
                  <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">→</span>
                </Link>
                <span className="label text-gray-dim">{site.availability}</span>
              </Reveal>
            </div>
          </div>
        </section>

        {/* Packages */}
        <section
          id="pilot-packages"
          aria-labelledby="pilot-packages-heading"
          className="scroll-mt-20 border-b border-line py-16 md:py-24"
        >
          <div className="shell">
            <div className="mb-12 grid gap-6 md:grid-cols-12 md:items-end md:gap-8">
              <div className="md:col-span-7">
                <Reveal as="p" className="label mb-4 text-accent-soft">
                  {pilotMeta.packagesLabel}
                </Reveal>
                <Reveal as="div">
                  <h2
                    id="pilot-packages-heading"
                    className="display max-w-3xl text-balance text-[clamp(2rem,4.6vw,3.5rem)] text-ivory"
                  >
                    {pilotMeta.packagesHeading}
                  </h2>
                </Reveal>
              </div>
              <Reveal
                as="p"
                className="max-w-md text-pretty text-sm leading-relaxed text-gray md:col-span-4 md:col-start-9"
              >
                {pilotMeta.packagesIntro}
              </Reveal>
            </div>

            <div className="border-b border-line">
              {/* Drawn slate head rule — accent hint settling into the standard
                  hairline; static fallback renders it fully drawn. */}
              <div
                aria-hidden
                className="rule-draw-x h-px w-full bg-gradient-to-r from-accent/70 via-line to-line"
              />
              {packages.map((offer, i) => (
                <Reveal key={offer.id}>
                  <OfferRow
                    offer={offer}
                    index={i}
                    isLast={i === packages.length - 1}
                  />
                </Reveal>
              ))}
            </div>

            {/* Add-on band */}
            {addOn && (
              <Reveal as="div" className="mt-8 border-y border-line bg-soft/60">
                <div className="grid gap-7 px-5 py-8 md:grid-cols-12 md:items-start md:gap-8 md:px-7">
                  <div className="md:col-span-1">
                    <span className="label text-gray-dim">
                      {pilotAddOnCopy.marker}
                    </span>
                    <span
                      aria-hidden
                      className="mt-3 hidden h-px w-6 bg-line md:block"
                    />
                  </div>
                  <div className="md:col-span-7">
                    {addOn.label && (
                      <p className="label mb-3 border-l border-accent/70 pl-3 text-accent-soft">
                        {addOn.label}
                      </p>
                    )}
                    <h3 className="display text-2xl text-ivory md:text-3xl">
                      {addOn.title}
                    </h3>
                    {addOn.audience && (
                      <p className="mt-3 text-pretty text-sm font-medium leading-snug text-ivory">
                        {addOn.audience}
                      </p>
                    )}
                    <p className="mt-2 max-w-xl text-pretty text-sm leading-relaxed text-gray md:text-base">
                      {addOn.deliverable}
                    </p>
                  </div>
                  <div className="border-t border-line/70 pt-6 md:col-span-2 md:col-start-9 md:self-stretch md:border-t-0 md:border-l md:pl-6 md:pt-0">
                    <PriceBlock offer={addOn} compact />
                  </div>
                </div>
                <PilotAddOnSelector />
              </Reveal>
            )}
          </div>
        </section>

        {/* Pilot details */}
        <section aria-labelledby="pilot-details-heading" className="border-b border-line py-12 md:py-16">
          <div className="shell">
            <Reveal as="div" className="mb-8 max-w-2xl">
              <p className="label mb-4 text-accent-soft">Pilot scope</p>
              <h2 id="pilot-details-heading" className="display text-balance text-[clamp(1.8rem,4vw,3rem)] text-ivory">
                Clear scope before production starts.
              </h2>
            </Reveal>
            <div className="grid border-y border-line md:grid-cols-2">
              {pilotMeta.detailGroups.map((group) => (
                <Reveal
                  key={group.title}
                  as="section"
                  className="border-b border-line py-7 last:border-b-0 md:border-b-0 md:border-r md:px-7 md:last:border-r-0 md:first:pl-0 md:last:pr-0"
                >
                  <h3 className="display text-2xl text-ivory">{group.title}</h3>
                  <ul className="mt-5 space-y-3 border-t border-line/70 pt-5">
                    {group.items.map((item) => (
                      <li key={item} className="flex items-start gap-3 text-sm leading-relaxed text-gray">
                        <span aria-hidden className="mt-2 h-px w-3 shrink-0 bg-gray-dim/60" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* Pilot terms + disclaimer */}
        <section className="py-12 md:py-16">
          <div className="shell grid gap-10 md:grid-cols-12 md:gap-12">
            <div className="md:col-span-4">
              <Reveal as="p" className="label mb-5 text-accent-soft">
                {pilotMeta.termsLabel}
              </Reveal>
              <Reveal as="h2" className="display text-balance text-[clamp(1.8rem,4vw,3rem)] text-ivory">
                {pilotMeta.termsHeading}
              </Reveal>
            </div>
            <div className="md:col-span-8">
              <ol className="border-y border-line">
                {pilotMeta.termsLines.map((line, index) => (
                  <Reveal as="li" key={line} className="grid grid-cols-[2.5rem_1fr] border-b border-line py-5 last:border-b-0">
                    <span className="label pt-1.5 text-accent-soft">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span className="border-l border-line/70 pl-5 text-pretty text-base leading-relaxed text-ivory md:text-lg">{line}</span>
                  </Reveal>
                ))}
              </ol>
              <Reveal as="p" className="mt-8 max-w-xl border-t border-line pt-6 text-sm leading-relaxed text-gray-dim">
                {pilotMeta.disclaimer}
              </Reveal>

              <Reveal as="div" className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
                <Link
                  href="/#contact"
                  prefetch={false}
                  className="group inline-flex items-center gap-2 rounded-full cta-primary px-7 py-3.5 text-sm font-medium transition-colors duration-300"
                >
                  {site.cta.primary}
                  <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">→</span>
                </Link>
                <a
                  href={`mailto:${site.contact.email}`}
                  className="text-sm text-gray underline-offset-4 transition-colors hover:text-ivory hover:underline"
                >
                  {site.contact.email}
                </a>
              </Reveal>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}

function OfferRow({
  offer,
  index,
  isLast,
}: {
  offer: PilotBaseOffer;
  index: number;
  isLast: boolean;
}) {
  const included = getPilotIncludedScope(offer);

  return (
    <article
      id={offer.id}
      className={cn(
        "group relative grid scroll-mt-24 gap-7 px-5 py-8 transition-colors duration-300 md:grid-cols-12 md:items-start md:gap-8 md:px-7 md:py-10",
        !isLast && "border-b border-line",
        offer.featured
          ? "signature-band border-l-2 border-l-accent bg-blueblack/55 md:py-12"
          : "hover:bg-white/[0.03] focus-within:bg-white/[0.03]",
      )}
    >
      {/* Armed-row hairline — deliberately dimmer than the Signature accent
          edge, and absent on the featured row (it owns the accent). */}
      {!offer.featured && (
        <span
          aria-hidden
          className="absolute inset-y-0 left-0 w-px origin-top scale-y-0 bg-accent/45 transition-transform duration-300 group-hover:scale-y-100 group-focus-within:scale-y-100 motion-reduce:transition-none"
        />
      )}
      <div className="md:col-span-1">
        <span className="label text-gray-dim transition-colors duration-300 group-hover:text-accent-soft group-focus-within:text-accent-soft">
          P-{String(index + 1).padStart(2, "0")}
        </span>
        {/* Cue-sheet index tick — arms with the row. */}
        <span
          aria-hidden
          className={cn(
            "mt-3 hidden h-px w-6 md:block",
            offer.featured
              ? "bg-accent/60"
              : "bg-line transition-colors duration-300 group-hover:bg-accent/60 group-focus-within:bg-accent/60",
          )}
        />
      </div>

      <div className="md:col-span-4">
        {offer.label && (
          <p className="label mb-3 border-l border-accent/70 pl-3 text-accent-soft">
            {offer.label}
          </p>
        )}
        <h3
          className={cn(
            "display text-ivory",
            offer.featured ? "text-3xl md:text-[2.35rem]" : "text-2xl md:text-3xl",
          )}
        >
          {offer.title}
        </h3>
        {offer.audience && (
          <p className="mt-3 max-w-sm text-pretty text-sm font-medium leading-snug text-ivory">
            {offer.audience}
          </p>
        )}
      </div>

      <div className="border-t border-line/70 pt-6 md:col-span-3 md:self-stretch md:border-t-0 md:border-l md:pl-6 md:pt-0">
        <p className="label mb-4 text-gray-dim">Included scope</p>
        <ul className="space-y-2.5">
          {included.map((item) => (
            <li key={item} className="flex items-start gap-2.5 text-sm leading-relaxed text-gray">
              {/* Edit-suite scope tick — rests dim, arms with the row; the
                  featured row keeps its accent resting state. */}
              <span
                aria-hidden
                className={cn(
                  "mt-2 h-px w-3 shrink-0",
                  offer.featured
                    ? "bg-accent-soft"
                    : "bg-gray-dim/50 transition-colors duration-300 group-hover:bg-accent-soft group-focus-within:bg-accent-soft",
                )}
              />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="border-t border-line/70 pt-6 md:col-span-2 md:self-stretch md:border-t-0 md:border-l md:pl-6 md:pt-0">
        <PriceBlock offer={offer} />
      </div>

      <div className="flex md:col-span-2 md:justify-end">
        <OfferLink offer={offer} label="Start this project" />
      </div>
    </article>
  );
}

function PriceBlock({
  offer,
  compact = false,
}: {
  offer: Pick<PilotBaseOffer | PilotAddOnOffer, "pilotPrice" | "originalPrice">;
  compact?: boolean;
}) {
  return (
    <div>
      <p className="label mb-2 text-gray-dim">Pilot rate</p>
      <span
        className={cn(
          "display leading-none tabular-nums tracking-tight text-ivory",
          compact ? "text-3xl" : "text-4xl",
        )}
      >
        <span className="sr-only">Pilot price </span>
        {offer.pilotPrice}
      </span>
      <p className="mt-2 text-xs text-gray-dim">
        Original <s className="decoration-gray-dim/60"><span className="sr-only">price </span>{offer.originalPrice}</s>
      </p>
    </div>
  );
}

function OfferLink({ offer, label }: { offer: PilotBaseOffer; label: string }) {
  return (
    <Link
      href={getPilotInquiryHref(offer)}
      prefetch={false}
      className="group/offer link-underline inline-flex min-h-11 items-center gap-3 text-sm font-medium text-ivory hover:text-accent-soft [--underline-rest:var(--color-line)]"
    >
      {label}
      <span aria-hidden className="transition-transform duration-300 group-hover/offer:translate-x-1">→</span>
    </Link>
  );
}
