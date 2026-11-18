"""M3-C: execute independent corpus at production boundaries; preserve evidence."""

import hashlib
import itertools
import json
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_cli.main import main as cli
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.contracts import ContractError
from flip_core.execution import evaluate
from flip_core.integrity import compare_manifests
from flip_core.isolation import run_worker
from flip_core.models import ComparisonReport, Limits
from flip_core.verification import compare, compose, consume, parse_request
from m3_c_adapter import (
    ATTACKS,
    BENCHMARKS,
    CORPUS,
    GOLD,
    PROC,
    ROOT,
    SAT,
    SYNTH,
    WITNESSES,
    attack_claim,
    bank,
    case_request,
    import_fixture,
    pair_request,
    recipe_request,
    separate_context_comparison,
)


def evidence(
    record_property, fixture, actual, *, expected=None, reason=None, boundary=None, **details
):
    record_property(
        "m3_case",
        json.dumps(
            {
                "fixtureId": fixture.get("id", fixture.get("case")),
                "expected": expected
                or fixture.get("expected_result", fixture.get("expected_safe_behavior")),
                "actual": actual,
                "reason": reason,
                "boundary": boundary,
                "command": "python -m pytest packages/flip-core/tests/test_m3_acceptance.py -q",
                **details,
            },
            sort_keys=True,
        ),
    )


def check_table(spec, table, overrides=None):
    value, circuit = import_fixture(spec, overrides=overrides)
    for row in table:
        assert evaluate(circuit, row["in"]) == row["out"]
    return value, circuit


@pytest.mark.parametrize("case", GOLD, ids=lambda c: c["id"])
def test_golden_compositions(case, record_property):
    cid = case["id"]
    if cid in ("A07", "A08", "A09"):
        overrides = {}
        if cid == "A08":
            overrides = {
                (cpu, int(number)): (2, 1, bytes.fromhex(raw[2:]))
                for key, raw in case["banks"].items()
                for cpu, number in [key.split(":")]
            }
        with pytest.raises(ContractError) as exc:
            import_fixture(case, overrides=overrides)
        assert exc.value.code == "BAD_NETLIST"
        if cid == "A08":
            own = case["self_cycle_spec"]
            with pytest.raises(ContractError, match="cycle"):
                import_fixture(
                    {"n_in": 2, "n_out": 1, "netlist_hex": own["netlist"]},
                    overrides={(SYNTH, 3): (2, 1, bytes.fromhex(own["netlist"][2:]))},
                )
        if cid == "A09":
            with pytest.raises(ContractError):
                import_fixture(case["second_variant"])
        evidence(
            record_property, case, "REJECTED", reason=exc.value.code, boundary="M2_DECODER_RESOLVER"
        )
        return
    if cid == "A10":
        original, _ = import_fixture(case["base"])
        for substitution, expected in (
            ("substitution_bad", "SAT"),
            ("substitution_equivalent", "UNSAT"),
        ):
            raw = (
                bank()[(PROC, 2)][2]
                if substitution == "substitution_bad"
                else bytes.fromhex(case[substitution]["alternative_xor_netlist_hex"][2:])
            )
            overrides = {(PROC, 1): (2, 1, raw)}
            result, a, b = separate_context_comparison(
                case["base"], case["base"], overrides=overrides
            )
            assert result["outcome"] == expected
            fresh, _ = import_fixture(case["base"], overrides=overrides)
            changed = compare_manifests(original.manifest, fresh)
            assert changed.integrity.freshness == "STALE" and "NETLIST_CHANGED" in changed.changes
            if expected == "UNSAT":
                assert all(
                    evaluate(a, list(bits)) == evaluate(b, list(bits))
                    for bits in itertools.product((0, 1), repeat=2)
                )
        # A mixed closure must not be consumed as one coherent execution context.
        from test_m3_engine import pin, ref_component, request_for

        fresh, _ = import_fixture(
            case["base"], cid=9001, overrides={(PROC, 1): (2, 1, bank()[(PROC, 2)][2])}
        )
        req = request_for(
            None,
            original,
            [ref_component("candidate", "candidate", [pin(None, 0), pin(None, 1)])],
            [pin("candidate", 0), pin("candidate", 1)],
            2,
            [("candidate", fresh)],
        )
        with pytest.raises(ContractError) as exc:
            compare(req)
        assert exc.value.code == "IMPLEMENTATION_CHANGED"
        evidence(
            record_property,
            case,
            "SAT_BAD_UNSAT_EQUIVALENT_BOTH_STALE",
            reason=exc.value.code,
            boundary="PRODUCTION_SAT_EVALUATOR_MANIFEST_GUARD",
        )
        return
    if cid == "A05":
        check_table(case["reference"], case["reference_truth_table"])
        check_table(case["candidate"], case["candidate_truth_table"])
        request = recipe_request(case["reference"], case["candidate"])
    else:
        check_table(case, case["truth_table"])
        if cid == "A01":
            request = pair_request(case, case)
        else:
            reference = GOLD[1] if cid in ("A03", "A04") else GOLD[3] if cid == "A06" else case
            request = recipe_request(reference, case)
            assert compose(request)["netlist"] == case["netlist_hex"]
    result = compare(request)
    expected = "DIFFERENT" if cid in ("A04", "A05") else "EQUIVALENT"
    assert result["report"]["verification"]["verdict"] == expected
    if cid == "A02":
        builds = [compose(request)["netlist"] for _ in range(100)]
        assert len(set(builds)) == 1 and len(bytes.fromhex(builds[0][2:])) == 81
    evidence(
        record_property,
        case,
        expected,
        boundary="PRODUCTION_IMPORT_COMPOSE_COMPARE",
        rows=len(case.get("truth_table", [])),
    )


@pytest.mark.parametrize("case", SAT, ids=lambda c: c["id"])
def test_sat_corpus(case, record_property):
    cid = case["id"]
    if cid in ("B03", "B11", "B12", "B13", "B14"):
        with pytest.raises(ContractError) as exc:
            if cid == "B03":
                import_fixture(
                    {**case["candidate_spec"], "n_in": 2, "n_out": 1}, missing=((PROC, 1),)
                )
            elif cid == "B11":
                import_fixture(
                    {"n_in": 2, "n_out": 0, "netlist_hex": case["reference"]["netlist_hex"]}
                )
            elif cid == "B14":
                import_fixture({**case["candidate_spec"], "n_in": 2, "n_out": 1})
            else:
                pair_request(case["reference"], case["candidate"])
        assert exc.value.code == {
            "B03": "MISSING_REFERENCE",
            "B11": "BAD_NETLIST",
            "B14": "BAD_NETLIST",
        }.get(cid, "INVALID_INPUT")
        evidence(
            record_property,
            case,
            "REJECTED",
            reason=exc.value.code,
            boundary="PRODUCTION_IMPORT_PROJECT_VALIDATION",
        )
        return
    if cid == "B15":
        result, _, _ = separate_context_comparison(
            case["reference"], case["candidate"], overrides={(PROC, 1): bank()[(PROC, 2)]}
        )
        assert result["outcome"] == "SAT"
        evidence(
            record_property,
            case,
            "DIFFERENT",
            boundary="PRODUCTION_MITER_WORKER_TWO_VALIDATED_CONTEXTS",
            witness=result["witness"],
            consumerPolicy="mixed identity closures rejected, see A10",
        )
        return
    request = case_request(case)
    if cid == "B17":
        raw = request.model_dump(mode="json")
        raw["project"]["limits"]["solverTimeoutMs"] = 1
        request = parse_request(raw)
    result = compare(request)
    proof = result["report"]["verification"]
    assert proof["verdict"] == case["expected_result"], result["resources"]
    if proof["verdict"] == "DIFFERENT":
        _, a = import_fixture(case["reference"])
        _, b = import_fixture(case["candidate"], cid=9001)
        bits = [int(x) for x in proof["witness"]["inputs"]["bits"]]
        assert evaluate(a, bits) != evaluate(b, bits)
    evidence(
        record_property,
        case,
        proof["verdict"],
        reason=proof["reasonCode"],
        boundary="PRODUCTION_COMPARISON",
        resources=result["resources"],
    )


@pytest.mark.parametrize("witness", WITNESSES, ids=lambda c: c["case"])
def test_independent_witnesses(witness, record_property):
    reproduction = witness["minimal_reproduction"]
    ni, no = reproduction["n_in"], reproduction["n_out"]
    _, a = import_fixture(
        {"n_in": ni, "n_out": no, "netlist_hex": reproduction["reference_netlist_hex"]}
    )
    override = {(PROC, 1): bank()[(PROC, 2)]} if witness["case"] == "B15" else None
    _, b = import_fixture(
        {"n_in": ni, "n_out": no, "netlist_hex": reproduction["candidate_netlist_hex"]},
        cid=9001,
        overrides=override,
    )
    bits = witness["distinguishing_input"]
    ao, bo = evaluate(a, bits), evaluate(b, bits)
    assert ao == witness["reference_output_recursive"] == witness["reference_output_flat"]
    assert bo == witness["candidate_output_recursive"] == witness["candidate_output_flat"]
    assert ao != bo
    minimized = witness["greedy_minimized_witness"]
    assert evaluate(a, minimized) != evaluate(b, minimized)
    evidence(
        record_property,
        witness,
        "REPLAYED",
        expected="DIFFERENT",
        boundary="PRODUCTION_DIRECT_EVALUATOR",
        inputs=bits,
        referenceOutputs=ao,
        candidateOutputs=bo,
    )


@pytest.fixture(scope="module")
def proof_bases():
    result = {}
    for cid in ("B02", "B16", "B17"):
        request = case_request(next(c for c in SAT if c["id"] == cid))
        if cid == "B17":
            raw = request.model_dump(mode="json")
            raw["project"]["limits"]["solverTimeoutMs"] = 1
            request = parse_request(raw)
        result[cid] = request, compare(request)
    return result


@pytest.mark.parametrize("attack", ATTACKS, ids=lambda c: c["id"])
def test_proof_attacks(attack, proof_bases, record_property, tmp_path, capsys, monkeypatch):
    base = "B17" if attack["id"] == "D11" else "B16" if attack["id"] == "D10" else "B02"
    request, good = proof_bases[base]
    kwargs = {
        "expected_project_hash": content_hash(request.project),
        "expected_reference_hash": good["report"]["referenceManifestHash"],
    }
    with pytest.raises(ContractError):
        consume(request, {"report": attack["crafted_report"]}, **kwargs)
    claim = attack_claim(attack, good, request)
    if attack["id"] != "D08":
        ComparisonReport.model_validate(claim["report"])
    with pytest.raises(ContractError) as exc:
        consume(request, claim, **kwargs)
    if attack["id"] == "D10":
        assert exc.value.code == "WITNESS_REPLAY_FAILED"
    if attack["id"] == "D07":
        stale_raw = request.model_dump(mode="json")
        for imported in stale_raw["imports"]:
            imported["integrity"]["freshness"] = "STALE"
        stale_request = parse_request(stale_raw)
        stale = compare(stale_request)
        assert stale["report"]["integrity"]["freshness"] == "STALE"
        with pytest.raises(ContractError):
            consume(stale_request, good, **kwargs)
        assert (
            consume(stale_request, stale, **kwargs)["report"]["integrity"]["freshness"] == "STALE"
        )
    if attack["id"] == "D12":
        other_raw = request.model_dump(mode="json")
        other_raw["project"]["projectId"] = "anotherProject"
        other = parse_request(other_raw)
        with pytest.raises(ContractError):
            consume(
                other,
                good,
                expected_project_hash=content_hash(other.project),
                expected_reference_hash=kwargs["expected_reference_hash"],
            )
    # Same hostile bound claim through CLI and loopback consumer API.
    payload = {
        "schemaVersion": "m3-1.0.0",
        "kind": "M3_CONSUMPTION",
        "executionRequest": request.model_dump(mode="json"),
        "claimedResult": claim,
        "expectedProjectHash": kwargs["expected_project_hash"],
        "expectedReferenceHash": kwargs["expected_reference_hash"],
    }
    path = tmp_path / "attack.json"
    path.write_bytes(canonical_bytes(payload))
    expected_exit = 7 if exc.value.code == "IMPLEMENTATION_CHANGED" else 3
    assert cli(["consume", "--project", str(path)]) == expected_exit
    cli_error = json.loads(capsys.readouterr().out)
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    response = TestClient(app, client=("127.0.0.1", 1)).post(
        "/api/v1/consume", content=canonical_bytes(payload)
    )
    assert response.status_code == 422 and response.json() == cli_error
    evidence(
        record_property,
        attack,
        "REJECTED_RAW_AND_BOUND_CLAIMS_ALL_INTERFACES",
        reason=exc.value.code,
        boundary="TRUSTED_CONSUMER_CORE_CLI_API",
        expected=attack["expected_safe_behavior"],
    )


@pytest.mark.parametrize(
    "spec,mode",
    [(s, m) for s in BENCHMARKS for m in ("self", "equivalent", "different")],
    ids=[f"{s['id']}-{m}" for s in BENCHMARKS for m in ("self", "equivalent", "different")],
)
def test_independent_benchmarks(spec, mode, record_property):
    request = recipe_request(spec["variants"]["self"], spec["variants"][mode])
    assert compose(request)["netlist"] == spec["variants"][mode]["netlist_hex"]
    result = compare(request)
    proof = result["report"]["verification"]
    assert proof["verdict"] == spec["expected"][mode], result["resources"]
    assert result["resources"]["candidateGates"] == spec["actual_gates"]
    assert result["resources"]["peakBytes"] <= 64 * 1024**2
    evidence(
        record_property,
        {"id": f"{spec['id']}-{mode}"},
        proof["verdict"],
        expected=spec["expected"][mode],
        boundary="PRODUCTION_COMPILE_COMPARE",
        resources=result["resources"],
        note="fresh production metrics; independent fixture timing/CNF counts remain historical",
    )


def test_custody_and_scratch_regeneration(tmp_path, record_property):
    commit = "4822a05163166ec67b791328e2d1de490fa1c35f"
    paths = subprocess.check_output(
        ["git", "diff", "--name-only", commit + "^", commit], cwd=ROOT, text=True
    ).splitlines()
    for path in paths:
        assert (ROOT / path).read_bytes() == subprocess.check_output(
            ["git", "show", f"{commit}:{path}"], cwd=ROOT
        )
    manifest = json.loads((CORPUS / "MANIFEST.json").read_bytes())
    for item in [*manifest["authored_files"], *manifest["result_files"], manifest["build_info"]]:
        raw = (ROOT / item["path"]).read_bytes()
        assert len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"]
    target = tmp_path / "fixtures/m3-verification/generators"
    shutil.copytree(CORPUS / "generators", target, ignore=shutil.ignore_patterns("__pycache__"))
    # Exact independent script runs only in scratch; never overwrite custody bytes.
    shutil.copytree(
        CORPUS,
        tmp_path / "fixtures/m3-verification",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copytree(
        ROOT / "docs/evidence/m3-verification", tmp_path / "docs/evidence/m3-verification"
    )
    completed = subprocess.run(
        [sys.executable, str(target / "verify_corpus.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    evidence(
        record_property,
        {"id": "CUSTODY"},
        "BYTE_IDENTICAL",
        expected="UNCHANGED_AND_REGENERABLE",
        boundary="GIT_REGISTER_AND_SCRATCH_GENERATOR",
        files=len(paths),
        note="archival verifier's recorded SAT/witness booleans are not fresh production runs",
    )


def test_platform_fail_closed_and_repeated_cleanup(monkeypatch, record_property):
    import flip_core.isolation as isolation

    with monkeypatch.context() as patch:
        patch.setattr(isolation, "os", SimpleNamespace(name="unsupported"))
        patch.setattr(isolation, "sys", SimpleNamespace(platform="unsupported"))
        result = isolation.run_worker([], [], Limits())
        assert result["outcome"] == "INTERRUPTED" and result["reason"] == "RESOURCE_LIMIT"
    spawned = []
    original_popen = isolation.subprocess.Popen

    def tracked_popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        spawned.append(process)
        return process

    monkeypatch.setattr(isolation.subprocess, "Popen", tracked_popen)
    for mode in ("timeout-probe", "crash-probe", "memory-probe"):
        result = run_worker(
            [], [], Limits(solverTimeoutMs=500 if mode == "timeout-probe" else 5000), _probe=mode
        )
        if mode == "memory-probe":
            assert result["probe"] == "MEMORY_BLOCKED"
        else:
            assert result["outcome"] == "INTERRUPTED"
        for _ in range(3):
            assert run_worker([[1]], [1], Limits())["outcome"] == "SAT"
    assert len(spawned) == 12 and all(p.poll() is not None for p in spawned)
    evidence(
        record_property,
        {"id": "CONTAINMENT"},
        "FAIL_CLOSED_AND_SUBSEQUENT_JOBS_PASSED",
        expected="BOUNDED_AND_RECOVERABLE",
        boundary="REAL_WORKER",
        platform=sys.platform,
    )


def semantic_projection(value):
    if isinstance(value, dict):
        return {
            key: semantic_projection(item)
            for key, item in value.items()
            if key not in ("verifiedAt", "resources")
        }
    if isinstance(value, list):
        return [semantic_projection(item) for item in value]
    return value


@pytest.mark.parametrize("operation", ["compose", "compare", "vectors", "consume"])
def test_supported_operation_parity(
    operation, proof_bases, tmp_path, capsys, monkeypatch, record_property
):
    from flip_core.verification import bitvector

    request, result = proof_bases["B02"]
    payload = request.model_dump(mode="json")
    expected_exit = 1 if operation in ("compare", "consume") else 0
    if operation == "vectors":
        witness = next(w for w in WITNESSES if w["case"] == "B02")
        payload["vectors"] = [
            {
                "inputs": bitvector(witness["distinguishing_input"]).model_dump(mode="json"),
                "outputs": bitvector(witness["candidate_output_flat"]).model_dump(mode="json"),
            }
        ]
    elif operation == "consume":
        payload = {
            "schemaVersion": "m3-1.0.0",
            "kind": "M3_CONSUMPTION",
            "executionRequest": payload,
            "claimedResult": result,
            "expectedProjectHash": content_hash(request.project),
            "expectedReferenceHash": result["report"]["referenceManifestHash"],
        }
    path = tmp_path / "request.json"
    path.write_bytes(canonical_bytes(payload))
    assert cli([operation, "--project", str(path)]) == expected_exit
    local = json.loads(capsys.readouterr().out)
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    response = TestClient(app, client=("127.0.0.1", 1)).post(
        f"/api/v1/{operation}", content=canonical_bytes(payload)
    )
    assert response.status_code == 200
    cli_hash = content_hash(semantic_projection(local))
    api_hash = content_hash(semantic_projection(response.json()))
    assert cli_hash == api_hash
    evidence(
        record_property,
        {"id": f"PARITY-{operation}"},
        "IDENTICAL_SEMANTIC_HASHES",
        expected="CLI_API_PARITY",
        boundary="REAL_CLI_AND_ASGI",
        semanticHash=cli_hash,
        exitCode=expected_exit,
    )


def test_interfaces_recover_after_timeout(
    proof_bases, tmp_path, capsys, monkeypatch, record_property
):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    client = TestClient(app, client=("127.0.0.1", 1))
    for base, exit_code, verdict in (("B17", 2, "UNKNOWN"), ("B02", 1, "DIFFERENT")):
        request, _ = proof_bases[base]
        raw = canonical_bytes(request)
        path = tmp_path / "request.json"
        path.write_bytes(raw)
        assert cli(["compare", "--project", str(path)]) == exit_code
        assert json.loads(capsys.readouterr().out)["report"]["verification"]["verdict"] == verdict
        response = client.post("/api/v1/compare", content=raw)
        assert (
            response.status_code == 200
            and response.json()["report"]["verification"]["verdict"] == verdict
        )
    bad = proof_bases["B02"][0].model_dump(mode="json")
    bad["schemaVersion"] = "m4-1.0.0"
    path.write_bytes(canonical_bytes(bad))
    assert cli(["compare", "--project", str(path)]) == 3
    local_error = json.loads(capsys.readouterr().out)
    assert client.post("/api/v1/compare", json=bad).json() == local_error
    evidence(
        record_property,
        {"id": "FAILURE-RECOVERY"},
        "UNKNOWN_THEN_VERIFIED_DIFFERENT",
        expected="CONSISTENT_RECOVERY_AND_VERSION_REJECTION",
        boundary="REAL_CLI_AND_ASGI",
    )
