# -*- coding: utf-8 -*-
"""
MOTIONX visual-cold-open — sample-candidate ingestion (batch32 approval packet + CSV).

Parses the *decision* source (the approval packet's ranked table, which carries the
APPROVE / MAYBE / REJECT decision and the rank) and joins it with the *detail* source
(the sourcing-candidates CSV, which carries the verified observation, the possible
motion angle, the public contact evidence, and the source URLs). It then selects the
top-N APPROVE candidates by rank.

Design rules (mirror the task's safety posture):
  * Only fields present in the packet/CSV are used — no field is invented. A missing
    detail is recorded as an uncertainty flag, never filled in.
  * The decision (APPROVE/MAYBE) comes ONLY from the approval packet.
  * MAYBE candidates are used only as a fallback when fewer than N APPROVE rows exist.
  * A recipient email is used ONLY if the CSV explicitly provides a verified one; the
    batch32 CSV does not, so sample rows carry an empty recipient (a contact *page* is
    not a deliverable address) and the live-draft path blocks rather than guessing.
  * Pure stdlib.
"""
from __future__ import annotations

import csv
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SampleParseError(RuntimeError):
    """Raised when neither source can be parsed into any candidate row."""


# Columns that, if present in the CSV, are treated as a *verified* recipient/contact.
# The batch32 CSV has none of these, so this is forward-looking (and testable).
_RECIPIENT_COLUMNS = ("recipient_email", "verified_email", "contact_email")
_FIRST_NAME_COLUMNS = ("first_name", "contact_first_name", "recipient_first_name")


@dataclass
class SampleCandidate:
    rank: int
    decision: str                 # APPROVE | MAYBE | REJECT
    company: str
    domain: str
    category: str = ""
    verified_observation: str = ""
    why_motionx_relevant: str = ""
    possible_angle: str = ""
    public_contact_evidence: str = ""
    source_urls: str = ""
    risk_flags: str = ""
    candidate_id: str = ""
    official_website: str = ""
    recipient_email: str = ""     # empty unless the CSV explicitly verifies one
    first_name: str = ""
    selected_from: str = "batch32-approval-packet"
    uncertainty_flags: List[str] = field(default_factory=list)

    @property
    def decision_source(self) -> str:
        return f"approval_packet:rank_{self.rank}:{self.decision.upper()}"

    def to_item(self) -> dict:
        """Map onto the field names brief.build_brief + sample_copy expect.

        Only verified fields are populated; missing ones stay empty so downstream
        fabrication/uncertainty guards can see they are absent.
        """
        return {
            "business_name": self.company,
            "prospect_name": self.company,
            "company": self.company,
            "domain": self.domain,
            "category": self.category,
            "verified_observation": self.verified_observation,
            "proposed_creative_direction": self.possible_angle,
            # We deliberately do NOT assert a specific_opportunity we cannot verify.
            "specific_opportunity": "",
            "recipient_email": self.recipient_email,
            "greeting": "",           # no verified first name → sample_copy uses a team greeting
            "first_name": self.first_name,
            "preflight_status": "PASS",
            "lead_id": self.candidate_id or _slug(self.company),
            "selected_from": self.selected_from,
            "decision_source": self.decision_source,
            "decision": self.decision.upper(),
            "rank": self.rank,
            "source_urls": self.source_urls,
            "public_contact_evidence": self.public_contact_evidence,
            "verified_source_notes": self.source_urls,
            "risk_flags": self.risk_flags,
            "uncertainty_flags": list(self.uncertainty_flags),
        }


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_") or "candidate"


def _norm(name: str) -> str:
    """Normalize a company name / domain for joining (alnum-only, lowercased)."""
    return "".join(ch for ch in (name or "").lower() if ch.isalnum())


def _domain_root(domain: str) -> str:
    d = (domain or "").strip().lower()
    d = re.sub(r"^https?://", "", d)
    d = re.sub(r"^www\.", "", d)
    d = d.split("/")[0]
    # collapse to the registrable-ish label (drop the TLD) for a lenient join
    return d.split(".")[0] if "." in d else d


# ── approval packet (decision + rank) ─────────────────────────────────────────────
def parse_approval_packet(md_text: str) -> List[SampleCandidate]:
    """Parse the 'Ranked Candidates' markdown table from the approval packet.

    Expected row shape:
      | 1 | APPROVE | Northwind Gear | `northwindgear.example` | Category | ... |
    Only the leading Rank | Decision | Company | Domain | Category cells are read; the
    remaining descriptive columns are sourced from the CSV.
    """
    out: List[SampleCandidate] = []
    for line in md_text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 4:
            continue
        rank_cell = cells[0].strip().strip("`").rstrip(".")
        if not rank_cell.isdigit():
            continue  # header / separator / non-data row
        decision = cells[1].strip().upper()
        if decision not in ("APPROVE", "MAYBE", "REJECT"):
            continue
        company = cells[2].strip()
        domain = cells[3].strip().strip("`").strip()
        category = cells[4].strip() if len(cells) > 4 else ""
        if not company:
            continue
        out.append(SampleCandidate(
            rank=int(rank_cell), decision=decision, company=company,
            domain=domain, category=category,
            selected_from="batch32-approval-packet",
        ))
    return out


# ── sourcing CSV (verified detail) ────────────────────────────────────────────────
def parse_candidate_csv(csv_text: str) -> Dict[str, dict]:
    """Index the sourcing CSV rows by normalized company name, exact full domain, and
    TLD-stripped domain root.

    The lenient domain-root key (e.g. ``acme`` for both ``acme.com`` and ``acme.io``)
    is inherently ambiguous when two DIFFERENT rows share a second-level label. Binding
    such a key to an arbitrary first row could enrich a candidate with another company's
    verified observation (a misattribution). So a root key that would map to more than
    one distinct row is dropped (fail-closed): those candidates fall through to the
    exact full-domain / company key, or to the "no matching CSV row" uncertainty flag.
    """
    index: Dict[str, dict] = {}
    ambiguous_roots: set = set()
    reader = csv.DictReader(csv_text.splitlines())
    for row in reader:
        company = (row.get("company") or row.get("Company") or "").strip()
        domain = (row.get("domain") or row.get("Domain") or "").strip()
        if not company and not domain:
            continue
        if company:
            index.setdefault("c:" + _norm(company), row)
        if domain:
            index.setdefault("d:" + _norm(domain), row)     # exact full domain
            rk = "d:" + _domain_root(domain)                 # lenient TLD-stripped root
            if rk in index and index[rk] is not row:
                ambiguous_roots.add(rk)                      # two distinct rows collide
            else:
                index.setdefault(rk, row)
    for rk in ambiguous_roots:
        index.pop(rk, None)
    return index


def _first_col(row: dict, cols) -> str:
    for c in cols:
        v = (row.get(c) or "").strip()
        if v:
            return v
    return ""


def _enrich_from_csv(cand: SampleCandidate, csv_index: Dict[str, dict]) -> None:
    # Order matters: exact company, then exact full domain, and only then the lenient
    # (collision-safe) TLD-stripped root — so an exact match always wins over the root.
    row = (csv_index.get("c:" + _norm(cand.company))
           or csv_index.get("d:" + _norm(cand.domain))
           or csv_index.get("d:" + _domain_root(cand.domain)))
    if not row:
        cand.uncertainty_flags.append(
            "no matching CSV row: verified observation/angle taken from packet only")
        return
    cand.candidate_id = (row.get("candidate_id") or "").strip() or cand.candidate_id
    cand.official_website = (row.get("official_website") or "").strip()
    cand.verified_observation = (row.get("verified_observation") or "").strip()
    cand.why_motionx_relevant = (row.get("why_motionx_relevant") or "").strip()
    cand.possible_angle = (row.get("possible_angle") or "").strip()
    cand.public_contact_evidence = (row.get("public_contact_evidence") or "").strip()
    cand.source_urls = (row.get("source_urls") or "").strip()
    cand.risk_flags = (row.get("risk_uncertainty_flags") or "").strip()
    if not cand.category:
        cand.category = (row.get("category") or "").strip()
    # A recipient/first-name is used ONLY if the CSV explicitly verifies one.
    cand.recipient_email = _first_col(row, _RECIPIENT_COLUMNS)
    cand.first_name = _first_col(row, _FIRST_NAME_COLUMNS)
    cand.selected_from = "batch32-approval-packet+sourcing-csv"
    if not cand.verified_observation:
        cand.uncertainty_flags.append("CSV row present but no verified_observation")


def load_candidates(approval_packet_path: str,
                    candidate_csv_path: str = "") -> List[SampleCandidate]:
    """Parse the packet, join the CSV, and return all candidates (packet order)."""
    if not approval_packet_path or not os.path.exists(os.path.expanduser(approval_packet_path)):
        raise SampleParseError(
            f"approval packet not found: {approval_packet_path!r}")
    with open(os.path.expanduser(approval_packet_path), "r", encoding="utf-8") as fh:
        md_text = fh.read()
    cands = parse_approval_packet(md_text)
    if not cands:
        raise SampleParseError(
            "approval packet parsed 0 candidates (no Ranked Candidates table rows found)")

    csv_index: Dict[str, dict] = {}
    if candidate_csv_path and os.path.exists(os.path.expanduser(candidate_csv_path)):
        with open(os.path.expanduser(candidate_csv_path), "r", encoding="utf-8") as fh:
            csv_index = parse_candidate_csv(fh.read())
    for c in cands:
        _enrich_from_csv(c, csv_index)
    return cands


def select_top_approve(candidates: List[SampleCandidate], limit: int) -> List[SampleCandidate]:
    """Return the top `limit` APPROVE candidates by rank.

    Falls back to the strongest MAYBE rows ONLY if fewer than `limit` APPROVE rows
    exist (per the task rule). Never returns more than `limit`.
    """
    approved = sorted((c for c in candidates if c.decision.upper() == "APPROVE"),
                      key=lambda c: c.rank)
    chosen = approved[:max(0, limit)]
    if len(chosen) < limit:
        maybes = sorted((c for c in candidates if c.decision.upper() == "MAYBE"),
                        key=lambda c: c.rank)
        for m in maybes:
            if len(chosen) >= limit:
                break
            m.uncertainty_flags.append(
                "MAYBE candidate used as fallback (fewer than requested APPROVE rows)")
            chosen.append(m)
    return chosen[:max(0, limit)]
