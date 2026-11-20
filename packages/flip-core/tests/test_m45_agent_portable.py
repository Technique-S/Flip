"""Combined production adapter acceptance. No copied claims become proof authority."""

import copy
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_cli.main import main
from flip_core import agent_portable_adapter as adapter
from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.contracts import ContractError
from flip_core.portable import bounded_operation, create_package, parse_package
from flip_core.verification import compose, parse_request
from flip_core.workflow import product, sample

ROOT = Path(__file__).resolve().parents[3]


def prior():
    return load_json(
        (ROOT / "docs/schema/m45-debugging/examples/swapped-prior.execution.json").read_bytes()
    )


def named_vectors():
    def bits(s):
        return dict(encoding="tap02-lsb0-v1", width=2, bits=s)

    return [
        dict(
            name="halfAdder",
            declaredIntent="Carry and sum at numeric pins 0 and 1",
            expectedCoverage="EXHAUSTIVE_DECLARED_DOMAIN",
            vectors=[
                dict(inputs=bits(i), outputs=bits(o))
                for i, o in [("00", "00"), ("01", "01"), ("10", "01"), ("11", "10")]
            ],
        )
    ]


def prepared(package=None, action="correct", **fields):
    package = package or create_package(prior(), tests=named_vectors())
    return adapter.prepare_adapter(
        dict(package=package, action=action, continueOnTestMismatch=True, **fields)
    )["request"]


def replay(package, artifacts):
    return bounded_operation(
        dict(
            schemaVersion="flip-portable-project-1.1.0",
            kind="PORTABLE_REQUEST",
            operation="replay-evidence",
            package=package,
            artifacts=artifacts,
        )
    )


def test_combined_15_stage_journey_preserves_original_and_prior_evidence():
    raw = prior()
    old = product(
        "export", dict(schemaVersion="m4-1.0.0", kind="PRODUCT_REQUEST", executionRequest=raw)
    )
    ref = dict(
        kind="FLIP_EVIDENCE",
        digest=old["contentHash"],
        executionRequestHash=content_hash(raw),
        reproduce=old["reproduce"],
        engineHash=old["comparison"]["engineHash"],
    )
    package = create_package(raw, tests=named_vectors(), evidence_refs=[ref])
    original = copy.deepcopy(package)
    body = prepared(package)
    body["evidenceArtifacts"] = {ref["digest"]: old}
    body["continueOnEvidenceDifference"] = True
    untouched = copy.deepcopy(body)
    result = adapter.execute(body)
    assert result["status"] == "COMPLETE", result["error"]
    assert body == untouched and package == original and result["originalPackage"] == original
    receipt = result["receipt"]
    logs = receipt["logs"]
    assert logs[0]["op"] == "verify_bundle" and logs[0]["status"] == "DIFFERENT"
    assert result["inputEvidence"][0]["status"] == "REPLAYED"
    assert any(e["op"] == "test" and e["output"]["verdict"] == "VECTORS_MISMATCH" for e in logs)
    difference = next(e for e in logs if e["op"] == "compare")
    assert (
        difference["output"]["report"]["verification"]["witness"]["replay"] == "REF_BEAT_REPRODUCED"
    )
    assert next(e for e in logs if e["op"] == "inspect")["output"]["uniqueFaultClaim"] is False
    for op in ("verify", "apply"):
        assert (
            next(e for e in logs if e["op"] == op)["output"]["classification"]
            == "VERIFIED_CORRECTION"
        )
    revised = result["revisedPackage"]
    assert revised["revision"]["parentHash"] == package["revision"]["revisionHash"]
    assert revised["ancestors"][-1] == package["revision"]
    assert revised["revision"]["editLog"][0]["beforeHash"] == package["executionRequestHash"]
    assert revised["revision"]["editLog"][-1]["afterHash"] == revised["executionRequestHash"]
    assert revised["tests"] == package["tests"]
    assert package["evidenceRefs"] == [ref] and ref not in revised["evidenceRefs"]
    assert revised["agentTaskRef"] == receipt["requestHash"]
    parse_package(canonical_bytes(revised))
    built = compose(parse_request(revised["executionRequest"]))
    assert len(bytes.fromhex(built["netlist"][2:])) == 81
    for e in replay(revised, result["evidenceArtifacts"])["results"]:
        assert e["status"] == "REPLAYED"
        assert e["result"]["report"]["verification"]["verdict"] == "EQUIVALENT"
        assert e["result"]["report"]["integrity"]["freshness"] == "HISTORICAL"
    assert (
        content_hash({k: v for k, v in result.items() if k != "resultHash"}) == result["resultHash"]
    )


@pytest.mark.parametrize(
    "field", ["expectedPackageHash", "expectedRevisionHash", "expectedExecutionRequestHash"]
)
def test_exact_pins_required(field):
    body = prepared()
    body[field] = "0x" + "00" * 32
    with pytest.raises(ContractError):
        adapter.execute(body)


@pytest.mark.parametrize(
    "change", ["version", "ancestry", "project", "closure", "stale", "authority", "replacement"]
)
def test_foreign_forged_stale_and_missing_closure(change):
    body = prepared()
    p = body["package"]
    if change == "version":
        p["schemaVersion"] = "flip-portable-project-9.0.0"
    elif change == "ancestry":
        p["revision"]["parentHash"] = "0x" + "11" * 32
    elif change == "project":
        p["executionRequest"]["project"]["projectId"] = "foreign"
    elif change == "closure":
        value = prior()
        value["imports"].pop()
        p = create_package(value)
        body = prepared(p)
    elif change == "stale":
        value = prior()
        value["imports"][0]["integrity"]["freshness"] = "STALE"
        body = prepared(create_package(value))
    elif change == "authority":
        body["permissions"] = ["SIGN", "SPEND"]
    else:
        body["workflow"]["executionRequest"] = sample("half-adder")
    try:
        result = adapter.execute(body)
    except ContractError:
        return
    assert result["status"] in ("STALE", "INVALID_INPUT")
    assert result["revisedPackage"] is None


@pytest.mark.parametrize("purpose", ["PUBLISH", "DEPLOY"])
def test_publication_stop_is_terminal_no_revision_or_later_operation(purpose):
    body = prepared(action="publish")
    body["purpose"] = purpose
    body["createRevision"] = True
    result = adapter.execute(body)
    assert result["status"] == "STOP_AUTHORIZATION"
    assert not result["revisionCreated"] and result["originalPackage"] == body["package"]
    assert len(result["receipt"]["logs"]) == 1
    stop = result["receipt"]["logs"][0]["output"]
    assert stop["signingCapability"] is False and stop["retryable"] is False
    assert "transaction" not in stop


def test_named_mismatch_stops_without_implicit_retry_or_commit():
    body = prepared()
    body["continueOnTestMismatch"] = False
    result = adapter.execute(body)
    assert result["status"] == "DIFFERENT" and not result["revisionCreated"]
    assert len(result["receipt"]["logs"]) == 1 and result["receipt"]["usage"]["iterations"] == 1
    body["runNamedTests"] = False
    with pytest.raises(ContractError):
        adapter.execute(body)


def test_cancellation_before_and_immediately_before_commit(monkeypatch):
    body = prepared()
    result = adapter.execute(body, cancelled=lambda: True)
    assert result["status"] == "CANCELLED" and result["receipt"] is None
    stopped = threading.Event()
    original = adapter.create_package

    def cancel_after_hashing(*args, **kwargs):
        value = original(*args, **kwargs)
        stopped.set()
        return value

    monkeypatch.setattr(adapter, "create_package", cancel_after_hashing)
    result = adapter.execute(body, cancelled=stopped.is_set)
    assert result["status"] == "CANCELLED" and result["revisedPackage"] is None
    assert result["originalPackage"] == body["package"]


def test_deadline_and_result_budget_no_original_loss():
    body = prepared()
    body["workflow"]["budget"]["deadlineMs"] = 1
    result = adapter.execute(body)
    assert result["status"] == "BUDGET_EXHAUSTED" and result["revisedPackage"] is None
    assert result["originalPackage"] == body["package"]
    body["workflow"]["budget"]["maxReceiptBytes"] = 4096
    with pytest.raises(ContractError):
        adapter.execute(body)


def test_early_stop_cannot_skip_final_verification_gate():
    p = create_package(sample("half-adder"))
    body = prepared(p, action="verify-edit", draftExecutionRequest=p["executionRequest"])
    body["workflow"]["stopOn"] = ["EQUIVALENT"]
    result = adapter.execute(body)
    assert result["status"] == "INVALID_INPUT" and not result["revisionCreated"]


def test_cli_api_parity_and_both_legacy_dispatchers_survive(tmp_path, capsysbinary, monkeypatch):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    body = prepared()
    file = tmp_path / "adapter.json"
    file.write_bytes(canonical_bytes(body))
    assert (
        main(["agent-portable", "--request", str(file), "--out", str(tmp_path / "result.json")])
        == 0
    )
    cli = json.loads(capsysbinary.readouterr().out)
    client = TestClient(app, client=("127.0.0.1", 1))
    response = client.post("/api/agent/v1/portable", json=body)
    assert response.status_code == 200
    api = response.json()
    assert cli["reproductionHash"] == api["reproductionHash"]
    assert cli["receipt"]["reproductionHash"] == api["receipt"]["reproductionHash"]
    assert (
        main(["agent-portable", "--request", str(file), "--out", str(tmp_path / "result.json")])
        == 3
    )
    capsysbinary.readouterr()
    assert (
        client.post(
            "/api/agent/v1/execute",
            json={
                "steps": [{"id": "build", "op": "build"}],
                "executionRequest": sample("half-adder"),
            },
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/v1/portable",
            json=dict(
                schemaVersion="flip-portable-project-1.1.0",
                kind="PORTABLE_REQUEST",
                operation="validate",
                package=body["package"],
            ),
        ).status_code
        == 200
    )
    assert client.post("/api/agent/v1/portable", content=b"x" * 1048577).status_code == 413
    monkeypatch.delenv("FLIP_LOCAL_SOLVER")
    assert client.post("/api/agent/v1/portable", json=body).status_code == 501


def test_repeated_and_concurrent_readonly_requests_preserve_original():
    p = create_package(sample("half-adder"))
    body = prepared(p, action="inspect")
    before = copy.deepcopy(body)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(adapter.execute, [body, body]))
    assert body == before
    assert all(not r["revisionCreated"] for r in results)
    assert results[0]["reproductionHash"] == results[1]["reproductionHash"]


def test_downgrade_reports_loss_and_input_evidence_missing_is_not_verified():
    raw = prior()
    ref = dict(
        kind="FLIP_EVIDENCE",
        digest="0x" + "55" * 32,
        executionRequestHash=content_hash(raw),
        reproduce="flip verify-bundle --project project.json --bundle evidence.json",
        engineHash="0x" + "66" * 32,
    )
    p = create_package(raw, evidence_refs=[ref])
    result = adapter.execute(prepared(p))
    assert result["inputEvidence"] == [{"digest": ref["digest"], "status": "MISSING_EVIDENCE"}]
    converted = bounded_operation(
        dict(
            schemaVersion="flip-portable-project-1.1.0",
            kind="PORTABLE_REQUEST",
            operation="downgrade",
            package=result["revisedPackage"],
            allowLossy=True,
        )
    )
    assert (
        "evidenceRefs" in converted["discardedFields"]
        and "revision" in converted["discardedFields"]
    )


@pytest.mark.parametrize("field", ["digest", "engineHash", "reproduce"])
def test_corrupt_evidence_and_wrong_engine_are_not_replayed(field):
    raw = prior()
    old = product(
        "export", dict(schemaVersion="m4-1.0.0", kind="PRODUCT_REQUEST", executionRequest=raw)
    )
    ref = dict(
        kind="FLIP_EVIDENCE",
        digest=old["contentHash"],
        executionRequestHash=content_hash(raw),
        reproduce=old["reproduce"],
        engineHash=old["comparison"]["engineHash"],
    )
    if field in ("digest", "engineHash"):
        ref[field] = "0x" + "99" * 32
    else:
        old["reproduce"] = "do-not-execute-any-reproduction-command"
    p = create_package(raw, evidence_refs=[ref])
    body = prepared(p)
    body["evidenceArtifacts"] = {ref["digest"]: old}
    result = adapter.execute(body)
    assert result["status"] == "INVALID_INPUT" and result["receipt"] is None
    assert result["revisedPackage"] is None and result["originalPackage"] == p


def test_foreign_candidate_and_revalidation_chain_change_fail_closed():
    from flip_core.library_models import LibraryRequest
    from flip_core.workflow import project_from_import
    from test_m2_import import identity
    from test_m45_agent_workflow import chain_server
    from test_m45_library import LibraryChain

    p = create_package(prior())
    foreign = prior()
    foreign["project"]["projectId"] = "foreign"
    with pytest.raises(ContractError):
        prepared(p, action="verify-edit", draftExecutionRequest=foreign)
    chain = LibraryChain()
    imported = (
        chain.library()
        .execute(
            LibraryRequest(
                operation="import", identity=dict(processor=identity().processor, circuitId="1")
            )
        )
        .imported
    )
    p = create_package(project_from_import(imported))
    body = prepared(p, action="inspect")
    body["workflow"]["steps"] = [dict(id="fresh", op="revalidate"), dict(id="later", op="build")]
    chain.beacon_impl = "0x" + "cc" * 20
    with chain_server(chain) as (_, settings):
        result = adapter.execute(body, settings=settings)
    assert result["status"] == "STALE" and result["revisedPackage"] is None
    assert len(result["receipt"]["logs"]) == 1


def test_sparse_original_request_and_explicit_apply_order_preserved():
    raw = prior()
    raw["project"]["limits"] = {}
    p = create_package(raw)
    body = prepared(p)
    result = adapter.execute(body)
    assert result["status"] == "COMPLETE"
    assert result["originalPackage"]["executionRequest"] == raw
    assert result["revisedPackage"]["executionRequest"]["project"]["limits"] == {}
    assert result["receipt"]["originalExecutionHash"] == content_hash(parse_request(raw))
    assert p["executionRequestHash"] == content_hash(raw)
    assert p["executionRequestHash"] != result["receipt"]["originalExecutionHash"]


def test_declared_steps_cannot_silently_replace_project_or_reset_budgets():
    body = prepared()
    for op in ("sample", "import", "discover"):
        changed = copy.deepcopy(body)
        changed["workflow"]["steps"] = [{"id": "replace", "op": op}]
        with pytest.raises(ContractError):
            adapter.execute(changed)
    body["workflow"]["budget"]["maxIterations"] = 1
    result = adapter.execute(body)
    assert result["status"] == "BUDGET_EXHAUSTED" and not result["revisionCreated"]
    assert result["receipt"]["usage"]["iterations"] == 1


def test_preparation_cli_and_api_hash_parity(tmp_path, capsysbinary):
    prep = dict(package=create_package(prior()), action="correct")
    path = tmp_path / "preparation.json"
    path.write_bytes(canonical_bytes(prep))
    assert main(["agent-portable", "--prepare", "--request", str(path)]) == 0
    cli = json.loads(capsysbinary.readouterr().out)
    api = TestClient(app).post("/api/agent/v1/portable/prepare", json=prep)
    assert api.status_code == 200 and api.json() == cli
    assert cli["trust"] == "UNVERIFIED_PLAN_AND_IDENTITIES_ONLY"


def test_new_api_query_loopback_and_shared_concurrency_gate(monkeypatch):
    from importlib import import_module

    module = import_module("flip_api.app")
    body = prepared()
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    assert (
        TestClient(app, client=("10.0.0.1", 1))
        .post("/api/agent/v1/portable", json=body)
        .status_code
        == 501
    )
    client = TestClient(app, client=("127.0.0.1", 1))
    assert client.post("/api/agent/v1/portable?unknown=1", json=body).status_code == 422
    assert module._slots.acquire(blocking=False)
    assert module._slots.acquire(blocking=False)
    try:
        assert client.post("/api/agent/v1/portable", json=body).status_code == 429
    finally:
        module._slots.release()
        module._slots.release()


def test_repeated_apply_failure_never_commits_the_partial_revision():
    body = prepared()
    again = copy.deepcopy(body["workflow"]["steps"][-1])
    again["id"] = "applyAgain"
    body["workflow"]["steps"].append(again)
    result = adapter.execute(body)
    assert result["status"] == "STALE" and result["revisedPackage"] is None
    assert result["originalPackage"] == body["package"]
    assert result["receipt"]["executionRequest"] != result["receipt"]["originalExecutionRequest"]


def test_rehashed_fake_engine_cannot_turn_integrity_into_proof():
    raw = prior()
    artifact = product(
        "export", dict(schemaVersion="m4-1.0.0", kind="PRODUCT_REQUEST", executionRequest=raw)
    )
    artifact["comparison"]["engineHash"] = "0x" + "77" * 32
    artifact["contentHash"] = content_hash(
        {k: v for k, v in artifact.items() if k != "contentHash"}
    )
    ref = dict(
        kind="FLIP_EVIDENCE",
        digest=artifact["contentHash"],
        executionRequestHash=content_hash(raw),
        reproduce=artifact["reproduce"],
        engineHash=artifact["comparison"]["engineHash"],
    )
    p = create_package(raw, evidence_refs=[ref])
    body = prepared(p)
    body["evidenceArtifacts"] = {ref["digest"]: artifact}
    result = adapter.execute(body)
    assert result["status"] == "STALE" and result["revisedPackage"] is None
    assert result["inputEvidence"][0]["status"] == "NOT_REPLAYED"
