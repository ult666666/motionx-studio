"use client";

import { useEffect, useRef, useState } from "react";
import { copyToClipboard } from "@/lib/utilities";

/**
 * Self-contained copy-to-clipboard island for the contact section's
 * server-rendered supporting rail. Owns its confirmation state and polite
 * live region, so the announcement works without the form island.
 */
export function CopyEmailButton({ email }: { email: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const timerRef = useRef<number | null>(null);

  useEffect(
    () => () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
      }
    },
    [],
  );

  const copy = async () => {
    const ok = await copyToClipboard(email);
    setState(ok ? "copied" : "failed");
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
    }
    timerRef.current = window.setTimeout(() => {
      setState("idle");
      timerRef.current = null;
    }, 2200);
  };

  return (
    <>
      <button
        type="button"
        onClick={copy}
        className="link-underline inline-flex min-h-11 items-center px-1 py-2 text-xs text-gray transition-colors hover:text-ivory"
      >
        {state === "copied" ? "Copied ✓" : "Copy"}
      </button>
      <span role="status" aria-live="polite" className="text-xs text-accent-soft">
        {state === "copied" && "Email copied."}
        {state === "failed" && "Couldn’t copy — select the address manually."}
      </span>
    </>
  );
}
