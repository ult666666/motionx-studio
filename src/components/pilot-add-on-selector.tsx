"use client";

import { useState } from "react";
import Link from "next/link";
import {
  campaignAddOnOffer,
  getPilotAddOnInquiryHref,
  getPilotAddOnTotal,
  pilotAddOnCopy,
  pilotBaseOffers,
} from "@/content/pilot";
import { cn } from "@/lib/utilities";

/**
 * A small client island for the only conditional pilot scope. The package
 * slate remains server-rendered; JavaScript is limited to the explicit base
 * selection that produces the paired contact URL.
 */
export function PilotAddOnSelector() {
  const [selectedBaseId, setSelectedBaseId] = useState<string | null>(null);
  const selectedBase =
    pilotBaseOffers.find((offer) => offer.id === selectedBaseId) ?? null;

  if (!campaignAddOnOffer) return null;

  return (
    <div className="grid gap-8 border-t border-line px-5 py-8 md:grid-cols-12 md:items-start md:gap-8 md:px-7">
      <div className="md:col-span-4">
        <p className="label text-accent-soft">{pilotAddOnCopy.selectorLabel}</p>
        <p
          id="pilot-add-on-base-hint"
          className="mt-3 max-w-md text-pretty text-sm leading-relaxed text-gray"
        >
          {pilotAddOnCopy.selectorHint}
        </p>
      </div>

      <fieldset
        aria-describedby="pilot-add-on-base-hint"
        className="min-w-0 md:col-span-5 md:self-stretch md:border-l md:border-line/70 md:pl-6"
      >
        <legend className="label mb-3 text-gray-dim">
          {pilotAddOnCopy.selectorLegend}
        </legend>
        {/* Edit-suite index chrome: hairline-separated rows, an arming left
            tick, and a tonal selected state — same language as the Selected
            Work cue sheet. */}
        <div className="grid gap-px border border-line bg-line">
          {pilotBaseOffers.map((offer) => {
            const selected = offer.id === selectedBaseId;

            return (
              <label
                key={offer.id}
                className={cn(
                  "group relative flex min-h-11 cursor-pointer items-center gap-3 px-3.5 py-2.5 transition-colors duration-200",
                  selected
                    ? "bg-blueblack text-ivory"
                    : "bg-ink text-gray hover:bg-soft hover:text-ivory focus-within:bg-soft focus-within:text-ivory",
                )}
              >
                <span
                  aria-hidden
                  className={cn(
                    "absolute inset-y-0 left-0 w-0.5 origin-bottom bg-accent transition-transform duration-300 motion-reduce:transition-none",
                    selected
                      ? "scale-y-100"
                      : "scale-y-0 group-hover:scale-y-[0.28] group-focus-within:scale-y-100",
                  )}
                />
                <input
                  type="radio"
                  name="pilot-addon-base"
                  value={offer.id}
                  checked={selected}
                  onChange={() => setSelectedBaseId(offer.id)}
                  className="h-4 w-4 shrink-0 accent-accent"
                />
                <span className="min-w-0 flex-1 text-sm font-medium">
                  {offer.title}
                </span>
                <span className="shrink-0 font-mono text-xs tabular-nums text-ivory">
                  {offer.pilotPrice}
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>

      <div className="md:col-span-3 md:self-stretch md:border-l md:border-line/70 md:pl-3">
        <div aria-live="polite" className="min-h-10">
          {selectedBase && (
            <div
              key={selectedBase.id}
              className="settle-enter border-l-2 border-accent bg-accent/[0.04] px-4 py-3"
            >
              <p className="text-xs leading-relaxed text-gray">
                <span className="label mr-2 text-gray-dim">
                  {pilotAddOnCopy.selectedLabel}
                </span>
                <span className="text-ivory">{selectedBase.title}</span>
              </p>
              <p className="mt-3 flex items-baseline justify-between gap-3 border-t border-line pt-3">
                <span className="label text-gray-dim">
                  {pilotAddOnCopy.combinedTotalLabel}
                </span>
                <span className="font-mono text-sm tabular-nums text-ivory">
                  {getPilotAddOnTotal(selectedBase, campaignAddOnOffer)}
                </span>
              </p>
            </div>
          )}
        </div>

        {selectedBase ? (
          <Link
            href={getPilotAddOnInquiryHref(selectedBase)}
            prefetch={false}
            className="group mt-3 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-full cta-primary px-3.5 py-3 text-center text-sm font-medium transition-colors duration-300"
          >
            {pilotAddOnCopy.readyCta}
            <span
              aria-hidden
              className="transition-transform duration-300 group-hover:translate-x-0.5"
            >
              →
            </span>
          </Link>
        ) : (
          <button
            type="button"
            disabled
            className="mt-3 inline-flex min-h-11 w-full cursor-not-allowed items-center justify-center rounded-full border border-line px-3.5 py-3 text-center text-sm text-gray-dim opacity-70"
          >
            {pilotAddOnCopy.disabledCta}
          </button>
        )}

      </div>
    </div>
  );
}
