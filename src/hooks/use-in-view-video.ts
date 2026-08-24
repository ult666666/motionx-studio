"use client";

import { useEffect, useRef, useState, type RefObject } from "react";

type Options = {
  /** Fraction of the video that must be visible before it plays. */
  threshold?: number;
  /** If false, the hook will not auto-play. */
  enabled?: boolean;
};

/**
 * Visibility-driven video playback:
 *  - plays (muted) when sufficiently in view,
 *  - pauses when scrolled away or when the browser tab is hidden,
 *  - never fights a manual pause issued by the user.
 *
 * The element ref is owned by the caller rather than this hook, because the
 * same element is also driven by `useMediaArming`, and the arming effect has to
 * run before this one in the commit where both change. Effects fire in
 * declaration order, so the caller declares arming first and passes the shared
 * ref to both.
 */
export function useInViewVideo<T extends HTMLVideoElement>(
  ref: RefObject<T | null>,
  options: Options = {},
): {
  isPlaying: boolean;
  setManualPaused: (v: boolean) => void;
} {
  const { threshold = 0.45, enabled = true } = options;
  const [isPlaying, setIsPlaying] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const manualPaused = useRef(false);

  // Track in-view via IntersectionObserver
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const io = new IntersectionObserver(
      ([entry]) =>
        setIsInView(
          entry.isIntersecting && entry.intersectionRatio >= threshold,
        ),
      { threshold },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [threshold, ref]);

  // React to in-view + tab visibility + enabled flag
  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    el.addEventListener("play", onPlay);
    el.addEventListener("pause", onPause);

    const sync = () => {
      const tabHidden = typeof document !== "undefined" && document.hidden;
      const shouldPlay =
        enabled && isInView && !manualPaused.current && !tabHidden;

      if (shouldPlay) {
        const p = el.play();
        if (p && typeof p.catch === "function") {
          // Autoplay can be blocked — fail gracefully, poster stays visible.
          p.catch(() => setIsPlaying(false));
        }
      } else {
        el.pause();
      }
    };

    sync();
    document.addEventListener("visibilitychange", sync);
    return () => {
      el.removeEventListener("play", onPlay);
      el.removeEventListener("pause", onPause);
      document.removeEventListener("visibilitychange", sync);
    };
  }, [isInView, enabled, ref]);

  const setManualPaused = (v: boolean) => {
    manualPaused.current = v;
    const el = ref.current;
    if (!el) return;
    if (v) {
      el.pause();
    } else if (isInView) {
      void el.play().catch(() => {});
    }
  };

  return { isPlaying, setManualPaused };
}
