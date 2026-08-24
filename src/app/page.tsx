import { Navigation } from "@/components/navigation";
import { Hero } from "@/components/hero";
import { StudioIntro } from "@/components/studio-intro";
import { LaunchSystem } from "@/components/launch-system";
import { SelectedWork } from "@/components/selected-work";
import { Services } from "@/components/services";
import { PilotCallout } from "@/components/pilot-callout";
import { Process } from "@/components/process";
import { StudioSection } from "@/components/studio-section";
import { ContactSection } from "@/components/contact-section";
import { Footer } from "@/components/footer";
import { heroReelMedia, MOBILE_MEDIA_CONDITION } from "@/content/media";

export default function Home() {
  return (
    <>
      {/* The responsive hero poster is the LCP element (the reel itself is
          preload="none"). React 19 hoists these media-qualified links into
          <head> so only the matching fallback paints early. */}
      <link
        rel="preload"
        as="image"
        media={MOBILE_MEDIA_CONDITION}
        href={heroReelMedia.mobilePoster}
        fetchPriority="high"
      />
      <link
        rel="preload"
        as="image"
        media="(min-width: 768px)"
        href={heroReelMedia.poster}
        fetchPriority="high"
      />
      <Navigation />
      <main id="content">
        <Hero />
        <StudioIntro />
        <SelectedWork />
        <LaunchSystem />
        <Services />
        <PilotCallout />
        <Process />
        <StudioSection />
        <ContactSection />
      </main>
      <Footer />
    </>
  );
}
