#!/usr/bin/env python3
"""
MOTIONX outreach — reusable batch gate runner (v2.9).

Replaces the per-batch one-off scripts (e.g. the stray ~/.motionx-outreach/_batch19_gates.py,
which had a hardcoded date and a /tmp input path). Reads a batch JSON file and runs, in
order: authoring_lint.lint_batch (advisory) -> preflight() per draft -> batch_preflight()
-> batch_voice_preflight(). Prints a JSON verdict to stdout. Exit 0 only if every draft
passes all three binding gates.

Usage:
  python3 outreach/scripts/run_gates.py <batch.json>

Batch JSON shape:
{
  "context": {"policy_version": "2.7", "recent_subjects": ["..."], ...},   # optional extras
  "drafts": [ { <DraftModel field>: value, ... }, ... ]
}
Unknown draft keys are rejected (typo safety). The batch file may live outside the repo
(it usually contains prospect PII — keep it in ~/.motionx-outreach/ or a scratch dir).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import authoring_lint  # noqa: E402
import preflight as pf  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip())
        return 2
    with open(sys.argv[1]) as f:
        batch = json.load(f)

    context = batch.get("context") or {}
    context.setdefault("policy_version", pf.POLICY_VERSION)

    valid_fields = set(pf.DraftModel.__dataclass_fields__)
    drafts = []
    for i, spec in enumerate(batch["drafts"]):
        unknown = set(spec) - valid_fields
        if unknown:
            print(json.dumps({"status": "ERROR", "draft_index": i,
                              "unknown_fields": sorted(unknown)}))
            return 2
        drafts.append(pf.DraftModel(**spec))

    lint = authoring_lint.lint_batch(drafts) \
        if hasattr(authoring_lint, "lint_batch") else []

    per_draft = []
    all_pass = True
    for d in drafts:
        res = pf.preflight(d, dict(context))
        ok = res["status"] == "PASS"
        all_pass &= ok
        per_draft.append({"prospect": d.prospect_name, "status": res["status"],
                          "failure_codes": sorted(set(res.get("failure_codes", []))),
                          "word_count": res.get("final_body_word_count")})

    bres = pf.batch_preflight(drafts)
    vres = pf.batch_voice_preflight(drafts)
    all_pass &= bres["status"] == "PASS" and vres["status"] == "PASS"

    print(json.dumps({
        "status": "PASS" if all_pass else "FAIL",
        "engine": pf.POLICY_VERSION,
        "n": len(drafts),
        "lint_advisories": lint,
        "per_draft": per_draft,
        "batch_preflight": {"status": bres["status"],
                            "failure_codes": sorted(set(bres.get("failure_codes", [])))},
        "batch_voice_preflight": {"status": vres["status"],
                                  "failure_codes": sorted(set(vres.get("failure_codes", [])))},
    }, indent=1))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
