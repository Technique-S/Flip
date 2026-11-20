"""Production portable contracts, trusted replay and transport parity regressions."""

import copy
import json

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_cli.main import main
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.contracts import ContractError
from flip_core.portable import (
    VERSION,
    bounded_operation,
    create_package,
    parse_package,
    record_hash,
)
from flip_core.verification import compose, parse_request
from flip_core.workflow import REPRODUCE, product, sample


def operation(op, **fields):
    return dict(schemaVersion=VERSION, kind="PORTABLE_REQUEST", operation=op, **fields)


def named():
    def bits(s):
        return dict(encoding="tap02-lsb0-v1", width=len(s), bits=s)

    return [
        dict(
            name="halfAdder",
            declaredIntent="Carry and sum, numeric pins from zero",
            expectedCoverage="EXHAUSTIVE_DECLARED_DOMAIN",
            vectors=[
                dict(inputs=bits(a), outputs=bits(b))
                for a, b in [("00", "00"), ("01", "01"), ("10", "01"), ("11", "10")]
            ],
        )
    ]


def test_named_roundtrip_exact_request_hash_and_bytes():
    raw = sample("half-adder")
    # Both sparse legacy requests and normalized requests retain their original hash.
    for execution in (raw, parse_request(raw).model_dump(mode="json")):
        p = create_package(execution, tests=named())
        assert p["executionRequest"] == execution
        assert p["executionRequestHash"] == content_hash(execution)
        assert parse_package(canonical_bytes(p)).model_dump(mode="json") == p
        out = bounded_operation(operation("test", package=p))
        assert out["results"][0]["result"]["verdict"] == "VECTORS_MATCH"
        assert "EQUIVALENT" not in json.dumps(out)
        built = compose(
            parse_request(bounded_operation(operation("open", package=p))["executionRequest"])
        )
        assert len(bytes.fromhex(built["netlist"][2:])) == 81
        assert (
            built["manifest"]["netlistHash"]
            == "0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce"
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda p: p.pop("noDeclaredTests"),
        lambda p: p.update(noDeclaredTests=False),
        lambda p: p.update(schemaVersion="flip-portable-project-2.0.0"),
        lambda p: p.update(executionRequestHash="0x" + "00" * 32),
        lambda p: p.update(projectId="duplicateCanonicalState"),
        lambda p: p["revision"].update(parentHash="0x" + "11" * 32),
        lambda p: p["revision"].update(projectId="otherProject"),
        lambda p: p["revision"]["editLog"][0].update(beforeHash="0x" + "11" * 32),
        lambda p: p.update(agentTaskRef="0x" + "12" * 32),
    ],
)
def test_shape_hash_and_ancestry_attacks(mutation):
    p = create_package(sample("half-adder"))
    mutation(p)
    with pytest.raises(ContractError):
        bounded_operation(operation("validate", package=p))


def test_named_bounds_and_empty_marker():
    assert bounded_operation(operation("test", package=create_package(sample("half-adder")))) == {
        "noDeclaredTests": True,
        "results": [],
    }
    for change in ("width", "duplicate", "coverage", "empty", "name"):
        tests = named()
        if change == "width":
            tests[0]["vectors"][0]["inputs"] = dict(encoding="tap02-lsb0-v1", width=1, bits="0")
        elif change == "duplicate":
            tests[0]["vectors"][1] = copy.deepcopy(tests[0]["vectors"][0])
        elif change == "coverage":
            tests[0]["vectors"].pop()
        elif change == "empty":
            tests[0]["vectors"] = []
        else:
            tests.append(copy.deepcopy(tests[0]))
        with pytest.raises(ContractError):
            bounded_operation(operation("wrap", executionRequest=sample("half-adder"), tests=tests))


def test_chain_reordering_and_incompatible_parent():
    genesis = create_package(sample("half-adder"))
    second = create_package(sample("swapped"), previous=genesis)
    third = create_package(sample("half-adder"), previous=second)
    assert third["ancestors"][0] == genesis["revision"]
    assert third["ancestors"][1] == second["revision"]
    assert parse_package(third).revision.sequence == 2
    for p in [copy.deepcopy(third) for _ in range(3)]:
        p["ancestors"].reverse()
        with pytest.raises(ContractError):
            bounded_operation(operation("validate", package=p))
    edits = second["revision"]["editLog"]
    middle = "0x" + "55" * 32
    edits[:] = [
        dict(beforeHash=genesis["executionRequestHash"], afterHash=middle, description="First"),
        dict(beforeHash=middle, afterHash=second["executionRequestHash"], description="Second"),
    ]
    second["revision"]["revisionHash"] = record_hash(second["revision"])
    parse_package(second)
    edits.reverse()
    second["revision"]["revisionHash"] = record_hash(second["revision"])
    with pytest.raises(ContractError):
        bounded_operation(operation("validate", package=second))
    with pytest.raises(ContractError):
        bounded_operation(operation("wrap", executionRequest=sample("swapped"), previous=genesis))
    other = sample("half-adder")
    other["project"]["projectId"] = "other"
    with pytest.raises(ContractError):
        bounded_operation(
            operation(
                "wrap",
                executionRequest=other,
                previous=genesis,
                expectedRevisionHash=genesis["revision"]["revisionHash"],
            )
        )


def test_downgrade_is_explicit_and_discloses_all_loss():
    p = create_package(sample("half-adder"), tests=named())
    with pytest.raises(ContractError):
        bounded_operation(operation("downgrade", package=p))
    result = bounded_operation(operation("downgrade", package=p, allowLossy=True))
    assert result["executionRequest"] == p["executionRequest"]
    assert set(result["discardedFields"]) == {
        "tests",
        "noDeclaredTests",
        "evidenceRefs",
        "revision",
        "ancestors",
        "provenance",
        "agentTaskRef",
    }
    assert result["warning"].startswith("LOSSY_DOWNGRADE")


@pytest.fixture
def evidence():
    raw = sample("half-adder")
    bundle = product(
        "export", dict(schemaVersion="m4-1.0.0", kind="PRODUCT_REQUEST", executionRequest=raw)
    )
    ref = dict(
        kind="FLIP_EVIDENCE",
        digest=bundle["contentHash"],
        executionRequestHash=content_hash(raw),
        reproduce=REPRODUCE,
        engineHash=bundle["comparison"]["engineHash"],
    )
    return raw, bundle, ref


def test_evidence_reference_replay_missing_and_tampering(evidence):
    raw, bundle, ref = evidence
    p = create_package(raw, evidence_refs=[ref])
    assert (
        bounded_operation(operation("replay-evidence", package=p))["results"][0]["status"]
        == "MISSING_EVIDENCE"
    )
    result = bounded_operation(
        operation("replay-evidence", package=p, artifacts={ref["digest"]: bundle})
    )
    assert result["results"][0]["result"]["report"]["verification"]["verdict"] == "EQUIVALENT"
    assert result["results"][0]["result"]["report"]["integrity"]["freshness"] == "HISTORICAL"
    changed = copy.deepcopy(bundle)
    changed["comparison"]["report"]["verification"]["verdict"] = "UNKNOWN"
    with pytest.raises(ContractError):
        bounded_operation(
            operation("replay-evidence", package=p, artifacts={ref["digest"]: changed})
        )
    for field in ("digest", "engineHash", "executionRequestHash"):
        wrong = {**ref, field: "0x" + "00" * 32}
        with pytest.raises((ContractError, ValueError)):
            q = create_package(raw, evidence_refs=[wrong])
            bounded_operation(
                operation("replay-evidence", package=q, artifacts={wrong["digest"]: bundle})
            )
    # Even rehashed, self-consistent claims cannot substitute another project's trusted comparison.
    other = copy.deepcopy(raw)
    other["project"]["projectId"] = "otherProject"
    wrong = {**ref, "executionRequestHash": content_hash(other)}
    q = create_package(other, evidence_refs=[wrong])
    with pytest.raises(ContractError):
        bounded_operation(
            operation("replay-evidence", package=q, artifacts={ref["digest"]: bundle})
        )


def test_cli_api_legacy_parity_and_immutable_output(tmp_path, capsysbinary):
    client = TestClient(app, client=("127.0.0.1", 1))
    body = operation("wrap", executionRequest=sample("half-adder"), tests=named())
    file, output = tmp_path / "request.json", tmp_path / "project.json"
    file.write_bytes(canonical_bytes(body))
    assert main(["portable", "--request", str(file), "--out", str(output)]) == 0
    cli = json.loads(capsysbinary.readouterr().out)
    web = client.post("/api/v1/portable", json=body)
    assert web.status_code == 200 and web.json() == cli
    assert main(["portable", "--request", str(file), "--out", str(output)]) == 3
    capsysbinary.readouterr()
    assert main(["compose", "--project", str(output)]) == 0
    result = json.loads(capsysbinary.readouterr().out)
    assert client.post("/api/v1/compose", json=cli).json() == result
    assert client.post("/api/v1/compose", json=sample("half-adder")).json() == result
    assert (
        client.post("/api/v1/portable", json=operation("downgrade", package=cli)).status_code == 422
    )
    assert client.post("/api/v1/portable", content=b"x" * 1_048_577).status_code == 413


def test_freshness_and_dependency_restrictions():
    raw = sample("half-adder")
    raw["imports"][0]["integrity"]["freshness"] = "STALE"
    p = create_package(raw)
    with pytest.raises(ContractError):
        bounded_operation(operation("open", package=p))
    raw = sample("half-adder")
    raw["imports"].pop()
    p = create_package(raw)
    with pytest.raises(ContractError):
        bounded_operation(operation("open", package=p))
    with pytest.raises(ContractError):
        bounded_operation(
            operation(
                "wrap",
                executionRequest=sample("half-adder"),
                provenance={"sourceFreshness": "CURRENT"},
            )
        )


def test_replay_solver_opt_in_and_no_remote_authority(evidence, monkeypatch):
    raw, bundle, ref = evidence
    p = create_package(raw, evidence_refs=[ref])
    body = operation("replay-evidence", package=p, artifacts={ref["digest"]: bundle})
    monkeypatch.delenv("FLIP_LOCAL_SOLVER", raising=False)
    assert (
        TestClient(app, client=("127.0.0.1", 1)).post("/api/v1/portable", json=body).status_code
        == 501
    )
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    assert (
        TestClient(app, client=("10.0.0.1", 1)).post("/api/v1/portable", json=body).status_code
        == 501
    )
    assert (
        TestClient(app, client=("127.0.0.1", 1)).post("/api/v1/portable", json=body).status_code
        == 200
    )


def test_exported_schema_validates_the_embedded_frozen_request():
    from flip_core.portable_schema_export import artifacts
    from jsonschema import Draft202012Validator

    schema = artifacts()["package.schema.json"]
    validator = Draft202012Validator(schema)
    value = create_package(sample("half-adder"))
    validator.validate(value)
    del value["executionRequest"]["project"]
    assert list(validator.iter_errors(value))


def test_stale_bundle_replay_cannot_promote_freshness(evidence):
    raw, bundle, ref = evidence
    # Generate a genuinely stale reproduction; changing only the annotation on an
    # older reproduction fails the frozen consumer's exact request binding.
    for item in raw["imports"]:
        item["integrity"]["freshness"] = "STALE"
    bundle = product(
        "export", dict(schemaVersion="m4-1.0.0", kind="PRODUCT_REQUEST", executionRequest=raw)
    )
    ref["executionRequestHash"] = content_hash(raw)
    bundle["chainObservation"] = dict(
        schemaVersion="1.0.0",
        chainId=196,
        candidateNetlistHash="0x" + "11" * 32,
        manifestHash="0x" + "11" * 32,
        mode="READ_ONLY_ETH_CALL",
        status="UNKNOWN",
        reasonCode="IMPLEMENTATION_CHANGED",
        observation=None,
        integrity={"freshness": "STALE", "checkedBlock": None},
    )
    bundle["contentHash"] = content_hash({k: v for k, v in bundle.items() if k != "contentHash"})
    ref["digest"] = bundle["contentHash"]
    p = create_package(raw, evidence_refs=[ref])
    result = bounded_operation(
        operation("replay-evidence", package=p, artifacts={ref["digest"]: bundle})
    )
    assert result["freshness"] == "STALE"
    assert result["results"][0]["result"]["report"]["integrity"]["freshness"] == "STALE"


def test_digest_valid_forged_equivalence_is_recomputed(evidence):
    raw, bundle, ref = evidence
    raw["project"]["candidate"]["outputs"].reverse()
    # Rebinding a claim to a different request is insufficient even if the artifact is rehashed.
    ref["executionRequestHash"] = content_hash(raw)
    p = create_package(raw, evidence_refs=[ref])
    with pytest.raises(ContractError):
        bounded_operation(
            operation("replay-evidence", package=p, artifacts={ref["digest"]: bundle})
        )
    bad = copy.deepcopy(bundle)
    bad["comparison"] = []
    bad["contentHash"] = content_hash({k: v for k, v in bad.items() if k != "contentHash"})
    ref["digest"] = bad["contentHash"]
    p = create_package(raw, evidence_refs=[ref])
    with pytest.raises(ContractError):
        bounded_operation(operation("replay-evidence", package=p, artifacts={ref["digest"]: bad}))


def test_independent_portability_evidence_custody():
    import hashlib
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    evidence = root / "docs/evidence/m45-portable-project"
    manifest = (evidence / "MANIFEST.json").read_bytes().replace(b"\r\n", b"\n")
    assert (
        hashlib.sha256(manifest).hexdigest()
        == "149c74dd573e97f0d34e2648b088e1096391aa292e4c1678626e9c981c0c8ae3"
    )
    for entry in json.loads(manifest)["files"]:
        raw = (evidence / entry["path"]).read_bytes().replace(b"\r\n", b"\n")
        assert len(raw) == entry["bytes"]
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]
