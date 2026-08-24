# MOTIONX SEO and Content Strategy

## Current Baseline

- Home, pilot, System Study, and work routes have route-specific metadata.
- Sitemap includes `/`, `/pilot`, `/system-study`, and all four project routes.
- Robots allows indexing and points at the generated sitemap.
- Organization JSON-LD exists without invented address, phone, awards, or sameAs profiles.
- Project routes use dedicated 1200x630 JPEG Open Graph cards.

## Safe SEO Improvements

- Keep metadata accurate and route-specific.
- Add WebSite JSON-LD at the site level.
- Add CreativeWork JSON-LD on each concept project page with explicit concept/internal wording.
- Add a deterministic `seo:check` script to guard expected routes and forbidden schema fields.
- Keep FAQ content visible for conversion, but do not rely on FAQ rich results after Google's 2026 removal.

## Service Pages Decision

Do not add service-specific pages yet:

- `/services/product-films`
- `/services/motion-first-websites`
- `/services/product-launch-pages`
- `/services/campaign-content-systems`

Reason: they would be thin if created only from current homepage copy. Each page should wait for distinct examples, first-party visuals, process notes, FAQs, and proof-safe case-study links.

Acceptance criteria before adding a service page:

- Unique page thesis and audience.
- Concrete deliverables and scope boundaries.
- At least one relevant first-party example, concept breakdown, or process artifact.
- No fake client proof, metrics, testimonials, awards, location, or scarcity.
- Route-specific metadata and Open Graph card.
- Included in sitemap and SEO sanity script.
- E2E route-health and mobile-overflow checks.

## Future Content Hubs

Good candidates after MOTIONX has first-party artifacts:

- "How a product film becomes a launch page"
- "Responsible cinematic video on the web"
- "Concept project breakdown: Renewal"
- "Concept project breakdown: Liquid Signal"
- "Motion-first launch checklist for founders"

## Structured Data Rules

Allowed now:

- `Organization`
- `WebSite`
- `CreativeWork` for concept projects

Avoid unless real and public:

- `PostalAddress`
- `telephone`
- `foundingDate`
- `numberOfEmployees`
- `award` / `awards`
- `aggregateRating`
- `review`
- `sameAs`
- client, customer, or brand relationship fields

## Sources

- Next.js metadata docs: `https://nextjs.org/docs/app/api-reference/functions/generate-metadata`
- Next.js sitemap docs: `https://nextjs.org/docs/app/api-reference/file-conventions/metadata/sitemap`
- Next.js JSON-LD guide: `https://nextjs.org/docs/app/guides/json-ld`
- Google structured data intro: `https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data`
- Google FAQ rich result removal: `https://developers.google.com/search/updates#removing-faq-rich-result`
- Schema.org Organization: `https://schema.org/Organization`
- Schema.org CreativeWork: `https://schema.org/CreativeWork`
