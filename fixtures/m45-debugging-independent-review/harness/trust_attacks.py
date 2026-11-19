"""Additional Task B trust attacks: witness forgery and identity substitution.

The DebugRequest schema has no witness field and binds identities through the pinned
imports; these attempts deliberately inject forbidden fields and swap identities to
confirm the engine fails closed rather than promoting a fabricated diagnosis.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "docs/evidence/m45-debugging-independent-review/results/run"
OUT = ROOT / "docs/evidence/m45-debugging-independent-review/results/trust-attacks.json"
FLIP = str(ROOT / ".venv/Scripts/flip.exe")
BASE = json.loads((RUN / "base.request.json").read_bytes())


def attempt(cid, label, mutate):
    payload = json.loads(json.dumps(BASE))
    mutate(payload)
    path = RUN / f"{cid}.request.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    proc = subprocess.run([FLIP, "debug", "--request", str(path)], cwd=ROOT,
                          env=dict(os.environ, FLIP_LOCAL_SOLVER="1"),
                          capture_output=True, timeout=120)
    stdout = proc.stdout.decode("utf-8", "replace")
    try:
        result = json.loads(stdout)
    except ValueError:
        result = None
    return {"caseId": cid, "name": label, "exit": proc.returncode,
            "classification": (result or {}).get("classification"),
            "correction": ((result or {}).get("correction") or {}).get("classification"),
            "connections": len((result or {}).get("connections", [])),
            "stdoutSha256": hashlib.sha256(proc.stdout).hexdigest(),
            "safe": proc.returncode in (2, 3)
                    and (result or {}).get("classification") in (None, "UNKNOWN")
                    and not (result or {}).get("connections")
                    and (result or {}).get("correction") is None,
            "passed": proc.returncode in (2, 3)
                      and (result or {}).get("classification") in (None, "UNKNOWN")
                      and not (result or {}).get("connections")
                      and (result or {}).get("correction") is None}


def main():
    def forged_witness(p):
        p["witness"] = {"inputs": {"bits": "00"},
                        "referenceOutputs": {"bits": "00"},
                        "candidateOutputs": {"bits": "11"}}

    def swapped_identity(p):
        imports = p["executionRequest"]["imports"]
        imports[0]["circuits"][0]["identity"]["circuitId"] = "999"

    def duplicate_closure(p):
        imports = p["executionRequest"]["imports"]
        imports.append(json.loads(json.dumps(imports[0])))

    rows = [
        attempt("B10", "Forged witness inputs injected into request", forged_witness),
        attempt("B11", "Changed candidate circuit identity", swapped_identity),
        attempt("B12", "Duplicated substituted dependency closure", duplicate_closure),
    ]
    record = {"artifactType": "DEBUG_TRUST_ATTACKS",
              "testedSha": "b9d3fc3f87d34cc6bd46e2a716504fe113f44f48",
              "rows": rows, "passed": sum(1 for r in rows if r["passed"]),
              "total": len(rows)}
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps({"passed": record["passed"], "total": record["total"],
                      "failures": [r["caseId"] for r in rows if not r["passed"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
