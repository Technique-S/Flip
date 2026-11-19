"""Acceptance attacks on real debugger trust boundaries; no archived fixture edits."""

import copy
import json
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_core import debugging, isolation, verification
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.composition import compile_project
from flip_core.contracts import ContractError
from flip_core.verification import parse_request
from m45_debug_adapter import CASES, request


def no_attribution(result, reason=None):
    assert result.classification == "UNKNOWN"
    assert result.attribution == "UNKNOWN_NO_ATTRIBUTION"
    assert not result.connections and not result.actions and not result.differingOutputBits
    assert result.comparison is None and result.correction is None
    assert not result.uniqueFaultClaim
    if reason:
        assert result.reasonCode == reason


def rebind_manifest(body, index, old_hash):
    imported = body["executionRequest"]["imports"][index]
    imported["manifestHash"] = content_hash(imported["manifest"])
    for source in body["executionRequest"]["project"]["sources"]:
        if source["manifestHash"] == old_hash:
            source["manifestHash"] = imported["manifestHash"]


@pytest.mark.parametrize("field", ["inputs", "referenceOutputs", "candidateOutputs"])
def test_altered_witness_bits_are_independently_replayed(monkeypatch, field):
    body = request(CASES[1])
    report = debugging.compare(parse_request(body["executionRequest"]))
    forged = copy.deepcopy(report)
    vector = forged["report"]["verification"]["witness"][field]
    vector["bits"] = "00" if field == "inputs" else str(1 - int(vector["bits"]))
    unchanged = copy.deepcopy(forged)
    monkeypatch.setattr(debugging, "compare", lambda _: forged)
    no_attribution(debugging.execute(body), "WITNESS_REPLAY_FAILED")
    assert forged == unchanged


def test_false_native_sat_witness_cannot_establish_difference(monkeypatch):
    # 00 is not a distinguishing witness for D02. This crosses the trusted M3 replay,
    # rather than accepting the worker's SAT label or a caller-provided report.
    monkeypatch.setattr(
        verification, "run_worker", lambda *args: dict(outcome="SAT", witness=[0, 0])
    )
    no_attribution(debugging.execute(request(CASES[1])), "WITNESS_REPLAY_FAILED")


@pytest.mark.parametrize("field", ["witness", "claimedResult", "proposedRevision"])
def test_untrusted_evidence_and_revisions_are_not_execution_inputs(field):
    body = request(CASES[1])
    body[field] = {"classification": "VERIFIED_CORRECTION"}
    with pytest.raises(ContractError) as exc:
        debugging.execute(body)
    assert exc.value.code == "INVALID_INPUT"


@pytest.mark.parametrize("rebind", [False, True])
def test_substituted_dependency_hash_rejected_even_with_recomputed_outer_bindings(rebind):
    body = request(CASES[6])
    imported = body["executionRequest"]["imports"][0]
    old_hash = imported["manifestHash"]
    imported["manifest"]["dependencies"][0]["netlistHash"] = "0x" + "99" * 32
    if rebind:
        rebind_manifest(body, 0, old_hash)
    with pytest.raises(ContractError) as exc:
        debugging.execute(body)
    assert exc.value.code == "INVALID_INPUT"


def test_valid_but_substituted_import_cannot_replace_expected_source(monkeypatch):
    body = request(CASES[1])
    body["executionRequest"]["imports"] = [request(CASES[0])["executionRequest"]["imports"][0]]

    def forbidden_compare(_):
        raise AssertionError("Substituted source reached the solver")

    monkeypatch.setattr(debugging, "compare", forbidden_compare)
    no_attribution(debugging.execute(body), "MISSING_REFERENCE")


def test_self_consistent_but_incomplete_manifest_still_requires_actual_ref_closure():
    body = request(CASES[6])
    imported = body["executionRequest"]["imports"][0]
    old_hash = imported["manifestHash"]
    removed = imported["manifest"]["dependencies"].pop()["identity"]
    imported["circuits"] = [c for c in imported["circuits"] if c["identity"] != removed]
    imported["manifest"]["edges"] = [
        e for e in imported["manifest"]["edges"] if e["parent"] != removed and e["child"] != removed
    ]
    rebind_manifest(body, 0, old_hash)
    # Model-level byte/hash consistency is insufficient: the native REF still targets
    # the omitted child, which the existing resolver must reject before diagnosis.
    no_attribution(debugging.execute(body), "MISSING_REFERENCE")


@pytest.mark.parametrize("change", ["projectId", "candidate", "reference", "environment"])
def test_correction_id_is_bound_to_original_project_and_dependencies(change):
    body = request(CASES[1])
    proposal = debugging.execute(body).actions[0]
    edited = copy.deepcopy(body)
    project = edited["executionRequest"]["project"]
    if change == "projectId":
        project["projectId"] = "ChangedProject"
    elif change == "candidate":
        project["candidate"]["components"][0]["inputs"].reverse()
    elif change == "reference":
        project["referenceCandidate"]["components"][0]["inputs"].reverse()
    else:
        imported = edited["executionRequest"]["imports"][0]
        old_hash = imported["manifestHash"]
        imported["manifest"]["root"]["environment"]["processorCodeHash"] = "0x" + "ab" * 32
        rebind_manifest(edited, 0, old_hash)
    edited.update(operation="verify-correction", actionId=proposal.actionId)
    no_attribution(debugging.execute(edited), "INVALID_INPUT")
    assert body == request(CASES[1])


def test_depth_limit_rejects_actual_nested_descent():
    body = request(CASES[6])
    body["budget"] = dict(maxDepth=1)
    no_attribution(debugging.execute(body), "REF_DEPTH_EXCEEDED")


def test_nonidentity_pin_order_selects_correct_reference_and_candidate_trace_roots():
    body = request(CASES[4])  # three distinct output functions and a rotated candidate
    plan = body["executionRequest"]["project"]["comparison"]
    plan["inputMap"], plan["outputMap"] = [1, 0], [2, 0, 1]
    result = debugging.execute(body)
    assert result.classification == "VERIFIED_DIFFERENCE"
    assert result.comparison["report"]["inputMap"] == [1, 0]
    assert result.comparison["report"]["outputMap"] == [2, 0, 1]
    roots = {
        side: {
            edge.outputPin
            for edge in result.connections
            if edge.side == side and edge.kind == "OUTPUT_MAP"
        }
        for side in ("reference", "candidate")
    }
    assert roots["reference"] == set(result.differingOutputBits)
    assert roots["candidate"] == {plan["outputMap"][i] for i in result.differingOutputBits}
    assert roots["candidate"] != roots["reference"]


def test_repeated_ref_expansion_is_bounded_independently_of_gate_cap():
    body = request(CASES[1])
    project = body["executionRequest"]["project"]
    for side in ("candidate", "referenceCandidate"):
        prototype = project[side]["components"][0]
        project[side]["components"] = []
        project[side]["outputs"] = []
        for index in range(64):
            component = copy.deepcopy(prototype)
            component["instanceId"] = f"copy{index}"
            project[side]["components"].append(component)
            project[side]["outputs"].append(dict(component=f"copy{index}", pin=0))
    project["comparison"]["outputMap"] = list(range(64))
    body["budget"] = dict(maxIndexedSignals=300, maxNodes=8192, maxConnections=8192)
    execution = parse_request(body["executionRequest"])
    compiled = compile_project(execution.project, execution.imports)
    assert compiled.candidate.gates == compiled.reference.gates == 192
    assert compiled.candidate.gates < execution.project.limits.gateCap
    no_attribution(debugging.execute(body), "RESOURCE_LIMIT")


@pytest.mark.parametrize("probe", ["timeout-probe", "crash-probe"])
def test_actual_worker_timeout_and_crash_produce_no_attribution(monkeypatch, probe):
    def worker(clauses, inputs, limits):
        if probe == "timeout-probe":
            limits = limits.model_copy(update={"solverTimeoutMs": 250})
        return isolation.run_worker(clauses, inputs, limits, _probe=probe)

    monkeypatch.setattr(verification, "run_worker", worker)
    result = debugging.execute(request(CASES[1]))
    no_attribution(result)
    assert result.reasonCode in ("SOLVER_TIMEOUT", "RESOURCE_LIMIT")


@pytest.mark.parametrize("probe", ["timeout-probe", "crash-probe"])
def test_correction_worker_failure_never_promotes_candidate(monkeypatch, probe):
    body = request(CASES[1])
    action_id = debugging.execute(body).actions[0].actionId
    calls = []

    def worker(clauses, inputs, limits):
        calls.append(len(calls))
        if len(calls) == 2:
            if probe == "timeout-probe":
                limits = limits.model_copy(update={"solverTimeoutMs": 250})
            return isolation.run_worker(clauses, inputs, limits, _probe=probe)
        return isolation.run_worker(clauses, inputs, limits)

    monkeypatch.setattr(verification, "run_worker", worker)
    body.update(operation="verify-correction", actionId=action_id)
    result = debugging.execute(body)
    assert len(calls) == 2
    assert result.classification == "VERIFIED_DIFFERENCE"  # original remains a valid mismatch
    assert result.correction.classification == "UNKNOWN"
    assert result.correction.comparison["report"]["verification"]["verdict"] == "UNKNOWN"
    assert not result.uniqueFaultClaim


def test_repeated_corrections_always_execute_new_comparisons(monkeypatch):
    body = request(CASES[1])
    original = copy.deepcopy(body)
    trusted_compare = debugging.compare
    compared = []

    def compare(execution):
        compared.append(content_hash(execution))
        return trusted_compare(execution)

    monkeypatch.setattr(debugging, "compare", compare)
    proposal = debugging.execute(body).actions[0]
    body.update(operation="verify-correction", actionId=proposal.actionId)
    for _ in range(2):
        checked = debugging.execute(body)
        assert checked.correction.classification == "VERIFIED_CORRECTION"
    original_hash = content_hash(parse_request(original["executionRequest"]))
    revised_hash = content_hash(proposal.proposedRevision)
    assert compared == [original_hash, original_hash, revised_hash, original_hash, revised_hash]
    assert body["executionRequest"] == original["executionRequest"]
    # Reusing a previously successful action on the already applied project does not
    # reuse its old certificate or claim a new correction on an equivalent design.
    body["executionRequest"] = proposal.proposedRevision.model_dump(mode="json")
    no_attribution(debugging.execute(body), "INVALID_INPUT")


@pytest.mark.parametrize("forged", [False, True])
def test_correction_success_and_rejection_have_cli_api_semantic_parity(
    monkeypatch, tmp_path, forged
):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    body = request(CASES[1])
    action_id = debugging.execute(body).actions[0].actionId
    body.update(operation="verify-correction", actionId="0x" + "00" * 32 if forged else action_id)
    path = tmp_path / "correction.json"
    path.write_bytes(canonical_bytes(body))
    cli = subprocess.run(
        [sys.executable, "-m", "flip_cli", "debug", "--request", str(path)], capture_output=True
    )
    assert cli.returncode == (2 if forged else 0), cli.stderr
    api = TestClient(app, client=("127.0.0.1", 52000)).post("/api/v1/debug", json=body)
    assert api.status_code == 200
    assert json.loads(cli.stdout) == api.json() == debugging.execute(body).model_dump(mode="json")
    assert path.read_bytes() == canonical_bytes(body)
