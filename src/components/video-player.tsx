"use client";

import { useEffect, useId, useRef, useState } from "react";
import { interfaceCopy } from "@/content/interface";
import { MOBILE_MEDIA_CONDITION } from "@/content/media";
import { useInViewVideo } from "@/hooks/use-in-view-video";
import { useMediaArming } from "@/hooks/use-media-arming";
import { useVideoAutoplayAllowed } from "@/hooks/use-video-autoplay-policy";
import { cn } from "@/lib/utilities";

/** Whole-second MM:SS readout — real playback data, never frame precision. */
function formatTimecode(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
}

type Props = {
  /** Accessible name used to disambiguate repeated media controls. */
  label: string;
  /** Full-resolution web copy — the final fallback in the source ladder. */
  src: string;
  /** Optional mobile derivative, offered first via `<source media>` so the
   *  browser picks it natively on small viewports (no JS branching). */
  mobileSrc?: string;
  poster: string;
  width: number;
  height: number;
  /** Optional English WebVTT captions for the film's audio track. Renders a
   *  <track> plus an accessible CC toggle (native controls are disabled). */
  captionsSrc?: string;
  className?: string;
  /** Normal visitors default to metadata. Until autoplay preferences are known,
   *  and for reduced-motion/data-saver visitors, the player forces `none`. */
  preload?: "none" | "metadata" | "auto";
  /** Show the floating play/pause + mute controls. */
  controls?: boolean;
  rounded?: boolean;
  /** Pause auto-playback when a containing surface temporarily disables it. */
  enabled?: boolean;
  /** Edit-suite telemetry overlay: a real MM:SS / MM:SS readout and a 1px
   *  playhead rule in the surrounding --project-accent. Decorative
   *  (aria-hidden, pointer-events-none), derived entirely from the media
   *  element, and absent until real duration data exists — so poster-only
   *  visitors see nothing and no extra bytes are ever requested. Opt-in from
   *  the edit bay only. */
  telemetry?: boolean;
};

const AUDIO_OWNER_EVENT = "motionx:video-audio-owner";

export function VideoPlayer({
  label,
  src,
  mobileSrc,
  poster,
  width,
  height,
  captionsSrc,
  className,
  preload = "metadata",
  controls = true,
  rounded = true,
  enabled = true,
  telemetry = false,
}: Props) {
  const ownerId = useId();
  const autoplayAllowed = useVideoAutoplayAllowed();
  const [failed, setFailed] = useState(false);
  const ref = useRef<HTMLVideoElement>(null);
  // Declared before playback on purpose: both effects fire in the commit where
  // `armed` flips, and the sources must be loaded before anything plays.
  const { armed, requestPlay } = useMediaArming(ref, enabled && autoplayAllowed);
  const { isPlaying, setManualPaused } = useInViewVideo(ref, {
    enabled: enabled && autoplayAllowed && armed && !failed,
  });
  const [muted, setMuted] = useState(true);
  const [captionsOn, setCaptionsOn] = useState(false);
  const trackRef = useRef<HTMLTrackElement>(null);
  const playheadRef = useRef<HTMLSpanElement>(null);
  // Whole seconds only (≤1 re-render/s); the playhead transform is written
  // imperatively on each timeupdate so React never runs at media frequency.
  const [clock, setClock] = useState<{ current: number; total: number } | null>(
    null,
  );

  useEffect(() => {
    if (!telemetry) return;
    const el = ref.current;
    if (!el) return;
    let lastSecond = -1;
    const sync = () => {
      if (!Number.isFinite(el.duration) || el.duration <= 0) return;
      if (playheadRef.current) {
        playheadRef.current.style.transform = `scaleX(${(
          el.currentTime / el.duration
        ).toFixed(4)})`;
      }
      const second = Math.floor(el.currentTime);
      if (second !== lastSecond) {
        lastSecond = second;
        setClock({ current: second, total: Math.round(el.duration) });
      }
    };
    el.addEventListener("timeupdate", sync);
    el.addEventListener("durationchange", sync);
    return () => {
      el.removeEventListener("timeupdate", sync);
      el.removeEventListener("durationchange", sync);
    };
  }, [telemetry, ref]);

  // Keep the requested caption state authoritative even when WebKit exposes
  // the <track> element before its TextTrack object is ready. The load handler
  // below reapplies the same state when the track finishes initializing.
  useEffect(() => {
    const track = trackRef.current?.track;
    if (track) track.mode = captionsOn ? "showing" : "disabled";
  }, [captionsOn]);

  const toggleCaptions = () => {
    setCaptionsOn((current) => !current);
  };

  // Independent players stay decoupled while a lightweight document event
  // ensures only the visitor's latest choice can own audible playback.
  useEffect(() => {
    const muteIfPeerOwnsAudio = (event: Event) => {
      const owner = (event as CustomEvent<string>).detail;
      const element = ref.current;
      if (!element || owner === ownerId || element.muted) return;
      element.muted = true;
      setMuted(true);
    };
    window.addEventListener(AUDIO_OWNER_EVENT, muteIfPeerOwnsAudio);
    return () => window.removeEventListener(AUDIO_OWNER_EVENT, muteIfPeerOwnsAudio);
  }, [ownerId, ref]);

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

  const toggleMute = () => {
    const el = ref.current;
    if (!el) return;
    const next = !el.muted;
    el.muted = next;
    setMuted(next);
    if (!next) {
      window.dispatchEvent(
        new CustomEvent<string>(AUDIO_OWNER_EVENT, { detail: ownerId }),
      );
    }
    // Unmuting implies the visitor wants it playing. From a cold start this
    // routes through arming, which defers the play by one commit; the element
    // is already unmuted by then, so a browser that requires a live gesture for
    // audible playback may reject it and leave the poster. That only affects
    // unmuting a film that has never been played on a reduced-motion or
    // Save-Data visit — the play control beside it still works.
    if (!next && el.paused) {
      setManualPaused(false);
      requestPlay();
    }
  };

  return (
    <div
      className={cn(
        "group relative overflow-hidden bg-soft",
        rounded && "rounded-xl",
        className,
      )}
      style={{ aspectRatio: `${width} / ${height}` }}
    >
      <video
        ref={ref}
        className="h-full w-full object-cover"
        poster={poster}
        width={width}
        height={height}
        muted={muted}
        loop
        playsInline
        preload={autoplayAllowed ? preload : "none"}
        aria-label={`${label} video`}
        // No `controls` attr — we provide accessible custom controls.
      >
        {/* Ordered source ladder: the media-qualified mobile derivative is
            offered first; browsers outside the condition skip it natively.
            A failed <source> fires `error` on the source element (not the
            video), and the browser then tries the NEXT candidate — so only
            the LAST source's error means the ladder is exhausted and the
            player is genuinely unavailable. Poster-only policy
            (preload="none", no play attempt) never triggers it.

            Withheld until `armed`. `preload="none"` alone is a hint that some
            engines ignore, and an element with no candidates cannot leak bytes
            for a reduced-motion or Save-Data visitor. */}
        {armed && mobileSrc && (
          <source src={mobileSrc} type="video/mp4" media={MOBILE_MEDIA_CONDITION} />
        )}
        {armed && (
          <source src={src} type="video/mp4" onError={() => setFailed(true)} />
        )}
        {captionsSrc && (
          <track
            ref={trackRef}
            kind="captions"
            srcLang="en"
            label="English"
            src={captionsSrc}
            onLoad={() => {
              const track = trackRef.current?.track;
              if (track) track.mode = captionsOn ? "showing" : "disabled";
            }}
          />
        )}
      </video>

      {failed && (
        <p
          role="status"
          className="label absolute bottom-3 left-3 z-20 max-w-[85%] rounded-full border border-white/15 bg-ink/70 px-3.5 py-2 text-ivory backdrop-blur-md md:bottom-4 md:left-4"
        >
          {interfaceCopy.media.unavailable}
        </p>
      )}

      {/* Telemetry layer — decorative, real playback data only. Appears once
          the element reports a genuine duration (metadata), so poster-only
          policies keep it absent. Sits under the control layer and takes no
          pointer events. */}
      {telemetry && !failed && clock && (
        <div aria-hidden className="pointer-events-none absolute inset-0 z-10">
          <span className="label absolute left-3 top-3 border-l border-[var(--project-accent)] bg-ink/60 px-2.5 py-1.5 tabular-nums text-ivory/85 backdrop-blur-sm md:left-4 md:top-4">
            {interfaceCopy.media.timecodeLabel} {formatTimecode(clock.current)}{" "}
            / {formatTimecode(clock.total)}
          </span>
          {/* Ink-backed rail keeps the accent playhead legible over bright
              frames — the "one active playhead" signature was invisible at
              1px on a white/10 track. */}
          <span className="absolute inset-x-0 bottom-0 h-0.5 bg-ink/60">
            <span
              ref={playheadRef}
              className="block h-full origin-left scale-x-0 bg-[var(--project-accent)] transition-transform duration-300 ease-linear motion-reduce:transition-none"
            />
          </span>
        </div>
      )}

      {controls && !failed && (
        <div className="pointer-events-none absolute inset-0 z-20 flex items-end justify-between p-3 md:p-4">
          <button
            type="button"
            onClick={togglePlay}
            aria-label={`${isPlaying ? "Pause video" : "Play video"} — ${label}`}
            className="media-control pointer-events-auto flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-ink/65 text-ivory backdrop-blur-md hover:bg-ink/80"
          >
            {isPlaying ? <PauseIcon /> : <PlayIcon />}
          </button>
          {/* Secondary toggles rest at reduced presence so the chrome recedes
              behind the film; hover or keyboard focus restores full weight.
              Never hidden — fully rendered and hit-testable at all times. */}
          <div className="pointer-events-none flex items-center gap-2 opacity-70 transition-opacity duration-300 group-hover:opacity-100 group-focus-within:opacity-100 motion-reduce:transition-none">
            {captionsSrc && (
              <button
                type="button"
                onClick={toggleCaptions}
                // Same convention as mute: the swapping label carries the
                // state; adding aria-pressed on top would announce twice.
                aria-label={`${captionsOn ? "Hide captions" : "Show captions"} — ${label}`}
                className={cn(
                  "media-control pointer-events-auto flex h-11 w-11 items-center justify-center rounded-full border border-white/15 font-mono text-[0.65rem] tracking-[0.08em] backdrop-blur-md",
                  captionsOn
                    ? "bg-ivory/90 text-ink hover:bg-ivory"
                    : "bg-ink/65 text-ivory hover:bg-ink/80",
                )}
              >
                CC
              </button>
            )}
            <button
              type="button"
              onClick={toggleMute}
              // Swapping label already conveys state; aria-pressed on top of it
              // makes SRs announce a contradictory "Unmute video, pressed".
              aria-label={`${muted ? "Unmute video" : "Mute video"} — ${label}`}
              className="media-control pointer-events-auto flex h-11 w-11 items-center justify-center rounded-full border border-white/15 bg-ink/65 text-ivory backdrop-blur-md hover:bg-ink/80"
            >
              {muted ? <MutedIcon /> : <SoundIcon />}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function PlayIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
      <path d="M3 1.5L12 7L3 12.5V1.5Z" fill="currentColor" />
    </svg>
  );
}
function PauseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
      <rect x="2.5" y="2" width="3" height="10" rx="0.6" fill="currentColor" />
      <rect x="8.5" y="2" width="3" height="10" rx="0.6" fill="currentColor" />
    </svg>
  );
}
function SoundIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M2 6v4h2.5L8 13V3L4.5 6H2Z" fill="currentColor" />
      <path d="M10.5 5.5a3 3 0 010 5M12.4 4a5.5 5.5 0 010 8" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
    </svg>
  );
}
function MutedIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden>
      <path d="M2 6v4h2.5L8 13V3L4.5 6H2Z" fill="currentColor" />
      <path d="M10.5 6l4 4M14.5 6l-4 4" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round" />
    </svg>
  );
}
