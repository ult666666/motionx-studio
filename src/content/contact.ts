/**
 * Public inquiry options shared by service, project, base-pilot, and form content.
 * Keeping the project-type union here makes broken CTA preselection a compile-
 * time error instead of a silent conversion bug. The paired Campaign Content
 * Add-On is intentionally absent: it is a referral-only scope in pilot.ts.
 */
export const projectTypes = [
  "Not sure yet",
  "Product Film",
  "Motion-First Website",
  "Product Launch Page",
  "Film + Website Launch System",
  "Campaign Content System",
  "Other",
] as const;

export type ProjectType = (typeof projectTypes)[number];

export const budgetRanges = [
  "Under $1,000",
  "$1,000–$2,500",
  "$2,500–$5,000",
  "$5,000+",
  "To be discussed",
] as const;

export const timelineRanges = ["ASAP", "2–4 weeks", "1–2 months", "Flexible"] as const;

export function isProjectType(value: string): value is ProjectType {
  return (projectTypes as ReadonlyArray<string>).includes(value);
}
