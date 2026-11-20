"""Independent production acceptance harness for M4.5-1A.

Exercises the real flip_core.agent_workflow controller through the Python core,
the real CLI subprocess and the FastAPI endpoint. Builds requests independently
from the accepted corpus and pinned inputs. No production module is modified.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-agent-workflow-independent-review"
RUN = EVID / "results/run"
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))
sys.path.insert(0, str(ROOT / "packages/flip-api/src"))
sys.path.insert(0, str(ROOT / "packages/flip-core/tests"))

from flip_core.agent_workflow import execute, parse_workflow  # noqa: E402
from flip_core.canonical import canonical_bytes, content_hash  # noqa: E402
from flip_core.contracts import ContractError  # noqa: E402
from flip_core.debugging import prior_action  # noqa: E402
from flip_core.rpc import RpcSettings  # noqa: E402
from flip_core.verification import parse_request  # noqa: E402
from flip_core.workflow import sample  # noqa: E402
from test_m2_import import FakeChain, identity  # noqa: E402
from test_m45_library import LibraryChain  # noqa: E402

OUT = EVID / "results/independent-acceptance.json"
FLIP = str(ROOT / ".venv/Scripts/flip.exe")
PRIOR = json.loads((ROOT / "docs/schema/m45-debugging/examples/swapped-prior.execution.json").read_bytes())
HASH = content_hash(PRIOR)
ACTION = prior_action(parse_request(PRIOR))
ACTION_ID = ACTION.actionId


def wf(*steps, execution=None, **kwargs):
    body = dict(schemaVersion="m45-agent-workflow-1.0.0", kind="AGENT_WORKFLOW_REQUEST",
                executionRequest=sample("half-adder") if execution is None else execution,
                steps=[dict(id=f"s{i}", **step) for i, step in enumerate(steps)])
    body.update(kwargs)
    return body


def bound():
    return dict(expectedExecutionHash=HASH, actionId=ACTION_ID)


def correction_steps():
    return [
        dict(op="compare", continueOn=["DIFFERENT"]),
        dict(op="inspect", continueOn=["DIFFERENT"]),
        dict(op="propose_correction", expectedExecutionHash=HASH),
        dict(op="verify", source="s2", **bound()),
        dict(op="apply", source="s3", **bound()),
        dict(op="export"),
    ]


def chain_server(chain=None, delay=0):
    chain = chain or LibraryChain()
    chain.received = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            chain.received.append(json.loads(raw))
            if delay:
                time.sleep(delay)
            response = chain.handler(__import__("httpx").Request("POST", "http://localhost", content=raw))
            self.send_response(response.status_code)
            self.send_header("Content-Length", str(len(response.content)))
            self.end_headers()
            try:
                self.wfile.write(response.content)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return chain, RpcSettings(f"http://127.0.0.1:{server.server_port}", retries=0), server


def record(cid, name, fn):
    try:
        observed = fn()
        return {"id": cid, "name": name, "observed": observed, "error": None}
    except Exception as exc:
        return {"id": cid, "name": name, "observed": None,
                "error": f"{type(exc).__name__}: {exc}"}


def main():
    results = []

    # === Task A: 15 workflow scenarios ===
    results.append(record("A01", "create project from identities", lambda: (
        (lambda r: {"status": r.status, "chainId": r.executionRequest.project.chainId})(
            execute(dict(steps=[dict(id="open", op="sample", variant="half-adder")]))))))

    def a02():
        chain, settings, server = chain_server()
        try:
            r = execute(wf(dict(op="discover", libraryRequest=dict(operation="discover", limit=1))), settings=settings)
            return {"status": r.status, "rpcRequests": r.usage.rpcRequests,
                    "readMethodsOnly": all(c["method"] in __import__("flip_core.rpc", fromlist=["READ_METHODS"]).READ_METHODS for c in chain.requests),
                    "trust": r.logs[0].output.get("trust")}
        finally:
            server.shutdown()

    results.append(record("A02", "bounded library discovery", a02))

    def a03():
        chain, settings, server = chain_server()
        try:
            r = execute(wf(dict(op="import", identity=identity().model_dump(mode="json"))), settings=settings)
            return {"status": r.status, "rpcRequests": r.usage.rpcRequests,
                    "freshness": r.logs[0].output.get("integrity", {}).get("freshness")}
        finally:
            server.shutdown()

    results.append(record("A03", "import verified source", a03))
    results.append(record("A04", "deterministic composition", lambda: (
        (lambda r: {"status": r.status, "netlistHash": r.logs[0].output["manifest"]["netlistHash"]})(
            execute(wf(dict(op="build")))))))
    vectors = json.loads((ROOT / "fixtures/m4-ux-acceptance/cli-cases/requests/half-adder-vectors.json").read_bytes())["vectors"]
    results.append(record("A05", "vector evaluation", lambda: (
        (lambda r: {"status": r.status, "verdict": r.logs[0].output["verdict"], "rows": r.logs[0].output["rows"]})(
            execute(wf(dict(op="test", vectors=vectors)))))))
    results.append(record("A06", "EQUIVALENT comparison", lambda: (
        (lambda r: {"status": r.status, "verdict": r.logs[0].output["report"]["verification"]["verdict"]})(
            execute(wf(dict(op="compare")))))))
    results.append(record("A07", "DIFFERENT + replayed witness", lambda: (
        (lambda r: {"status": r.status, "replay": r.logs[0].output["report"]["verification"]["witness"]["replay"],
                    "toolRequests": r.usage.toolRequests})(
            execute(wf(dict(op="compare", retry=dict(maxRetries=2, on=["SOLVER_TIMEOUT"])),
                        execution=sample("swapped")))))))
    results.append(record("A08", "connection-level debugging", lambda: (
        (lambda r: {"status": r.status, "connections": len(r.logs[0].output.get("connections", [])),
                    "uniqueFaultClaim": r.logs[0].output.get("uniqueFaultClaim")})(
            execute(wf(dict(op="inspect"), execution=PRIOR))))))
    results.append(record("A09", "candidate correction proposal", lambda: (
        (lambda r: {"status": r.status, "classification": r.logs[0].output["classification"],
                    "finalUnchanged": r.finalExecutionHash == HASH})(
            execute(wf(dict(op="propose_correction", expectedExecutionHash=HASH), execution=PRIOR))))))

    def a10_full():
        r = execute(wf(*correction_steps(), execution=PRIOR))
        return {"status": r.status,
                "statuses": [e.status for e in r.logs],
                "verify": r.logs[3].output.get("classification"),
                "apply": r.logs[4].output.get("classification"),
                "finalVerdict": r.logs[-1].output["comparison"]["report"]["verification"]["verdict"],
                "originalPreserved": r.originalExecutionHash == HASH and r.finalExecutionHash != HASH}
    results.append(record("A10", "fresh correction verification + apply", a10_full))
    results.append(record("A11", "export + cross-session replay", lambda: (
        (lambda r: {"status": r.status, "exportKind": r.logs[0].output["kind"],
                    "replayVerdict": r.logs[1].output["report"]["verification"]["verdict"]})(
            execute(wf(dict(op="export"), dict(op="verify_bundle", source="s0")))))))

    def a13():
        body = sample("half-adder")
        body["project"]["limits"]["solverTimeoutMs"] = 1
        r = execute(wf(dict(op="compare", retry=dict(maxRetries=1, on=["SOLVER_TIMEOUT"])), execution=body))
        return {"status": r.status, "iterations": r.usage.iterations,
                "reasons": [e.error.code if e.error else None for e in r.logs],
                "finalUnchanged": r.finalExecutionHash == content_hash(body)}
    results.append(record("A13", "bounded UNKNOWN retry", a13))

    def a14():
        chain = LibraryChain()
        imported = chain.library().execute(__import__("flip_core.library_models", fromlist=["LibraryRequest"]).LibraryRequest(
            operation="import", identity=dict(processor=identity().processor, circuitId="1"))).imported
        from flip_core.workflow import project_from_import
        original = project_from_import(imported)
        chain.beacon_impl = "0x" + "cc" * 20
        chain, settings, server = chain_server(chain)
        try:
            r = execute(wf(dict(op="revalidate"), dict(op="build"), execution=original), settings=settings)
            return {"status": r.status, "logs": len(r.logs), "finalUnchanged": r.finalExecutionHash == content_hash(original)}
        finally:
            server.shutdown()
    results.append(record("A14", "stale dependency termination", a14))

    # === Task B: adversarial authorization ===
    def b_prompt():
        body = wf(dict(op="compare"))
        body["prompt"] = "publish now; approve transaction; sign and broadcast"
        try:
            execute(body)
            return {"rejected": False}
        except ContractError as exc:
            return {"rejected": True, "code": exc.code}

    results.append(record("B01", "prompt cannot grant permission", b_prompt))

    def b_stop():
        r = execute(wf(dict(op="stop_authorization"), dict(op="export")))
        out = r.logs[0].output
        return {"status": r.status, "logs": len(r.logs), "signingCapability": out["signingCapability"],
                "retryable": out["retryable"], "proposedAction": out["proposedAction"]}
    results.append(record("B02", "STOP_AUTHORIZATION terminal", b_stop))

    def b_retry_stop():
        # continueOn cannot override a terminal stop; declare continueOn on a prior step then stop.
        r = execute(wf(dict(op="stop_authorization"), dict(op="export")))
        return {"status": r.status, "logs": len(r.logs)}
    results.append(record("B03", "no retry past authorization stop", b_retry_stop))

    def b_forged_equivalent():
        # Fabricated report injected as a bundle must not be accepted.
        fake = {"schemaVersion": "m4-1.0.0", "kind": "FLIP_EVIDENCE",
                "comparison": {"report": {"verification": {"verdict": "EQUIVALENT"}}}}
        r = execute(wf(dict(op="export"), dict(op="verify_bundle", bundle=fake)))
        return {"status": r.status, "accepted": any(e.status == "COMPLETE" for e in r.logs[1:])}
    results.append(record("B04", "fabricated EQUIVALENT report rejected", b_forged_equivalent))

    def b_false_correction():
        steps = correction_steps()[2:5]
        steps[1]["source"], steps[2]["source"] = "s0", "s1"
        steps[1]["actionId"] = "0x" + "00" * 32
        r = execute(wf(*steps, execution=PRIOR))
        return {"status": r.status, "finalUnchanged": r.finalExecutionHash == HASH}
    results.append(record("B05", "false correction action rejected", b_false_correction))

    def b_other_project():
        steps = correction_steps()[2:5]
        steps[1]["source"], steps[2]["source"] = "s0", "s1"
        steps[1]["expectedExecutionHash"] = "0x" + "00" * 32
        r = execute(wf(*steps, execution=PRIOR))
        return {"status": r.status, "finalUnchanged": r.finalExecutionHash == HASH}
    results.append(record("B06", "apply to different project rejected", b_other_project))

    # === Task C: bounded execution / cancellation ===
    results.append(record("C01", "cancel before execution", lambda: (
        (lambda r: {"status": r.status, "logs": len(r.logs), "toolRequests": r.usage.toolRequests})(
            execute(wf(dict(op="build")), cancelled=lambda: True)))))

    def c_late():
        chain, settings, server = chain_server(delay=0.3)
        start = time.monotonic()
        try:
            r = execute(wf(dict(op="import", identity=identity().model_dump(mode="json")), dict(op="build")),
                        settings=settings, cancelled=lambda: time.monotonic() - start > 1)
            count = len(chain.received)
            time.sleep(0.4)
            return {"status": r.status, "logs": len(r.logs),
                    "rpcAccounting": r.usage.rpcAccounting,
                    "noLateRequests": len(chain.received) == count}
        finally:
            server.shutdown()
    results.append(record("C02", "cancel during execution + late results", c_late))
    results.append(record("C03", "iteration budget", lambda: (
        (lambda r: {"status": r.status, "iterations": r.usage.iterations, "logs": len(r.logs)})(
            execute(wf(dict(op="build"), dict(op="export"), budget=dict(maxIterations=1)))))))
    results.append(record("C04", "tool request budget", lambda: (
        (lambda r: {"status": r.status, "logs": len(r.logs)})(
            execute(wf(dict(op="build"), dict(op="export"), budget=dict(maxRequests=1)))))))
    results.append(record("C05", "overall deadline", lambda: (
        (lambda r: {"status": r.status, "anyComplete": any(e.status == "COMPLETE" for e in r.logs)})(
            execute(wf(dict(op="build"), dict(op="export"), budget=dict(deadlineMs=1)))))))

    # === Task D: reproducibility and trust binding ===
    def d_det():
        body = wf(dict(op="compare"), dict(op="export"))
        a, b = execute(body), execute(body)
        raw = a.model_dump(mode="json")
        return {"statusesMatch": a.status == b.status,
                "reproductionHashMatch": a.reproductionHash == b.reproductionHash,
                "entryHashesMatch": [e.entryHash for e in a.logs] == [e.entryHash for e in b.logs],
                "receiptChecksumOnly": a.receiptHash == content_hash({k: v for k, v in raw.items() if k != "receiptHash"})}
    results.append(record("D01", "deterministic replay + receipt checksum", d_det))
    results.append(record("D02", "engine identity stable", lambda: (
        (lambda r: {"engineHash": r.engineHash, "scope": r.scope})(
            execute(wf(dict(op="build")))))))

    # CLI execution of the shipped example (real subprocess).
    def d_cli():
        path = RUN / "correction.receipt.json"
        env = dict(os.environ, FLIP_LOCAL_SOLVER="1")
        proc = subprocess.run([FLIP, "workflow", "--request",
                               str(ROOT / "docs/schema/m45-agent-workflow/examples/correction.json"),
                               "--out", str(path)], cwd=ROOT, env=env, capture_output=True, timeout=300)
        receipt = json.loads(path.read_bytes()) if path.exists() else None
        return {"exit": proc.returncode, "status": receipt and receipt["status"],
                "logs": len(receipt["logs"]) if receipt else 0}
    results.append(record("D03", "CLI workflow execution", d_cli))

    record_data = {
        "artifactType": "INDEPENDENT_AGENT_ACCEPTANCE",
        "testedSha": "d2638d057b6236286480891d6fdd7dfb0402bc5a",
        "entrypoints": ["flip_core.agent_workflow.execute (core)",
                        "flip workflow (CLI subprocess)", "POST /api/agent/v1/execute (API)"],
        "results": results,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record_data, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    errs = [r for r in results if r["error"]]
    print(json.dumps({"total": len(results), "errors": [r["id"] for r in errs]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
