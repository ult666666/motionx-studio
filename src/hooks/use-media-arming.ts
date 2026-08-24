"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

/**
 * Gate on whether a media element may spend bytes yet.
 *
 * The poster-only policy used to rest entirely on `preload="none"`. That is a
 * hint, not a guarantee: CI's WebKit fetches the mp4 anyway, so reduced-motion
 * and Save-Data visitors — the exact people who opted out — were downloading
 * video while the element still reported `paused` and `currentTime === 0`. The
 * fix is structural rather than advisory: a caller renders no `<source>`
 * children at all until `armed` is true, and an element with no candidates has
 * nothing any engine can fetch.
 *
 * Arming happens when the autoplay policy allows it, or when the visitor
 * explicitly asks for playback through `requestPlay`.
 */
export function useMediaArming<T extends HTMLMediaElement>(
  ref: RefObject<T | null>,
  autoplayAllowed: boolean,
): { armed: boolean; requestPlay: () => void } {
  const [armed, setArmed] = useState(false);
  const pendingPlay = useRef(false);

  // The policy is reactive — a visitor can switch reduced motion or data saver
  // mid-session — so arming follows it rather than sampling once on mount.
  useEffect(() => {
    if (autoplayAllowed) setArmed(true);
  }, [autoplayAllowed]);

  useEffect(() => {
    const el = ref.current;
    if (!armed || !el) return;

    // Inserting a <source> into a media element that is still NETWORK_EMPTY
    // re-runs resource selection on its own, but an element that already
    // completed selection with no candidates will not notice. `load()` makes
    // that deterministic across engines. Guarded on `currentSrc` so it can
    // never restart media that is already resolved or playing.
    if (!el.currentSrc) el.load();

    if (pendingPlay.current) {
      pendingPlay.current = false;
      // Safe without a user gesture because players start muted; the promise
      // rejection path is handled so a blocked attempt just leaves the poster.
      void el.play().catch(() => {});
    }
  }, [armed, ref]);

  const requestPlay = useCallback(() => {
    const el = ref.current;
    if (armed) {
      void el?.play().catch(() => {});
      return;
    }
    // Cold start: arm first, then play once the sources have been committed.
    pendingPlay.current = true;
    setArmed(true);
  }, [armed, ref]);

  return { armed, requestPlay };
}
