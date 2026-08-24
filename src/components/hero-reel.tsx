"use client";

import { useEffect, useRef, useState } from "react";
import { heroReelMedia, MOBILE_MEDIA_CONDITION } from "@/content/media";
import { useInViewVideo } from "@/hooks/use-in-view-video";
import { useMediaArming } from "@/hooks/use-media-arming";
import { useVideoAutoplayAllowed } from "@/hooks/use-video-autoplay-policy";

/** Real elapsed loop time as MM:SS — telemetry, never fabricated precision. */
function formatReelTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

/**
 * Client island for the hero's background teaser. The rest of the hero renders
 * on the server; this fragment owns the only pieces that need the client —
 * the video element (visibility/policy-driven playback) and its play/pause
 * control. Both blocks are absolutely positioned against the hero section, so
 * rendering them as a fragment preserves the layout and stacking order.
 */
export function HeroReel({ label }: { label: string }) {
  // Starts poster-first on the server, then follows reduced-motion and
  // Save-Data changes for the full lifetime of the page.
  const canPlay = useVideoAutoplayAllowed();
  const [hasStarted, setHasStarted] = useState(false);
  const ref = useRef<HTMLVideoElement>(null);
  const playControlRef = useRef<HTMLButtonElement>(null);
  // Whole seconds only: state updates at most once per second, while the
  // ring's --reel-progress is written imperatively so the island never
  // re-renders at timeupdate frequency.
  const [reelSeconds, setReelSeconds] = useState<number | null>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let lastSecond = -1;
    const onTimeUpdate = () => {
      const progress = el.duration > 0 ? el.currentTime / el.duration : 0;
      playControlRef.current?.style.setProperty(
        "--reel-progress",
        progress.toFixed(4),
      );
      const second = Math.floor(el.currentTime);
      if (second !== lastSecond) {
        lastSecond = second;
        setReelSeconds(second);
      }
    };
    el.addEventListener("timeupdate", onTimeUpdate);
    return () => el.removeEventListener("timeupdate", onTimeUpdate);
  }, []);

  // Declared before playback on purpose: both effects fire in the commit where
  // `armed` flips, and the sources must be loaded before anything plays.
  const { armed, requestPlay } = useMediaArming(ref, canPlay);
  const { isPlaying, setManualPaused } = useInViewVideo(ref, {
    threshold: 0.15,
    enabled: canPlay && armed,
  });

  const togglePlay = () => {
    const el = ref.current;
    if (!el) return;
    if (el.paused) {
      setManualPaused(false);
      // Arms the element first when the visitor opted out of autoplay, so an
      // explicit press still works from a cold, source-less start.
      requestPlay();
    } else {
      setManualPaused(true);
    }
  };

  return (
    <>
      {/* Background teaser — a short, claim-light cut from the Agentic Trading
          concept film. The complete narrated film lives in Selected Work.
          No audio track by design. */}
      <div className="grain absolute inset-0 z-0">
        {/* Two nested transform wrappers, deliberately separate: CSS
            animations REPLACE each other when two drive `transform` on one
            element. The outer node carries the scroll-driven exit drift, the
            inner one the 18s push-in; picture + video share the inner
            geometry so the poster→reel crossfade stays seamless. The gradient
            washes and mobile copy band stay direct children of the un-moved
            container — their protection geometry is load-bearing and must
            remain viewport-true. */}
        <div className="hero-exit-drift absolute inset-0">
          <div className="hero-media-pushin absolute inset-0">
            <picture className="absolute inset-0">
              <source
                media={MOBILE_MEDIA_CONDITION}
                srcSet={heroReelMedia.mobilePoster}
              />
              <img
                src={heroReelMedia.poster}
                width={heroReelMedia.width}
                height={heroReelMedia.height}
                alt=""
                fetchPriority="high"
                className="h-full w-full object-cover"
                style={{ objectPosition: "center 42%" }}
              />
            </picture>
            <video
              ref={ref}
              className={`relative h-full w-full object-cover transition-opacity duration-500 motion-reduce:transition-none ${
                hasStarted ? "opacity-100" : "opacity-0"
              }`}
              style={{ objectPosition: "center 42%" }}
              width={heroReelMedia.width}
              height={heroReelMedia.height}
              muted
              loop
              playsInline
              preload="none"
              aria-label={`${label} silent concept-film teaser`}
              onPlaying={() => setHasStarted(true)}
            >
              {/* Ordered ladder: the purpose-built vertical mobile reframe
                  first, then the widescreen teaser as the desktop fallback.

                  Withheld until `armed`. `preload="none"` alone is a hint that
                  some engines ignore, and an element with no candidates cannot
                  leak bytes for a reduced-motion or Save-Data visitor. */}
              {armed && (
                <>
                  <source
                    src={heroReelMedia.mobileSrc}
                    type="video/mp4"
                    media={MOBILE_MEDIA_CONDITION}
                  />
                  <source src={heroReelMedia.src} type="video/mp4" />
                </>
              )}
            </video>
          </div>
        </div>
        {/* Cinematic overlays — protect text contrast, keep video legible. */}
        <div className="absolute inset-0 bg-gradient-to-t from-ink via-ink/45 to-ink/15" />
        <div className="absolute inset-0 bg-gradient-to-r from-ink/80 via-ink/15 to-transparent" />
        <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-ink/70 to-transparent" />
        {/* Mobile-only copy band. The left-to-right wash above is tuned for the
            desktop composition, where copy occupies the left third; on the 9:16
            reframe the copy spans the full width and the mascot's bright limb
            sits directly behind it, measuring ~1.5:1 against the eyebrow. This
            deepens only the copy region so the frame elsewhere stays intact. */}
        <div className="absolute inset-x-0 top-[18%] h-[54%] bg-gradient-to-b from-transparent via-ink/72 to-transparent md:hidden" />
        {/* Exit grade: authored static state is fully transparent — the fade
            to 0.55 exists only inside the double-gated scroll animation. */}
        <div
          aria-hidden
          className="hero-exit-dim pointer-events-none absolute inset-0 bg-ink opacity-0"
        />
      </div>

      {/* Transport cluster: real elapsed loop time + play/pause. The reel has
          no audio, so no mute toggle. The timecode is decorative telemetry
          derived from currentTime (whole seconds, MM:SS — never fabricated
          frame precision), hidden from AT, and absent until playback actually
          starts, so reduced-motion and Save-Data visitors see nothing. */}
      <div className="absolute bottom-36 right-5 z-20 flex items-center gap-3 md:bottom-28 md:right-9">
        {hasStarted && reelSeconds !== null && (
          <span aria-hidden className="label over-media tabular-nums text-ivory/85">
            {formatReelTime(reelSeconds)}
          </span>
        )}
        <button
          ref={playControlRef}
          type="button"
          onClick={togglePlay}
          aria-label={isPlaying ? `Pause ${label} teaser` : `Play ${label} teaser`}
          className="reel-ring media-control flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-ink/55 text-ivory backdrop-blur-md hover:bg-ink/80"
        >
          {isPlaying ? (
            <svg width="13" height="13" viewBox="0 0 14 14" aria-hidden>
              <rect x="2.5" y="2" width="3" height="10" rx="0.6" fill="currentColor" />
              <rect x="8.5" y="2" width="3" height="10" rx="0.6" fill="currentColor" />
            </svg>
          ) : (
            <svg width="13" height="13" viewBox="0 0 14 14" aria-hidden>
              <path d="M3 1.5L12 7L3 12.5V1.5Z" fill="currentColor" />
            </svg>
          )}
        </button>
      </div>
    </>
  );
}
