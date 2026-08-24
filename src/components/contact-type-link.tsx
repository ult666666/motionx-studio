"use client";

import type { MouseEvent, ReactNode } from "react";
import Link from "next/link";
import type { ProjectType } from "@/content/contact";
import { navigateToContactWithType } from "@/lib/utilities";

/**
 * Small client island for contextual homepage CTAs. The surrounding service
 * and system sections stay server-rendered while this link owns the same-route
 * URL, form synchronization, scroll, and focus contract.
 */
export function ContactTypeLink({
  formType,
  children,
  className,
}: {
  formType: ProjectType;
  children: ReactNode;
  className?: string;
}) {
  return (
    <Link
      href={`/?type=${encodeURIComponent(formType)}#contact`}
      prefetch={false}
      onClick={(event: MouseEvent<HTMLAnchorElement>) =>
        navigateToContactWithType(event, formType)
      }
      className={className}
    >
      {children}
    </Link>
  );
}
