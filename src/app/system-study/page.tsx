import type { Metadata } from "next";
import Link from "next/link";
import { AuraPrototype } from "@/components/aura-prototype";
import { Footer } from "@/components/footer";
import { Navigation } from "@/components/navigation";
import { MaskedLines } from "@/components/reveal";
import {
  ChromeObject,
  StageCampaign,
  StageFilm,
  StageWebsite,
} from "@/components/system-study-visuals";
import { site } from "@/content/site";
import { systemStudy, type SystemStudyStage } from "@/content/system-study";

const title = `${systemStudy.name} System Study — ${site.name}`;

export const metadata: Metadata = {
  title: `${systemStudy.name} System Study`,
  description: systemStudy.metaDescription,
  alternates: { canonical: "/system-study" },
  openGraph: {
    type: "article",
    siteName: site.name,
    url: "/system-study",
    title,
    description: systemStudy.metaDescription,
    images: [
      {
        url: "/og/system-study.jpg",
        width: 1200,
        height: 630,
        alt: `${site.name} — ${systemStudy.name} System Study concept`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description: systemStudy.metaDescription,
    images: ["/og/system-study.jpg"],
  },
};

export default function SystemStudyPage() {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    name: `${systemStudy.name} integrated launch system concept study`,
    description: `${systemStudy.intro} ${systemStudy.disclosure}`,
    creator: { "@type": "Organization", name: site.name, url: site.url },
    publisher: { "@type": "Organization", name: site.name, url: site.url },
    url: `${site.url}/system-study`,
    image: `${site.url}/og/system-study.jpg`,
    genre: "Integrated launch system concept study",
    inLanguage: "en",
    isPartOf: { "@type": "WebSite", name: site.name, url: site.url },
  };

  return (
    <>
      <Navigation />
      <main id="content" className="bg-ink pt-28 md:pt-36">
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
          }}
        />

        <header className="shell relative overflow-clip pb-16 md:pb-24">
          <Link
            href="/#launch-system"
            prefetch={false}
            className="label inline-flex min-h-11 items-center gap-2 text-gray transition-colors hover:text-ivory"
          >
            <span aria-hidden>←</span> Back to the homepage study
          </Link>
          <div className="mt-8 grid gap-10 md:grid-cols-12 md:items-center md:gap-12">
            <div className="relative z-10 md:col-span-7">
              <div className="mb-5 flex flex-wrap items-center gap-3">
                <p className="label text-accent-soft">{systemStudy.eyebrow}</p>
                <span className="concept-mark">
                  Concept
                </span>
              </div>
              <h1 className="display max-w-5xl text-balance text-[clamp(2.6rem,7vw,5.75rem)] text-ivory">
                {systemStudy.title}
              </h1>
              <p className="mt-7 max-w-2xl text-pretty text-base leading-relaxed text-gray md:text-lg">
                {systemStudy.intro}
              </p>
              <div className="mt-7 max-w-2xl border-l border-accent/60 bg-accent/[0.025] py-1 pl-4">
                <p className="label mb-2 text-accent-soft">Concept disclosure</p>
                <p className="text-sm leading-relaxed text-gray">
                  {systemStudy.disclosure}
                </p>
              </div>
            </div>

            {/* The self-owned chrome object enters in the first viewport so the
                route opens on visual proof, not another text-only template. */}
            <div className="relative md:col-span-5" aria-hidden="true">
              <div className="relative mx-auto aspect-[5/4] w-full max-w-xl overflow-hidden border border-line bg-blueblack md:aspect-[4/5]">
                <div
                  className="absolute inset-0"
                  style={{
                    background:
                      "radial-gradient(55% 55% at 55% 45%, #171b3a, transparent 70%), linear-gradient(135deg, transparent 45%, #6d7cff0d 50%, transparent 55%)",
                  }}
                />
                {/* Viewfinder registration — the accent leads top-left, the
                    other three corners stay hairline-quiet. */}
                <span className="absolute left-0 top-0 h-8 w-8 border-l border-t border-accent-soft/70" />
                <span className="absolute right-0 top-0 h-8 w-8 border-r border-t border-line" />
                <span className="absolute bottom-0 left-0 h-8 w-8 border-b border-l border-line" />
                <span className="absolute bottom-0 right-0 h-8 w-8 border-b border-r border-line" />
                <span className="absolute inset-x-0 top-1/2 h-px bg-white/[0.05]" />
                <span className="absolute inset-y-0 left-1/2 w-px bg-white/[0.05]" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="scale-75 sm:scale-100 md:scale-110">
                    <ChromeObject size={2.2} />
                  </div>
                </div>
                <p className="absolute left-4 top-4 font-mono text-[0.58rem] tracking-[0.2em] text-accent-soft">
                  AURA · FORM 01
                </p>
                <p className="absolute bottom-4 right-4 font-mono text-[0.58rem] tracking-[0.2em] text-gray-dim">
                  FILM → WEB → CAMPAIGN
                </p>
              </div>
            </div>
          </div>
        </header>

        <section
          aria-labelledby="prototype-heading"
          className="border-y border-line bg-blueblack py-16 md:py-24"
        >
          <div className="shell">
            <div className="mb-6 flex items-center gap-4 md:mb-8">
              <p className="label text-accent-soft">{systemStudy.prototype.label}</p>
              <span aria-hidden className="h-px flex-1 bg-line" />
            </div>
            <AuraPrototype />
          </div>
        </section>

        <section
          id="system-breakdown"
          aria-labelledby="breakdown-heading"
          className="scroll-mt-20 py-16 md:py-24"
        >
          <div className="shell">
            <div className="mb-12 max-w-3xl md:mb-16">
              <div className="mb-5 flex items-center gap-4">
                <p className="label text-accent-soft">System breakdown</p>
                <span aria-hidden className="h-px flex-1 bg-line" />
              </div>
              <h2
                id="breakdown-heading"
                className="display text-balance text-[clamp(2.1rem,5vw,4rem)] text-ivory"
              >
                One direction. Three launch surfaces.
              </h2>
            </div>

            <div className="relative">
              {/* Breakdown spine — same drawn-rail grammar as the process
                  playhead; the static track is the fallback state. */}
              <div
                aria-hidden
                className="absolute -left-6 top-2 hidden h-[calc(100%-1rem)] w-px bg-line lg:block"
              >
                <div className="rule-draw-y h-full w-px bg-gradient-to-b from-accent via-accent-soft/70 to-magenta/80" />
              </div>
              {/* Cue-sheet rhythm — one hairline opens the sequence and one
                  closes each stage, so text and visuals share a drawn frame. */}
              <ol className="border-t border-line">
                {systemStudy.stages.map((stage, index) => (
                  <StudyStage key={stage.index} stage={stage} reverse={index % 2 === 1} />
                ))}
              </ol>
            </div>
          </div>
        </section>

        <section className="border-y border-line bg-soft py-16 md:py-20">
          <div className="shell">
            <div className="max-w-4xl">
              <div className="mb-5 flex items-center gap-4">
                <p className="label text-accent-soft">{systemStudy.method.label}</p>
                <span aria-hidden className="h-px flex-1 bg-line" />
              </div>
              <h2 className="display text-balance text-[clamp(2rem,4.6vw,3.75rem)] text-ivory">
                {systemStudy.method.heading}
              </h2>
              <p className="mt-6 max-w-2xl text-pretty text-base leading-relaxed text-gray">
                {systemStudy.method.body}
              </p>
            </div>
          </div>
        </section>

        <section className="relative overflow-clip py-20 md:py-28">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 opacity-80"
            style={{
              background:
                "radial-gradient(45% 65% at 70% 30%, #6d7cff1c, transparent 70%), radial-gradient(35% 50% at 20% 90%, #d65bd612, transparent 70%)",
            }}
          />
          <div className="shell relative grid gap-8 md:grid-cols-12 md:items-end">
            <div className="md:col-span-8">
              <div className="mb-5 flex items-center gap-4">
                <p className="label text-accent-soft">{systemStudy.cta.eyebrow}</p>
                <span aria-hidden className="h-px flex-1 bg-line" />
              </div>
              <h2 className="display max-w-4xl text-balance text-[clamp(2.2rem,5.2vw,4.25rem)] text-ivory">
                {systemStudy.cta.heading}
              </h2>
              <p className="mt-6 max-w-2xl text-pretty text-base leading-relaxed text-gray">
                {systemStudy.cta.body}
              </p>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row md:col-span-4 md:flex-col md:items-stretch">
              <Link
                href={`/?type=${encodeURIComponent(systemStudy.cta.formType)}#contact`}
                prefetch={false}
                className="group inline-flex min-h-12 items-center justify-center gap-2 rounded-full cta-primary px-7 py-3.5 text-sm font-medium transition-colors duration-300"
              >
                {systemStudy.cta.primary}
                <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">
                  →
                </span>
              </Link>
              <Link
                href={systemStudy.cta.secondaryHref}
                className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/20 px-7 py-3.5 text-sm font-medium text-ivory transition-colors duration-300 hover:border-white/50 hover:bg-white/5"
              >
                {systemStudy.cta.secondary}
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}

function StudyStage({
  stage,
  reverse,
}: {
  stage: SystemStudyStage;
  reverse: boolean;
}) {
  return (
    <li className="grid items-center gap-7 border-b border-line py-10 md:grid-cols-12 md:gap-12 md:py-16">
      <div
        className={
          "md:col-span-6 " +
          (reverse ? "md:order-2 md:col-start-7" : "md:order-1")
        }
        aria-hidden="true"
      >
        {stage.visual === "film" && <StageFilm />}
        {stage.visual === "website" && (
          <div className="mx-auto max-w-sm">
            <StageWebsite />
          </div>
        )}
        {stage.visual === "campaign" && (
          <div className="mx-auto max-w-md">
            <StageCampaign />
          </div>
        )}
      </div>
      <div
        className={
          "md:col-span-5 " +
          (reverse ? "md:order-1" : "md:order-2 md:col-start-8")
        }
      >
        <div className="mb-5 flex items-center gap-3">
          <p className="label text-accent-soft">{stage.index}</p>
          <span aria-hidden className="h-px flex-1 bg-line" />
        </div>
        <h3 className="display text-balance text-[clamp(1.9rem,4vw,3.25rem)] text-ivory">
          <MaskedLines lines={[stage.title]} />
        </h3>
        <p className="mt-4 max-w-xl text-pretty text-base leading-relaxed text-gray">
          {stage.description}
        </p>
        <ul className="mt-6 flex flex-wrap gap-x-5 gap-y-2 border-t border-line pt-4">
          {stage.carries.map((item) => (
            <li key={item} className="flex items-center gap-2 text-xs leading-relaxed text-ivory sm:text-sm">
              <span aria-hidden className="h-px w-3 shrink-0 bg-accent-soft" />
              {item}
            </li>
          ))}
        </ul>
      </div>
    </li>
  );
}
