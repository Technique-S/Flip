"""Task A: adversarial evaluation of the trusted proof consumer."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_common as rc  # noqa: E402
from flip_core.contracts import ContractError  # noqa: E402


def attempt(name, req, claimed, *, project_hash=None, reference_hash=None, mutate_claim=None):
    claim = copy.deepcopy(claimed)
    if mutate_claim:
        try:
            mutate_claim(claim)
        except Exception as exc:  # noqa: BLE001
            return {"case": name, "outcome": "CLAIM_CONSTRUCTION_REJECTED",
                    "detail": "%s: %s" % (type(exc).__name__, exc)}
    envelope = rc.consume_request(req, claim, project_hash, reference_hash)
    try:
        result = rc.execute("consume", json.dumps(envelope, sort_keys=True,
                                                  separators=(",", ":")).encode())
        return {"case": name, "outcome": "ACCEPTED",
                "verdict": result["report"]["verification"]["verdict"],
                "SAFE": False}
    except ContractError as exc:
        return {"case": name, "outcome": "REJECTED", "code": exc.code,
                "message": exc.message, "SAFE": True}
    except Exception as exc:  # noqa: BLE001
        return {"case": name, "outcome": "ERROR",
                "detail": "%s: %s" % (type(exc).__name__, exc), "SAFE": False}


def main():
    base = rc.base_request()
    eq = rc.run("compare", base)
    diff_req = rc.swap_outputs(base)
    diff = rc.run("compare", diff_req)
    rows = []

    rows.append(attempt("valid_equivalent_replay", base, eq))
    rows.append(attempt("valid_different_witness_replay", diff_req, diff))

    # A schema-valid EQUIVALENT report derived from a genuinely DIFFERENT run.
    def forge_equivalent(claim):
        v = claim["report"]["verification"]
        v["verdict"] = "EQUIVALENT"
        v["solverOutcome"] = "UNSAT"
        v["reasonCode"] = None
        v["witness"] = None

    rows.append(attempt("forged_equivalent_from_different", diff_req, diff,
                        mutate_claim=forge_equivalent))

    # Empty self-declared maps on an otherwise genuine conclusive report.
    def empty_maps(claim):
        claim["report"]["inputMap"] = []
        claim["report"]["outputMap"] = []

    rows.append(attempt("empty_self_declared_maps", base, eq, mutate_claim=empty_maps))

    def current_freshness(claim):
        claim["report"]["integrity"] = {
            "freshness": "CURRENT",
            "checkedBlock": {"number": 76020961, "hash": "0x" + "00" * 32},
        }

    rows.append(attempt("false_current_freshness", base, eq, mutate_claim=current_freshness))

    rows.append(attempt("swapped_reference_identity", base, eq,
                        reference_hash="0x" + "ab" * 32))
    rows.append(attempt("project_hash_mismatch", base, eq,
                        project_hash="0x" + "cd" * 32))

    def replaced_candidate(claim):
        claim["candidateIdentity"] = {
            "kind": "LOCAL_COMPOSITION", "netlistHash": "0x" + "ef" * 32}

    rows.append(attempt("replaced_candidate_identity", base, eq,
                        mutate_claim=replaced_candidate))

    def altered_netlist_hash(claim):
        claim["candidateManifest"]["netlistHash"] = "0x" + "12" * 32

    rows.append(attempt("altered_netlist_hash", base, eq,
                        mutate_claim=altered_netlist_hash))

    # Witness that does not distinguish: same outputs both sides.
    def non_differing_witness(claim):
        w = claim["report"]["verification"]["witness"]
        w["candidateOutputs"] = copy.deepcopy(w["referenceOutputs"])

    rows.append(attempt("witness_without_difference", diff_req, diff,
                        mutate_claim=non_differing_witness))

    # Witness with a plausible difference but a wrong distinguishing input.
    def wrong_input_witness(claim):
        w = claim["report"]["verification"]["witness"]
        bits = list(w["inputs"]["bits"])
        bits[0] = "1" if bits[0] == "0" else "0"
        w["inputs"]["bits"] = "".join(bits)

    rows.append(attempt("wrong_input_witness", diff_req, diff,
                        mutate_claim=wrong_input_witness))

    def unverified_sources(claim):
        claim["report"]["verification"]["sourceValidation"] = "UNVERIFIED"

    rows.append(attempt("unverified_source_flags", base, eq,
                        mutate_claim=unverified_sources))

    # Proof transplanted to another project: pin one project, claim another.
    other = rc.reversed_refs(base)
    other_actual = rc.run("compare", other)
    rows.append(attempt("reused_proof_other_project", base, other_actual))

    out = {
        "schema": "flip-m3-independent-consumer-review/1",
        "commit": "59751e20590117f0cbc4ef41b9b30d836e533f84",
        "cases": rows,
        "accepted": [r["case"] for r in rows if r["outcome"] == "ACCEPTED"],
        "attack_cases": len(rows) - 2,
        "safe_rejections": sum(1 for r in rows if r.get("SAFE")),
    }
    p = HERE / "consumer-attacks.json"
    p.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "accepted": out["accepted"],
        "attack_cases": out["attack_cases"],
        "safe_rejections": out["safe_rejections"],
        "cases": [(r["case"], r["outcome"], r.get("code")) for r in rows],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
