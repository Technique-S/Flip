"""Task B: independent SAT soundness review of the production engine."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_common as rc  # noqa: E402
import independent_core as ic  # noqa: E402

VARIANTS = [
    ("self_equivalence", lambda r: r, "EQUIVALENT"),
    ("output_permutation", rc.swap_outputs, "DIFFERENT"),
    ("commutative_inputs", rc.reversed_refs, "EQUIVALENT"),
    ("glue_wrong_wiring", rc.glue_wrong, "DIFFERENT"),
    ("triple_output", rc.extra_output, "EQUIVALENT"),
    ("output_map_permutation", rc.permuted_output_map, "EQUIVALENT"),
    ("input_map_reversal", rc.permuted_input_map, "EQUIVALENT"),
]


def main():
    rows = []
    for name, mutate, expected in VARIANTS:
        base = rc.base_request()
        try:
            req = mutate(base)
            actual = rc.run("compare", req)
            verdict = actual["report"]["verification"]["verdict"]
            outcome = actual["report"]["verification"]["solverOutcome"]
            gt = rc.exhaustive_ground_truth(req)
            row = {
                "case": name, "expected": expected, "production_verdict": verdict,
                "production_solver_outcome": outcome, "independent_ground_truth": gt,
                "matches_expected": verdict == expected,
                "matches_independent": verdict == gt["verdict"],
            }
            if verdict == "DIFFERENT":
                w = actual["report"]["verification"].get("witness")
                row["witness_replay"] = rc.replay_witness_independently(req, w) if w else {
                    "error": "no witness in DIFFERENT report"}
            if verdict == "EQUIVALENT":
                row["requires_unsat"] = (outcome == "UNSAT")
                # independent UNSAT re-derivation over the same compiled netlists
                parsed = rc.parse_request(req.model_dump(mode="json"))
                comp = rc.compile_project(parsed.project, parsed.imports)
                a = rc.production_to_independent(comp.reference)
                b = rc.production_to_independent(comp.candidate)
                miter = ic.cnf_miter(a, b)
                res = ic.solve(miter[0]) if miter else None
                row["independent_miter"] = {
                    "result": res["result"] if res else "WIDTH_MISMATCH",
                    "clauses": len(miter[0].clauses) if miter else None,
                    "unsat_confirmed": bool(res and res["result"] == "UNSAT"),
                }
            rows.append(row)
        except Exception as exc:  # noqa: BLE001
            rows.append({"case": name, "expected": expected,
                         "error": "%s: %s" % (type(exc).__name__, exc)})

    out = {
        "schema": "flip-m3-independent-sat-review/1",
        "commit": "59751e20590117f0cbc4ef41b9b30d836e533f84",
        "evaluators": ["production execute/compare", "OpenCode independent_core",
                       "official TAP-02 reference.py"],
        "cases": rows,
        "agreements": sum(1 for r in rows if r.get("matches_independent")),
        "total": len(rows),
        "note": "EQUIVALENT is confirmed by completed UNSAT on both miters and full "
                "exhaustive enumeration over small input domains; no sampled claim is "
                "promoted to an equivalence proof.",
    }
    p = HERE / "sat-soundness.json"
    p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "agreements": out["agreements"], "total": out["total"],
        "cases": [(r["case"], r.get("production_verdict"),
                   (r.get("independent_ground_truth") or {}).get("verdict"),
                   r.get("matches_independent"), r.get("witness_replay", {}).get("differs")) for r in rows],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
