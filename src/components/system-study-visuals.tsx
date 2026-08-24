/**
 * Shared, self-owned AURA concept visuals. These are intentionally pure HTML/CSS
 * so the homepage System Study and its dedicated proof route use the same
 * visual language without loading media or implying a third-party client.
 */

export function ChromeObject({ size = 1 }: { size?: number }) {
  return (
    <div
      className="relative"
      style={{ width: `${64 * size}px`, height: `${112 * size}px` }}
      aria-hidden
    >
      <div
        className="absolute -inset-6 rounded-full blur-2xl"
        style={{
          background:
            "radial-gradient(circle at 50% 40%, #6d7cff66, transparent 65%), radial-gradient(circle at 60% 75%, #d65bd644, transparent 60%)",
        }}
      />
      <div
        className="absolute inset-0 overflow-hidden rounded-[999px]"
        style={{
          background:
            "linear-gradient(150deg, #f4f4fa 4%, #aeb0c2 22%, #6f7184 40%, #eef0f8 56%, #595b6c 72%, #c9cbda 92%)",
          boxShadow:
            "inset 0 2px 6px #ffffffcc, inset 0 -8px 14px #00000080, 0 12px 30px -10px #000000aa",
        }}
      >
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(120deg, transparent 30%, #6d7cff55 46%, transparent 52%), linear-gradient(300deg, transparent 40%, #d65bd644 60%, transparent 66%)",
          }}
        />
        <div className="absolute left-[26%] top-[6%] h-[88%] w-[10%] rounded-full bg-white/70 blur-[2px]" />
      </div>
    </div>
  );
}

export function StageFilm() {
  return (
    <div className="grain relative aspect-video w-full overflow-hidden rounded-lg border border-line bg-ink">
      <div
        className="absolute inset-0 opacity-90"
        style={{
          background:
            "radial-gradient(60% 90% at 50% 55%, #11142a, #050505 70%), conic-gradient(from 200deg at 50% 50%, transparent, #6d7cff22, transparent 40%, #d65bd61f, transparent 70%)",
        }}
      />
      <div
        className="absolute inset-0 opacity-60"
        style={{
          background:
            "repeating-conic-gradient(from 0deg at 50% 48%, #6d7cff00 0deg, #8a96ff14 2deg, #6d7cff00 6deg)",
        }}
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <ChromeObject size={1} />
      </div>
      <div className="absolute inset-x-0 top-0 h-[10%] bg-ink" />
      <div className="absolute inset-x-0 bottom-0 h-[10%] bg-ink" />
      <div className="absolute bottom-2 left-3 flex items-center gap-2">
        <span className="flex h-1.5 w-1.5 items-center justify-center rounded-full bg-magenta" />
        <span className="font-mono text-[0.55rem] tracking-[0.2em] text-ivory/80">
          REC 00:07
        </span>
      </div>
      <div className="absolute bottom-2 right-3 font-mono text-[0.55rem] tracking-[0.2em] text-ivory/60">
        MOTIONX · FILM
      </div>
    </div>
  );
}

export function StageWebsite() {
  return (
    <div className="overflow-hidden rounded-lg border border-line bg-soft shadow-[0_24px_60px_-30px_#6d7cff55]">
      <div className="flex items-center gap-1.5 border-b border-line bg-ink/60 px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-line" />
        <span className="h-2 w-2 rounded-full bg-line" />
        <span className="h-2 w-2 rounded-full bg-line" />
        <span className="ml-2 flex h-3.5 flex-1 items-center rounded-full bg-line/50 px-2 font-mono text-[0.5rem] text-gray-dim">
          AURA · CONCEPT STUDY
        </span>
      </div>

      <div className="relative aspect-[4/5] overflow-hidden bg-ink">
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(70% 60% at 70% 30%, #11142e, transparent 70%)",
          }}
        />
        <div className="relative flex items-center justify-between px-3 py-2.5">
          <span className="font-mono text-[0.55rem] font-semibold tracking-[0.2em] text-ivory">
            AURA
          </span>
          <div className="hidden items-center gap-2 sm:flex">
            <span className="text-[0.5rem] text-gray">Form</span>
            <span className="text-[0.5rem] text-gray">Light</span>
            <span className="rounded-full bg-ivory px-2 py-0.5 text-[0.5rem] font-medium text-ink">
              Explore
            </span>
          </div>
        </div>

        <div className="relative grid grid-cols-5 items-center gap-2 px-3 pt-3">
          <div className="col-span-3">
            <p className="font-mono text-[0.45rem] tracking-[0.2em] text-accent-soft">
              CONCEPT · 2026
            </p>
            <p
              className="mt-1.5 text-[1.05rem] font-semibold leading-[0.95] tracking-tight text-ivory"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Designed
              <br />
              to be seen.
            </p>
            <div className="mt-3 inline-flex items-center gap-1 rounded-full bg-ivory px-2.5 py-1 text-[0.5rem] font-medium text-ink">
              Discover <span aria-hidden>→</span>
            </div>
          </div>
          <div className="col-span-2 flex items-center justify-center">
            <ChromeObject size={0.7} />
          </div>
        </div>

        <div className="absolute inset-x-0 bottom-0 flex items-center justify-between border-t border-line/70 px-3 py-2 font-mono text-[0.45rem] tracking-[0.15em] text-gray-dim">
          <span>01 — FORM</span>
          <span>02 — LIGHT</span>
          <span>03 — MOTION</span>
        </div>
      </div>
    </div>
  );
}

export function StageCampaign() {
  return (
    <div className="grid h-full grid-cols-5 gap-2">
      <div className="relative col-span-2 aspect-[9/16] overflow-hidden rounded-md border border-line bg-ink sm:aspect-auto">
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(60% 50% at 50% 35%, #14172e, transparent 70%)",
          }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <ChromeObject size={0.62} />
        </div>
        <p
          className="absolute bottom-2 left-2 right-2 text-[0.55rem] font-semibold leading-tight text-ivory"
          style={{ fontFamily: "var(--font-display)" }}
        >
          Designed to be seen.
        </p>
        <span className="absolute left-2 top-2 font-mono text-[0.4rem] tracking-[0.2em] text-accent-soft">
          9:16
        </span>
      </div>

      <div className="col-span-3 flex flex-col gap-2">
        <div className="relative aspect-square overflow-hidden rounded-md border border-line bg-soft sm:aspect-auto sm:flex-1">
          <div
            className="absolute inset-0"
            style={{
              background:
                "radial-gradient(70% 60% at 30% 40%, #15182f, transparent 70%)",
            }}
          />
          <div className="absolute right-2 top-1/2 -translate-y-1/2">
            <ChromeObject size={0.55} />
          </div>
          <div className="absolute left-2.5 top-2.5">
            <p className="font-mono text-[0.4rem] tracking-[0.2em] text-accent-soft">
              AURA
            </p>
            <p
              className="mt-1 text-[0.7rem] font-semibold leading-[0.95] text-ivory"
              style={{ fontFamily: "var(--font-display)" }}
            >
              The new
              <br />
              standard.
            </p>
          </div>
          <span className="absolute bottom-2 left-2.5 font-mono text-[0.4rem] tracking-[0.2em] text-gray-dim">
            1:1
          </span>
        </div>

        <div className="relative aspect-[16/7] overflow-hidden rounded-md border border-line bg-ink sm:aspect-auto sm:flex-1">
          <div
            className="absolute inset-0"
            style={{ background: "linear-gradient(100deg, #050505 40%, #14172e)" }}
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <ChromeObject size={0.5} />
          </div>
          <div className="absolute left-3 top-1/2 -translate-y-1/2">
            <p
              className="text-[0.62rem] font-semibold leading-none text-ivory"
              style={{ fontFamily: "var(--font-display)" }}
            >
              Explore the form
            </p>
            <span className="mt-1 inline-block rounded-full bg-ivory px-2 py-0.5 text-[0.42rem] font-medium text-ink">
              AURA · CONCEPT
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
