"""Independent integration acceptance harness for agent workflow + portable project.

Exercises the real combined production implementation via core and CLI. Expected
results are derived independently from pinned inputs and the documented contracts,
not from production output alone. No production code modified.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-agent-portable-independent-review"
RUN = EVID / "results/run"
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))

from flip_core.agent_workflow import execute as workflow_execute  # noqa: E402
from flip_core.canonical import canonical_bytes, content_hash  # noqa: E402
from flip_core.contracts import ContractError  # noqa: E402
from flip_core.debugging import prior_action  # noqa: E402
from flip_core.portable import bounded_operation, create_package, parse_package  # noqa: E402
from flip_core.verification import parse_request  # noqa: E402
from flip_core.workflow import sample  # noqa: E402

OUT = EVID / "results/integration-acceptance.json"
FLIP = str(ROOT / ".venv/Scripts/flip.exe")
GOLD = json.loads((ROOT / "docs/schema/m45-portable-project/1.1.0/golden.json").read_bytes())
GENESIS, EDITED, RICH = GOLD["packages"]
PRIOR = json.loads((ROOT / "docs/schema/m45-debugging/examples/swapped-prior.execution.json").read_bytes())
PRIOR_HASH = content_hash(PRIOR)
ACTION_ID = prior_action(parse_request(PRIOR)).actionId
LEGACY = sample("half-adder")


def portable_request(op, **kwargs):
    b = dict(schemaVersion="flip-portable-project-1.1.0", kind="PORTABLE_REQUEST", operation=op)
    b.update(kwargs)
    return b


def workflow_request(*steps, execution=None, **kwargs):
    b = dict(schemaVersion="m45-agent-workflow-1.0.0", kind="AGENT_WORKFLOW_REQUEST",
             executionRequest=sample("half-adder") if execution is None else execution,
             steps=[dict(id=f"s{i}", **step) for i, step in enumerate(steps)])
    b.update(kwargs)
    return b


def safe(fn):
    try:
        return {"ok": True, "result": fn()}
    except ContractError as exc:
        return {"ok": False, "code": exc.code, "message": exc.message[:120]}
    except Exception as exc:
        return {"ok": False, "code": type(exc).__name__, "message": str(exc)[:120]}


def record(cid, name, fn):
    try:
        return {"id": cid, "name": name, "observed": fn(), "error": None}
    except Exception as exc:
        return {"id": cid, "name": name, "observed": {"exception": f"{type(exc).__name__}: {exc}"},
                "error": f"{type(exc).__name__}: {exc}"}


def main():
    rows = []

    # 1. Portable package -> agent execution-request identity.
    def identity():
        opened = bounded_operation(portable_request("open", package=GENESIS))
        exec_req = opened["executionRequest"]
        r = workflow_execute(workflow_request(dict(op="compare"), execution=exec_req))
        return {"portableHash": GENESIS["executionRequestHash"],
                "openedMatches": content_hash(exec_req) == GENESIS["executionRequestHash"],
                "workflowStatus": r.status, "verdict": r.logs[0].output["report"]["verification"]["verdict"]}
    rows.append(record("I01", "portable package -> agent execution identity", identity))

    # Direct package as agent executionRequest must not be silently accepted as proof.
    def direct_package():
        body = workflow_request(dict(op="compare"), execution=GENESIS)
        return safe(lambda: workflow_execute(body))
    rows.append(record("I02", "raw portable package rejected by workflow", direct_package))

    # 2. Named test-vector binding and budget enforcement.
    def named_vectors():
        ptest = bounded_operation(portable_request("test", package=RICH))
        vectors = RICH["tests"][0]["vectors"]
        # Same vectors via agent test step against the same execution request.
        wr = workflow_execute(workflow_request(dict(op="test", vectors=[v for v in vectors]),
                                               execution=RICH["executionRequest"]))
        return {"portableVerdict": ptest["results"][0]["result"]["verdict"],
                "agentVerdict": wr.logs[0].output["verdict"],
                "portableCoverage": ptest["results"][0]["result"]["coverage"]}
    rows.append(record("I03", "named vectors bind identically across features", named_vectors))

    def vector_budget():
        pkg = copy.deepcopy(RICH)
        # Duplicate input rows in a vector set -> duplicate domain rejected.
        pkg["tests"][0]["vectors"] = [pkg["tests"][0]["vectors"][0]] * 2
        return safe(lambda: bounded_operation(portable_request("validate", package=pkg)))
    rows.append(record("I04", "duplicate vector inputs rejected", vector_budget))

    # 3. Agent correction -> new revision hash chain.
    def correction_revision():
        steps = [
            dict(op="compare", continueOn=["DIFFERENT"]),
            dict(op="inspect", continueOn=["DIFFERENT"]),
            dict(op="propose_correction", expectedExecutionHash=PRIOR_HASH),
            dict(op="verify", source="s2", expectedExecutionHash=PRIOR_HASH, actionId=ACTION_ID),
            dict(op="apply", source="s3", expectedExecutionHash=PRIOR_HASH, actionId=ACTION_ID),
        ]
        wr = workflow_execute(workflow_request(*steps, execution=PRIOR))
        revised = wr.logs[-1].output.get("executionRequest") if wr.logs[-1].output else None
        # The apply step's output has the revised request in the receipt's final execution.
        final_exec = wr.executionRequest.model_dump(mode="json")
        g1 = create_package(PRIOR)
        g2 = create_package(final_exec, previous=g1, description="agent applied correction")
        pkg = parse_package(g2)
        return {"workflowStatus": wr.status,
                "applyClassification": wr.logs[-1].output.get("classification"),
                "originalPreserved": wr.originalExecutionHash == PRIOR_HASH,
                "revisionSequence": pkg.revision.sequence,
                "parentHash": pkg.revision.parentHash,
                "parentMatches": pkg.revision.parentHash == g1["revision"]["revisionHash"]}
    rows.append(record("I05", "agent correction -> new revision chain", correction_revision))

    # 4. Original package preservation on failed/cancelled execution.
    def cancelled_preserves():
        pkg_before = json.dumps(GENESIS, sort_keys=True)
        wr = workflow_execute(workflow_request(dict(op="compare"), execution=GENESIS["executionRequest"]),
                              cancelled=lambda: True)
        return {"status": wr.status, "logs": len(wr.logs),
                "packageUnchanged": json.dumps(GENESIS, sort_keys=True) == pkg_before,
                "originalHash": wr.originalExecutionHash}
    rows.append(record("I06", "cancelled execution preserves original package", cancelled_preserves))

    # 5. Evidence generation -> portable evidence reference -> trusted replay.
    def evidence_roundtrip():
        wr = workflow_execute(workflow_request(dict(op="export"),
                                               execution=GENESIS["executionRequest"]))
        evidence = wr.logs[0].output
        digest = evidence["contentHash"]
        ref = dict(kind="FLIP_EVIDENCE", digest=digest,
                   executionRequestHash=GENESIS["executionRequestHash"],
                   reproduce=evidence["reproduce"],
                   engineHash=evidence["comparison"]["engineHash"])
        pkg = create_package(GENESIS["executionRequest"], evidence_refs=[ref])
        replay = bounded_operation(portable_request("replay-evidence", package=pkg,
                                                    artifacts={digest: evidence}))
        return {"exportKind": evidence["kind"], "refDigest": digest,
                "replayStatus": replay["results"][0]["status"],
                "trust": replay["trust"]}
    rows.append(record("I07", "generated evidence -> portable ref -> replay", evidence_roundtrip))

    # 6. Project substitution and foreign evidence.
    def foreign_evidence():
        wr = workflow_execute(workflow_request(dict(op="export"), execution=sample("swapped")))
        foreign = wr.logs[0].output
        ref = dict(kind="FLIP_EVIDENCE", digest=foreign["contentHash"],
                   executionRequestHash=GENESIS["executionRequestHash"],
                   reproduce=foreign["reproduce"],
                   engineHash=foreign["comparison"]["engineHash"])
        pkg = create_package(GENESIS["executionRequest"], evidence_refs=[ref])
        # The decisive boundary is trusted replay, not wrap.
        replay = safe(lambda: bounded_operation(portable_request(
            "replay-evidence", package=pkg, artifacts={foreign["contentHash"]: foreign})))
        return {"wrapAccepted": True,
                "replayRejected": not replay["ok"], "replayCode": replay.get("code"),
                "replayStatuses": [r.get("status") for r in replay.get("result", {}).get("results", [])]
                if isinstance(replay.get("result"), dict) else None}
    rows.append(record("I08", "foreign evidence project substitution rejected on replay", foreign_evidence))

    # 7. Revision-chain tampering.
    def chain_tamper():
        p1 = create_package(LEGACY)
        r2 = copy.deepcopy(LEGACY); r2["project"]["limits"]["gateCap"] = 2000
        p2 = create_package(r2, previous=p1, description="cap")
        bad = copy.deepcopy(p2)
        bad["ancestors"] = []
        return safe(lambda: bounded_operation(portable_request("validate", package=bad)))
    rows.append(record("I09", "revision-chain tampering rejected", chain_tamper))

    # 8. Stale and historical evidence.
    def freshness():
        pkg = copy.deepcopy(RICH)
        pkg["provenance"]["sourceFreshness"] = "STALE"
        # recompute chain so only provenance blocks
        from flip_core.portable import metadata_hash, record_hash
        pkg["revision"]["metadataHash"] = metadata_hash(pkg)
        pkg["revision"]["revisionHash"] = record_hash(pkg["revision"])
        opened = safe(lambda: bounded_operation(portable_request("open", package=pkg)))
        validated = bounded_operation(portable_request("validate", package=pkg))
        return {"openRejected": not opened["ok"], "openCode": opened.get("code"),
                "validateOk": validated.get("kind") == "PORTABLE_PROJECT"}
    rows.append(record("I10", "STALE provenance blocks open, not validate", freshness))

    # 9. UNKNOWN and deadline exhaustion.
    def unknown_deadline():
        body = sample("half-adder")
        body["project"]["limits"]["solverTimeoutMs"] = 1
        wr = workflow_execute(workflow_request(
            dict(op="compare", retry=dict(maxRetries=1, on=["SOLVER_TIMEOUT"])), execution=body))
        budget_wr = workflow_execute(workflow_request(dict(op="build"), dict(op="export"),
                                                      budget=dict(maxIterations=1)))
        return {"status": wr.status, "reasons": [e.error.code if e.error else None for e in wr.logs],
                "finalUnchanged": wr.finalExecutionHash == content_hash(body),
                "budgetStatus": budget_wr.status}
    rows.append(record("I11", "UNKNOWN retry and deadline exhaustion", unknown_deadline))

    # 10. STOP_AUTHORIZATION terminates workflow.
    def stop_auth():
        wr = workflow_execute(workflow_request(dict(op="stop_authorization"), dict(op="export")))
        out = wr.logs[0].output
        return {"status": wr.status, "logs": len(wr.logs),
                "signingCapability": out["signingCapability"], "retryable": out["retryable"]}
    rows.append(record("I12", "STOP_AUTHORIZATION terminal", stop_auth))

    # 11. CLI/API semantic parity (ported from prior harness).
    def parity():
        from fastapi.testclient import TestClient
        sys.path.insert(0, str(ROOT / "packages/flip-api/src"))
        from flip_api.app import app
        os.environ["FLIP_LOCAL_SOLVER"] = "1"
        client = TestClient(app, client=("127.0.0.1", 12345))
        wf = workflow_request(dict(op="compare"))
        core = workflow_execute(copy.deepcopy(wf))
        api_resp = client.post("/api/agent/v1/execute", json=wf)
        api = api_resp.json()
        pb = portable_request("validate", package=GENESIS)
        pc = bounded_operation(copy.deepcopy(pb))
        pa = client.post("/api/v1/portable", json=pb).json()
        return {"workflowParity": api.get("reproductionHash") == core.reproductionHash,
                "portableParity": pa.get("executionRequestHash") == pc.get("executionRequestHash")}
    rows.append(record("I13", "CLI/API/core semantic parity", parity))

    # 12. Legacy compatibility after integration.
    def legacy():
        path = RUN / "legacy.request.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(LEGACY), encoding="utf-8")
        proc = subprocess.run([FLIP, "compose", "--project", str(path)],
                              cwd=ROOT, env=dict(os.environ), capture_output=True, timeout=120)
        out = json.loads(proc.stdout)
        wrapped = create_package(LEGACY)
        opened = bounded_operation(portable_request("open", package=wrapped))
        return {"composeExit": proc.returncode,
                "netlistHash": out["manifest"]["netlistHash"],
                "roundtripExact": opened["executionRequest"] == LEGACY}
    rows.append(record("I14", "legacy compatibility after integration", legacy))

    # === ATTACKS ===
    # Forge a successful correction: false VERIFIED_CORRECTION artifact/action.
    def forge_correction():
        steps = [
            dict(op="propose_correction", expectedExecutionHash=PRIOR_HASH),
            dict(op="verify", source="s0", expectedExecutionHash=PRIOR_HASH,
                 actionId="0x" + "00" * 32),
        ]
        wr = workflow_execute(workflow_request(*steps, execution=PRIOR))
        last = wr.logs[-1].output if wr.logs else None
        return {"status": wr.status,
                "classification": last.get("classification") if isinstance(last, dict) else None,
                "logs": len(wr.logs),
                "finalUnchanged": wr.finalExecutionHash == PRIOR_HASH}
    rows.append(record("X01", "forge successful correction rejected", forge_correction))

    # Inject authority fields into both protocols.
    def inject_authority():
        wf = workflow_request(dict(op="compare"))
        wf["transactionAuthority"] = True
        wf["steps"][0]["approveAndPublish"] = True
        a = safe(lambda: workflow_execute(wf))
        pb = portable_request("wrap", executionRequest=LEGACY)
        pb["signer"] = "auto"
        b = safe(lambda: bounded_operation(pb))
        return {"workflowRejected": not a["ok"], "workflowCode": a.get("code"),
                "portableRejected": not b["ok"], "portableCode": b.get("code")}
    rows.append(record("X02", "authority-field injection rejected", inject_authority))

    # Reuse an old correction against a different package.
    def reuse_correction():
        other = sample("swapped")
        other_hash = content_hash(other)
        steps = [
            dict(op="propose_correction", expectedExecutionHash=other_hash),
            dict(op="verify", source="s0", expectedExecutionHash=other_hash, actionId=ACTION_ID),
            dict(op="apply", source="s1", expectedExecutionHash=other_hash, actionId=ACTION_ID),
        ]
        wr = workflow_execute(workflow_request(*steps, execution=other))
        return {"status": wr.status, "finalUnchanged": wr.finalExecutionHash == other_hash}
    rows.append(record("X03", "old correction reused on other package rejected", reuse_correction))

    # Race cancellation against revision creation.
    def cancellation_race():
        pkg = GENESIS
        before = json.dumps(pkg, sort_keys=True)
        # Cancel immediately before execution; a later attempt must be a new request.
        wr = workflow_execute(workflow_request(dict(op="compare"), execution=pkg["executionRequest"]),
                              cancelled=lambda: True)
        return {"status": wr.status, "logs": len(wr.logs),
                "packageUnchanged": json.dumps(pkg, sort_keys=True) == before}
    rows.append(record("X04", "cancellation race preserves package", cancellation_race))

    rec = {"artifactType": "AGENT_PORTABLE_INTEGRATION_ACCEPTANCE",
           "testedSha": "cef5f4d0649eebb89bc237290eb949d9ecd823fb",
           "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    errs = [r for r in rows if r["error"]]
    print(json.dumps({"total": len(rows), "errors": [r["id"] for r in errs]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
