"use client";

import { useEffect } from "react";
import Link from "next/link";
import { Logotype } from "@/components/logotype";
import { brandName } from "@/content/chrome";
import { interfaceCopy } from "@/content/interface";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Keep the exception available to platform logging without exposing its
    // internals or digest in the visitor-facing interface.
    console.error(error);
  }, [error]);

  const copy = interfaceCopy.error;

  return (
    <>
      <header className="fixed inset-x-0 top-0 z-50 border-b border-line bg-ink/90 backdrop-blur-xl">
        <div className="shell flex h-16 items-center md:h-20">
          <Link
            href="/"
            className="text-xl md:text-2xl"
            aria-label={`${brandName} — home`}
          >
            <Logotype />
          </Link>
        </div>
      </header>
      <main id="content" className="grain relative flex min-h-svh items-center overflow-hidden bg-ink pt-24">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 opacity-70"
          style={{
            background:
              "linear-gradient(115deg, transparent 35%, #6d7cff12 50%, transparent 65%)",
          }}
        />
        {/* Registration ticks — the edit-suite framing idiom, zero animation:
            the accent leads top-left, the other three stay hairline-quiet. */}
        <div aria-hidden className="pointer-events-none absolute inset-x-6 inset-y-24 md:inset-x-10">
          <span className="absolute left-0 top-0 h-6 w-6 border-l border-t border-accent-soft/60" />
          <span className="absolute right-0 top-0 h-6 w-6 border-r border-t border-line" />
          <span className="absolute bottom-0 left-0 h-6 w-6 border-b border-l border-line" />
          <span className="absolute bottom-0 right-0 h-6 w-6 border-b border-r border-line" />
        </div>
        <div className="shell relative py-20">
          <p className="label mb-5 text-accent-soft">{copy.eyebrow}</p>
          <h1 className="display max-w-4xl text-balance text-[clamp(2.6rem,7vw,5.25rem)] text-ivory">
            {copy.heading}
          </h1>
          <p className="mt-6 max-w-lg text-pretty text-base leading-relaxed text-gray">
            {copy.body}
          </p>
          {/* Mono telemetry strip — decorative edit-suite status, no claims. */}
          <div aria-hidden className="mt-8 flex max-w-lg items-center gap-3 border-t border-line pt-4">
            <span className="h-px w-5 bg-accent-soft" />
            <p className="label text-gray-dim">{copy.statusLine}</p>
          </div>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={reset}
              className="inline-flex min-h-12 items-center justify-center rounded-full cta-primary px-7 py-3.5 text-sm font-medium transition-colors duration-300"
            >
              {copy.retry}
            </button>
            <Link
              href="/"
              className="inline-flex min-h-12 items-center justify-center rounded-full border border-white/20 px-7 py-3.5 text-sm font-medium text-ivory transition-colors duration-300 hover:border-white/50 hover:bg-white/5"
            >
              {copy.home}
            </Link>
            <Link
              href="/#contact"
              prefetch={false}
              className="inline-flex min-h-12 items-center justify-center px-4 py-3.5 text-sm font-medium text-gray transition-colors hover:text-ivory"
            >
              {copy.contact}
            </Link>
          </div>
        </div>
      </main>
    </>
  );
}
