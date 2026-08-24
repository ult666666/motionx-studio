# MOTIONX outreach — Continuous Improvement Loop (operating policy v2.9 · engine v2.7)

**Purpose.** Every outreach run should leave the system a little better than it found
it. v2.7 is an **operating-mode addendum** (like v2.6): it adds NO new content gate
by itself. (The deterministic validator engine has since advanced to **2.7** —
Geography & Scope plus Artifact Readback Integrity — with all **170** regression tests
green; those were separate, deliberate engine changes, not this addendum.) It
formalizes a habit:
*observe what slowed the last run down or nearly slipped through, then fix the system
so the next run is faster and safer.*

This file is the **accumulated, living craft** of the system. The running per-run
journal lives OUTSIDE the repo at `~/.motionx-outreach/improvement-log.md` (it may
reference prospects/PII; never commit it). This file holds only the distilled,
non-PII lessons + the loop itself.

## The loop (run at the END of every drafting run, manual or scheduled)

1. **Measure.** Note, for the run: how many drafts were requested vs delivered; how
   many `preflight()` / `batch_preflight()` / `batch_voice_preflight()` iterations it
   took to get to all-PASS; which failure codes recurred; any integrity near-miss
   (e.g. a snippet-sourced email almost used, a stale trigger almost shipped).
2. **Diagnose.** For each recurring failure or near-miss, ask: *was this an authoring
   habit I can pre-empt, a missing heuristic, a gap in a gate, or a tooling problem?*
3. **Improve (pick the smallest safe change that helps):**
   - **Authoring heuristic** → add a one-line rule to "Accumulated authoring heuristics"
     below so the next run writes cleaner first drafts (fewer iterations).
   - **Tooling** → improve `outreach/authoring_lint.py` (a pre-validator lint that
     catches likely failures *before* the formal gates), or add a helper.
   - **Gate change** → only when a real defect pattern is escaping the existing gates.
     Changing `preflight.py` requires updating `tests/test_preflight.py` and keeping
     all tests green; bump the engine version deliberately, never casually.
   - **Doc/policy** → update `tone-guide.md` / `research-thesis-framework.md` / this file.
4. **Log.** Append a dated entry to `~/.motionx-outreach/improvement-log.md`:
   metrics, what was observed, what was changed (or explicitly "logged only, no change
   warranted"). One entry per run, always — even a clean run records "nothing to change."
5. **Never** weaken a gate, lower a threshold, or relax an integrity rule to make a run
   look better. Improvement means higher quality and/or less wasted effort, never a
   lower bar. If a change would trade quality for speed, don't make it.

## Guardrails on self-modification
- Additive and reversible by default. Engine + tests are the safety net: if a change
  touches `preflight.py`, the 170 tests must still pass, or revert.
- No PII or the postal address in any repo file (lint, docs, config). PII stays in
  `~/.motionx-outreach/`.
- A heuristic earns its place only if it traces to a real observed failure/near-miss —
  don't overfit to one prospect or invent rules speculatively.
- Charles can veto or prune any heuristic; this file is craft, not law (SKILL.md is law).

## Accumulated authoring heuristics (distilled from real run failures)
*Each line cites the run that produced it. Follow these while writing the structured
draft so the formal gates pass on the first or second try.*

- **2026-06-22 (45-draft session):** EXCESSIVE_LISTING was the #1 repeat failure. A
  body may contain **at most one** 3-item comma list (e.g. "the pour, the flame, the
  glass"); write any second enumeration with "and" instead of commas. Watch appositives
  ("X, the A and the B, is…") and "calm, a little cinematic," — both can read as a list.
- **2026-06-22:** BATCH_PHRASE_OVERUSE recurred on the inline credibility/positioning
  line. Across a batch, the same 5-word shingle (e.g. "through MOTIONX, my small studio"
  or "I make short product films") may appear in **at most 3** bodies — vary the verb
  (make/shoot/build/run), the studio descriptor, and the price lead-in
  ("my pilot rate is" / "the pilot runs" / "$399 for the pilot").
- **2026-06-22:** BATCH_PARAGRAPH_PATTERN trips when >60% of bodies share a paragraph
  count. With ~15-20 drafts, split roughly half 5-paragraph / half 6-paragraph (leave
  `concise_interpretation` empty on about half).
- **2026-06-22:** MINI_PROPOSAL_OVERBUILT fired on the word "milestone" and on
  multi-channel phrasing ("works on screens and online", "across both locations"). Keep
  the idea to ONE thing in ONE place; avoid "milestone / rollout / deliverables / phase".
- **2026-06-22 (integrity):** prospecting subagents repeatedly hit a transient WebFetch
  outage and returned snippet-sourced emails marked "verified". A snippet is NOT
  verification — **always firsthand-fetch each email-source page and trigger page
  yourself before drafting.** Check `/policies/contact-information` (Shopify) when the
  contact page shows only a form.
- **2026-06-22 (deliverability) — SUPERSEDED 2026-07-02:** the old rule ("full https in
  plaintext reads back clean") stopped holding when the connector changed (~2026-06-30
  21:30–22:15 PDT): it now rewrites ANY url/domain in submitted plaintext into a
  `google.com/url` wrapper at ingest (scheme-less additionally downgrades to `q=http`),
  verified by 4 canary drafts. Current rule (v2.9, SKILL Step 8): keep the full https
  scheme in plaintext AND always supply `htmlBody` via `render_html()` — the composer
  loads the html part, so Charles reviews/sends the clean anchor. Gate the readback with
  `check_readback_artifact(plain, price, html_supplied=True)`; a plaintext-only draft
  with any URL now ships a visible wrapper to recipients (the batch20/21 escape).
- **2026-06-24 (batch10, 20 drafts):** SENTENCE_RHYTHM_ARTIFICIAL (em dashes). The cap is
  **one em dash per body** — counted over the whole greeting→CTA. When the observation,
  interpretation, and idea each want a dash, keep the single dash for the central idea and
  rewrite the others with commas/periods. Also: an appositive list **plus** a trailing
  clause in one sentence easily exceeds the 34-word read-aloud limit — split it in two.
- **2026-06-24 (batch10):** the BATCH_PHRASE_OVERUSE shingle threshold is *fractional*
  (>25%), so for n=20 the exact 5-gram "make short films for" may appear in **at most 5**
  bodies. The inline credibility line is the worst offender — rotate its *structure*, not
  just its nouns: "MOTIONX is the studio behind…", "I run a small studio, MOTIONX, for…",
  "Through MOTIONX I help… show their products", "I film objects the way they deserve".
  Keep the first three words of the positioning line shared by ≤50% of the batch.
- **2026-06-22 (batch #4):** omitting the price drops a body ~10-15 words and can trip
  BODY_TOO_SHORT (<75). When you omit price, pad the central idea with one concrete
  sensory detail so the body still clears ~85 words.
- **2026-06-22 (batch #4):** avoid abbreviations ending in a period (Mt., Co., St., Ave.)
  inside the observation/interpretation — the sentence-splitter treats the "." as a
  sentence end and the extra count can trip DIAGNOSIS_HEAVY. Spell them out ("Mount").
- **2026-06-23 (batch #5):** in a SMALL batch (<12), the BATCH_PHRASE_OVERUSE threshold (>25% of bodies) is tight, so a factual hook several prospects share (e.g. "2026 Good Food Award for the…", or a repeated CTA shape) trips it at just 3 occurrences. Vary the framing verb/structure per draft ("Award with the" vs "Award for the"), not only the neighbouring words.
- **2026-06-22 (batch #4):** a subject starting "A [deliverable] for …" is a banned shape
  (SUBJECT_WEAK). Use a concrete noun phrase ("The reopening, filmed", "Mountain in the
  glass") instead.
- **2026-06-23 (integrity — escaped to send):** an "expansion/new-location" trigger
  reached French Buckets but the third-shop news actually belonged to a similarly-named
  competitor (French Florist), not the recipient business (French Buckets **Flowers**).
  When the premise is a milestone/expansion/opening, **verify the source names the exact
  legal business that owns the recipient's email domain** — cross-check the press/article
  business name against the official site's own name and the domain. A near-name match in
  the same city/category is a red flag, not corroboration. Tie the trigger to the
  recipient before drafting, or reject.
- **2026-06-23 (reconciliation tooling):** email-keyed sent↔lead reconciliation missed
  Ekam because the lead stored `bliss@` while Charles sent to `retreats@` (same domain,
  different mailbox). **Reconcile on the stored Gmail thread ref first, recipient email
  second.** Also: the full reconcile is cheap (3 paged `in:sent` searches in METADATA
  view yield every real `sent_at`) — run it at Step 0, don't defer it; deferral let
  `total_sent_program` sit stale at 9 while 109 had actually sent.
- **2026-06-23 (batch6):** the appositive credibility line "I'm Charles, founder of
  MOTIONX, a small studio for product films" reads as a ≥2-item comma list and trips
  EXCESSIVE_LISTING when the body already has one list. Use a single-appositive form
  ("I'm Charles and I run MOTIONX, a small studio…") instead.
- **2026-06-23 (batch6):** a `central_idea` with a 3-item list embedded in a long clause
  ("…earns a short film: the copper pot, the fruit going in, the jars lined up, cut to…")
  runs 35+ words → SENTENCE_RHYTHM_ARTIFICIAL. Split at the colon into two sentences so
  the one allowed list stays and both sentences fall under 34 words.
- **2026-06-23 (batch6):** "sketch" in a CTA ("I can sketch the idea…") trips
  FREE_WORK_CTA. Use "I can write the idea up in a few lines" / "outline the idea".
- **2026-06-23 (batch7):** when a batch has >3 priced drafts, pre-vary the price lead-in
  ("$399 for the pilot" / "my pilot films are $399" / "the pilot is $399" / "$399 for a
  pilot film") AND the credibility verb (make/shoot/build/run/film) while authoring —
  the credibility+price line is the #1 source of BATCH_PHRASE_OVERUSE (5-gram >3 bodies).
- **2026-06-23 (batch7):** "milestone" trips MINI_PROPOSAL_OVERBUILT. Use "a big one for
  you" / "a real step" instead. Also avoid "still building/growing/ramping" (reads as an
  UNSUPPORTED_INFERENCE about internal condition).
- **2026-06-23 (batch7, integrity):** scouts must state each prospect's COUNTRY with a
  source; re-verify country before booking any non-obviously-US lead. USD pricing does
  not prove US (Canadian DTC brands price in USD). "Nationwide" = US unless widened. A
  Canadian lead (Victory Barber) reached draft creation before being caught and excluded.
- **2026-06-25 (batch11):** the appositive-list trap also fires from the POSITIONING line, not just the inline credibility line. A positioning sentence that opens with a comma-appositive — "Through MOTIONX, my studio, short product films are what I do." or "Filming objects like these, what MOTIONX, my studio, does." — reads to `_list_groups` as a 2-item comma-list ("Through MOTIONX," + "my studio,"). When the central idea already spends the one allowed tricolon, this tips EXCESSIVE_LISTING. Fix: keep the studio as ONE trailing appositive ("…what I do at MOTIONX, my studio.") or drop the comma ("through MOTIONX my studio"); never sandwich "…, my studio, …" mid-sentence in a body that already has a list.
- **2026-06-25 (batch12):** two recurrences worth hardening. (1) The "X, my studio," comma-appositive reads as a decorative list to `_list_groups` ANYWHERE in the body — leading ("Through MOTIONX, my studio, ..."), middle ("...a small studio, MOTIONX, and..."), or inline credibility. It's only safe as a SINGLE TRAILING clause ("...what I do at MOTIONX, my studio."). When the central idea already spends the one allowed tricolon, any second comma-appositive tips EXCESSIVE_LISTING. (2) Omitting BOTH price and `concise_interpretation` drops a body ~12–15 words and routinely lands at 71–73 (< hard min 75). When you omit both, author the central idea ~12–15 words longer up front with one extra concrete clause. `authoring_lint.py` now has a `<75` word-count advisory — RUN `lint_batch(drafts)` before authoring so both are caught pre-gate.
- **2026-06-26 (batch13):** BATCH_PHRASE_OVERUSE can come from a CROSS-SENTENCE seam, not just one repeated line. When several price-shown drafts end the idea on "...is $399." and the next paragraph (positioning) starts "Short product films are...", batch_preflight strips "$399" and sees "is short product films are" repeated. Mitigation now automated: `authoring_lint.py` shingles the price-stripped FULL body (not just the positioning sentence), so the seam is caught pre-gate. Authoring rule: don't pair a "...is $399." idea-ending with a positioning line that opens on a high-frequency stem ("Short product films are...") across many drafts — vary the opener or the price lead-in.
- **2026-06-26 (procedural, reaffirmed):** run `authoring_lint.lint_batch(drafts)` BEFORE preflight every batch. In batch13 it predicted 7/7 first-pass failures, turning what would have been blind iterations into one targeted edit pass.
- **2026-06-29 (batch15):** DIAGNOSIS_HEAVY is a *ratio* gate, not a sentence-count gate — it fires when obs+interpretation exceeds ~30% of total body words, regardless of how many sentences they are. The fix is always: (1) shorten obs to ≤20 words or 1 tight sentence; (2) empty `concise_interpretation` on that draft; (3) expand `central_idea` to carry the reasoning. A populated 1-sentence interpretation still fails if obs+interp together top 35–40% of a short body.
- **2026-06-29 (batch15):** parenthetical em dashes ("X — detail, detail — rest") count as TWO em dashes, not one — the body cap is 1 total. Always replace the parenthetical form with a colon or paired commas ("X: detail, detail; rest" or "X, detail, detail, rest"). Keep the single em dash for the main clause of the central idea where it has the most impact.
- **2026-06-29 (batch15):** for a 12-draft batch, plan paragraph-count distribution BEFORE authoring: e.g. 4-para × 3 + 5-para × 5 + 6-para × 4. The BATCH_PARAGRAPH_PATTERN gate fires when any single count exceeds 60% of the batch (= 7+ of 12 sharing the same count). Setting `concise_interpretation=""` gives 5-para; merging positioning into `central_idea` (set `motionx_positioning_sentence=""`) gives 4-para. Decide which drafts get which structure up front — don't discover uniform 6-para after first preflight.
- **2026-06-29 (batch15):** BATCH_PHRASE_OVERUSE catches 5-grams in the price-CTA zone across the batch. Two identical price framings ("pilot rate for a film", "worth a brief written concept") at 2/12 = 16.7% still triggered. Pre-vary every price lead-in while authoring: "pilot rate is $399", "I work on a pilot basis — $399", "that's $399 for a focused pilot film", "pilot rate for something like this is $399". Likewise for WRITTEN_DIRECTION CTAs: "worth a written concept", "worth a short written concept", "interested in seeing a specific direction in writing first?" — never let the same 5-gram appear in more than 1 draft.
- **2026-06-29 (batch16, recipient certainty):** a personal-named local-part (pablo@, kendall@, dennis@) is NOT by itself sufficient for a first-name greeting — the RECIPIENT gate wants HIGH confidence the named person is the recipient. Use a first-name greeting ONLY when the site also corroborates a sole maker/founder by that name (e.g. JFR Glass About: "Jared F. Rosenacker is a glass artist" → "Hi Jared"; Kehoe solo forge + dennis@ on contact → "Hi Dennis"). When the local-part is a name but there's no founder/sole-maker evidence, default to the brand-team greeting ("Hi [Brand] team,") — it never trips RECIPIENT_UNCERTAIN and reads fine even to a personal mailbox.
- **2026-06-29 (batch16, procedural win):** applying the accumulated heuristics *at authoring time* (not after a failed preflight) produced the first 0-iteration batch — lint clean + 10/10 per-draft + batch + voice all PASS on first run. The discipline that did it: per-draft, plan (a) obs ≤20 words + which fields are empty, (b) paragraph count toward a pre-set batch distribution, (c) a unique price lead-in and credibility-line structure, (d) colons/commas instead of any parenthetical em dash. Author the whole batch against that plan, THEN run lint+gates as confirmation rather than discovery.
- **2026-06-29 (batch17):** the BODY_TOO_SHORT floor (75w) bites specifically on **4-para drafts that BOTH omit price AND use a <6-word CTA** — e.g. obs(19)+merged-idea(50)+cta(5)=74. When a draft has no `concise_interpretation`, no separate `motionx_positioning_sentence` (merged into idea), no price, and a terse CTA, author the central idea to ~52+ words (one extra concrete clause) so the body clears 75. The `authoring_lint` <75 advisory flags it pre-gate — trust it and fix before running preflight.
- **2026-06-29 (batch17, geography):** a clear on-site **"Made in USA"** statement IS sufficient country evidence for the geography gate even when no city is given — set prospect_country=US, geography_evidence="Made in USA (stated on product pages)", and record the city as unconfirmed in the lead row. But when US is only *implied* (e.g. a phone area code or a regional brand word) with no explicit US statement, DROP the prospect rather than guess — don't manufacture geography evidence to hit N.
- **2026-06-29 (batch18, small-batch phrase overuse):** at **n=5** the BATCH_PHRASE_OVERUSE threshold (>25%) means a 5-gram may appear in **at most ONE** body — far tighter than the big batches. The **idea-opener** is the #1 collider: "A short film makes someone…" is the natural phrasing and two drafts land it instantly. Pre-assign each draft a DISTINCT idea-opener before writing — rotate among "A short film makes…", "Thirty seconds that gets…", "It shows…", "A short film of that:…", "A film up close:…", "A short film close on…" — the same discipline already applied to price lead-ins and credibility lines. authoring_lint's price-stripped shingle check predicts it pre-gate; trust it and vary before running preflight.
- **2026-06-30 (batch19, City,State comma trap):** a "City, State," fragment inside the observation reads to `_list_groups`/`_list_count` as a 2-item comma list ("Roan Mountain," + "Tennessee,"), so an observation like "…in Statesboro, Georgia, in small batches…" plus ANY second comma-list in the body (almost always the vivid idea tricolon) tips EXCESSIVE_LISTING. Fix: keep the one allowed list in the central_idea and neutralize the obs — END the obs on the place ("…down in Statesboro, Georgia.") so the state has no trailing comma, or write "in [City] in [State]" (no comma), or split into two sentences ("You make cheese in Perry, New York. Your wheels carry names like…"). Reserve the single comma-list for the idea, never the observation.
- **2026-06-30 (batch19, four-para empty-positioning artifact):** 4-para drafts leave `motionx_positioning_sentence` empty; `batch_preflight`'s exact-positioning-repeat check (max 4) counts identical empty strings, so **5+ four-para drafts in one batch trip BATCH_POSITIONING_REPEAT** on the empty line. Plan the paragraph distribution so **at most 4 drafts are 4-para** (give the 5th a real one-line positioning sentence = 5-para). `authoring_lint` now flags this pre-gate (positioning line repeated in >4 drafts). For a 15-draft batch, 4/6/5 (4-para/5-para/6-para) is a safe split that also clears BATCH_PARAGRAPH_PATTERN.
- **2026-06-30 (batch19, lint hardening):** added two advisory checks to `authoring_lint.py` (engine unchanged, still 2.6): (1) a **>34-word sentence** check that mirrors preflight.MAX_SENTENCE_WORDS (a 36-word central_idea reached preflight this run); (2) the **empty/duplicate-positioning >4** check above. Both are additive/reversible and trace to real batch19 iterations. Keep running `lint_batch` BEFORE preflight.
- **2026-06-30 (batch20, adjective-pair comma trap):** an adjective pair or short qualifier set off by a comma ("a slow, heavy ribbon", "real, cooked-down maple", "dried slowly, not cooked") reads to `_list_groups` as the START of a comma-list, so when the sentence continues with more commas it tips EXCESSIVE_LISTING — and it collides with the one allowed idea tricolon. Fix: either drop the internal comma ("a slow heavy ribbon", "real cooked-down maple") or end the phrase on a period before the next comma-series. Reserve ALL commas in a body for the single intended list; adjective pairs elsewhere should be comma-free.
- **2026-06-30 (batch20, cadence allocator):** use **`outreach/cadence.py`** (`assign(n)`) to lay out a batch's structural diversity BEFORE authoring — it distributes paragraph count (hard-capping 4-para at 4 for the empty-positioning gate), price show/omit, a distinct idea-opener, credibility structure, price lead-in, and CTA category across N drafts, mirroring the gate thresholds. For a large batch (n=32) this took the diversity gates from a guess to deterministic: authoring to the printed worksheet, only 3 iterations (all content-level listing fixes), zero batch-diversity failures. Print the worksheet, author each body to its slot, then run lint+gates as confirmation. Watch two slot hazards: (a) two same-lane prospects can land on the SAME idea-opener (opener index = i % 24) — hand-override one so near-identical lane bodies don't share both lane + opener; (b) never fold credibility into a draft the allocator marked 5/6-para (that silently creates an extra empty positioning line — a mis-authored 5th 4-para tripped BATCH_POSITIONING_REPEAT this run).
- **2026-06-30 (batch20, lint threshold parity):** `authoring_lint`'s positioning-5-gram check was absolute (>3); for a 32-draft batch that over-warned ("the small studio i run" in 5 bodies = 15.6% is fine — the gate fails at >25%). Changed to `max(3, 25%*n)` so it matches `batch_preflight` for large batches while keeping the tight rule for small ones. General rule for lint heuristics: mirror the GATE's fractional thresholds, don't hard-code counts calibrated on 5-15-draft batches.
- **2026-06-30 (batch19, spend-limit resilience — operational):** a large multi-agent Workflow can hit the **account monthly spend limit** mid-run; subagents then fail en masse while **main-loop tools (WebFetch, Bash/Python, the Gmail create_draft connector) keep working** (the limit is on subagent spend, not the main session). Two durable lessons: (a) **discovery + verification are recoverable** — scout/verify subagent outputs persist in the workflow transcript JSONL (`subagents/workflows/<run>/agent-*.jsonl`); on a mid-run failure, salvage them with a local parse (free file reads) rather than re-running, then FIRSTHAND re-verify the final selections in the main loop before drafting. (b) When a workflow filter normalizes a field, **match preflight's own normalization** — batch19's workflow under-reported confirmations (3 of 38) because its US-country regex matched "US"/"USA"/"AMERICA" but not "United States" (the space survived `replace('.','')`); always strip/normalize spaces and reuse the ALLOWED_COUNTRIES set. For a routine 10–15 batch, prefer main-loop verification (or a smaller fan-out) over a 100-agent workflow.
- **2026-07-03 (batch24, concurrent-writer lead-ID collision — integrity):** during a MANUAL run, a **separate scheduled process was writing to `leads.csv`/`outcome-log.csv`/`activity-log.csv` at the same time** and claimed the next lead-ID block (L0361–L0370) for its own new leads. Because this run also assigned IDs from the row-count, both used L0361+ → 10 duplicate lead IDs. Rule: **never assign lead IDs by row-count/`max+1` at write time in a manual run — a concurrent append can claim the same block.** Instead (a) write your rows, then (b) IMMEDIATELY re-read and check for duplicate IDs, and (c) if collided, renumber ONLY your own rows — matched by a **unique per-row key you control (the Gmail draft ref in leads, the unique subject in outcome-log, the draft id in activity-log)**, never by the old lead ID — to sit above the current non-mine max. Verify zero duplicate IDs before finishing. (Do NOT touch the other process's rows.)
- **2026-07-03 (batch24, reconcile also fixes CRM gaps):** Step 0 reconciliation isn't only sent_at stamping — the prior batch (batch23's 5 prospects) had been **SENT + labeled but never written to `leads.csv`/`outcome-log`**. Reconcile-first should cross-check Gmail Sent against `leads.csv` for *missing* leads, not just status drift, and backfill them (SENT, thread ref, outcome row) before drafting new ones.
- **2026-07-03 (batch24, saturation → niche steering):** the "US handmade maker with a visual product" universe is now ~360 contacted domains deep; the obvious lanes (knives/forges, ceramics, candles/soap/perfume, jewelry, coffee/tea, leather, machined pens, chocolate/confection, denim, glassblowing) are **saturated** and re-scouting them mostly returns already-contacted domains. Steer discovery scouts to **under-mined but highly visual niches** (bamboo fly rods, pool cues, umbrellas, telescopes/optics, cymbals/gongs, hand-blown neon, snowshoes, banjos/dulcimers, kites, lawn games, baseball gloves/bats, walking sticks) and hard-dedup each candidate domain against the full leads set *before* investing verify effort. One clean subject-shape collision ("Maple off the lathe" = `X X the X`, matching a recent "Light through the glass") was the run's only gate iteration — reaffirms: run `_subject_shape()` on candidate subjects vs recent-40 AND check intra-batch shape uniqueness before finalizing.
