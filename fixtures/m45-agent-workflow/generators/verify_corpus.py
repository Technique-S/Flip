"""Independent verifier for the M4.5-1A agent workflow corpus."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-agent-workflow"
FIX = ROOT / "fixtures/m45-agent-workflow"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    errors, checks = [], []
    manifest = json.loads((EVID / "MANIFEST.json").read_bytes())
    for item in manifest["files"]:
        path = ROOT / item["path"]
        data = path.read_bytes() if path.exists() else b""
        if sha(data) != item["sha256"] or len(data) != item["bytes"]:
            errors.append(f"hash mismatch {item['path']}")
    checks.append({"name": "manifest", "files": len(manifest["files"])})

    cases = json.loads((EVID / "cases/agent-workflow-cases.json").read_bytes())
    rows = cases["cases"]
    required = {
        "create_project", "search_library", "import", "build", "test", "compare",
        "inspect_difference", "inspect", "propose_correction", "verify", "export",
        "verify_bundle", "retry", "revalidate", "stop_authorization",
    }
    ids = {c["caseId"] for c in rows}
    if len(rows) != 15 or len(ids) != 15:
        errors.append("expected 15 unique cases")
    if {c["workflowStep"] for c in rows} != required:
        errors.append("workflow step coverage incomplete")
    classifications = {
        "EXECUTED_OFFLINE", "EXECUTED_WITH_LOOPBACK_DOUBLE",
        "EXECUTED_ABSENCE_EVIDENCE", "PARTIAL_LIBRARY_DEPENDENT",
        "SPEC_ONLY_NOT_IMPLEMENTED",
    }
    for c in rows:
        if c["classification"] not in classifications:
            errors.append(f"bad classification {c['caseId']}")
        bounds = c["bounds"]
        if not all(k in bounds for k in ("maxSteps", "deadlineMs")):
            errors.append(f"missing bounds {c['caseId']}")
        if not c["successCriteria"] or not c["failureCriteria"]:
            errors.append(f"missing criteria {c['caseId']}")
    checks.append({"name": "cases", "count": len(rows)})

    negatives = json.loads((EVID / "cases/negative-cases.json").read_bytes())
    if len(negatives["cases"]) != 5:
        errors.append("expected 5 negative cases")
    checks.append({"name": "negative_cases", "count": len(negatives["cases"])})

    protocol = json.loads((EVID / "protocol/agent-workflow-protocol.json").read_bytes())
    ops = {o["op"] for o in protocol["operations"]}
    needed = {"build", "test", "compare", "inspect", "propose_correction",
              "verify", "export", "stop_authorization"}
    if ops != needed:
        errors.append("protocol operations incomplete")
    if protocol["iterationContract"]["maxSteps"] > 12:
        errors.append("unbounded agent loop")
    checks.append({"name": "protocol", "operations": len(ops)})

    record = json.loads((EVID / "results/executed-commands.json").read_bytes())
    if record["total"] != 18 or record["exitMatches"] != 18:
        errors.append("CLI execution record incomplete")
    bad_fields = [e["caseId"] for e in record["entries"]
                  if any(not v["matches"] for v in e["expectedFields"].values())]
    if bad_fields:
        errors.append(f"field mismatches {bad_fields}")
    checks.append({"name": "executed_cli", "count": record["total"]})

    stray = [p for p in FIX.rglob("*.json")]
    if stray:
        errors.append(f"unregistered JSON under fixtures: {stray}")
    checks.append({"name": "fixtures_json_free", "count": len(stray)})

    print(json.dumps({"checks": checks, "errors": errors,
                      "result": "PASS" if not errors else "FAIL"},
                     indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
