import type { Metadata } from "next";
import Link from "next/link";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { interfaceCopy } from "@/content/interface";

export const metadata: Metadata = {
  title: "Page not found",
  // A 404 must not inherit the layout's indexable/shareable metadata: without
  // these explicit overrides the built _not-found.html shipped the homepage
  // canonical, og:url/image, Twitter card, AND a conflicting "index, follow"
  // robots directive alongside Next's automatic noindex.
  robots: { index: false, follow: false },
  alternates: null,
  openGraph: null,
  twitter: null,
};

/** Branded 404 — same shell as every route (nav, #content main for the skip
 *  link, footer), pointing lost visitors back at the work. */
export default function NotFound() {
  const copy = interfaceCopy.notFound;
  return (
    <>
      <Navigation />
      <main id="content" className="grain relative flex min-h-[72vh] items-center bg-ink pt-28 md:pt-32">
        {/* Registration ticks — the edit-suite framing idiom, zero animation:
            the accent leads top-left, the other three stay hairline-quiet. */}
        <div aria-hidden className="pointer-events-none absolute inset-x-6 inset-y-24 md:inset-x-10">
          <span className="absolute left-0 top-0 h-6 w-6 border-l border-t border-accent-soft/60" />
          <span className="absolute right-0 top-0 h-6 w-6 border-r border-t border-line" />
          <span className="absolute bottom-0 left-0 h-6 w-6 border-b border-l border-line" />
          <span className="absolute bottom-0 right-0 h-6 w-6 border-b border-r border-line" />
        </div>
        <div className="shell relative pb-24">
          <p className="label mb-5 text-accent-soft">{copy.eyebrow}</p>
          <h1 className="display text-[clamp(2.5rem,7vw,5rem)] text-ivory">
            {copy.heading}
          </h1>
          <p className="mt-6 max-w-md text-pretty text-base leading-relaxed text-gray">
            {copy.body}
          </p>
          {/* Mono telemetry strip — decorative edit-suite status, no claims. */}
          <div aria-hidden className="mt-8 flex max-w-md items-center gap-3 border-t border-line pt-4">
            <span className="h-px w-5 bg-accent-soft" />
            <p className="label text-gray-dim">{copy.statusLine}</p>
          </div>
          <div className="mt-9 flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:gap-4">
            <Link
              href="/"
              className="group inline-flex w-full items-center justify-center gap-2 rounded-full cta-primary px-7 py-3.5 text-sm font-medium transition-colors duration-300 sm:w-auto"
            >
              {copy.primary}
              <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">→</span>
            </Link>
            <Link
              href="/#work"
              prefetch={false}
              className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-white/20 px-7 py-3.5 text-sm font-medium text-ivory transition-colors duration-300 hover:border-white/50 hover:bg-white/5 sm:w-auto"
            >
              {copy.secondary}
            </Link>
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
