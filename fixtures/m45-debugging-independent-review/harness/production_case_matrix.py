"""Map the original 10-case debugging corpus onto the real production debugger.

Each variant is derived from the shipped historical request by one declared edit,
mirroring a corpus category. Results are recorded with exact exit codes, semantic
fields and hashes. No production output is taken as the expected oracle: the original
corpus expectation is compared against the observed classification.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-debugging-independent-review"
RUN = EVID / "results/run"
FLIP = str(ROOT / ".venv/Scripts/flip.exe")
BASE = json.loads((RUN / "base.request.json").read_bytes())
BASE_ACTION = json.loads((RUN / "base.result.json").read_bytes())["actions"][0]["actionId"]
OUT = EVID / "results/production-case-matrix.json"


def candidate(request):
    return request["executionRequest"]["project"]["candidate"]


def reference(request):
    return request["executionRequest"]["project"]["referenceCandidate"]


def component(design, name):
    return next(c for c in design["components"] if c["instanceId"] == name)


def run(cid, label, request, expected_class, expected_attribution=None):
    path = RUN / f"{cid}.request.json"
    out = RUN / f"{cid}.result.json"
    path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    proc = subprocess.run([FLIP, "debug", "--request", str(path), "--out", str(out)],
                          cwd=ROOT, env=dict(os.environ, FLIP_LOCAL_SOLVER="1"),
                          capture_output=True, timeout=120)
    result = json.loads(out.read_bytes()) if out.exists() else None
    classification = (result or {}).get("classification")
    attribution = (result or {}).get("attribution")
    return {
        "caseId": cid, "corpusCase": label, "expectedClassification": expected_class,
        "expectedAttribution": expected_attribution,
        "exit": proc.returncode, "classification": classification,
        "attribution": attribution, "reasonCode": (result or {}).get("reasonCode"),
        "differingBits": (result or {}).get("differingOutputBits"),
        "connections": len((result or {}).get("connections", [])),
        "actions": len((result or {}).get("actions", [])),
        "correction": ((result or {}).get("correction") or {}).get("classification"),
        "uniqueFaultClaim": (result or {}).get("uniqueFaultClaim"),
        "resultSha256": __import__("hashlib").sha256(out.read_bytes()).hexdigest() if out.exists() else None,
        "safeRejection": expected_class == "SAFE_REJECTION" and proc.returncode == 3
                         and result is None,
        "passed": (classification == expected_class and (
            expected_attribution is None or attribution == expected_attribution))
                  or (expected_class == "SAFE_REJECTION" and proc.returncode == 3
                      and result is None),
    }


def variants():
    rows = []

    rows.append(run("D01", "swapped_outputs", json.loads(json.dumps(BASE)),
                    "VERIFIED_DIFFERENCE", "AMBIGUOUS_MULTIPLE_CAUSES"))

    r = json.loads(json.dumps(BASE))
    component(candidate(r), "sum")["inputs"] = [{"component": None, "pin": 1},
                                                 {"component": None, "pin": 0}]
    rows.append(run("D02", "incorrect_ref_input_mapping", r, "VERIFIED_DIFFERENCE"))

    r = json.loads(json.dumps(BASE))
    component(candidate(r), "sum")["inputs"] = [{"component": None, "pin": 0},
                                                 {"component": None, "pin": 0}]
    rows.append(run("D03", "duplicate_fan_out", r, "VERIFIED_DIFFERENCE",
                    "AMBIGUOUS_MULTIPLE_CAUSES"))

    r = json.loads(json.dumps(BASE))
    component(candidate(r), "sum")["inputs"] = [{"component": None, "pin": 0},
                                                 {"component": None, "pin": 9}]
    rows.append(run("D04", "disconnected_or_unbound_pin", r, "SAFE_REJECTION"))

    r = json.loads(json.dumps(BASE))
    component(candidate(r), "nand0")["inputs"] = [{"component": None, "pin": 1},
                                                   {"component": None, "pin": 0}]
    rows.append(run("D05", "wrong_output_ordering_analog", r, "VERIFIED_DIFFERENCE"))

    r = json.loads(json.dumps(BASE))
    # Base candidate already swaps outputs; also reverse the XOR REF inputs.
    component(candidate(r), "sum")["inputs"] = [{"component": None, "pin": 1},
                                                 {"component": None, "pin": 0}]
    rows.append(run("D06", "multiple_changed_connections", r, "VERIFIED_DIFFERENCE"))

    r = json.loads(json.dumps(BASE))
    r["executionRequest"]["imports"][0]["circuits"][0]["netlist"] = (
        r["executionRequest"]["imports"][1]["circuits"][0]["netlist"])
    rows.append(run("D07", "nested_or_substituted_dependency", r, "SAFE_REJECTION"))

    r = json.loads(json.dumps(BASE))
    candidate(r)["outputs"] = json.loads(json.dumps(reference(r)["outputs"]))
    rows.append(run("D08", "equivalent_rewiring", r, "NO_FAULT_ATTRIBUTION",
                    "NO_FAULT_ATTRIBUTION"))

    r = json.loads(json.dumps(BASE))
    component(candidate(r), "nand0")["inputs"] = [{"component": None, "pin": 1},
                                                   {"component": None, "pin": 0}]
    component(candidate(r), "sum")["inputs"] = [{"component": None, "pin": 1},
                                                 {"component": None, "pin": 0}]
    rows.append(run("D09", "several_contributing_connections", r, "VERIFIED_DIFFERENCE"))

    r = json.loads(json.dumps(BASE))
    # Keep the output swap (base defect) and reverse the XOR REF inputs too.
    component(candidate(r), "sum")["inputs"] = [{"component": None, "pin": 1},
                                                 {"component": None, "pin": 0}]
    rows.append(run("D10", "not_uniquely_identifiable", r, "VERIFIED_DIFFERENCE"))

    # Attacks on diagnostic trust.
    r = json.loads(json.dumps(BASE))
    r["executionRequest"]["project"]["projectId"] = "forged-project-id"
    rows.append(run("B04", "changed_project_hash", r, "VERIFIED_DIFFERENCE"))

    r = json.loads(json.dumps(BASE))
    r["correction"] = {"classification": "VERIFIED_CORRECTION"}
    rows.append(run("B05", "false_verified_correction_field", r, "SAFE_REJECTION"))

    r = json.loads(json.dumps(BASE))
    r["connections"] = [{"connectionRef": "top/element[0].in[0]"}]
    rows.append(run("B06", "fabricated_connection_paths", r, "SAFE_REJECTION"))

    r = json.loads(json.dumps(BASE))
    r["operation"] = "verify-correction"
    r["actionId"] = BASE_ACTION
    r["executionRequest"]["project"]["projectId"] = "another-project"
    rows.append(run("B07", "reused_action_from_other_project", r, "UNKNOWN"))

    r = json.loads(json.dumps(BASE))
    r.setdefault("budget", {})["maxNodes"] = 1
    rows.append(run("B08", "resource_exhaustion", r, "UNKNOWN", "UNKNOWN_NO_ATTRIBUTION"))

    r = json.loads(json.dumps(BASE))
    r.setdefault("budget", {})["maxDepth"] = 0
    rows.append(run("B09", "ref_depth_limit", r, "UNKNOWN", "UNKNOWN_NO_ATTRIBUTION"))
    return rows


def main():
    rows = variants()
    record = {"artifactType": "PRODUCTION_CASE_MATRIX",
              "testedSha": "b9d3fc3f87d34cc6bd46e2a716504fe113f44f48",
              "corpus": "fixtures/m45-debugging/cases/debugging-corpus.json",
              "rows": rows, "passed": sum(1 for r in rows if r["passed"]),
              "total": len(rows)}
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps({"passed": record["passed"], "total": record["total"],
                      "failures": [r["caseId"] for r in rows if not r["passed"]]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
