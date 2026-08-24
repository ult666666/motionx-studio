"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  budgetRanges as BUDGETS,
  isProjectType,
  projectTypes as PROJECT_TYPES,
  timelineRanges as TIMELINES,
  type ProjectType,
} from "@/content/contact";
import {
  getPilotReferralFromParams,
  pilotOffers,
  pilotReferralCopy,
  type PilotReferral,
} from "@/content/pilot";
import { copyToClipboard, gmailComposeUrl, mailto } from "@/lib/utilities";

const FIELD_LIMITS = {
  name: 80,
  email: 254,
  company: 120,
  message: 2000,
} as const;

type Fields = {
  name: string;
  email: string;
  company: string;
  type: ProjectType;
  budget: string;
  timeline: string;
  message: string;
};

const EMPTY: Fields = {
  name: "",
  email: "",
  company: "",
  type: PROJECT_TYPES[0],
  budget: BUDGETS[4],
  timeline: TIMELINES[3],
  message: "",
};

type Status = "idle" | "prepared" | "error";

function projectTypeFromLocation(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("type");
}

function pilotReferralFromLocation() {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  const type = params.get("type");
  const pilotId = params.get("pilot");
  if (!type || !pilotId) return null;
  const exactOffer = pilotOffers.find(
    (offer) => offer.id === pilotId && offer.formType === type,
  );
  return exactOffer ? getPilotReferralFromParams(params) : null;
}

function pilotReferralKey(referral: PilotReferral | null) {
  if (!referral) return null;
  return `${referral.baseOffer.id}:${referral.addOn?.id ?? "none"}`;
}

/**
 * The contact form client island. The surrounding section — pitch, supporting
 * details, FAQ — is server-rendered in ContactSection, so controlled-input
 * keystrokes re-render only this form. Coordination with the rest of the page
 * happens through window.location plus the popstate/hashchange/
 * motionx:locationchange events. The public studio email arrives as a narrow
 * serialized prop — client islands never import the full `site` object, so
 * non-public config can't ride along into browser chunks.
 */
export function ContactForm({ email }: { email: string }) {
  const [fields, setFields] = useState<Fields>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<keyof Fields, string>>>({});
  const [status, setStatus] = useState<Status>("idle");
  const [prepared, setPrepared] = useState<{ subject: string; body: string } | null>(null);
  const [helperDismissed, setHelperDismissed] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [selectedPilotReferral, setSelectedPilotReferral] =
    useState<PilotReferral | null>(null);
  const [showOptional, setShowOptional] = useState(false);
  const formRef = useRef<HTMLFormElement>(null);
  const submitButtonRef = useRef<HTMLButtonElement>(null);
  const previousUrlTypeRef = useRef<string | null | undefined>(undefined);
  const previousPilotKeyRef = useRef<string | null | undefined>(undefined);
  const copyTimerRef = useRef<number | null>(null);

  // Keep the pilot context tied to the URL rather than sticky component state.
  // This also pre-selects any valid project type supplied by a trusted site CTA.
  useEffect(() => {
    const syncFromLocation = () => {
      const param = projectTypeFromLocation();
      const previousParam = previousUrlTypeRef.current;
      const pilotReferral = pilotReferralFromLocation();
      const previousPilotKey = previousPilotKeyRef.current;
      const nextPilotKey = pilotReferralKey(pilotReferral);
      previousUrlTypeRef.current = param;
      previousPilotKeyRef.current = nextPilotKey;
      setSelectedPilotReferral(pilotReferral);

      if (
        previousParam !== undefined &&
        (param !== previousParam || nextPilotKey !== previousPilotKey)
      ) {
        setSubmitError(null);
        setPrepared(null);
        setStatus("idle");
        setHelperDismissed(false);
        setCopied(null);
      }

      if (param && param !== previousParam && isProjectType(param)) {
        setFields((current) =>
          current.type === param ? current : { ...current, type: param },
        );
      } else if (
        previousParam &&
        !pilotReferral &&
        (!param || !isProjectType(param))
      ) {
        // Browser history or another URL update removed the pilot referral.
        // Reset only when the field still carries that old referral; a user's
        // explicit selection must never be overwritten.
        setFields((current) =>
          current.type === previousParam
            ? { ...current, type: EMPTY.type }
            : current,
        );
      }
    };

    syncFromLocation();
    window.addEventListener("popstate", syncFromLocation);
    window.addEventListener("hashchange", syncFromLocation);
    window.addEventListener("motionx:locationchange", syncFromLocation);
    return () => {
      window.removeEventListener("popstate", syncFromLocation);
      window.removeEventListener("hashchange", syncFromLocation);
      window.removeEventListener("motionx:locationchange", syncFromLocation);
    };
  }, []);

  useEffect(
    () => () => {
      if (copyTimerRef.current !== null) {
        window.clearTimeout(copyTimerRef.current);
      }
    },
    [],
  );

  const set = <K extends keyof Fields>(k: K, v: Fields[K]) => {
    if (k === "type" && typeof window !== "undefined") {
      const url = new URL(window.location.href);
      const projectTypeChanged = fields.type !== v;

      // Pilot intent comes only from the exact offer CTA. A project-type edit
      // must never infer a different package merely because another offer uses
      // the newly selected form type. Keep attribution, but clear both referral
      // markers so the edited inquiry is treated as a normal project inquiry.
      if (
        projectTypeChanged &&
        (url.searchParams.has("type") ||
          url.searchParams.has("pilot") ||
          url.searchParams.has("addon"))
      ) {
        url.searchParams.delete("type");
        url.searchParams.delete("pilot");
        url.searchParams.delete("addon");
        history.replaceState(
          history.state,
          "",
          `${url.pathname}${url.search}${url.hash}`,
        );
        previousUrlTypeRef.current = null;
        previousPilotKeyRef.current = null;
        setSelectedPilotReferral(null);
        window.dispatchEvent(new Event("motionx:locationchange"));
      } else {
        setSelectedPilotReferral(
          projectTypeChanged ? null : pilotReferralFromLocation(),
        );
      }
    } else {
      // If another interaction follows a browser/history URL change, clear any
      // stale pilot banner before a new draft can be prepared.
      const referral = pilotReferralFromLocation();
      setSelectedPilotReferral(referral);
      previousUrlTypeRef.current = projectTypeFromLocation();
      previousPilotKeyRef.current = pilotReferralKey(referral);
    }

    setFields((f) => ({ ...f, [k]: v }));
    setErrors((e) => ({ ...e, [k]: undefined }));
    setSubmitError(null);
    setPrepared(null);
    setStatus("idle");
    setHelperDismissed(false);
    setCopied(null);
  };

  const validate = (): boolean => {
    const next: Partial<Record<keyof Fields, string>> = {};
    if (!fields.name.trim()) next.name = "Please enter your name.";
    if (!fields.email.trim()) {
      next.email = "Please enter your email.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email.trim())) {
      next.email = "Please enter a valid email address.";
    }
    if (!fields.message.trim()) next.message = "Tell us a little about the project.";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const buildMessage = (
    pilotReferral: PilotReferral | null,
    projectType: string = fields.type,
  ) => {
    const who = fields.company.trim() || fields.name.trim();
    const subjectPrefix = pilotReferral
      ? "MOTIONX Pilot Project Inquiry"
      : "MOTIONX Project Inquiry";
    const subject = `${subjectPrefix} — ${who} · ${projectType}`;
    const pilotLines = pilotReferral
      ? [
          `${pilotReferralCopy.draftBaseLabel}: ${pilotReferral.baseOffer.title} — ${pilotReferral.baseOffer.pilotPrice}`,
          ...(pilotReferral.addOn
            ? [
                `${pilotReferralCopy.draftAddOnLabel}: ${pilotReferral.addOn.title} — ${pilotReferral.addOn.pilotPrice}`,
              ]
            : []),
        ]
      : [];
    const body = [
      `Name: ${fields.name}`,
      `Email: ${fields.email}`,
      `Company: ${fields.company || "—"}`,
      `Project type: ${projectType}`,
      ...pilotLines,
      `Budget range: ${fields.budget}`,
      `Timeline: ${fields.timeline}`,
      "",
      "Project description:",
      fields.message,
    ].join("\n");
    return { subject, body };
  };

  /**
   * Open Gmail compose via a real, transient anchor click. This is a direct
   * user-gesture navigation — unlike window.open() it does NOT return null when
   * a tab actually opens (the old false "blocked" state), so we only treat a
   * thrown exception as a genuine failure.
   */
  const openGmail = (msg: { subject: string; body: string }): boolean => {
    const url = gmailComposeUrl(email, msg.subject, msg.body);
    let anchor: HTMLAnchorElement | null = null;
    try {
      anchor = document.createElement("a");
      anchor.href = url;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.style.display = "none";
      document.body.appendChild(anchor);
      anchor.click();
      return true;
    } catch {
      return false;
    } finally {
      anchor?.remove();
    }
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!validate()) {
      // Announce the failure and move focus to the first invalid control so a
      // keyboard/screen-reader user isn't left silent after pressing submit.
      // rAF waits for the re-render that sets aria-invalid + the error text, so
      // focusing then announces the field's associated message.
      setSubmitError("Please complete the highlighted fields to continue.");
      requestAnimationFrame(() => {
        formRef.current
          ?.querySelector<HTMLElement>('[aria-invalid="true"]')
          ?.focus();
      });
      return;
    }
    setSubmitError(null);
    // Read the URL at the moment of intent so a removed `type` query can never
    // leak a stale pilot subject into a later general inquiry.
    const locationType = projectTypeFromLocation();
    const submittedType =
      locationType && isProjectType(locationType)
        ? locationType
        : fields.type;
    const msg = buildMessage(pilotReferralFromLocation(), submittedType);
    setPrepared(msg);
    setHelperDismissed(false);
    setStatus(openGmail(msg) ? "prepared" : "error");
  };

  const flashCopied = (label: string) => {
    setCopied(label);
    if (copyTimerRef.current !== null) {
      window.clearTimeout(copyTimerRef.current);
    }
    copyTimerRef.current = window.setTimeout(() => {
      setCopied((current) => (current === label ? null : current));
      copyTimerRef.current = null;
    }, 2200);
  };

  const handleCopy = async (text: string, label: string) => {
    const ok = await copyToClipboard(text);
    flashCopied(
      ok ? label : "Couldn’t copy—select the address or message manually",
    );
  };

  const dismissHelper = () => {
    setHelperDismissed(true);
    requestAnimationFrame(() => submitButtonRef.current?.focus());
  };

  const currentDraft = buildMessage(selectedPilotReferral);

  return (
    <form ref={formRef} noValidate onSubmit={onSubmit} className="space-y-5">
      {/* One PERSISTENT polite live region: it stays mounted across referral
          changes so announcements come from content changes, never from
          region remounts. Only the inner presentational slate is keyed, so
          the settle entrance replays when the referral actually changes. */}
      <div aria-live="polite">
        {selectedPilotReferral && (
          <div
            key={pilotReferralKey(selectedPilotReferral) ?? "none"}
            className="settle-enter border-l-2 border-accent bg-accent/[0.04] px-4 py-3"
          >
            <p className="label text-accent-soft">
              {pilotReferralCopy.selectedLabel}
            </p>
            <div className="mt-3">
              <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                <div>
                  <p className="label text-gray-dim">
                    {pilotReferralCopy.baseLabel}
                  </p>
                  <p className="mt-1 text-sm font-medium text-ivory">
                    {selectedPilotReferral.baseOffer.title}
                  </p>
                </div>
                <p className="font-mono text-xs tabular-nums text-ivory">
                  {selectedPilotReferral.baseOffer.pilotPrice}
                </p>
              </div>
              <p className="mt-1 text-xs leading-relaxed text-gray">
                {selectedPilotReferral.baseOffer.deliverable}
              </p>
            </div>
            {selectedPilotReferral.addOn && (
              <div className="mt-3 border-t border-line pt-3">
                <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
                  <div>
                    <p className="label text-gray-dim">
                      {pilotReferralCopy.addOnLabel}
                    </p>
                    <p className="mt-1 text-sm font-medium text-ivory">
                      {selectedPilotReferral.addOn.title}
                    </p>
                  </div>
                  <p className="font-mono text-xs tabular-nums text-ivory">
                    {selectedPilotReferral.addOn.pilotPrice}
                  </p>
                </div>
                <p className="mt-1 text-xs leading-relaxed text-gray">
                  {selectedPilotReferral.addOn.deliverable}
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <Field
          label="Name"
          htmlFor="contact-name"
          required
          error={errors.name}
          errorId="err-name"
          input={
            <input
              id="contact-name"
              name="name"
              type="text"
              value={fields.name}
              onChange={(e) => set("name", e.target.value)}
              autoComplete="name"
              maxLength={FIELD_LIMITS.name}
              required
              aria-required="true"
              className={inputCls(!!errors.name)}
              aria-invalid={!!errors.name}
              aria-describedby={errors.name ? "err-name" : undefined}
            />
          }
        />
        <Field
          label="Email"
          htmlFor="contact-email"
          required
          error={errors.email}
          errorId="err-email"
          input={
            <input
              id="contact-email"
              name="email"
              type="email"
              value={fields.email}
              onChange={(e) => set("email", e.target.value)}
              autoComplete="email"
              maxLength={FIELD_LIMITS.email}
              spellCheck={false}
              required
              aria-required="true"
              className={inputCls(!!errors.email)}
              aria-invalid={!!errors.email}
              aria-describedby={errors.email ? "err-email" : undefined}
            />
          }
        />
      </div>

      <Field
        label="Project type"
        htmlFor="contact-project-type"
        input={
          <Select
            id="contact-project-type"
            name="project-type"
            value={fields.type}
            onChange={(v) => {
              if (isProjectType(v)) set("type", v);
            }}
            options={PROJECT_TYPES}
          />
        }
      />

      <Field
        label="Project description"
        htmlFor="contact-message"
        required
        error={errors.message}
        errorId="err-message"
        input={
          <>
            <textarea
              id="contact-message"
              name="message"
              rows={5}
              value={fields.message}
              onChange={(e) => set("message", e.target.value)}
              maxLength={FIELD_LIMITS.message}
              required
              aria-required="true"
              className={inputCls(!!errors.message) + " resize-y"}
              placeholder="What are you launching, who’s it for, and what should it achieve?"
              aria-invalid={!!errors.message}
              aria-describedby={errors.message ? "err-message message-count" : "message-count"}
            />
            {/* Brief-length meter — decorative only; the n/2000 count below
                remains the sole accessible source. Accent throughout (magenta
                stays the error voice). */}
            <span aria-hidden className="mt-1.5 block h-px w-full bg-line">
              <span
                className="block h-full origin-left bg-accent/70 transition-transform duration-300 ease-cinematic motion-reduce:transition-none"
                style={{
                  transform: `scaleX(${Math.min(
                    1,
                    fields.message.length / FIELD_LIMITS.message,
                  )})`,
                }}
              />
            </span>
            <span
              id="message-count"
              className="mt-1.5 block text-right font-mono text-[0.62rem] tabular-nums text-gray-dim"
            >
              {fields.message.length}/{FIELD_LIMITS.message}
            </span>
          </>
        }
      />

      <button
        type="button"
        aria-expanded={showOptional}
        aria-controls="contact-optional-details"
        onClick={() => setShowOptional((visible) => !visible)}
        className="flex min-h-11 w-full items-center justify-between rounded-lg border border-line px-4 py-2.5 text-left text-sm text-gray transition-colors duration-200 hover:border-white/30 hover:text-ivory sm:hidden"
      >
        <span>
          {showOptional
            ? "Hide optional details"
            : "Add company, budget & timeline"}
        </span>
        <span aria-hidden className="font-mono text-base text-accent-soft">
          {showOptional ? "−" : "+"}
        </span>
      </button>

      <div
        id="contact-optional-details"
        className={`${showOptional ? "grid" : "hidden"} gap-5 sm:grid sm:grid-cols-2`}
      >
        <div className="sm:col-span-2">
          <Field
            label="Company"
            htmlFor="contact-company"
            input={
              <input
                id="contact-company"
                name="company"
                type="text"
                value={fields.company}
                onChange={(e) => set("company", e.target.value)}
                autoComplete="organization"
                maxLength={FIELD_LIMITS.company}
                className={inputCls(false)}
              />
            }
          />
        </div>
        <Field
          label="Budget range"
          htmlFor="contact-budget"
          input={
            <Select
              id="contact-budget"
              name="budget"
              value={fields.budget}
              onChange={(v) => set("budget", v)}
              options={BUDGETS}
            />
          }
        />
        <Field
          label="Timeline"
          htmlFor="contact-timeline"
          input={
            <Select
              id="contact-timeline"
              name="timeline"
              value={fields.timeline}
              onChange={(v) => set("timeline", v)}
              options={TIMELINES}
            />
          }
        />
      </div>

      {/* Actions — primary, then clearly-secondary supports */}
      <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:flex-wrap sm:items-center">
        <button
          ref={submitButtonRef}
          type="submit"
          className="group inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-full cta-primary px-7 py-3.5 text-sm font-medium transition-colors duration-300 sm:w-auto"
        >
          Continue in Gmail
          <span aria-hidden className="transition-transform duration-300 group-hover:translate-x-0.5">→</span>
        </button>
        {/* Secondary supports use the drawn-underline text voice so the ivory
            CTA keeps the only pill silhouette in the section. */}
        {status === "idle" && (
          <a
            href={mailto(email, currentDraft.subject, currentDraft.body)}
            className="link-underline inline-flex min-h-11 items-center self-start px-1 py-2 text-sm text-gray transition-colors duration-300 hover:text-ivory sm:self-auto"
          >
            Open default mail app
          </a>
        )}
        <button
          type="button"
          onClick={() => handleCopy(email, "Email copied")}
          className="link-underline inline-flex min-h-11 items-center self-start px-1 py-2 text-sm text-gray transition-colors duration-300 hover:text-ivory sm:self-auto"
        >
          {copied === "Email copied" ? "Email copied ✓" : "Copy email address"}
        </button>
      </div>

      {/* Assertive validation announcement — only present on a failed
          submit, so it interrupts to say the form needs attention. */}
      <p role="alert" className="min-h-0 text-xs leading-relaxed text-magenta">
        {submitError}
      </p>

      {/* Status / live region (never claims the message was sent) */}
      <p role="status" aria-live="polite" className="min-h-5 text-xs leading-relaxed text-gray">
        {status === "idle" &&
          "Submitting opens a pre-filled Gmail compose tab — nothing goes anywhere until you press Send."}
        {status === "prepared" &&
          "Your project brief is ready in Gmail — press Send when it reads right."}
        {status === "error" &&
          "Gmail could not be opened automatically. Your project brief is still ready below."}
        {copied && <span className="ml-1 text-accent-soft">{copied}.</span>}
      </p>

      {/* Compact helper — appears only after a Gmail attempt, dismissible.
          Presented as assistance ("Having trouble?"), not an error. */}
      {status !== "idle" && !helperDismissed && prepared && (
        <div className="settle-enter rounded-xl border border-line bg-soft/60 p-4">
          <div className="flex items-center justify-between">
            <p className="label text-gray">Having trouble?</p>
            <button
              type="button"
              onClick={dismissHelper}
              aria-label="Dismiss helper"
              className="-m-2.5 flex h-11 w-11 items-center justify-center rounded-full text-gray transition-colors hover:bg-white/5 hover:text-ivory"
            >
              <svg width="11" height="11" viewBox="0 0 14 14" aria-hidden>
                <path d="M1 1l12 12M13 1L1 13" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
              </svg>
            </button>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => openGmail(prepared)}
              className="inline-flex min-h-11 items-center rounded-full border border-line px-4 py-2 text-xs text-ivory transition-colors hover:bg-white/5"
            >
              Try Gmail again
            </button>
            <button
              type="button"
              onClick={() => handleCopy(email, "Email copied")}
              className="inline-flex min-h-11 items-center rounded-full border border-line px-4 py-2 text-xs text-ivory transition-colors hover:bg-white/5"
            >
              {copied === "Email copied" ? "Email copied ✓" : "Copy email"}
            </button>
            <button
              type="button"
              onClick={() => handleCopy(`${prepared.subject}\n\n${prepared.body}`, "Message copied")}
              className="inline-flex min-h-11 items-center rounded-full border border-line px-4 py-2 text-xs text-ivory transition-colors hover:bg-white/5"
            >
              {copied === "Message copied" ? "Message copied ✓" : "Copy prepared message"}
            </button>
            <a
              href={mailto(email, prepared.subject, prepared.body)}
              className="inline-flex min-h-11 items-center rounded-full border border-line px-4 py-2 text-xs text-ivory transition-colors hover:bg-white/5"
            >
              Open default mail app
            </a>
          </div>

          {/* Only a genuine error shows the full prepared brief inline. */}
          {status === "error" && (
            <pre
              tabIndex={0}
              aria-label="Prepared project brief"
              className="mt-3 max-h-40 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-ink px-3 py-2 text-xs text-ivory"
            >
              {prepared.subject}
              {"\n\n"}
              {prepared.body}
            </pre>
          )}
        </div>
      )}
    </form>
  );
}

function inputCls(hasError: boolean) {
  return [
    "w-full rounded-lg border bg-soft px-4 py-3 text-sm text-ivory transition-colors duration-200",
    "placeholder:text-gray-dim",
    hasError
      ? "border-magenta focus:border-magenta"
      : "border-line hover:border-white/25 focus:border-accent",
  ].join(" ");
}

function Field({
  label,
  htmlFor,
  input,
  required,
  error,
  errorId,
}: {
  label: string;
  htmlFor: string;
  input: React.ReactNode;
  required?: boolean;
  error?: string;
  errorId?: string;
}) {
  return (
    <div className="form-field block">
      <label htmlFor={htmlFor} className="label mb-2 block">
        {label}
        {required && <span aria-hidden className="text-magenta"> *</span>}
      </label>
      {input}
      {error && (
        <span id={errorId} className="mt-1.5 block text-xs text-magenta">
          {error}
        </span>
      )}
    </div>
  );
}

function Select({
  id,
  name,
  value,
  onChange,
  options,
}: {
  id: string;
  name: string;
  value: string;
  onChange: (v: string) => void;
  options: ReadonlyArray<string>;
}) {
  return (
    <div className="relative">
      <select
        id={id}
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={inputCls(false) + " cursor-pointer appearance-none pr-9"}
      >
        {options.map((o) => (
          <option key={o} value={o} className="bg-soft text-ivory">
            {o}
          </option>
        ))}
      </select>
      <span aria-hidden className="pointer-events-none absolute right-3.5 top-1/2 -translate-y-1/2 text-gray">
        ▾
      </span>
    </div>
  );
}
