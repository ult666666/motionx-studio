import {
  getProjectCapabilityLabel,
  getProjectConceptLabel,
  getProjectTrt,
  projectNavigationCopy,
  projects,
  selectedWorkIntro,
} from "@/content/projects";
import { MaskedLines, Reveal } from "./reveal";
import { SelectedWorkEditBay } from "./selected-work-edit-bay";

/**
 * Server-rendered section shell. Only the compact project index and active
 * media stage hydrate; long-form case-study content remains on canonical
 * /work/[slug] routes instead of being duplicated in a homepage modal.
 */
export function SelectedWork() {
  const items = projects.map((project) => ({
    slug: project.slug,
    title: project.title,
    index: project.index,
    capability: getProjectCapabilityLabel(project.category),
    conceptLabel: getProjectConceptLabel(project.category),
    duration: project.duration,
    trt: getProjectTrt(project),
    orientation: project.orientation,
    width: project.width,
    height: project.height,
    video: project.video,
    videoMobile: project.videoMobile,
    poster: project.poster,
    captions: project.captions,
    accent: project.accent,
    demonstrates: project.demonstrates,
  }));

  return (
    <section
      id="work"
      className="relative scroll-mt-20 border-t border-line bg-ink py-20 md:py-28"
    >
      <div className="shell">
        <div className="mb-12 flex flex-col gap-6 md:mb-16 md:flex-row md:items-end md:justify-between">
          <div>
            <Reveal as="p" className="label mb-5 text-accent-soft">
              {selectedWorkIntro.label}
            </Reveal>
            <h2 className="display text-balance text-[clamp(2.25rem,6vw,4.5rem)] text-ivory">
              <MaskedLines lines={[selectedWorkIntro.heading]} />
            </h2>
          </div>
          <Reveal
            as="p"
            className="max-w-sm text-pretty text-sm leading-relaxed text-gray md:text-right"
          >
            {selectedWorkIntro.body}
          </Reveal>
        </div>

        <SelectedWorkEditBay
          items={items}
          nowViewingLabel={projectNavigationCopy.nowViewing}
          previewLabel={projectNavigationCopy.previewFilm}
          openCaseStudyLabel={projectNavigationCopy.openCaseStudy}
          caseStudyCta={selectedWorkIntro.caseStudyCta}
        />
      </div>
    </section>
  );
}
