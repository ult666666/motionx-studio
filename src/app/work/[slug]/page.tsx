import type { Metadata } from "next";
import { notFound } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  getAdjacentProjects,
  getProject,
  getProjectCapabilityLabel,
  getProjectConceptLabel,
  getProjectInquiryHref,
  projectToSystemBridge,
  projectNavigationCopy,
  projects,
  type Project,
} from "@/content/projects";
import { site } from "@/content/site";
import { VideoPlayer } from "@/components/video-player";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";

/** Only the centrally defined concept studies are valid work routes. */
export const dynamicParams = false;

export function generateStaticParams() {
  return projects.map((p) => ({ slug: p.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const project = getProject(slug);
  if (!project) return {};
  const pageTitle = `${project.title} Concept Study`;
  const socialTitle = `${pageTitle} — ${site.name}`;
  // Dedicated 1200x630 landscape share card per project (the raw poster is the
  // portrait 9:16 video frame — wrong shape for a summary_large_image card).
  const ogImage = {
    url: `/og/${project.slug}.jpg`,
    width: 1200,
    height: 630,
    alt: `${project.title} — ${site.name}`,
  };
  return {
    title: pageTitle,
    description: project.metaDescription,
    alternates: { canonical: `/work/${project.slug}` },
    openGraph: {
      type: "article",
      siteName: site.name,
      url: `/work/${project.slug}`,
      title: socialTitle,
      description: project.metaDescription,
      images: [ogImage],
    },
    twitter: {
      card: "summary_large_image",
      title: socialTitle,
      description: project.metaDescription,
      images: [ogImage.url],
    },
  };
}

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const project = getProject(slug);
  if (!project) notFound();

  const { next } = getAdjacentProjects(slug);
  const projectJsonLd = {
    "@context": "https://schema.org",
    "@type": "CreativeWork",
    name: `${project.title} concept project`,
    description: `${project.summary} ${project.disclosure}`,
    creator: { "@type": "Organization", name: site.name, url: site.url },
    publisher: { "@type": "Organization", name: site.name, url: site.url },
    url: `${site.url}/work/${project.slug}`,
    image: `${site.url}/og/${project.slug}.jpg`,
    genre: project.category,
    keywords: project.tags,
    inLanguage: "en",
    isPartOf: { "@type": "WebSite", name: site.name, url: site.url },
  };

  return (
    <>
      <Navigation />
      <main id="content" className="bg-ink pt-28 md:pt-36">
        <article
          className="shell pb-24 md:pb-32"
          // Scopes every accent consumer on the case route — registration
          // corners, arming ticks, drawn underlines, and the player's
          // media-control hover warm — to this film's colour (registered
          // --project-accent falls back to electric blue outside any scope).
          style={{ ["--project-accent" as string]: project.accent }}
        >
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{
              __html: JSON.stringify(projectJsonLd).replace(/</g, "\\u003c"),
            }}
          />
          <Link
            href={`/#work-${project.slug}`}
            prefetch={false}
            className="link-underline label inline-flex min-h-11 items-center gap-2 py-2 text-gray hover:text-ivory [--underline-from:var(--project-accent)] [--underline-to:var(--project-accent)] [--underline-rest:transparent]"
          >
            <span aria-hidden>←</span> Back to work
          </Link>

          <div
            className={
              "mt-8 " +
              (project.orientation === "portrait"
                ? "lg:grid lg:grid-cols-12 lg:items-start lg:gap-12"
                : "")
            }
          >
            <header
              className={
                "max-w-4xl " +
                (project.orientation === "portrait"
                  ? "lg:col-span-6 lg:pt-8"
                  : "")
              }
            >
              <div className="flex items-start gap-3">
                {/* Registers on the label's first line even when the long
                    capability label wraps on narrow viewports. */}
                <span
                  aria-hidden
                  className="mt-2 h-px w-8 shrink-0 bg-[var(--project-accent)]"
                />
                <span
                  className="label leading-relaxed"
                  style={{ color: project.accent }}
                >
                  {getProjectCapabilityLabel(project.category)}
                </span>
              </div>
              <h1 className="display mt-5 text-[clamp(2.75rem,8vw,6rem)] text-ivory">
                {project.title}
              </h1>
              <p className="mt-6 max-w-2xl text-pretty text-lg leading-relaxed text-gray">
                {project.summary}
              </p>
              {project.concept && (
                <div className="mt-7 max-w-2xl border-l-2 border-accent/60 bg-accent/[0.04] py-4 pl-5 pr-5 sm:pr-6">
                  <p className="label mb-2.5 text-accent-soft">Concept disclosure</p>
                  <p className="text-sm leading-relaxed text-gray">
                    {project.disclosure}
                  </p>
                </div>
              )}
            </header>

            <div
              id="case-film"
              className={
                "relative mt-12 scroll-mt-28 p-2 sm:p-3 " +
                (project.orientation === "portrait"
                  ? "mx-auto max-w-md lg:col-span-5 lg:col-start-8 lg:mt-0 lg:w-full"
                  : "")
              }
            >
              {/* Registration corners — the film's accent leads top-left,
                  the other three stay hairline-quiet. Decorative viewfinder
                  chrome only; the player keeps its own stage. */}
              <span
                aria-hidden
                className="pointer-events-none absolute left-0 top-0 h-2 w-2 border-l border-t border-[var(--project-accent)]"
              />
              <span
                aria-hidden
                className="pointer-events-none absolute right-0 top-0 h-2 w-2 border-r border-t border-line"
              />
              <span
                aria-hidden
                className="pointer-events-none absolute bottom-0 left-0 h-2 w-2 border-b border-l border-line"
              />
              <span
                aria-hidden
                className="pointer-events-none absolute bottom-0 right-0 h-2 w-2 border-b border-r border-line"
              />
              <VideoPlayer
                label={project.title}
                src={project.video}
                mobileSrc={project.videoMobile}
                poster={project.poster}
                captionsSrc={project.captions}
                width={project.width}
                height={project.height}
                preload="metadata"
              />
            </div>
          </div>

          {project.artFrame && (
            <figure className="relative mt-8 border border-line bg-panel p-2 sm:p-3">
              {/* Registration corners on the still-frame stage — same
                  edit-suite chrome as the homepage edit bay. */}
              <span
                aria-hidden
                className="pointer-events-none absolute -left-px -top-px h-2 w-2 border-l border-t border-[var(--project-accent)]"
              />
              <span
                aria-hidden
                className="pointer-events-none absolute -right-px -top-px h-2 w-2 border-r border-t border-line"
              />
              <span
                aria-hidden
                className="pointer-events-none absolute -bottom-px -left-px h-2 w-2 border-b border-l border-line"
              />
              <span
                aria-hidden
                className="pointer-events-none absolute -bottom-px -right-px h-2 w-2 border-b border-r border-line"
              />
              <picture>
                <source
                  media="(max-width: 639px)"
                  srcSet={project.artFrame.mobileSrc}
                />
                {/* The responsive files are pre-optimized, contract-checked
                    WebP derivatives; picture selects them without an image
                    optimizer request or a client component. */}
                <img
                  src={project.artFrame.src}
                  width={project.artFrame.width}
                  height={project.artFrame.height}
                  alt={project.artFrame.alt}
                  loading="lazy"
                  decoding="async"
                  className="h-auto w-full"
                />
              </picture>
              <figcaption className="flex flex-col gap-2 border-t border-line px-2 pb-1 pt-4 sm:flex-row sm:items-baseline sm:justify-between sm:px-3">
                <span className="label shrink-0 text-accent-soft">
                  {project.artFrame.label}
                </span>
                <span className="max-w-2xl text-pretty text-xs leading-relaxed text-gray sm:text-right">
                  {project.artFrame.caption}
                </span>
              </figcaption>
            </figure>
          )}

          <div
            id="case-breakdown"
            className="mt-14 grid scroll-mt-28 gap-10 border-t border-line pt-12 md:grid-cols-12 md:gap-12"
          >
            <aside
              className="hidden md:col-span-4 md:block"
              aria-label={projectNavigationCopy.caseIndexLabel}
            >
              <div className="sticky top-28">
                <p className="label mb-4 text-accent-soft">
                  {projectNavigationCopy.caseIndexLabel}
                </p>
                <CaseIndexContent project={project} />
              </div>
            </aside>

            <section
              aria-labelledby="case-breakdown-heading"
              className="space-y-8 md:col-span-8"
            >
              <div
                className="border-l-2 bg-soft/45 px-5 py-5 sm:px-6"
                style={{ borderColor: project.accent }}
              >
                <h2 id="case-breakdown-heading" className="label text-accent-soft">
                  {projectNavigationCopy.whatThisShows}
                </h2>
                <p className="mt-3 max-w-2xl text-pretty text-lg leading-relaxed text-ivory">
                  {project.demonstrates}
                </p>
              </div>

              <details className="group details-unfold border-y border-line md:hidden">
                <summary className="flex min-h-12 cursor-pointer list-none items-center gap-3 py-3 text-left [&::-webkit-details-marker]:hidden">
                  <span className="label text-accent-soft">
                    {projectNavigationCopy.caseIndexLabel}
                  </span>
                  <span className="ml-auto text-xs text-gray">
                    {project.duration} ·{" "}
                    {project.orientation === "portrait" ? "9:16" : "16:9"}
                  </span>
                  <span
                    aria-hidden
                    className="text-lg text-accent-soft transition-transform duration-300 group-open:rotate-45 motion-reduce:transition-none"
                  >
                    +
                  </span>
                </summary>
                <div className="border-t border-line pb-6 pt-5">
                  <CaseIndexContent project={project} />
                </div>
              </details>

              <Section title="Creative objective" body={project.objective} />
              <Section title="Visual approach" body={project.approach} />
              <details className="group details-unfold border-y border-line">
                <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-4 py-3 text-left [&::-webkit-details-marker]:hidden">
                  <span className="label text-accent-soft">
                    {projectNavigationCopy.conceptNotesLabel}
                  </span>
                  <span
                    aria-hidden
                    className="text-lg text-accent-soft transition-transform duration-300 group-open:rotate-45 motion-reduce:transition-none"
                  >
                    +
                  </span>
                </summary>
                <div className="grid gap-5 border-t border-line py-5 sm:grid-cols-2">
                  <ConceptNotes project={project} />
                </div>
              </details>
              <div className="border-t border-line pt-6">
                <p className="label mb-4">{projectNavigationCopy.outputScope}</p>
                <ul className="grid gap-2.5 sm:grid-cols-2 sm:gap-x-10">
                  {project.deliverables.map((d) => (
                    <li key={d} className="flex items-start gap-3 text-sm text-gray">
                      <span
                        aria-hidden
                        className="mt-2 h-px w-3 shrink-0"
                        style={{ backgroundColor: project.accent }}
                      />
                      <span>{d}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          </div>

          <section
            id="case-inquiry"
            aria-labelledby="project-inquiry-heading"
            className="mt-16 grid scroll-mt-28 gap-7 border-y border-line py-10 md:grid-cols-12 md:items-end md:gap-12 md:py-12"
          >
            <div className="md:col-span-7">
              <p className="label text-accent-soft">{project.inquiry.eyebrow}</p>
              <h2
                id="project-inquiry-heading"
                className="display mt-4 max-w-2xl text-balance text-[clamp(2rem,4vw,3.5rem)] text-ivory"
              >
                {project.inquiry.heading}
              </h2>
            </div>
            <div className="md:col-span-5">
              <p className="max-w-md text-pretty text-base leading-relaxed text-gray">
                {project.inquiry.body}
              </p>
              <div className="mt-6 flex flex-col items-start gap-2 sm:flex-row sm:flex-wrap sm:items-center sm:gap-4">
                <Link
                  href={getProjectInquiryHref(project)}
                  prefetch={false}
                  className="group inline-flex min-h-12 items-center gap-2 rounded-full cta-primary px-6 py-3 text-sm font-medium transition-colors duration-300"
                >
                  {project.inquiry.cta}
                  <span
                    aria-hidden
                    className="transition-transform duration-300 group-hover:translate-x-0.5"
                  >
                    →
                  </span>
                </Link>
                <Link
                  href={projectToSystemBridge.href}
                  className="link-underline inline-flex min-h-11 items-center py-2 text-sm text-gray hover:text-ivory [--underline-rest:transparent]"
                >
                  {projectToSystemBridge.label}
                </Link>
              </div>
            </div>
          </section>

          <nav aria-label="Project navigation" className="mt-16 border-t border-line pt-8">
            <Link
              href={`/#work-${project.slug}`}
              prefetch={false}
              className="group inline-flex min-h-12 flex-col justify-center py-2 text-left"
            >
              <span className="label block">{projectNavigationCopy.collectionEyebrow}</span>
              <span className="link-underline mt-1 self-start text-base text-ivory group-hover:text-accent-soft group-hover:[background-size:100%_1px,100%_1px] group-focus-visible:[background-size:100%_1px,100%_1px] [--underline-rest:transparent]">
                {projectNavigationCopy.collectionLabel}
              </span>
            </Link>

            {next && (
              <Link
                href={`/work/${next.slug}`}
                className="group mt-6 grid overflow-hidden border border-line bg-panel transition-colors hover:border-white/25 md:grid-cols-12"
                style={{ ["--next-accent" as string]: next.accent }}
              >
                <span className="relative min-h-40 overflow-hidden bg-soft md:col-span-5 md:min-h-56">
                  <Image
                    src={next.poster}
                    alt=""
                    fill
                    sizes="(max-width: 767px) 100vw, 42vw"
                    unoptimized
                    className="absolute inset-0 h-full w-full object-cover opacity-80 transition-[transform,opacity] duration-500 group-hover:scale-[1.025] group-hover:opacity-100 motion-reduce:transition-none"
                  />
                  {/* Static letterbox bars — the poster reads as a film strip. */}
                  <span aria-hidden className="absolute inset-x-0 top-0 h-[6%] bg-ink" />
                  <span aria-hidden className="absolute inset-x-0 bottom-0 h-[6%] bg-ink" />
                  {/* One-shot hover playhead along the bottom bar. */}
                  <span
                    aria-hidden
                    className="absolute bottom-0 left-0 h-px w-full origin-left scale-x-0 bg-[var(--next-accent)] transition-transform duration-700 ease-cinematic group-hover:scale-x-100 group-focus-within:scale-x-100 motion-reduce:transition-none"
                  />
                  <span
                    aria-hidden
                    className="absolute inset-0 bg-gradient-to-t from-ink/75 via-transparent to-transparent"
                  />
                  {/* Provenance stays above the letterbox bar. */}
                  <span className="concept-mark absolute bottom-4 left-4 z-10">
                    {getProjectConceptLabel(next.category)}
                  </span>
                </span>
                <span className="flex min-h-52 flex-col justify-between gap-5 p-5 sm:p-7 md:col-span-7 md:min-h-56">
                  <span>
                    <span className="label text-[var(--next-accent)]">
                      {projectNavigationCopy.nextEyebrow} · {next.index}
                    </span>
                    <span className="display mt-4 block text-[clamp(2.25rem,5vw,4.5rem)] text-ivory">
                      {next.title}
                    </span>
                    <span className="label mt-4 block leading-relaxed text-gray-dim">
                      {getProjectCapabilityLabel(next.category)} · {next.duration}
                    </span>
                  </span>
                  <span className="link-underline inline-flex min-h-11 items-center gap-2 self-start py-2 text-sm font-medium text-ivory group-hover:[background-size:100%_1px,100%_1px] group-focus-within:[background-size:100%_1px,100%_1px] [--underline-from:var(--next-accent)] [--underline-to:var(--next-accent)]">
                    {projectNavigationCopy.nextCta}
                    <span
                      aria-hidden
                      className="transition-transform duration-300 group-hover:translate-x-1 motion-reduce:transition-none"
                    >
                      →
                    </span>
                  </span>
                </span>
              </Link>
            )}
          </nav>
        </article>
      </main>
      <Footer />
    </>
  );
}

function Section({ title, body }: { title: string; body: string }) {
  return (
    <div className="border-t border-line pt-6">
      <h2 className="label mb-3">{title}</h2>
      <p className="max-w-xl text-pretty text-base leading-relaxed text-gray">
        {body}
      </p>
    </div>
  );
}

function CaseIndexContent({ project }: { project: Project }) {
  const format =
    project.orientation === "portrait" ? "Vertical · 9:16" : "Horizontal · 16:9";
  const links = [
    ["#case-film", projectNavigationCopy.filmAnchor],
    ["#case-breakdown", projectNavigationCopy.breakdownAnchor],
    ["#case-inquiry", projectNavigationCopy.inquiryAnchor],
  ] as const;

  return (
    <>
      {/* Hairline metadata grid — the edit-bay index language: gap-px cells
          over the line colour, mono label above each value. */}
      <dl className="grid grid-cols-2 gap-px border border-line bg-line sm:grid-cols-3 md:grid-cols-1">
        <div className="bg-ink px-4 py-3">
          <dt className="label mb-2">Runtime</dt>
          <dd className="text-sm tabular-nums text-ivory">{project.duration}</dd>
        </div>
        <div className="bg-ink px-4 py-3">
          <dt className="label mb-2">Format</dt>
          <dd className="text-sm tabular-nums text-ivory">{format}</dd>
        </div>
        <div className="col-span-2 bg-ink px-4 py-3 sm:col-span-1">
          <dt className="label mb-2">Type</dt>
          <dd className="text-sm text-ivory">
            {getProjectConceptLabel(project.category)}
          </dd>
        </div>
      </dl>
      <nav
        aria-label={projectNavigationCopy.onThisPageLabel}
        className="mt-7"
      >
        <p className="label mb-3 text-gray-dim">
          {projectNavigationCopy.onThisPageLabel}
        </p>
        <ul className="border-t border-line">
          {links.map(([href, label]) => (
            <li key={href}>
              <a
                href={href}
                className="group relative flex min-h-11 items-center justify-between gap-3 border-b border-line py-2 pl-3 text-sm text-gray transition-colors hover:text-ivory"
              >
                {/* Quiet arming cue — a short accent tick draws in from the
                    left rail on hover/focus, echoing the edit-bay index. */}
                <span
                  aria-hidden
                  className="absolute left-0 top-1/2 h-3.5 w-0.5 -translate-y-1/2 scale-y-0 bg-[var(--project-accent)] transition-transform duration-300 group-hover:scale-y-100 group-focus-visible:scale-y-100 motion-reduce:transition-none"
                />
                <span>{label}</span>
                <span
                  aria-hidden
                  className="transition-transform group-hover:translate-y-0.5 motion-reduce:transition-none"
                >
                  ↓
                </span>
              </a>
            </li>
          ))}
        </ul>
      </nav>
    </>
  );
}

function ConceptNotes({ project }: { project: Project }) {
  return project.conceptStudyNotes.map((note) => (
    <div key={note.title} className="border-l border-line pl-4">
      <h2 className="text-sm font-medium text-ivory">{note.title}</h2>
      <p className="mt-2 text-pretty text-sm leading-relaxed text-gray">
        {note.body}
      </p>
    </div>
  ));
}
