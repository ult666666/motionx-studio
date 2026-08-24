import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { site } from "@/content/site";
import "./globals.css";

const title = `${site.name} — ${site.tagline}`;

export const metadata: Metadata = {
  metadataBase: new URL(site.url),
  title: {
    default: title,
    template: `%s — ${site.name}`,
  },
  description: site.description,
  applicationName: site.name,
  keywords: [
    "product films",
    "motion-first websites",
    "product launch pages",
    "launch systems",
    "motion design",
    "campaign content",
    "creative studio",
    "product launch",
    "MOTIONX",
  ],
  authors: [{ name: site.founder }],
  creator: site.founder,
  alternates: { canonical: "/" },
  openGraph: {
    type: "website",
    url: site.url,
    siteName: site.name,
    title,
    description: site.description,
    images: [
      {
        // JPEG, not WebP — LinkedIn/WhatsApp/iMessage crawlers don't reliably
        // render WebP link previews.
        url: "/og/og-image.jpg",
        width: 1200,
        height: 630,
        alt: `${site.name} — ${site.tagline}`,
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title,
    description: site.description,
    images: ["/og/og-image.jpg"],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: "#050505",
  colorScheme: "dark",
  width: "device-width",
  initialScale: 1,
};

const jsonLd = [
  {
    "@context": "https://schema.org",
    // Organization (not ProfessionalService) — the latter is a LocalBusiness
    // subtype that needs a postal address, which the studio deliberately omits.
    // Every property below is valid on Organization with nothing fabricated.
    "@type": "Organization",
    name: site.name,
    description: site.description,
    founder: { "@type": "Person", name: site.founder },
    url: site.url,
    email: site.contact.email,
    areaServed: "Worldwide",
    knowsAbout: [
      "Product Films",
      "Motion-First Websites",
      "Product Launch Pages",
      "Campaign Content Systems",
    ],
    // Only advertise profiles that actually exist.
    ...(site.social.length > 0 ? { sameAs: site.social.map((s) => s.href) } : {}),
  },
  {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: site.name,
    description: site.description,
    url: site.url,
    inLanguage: "en",
    publisher: { "@type": "Organization", name: site.name, url: site.url },
  },
];

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      {/* Build-provenance marker: "production" is baked into prerendered HTML
          by `next build`, while `next dev` renders "development". Browser
          verification DETECTS the served artifact's mode from this attribute
          instead of trusting a caller-provided label. Public, non-sensitive. */}
      <body data-motionx-env={process.env.NODE_ENV}>
        {/* Every route's <main> carries id="content" — #work only exists on
            the home page, so it would be a dead target on /pilot and /work. */}
        <a
          href="#content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[300] focus:rounded-full focus:bg-ivory focus:px-5 focus:py-2.5 focus:text-sm focus:font-medium focus:text-ink"
        >
          Skip to content
        </a>
        {children}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(jsonLd).replace(/</g, "\\u003c"),
          }}
        />
      </body>
    </html>
  );
}
