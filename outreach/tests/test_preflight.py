#!/usr/bin/env python3
"""
MOTIONX outreach — regression tests for preflight.py (validator engine v2.7).

Pure stdlib. Run:  python3 outreach/tests/test_preflight.py
All data is fictional/redacted. The real postal address is NEVER used here — the
footer renderer is exercised with a placeholder only.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import preflight as pf  # noqa: E402

POSTAL_PLACEHOLDER = "[REDACTED — injected only at Gmail draft time]"

_passed = 0
_failed = 0


def check(name, cond):
    global _passed, _failed
    if cond:
        _passed += 1
    else:
        _failed += 1
        print(f"  FAIL: {name}")


def codes(fails):
    return {c for c, _ in fails}


def base():
    """A v2.5-compliant baseline draft (full preflight PASS): human voice, 75-140 words,
    recorded reasoning, non-generic CTA, low modal density."""
    return pf.DraftModel(
        prospect_name="Acme Candles",
        recipient_email="hello@acmecandles.example",
        recipient_type="generic",
        recipient_confidence="LOW",
        greeting="Hi Acme Candles team,",
        verified_observation="Your winter collection went up this week, and the scent names set a mood before you even smell anything.",
        concise_interpretation="",
        central_idea="What I keep picturing is a short film that leans into that warmth. Less a product demo, more the first pour and the wax catching light, like lighting one on a cold night.",
        motionx_positioning_sentence="I make short product films through MOTIONX, and a pilot is $399 if it helps to start small.",
        cta="Do the winter scents feel like the right place to try it?",
        selected_offer="Product Film",
        optional_price=399,
        subject="Winter scents on film",
        human_reaction="the scent names do mood work on their own",
        why_this_idea="the names already sell a feeling, so the film should too",
        prospect_specific_connection="ties the winter scent names to a warmth-first film",
        brand_noun_removal_result="DISTINCT",
        conversational_read_result="PASS",
    )


def med_base():
    d = base()
    d.prospect_name = "Glow Aesthetics"
    d.recipient_email = "info@glowaesthetics.example"
    d.greeting = "Hi Glow Aesthetics team,"
    d.claims_sensitive = True
    d.official_claim_wording = "no needles, no downtime"
    d.official_claim_url = "https://glowaesthetics.example/service"
    d.subject = "Treatment launch page"
    d.selected_offer = "Motion-First Website"
    d.optional_price = 699
    d.central_idea = "I think a calm treatment-room film and the offer on one page could help the launch."
    d.motionx_positioning_sentence = "I run MOTIONX, a motion-first studio; my pilot rate for a page like this is $699."
    return d


# ── Signature ──────────────────────────────────────────────────────────────────
check("sig canonical PASS", codes(pf.check_signature(pf.CANONICAL_SIGNATURE)) == set())
check("sig +sender-email FAIL",
      "SIGNATURE_DRIFT" in codes(pf.check_signature(pf.CANONICAL_SIGNATURE + "\ncharles@madebymotionx.com")))
check("sig +Available Worldwide FAIL",
      "SIGNATURE_DRIFT" in codes(pf.check_signature(pf.CANONICAL_SIGNATURE + "\nAvailable Worldwide")))
check("sig +Website: FAIL",
      "SIGNATURE_DRIFT" in codes(pf.check_signature(pf.CANONICAL_SIGNATURE.replace("madebymotionx.com", "Website: madebymotionx.com"))))
check("renderer returns canonical sig", pf.render_signature() == pf.CANONICAL_SIGNATURE)

# ── Links ──────────────────────────────────────────────────────────────────────
check("link https PASS", codes(pf.check_links("see https://madebymotionx.com")) == set())
check("link plain-domain PASS", codes(pf.check_links("madebymotionx.com")) == set())
check("link google redirect http FAIL",
      "REDIRECT_URL" in codes(pf.check_links("https://www.google.com/url?q=http://madebymotionx.com&source=gmail")))
check("link shortener FAIL", "REDIRECT_URL" in codes(pf.check_links("bit.ly/abc")))
check("gmail readback html anchor q=https PASS",
      codes(pf.check_gmail_readback_link('<a href="https://www.google.com/url?q=https://madebymotionx.com&source=gmail">madebymotionx.com</a>', is_plaintext=False)) == set())
check("gmail readback q=http FAIL",
      "REDIRECT_URL" in codes(pf.check_gmail_readback_link('href="https://www.google.com/url?q=http://madebymotionx.com"', is_plaintext=False)))

# ── Recipient certainty / greeting ──────────────────────────────────────────────
conf, rtype = pf.resolve_recipient("amber@brandexample.example", True)
check("personal+evidence -> HIGH", conf == "HIGH" and rtype == "personal")
conf2, _ = pf.resolve_recipient("info@brandexample.example", False)
check("generic -> LOW", conf2 == "LOW")
d = base(); d.recipient_confidence = "HIGH"; d.greeting = "Hi Amber,"
check("named greeting + HIGH PASS", codes(pf.check_greeting(d)) == set())
check("team greeting PASS", codes(pf.check_greeting(base())) == set())
d = base(); d.greeting = "Hi Anisa,"; d.recipient_confidence = "LOW"
check("named greeting + LOW no-evidence FAIL", "RECIPIENT_UNCERTAIN" in codes(pf.check_greeting(d)))
d = base(); d.greeting = "Hi Jordan,"; d.recipient_confidence = "MEDIUM"; d.greeting_evidence = "bio page: Jordan personally answers this inbox"
check("named greeting + MEDIUM + evidence PASS", codes(pf.check_greeting(d)) == set())

# ── CTA (free-work guard) ───────────────────────────────────────────────────────
check("CTA written-concept PASS", codes(pf.check_free_work_cta("Would a short written concept be useful?")) == set())
check("CTA quick-convo PASS", codes(pf.check_free_work_cta("Worth a quick conversation?")) == set())
check("CTA sketch FAIL", "FREE_WORK_CTA" in codes(pf.check_free_work_cta("Want me to sketch a rough direction?")))
check("CTA free sample FAIL", "FREE_WORK_CTA" in codes(pf.check_free_work_cta("I can make a free sample.")))
check("CTA mock up FAIL", "FREE_WORK_CTA" in codes(pf.check_free_work_cta("Want me to mock this up?")))
check("CTA rough visual direction FAIL", "FREE_WORK_CTA" in codes(pf.check_free_work_cta("Open to seeing a rough visual direction?")))

# ── Medical / regulated ─────────────────────────────────────────────────────────
d = med_base(); d.central_idea = "A light motion showing the treatment experience could open the page."
check("medical experience PASS", codes(pf.check_medical(d)) == set())
d = med_base(); d.central_idea = "Lead with the verified no needles, no downtime positioning."
check("medical no-needles PASS", codes(pf.check_medical(d)) == set())
d = med_base(); d.central_idea = "A short motion showing how the treatment tightens the skin."
check("medical mechanism FAIL", "MEDICAL_CLAIM_UNSUPPORTED" in codes(pf.check_medical(d)))
d = med_base(); d.central_idea = "Demonstrating what happens beneath the skin during the session."
check("medical beneath-skin FAIL", "MEDICAL_CLAIM_UNSUPPORTED" in codes(pf.check_medical(d)))
d = med_base(); d.central_idea = "Promise guaranteed results from the first treatment."
check("medical guaranteed FAIL", "MEDICAL_CLAIM_UNSUPPORTED" in codes(pf.check_medical(d)))
d = med_base(); d.official_claim_url = ""; d.central_idea = "A calm room film."
check("medical missing source FAIL", "MEDICAL_CLAIM_UNSUPPORTED" in codes(pf.check_medical(d)))

# ── Language gate ───────────────────────────────────────────────────────────────
for phrase in ["real early-adopter offer", "feel of-a-piece", "could carry it",
               "compelling visual narrative", "unlock your brand's potential"]:
    check(f"AI phrase FAIL: {phrase}", "AI_LANGUAGE" in codes(pf.check_ai_language(phrase)))

# ── Offer / price ───────────────────────────────────────────────────────────────
check("one Product Film $399 PASS", codes(pf.check_offer_and_price(base())) == set())
d = base(); d.selected_offer = "Motion-First Website"; d.optional_price = 699
d.motionx_positioning_sentence = "I run MOTIONX, a motion-first studio; my pilot rate for a page like this is $699."
check("one Motion-First Website $699 PASS", codes(pf.check_offer_and_price(d)) == set())
d = base(); d.central_idea = "We could do a Product Film and a Motion-First Website together."
check("film+website competing FAIL", "MULTIPLE_OFFERS" in codes(pf.check_offer_and_price(d)))
d = base(); d.central_idea = "Either at $399 or $699 depending on scope."; d.optional_price = None
check("multiple prices FAIL", "PRICE_MISMATCH" in codes(pf.check_offer_and_price(d)))
d = base(); d.optional_price = 699  # wrong price for Product Film
d.motionx_positioning_sentence = "I run MOTIONX, a motion-first studio; my pilot rate for this is $699."
check("wrong price FAIL", "PRICE_MISMATCH" in codes(pf.check_offer_and_price(d)))

# ── State transitions ───────────────────────────────────────────────────────────
check("draft_created not-sent PASS", codes(pf.validate_state_transition("draft_created", {"status": "draft_created"})) == set())
check("draft starts follow-up FAIL", "STATE_INVALID" in codes(pf.validate_state_transition("draft_created", {"status": "draft_created", "follow_up_due": True})))
check("draft logged sent FAIL", "STATE_INVALID" in codes(pf.validate_state_transition("draft_created", {"status": "sent"})))

# ── Body length ─────────────────────────────────────────────────────────────────
check("body 75-140 PASS", pf.check_word_count(base())[1] == [])
d = base(); d.verified_observation = "Nice site."; d.concise_interpretation = "Good."
d.central_idea = "A film."; d.motionx_positioning_sentence = "MOTIONX here."; d.cta = "Useful?"
check("body too short FAIL", "BODY_TOO_SHORT" in codes(pf.check_word_count(d)[1]))
d = base(); d.central_idea = ("I think a short film of the pour and the finished jars could anchor the "
                             "collection page and your posts " * 8)
check("body too long FAIL", "BODY_TOO_LONG" in codes(pf.check_word_count(d)[1]))

# ── Claim scope & evidence precision (v2.3.1) ────────────────────────────────────
# Scoped/limited phrasing PASSES at OBSERVED_ON_PAGE
check("scope page-led PASS", pf.scope_violations("The collection page is currently led by still photography.") == [])
check("scope didn't-see-on-page PASS", pf.scope_violations("I didn't see a dedicated product film on that page.") == [])
check("scope mentioned-briefly PASS", pf.scope_violations("The opening is mentioned briefly on the homepage.") == [])
check("scope SD mentioned-briefly PASS", pf.scope_violations("The San Diego opening is currently mentioned briefly on the homepage.") == [])
check("scope combined page PASS", pf.scope_violations("The collection page is currently led by still photography, and I didn't see a dedicated product film on that page.") == [])
# Absolute claims PASS only with recorded matching evidence
check("scope site-wide w/ routes PASS", pf.scope_violations("The official website does not list a dedicated location page.", "CHECKED_RELEVANT_SITE_ROUTES") == [])
check("scope cross-channel w/ evidence PASS", pf.scope_violations("No dedicated product film appears across the official website and Instagram.", "VERIFIED_CROSS_CHANNEL", ["official_website", "instagram"]) == [])
# Absolute claims FAIL without matching evidence
check("scope no-film line FAIL", "ABSENCE_EVIDENCE_INSUFFICIENT" in codes(pf.scope_violations("There is no film for the line yet.")))
check("scope no-page-of-own FAIL", "CLAIM_SCOPE_UNSUPPORTED" in codes(pf.scope_violations("The studio has no page of its own.")))
check("scope only-still FAIL", "CHANNEL_SCOPE_OVERREACH" in codes(pf.scope_violations("The brand uses only still photography.")))
check("scope site-wide w/o routes FAIL", "CLAIM_SCOPE_UNSUPPORTED" in codes(pf.scope_violations("The official website does not list a dedicated location page.")))
check("scope cross-channel w/o evidence FAIL", "ABSENCE_EVIDENCE_INSUFFICIENT" in codes(pf.scope_violations("No dedicated product film appears across the official website and Instagram.")))
# Original Drenched / Facial Lounge sentences as regression fixtures
check("regress Drenched original FAIL", "CLAIM_SCOPE_UNSUPPORTED" in codes(pf.scope_violations("Right now the new studio is a single line on the homepage, with no page of its own to gather interest before opening.")))
check("regress Facial original FAIL", len(pf.scope_violations("It's carried entirely by still photography, with no film for the line yet.")) >= 1)
check("regress Drenched corrected PASS", pf.scope_violations("The San Diego opening is currently mentioned briefly on the homepage.") == [])
check("regress Facial corrected PASS", pf.scope_violations("The collection page is currently led by still photography, and I didn't see a dedicated product film on that page.") == [])

# ── Full preflight ──────────────────────────────────────────────────────────────
res = pf.preflight(base(), {"policy_version": "2.7"})
check("full preflight baseline PASS", res["status"] == "PASS")
check("baseline reports word count", 75 <= res["final_body_word_count"] <= 140)
bad = base(); bad.greeting = "Hi Bob,"; bad.recipient_confidence = "LOW"
bad.cta = "Want me to sketch a rough direction?"; bad.signature = pf.CANONICAL_SIGNATURE + "\nAvailable Worldwide"
res2 = pf.preflight(bad, {"policy_version": "2.7", "suppressed": True})
check("bad draft FAILs", res2["status"] == "FAIL")
check("bad draft codes incl RECIPIENT_UNCERTAIN", "RECIPIENT_UNCERTAIN" in res2["failure_codes"])
check("bad draft codes incl FREE_WORK_CTA", "FREE_WORK_CTA" in res2["failure_codes"])
check("bad draft codes incl SIGNATURE_DRIFT", "SIGNATURE_DRIFT" in res2["failure_codes"])
check("bad draft codes incl PREVIOUSLY_CONTACTED", "PREVIOUSLY_CONTACTED" in res2["failure_codes"])

# ── Footer renderer uses placeholder; no real address in this file ──────────────
foot = pf.render_footer(POSTAL_PLACEHOLDER)
check("footer has opt-out", "no thanks" in foot)
check("footer uses placeholder", "REDACTED" in foot)
check("no real street address in test file", not re.search(r"\b\d{3,5}\s+\w+\s+(Ave|Avenue|St|Street|Rd|Road|Blvd)\b", open(__file__).read()))

# ══════════════════════════════════════════════════════════════════════════════
# v2.4 — Humanization, Batch Diversity & Offer Fit
# ══════════════════════════════════════════════════════════════════════════════

# ── Negative framing (prospect-defensive language) ──────────────────────────────
d = base(); d.verified_observation = "Your current site is a clean, standard template."
check("neg-framing standard template FAIL", "NEGATIVE_FRAMING" in codes(pf.check_negative_framing(d)))
d = base(); d.verified_observation = "Your Enchanted Glow line runs on a booking template right now."
check("neg-framing booking template FAIL", "NEGATIVE_FRAMING" in codes(pf.check_negative_framing(d)))
d = base(); d.concise_interpretation = "A dedicated page reads stronger than that."
check("neg-framing reads stronger FAIL", "NEGATIVE_FRAMING" in codes(pf.check_negative_framing(d)))
d = base(); d.verified_observation = "The summer special currently leads into the existing booking flow."
check("neg-framing respectful PASS", codes(pf.check_negative_framing(d)) == set())

# ── Unsupported business inference ──────────────────────────────────────────────
d = base(); d.concise_interpretation = "Those offers read like a newer studio still filling its first members."
check("inference newer-studio FAIL", "UNSUPPORTED_INFERENCE" in codes(pf.check_business_inference(d)))
d = base(); d.concise_interpretation = "They are probably trying to build initial demand."
check("inference build-demand FAIL", "UNSUPPORTED_INFERENCE" in codes(pf.check_business_inference(d)))
d = base(); d.verified_observation = "The homepage currently features two introductory offers."
check("inference observable PASS", codes(pf.check_business_inference(d)) == set())

# ── Existing-asset contradiction ────────────────────────────────────────────────
d = base(); d.existing_assets = ["memberships_page"]; d.proposed_asset = "memberships_page"
check("existing-asset proposed==existing FAIL", "PROPOSED_ASSET_ALREADY_EXISTS" in codes(pf.check_existing_asset(d)))
d = base(); d.existing_assets = ["memberships_page"]
d.central_idea = "A single membership page could give the program a home of its own."
check("existing-asset home-of-its-own FAIL", "PROPOSED_ASSET_ALREADY_EXISTS" in codes(pf.check_existing_asset(d)))
d = base(); d.existing_assets = ["memberships_page"]
d.central_idea = "Restructuring the existing memberships page into a clear tier comparison could help."
check("existing-asset restructure PASS", codes(pf.check_existing_asset(d)) == set())
d = base()  # no existing assets recorded
d.central_idea = "A page of its own could anchor the launch."
check("existing-asset no-existing PASS", codes(pf.check_existing_asset(d)) == set())

# ── Currentness / seasonal relevance ────────────────────────────────────────────
d = base(); d.currentness_status = "ENDED"
check("currentness ended FAIL", "STALE_OPPORTUNITY" in codes(pf.check_currentness(d)))
d = base(); d.currentness_status = "STALE_PAGE_ONLY"
check("currentness stale-page FAIL", "STALE_OPPORTUNITY" in codes(pf.check_currentness(d)))
d = base(); d.currentness_status = "STALE_PAGE_ONLY"; d.reframed_as_evergreen = True
check("currentness stale-but-reframed PASS", codes(pf.check_currentness(d)) == set())
d = base(); d.product_availability = "UNAVAILABLE"
check("currentness product-unavailable FAIL", "PRODUCT_UNAVAILABLE" in codes(pf.check_currentness(d)))
d = base(); d.promotion_status = "ENDED"
check("currentness promo-ended FAIL", "PROMOTION_ENDED" in codes(pf.check_currentness(d)))
d = base(); d.currentness_status = "UNCLEAR"
check("currentness unclear FAIL", "CURRENTNESS_UNVERIFIED" in codes(pf.check_currentness(d)))
d = base(); d.currentness_status = "CURRENT"
check("currentness current PASS", codes(pf.check_currentness(d)) == set())
d = base(); d.currentness_status = "EVERGREEN"
check("currentness evergreen PASS", codes(pf.check_currentness(d)) == set())

# ── Offer fit (positioning matches offer + prospect type) ───────────────────────
d = base(); d.prospect_kind = "lighting_studio"
d.motionx_positioning_sentence = "I run MOTIONX, a founder-led studio making product films. My pilot rate is $399."
check("offer-fit product-film for architecture FAIL", "OFFER_MISMATCH" in codes(pf.check_offer_fit(d)))
d = base(); d.prospect_kind = "photographer"
d.motionx_positioning_sentence = "I run MOTIONX, a founder-led studio making short brand and capability films. My pilot rate is $399."
check("offer-fit brand-film for photographer PASS", codes(pf.check_offer_fit(d)) == set())
d = base(); d.selected_offer = "Product Film"
d.motionx_positioning_sentence = "I run MOTIONX; I build product films and launch systems. My pilot rate is $399."
check("offer-fit launch-systems in product-film pitch FAIL", "OFFER_MISMATCH" in codes(pf.check_offer_fit(d)))
d = base()
check("offer-fit product-brand product-film PASS", codes(pf.check_offer_fit(d)) == set())

# ── Batch preflight: builders ───────────────────────────────────────────────────
_B_SUBJECTS = ["Citrus bloom honey", "Koji microlot format", "Wheel thrown dinnerware",
    "Fresh harvest pressing", "Checkmate swim fabric", "Rope kit collab", "Titanium frame light",
    "Melt pool macro", "Lighting awards reel", "Analog to digital", "Reef planting story",
    "Injectable specials hub", "Barre intro flow", "Pandan tea bloom", "Reformer start sequence",
    "Summer glow campaign", "Lash nap closeups", "Membership tiers clear", "Stone setting macro",
    "Volcano scent pour"]
_B_POS = [
    "I run MOTIONX, a founder-led studio making short product films. My pilot rate for this is $399.",
    "I lead MOTIONX, where I make focused product films for independent brands; pilot rate is $399.",
    "MOTIONX is my one-person studio for product storytelling, and the pilot rate is $399.",
    "I'm the founder of MOTIONX; for a piece like this the pilot rate is $399.",
    "At MOTIONX I produce short brand films, with a $399 pilot rate.",
]
_B_CTA = ["Would a brief written direction be useful?", "Open to a short conversation about it?",
    "Would it help if I outlined the scope?", "Is this something you're considering for the launch?",
    "Worth discussing while it's current?"]
_B_OBS = [
    "Your spring citrus-bloom honey is a dated, single-harvest drop.",
    "Your products page rotates new single-origin microlots often.",
    "You release new ceramics every month from a two-person workshop.",
    "Your homepage leads with the fresh-pressed new harvest batch.",
    "Your summer swim is cut and sewn in your own LA workroom.",
    "Your current collaboration drops bright DIY rope kits.",
    "Your eyewear line adds fresh styles every month.",
    "Your summer candle set just went live with three new scents.",
    "Your studio just earned nine award nominations this spring.",
    "You shoot weddings on both film and digital, booking two years out.",
    "Your suits fund a coral planted for each one sold.",
    "Your specials page rotates several limited new-client offers.",
    "Your homepage opens with a one-month intro across yoga and barre.",
    "Your reserve blends draw on Southeast-Asian flavors year round.",
    "Your homepage stacks several first-step pricing offers together.",
    "Your homepage runs a seasonal half-off treatment promotion.",
    "Your studio leans into a calm, plush treatment-room feel.",
    "Your memberships page lists three tiers at two prices.",
    "Your latest fine-jewelry drop layers gold and stones.",
    "Your tropical scent leads the summer collection right now.",
]
_B_IDEA = [
    "A film tracing the orchard bloom to the jar would ride beside that limited batch.",
    "A repeatable shoot per release would keep each drop looking consistent.",
    "Short clips of the wheel and glaze would suit that monthly rhythm.",
    "A slow pour of the green-gold oil would mark the season cleanly.",
    "Macro fabric and the made-here detail would anchor the launch.",
    "Stop-motion of a kit coming together would match the playful colorways.",
    "Raking light across the titanium edges would read across each release.",
    "A first-melt close-up would tie the trio together for summer.",
    "A capability film of your light-led spaces would mark the moment.",
    "A brand film blending grain and clean frames would anchor inquiries.",
    "A piece from weave to reef would carry the cause without overstating it.",
    "A motion-led hub would let those offers refresh in one clean place.",
    "A calm, breath-paced page would turn the trial into signups.",
    "A leaf-bloom film would suit those evergreen, distinctive teas.",
    "A motion sequence would order those steps into one clear start.",
    "A focused destination would complement the booking you already use.",
    "Close-up sets and room atmosphere would extend the video you make.",
    "A clearer side-by-side comparison would separate the matching prices.",
    "A macro piece catching the light would carry it across product pages.",
    "A warm pour and flame would set the mood for the drop.",
]


def diverse_batch(n=20):
    out = []
    for i in range(n):
        d = base()
        d.prospect_name = f"Biz{i:02d}"
        d.greeting = f"Hi Biz{i:02d} team,"
        d.subject = _B_SUBJECTS[i % len(_B_SUBJECTS)]
        d.motionx_positioning_sentence = _B_POS[i % len(_B_POS)]
        d.cta = _B_CTA[i % len(_B_CTA)]
        d.verified_observation = _B_OBS[i % len(_B_OBS)]
        d.concise_interpretation = ""
        d.central_idea = _B_IDEA[i % len(_B_IDEA)]
        out.append(d)
    return out


# ── Batch preflight: PASS on a genuinely varied 20-draft batch ──────────────────
rb = pf.batch_preflight(diverse_batch())
check("batch diverse PASS", rb["status"] == "PASS")
check("batch diverse no failure codes", rb["failure_codes"] == [])

# ── Batch: subject diversity ────────────────────────────────────────────────────
b = diverse_batch()
for i in range(6):
    b[i].subject = f"{['Honey','Koji','Clay','Oil','Swim','Frame'][i]} on film"
check("batch 6x 'on film' FAIL", "BATCH_SUBJECT_PATTERN" in pf.batch_preflight(b)["failure_codes"])
b = diverse_batch()
for i in range(6):
    b[i].subject = f"{['Honey','Koji','Clay','Oil','Swim','Frame'][i]} in motion"
check("batch 6x 'in motion' FAIL", "BATCH_SUBJECT_PATTERN" in pf.batch_preflight(b)["failure_codes"])
b = diverse_batch()
for i in range(5):
    b[i].subject = f"One page for {['memberships','specials','bookings','launches','summer'][i]}"
check("batch 5x 'One page for' shape FAIL", "BATCH_SUBJECT_SHAPE" in pf.batch_preflight(b)["failure_codes"])
b = diverse_batch(); b[1].subject = b[0].subject
check("batch duplicate subject FAIL", "BATCH_SUBJECT_DUPLICATE" in pf.batch_preflight(b)["failure_codes"])
b = diverse_batch(); b[3].subject = "Rise, in motion"
check("batch comma gimmick FLAG", any("BATCH_SUBJECT_PUNCT" in f for f in pf.batch_preflight(b)["flags"]))

# ── Batch: CTA diversity ────────────────────────────────────────────────────────
b = diverse_batch()
for i in range(10):
    b[i].cta = "Would a short written concept be useful?"
check("batch CTA 10x same FAIL", "BATCH_CTA_REPEAT" in pf.batch_preflight(b)["failure_codes"])
check("batch CTA varied PASS", "BATCH_CTA_REPEAT" not in pf.batch_preflight(diverse_batch())["failure_codes"])

# ── Batch: positioning diversity ────────────────────────────────────────────────
b = diverse_batch()
for i in range(15):
    b[i].motionx_positioning_sentence = "I run MOTIONX, a founder-led studio creating product films. My pilot rate for this is $399."
check("batch positioning 15x same FAIL", "BATCH_POSITIONING_REPEAT" in pf.batch_preflight(b)["failure_codes"])

# ── Batch: repeated-phrase frequency ────────────────────────────────────────────
b = diverse_batch()
for i in range(9):
    b[i].central_idea = "This is a natural fit for a short film."
check("batch 'a natural fit' 9x FAIL", "BATCH_PHRASE_OVERUSE" in pf.batch_preflight(b)["failure_codes"])
b = diverse_batch()
for i in range(8):
    b[i].verified_observation = "That release is a good moment for a film."
check("batch 'a good moment' 8x FAIL", "BATCH_PHRASE_OVERUSE" in pf.batch_preflight(b)["failure_codes"])
b = diverse_batch()
for i in range(7):
    b[i].central_idea = "A short film could carry the launch across your pages."
check("batch 'could carry' 7x FAIL", "BATCH_PHRASE_OVERUSE" in pf.batch_preflight(b)["failure_codes"])
# signature/footer never enter batch analysis (bodies are personalized_body only):
check("batch ignores canonical signature repetition PASS",
      pf.batch_preflight(diverse_batch())["status"] == "PASS")

# ── Batch: near-duplicate bodies (nouns swapped) ────────────────────────────────
b = diverse_batch()
tmpl_o = "Your new summer collection just went live on the homepage this week."
tmpl_i = "A short product film of the {X} could anchor the collection page and your posts."
b[0].verified_observation = tmpl_o; b[0].central_idea = tmpl_i.format(X="candles")
b[1].verified_observation = tmpl_o; b[1].central_idea = tmpl_i.format(X="bottles")
b[0].cta = b[1].cta = _B_CTA[0]
b[0].motionx_positioning_sentence = b[1].motionx_positioning_sentence = _B_POS[0]
check("batch near-duplicate bodies FAIL", "BATCH_NEAR_DUPLICATE" in pf.batch_preflight(b)["failure_codes"])
check("batch distinct bodies PASS", "BATCH_NEAR_DUPLICATE" not in pf.batch_preflight(diverse_batch())["failure_codes"])

# ── Batch: empty batch is a no-op PASS ──────────────────────────────────────────
check("batch empty PASS", pf.batch_preflight([])["status"] == "PASS")

# ── Policy version is 2.7 ───────────────────────────────────────────────────────
check("policy version 2.7", pf.POLICY_VERSION == "2.7")

# ══════════════════════════════════════════════════════════════════════════════
# v2.5 — Human Voice & Conversational Credibility
# ══════════════════════════════════════════════════════════════════════════════

# ── Length & completeness (reasoning, not just word count) ──────────────────────
thin = base()
thin.verified_observation = "Your new collection is live on the homepage."
thin.central_idea = "A short film could showcase the products nicely across your channels."
thin.motionx_positioning_sentence = "I run MOTIONX. My pilot rate is $399."
thin.cta = "Worth a quick chat?"
thin.human_reaction = thin.why_this_idea = thin.prospect_specific_connection = ""
check("v2.5 thin email (no reasoning) FAIL", pf.preflight(thin, {"policy_version": "2.7"})["status"] == "FAIL")
check("v2.5 thin email is too short", pf.count_words(pf.personalized_body(thin)) < 75)
check("v2.5 88-word reasoned email PASS", pf.preflight(base(), {"policy_version": "2.7"})["status"] == "PASS")
complex_ok = base()
complex_ok.prospect_kind = "med_spa"; complex_ok.selected_offer = "Motion-First Website"; complex_ok.optional_price = 699
complex_ok.claims_sensitive = True; complex_ok.official_claim_url = "https://x.example/memberships"
complex_ok.existing_assets = ["memberships_page"]
complex_ok.verified_observation = "Your memberships page lists three tiers, and two of them sit at the same monthly price."
complex_ok.central_idea = ("The thing that made me write is those two same-priced tiers. Rather than a new page, I would rework the page you already have into a side-by-side that makes the difference clear, with one join-or-ask step and a little motion to guide the eye.")
complex_ok.motionx_positioning_sentence = "I build focused pages through MOTIONX, and a pilot is $699."
complex_ok.cta = "Would tightening that page be useful, or is the current layout doing fine?"
complex_ok.human_reaction = "couldn't tell the two tiers apart"; complex_ok.why_this_idea = "same price, unclear difference"
complex_ok.subject = "Clarifying the tiers"
_co = pf.preflight(complex_ok, {"policy_version": "2.7"})
check("v2.5 ~120-word complex email PASS", _co["status"] == "PASS")
check("v2.5 complex email within 75-140", 75 <= _co["final_body_word_count"] <= 140)
padded = base()
padded.central_idea = ("A short film could showcase your products and elevate your brand and amplify your reach " * 6)
check("v2.5 padded 140+ email FAIL", "BODY_TOO_LONG" in pf.preflight(padded, {"policy_version": "2.7"})["failure_codes"])

# ── AI language / abstract terms ────────────────────────────────────────────────
d = base(); d.central_idea = "We would create a cohesive visual identity across your digital ecosystem."
check("v2.5 cohesive-visual-identity FAIL", "AI_PHRASE_PATTERN" in codes(pf.check_ai_phrase_patterns(d)))
d = base(); d.central_idea = "A cinematic destination that elevates the customer journey."
check("v2.5 cinematic-destination FAIL", "AI_PHRASE_PATTERN" in codes(pf.check_ai_phrase_patterns(d)))
d = base(); d.central_idea = "The film would carry the story across the collection page and social."
check("v2.5 carry-the-story FAIL", "AI_PHRASE_PATTERN" in codes(pf.check_ai_phrase_patterns(d)))
d = base(); d.central_idea = "A short film could give the line its own visual identity and a cohesive system."
check("v2.5 abstract overuse FAIL", "ABSTRACT_LANGUAGE_OVERUSE" in codes(pf.check_abstract_language(d)))
check("v2.5 plain language PASS", codes(pf.check_ai_phrase_patterns(base())) == set() and codes(pf.check_abstract_language(base())) == set())

# ── Personalization depth + brand-noun removal ──────────────────────────────────
d = base(); d.human_reaction = d.why_this_idea = d.prospect_specific_connection = ""
check("v2.5 fact-only personalization FAIL", "PERSONALIZATION_FACT_ONLY" in codes(pf.check_personalization_depth(d)))
d = base(); d.brand_noun_removal_result = "GENERIC"
check("v2.5 brand-noun-removal GENERIC FAIL", "GENERIC_WITH_SPECIFIC_NOUNS" in codes(pf.check_brand_noun_removal(d)))
d = base()
d.why_this_idea = "the collection changes monthly, so I'd treat the format as repeatable rather than one film"
d.prospect_specific_connection = "monthly drops -> repeatable production format"
check("v2.5 monthly->repeatable depth PASS", codes(pf.check_personalization_depth(d)) == set() and codes(pf.check_brand_noun_removal(d)) == set())

# ── Modal overuse ───────────────────────────────────────────────────────────────
d = base(); d.central_idea = "This could work, and it would help, and it might land, and we could try, and you could see."
check("v2.5 five modals FAIL", "MODAL_VERB_OVERUSE" in codes(pf.check_modal_overuse(d)))
check("v2.5 one-two modals PASS", codes(pf.check_modal_overuse(base())) == set())

# ── Mini-proposal overbuild ─────────────────────────────────────────────────────
d = base(); d.central_idea = ("Here is the plan: a five-shot sequence, a placement plan for each channel, a full channel rollout, and the deliverables broken into phase 1 and phase 2.")
check("v2.5 mini-proposal FAIL", "MINI_PROPOSAL_OVERBUILT" in codes(pf.check_mini_proposal(d)))
check("v2.5 one-or-two details PASS", codes(pf.check_mini_proposal(base())) == set())

# ── Excessive listing ───────────────────────────────────────────────────────────
d = base()
d.verified_observation = "The pour, the melt, and the glow all stand out."
d.central_idea = "A film of the wax, the flame, and the smoke could open it."
check("v2.5 two triple-lists FAIL", "EXCESSIVE_LISTING" in codes(pf.check_excessive_listing(d)))
check("v2.5 single list PASS", codes(pf.check_excessive_listing(base())) == set())

# ── Credibility boilerplate ─────────────────────────────────────────────────────
d = base(); d.motionx_positioning_sentence = "I run MOTIONX, a founder-led studio building motion-first pages. My pilot rate is $699."
check("v2.5 credibility boilerplate FAIL", "CREDIBILITY_BOILERPLATE" in codes(pf.check_credibility_boilerplate(d)))
check("v2.5 context-credibility PASS", codes(pf.check_credibility_boilerplate(base())) == set())

# ── CTA generic ─────────────────────────────────────────────────────────────────
d = base(); d.cta = "Would a short written concept be useful?"
check("v2.5 generic CTA FAIL", "CTA_GENERIC" in codes(pf.check_cta_generic(d)))
check("v2.5 natural CTA PASS", codes(pf.check_cta_generic(base())) == set())

# ── Read-aloud ──────────────────────────────────────────────────────────────────
d = base(); d.central_idea = ("This is a single sentence that simply keeps going and going with clause after clause after clause until it is honestly far too long for anyone to ever say comfortably out loud in just one calm breath at all.")
check("v2.5 over-long sentence FAIL", "SENTENCE_RHYTHM_ARTIFICIAL" in codes(pf.check_read_aloud(d)))
d = base(); d.verified_observation = "I saw the new drop — nice — and the colors — bold — caught me."
check("v2.5 too many em dashes FAIL", "SENTENCE_RHYTHM_ARTIFICIAL" in codes(pf.check_read_aloud(d)))
check("v2.5 read-aloud PASS", codes(pf.check_read_aloud(base())) == set())

# ── Human-voice composite ───────────────────────────────────────────────────────
d = base(); d.conversational_read_result = "FAIL"
check("v2.5 read-result FAIL -> HUMAN_VOICE_LOW", "HUMAN_VOICE_LOW" in codes(pf.check_human_voice(d)))
d = base(); d.voice_risk = "HIGH"
check("v2.5 voice_risk HIGH -> HUMAN_VOICE_LOW", "HUMAN_VOICE_LOW" in codes(pf.check_human_voice(d)))

# ── Batch voice preflight ───────────────────────────────────────────────────────
def _vd(prospect, obs, idea, pos, cta, hr="reaction", extra_interp=""):
    d = base()
    d.prospect_name = prospect; d.greeting = f"Hi {prospect} team,"
    d.verified_observation = obs; d.concise_interpretation = extra_interp
    d.central_idea = idea; d.motionx_positioning_sentence = pos; d.cta = cta
    d.human_reaction = hr; d.why_this_idea = hr; d.prospect_specific_connection = hr
    return d

def human_voice_batch():
    return [
        _vd("Alpha", "Your new tins just dropped and the labels are loud in a good way.",
            "I keep thinking a short film should sell that loudness, not the product spec.",
            "I make short product films through MOTIONX, pilot $399.", "Right place to try it?"),
        _vd("Bravo", "",
            "The monthly cadence is what got me. I would set one repeatable format you re-run each drop.",
            "I make product films for design brands through MOTIONX, $399 to pilot.",
            "Does a repeatable setup fit your side?"),
        _vd("Charlie", "Your reserve flavors stay interesting past any one season.",
            "So instead of a one-off, I picture a page that swaps in whatever you are featuring.",
            "I build pages through MOTIONX, $699 to pilot one.", "Fit how you release things?",
            extra_interp="That keeps each push fresh without rebuilding from scratch."),
        _vd("Delta", "Lash work is something people want to see up close.",
            "I picture a few tight clips that point straight at your booking.",
            "I'm Charles; I make short films for visual studios.", "Want it in writing?"),
        _vd("Echo", "Nine award nods is a real moment, congrats.",
            "Light barely reads in a still, so a short film says more than a portfolio page.",
            "I make brand films for studios through MOTIONX.", "Worth a quick talk?"),
        _vd("Foxtrot", "",
            "The two same-priced tiers stopped me. Rather than a new page, I'd tighten the one you have.",
            "I build focused pages through MOTIONX, $699 to pilot.", "Useful, or is it fine as is?"),
    ]

rbv = pf.batch_voice_preflight(human_voice_batch())
check("v2.5 batch voice human PASS", rbv["status"] == "PASS")

# AI-cadence batch: identical 5-paragraph shape, same credibility opener, "A focused page
# could…" openers, high modals, em dashes everywhere — varied nouns but one robot voice.
def ai_voice_batch():
    out = []
    nouns = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel"]
    for nm in nouns:
        d = base()
        d.prospect_name = nm; d.greeting = f"Hi {nm} team,"
        d.verified_observation = f"Your {nm} collection is live on the homepage — right now."
        d.concise_interpretation = ""
        d.central_idea = f"A focused page could carry the {nm} story and could elevate the journey and could help conversions and might lift it."
        d.motionx_positioning_sentence = "I run MOTIONX, a founder-led studio building motion-first pages. My pilot rate is $699."
        d.cta = "Would a brief written direction be useful?"
        d.human_reaction = d.why_this_idea = d.prospect_specific_connection = ""
        out.append(d)
    return out

rba = pf.batch_voice_preflight(ai_voice_batch())
check("v2.5 batch voice AI-cadence FAIL", rba["status"] == "FAIL")
check("v2.5 batch voice flags concentration", "BATCH_AI_VOICE_CONCENTRATION" in rba["failure_codes"])
check("v2.5 batch voice catches credibility pattern", "BATCH_CREDIBILITY_PATTERN" in rba["failure_codes"])
check("v2.5 batch voice empty PASS", pf.batch_voice_preflight([])["status"] == "PASS")

# ── v2.4 batch diversity still works (no regression) ────────────────────────────
check("v2.5 keeps v2.4 batch diversity PASS", pf.batch_preflight(diverse_batch())["status"] == "PASS")

# ── v2.6 — Geography & Scope Integrity ──────────────────────────────────────────
check("v2.6 gates present under 2.7 engine", hasattr(pf, "check_geography"))
check("v2.6 US default geography PASS", codes(pf.check_geography(base())) == set())
_us_ok = True
for _c in ["US", "USA", "U.S.", "United States", "united states of america", "America"]:
    _d = base(); _d.prospect_country = _c
    if codes(pf.check_geography(_d)) != set():
        _us_ok = False
check("v2.6 US-variant countries PASS", _us_ok)
_ca = base(); _ca.prospect_country = "Canada"
check("v2.6 Canada check_geography FAIL", "GEOGRAPHY_OUT_OF_SCOPE" in codes(pf.check_geography(_ca)))
check("v2.6 Canada full-preflight FAIL", "GEOGRAPHY_OUT_OF_SCOPE" in pf.preflight(_ca, {"policy_version": "2.7"})["failure_codes"])
_blank = base(); _blank.prospect_country = ""
check("v2.6 blank country fail-closed", "GEOGRAPHY_OUT_OF_SCOPE" in codes(pf.check_geography(_blank)))
check("v2.6 context authorizes wider scope", codes(pf.check_geography(_ca, {"geography_authorized": True})) == set())
check("v2.6 baseline still PASS under new engine", pf.preflight(base(), {"policy_version": "2.7"})["status"] == "PASS")

# ── v2.7 — Artifact Readback Integrity ──────────────────────────────────────────
check("v2.7 engine version", pf.POLICY_VERSION == "2.7")

_clean_artifact = (
    "Hi Example team,\n\nBody text here about the product.\n\n"
    + pf.CANONICAL_SIGNATURE + "\n\n"
    + "MOTIONX · Example Plaza Unit One, City, ST 00000\n"
    + pf.OPT_OUT_LINE
)
check("v2.7 clean stored plaintext PASS", codes(pf.check_readback_artifact(_clean_artifact)) == set())

_wrapped = _clean_artifact.replace(
    "https://madebymotionx.com",
    "https://www.google.com/url?q=https://madebymotionx.com&source=gmail&ust=1782969370949000&sa=E")
check("v2.7 wrapper in stored plaintext FAIL (batch20/21 defect)",
      "READBACK_ARTIFACT_DEFECT" in codes(pf.check_readback_artifact(_wrapped)))
check("v2.7 wrapper caught by strengthened link readback too",
      "READBACK_ARTIFACT_DEFECT" in codes(pf.check_gmail_readback_link(_wrapped)))
check("v2.7 q=https wrapper tolerated when htmlBody was supplied (connector ingest artifact)",
      codes(pf.check_readback_artifact(_wrapped, html_supplied=True)) == set())
_wrapped_http = _clean_artifact.replace(
    "https://madebymotionx.com",
    "https://www.google.com/url?q=http://madebymotionx.com&source=gmail&ust=1&sa=E")
check("v2.7 q=http wrapper still FAILS even with htmlBody supplied",
      "REDIRECT_URL" in codes(pf.check_readback_artifact(_wrapped_http, html_supplied=True)))
_wrapped_wrongdest = _clean_artifact.replace(
    "https://madebymotionx.com",
    "https://www.google.com/url?q=https://example.com&source=gmail&ust=1&sa=E")
check("v2.7 wrapper to non-canonical destination FAILS with htmlBody supplied",
      "READBACK_ARTIFACT_DEFECT" in codes(pf.check_readback_artifact(_wrapped_wrongdest, html_supplied=True))
      or "REDIRECT_URL" in codes(pf.check_readback_artifact(_wrapped_wrongdest, html_supplied=True)))

_downgrade = _clean_artifact.replace("https://madebymotionx.com", "http://madebymotionx.com")
check("v2.7 q=http downgrade still FAIL",
      "REDIRECT_URL" in codes(pf.check_gmail_readback_link(
          _downgrade.replace("http://madebymotionx.com", "q=http://madebymotionx.com"))))

_placeholder = _clean_artifact.replace("Example Plaza Unit One, City, ST 00000",
                                       pf.POSTAL_PLACEHOLDER)
check("v2.7 unsubstituted postal placeholder FAIL",
      "READBACK_ARTIFACT_DEFECT" in codes(pf.check_readback_artifact(_placeholder)))

_no_optout = _clean_artifact.replace(pf.OPT_OUT_LINE, "")
check("v2.7 missing opt-out FAIL",
      "READBACK_ARTIFACT_DEFECT" in codes(pf.check_readback_artifact(_no_optout)))

_no_footer = _clean_artifact.replace(
    "MOTIONX · Example Plaza Unit One, City, ST 00000\n", "")
check("v2.7 missing postal footer line FAIL",
      "READBACK_ARTIFACT_DEFECT" in codes(pf.check_readback_artifact(_no_footer)))

check("v2.7 stored price matches expected PASS",
      codes(pf.check_readback_artifact(_clean_artifact + "\nThe pilot is $399.",
                                       expected_price=399)) == set())
check("v2.7 stored price mismatch FAIL",
      "READBACK_ARTIFACT_DEFECT" in codes(pf.check_readback_artifact(
          _clean_artifact + "\nThe pilot is $499.", expected_price=399)))

# v2.7 price-gate hardening: a lone wrong $ amount fails even with optional_price=None
_wrongprice = base()
_wrongprice.motionx_positioning_sentence = _wrongprice.motionx_positioning_sentence.replace(
    "$399", "$499")
_wrongprice.optional_price = None
check("v2.7 lone wrong price FAIL without optional_price",
      "PRICE_MISMATCH" in codes(pf.check_offer_and_price(_wrongprice)))
_rightprice = base()
_rightprice.optional_price = None
check("v2.7 lone correct price PASS without optional_price",
      "PRICE_MISMATCH" not in codes(pf.check_offer_and_price(_rightprice)))

print(f"\n{_passed} passed, {_failed} failed")
sys.exit(1 if _failed else 0)
