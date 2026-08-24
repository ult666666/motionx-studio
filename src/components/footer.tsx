import Link from "next/link";
import { hasSocial, site } from "@/content/site";
import { mailto } from "@/lib/utilities";
import { Logotype } from "./logotype";

export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="relative border-t border-line bg-soft">
      {/* End-slate rule: the site's drawn-hairline signature closes the page.
          Static fallback is fully drawn. */}
      <div aria-hidden className="shell pt-10 md:pt-12">
        {/* The default draw range (cover 45%) is unreachable for a footer
            flush with the document end — the page runs out of scroll and the
            rule froze at ~9% drawn. Entry-only range completes while the
            footer scrolls into view; the static fallback stays fully drawn. */}
        <div
          className="rule-draw-x h-px w-full bg-gradient-to-r from-accent via-accent-soft/60 to-magenta/70"
          style={{ ["--draw-range" as string]: "entry 0% cover 30%" }}
        />
      </div>
      <div className="shell pb-10 pt-8 md:pb-12">
        <div className="grid gap-8 md:grid-cols-12 md:items-start">
          <div className="md:col-span-4">
            <Link
              href="/#top"
              prefetch={false}
              aria-label={`${site.name} — home`}
              className="text-3xl"
            >
              <Logotype />
            </Link>
            <p className="mt-4 text-sm text-gray">
              {site.footerTagline}
            </p>
            <p className="mt-2 flex items-center gap-2 text-xs text-gray-dim">
              <span
                aria-hidden
                className="inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-accent shadow-[0_0_6px_rgba(109,124,255,0.8)]"
              />
              {site.founder} · {site.availability}
            </p>
          </div>

          <div className="md:col-span-3">
            <p className="label mb-3">Connect</p>
            <a
              href={mailto(site.contact.email)}
              className="link-underline inline-flex min-h-11 items-center break-all px-1 text-sm text-gray transition-colors hover:text-ivory [--underline-rest:transparent]"
            >
              {site.contact.email}
            </a>
            {hasSocial && (
              <ul className="mt-2 flex flex-wrap gap-4 text-sm">
                {site.social.map((s) => (
                  <li key={s.label}>
                    <a
                      href={s.href}
                      target="_blank"
                      rel="noreferrer"
                      className="text-gray transition-colors hover:text-ivory"
                    >
                      {s.label}
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Pulled to the right edge so the three blocks span the shell
              instead of leaving a dead band across the footer's middle. */}
          <nav aria-label="Footer" className="md:col-span-4 md:col-start-9">
            <p className="label mb-3 md:text-right">Navigate</p>
            <ul className="flex flex-wrap gap-x-6 gap-y-3 text-sm md:justify-end">
              {site.footerNav.map((n) => (
                <li key={n.href}>
                  <Link
                    href={n.href}
                    prefetch={false}
                    className="link-underline -mx-1 inline-flex min-h-11 items-center px-1 text-gray transition-colors hover:text-ivory [--underline-rest:transparent]"
                  >
                    {n.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        {/* Closing metadata rail — mono, square-edged, edit-suite. */}
        <div className="mt-9 flex flex-col gap-4 border-t border-line pt-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="label text-gray">
            © {year} · {site.name}
          </p>
          <a
            href="#content"
            className="group label inline-flex min-h-11 items-center gap-2 self-start border-l border-accent/50 pl-3 text-gray transition-colors hover:text-ivory sm:self-auto"
          >
            Back to top
            <span aria-hidden className="transition-transform duration-300 group-hover:-translate-y-0.5 motion-reduce:transition-none">↑</span>
          </a>
        </div>
      </div>
    </footer>
  );
}
