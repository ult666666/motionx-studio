"""
MOTIONX outreach — authoring pre-lint (operating policy v2.9 · engine v2.7, Continuous Improvement Loop).

A FAST, ADVISORY pre-check you run on a batch of DraftModels BEFORE the formal gates
(preflight / batch_preflight / batch_voice_preflight). It does not replace them and is
not authoritative — it just catches the failure patterns that historically cost the
most iterations, so first drafts come out cleaner. Pure stdlib, no network, no PII.

It encodes the "Accumulated authoring heuristics" from self-improvement.md as code:
  * comma-triplet lists per body  (-> EXCESSIVE_LISTING risk; max 1)
  * repeated 5-gram across positioning lines (-> BATCH_PHRASE_OVERUSE risk; max 3)
  * paragraph-count concentration (-> BATCH_PARAGRAPH_PATTERN risk; >60%)
  * mini-proposal words (milestone/rollout/deliverables/phase/across both)
Run:  python3 outreach/authoring_lint.py   (self-test)
Use:  from authoring_lint import lint_batch ; hints = lint_batch(drafts)
"""
from __future__ import annotations
import re
from collections import Counter

# 2+ consecutive comma-separated SHORT items (each <=4 words) = a decorative list.
_LIST_RE = re.compile(r"(?:[\w'’&-]+(?:\s+[\w'’&-]+){0,3},\s+){2,}")
_MINI = [r"\bmilestones?\b", r"\broll-?out\b", r"\bdeliverables?\b", r"\bphase [12]\b",
         r"\bshot list\b", r"across both", r"on screens and"]


def _body(d):
    parts = [d.greeting, d.verified_observation, d.concise_interpretation,
             d.central_idea, d.motionx_positioning_sentence, d.cta]
    return "\n\n".join(p for p in parts if p)


def _norm(t):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t.lower())).strip()


def _shingles(t, n=5):
    toks = _norm(t).split()
    return {" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1)} if len(toks) >= n else set()


def _list_count(b):
    """Count sentences containing a decorative comma-list, matching preflight's
    per-sentence _list_groups logic (avoids over-counting a single run of commas;
    calibration fix logged 2026-06-22 batch #4)."""
    sents = re.split(r"(?<=[.!?])\s+", b)
    return sum(1 for s in sents if _LIST_RE.search(s))


def lint_batch(drafts: list) -> list:
    """Return a list of advisory hint strings. Empty list = clean (likely first-try PASS)."""
    hints = []
    n = len(drafts)
    # per-draft: geography (v2.6), comma-triplets + mini-proposal words
    _US_OK = {"US", "USA", "U.S.", "U.S.A.", "UNITED STATES", "UNITED STATES OF AMERICA", "AMERICA"}
    for d in drafts:
        _country = (getattr(d, "prospect_country", "") or "").strip().upper().rstrip(".")
        if {_country, _country.replace(".", "")} .isdisjoint(_US_OK):
            label = _country or "BLANK"
            hints.append(f"[{d.prospect_name}] prospect_country={label} not US-verified -> GEOGRAPHY_OUT_OF_SCOPE risk (verify US + set prospect_country before drafting)")
        b = _body(d)
        lists = _list_count(b)
        if lists >= 2:
            hints.append(f"[{d.prospect_name}] {lists} comma-lists (max 1) -> rewrite one with 'and' (EXCESSIVE_LISTING risk)")
        for pat in _MINI:
            if re.search(pat, b.lower()):
                hints.append(f"[{d.prospect_name}] mini-proposal phrase /{pat}/ -> simplify (MINI_PROPOSAL_OVERBUILT risk)")
                break
        if b.count("—") > 1:
            hints.append(f"[{d.prospect_name}] >1 em dash -> use periods (SENTENCE_RHYTHM risk)")
        # sentence longer than 34 words -> SENTENCE_RHYTHM_ARTIFICIAL. Added 2026-06-30
        # (batch19): a 36-word central_idea sentence (Ground Up) reached preflight because
        # the lint had no sentence-length check; preflight caught it, but one iteration was
        # avoidable. Mirrors preflight.MAX_SENTENCE_WORDS.
        _long = max((len(re.findall(r"\S+", s)) for s in re.split(r"(?<=[.!?])\s+", b)), default=0)
        if _long > 34:
            hints.append(f"[{d.prospect_name}] sentence of {_long} words (>34) -> split it (SENTENCE_RHYTHM_ARTIFICIAL risk)")
        # word-count floor (hard min 75) — flag a small buffer so an omit-price +
        # omit-interpretation body that lands at 71-73 is caught before the gate.
        # Traced to 2026-06-25 batch12 (Heartwood/Vermont/Danforth all 71-73w).
        _wc = len(re.findall(r"\S+", b))
        if _wc < 75:
            hints.append(f"[{d.prospect_name}] body is {_wc} words (< hard min 75) -> add one concrete detail to the central idea (BODY_TOO_SHORT)")
    # batch: repeated positioning 5-gram in >3 bodies
    sh = Counter()
    for d in drafts:
        for s in set(_shingles(d.motionx_positioning_sentence, 5)):
            sh[s] += 1
    # Threshold aligns with the gate: batch_preflight fails a shingle at >25% of the
    # batch, so for large n an absolute ">3" over-warns (logged 2026-06-30 batch20: at
    # n=32, "the small studio i run" in 5 bodies = 15.6% passed the gate but tripped the
    # old >3 lint). Use max(3, 25% of n) so small batches keep the tight rule.
    _pos_cap = max(3, int(0.25 * n))
    for gram, c in sh.items():
        if c > _pos_cap:
            hints.append(f"[batch] positioning 5-gram '{gram}' in {c}/{n} bodies (>{_pos_cap}) -> vary verb/studio/price phrasing (BATCH_PHRASE_OVERUSE risk)")
    # batch: repeated 5-gram ANYWHERE in the price-stripped body (mirrors batch_preflight,
    # which strips "$399" before shingling). Catches cross-sentence boundary shingles the
    # positioning-only check misses — e.g. the price-line+positioning seam "is short product
    # films are" when "...is $399." is followed by "Short product films are...".
    # Added 2026-06-26 (batch13): that exact 5-gram tripped batch_preflight in 4/15 bodies.
    if n >= 5:
        fullsh = Counter()
        for d in drafts:
            body = re.sub(r"\$\d[\d,]*", "", _body(d))
            for s in set(_shingles(body, 5)):
                fullsh[s] += 1
        for gram, c in fullsh.items():
            if c / n > 0.25 and gram not in sh:  # sh already reported positioning-only grams
                hints.append(f"[batch] body 5-gram '{gram}' in {c}/{n} price-stripped bodies (>25%) -> vary phrasing (BATCH_PHRASE_OVERUSE risk)")
    # batch: paragraph-count concentration (>60%) — only meaningful for real batches
    if n >= 5:
        pc = Counter(len([p for p in _body(d).split("\n\n") if p.strip()]) for d in drafts)
        worst, cnt = pc.most_common(1)[0]
        if cnt / n > 0.6:
            hints.append(f"[batch] {cnt}/{n} bodies have {worst} paragraphs (>60%) -> empty concise_interpretation on some to vary (BATCH_PARAGRAPH_PATTERN risk)")
    # batch: identical positioning sentence in >4 drafts trips BATCH_POSITIONING_REPEAT.
    # The trap (logged 2026-06-30 batch19): 4-para drafts leave motionx_positioning_sentence
    # empty, so 5+ of them give the gate 5 identical "" positioning lines = a "repeat".
    # Mirror the gate's exact_positioning_max=4 here, including the empty line.
    if n >= 5:
        pos = Counter((getattr(d, "motionx_positioning_sentence", "") or "").strip() for d in drafts)
        for line, c in pos.items():
            if c > 4:
                lbl = "EMPTY (4-para drafts share no positioning line)" if line == "" else f"'{line[:30]}'"
                hints.append(f"[batch] positioning {lbl} appears in {c} drafts (>4) -> cap 4-para drafts at 4, or vary the line (BATCH_POSITIONING_REPEAT risk)")
    return hints


if __name__ == "__main__":
    class _D:
        def __init__(s, **k): s.__dict__.update(k); s.__dict__.setdefault("prospect_name", "test")
    good = _D(prospect_country="US",
              greeting="Hi X team,",
              verified_observation="Your new single-origin bar caught my eye, the one with the dried cherry and sea salt you started making this spring.",
              concise_interpretation="",
              central_idea="I'd film the bar snapping and the inclusions catching light, the temper and the pour behind it. Kept tight and appetizing, it reads in a few seconds on the page and in a post.",
              motionx_positioning_sentence="I make short product films through MOTIONX, the small studio I run.",
              cta="Would one of the new bars be worth filming?")
    bad = _D(prospect_country="US", greeting="Hi Y team,",
             verified_observation="The pour, the flame, the glass caught me.",
             concise_interpretation="A real milestone for the brand.",
             central_idea="I'd show the snap, the shine, the melt across both locations.",
             motionx_positioning_sentence="I make short films at MOTIONX; the pilot is $399.",
             cta="Worth a chat?")
    print("good ->", lint_batch([good]))
    print("bad  ->", lint_batch([bad]))
    assert lint_batch([good]) == [], "clean draft should produce no hints"
    assert lint_batch([bad]), "bad draft should produce hints"
    print("authoring_lint self-test OK")
