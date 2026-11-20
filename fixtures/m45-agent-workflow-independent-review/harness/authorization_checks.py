"""Deep adversarial authorization, freshness and API-parity checks (Task B/D)."""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-agent-workflow-independent-review"
RUN = EVID / "results/run"
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))
sys.path.insert(0, str(ROOT / "packages/flip-api/src"))

from flip_core.agent_workflow import execute, parse_workflow  # noqa: E402
from flip_core.canonical import content_hash  # noqa: E402
from flip_core.contracts import ContractError  # noqa: E402
from flip_core.workflow import sample  # noqa: E402

OUT = EVID / "results/authorization-checks.json"
HIST = sample("half-adder")  # imports are HISTORICAL by construction


def wf(*steps, execution=None, **kwargs):
    b = dict(schemaVersion="m45-agent-workflow-1.0.0", kind="AGENT_WORKFLOW_REQUEST",
             executionRequest=sample("half-adder") if execution is None else execution,
             steps=[dict(id=f"s{i}", **step) for i, step in enumerate(steps)])
    b.update(kwargs)
    return b


def attempt(cid, name, fn):
    try:
        return {"id": cid, "name": name, "observed": fn(), "error": None}
    except Exception as exc:
        return {"id": cid, "name": name, "observed": {"exception": f"{type(exc).__name__}: {exc}"},
                "error": f"{type(exc).__name__}: {exc}"}


def main():
    rows = []

    # Freshness promotion: HISTORICAL execution stays HISTORICAL through compare/export.
    def historical_stays():
        r = execute(wf(dict(op="compare"), dict(op="export"), execution=HIST))
        comp = r.logs[0].output["report"]["integrity"]["freshness"]
        exp = r.logs[1].output["comparison"]["report"]["integrity"]["freshness"]
        return {"status": r.status, "compareFreshness": comp, "exportFreshness": exp,
                "promoted": "CURRENT" in (comp, exp)}
    rows.append(attempt("E01", "HISTORICAL never promoted to CURRENT", historical_stays))

    # Top-level authority fields injected at several layers.
    for i, field in enumerate(["permissions", "approvalToken", "transactionAuthority", "signer"]):
        def inject(field=field):
            body = wf(dict(op="compare"))
            body[field] = ["SIGN", "BROADCAST"]
            try:
                execute(body)
                return {"rejected": False, "field": field}
            except ContractError as exc:
                return {"rejected": True, "code": exc.code, "field": field}
        rows.append(attempt(f"E{i+2:02d}", f"top-level {field} rejected", inject))

    # Step-level authority field.
    def step_inject():
        body = wf(dict(op="compare"))
        body["steps"][0]["permissions"] = ["SIGN"]
        try:
            execute(body)
            return {"rejected": False}
        except ContractError as exc:
            return {"rejected": True, "code": exc.code}
    rows.append(attempt("E06", "step-level authority field rejected", step_inject))

    # Unsupported write method through discover (only read catalog operations allowed).
    def write_method():
        body = wf(dict(op="discover", libraryRequest=dict(operation="tapeout", limit=1)))
        try:
            parse_workflow(body)
            return {"rejected": False}
        except ContractError as exc:
            return {"rejected": True, "code": exc.code}
    rows.append(attempt("E07", "unsupported network write op rejected", write_method))

    # Fabricated STOP_AUTHORIZATION as a source artifact for a later step.
    def fake_stop_source():
        # A step cannot select stop_authorization output as an import/build source;
        # injected dicts are never accepted as executionRequest.
        fake = {"kind": "STOP_AUTHORIZATION", "signingCapability": True,
                "proposedAction": "SIGN_AND_BROADCAST"}
        body = wf(dict(op="build"), dict(op="export"))
        body["steps"][1]["bundle"] = fake  # not a valid verify_bundle source here
        try:
            r = execute(body)
            return {"status": r.status, "accepted": any(e.status == "COMPLETE" for e in r.logs)}
        except ContractError as exc:
            return {"status": "INVALID_INPUT", "code": exc.code, "accepted": False}
    rows.append(attempt("E08", "fabricated stop artifact not promotable", fake_stop_source))

    # API parity + loopback gating.
    def api():
        os.environ["FLIP_LOCAL_SOLVER"] = "1"
        from fastapi.testclient import TestClient
        from flip_api.app import app
        client = TestClient(app, client=("127.0.0.1", 12345))
        body = wf(dict(op="compare"), dict(op="export"))
        resp = client.post("/api/agent/v1/execute", json=body)
        api_result = resp.json()
        core = execute(body)
        parity = (api_result.get("status") == core.status
                  and api_result.get("reproductionHash") == core.reproductionHash)
        os.environ["FLIP_LOCAL_SOLVER"] = "0"
        disabled = client.post("/api/agent/v1/execute", json=body)
        return {"apiStatus": resp.status_code, "parity": parity,
                "solverDisabledStatus": disabled.status_code}
    rows.append(attempt("E09", "API parity and loopback gate", api))

    # Rejection of changed reference between steps (expectedExecutionHash on compare).
    def changed_reference():
        body = wf(dict(op="compare", expectedExecutionHash="0x" + "00" * 32))
        try:
            r = execute(body)
            return {"status": r.status, "logs": len(r.logs)}
        except ContractError as exc:
            return {"status": "INVALID_INPUT", "code": exc.code, "logs": 0}
    rows.append(attempt("E10", "changed reference between steps rejected", changed_reference))

    record = {"artifactType": "AGENT_AUTHORIZATION_CHECKS",
              "testedSha": "d2638d057b6236286480891d6fdd7dfb0402bc5a", "rows": rows}
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    bad = [r for r in rows if r["error"]]
    print(json.dumps({"total": len(rows), "exceptions": [r["id"] for r in bad]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
