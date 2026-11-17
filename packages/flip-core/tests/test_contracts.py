import copy
import json
from pathlib import Path

import pytest
from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.contracts import ContractError, validate_contract
from flip_core.models import CONTRACTS, BitVector
from flip_core.schema_export import rendered_schemas
from jsonschema import Draft202012Validator
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs" / "schema"


def example(kind):
    return json.loads((DOCS / "examples" / f"{kind}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("kind", CONTRACTS)
def test_roundtrip_schema_and_determinism(kind):
    data = example(kind)
    model = validate_contract(kind, json.dumps(data))
    raw = canonical_bytes(model)
    assert canonical_bytes(validate_contract(kind, raw)) == raw
    assert {content_hash(validate_contract(kind, raw)) for _ in range(100)} == {content_hash(model)}
    schema = json.loads((DOCS / "1.0.0" / f"{kind}.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(json.loads(raw))
    assert schema["additionalProperties"] is False


def test_generated_schemas_have_no_drift():
    for name, rendered in rendered_schemas().items():
        assert (DOCS / "1.0.0" / name).read_text(encoding="utf-8") == rendered


@pytest.mark.parametrize("kind", CONTRACTS)
@pytest.mark.parametrize("version", ["0.9.0", "1.0.1", "1.1.0", "2.0.0", "future"])
def test_unsupported_versions(kind, version):
    data = example(kind)
    data["schemaVersion"] = version
    with pytest.raises(ContractError) as error:
        validate_contract(kind, json.dumps(data))
    assert error.value.code == "UNSUPPORTED_SCHEMA_VERSION"


@pytest.mark.parametrize("kind", [k for k in CONTRACTS if k != "error-envelope"])
@pytest.mark.parametrize("chain", [8453, 1952, "196", 196.0, True])
def test_wrong_chain(kind, chain):
    data = example(kind)
    data["chainId"] = chain
    with pytest.raises(ContractError):
        validate_contract(kind, json.dumps(data))


@pytest.mark.parametrize("value", [1, 1.0, "01", "-1", "0x1", "1e3", "", str(2**256)])
def test_bad_quantities(value):
    data = example("circuit-identity")
    data["circuitId"] = value
    with pytest.raises(ContractError):
        validate_contract("circuit-identity", json.dumps(data))


def test_large_quantities_and_addresses():
    data = example("circuit-identity")
    data["circuitId"] = str(2**256 - 1)
    data["processor"] = "0x" + "Ab" * 20
    model = validate_contract("circuit-identity", json.dumps(data))
    assert model.circuitId == str(2**256 - 1)
    assert model.processor == data["processor"].lower()
    assert content_hash(model) == content_hash(
        validate_contract(
            "circuit-identity", json.dumps({**data, "processor": data["processor"].lower()})
        )
    )


@pytest.mark.parametrize("address", ["0x1234", "ab" * 20, "0x" + "g0" * 20, 12])
def test_bad_address(address):
    data = example("circuit-identity")
    data["processor"] = address
    with pytest.raises(ContractError):
        validate_contract("circuit-identity", json.dumps(data))


@pytest.mark.parametrize("kind", CONTRACTS)
def test_extra_and_missing_fields(kind):
    data = example(kind)
    data["unexpected"] = True
    with pytest.raises(ContractError):
        validate_contract(kind, json.dumps(data))
    del data["unexpected"]
    del data["schemaVersion"]
    with pytest.raises(ContractError):
        validate_contract(kind, json.dumps(data))


@pytest.mark.parametrize(
    "field,excess",
    [
        ("gateCap", 5001),
        ("refDepthCap", 65),
        ("solverTimeoutMs", 5001),
        ("solverMemoryMiB", 65),
    ],
)
def test_hard_limits(field, excess):
    data = example("project")
    data["limits"][field] = excess
    with pytest.raises(ContractError):
        validate_contract("project", json.dumps(data))


@pytest.mark.parametrize("mutation", ["pin", "mapping", "stateful", "ref-id", "unknown-ref"])
def test_project_semantics(mutation):
    data = example("project")
    if mutation == "pin":
        data["candidate"]["components"][0]["inputs"][0]["pin"] = 2
    elif mutation == "mapping":
        data["comparison"]["inputMap"] = [0, 0]
    elif mutation == "stateful":
        data["sources"][0]["nState"] = 1
    elif mutation == "ref-id":
        data["sources"][0]["identity"]["circuitId"] = str(2**64)
    else:
        data["candidate"]["components"][0]["sourceAlias"] = "absent"
    with pytest.raises(ContractError):
        validate_contract("project", json.dumps(data))


def conclusive_report(verdict):
    data = example("comparison-report")
    data["verification"].update(
        verdict=verdict,
        reasonCode=None,
        solverBackend="Minisat22",
        solverOutcome="UNSAT",
        sourceValidation="PASSED",
        mappingValidation="PASSED",
    )
    data["integrity"]["freshness"] = "HISTORICAL"
    return data


def test_equivalence_is_relative_and_freshness_independent():
    data = conclusive_report("EQUIVALENT")
    model = validate_contract("comparison-report", json.dumps(data))
    assert model.intent == "UNDECLARED"
    assert model.verification.verdict == "EQUIVALENT"
    data["integrity"]["freshness"] = "STALE"
    assert validate_contract("comparison-report", json.dumps(data)).integrity.freshness == "STALE"


@pytest.mark.parametrize("mutation", ["not-run", "timeout", "stateful", "unverified", "mapping"])
def test_false_equivalence_rejected(mutation):
    data = conclusive_report("EQUIVALENT")
    if mutation == "not-run":
        data["verification"]["solverOutcome"] = "NOT_RUN"
    elif mutation == "timeout":
        data["verification"]["reasonCode"] = "SOLVER_TIMEOUT"
    elif mutation == "stateful":
        data["verification"]["candidateNState"] = 1
    elif mutation == "mapping":
        data["inputMap"] = [0, 0]
    else:
        data["verification"]["sourceValidation"] = "UNVERIFIED"
    with pytest.raises(ContractError):
        validate_contract("comparison-report", json.dumps(data))


def test_different_requires_replayed_distinguishing_witness():
    data = conclusive_report("DIFFERENT")
    data["verification"]["solverOutcome"] = "SAT"
    with pytest.raises(ContractError):
        validate_contract("comparison-report", json.dumps(data))

    def vector(bits):
        return {"encoding": "tap02-lsb0-v1", "width": len(bits), "bits": bits}

    data["verification"]["witness"] = {
        "inputs": vector("10"),
        "referenceOutputs": vector("0"),
        "candidateOutputs": vector("1"),
        "replay": "REF_BEAT_REPRODUCED",
        "minimization": "NONE",
    }
    validate_contract("comparison-report", json.dumps(data))
    data["verification"]["witness"]["candidateOutputs"] = vector("0")
    with pytest.raises(ContractError):
        validate_contract("comparison-report", json.dumps(data))


def test_unknown_never_equivalent_and_requires_reason():
    data = example("comparison-report")
    data["verification"]["reasonCode"] = "SOLVER_TIMEOUT"
    assert (
        validate_contract("comparison-report", json.dumps(data)).verification.verdict == "UNKNOWN"
    )
    data["verification"]["reasonCode"] = None
    with pytest.raises(ContractError):
        validate_contract("comparison-report", json.dumps(data))


@pytest.mark.parametrize("label", ["SIMULATION_SUCCESS", "PUBLISHED", "STRUCTURALLY_ACCEPTED"])
def test_preflight_cannot_claim_success_without_observation(label):
    data = example("preflight")
    data["status"] = label
    with pytest.raises(ContractError):
        validate_contract("preflight", json.dumps(data))


def test_preflight_requires_current_fee_and_matching_block():
    data = example("preflight")
    block = {"number": "1", "hash": "0x" + "11" * 32}
    data.update(
        status="STRUCTURALLY_ACCEPTED",
        reasonCode=None,
        observation={
            "block": block,
            "feeWei": "1300000000000000",
            "manifestRevalidated": True,
            "revertData": "0x12345678",
            "classification": "KNOWN_BURN_STAGE",
        },
        integrity={"freshness": "CURRENT", "checkedBlock": block},
    )
    validate_contract("preflight", json.dumps(data))
    data["observation"]["block"] = {**block, "number": "2"}
    with pytest.raises(ContractError):
        validate_contract("preflight", json.dumps(data))


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "cycle", "unreachable"])
def test_bad_manifest_closure(mutation):
    data = example("manifest")
    other = copy.deepcopy(data["root"])
    other["identity"]["circuitId"] = "1"
    if mutation == "duplicate":
        data["dependencies"] = [data["root"]]
    elif mutation == "missing":
        data["edges"] = [{"parent": data["root"]["identity"], "child": other["identity"]}]
    elif mutation == "cycle":
        data["edges"] = [{"parent": data["root"]["identity"], "child": data["root"]["identity"]}]
    else:
        data["dependencies"] = [other]
    with pytest.raises(ContractError):
        validate_contract("manifest", json.dumps(data))


def test_bitvector_explicit_orientation():
    vector = BitVector(encoding="tap02-lsb0-v1", width=9, bits="100000001")
    # Independent TAP-02 section 5 formula, not a simulator or product packer.
    packed = bytearray((vector.width + 7) // 8)
    for i, bit in enumerate(vector.bits):
        packed[i // 8] |= int(bit) << (i % 8)
    assert packed.hex() == "0101"
    for bad in [
        {"encoding": "MSB_FIRST", "width": 2, "bits": "10"},
        {"encoding": "tap02-lsb0-v1", "width": 1, "bits": "10"},
        {"encoding": "tap02-lsb0-v1", "width": 2, "bits": 2},
    ]:
        with pytest.raises(ValidationError):
            BitVector.model_validate(bad)


def test_pinned_bitvector_golden():
    data = json.loads((DOCS / "bitvector-golden.json").read_text(encoding="utf-8"))
    for item in data["vectors"]:
        vector = BitVector.model_validate({key: item[key] for key in ("encoding", "width", "bits")})
        packed = bytearray((vector.width + 7) // 8)
        for i, bit in enumerate(vector.bits):
            packed[i // 8] |= int(bit) << (i % 8)
        assert "0x" + packed.hex() == item["packed"]


def test_nested_version_and_chain_rejected():
    for field, value, code in [
        ("schemaVersion", "1.0.1", "UNSUPPORTED_SCHEMA_VERSION"),
        ("chainId", 8453, "WRONG_CHAIN"),
    ]:
        data = example("project")
        data["sources"][0]["identity"][field] = value
        with pytest.raises(ContractError) as error:
            validate_contract("project", json.dumps(data))
        assert error.value.code == code


def test_preflight_boolean_not_numeric():
    from flip_core.models import CallObservation

    with pytest.raises(ValidationError):
        CallObservation.model_validate(
            {
                "block": {"number": "1", "hash": "0x" + "11" * 32},
                "feeWei": "0",
                "manifestRevalidated": 1,
                "revertData": "0x",
                "classification": "UNRECOGNIZED",
            }
        )


def test_canonical_golden():
    vectors = json.loads((DOCS / "canonical-golden.json").read_text(encoding="utf-8"))["vectors"]
    for vector in vectors:
        assert canonical_bytes(vector["input"]) == vector["canonical"].encode("utf-8")
        assert canonical_bytes(vector["input"]).hex() == vector["utf8Hex"]
        assert content_hash(vector["input"]) == vector["sha256"]
    assert vectors[0]["sha256"] == (
        "0x44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a"
    )


@pytest.mark.parametrize(
    "raw",
    [
        '{"a":1,"a":2}',
        '{"a":1.0}',
        '{"a":NaN}',
        '{"a":Infinity}',
        '{"a":9007199254740992}',
        '{"a":"\\ud800"}',
        '{"é":1}',
        "[",
    ],
)
def test_noncanonical_json_rejected(raw):
    with pytest.raises((ValueError, UnicodeError)):
        load_json(raw)


def test_negative_zero_rejected():
    with pytest.raises(ValueError):
        load_json('{"zero":-0}')


@pytest.mark.parametrize("value", [1.0, float("nan"), 2**53, {1: "a"}, (1, 2)])
def test_noncanonical_python_values_rejected(value):
    with pytest.raises(ValueError):
        canonical_bytes(value)
