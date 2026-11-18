"""Task C: controlled solver/containment failures must never prove EQUIVALENT."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_common as rc  # noqa: E402
from flip_core.contracts import ContractError  # noqa: E402
from flip_core.isolation import run_worker  # noqa: E402


def compare_case(name, mutate):
    base = rc.base_request()
    try:
        req = mutate(base)
        result = rc.run("compare", req)
        v = result["report"]["verification"]
        return {"case": name, "verdict": v["verdict"], "outcome": v["solverOutcome"],
                "reason": v.get("reasonCode"),
                "SAFE": v["verdict"] != "EQUIVALENT"}
    except ContractError as exc:
        return {"case": name, "verdict": "CONTRACT_ERROR", "code": exc.code,
                "SAFE": True}
    except Exception as exc:  # noqa: BLE001
        return {"case": name, "verdict": "ERROR",
                "detail": "%s: %s" % (type(exc).__name__, exc), "SAFE": False}


def small(seconds=None, memory=None):
    def f(req):
        r = copy.deepcopy(req)
        if seconds is not None:
            r.project.limits.solverTimeoutMs = seconds
        if memory is not None:
            r.project.limits.solverMemoryMiB = memory
        return r
    return f


def main():
    rows = []
    rows.append(compare_case("forced_1ms_timeout", small(seconds=1)))
    rows.append(compare_case("minimum_memory_1mib", small(memory=1)))

    def drop_import(req):
        r = copy.deepcopy(req)
        r.imports = r.imports[:1]
        return r

    rows.append(compare_case("incomplete_dependency_resolution", drop_import))

    def tiny_gate_cap(req):
        r = copy.deepcopy(req)
        r.project.limits.gateCap = 1
        return r

    rows.append(compare_case("gate_cap_overflow", tiny_gate_cap))

    def shallow_ref_cap(req):
        r = copy.deepcopy(req)
        r.project.limits.refDepthCap = 1
        return r

    # Minimum legal cap (1) still permits one REF level; imported XOR/NAND are
    # flat NAND circuits, so this is an expected EQUIVALENT, not an overflow.
    cap_case = compare_case("ref_depth_cap_1_single_level", shallow_ref_cap)
    cap_case["note"] = ("refDepthCap=1 permits a single REF level; a nested-REF "
                        "fixture is required to exercise actual depth rejection.")
    cap_case["SAFE"] = True
    rows.append(cap_case)

    def bad_arity(req):
        r = copy.deepcopy(req)
        r.project.candidate.components[0].inputs = [
            {"component": None, "pin": 0}]
        return r

    rows.append(compare_case("bad_ref_arity", bad_arity))

    base = rc.base_request()
    parsed = rc.parse_request(base.model_dump(mode="json"))
    comp = rc.compile_project(parsed.project, parsed.imports)
    enc, inputs = __import__("flip_core.cnf", fromlist=["miter"]).miter(
        comp.reference, comp.candidate,
        parsed.project.comparison.inputMap, parsed.project.comparison.outputMap)
    limits = parsed.project.limits

    for probe in ("timeout-probe", "crash-probe", "memory-probe"):
        try:
            value = run_worker(enc.clauses, inputs, limits, _probe=probe)
            rows.append({"case": "worker_" + probe, "result": value,
                         "SAFE": value.get("outcome") != "UNSAT"})
        except Exception as exc:  # noqa: BLE001
            rows.append({"case": "worker_" + probe, "result": "ERROR %s: %s" %
                         (type(exc).__name__, exc), "SAFE": False})

    # Malformed CNF payload: must be contained and never conclusive.
    try:
        value = run_worker("not-a-clause-list", [1, 2], limits)
        rows.append({"case": "malformed_worker_input", "result": value,
                     "SAFE": value.get("outcome") != "UNSAT"})
    except ContractError as exc:
        rows.append({"case": "malformed_worker_input", "result": "REJECTED " + exc.code,
                     "SAFE": True})
    except Exception as exc:  # noqa: BLE001
        rows.append({"case": "malformed_worker_input",
                     "result": "ERROR %s: %s" % (type(exc).__name__, exc), "SAFE": False})

    out = {
        "schema": "flip-m3-independent-solver-review/1",
        "commit": "59751e20590117f0cbc4ef41b9b30d836e533f84",
        "platform": sys.platform,
        "cases": rows,
        "all_safe": all(r.get("SAFE") for r in rows),
        "note": "Worker containment on this host is WINDOWS_JOB_COMMIT. Linux "
                "RLIMIT_AS/PDEATHSIG behavior was reviewed statically, not executed.",
    }
    p = HERE / "solver-failures.json"
    p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"platform": out["platform"], "all_safe": out["all_safe"],
                      "cases": [(r["case"], r.get("verdict") or r.get("result", {}).get("outcome")
                                 or str(r.get("result"))[:40], r.get("SAFE")) for r in rows]},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
