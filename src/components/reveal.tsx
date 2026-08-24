import type { CSSProperties, ReactNode } from "react";
import { cn } from "@/lib/utilities";

type RevealTag =
  | "div"
  | "section"
  | "ol"
  | "li"
  | "span"
  | "p"
  | "h1"
  | "h2"
  | "h3";

/**
 * Structural wrapper retained for a stable section API. Ordinary copy now
 * renders immediately instead of waiting for dozens of identical JS-driven
 * fades; this keeps the full marketing page readable before hydration and
 * makes the remaining motion cues feel intentional.
 *
 * `variant="soft"` opts a block into the CSS-only `.reveal-soft` scroll
 * entrance. Fail-open by construction: the hidden state exists only inside
 * globals.css's `@supports (animation-timeline: view())` + no-preference
 * gate, so no-JS, no-support, and reduced-motion visitors always see the
 * final state. Keep soft mounts rare (≤6 sitewide) and never on MaskedLines
 * headlines.
 */
export function Reveal({
  children,
  className,
  as = "div",
  variant = "none",
}: {
  children: ReactNode;
  className?: string;
  as?: RevealTag;
  variant?: "none" | "soft";
}) {
  const Tag = as;
  return (
    <Tag className={cn(variant === "soft" && "reveal-soft", className)}>
      {children}
    </Tag>
  );
}

/**
 * Headline-only reveal implemented in CSS. The words remain real, server-
 * rendered text and the animation still completes if client JavaScript never
 * hydrates; reduced-motion visitors see the final state immediately.
 */
export function MaskedLines({
  lines,
  className,
  lineClassName,
  delay = 0,
  stagger = 0.09,
}: {
  lines: string[];
  className?: string;
  lineClassName?: string;
  delay?: number;
  stagger?: number;
}) {
  return (
    <span className={cn("masked-lines", className)}>
      {lines.map((line, index) => (
        <span key={line} className={cn("masked-line", lineClassName)}>
          <span
            className="masked-line__inner"
            style={
              {
                "--masked-line-delay": `${delay + index * stagger}s`,
              } as CSSProperties
            }
          >
            {line}
          </span>
        </span>
      ))}
    </span>
  );
}
