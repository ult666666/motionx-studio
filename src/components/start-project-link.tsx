"use client";

import type { MouseEvent, ReactNode } from "react";
import { scrollToContact, shouldInterceptLinkActivation } from "@/lib/utilities";

/**
 * Small client island for "Start a Project" CTAs inside server-rendered
 * sections. Owns the focus-aware scroll contract (scroll + focus the contact
 * heading, never open email) while the plain #contact anchor keeps working
 * without JavaScript and for modified clicks.
 */
export function StartProjectLink({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <a
      href="#contact"
      onClick={(event: MouseEvent<HTMLAnchorElement>) => {
        if (!shouldInterceptLinkActivation(event)) return;
        scrollToContact(event);
      }}
      className={className}
    >
      {children}
    </a>
  );
}
