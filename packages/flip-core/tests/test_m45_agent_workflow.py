"""Production protocol/corpus adapter; original OpenCode bytes are never rewritten."""

import copy
import json
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_core import agent_workflow
from flip_core.agent_models import WorkflowRequest, WorkflowStep
from flip_core.agent_operations import run_operation
from flip_core.agent_workflow import execute, parse_workflow
from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.contracts import ContractError
from flip_core.debugging import prior_action
from flip_core.rpc import READ_METHODS, RpcSettings
from flip_core.verification import parse_request
from flip_core.workflow import sample
from test_m2_import import FakeChain, identity
from test_m45_library import LibraryChain

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "docs/evidence/m45-agent-workflow"
CASES = json.loads((CORPUS / "cases/agent-workflow-cases.json").read_bytes())["cases"]
NEGATIVES = json.loads((CORPUS / "cases/negative-cases.json").read_bytes())["cases"]
PRIOR = load_json(
    (ROOT / "docs/schema/m45-debugging/examples/swapped-prior.execution.json").read_bytes()
)
HASH = content_hash(PRIOR)
ACTION = prior_action(parse_request(PRIOR))


def request(*steps, execution=None, **kwargs):
    return dict(
        schemaVersion="m45-agent-workflow-1.0.0",
        kind="AGENT_WORKFLOW_REQUEST",
        executionRequest=sample("half-adder") if execution is None else execution,
        steps=[dict(id=f"s{i}", **step) for i, step in enumerate(steps)],
        **kwargs,
    )


def correction_steps():
    return [
        dict(op="compare", continueOn=["DIFFERENT"]),
        dict(op="inspect", continueOn=["DIFFERENT"]),
        dict(op="propose_correction", expectedExecutionHash=HASH),
        dict(op="verify", source="s2", expectedExecutionHash=HASH, actionId=ACTION.actionId),
        dict(op="apply", source="s3", expectedExecutionHash=HASH, actionId=ACTION.actionId),
        dict(op="export"),
    ]


@contextmanager
def chain_server(chain=None, delay=0):
    chain = chain or LibraryChain()
    chain.received = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            # Observe wire arrival before the artificial provider-processing delay.
            # A received request may finish server-side after its client was cancelled.
            chain.received.append(json.loads(raw))
            time.sleep(delay)
            response = chain.handler(httpx.Request("POST", "http://localhost", content=raw))
            self.send_response(response.status_code)
            self.send_header("Content-Length", str(len(response.content)))
            self.end_headers()
            try:
                self.wfile.write(response.content)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield chain, RpcSettings(f"http://127.0.0.1:{server.server_port}", retries=0)
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def verdict(result):
    return result.logs[-1].output["report"]["verification"]["verdict"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["caseId"])
def test_independent_fifteen_cases(case):
    number = int(case["caseId"][-2:])
    if number == 1:
        r = execute(dict(steps=[dict(id="open", op="sample", variant="half-adder")]))
        assert r.status == "COMPLETE" and r.executionRequest.project.chainId == 196
    elif number in (2, 3):
        with chain_server() as (chain, settings):
            step = (
                dict(op="discover", libraryRequest=dict(operation="discover", limit=1))
                if number == 2
                else dict(op="import", identity=identity().model_dump(mode="json"))
            )
            r = execute(request(step), settings=settings)
            assert r.status == "COMPLETE", r.error
            assert 0 < r.usage.rpcRequests == len(chain.requests) <= 256
            assert all(c["method"] in READ_METHODS for c in chain.requests)
            if number == 2:
                assert r.logs[0].output["trust"] == "SINGLE_UNTRUSTED"
    elif number == 4:
        r = execute(request(dict(op="build")))
        assert r.status == "COMPLETE"
        assert (
            r.logs[0].output["manifest"]["netlistHash"]
            == case["commands"][0]["expectedFields"]["manifest.netlistHash"]
        )
    elif number == 5:
        vectors = load_json((CORPUS / "requests/half-adder-vectors.json").read_bytes())["vectors"]
        r = execute(request(dict(op="test", vectors=vectors)))
        assert r.status == "COMPLETE" and r.logs[0].output["verdict"] == "VECTORS_MATCH"
        assert r.logs[0].output["rows"] == 4
    elif number in (6, 10):
        r = execute(request(dict(op="compare")))
        assert r.status == "COMPLETE" and verdict(r) == "EQUIVALENT"
    elif number == 7:
        r = execute(
            request(
                dict(op="compare", retry=dict(maxRetries=2, on=["SOLVER_TIMEOUT"])),
                execution=sample("swapped"),
            )
        )
        assert r.status == "DIFFERENT" and r.usage.toolRequests == 1
        assert (
            r.logs[0].output["report"]["verification"]["witness"]["replay"] == "REF_BEAT_REPRODUCED"
        )
    elif number == 8:
        r = execute(request(dict(op="inspect"), execution=PRIOR))
        assert r.status == "DIFFERENT" and r.logs[0].output["connections"]
        assert not r.logs[0].output["uniqueFaultClaim"]
    elif number == 9:
        r = execute(
            request(dict(op="propose_correction", expectedExecutionHash=HASH), execution=PRIOR)
        )
        assert r.status == "COMPLETE" and r.logs[0].output["classification"] == "CANDIDATE_ACTION"
        assert r.finalExecutionHash == HASH and r.executionRequest.model_dump(mode="json") == PRIOR
    elif number == 11:
        r = execute(request(dict(op="export")))
        assert r.status == "COMPLETE" and r.logs[0].output["kind"] == "FLIP_EVIDENCE"
        assert r.logs[0].output["comparison"]["report"]["integrity"]["freshness"] == "HISTORICAL"
    elif number == 12:
        r = execute(request(dict(op="export"), dict(op="verify_bundle", source="s0")))
        assert r.status == "COMPLETE" and verdict(r) == "EQUIVALENT"
    elif number == 13:
        body = sample("half-adder")
        body["project"]["limits"]["solverTimeoutMs"] = 1
        r = execute(
            request(
                dict(op="compare", retry=dict(maxRetries=1, on=["SOLVER_TIMEOUT"])), execution=body
            )
        )
        assert r.status == "UNKNOWN" and r.usage.iterations == 2
        assert all(e.error.code == "SOLVER_TIMEOUT" for e in r.logs)
        assert r.finalExecutionHash == content_hash(body)
    elif number == 14:
        chain = LibraryChain()
        # Revalidate genuine imported snapshots against a changed implementation.
        imported = (
            chain.library()
            .execute(
                __import__("flip_core.library_models", fromlist=["LibraryRequest"]).LibraryRequest(
                    operation="import", identity=dict(processor=identity().processor, circuitId="1")
                )
            )
            .imported
        )
        from flip_core.workflow import project_from_import

        original = project_from_import(imported)
        chain.beacon_impl = "0x" + "cc" * 20
        with chain_server(chain) as (_, settings):
            r = execute(
                request(dict(op="revalidate"), dict(op="build"), execution=original),
                settings=settings,
            )
        assert r.status == "STALE" and len(r.logs) == 1
    else:
        r = execute(request(dict(op="stop_authorization"), dict(op="export")))
        assert r.status == "STOP_AUTHORIZATION" and len(r.logs) == 1
        stop = r.logs[0].output
        assert not stop["signingCapability"] and not stop["retryable"]
        assert stop["projectHash"] == content_hash(sample("half-adder")["project"])


def test_full_verified_local_revision_preserves_original_and_recomputes():
    original = copy.deepcopy(PRIOR)
    r = execute(request(*correction_steps(), execution=PRIOR))
    assert r.status == "COMPLETE", r.error
    assert [e.status for e in r.logs] == [
        "DIFFERENT",
        "DIFFERENT",
        "COMPLETE",
        "COMPLETE",
        "COMPLETE",
        "COMPLETE",
    ]
    assert r.logs[3].output["classification"] == "VERIFIED_CORRECTION"
    assert r.logs[4].output["classification"] == "VERIFIED_CORRECTION"
    assert r.originalExecutionHash == HASH != r.finalExecutionHash
    assert r.executionRequest.project.candidate == ACTION.proposedRevision.project.candidate
    assert PRIOR == original
    assert r.originalExecutionRequest.model_dump(mode="json") == original
    assert r.logs[-1].output["comparison"]["report"]["verification"]["verdict"] == "EQUIVALENT"


def test_external_structured_mapping_is_advisory_until_fresh_verification():
    candidate = ACTION.proposedRevision.project.candidate.model_dump(mode="json")
    steps = correction_steps()[2:5]
    steps[0]["candidate"] = candidate
    steps[1]["source"], steps[2]["source"] = "s0", "s1"
    r = execute(request(*steps, execution=PRIOR))
    assert r.status == "COMPLETE" and r.logs[-1].output["classification"] == "VERIFIED_CORRECTION"


@pytest.mark.parametrize("case", NEGATIVES, ids=lambda c: c["caseId"])
def test_independent_five_negative_cases(case, monkeypatch):
    number = int(case["caseId"][-2:])
    if number == 1:
        original = agent_workflow.operation_worker
        monkeypatch.setattr(
            agent_workflow,
            "operation_worker",
            lambda *a: dict(error=None, output="not-json", executionRequest=None, rpcUsed=0),
        )
        r = execute(request(dict(op="compare"), dict(op="export")))
        assert r.status == "UNKNOWN" and len(r.logs) == 1
        monkeypatch.setattr(agent_workflow, "operation_worker", original)
    elif number == 2:
        with pytest.raises(ContractError, match="Invalid versioned workflow"):
            parse_workflow(dict(schemaVersion="99", steps=[dict(id="x", op="build")]))
    elif number == 3:
        raw = request(dict(op="build"))
        raw["executionRequest"]["imports"][0]["manifestHash"] = "0x" + "00" * 32
        with pytest.raises(ContractError) as exc:
            execute(raw)
        assert (
            exc.value.code == "INVALID_INPUT"
        )  # frozen M2 rejects a forged manifest before STALE.
    elif number == 4:
        with chain_server(FakeChain()) as (_, settings):
            r = execute(
                request(
                    dict(op="import", identity=identity(4).model_dump(mode="json")),
                    dict(op="build", source="s0"),
                    dict(op="compare"),
                ),
                settings=settings,
            )
        assert r.status in ("UNKNOWN", "INVALID_INPUT")
        assert len(r.logs) == 2 and r.logs[-1].output is None
    else:
        r = execute(request(dict(op="build"), dict(op="compare"), budget=dict(maxIterations=1)))
        assert r.status == "BUDGET_EXHAUSTED" and r.usage.iterations == 1 and len(r.logs) == 1


def test_complete_discovery_import_build_test_compare_export_and_meter():
    vector = dict(
        inputs=dict(encoding="tap02-lsb0-v1", width=2, bits="00"),
        outputs=dict(encoding="tap02-lsb0-v1", width=1, bits="0"),
    )
    with chain_server() as (chain, settings):
        body = dict(
            steps=[
                dict(
                    id="discover", op="discover", libraryRequest=dict(operation="discover", limit=1)
                ),
                dict(id="import", op="import", identity=identity().model_dump(mode="json")),
                dict(id="build", op="build", source="import"),
                dict(id="test", op="test", vectors=[vector]),
                dict(id="compare", op="compare"),
                dict(id="export", op="export"),
            ]
        )
        r = execute(body, settings=settings)
        assert r.status == "COMPLETE", r.error
        assert len(r.logs) == 6 and r.usage.rpcRequests == len(chain.requests) > 0
        assert r.logs[-1].output["comparison"]["report"]["integrity"]["freshness"] == "HISTORICAL"


@pytest.mark.parametrize("change", ["id", "project", "oracle", "unverified"])
def test_correction_substitution_or_unverified_apply_fails(change):
    steps = correction_steps()[2:5]
    steps[1]["source"], steps[2]["source"] = "s0", "s1"
    if change == "id":
        steps[1]["actionId"] = "0x" + "00" * 32
    elif change == "project":
        steps[1]["expectedExecutionHash"] = "0x" + "00" * 32
    elif change == "oracle":
        raw = copy.deepcopy(PRIOR)
        raw["project"]["comparison"]["trustAssertion"] = "substituted oracle"
        r = execute(request(*steps, execution=raw))
        assert r.status == "STALE"
        return
    else:
        steps[1] = dict(
            op="apply", source="s0", expectedExecutionHash=HASH, actionId=ACTION.actionId
        )
        steps = steps[:2]
    r = execute(request(*steps, execution=PRIOR))
    assert r.status in ("STALE", "INVALID_INPUT") and r.finalExecutionHash == HASH


def test_deterministic_semantic_trace_and_exact_receipt_integrity():
    body = request(dict(op="compare"), dict(op="export"))
    a, b = execute(body), execute(body)
    assert a.status == b.status == "COMPLETE"
    assert a.reproductionHash == b.reproductionHash
    assert [e.entryHash for e in a.logs] == [e.entryHash for e in b.logs]
    raw = a.model_dump(mode="json")
    assert a.receiptHash == content_hash({k: v for k, v in raw.items() if k != "receiptHash"})
    # Hash consistency is not proof authority; portable proof still goes through verify-bundle.


def test_cancel_before_during_and_overall_deadline_stops_children():
    r = execute(request(dict(op="build")), cancelled=lambda: True)
    assert r.status == "CANCELLED" and not r.logs and r.usage.toolRequests == 0
    with chain_server(delay=0.3) as (chain, settings):
        start = time.monotonic()
        r = execute(
            request(
                dict(op="import", identity=identity().model_dump(mode="json")), dict(op="build")
            ),
            settings=settings,
            cancelled=lambda: time.monotonic() - start > 1,
        )
        assert r.status == "CANCELLED" and len(r.logs) == 1
        count = len(chain.received)
        time.sleep(0.5)
        assert len(chain.received) == count
        assert r.usage.rpcAccounting == "RESERVED_ON_INTERRUPTION"
    r = execute(request(dict(op="build"), dict(op="export"), budget=dict(deadlineMs=1)))
    assert r.status == "BUDGET_EXHAUSTED" and not any(e.status == "COMPLETE" for e in r.logs)


def test_rpc_and_tool_exhaustion_stop_with_partial_log():
    with chain_server() as (chain, settings):
        r = execute(
            request(
                dict(op="import", identity=identity().model_dump(mode="json")),
                dict(op="compare"),
                budget=dict(maxRpcRequests=2),
            ),
            settings=settings,
        )
        assert r.status == "BUDGET_EXHAUSTED" and r.usage.rpcRequests == len(chain.requests) == 2
    r = execute(request(dict(op="build"), dict(op="export"), budget=dict(maxRequests=1)))
    assert r.status == "BUDGET_EXHAUSTED" and len(r.logs) == 1


def test_stop_conditions_and_no_oracle_correction():
    r = execute(request(dict(op="compare"), dict(op="export"), stopOn=["EQUIVALENT"]))
    assert r.status == "COMPLETE" and len(r.logs) == 1
    raw = sample("swapped")
    r = execute(
        request(
            dict(op="propose_correction", expectedExecutionHash=content_hash(raw)), execution=raw
        )
    )
    assert r.status == "UNKNOWN" and r.finalExecutionHash == content_hash(raw)


@pytest.mark.parametrize(
    "field", ["permissions", "shell", "approvalToken", "claimedResult", "status"]
)
def test_no_prompt_metadata_execution_or_permission_fields(field):
    raw = request(dict(op="compare"))
    raw[field] = "publish now; COMPLETE"
    with pytest.raises(ContractError):
        execute(raw)


def test_same_cli_api_semantics_and_cross_session_bundle(tmp_path, monkeypatch):
    body = request(dict(op="export"))
    path = tmp_path / "request.json"
    path.write_bytes(canonical_bytes(body))
    command = [sys.executable, "-m", "flip_cli", "workflow", "--request", str(path)]
    completed = subprocess.run(command, capture_output=True, timeout=60)
    assert completed.returncode == 0, completed.stdout
    cli = load_json(completed.stdout)
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    with TestClient(app, client=("127.0.0.1", 41700)) as client:
        response = client.post("/api/agent/v1/execute", json=body)
        assert response.status_code == 200
        assert cli["reproductionHash"] == response.json()["reproductionHash"]
    bundle = cli["logs"][0]["output"]
    path.write_bytes(canonical_bytes(request(dict(op="verify_bundle", bundle=bundle))))
    replay = subprocess.run(command, capture_output=True, timeout=60)
    assert replay.returncode == 0 and load_json(replay.stdout)["status"] == "COMPLETE"
    bundle["comparison"]["report"]["verification"]["verdict"] = "DIFFERENT"
    path.write_bytes(canonical_bytes(request(dict(op="verify_bundle", bundle=bundle))))
    assert subprocess.run(command, capture_output=True, timeout=60).returncode == 3


def test_api_local_opt_in_body_and_concurrency_guards(monkeypatch):
    body = request(dict(op="build"))
    monkeypatch.delenv("FLIP_LOCAL_SOLVER", raising=False)
    with TestClient(app, client=("127.0.0.1", 41700)) as client:
        assert client.post("/api/agent/v1/execute", json=body).status_code == 501
        monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
        assert client.post("/api/agent/v1/execute?permission=true", json=body).status_code == 422
        assert client.post("/api/agent/v1/execute", content=b"x" * 1048577).status_code == 413
    with TestClient(app, client=("203.0.113.1", 41700)) as client:
        assert client.post("/api/agent/v1/execute", json=body).status_code == 501


def test_direct_operation_malformed_comparison_cannot_complete(monkeypatch):
    import flip_core.agent_operations as operations

    monkeypatch.setattr(operations, "compare", lambda _: "forged success")
    payload = dict(
        step=WorkflowStep(id="x", op="compare").model_dump(mode="json"),
        executionRequest=sample("half-adder"),
        source=None,
        settings=asdict(RpcSettings()),
        rpcLimit=0,
    )
    with pytest.raises((ContractError, ValueError, TypeError)):
        run_operation(payload, None)


def test_versioned_schema_and_frozen_corpus_verifier():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "flip_core.agent_schema_export",
            "--out",
            "docs/schema/m45-agent-workflow/1.0.0",
            "--check",
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, "fixtures/m45-agent-workflow/generators/verify_corpus.py"],
        cwd=ROOT,
        check=True,
    )
    with pytest.raises(ContractError):
        parse_workflow(dict(steps=[dict(id="a", op="export", source="future")]))
    assert WorkflowRequest.model_validate(request(dict(op="build"))).steps[0].op == "build"


def test_failed_source_cannot_fall_back_to_an_unrelated_current_project():
    with chain_server() as (_, settings):
        r = execute(
            request(
                dict(
                    op="discover",
                    libraryRequest=dict(operation="discover", limit=1),
                    budget=dict(imports=dict(maxRequests=1)),
                    continueOn=["UNKNOWN"],
                ),
                dict(op="build", source="s0"),
            ),
            settings=settings,
        )
    assert r.status == "INVALID_INPUT" and r.logs[-1].output is None
    assert r.finalExecutionHash == content_hash(sample("half-adder"))


def test_receipt_output_bounds_and_stale_flags_cannot_be_overridden():
    r = execute(request(dict(op="export"), budget=dict(maxReceiptBytes=4096)))
    assert r.status == "BUDGET_EXHAUSTED" and len(canonical_bytes(r)) <= 4096
    r = execute(request(dict(op="build", budget=dict(maxOutputBytes=1024))))
    assert r.status == "BUDGET_EXHAUSTED" and r.logs[0].output is None
    original = sample("half-adder")
    original["imports"][0]["integrity"]["freshness"] = "STALE"
    r = execute(
        request(dict(op="compare", continueOn=["UNKNOWN"]), dict(op="export"), execution=original)
    )
    assert r.status == "STALE" and len(r.logs) == 1


def test_repeated_apply_and_trace_limits_fail_closed():
    steps = correction_steps()[:5]
    steps += [dict(op="apply", source="s3", expectedExecutionHash=HASH, actionId=ACTION.actionId)]
    r = execute(request(*steps, execution=PRIOR))
    assert r.status == "STALE" and r.finalExecutionHash == content_hash(ACTION.proposedRevision)
    r = execute(request(dict(op="inspect", budget=dict(trace=dict(maxNodes=1))), execution=PRIOR))
    assert r.status == "UNKNOWN" and r.logs[0].output["connections"] == []


def test_worker_crash_retry_is_bounded(monkeypatch):
    calls = []

    def failed(payload, *_):
        calls.append(payload)
        return dict(
            output=None,
            executionRequest=None,
            rpcUsed=0,
            error=dict(code="WORKER_FAILURE", message="worker failed"),
        )

    monkeypatch.setattr(agent_workflow, "operation_worker", failed)
    r = execute(
        request(
            dict(op="compare", retry=dict(maxRetries=2, on=["WORKER_FAILURE"])), dict(op="export")
        )
    )
    assert r.status == "UNKNOWN" and len(calls) == 3 == r.usage.toolRequests
    assert [e.attempt for e in r.logs] == [1, 2, 3]


def test_overall_deadline_includes_admission_and_identity_setup(monkeypatch):
    original = agent_workflow.controller_identity

    def slow_identity():
        time.sleep(0.02)
        return original()

    monkeypatch.setattr(agent_workflow, "controller_identity", slow_identity)
    r = execute(request(dict(op="build"), budget=dict(deadlineMs=1)))
    assert r.status == "BUDGET_EXHAUSTED" and not r.logs and r.usage.toolRequests == 0


def test_late_worker_revision_is_discarded_after_cancellation(monkeypatch):
    stopped = [False]

    def late(*_):
        stopped[0] = True
        return dict(
            error=None,
            output=dict(kind="COMPOSITION_RESULT"),
            rpcUsed=0,
            executionRequest=ACTION.proposedRevision.model_dump(mode="json"),
        )

    monkeypatch.setattr(agent_workflow, "operation_worker", late)
    r = execute(request(dict(op="build"), execution=PRIOR), cancelled=lambda: stopped[0])
    assert r.status == "CANCELLED" and r.finalExecutionHash == HASH
    assert r.logs[0].output is None


def test_shipped_example_contract_and_protocol_operations():
    example = load_json(
        (ROOT / "docs/schema/m45-agent-workflow/examples/correction.json").read_bytes()
    )
    r = execute(example)
    assert r.status == "COMPLETE" and r.logs[-1].output["kind"] == "FLIP_EVIDENCE"
    protocol = load_json((CORPUS / "protocol/agent-workflow-protocol.json").read_bytes())
    operations = WorkflowStep.model_fields["op"].annotation.__args__
    assert len(protocol["operations"]) == len(protocol["statusClasses"]) == 8
    assert all(item["op"] in operations for item in protocol["operations"])
