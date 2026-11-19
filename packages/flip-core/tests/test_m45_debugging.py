"""Real production diagnostics acceptance; frozen independent evidence is read-only."""

import copy
import hashlib
import json
import shutil
import subprocess
import sys

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.composition import compile_project
from flip_core.contracts import ContractError
from flip_core.debugging import ConeTracer, execute
from flip_core.debugging_models import TraceBudget
from flip_core.verification import mapped_outputs
from m45_debug_adapter import CASES, CORPUS, GUIDANCE, ROOT, bank, execution, request


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["caseId"])
def test_complete_production_corpus(case):
    if case["caseId"] == "D04":
        with pytest.raises(ContractError, match="forward signal"):
            execution(case)
        return
    body = request(case)
    saved = copy.deepcopy(body)
    result = execute(body)
    assert body == saved
    assert result.comparison["report"]["verification"]["verdict"] == case["expected"]["verdict"]
    assert result.attribution == case["diagnosticExpectation"]["class"]
    assert result.uniqueFaultClaim is False
    compiled = compile_project(execution(case).project, execution(case).imports)
    # Independently regenerate every truth-table row through the production evaluator.
    tables = case["expected"]["truthTables"]
    for side, index in (("reference", 0), ("candidate", 1)):
        assert len(tables[side]) == 2 ** case[side]["nIn"]
        for row in tables[side]:
            assert mapped_outputs(compiled, row["in"])[index] == row["out"]
    if case["expected"]["verdict"] == "EQUIVALENT":
        assert not result.connections and not result.actions and not result.differingOutputBits
        return
    assert result.classification == "VERIFIED_DIFFERENCE"
    proof = result.comparison["report"]["verification"]
    witness = proof["witness"]
    a, b = mapped_outputs(compiled, list(map(int, witness["inputs"]["bits"])))
    assert result.differingOutputBits == [i for i in range(len(a)) if a[i] != b[i]]
    assert all(c.classification == "RELEVANT_CONNECTION" for c in result.connections)
    assert len({(c.side, c.connectionRef) for c in result.connections}) == len(result.connections)
    if case["caseId"] == "D07":
        assert any("/ref[0]/ref[" in c.path for c in result.connections)
    # Archived first-difference witness must also replay, independently of SAT's witness choice.
    archived = case["expected"]["witness"]
    assert mapped_outputs(compiled, archived["in"]) == (
        archived["reference_out"],
        archived["candidate_out"],
    )


@pytest.mark.parametrize("guide", GUIDANCE, ids=lambda g: g["id"])
def test_eight_guidance_classifications(guide):
    case = next(c for c in CASES if c["caseId"] == guide["caseId"])
    if guide["caseId"] == "D04":
        with pytest.raises(ContractError):
            execution(case)
        assert guide["classification"] == "EXPLANATION_ONLY"
        return
    body = request(case)
    result = execute(body)
    if guide["classification"] == "VERIFIED_CORRECTION":
        assert result.actions
        original = copy.deepcopy(body)
        body.update(operation="verify-correction", actionId=result.actions[0].actionId)
        checked = execute(body)
        assert checked.correction.classification == "VERIFIED_CORRECTION"
        assert checked.correction.comparison["report"]["verification"]["verdict"] == "EQUIVALENT"
        assert body["executionRequest"] == original["executionRequest"]
        assert checked.correction.originalProjectHash != checked.correction.revisedProjectHash
    elif guide["classification"] == "EXPLANATION_ONLY":
        assert not result.actions
        assert result.attribution in ("NO_FAULT_ATTRIBUTION", "AMBIGUOUS_MULTIPLE_CAUSES")
    else:
        assert result.classification == "VERIFIED_DIFFERENCE"
        assert result.correction is None


@pytest.mark.parametrize(
    "budget",
    [
        dict(maxNodes=1),
        dict(maxConnections=1),
        dict(maxIndexedSignals=1),
        dict(maxDepth=0),
        dict(maxCircuitBytes=1),
        dict(maxCircuits=1),
        dict(maxExpandedGates=1),
    ],
)
def test_resource_failure_clears_attribution(budget):
    body = request(CASES[6])
    body["budget"] = budget
    result = execute(body)
    assert result.classification == "UNKNOWN"
    assert result.reasonCode in ("RESOURCE_LIMIT", "REF_DEPTH_EXCEEDED")
    assert not result.connections and not result.actions and result.correction is None


def test_stale_solver_unknown_forged_action_and_request_fail_closed(monkeypatch):
    body = request(CASES[1])
    body["executionRequest"]["imports"][0]["integrity"]["freshness"] = "STALE"
    result = execute(body)
    assert result.classification == "UNKNOWN" and not result.actions
    body = request(CASES[1])
    body.update(operation="verify-correction", actionId="0x" + "00" * 32)
    result = execute(body)
    assert result.reasonCode == "INVALID_INPUT" and not result.connections
    body = request(CASES[1])
    body["authority"] = "proof"
    with pytest.raises(ContractError):
        execute(body)
    import flip_core.verification as verification

    monkeypatch.setattr(
        verification, "run_worker", lambda *a: dict(outcome="INTERRUPTED", reason="SOLVER_TIMEOUT")
    )
    result = execute(request(CASES[1]))
    assert result.classification == "UNKNOWN" and result.reasonCode == "SOLVER_TIMEOUT"
    assert not result.connections and not result.actions


def test_api_cli_canonical_parity_and_loopback_gate(monkeypatch, tmp_path):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    body = request(CASES[1])
    path = tmp_path / "debug.json"
    path.write_bytes(canonical_bytes(body))
    cli = subprocess.run(
        [sys.executable, "-m", "flip_cli.main", "debug", "--request", str(path)],
        capture_output=True,
    )
    assert cli.returncode == 1, cli.stderr
    api = TestClient(app, client=("127.0.0.1", 321)).post("/api/v1/debug", json=body)
    assert api.status_code == 200
    assert json.loads(cli.stdout) == api.json() == execute(body).model_dump(mode="json")
    assert TestClient(app).post("/api/v1/debug", json=body).status_code == 501
    monkeypatch.delenv("FLIP_LOCAL_SOLVER")
    assert (
        TestClient(app, client=("127.0.0.1", 321)).post("/api/v1/debug", json=body).status_code
        == 501
    )


def test_output_specific_ref_cone_and_repeated_instances():
    req = execution(CASES[6])
    compiled = compile_project(req.project, req.imports)
    tracer = ConeTracer(TraceBudget())
    tracer.trace(compiled.candidate, [0], "candidate", req.project.candidate)
    paths = [c.path for c in tracer.connections.values()]
    assert any("/ref[0]/ref[0]" in p for p in paths)
    assert not any("/ref[0]/ref[1]" in p for p in paths)
    for edge in tracer.connections.values():
        if edge.kind == "REF_OUTPUT":
            assert edge.sourcePath.startswith(edge.path + "/ref[")
            assert edge.destination == edge.connectionRef
            assert edge.sourceIdentity is not None
        else:
            assert edge.sourcePath == edge.path
            assert edge.sourceNetlistHash == edge.netlistHash
    result = execute(request(CASES[0]))
    assert {c.instanceId for c in result.connections if c.side == "candidate"} >= {
        "element0",
        "element1",
    }
    assert result.projectHash == content_hash(execution(CASES[0]).project)


def test_frozen_corpus_regeneration_only_in_scratch(tmp_path):
    manifest = json.loads((CORPUS / "MANIFEST.json").read_bytes())
    for entry in manifest["files"]:
        raw = (CORPUS / entry["path"]).read_bytes()
        assert len(raw) == entry["bytes"]
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
    scratch = tmp_path / "fixtures/m45-debugging"
    shutil.copytree(CORPUS, scratch, ignore=shutil.ignore_patterns("__pycache__"))
    run = subprocess.run(
        [sys.executable, str(scratch / "generators/verify_corpus.py")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    recorded = json.loads(
        (tmp_path / "docs/evidence/m45-debugging/verification-transcript.json").read_bytes()
    )
    assert recorded["result"] == "PASS"
    # Never allow this reproduction to overwrite the independent agent's attestation.
    revision = "8fc4efb71cb750cced98b4e88540796d665b616a"
    paths = (
        subprocess.check_output(["git", "diff", "--name-only", revision + "^", revision], cwd=ROOT)
        .decode()
        .splitlines()
    )
    assert len(paths) == 15
    for path in paths:
        assert (ROOT / path).read_bytes() == subprocess.check_output(
            ["git", "show", revision + ":" + path], cwd=ROOT
        )


def test_indistinguishable_alternatives_replay_without_unique_cause():
    case = CASES[-1]
    for alternative in case["alternativeSingleEdgeCauses"]:
        mutated = copy.deepcopy(case)
        raw = bytearray.fromhex(case["reference"]["netlistHex"][2:])
        offset = alternative["elementIndex"] * 7 + 1 + 3 * alternative["inputPin"]
        raw[offset : offset + 3] = alternative["replacementSignal"].to_bytes(3, "big")
        mutated["candidate"]["netlistHex"] = "0x" + raw.hex()
        req = execution(mutated)
        compiled = compile_project(req.project, req.imports)
        actual = [
            mapped_outputs(compiled, row["in"])[1]
            for row in case["expected"]["truthTables"]["candidate"]
        ]
        assert actual == case["observedWrongTruthTable"]
        result = execute(
            dict(
                schemaVersion="m45-debugging-1.0.0",
                kind="DEBUG_REQUEST",
                executionRequest=req.model_dump(mode="json"),
            )
        )
        assert result.attribution == "AMBIGUOUS_MULTIPLE_CAUSES"
        assert not result.actions and not result.uniqueFaultClaim


def test_missing_closure_witness_failure_deadline_and_repeated_child(monkeypatch):
    import flip_core.debugging as debugging

    body = request(CASES[6])
    body["executionRequest"]["imports"][0]["circuits"].pop()
    try:
        result = execute(body)
    except ContractError as exc:
        assert exc.code == "INVALID_INPUT"
    else:
        assert result.classification == "UNKNOWN" and not result.connections
    with monkeypatch.context() as patch:
        patch.setattr(debugging, "mapped_outputs", lambda *args: ([0], [0]))
        result = execute(request(CASES[1]))
        assert result.reasonCode == "WITNESS_REPLAY_FAILED"
        assert result.comparison is None and not result.connections and not result.actions
    with monkeypatch.context() as patch:

        def timeout(self):
            raise ContractError("RESOURCE_LIMIT", "Diagnostic deadline exceeded.")

        patch.setattr(debugging.Deadline, "remaining", timeout)
        result = execute(request(CASES[1]))
        assert result.classification == "UNKNOWN" and result.reasonCode == "RESOURCE_LIMIT"
    req = execution(CASES[0]).model_dump(mode="json")
    for side in ("candidate", "referenceCandidate"):
        components = req["project"][side]["components"]
        components[1]["sourceAlias"] = components[0]["sourceAlias"]
    from flip_core.verification import parse_request

    parsed = parse_request(req)
    compiled = compile_project(parsed.project, parsed.imports)
    tracer = ConeTracer(TraceBudget())
    tracer.trace(compiled.candidate, [0, 1], "candidate", parsed.project.candidate)
    paths = {c.path for c in tracer.connections.values()}
    assert "top/ref[0]" in paths and "top/ref[1]" in paths


def test_shared_engine_raw_input_bound():
    with pytest.raises(ContractError) as error:
        execute(b" " * 1_048_577)
    assert error.value.code == "RESOURCE_LIMIT"


def test_adapter_uses_exact_frozen_dependency_bytes():
    # Read the frozen declaration in an isolated interpreter; never use its evaluator
    # to calculate a production verdict or truth table.
    code = (
        "import runpy,sys,json,hashlib; m=runpy.run_path(sys.argv[1]); "
        "print(json.dumps(sorted([[cpu,cid,ni,no,hashlib.sha256(raw).hexdigest()] "
        "for (cpu,cid),(ni,no,raw) in m['BANK'].items()])))"
    )
    declared = json.loads(
        subprocess.check_output(
            [sys.executable, "-B", "-c", code, str(CORPUS / "generators/build_corpus.py")]
        )
    )
    actual = sorted(
        [
            [cpu[2:], cid, ni, no, hashlib.sha256(raw).hexdigest()]
            for (cpu, cid), (ni, no, raw) in bank().items()
        ]
    )
    assert actual == declared
