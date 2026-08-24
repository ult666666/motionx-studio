import { cn } from "@/lib/utilities";

/**
 * MOTIONX text logotype, recreated with typography (no raster extraction).
 * "MOTION" in ivory, "X" in electric blue with a subtle chrome sheen.
 */
export function Logotype({
  className,
  onAccent = false,
}: {
  className?: string;
  onAccent?: boolean;
}) {
  return (
    <span
      className={cn(
        "font-display font-semibold tracking-[-0.04em] leading-none select-none",
        className,
      )}
      aria-hidden="true"
    >
      <span className={onAccent ? "text-ink" : "text-ivory"}>MOTION</span>
      {/* The gradient + hover chrome sweep live in .logotype-x (globals.css);
          the resting paint is byte-identical to the previous inline style. */}
      <span className={cn("relative", onAccent ? "text-ink" : "logotype-x text-accent")}>
        X
      </span>
    </span>
  );
}
