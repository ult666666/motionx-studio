"""
MOTIONX outreach — deterministic cadence-slot allocator (operating policy v2.9 · engine v2.7).

An ADDITIVE authoring aid: it changes NO gate and does not touch the validator engine
(preflight.py is at engine 2.7). It hands the author a per-draft "cadence slot" — paragraph
count, price show/omit, a distinct idea-opener, a distinct credibility structure, a
distinct price lead-in, and a CTA category — distributed across the batch so the set
clears batch_preflight() (diversity) and batch_voice_preflight() (voice) with far fewer
iterations. Traces to a real, recurring cost: on 15-45-draft batches (batch19/batch20),
hand-coordinating cross-draft diversity (idea-openers, credibility lines, price lead-ins,
paragraph mix) was the #1 source of gate iterations. This makes that assignment
deterministic and reviewable up front. The author still writes every body by hand and
supplies the genuine per-prospect thought; the slot only shapes structure.

Design targets (mirror the gate thresholds so a filled batch passes):
  * paragraph mix: no single count >~40% (BATCH_PARAGRAPH_PATTERN fails >60%).
  * idea-openers: >=24 distinct, cycled — for n<=48 each opener recurs <=2x
    (a 5-gram in <=2 of n>=8 drafts is well under the >25% BATCH_PHRASE_OVERUSE line).
  * credibility structures: >=16 distinct — first-3-words concentration stays under the
    50% BATCH_CREDIBILITY_PATTERN line.
  * price lead-ins: >=10 distinct, so no price 5-gram repeats past the threshold.
  * CTA categories: 5, round-robin (no exact-CTA repeat; the author varies wording).
  * 4-para drafts capped so their shared empty positioning line never exceeds 4
    (the BATCH_POSITIONING_REPEAT trap logged 2026-06-30).
"""
from __future__ import annotations

# Paragraph assignment. CRITICAL CONSTRAINT (logged batch19/batch20): a 4-para draft has
# an EMPTY motionx_positioning_sentence, and batch_preflight counts identical positioning
# lines — including the empty one — failing BATCH_POSITIONING_REPEAT when >4 drafts share
# it. So the number of 4-para drafts must be HARD-CAPPED at 4 for the WHOLE batch, at any
# n (not a fraction, not a rolling window). The remaining drafts alternate 5/6-para, which
# both carry real positioning lines and keep either count under the 60% BATCH_PARAGRAPH
# threshold. MAX_FOUR_PARA mirrors preflight.BATCH_DEFAULTS['exact_positioning_max'] (4).
MAX_FOUR_PARA = 4

IDEA_OPENERS = [
    "I'd film", "Thirty seconds, close up:", "What I'd shoot is", "Picture a short film of",
    "I'd put a camera on", "A film up close on", "The shot I want is", "I'd capture",
    "There's a film in", "I'd train the lens on", "I'd let the camera sit on",
    "One continuous shot:", "I'd film the moment", "Shot tight, you'd see",
    "Close on it, that's the film:", "The thing I'd film is", "I keep picturing",
    "I'd hold the shot on", "Slow and close:", "Imagine a short film of",
    "I'd start on", "The film opens on", "Right up close:", "I'd frame",
]

CRED_STRUCTURES = [
    "I make short product films through MOTIONX, the small studio I run.",
    "I run MOTIONX, a small studio that films objects like these.",
    "MOTIONX is the small studio I run; short product films are the work.",
    "Through MOTIONX I make short films for independent makers.",
    "I'm Charles, and I make short films at MOTIONX.",
    "I build these short films at MOTIONX, my one-person studio.",
    "MOTIONX is my studio, and I film products the way they deserve.",
    "I make short films for small brands through MOTIONX.",
    "I run MOTIONX and shoot short product films for makers like you.",
    "I film products for a living through MOTIONX, my small studio.",
    "MOTIONX is the studio behind these short films, and I run it.",
    "I run a small studio called MOTIONX, and these short films are the work.",
    "I shoot short films like this at MOTIONX, the studio I run.",
    "Filming objects like this is what I do at MOTIONX.",
    "I'm Charles; MOTIONX is the small studio where I make these.",
    "Short films like this are the whole of what I do at MOTIONX.",
]

# Product Film ($399) price lead-ins. Website ($699) variants are appended by the caller
# when selected_offer is a site; keep these all lexically distinct.
PRICE_LEADINS = [
    "The pilot is $399.", "$399 for the pilot film.", "My pilot rate is $399.",
    "I work on a pilot basis, $399.", "That's $399 for a focused pilot.",
    "Pilot films run $399.", "$399 to start, one film.", "The first one is $399.",
    "$399 covers the pilot.", "The pilot comes to $399.", "I keep the pilot at $399.",
    "A pilot film is $399.",
]

CTA_CATEGORIES = [
    "WRITTEN_DIRECTION", "QUICK_CONVERSATION", "SCOPE_OUTLINE", "INTEREST_CHECK", "TIMING_CHECK",
]


def assign(n: int, price_show_start: int = 0):
    """Return a list of n cadence-slot dicts. Deterministic (no RNG) so a run is
    reproducible and reviewable. `price_show_start` shifts the show/omit parity if you
    want a specific first-draft choice. 4-para slots are re-balanced so no rolling
    window of drafts carries more than 4 of them (empty-positioning safety)."""
    # Choose which drafts are 4-para: up to MAX_FOUR_PARA, spread evenly across the batch.
    n_four = min(MAX_FOUR_PARA, max(0, n // 3))
    four_idx = set()
    if n_four:
        step = n / n_four
        four_idx = {int(k * step + step / 2) for k in range(n_four)}
    slots = []
    fives = True  # alternate 5/6 for the non-4-para drafts
    for i in range(n):
        if i in four_idx:
            para = 4
        else:
            para = 5 if fives else 6
            fives = not fives
        price = "SHOW" if ((i + price_show_start) % 2 == 0) else "OMIT"
        slots.append({
            "index": i,
            "paragraph_target": para,
            "price": price,
            "idea_opener": IDEA_OPENERS[i % len(IDEA_OPENERS)],
            "credibility": CRED_STRUCTURES[i % len(CRED_STRUCTURES)],
            "price_leadin": PRICE_LEADINS[i % len(PRICE_LEADINS)],
            "cta_category": CTA_CATEGORIES[i % len(CTA_CATEGORIES)],
        })
    return slots


def summarize(slots):
    from collections import Counter
    return {
        "n": len(slots),
        "paragraphs": dict(Counter(s["paragraph_target"] for s in slots)),
        "price_show": sum(1 for s in slots if s["price"] == "SHOW"),
        "price_omit": sum(1 for s in slots if s["price"] == "OMIT"),
        "distinct_idea_openers": len({s["idea_opener"] for s in slots}),
        "distinct_credibility": len({s["credibility"] for s in slots}),
        "distinct_price_leadins": len({s["price_leadin"] for s in slots}),
    }


if __name__ == "__main__":
    for n in (5, 15, 33, 45):
        s = assign(n)
        summ = summarize(s)
        four = summ["paragraphs"].get(4, 0)
        assert four <= MAX_FOUR_PARA, f"n={n}: {four} four-para exceeds hard cap {MAX_FOUR_PARA}"
        top = max(summ["paragraphs"].values())
        assert top / n <= 0.60, f"n={n}: a paragraph count dominates ({top}/{n})"
        print(f"n={n}: {summ}")
    print("cadence self-test OK")
