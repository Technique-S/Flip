"""Independent deterministic acceptance of M3; synthetic environments are explicit."""

import copy
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_cli.main import main as cli
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.cnf import miter
from flip_core.composition import compile_project, nand, ref
from flip_core.contracts import ContractError
from flip_core.execution import beat, evaluate, pack, unpack, validated_import
from flip_core.import_models import ImportBudget, ImportResult
from flip_core.isolation import run_worker
from flip_core.models import Limits
from flip_core.tap02 import decode
from flip_core.verification import (
    VectorRequest,
    bitvector,
    check_vectors,
    compare,
    compose,
    consume,
    parse_request,
)
from pydantic import ValidationError
from test_m2_import import PROC, FakeChain, identity

ROOT = Path(__file__).resolve().parents[3]
VECTORS = json.loads((ROOT / "docs/evidence/raw/M0/vectors.json").read_bytes())
HISTORY = json.loads((ROOT / "docs/evidence/raw/M0/composition_poc.json").read_bytes())


def pin(component, index=0):
    return {"component": component, "pin": index}


def add_node(chain, cid, raw, ni, no, processor=PROC):
    decoded = decode(raw, ni, no, ImportBudget(maxGates=5000))
    gates, state = decoded.local_gates, decoded.local_state
    for record in decoded.records:
        if record.opcode == 2:
            child = chain.nodes.get((record.processor, record.circuit_id))
            if child:
                state += child[0][2]
                gates += child[0][3]
    chain.nodes[(processor, cid)] = ((ni, no, state, gates), raw)
    return identity(cid, processor)


def imported(chain, root):
    return chain.service(maxGates=5000, maxCircuits=1251, maxRequests=8192).import_circuit(root)


def source(alias, value):
    root = value.manifest.root
    return {
        "alias": alias,
        "identity": root.identity.model_dump(mode="json"),
        "manifestHash": value.manifestHash,
        "nIn": root.nIn,
        "nOut": root.nOut,
        "nState": root.nState,
    }


def request_for(chain, baseline, components, outputs, ni, additional=()):
    sources = [source("baseline", baseline), *[source(a, v) for a, v in additional]]
    raw = {
        "schemaVersion": "m3-1.0.0",
        "kind": "M3_EXECUTION",
        "relation": "BEHAVIORAL",
        "imports": [v.model_dump(mode="json") for v in [baseline, *[v for _, v in additional]]],
        "project": {
            "schemaVersion": "1.0.0",
            "projectId": "m3Acceptance",
            "chainId": 196,
            "toolVersion": "0.1.0",
            "sources": sources,
            "candidate": {"nIn": ni, "components": components, "outputs": outputs},
            "comparison": {
                "kind": "PAIRWISE_EQUIVALENCE",
                "referenceAlias": "baseline",
                "intent": "UNDECLARED",
                "trustAssertion": None,
                "inputMap": list(range(ni)),
                "outputMap": list(range(len(outputs))),
            },
            "limits": Limits(gateCap=5000).model_dump(mode="json"),
        },
    }
    return parse_request(raw)


def ref_component(name, alias, inputs):
    return {"kind": "REF", "instanceId": name, "sourceAlias": alias, "inputs": inputs}


@pytest.fixture
def half_adder():
    chain = FakeChain()
    baseline_id = add_node(chain, 900, bytes.fromhex(HISTORY["composedNetlist"][2:]), 2, 2)
    baseline, xor, nand_import = [
        imported(chain, i) for i in (baseline_id, identity(1), identity(2))
    ]
    components = [
        ref_component("nand", "nandSource", [pin(None, 0), pin(None, 1)]),
        {"kind": "NAND", "instanceId": "carry", "inputs": [pin("nand"), pin("nand")]},
        ref_component("sum", "xor", [pin(None, 0), pin(None, 1)]),
    ]
    return request_for(
        chain,
        baseline,
        components,
        [pin("carry"), pin("sum")],
        2,
        [("xor", xor), ("nandSource", nand_import)],
    )


@pytest.mark.parametrize("vector", VECTORS["valid"], ids=lambda v: v["name"])
def test_official_valid_vectors(vector):
    chain = FakeChain()
    for target in vector["refs"]:
        add_node(
            chain,
            target["id"],
            bytes.fromhex(target["netlist"][2:]),
            target["nIn"],
            target["nOut"],
            target["cpu"],
        )
    root = add_node(chain, 901, bytes.fromhex(vector["netlist"][2:]), vector["nIn"], vector["nOut"])
    _, circuit = validated_import(imported(chain, root), ImportBudget())
    assert circuit.state_width == vector["nState"]
    for row in vector.get("truthTable", []):
        outputs = evaluate(circuit, unpack(bytes.fromhex(row["inputs"]), vector["nIn"]))
        assert pack(outputs).hex() == row["outputs"]
    for row in vector.get("beats", []):
        state, outputs = beat(
            circuit,
            unpack(bytes.fromhex(row["state"]), vector["nState"]),
            unpack(bytes.fromhex(row["inputs"]), vector["nIn"]),
        )
        assert pack(outputs).hex() == row["outputs"]
        assert pack(state).hex() == row["newState"]


@pytest.mark.parametrize("vector", VECTORS["illFormed"], ids=lambda v: v["name"])
def test_official_ill_formed_vectors(vector):
    chain = FakeChain()
    for target in vector["refs"]:
        add_node(
            chain,
            target["id"],
            bytes.fromhex(target["netlist"][2:]),
            target["nIn"],
            target["nOut"],
            target["cpu"],
        )
    chain.nodes[(PROC, 901)] = (
        (vector["nIn"], vector["nOut"], 0, 0),
        bytes.fromhex(vector["netlist"][2:]),
    )
    with pytest.raises(ContractError):
        value = imported(chain, identity(901))
        validated_import(value, ImportBudget())


def test_official_packing_edges_and_roundtrip():
    for width in (0, 1, 7, 8, 9, 255, 65536):
        bits = [i % 2 for i in range(width)]
        assert unpack(pack(bits), width) == bits
    assert unpack(b"", 9) == [0] * 9


@pytest.mark.parametrize("row", VECTORS["packingEdgeCases"]["cases"], ids=lambda r: r["case"])
def test_official_packing_cases(row):
    c = FakeChain()
    _, circuit = validated_import(imported(c, identity(2)), ImportBudget())
    assert pack(evaluate(circuit, unpack(bytes.fromhex(row["inputs"]), 2))).hex() == row["outputs"]


def benchmark_request(target, mode):
    """Synthetic transport, archived real XOR bytes; no invented live observation."""
    chain = FakeChain()
    count = max(1, round(target / 4))
    ni = count + 1
    records, components = [], []
    previous = 2
    for i in range(count):
        other = 3 + i
        records.append(ref(identity(1), [previous, other], 1))
        pins = [pin(None, 0) if i == 0 else pin(f"xor{i - 1}"), pin(None, i + 1)]
        if mode == "equivalent" or mode == "fault_reverse_one" and i == count - 1:
            pins.reverse()
        if mode == "different" and i == count // 2:
            pins = [pin(None, i + 1), pin(None, i + 1)]
        components.append(ref_component(f"xor{i}", "xor", pins))
        previous = 2 + ni + i
    baseline_id = add_node(chain, 900, b"".join(records), ni, 1)
    baseline, xor = imported(chain, baseline_id), imported(chain, identity(1))
    return request_for(chain, baseline, components, [pin(f"xor{count - 1}")], ni, [("xor", xor)])


def test_real_xor_nand_wrapper_and_stateful_rejection():
    chain = FakeChain()
    for cid in (1, 2):
        _, circuit = validated_import(imported(chain, identity(cid)), ImportBudget())
        for a in (0, 1):
            for b in (0, 1):
                assert evaluate(circuit, [a, b]) == [a ^ b if cid == 1 else 1 - (a & b)]
    _, wrapper = validated_import(imported(chain, identity(4)), ImportBudget())
    assert wrapper.state_width == 2
    assert len(beat(wrapper, [0, 0], [])[0]) == 2
    with pytest.raises(ContractError, match="nState"):
        evaluate(wrapper, [])
    with pytest.raises(ContractError) as exc:
        miter(wrapper, wrapper, [], [0])
    assert exc.value.code == "UNSUPPORTED_STATEFUL_PROOF"


def test_audited_81_bytes_100_builds_and_truth_table(half_adder):
    builds = [compose(half_adder) for _ in range(100)]
    assert len({content_hash(b) for b in builds}) == 1
    assert builds[0]["netlist"] == HISTORY["composedNetlist"]
    assert len(bytes.fromhex(builds[0]["netlist"][2:])) == 81
    compiled = compile_project(half_adder.project, half_adder.imports)
    for row in HISTORY["truthTable"]:
        assert (
            pack(evaluate(compiled.candidate, unpack(bytes.fromhex(row["in"]), 2))).hex()
            == row["expected"]
        )


@pytest.mark.parametrize(
    "mutation,expected",
    [
        ("self", "EQUIVALENT"),
        ("symmetric", "EQUIVALENT"),
        ("duplicated", "DIFFERENT"),
        ("output_order", "DIFFERENT"),
    ],
)
def test_canary_and_every_witness_replays(half_adder, mutation, expected):
    raw = half_adder.model_dump(mode="json")
    components = raw["project"]["candidate"]["components"]
    if mutation == "symmetric":
        components[0]["inputs"].reverse()
        components[2]["inputs"].reverse()
    elif mutation == "duplicated":
        components[2]["inputs"][1] = pin(None, 0)
    elif mutation == "output_order":
        raw["project"]["candidate"]["outputs"].reverse()
    request = parse_request(raw)
    result = compare(request)
    assert result["report"]["verification"]["verdict"] == expected, result["resources"]
    assert result["report"]["integrity"]["freshness"] == "HISTORICAL"
    assert result["correctness"] == "INTENT_UNKNOWN"
    if expected == "DIFFERENT":
        witness = result["report"]["verification"]["witness"]
        compiled = compile_project(request.project, request.imports)
        bits = [int(b) for b in witness["inputs"]["bits"]]
        assert evaluate(compiled.reference, bits) != evaluate(compiled.candidate, bits)
        assert result["resources"]["minimizationAttempts"] <= 64


@pytest.mark.parametrize(
    "mutation",
    [
        "input_width",
        "output_width",
        "identity",
        "missing",
        "future",
        "cycle",
        "state",
        "cross_chain",
        "empty_map",
    ],
)
def test_actual_binding_rejections(half_adder, mutation):
    raw = half_adder.model_dump(mode="json")
    project = raw["project"]
    if mutation == "input_width":
        project["sources"][0]["nIn"] = 0
        project["candidate"]["nIn"] = 0
        project["comparison"]["inputMap"] = []
        project["candidate"]["components"] = []
        project["candidate"]["outputs"] = [pin(None, 0)]
    elif mutation == "output_width":
        project["sources"][1]["nOut"] = 2
    elif mutation == "identity":
        project["sources"][1]["identity"]["circuitId"] = "2"
    elif mutation == "missing":
        raw["imports"].pop()
    elif mutation in ("future", "cycle"):
        project["candidate"]["components"][0]["inputs"][0] = pin(
            "sum" if mutation == "future" else "nand"
        )
    elif mutation == "state":
        project["sources"][1]["nState"] = 1
    elif mutation == "cross_chain":
        project["sources"][1]["identity"]["chainId"] = 8453
    else:
        project["comparison"]["inputMap"] = []
    with pytest.raises((ContractError, ValidationError)):
        compose(parse_request(raw))


@pytest.mark.parametrize("mutation", ["edges", "bytes", "gates", "dependency_hash"])
def test_import_manifest_revalidated_not_just_shape(half_adder, mutation):
    raw = half_adder.model_dump(mode="json")
    imported_raw = raw["imports"][0]
    if mutation == "edges":
        imported_raw["manifest"]["edges"].pop()
    elif mutation == "bytes":
        imported_raw["circuits"][0]["netlist"] = "0x00"
    elif mutation == "gates":
        imported_raw["manifest"]["root"]["expandedGates"] = 1
    else:
        imported_raw["manifest"]["dependencies"][0]["netlistHash"] = "0x" + "00" * 32
    imported_raw["manifestHash"] = content_hash(imported_raw["manifest"])
    raw["project"]["sources"][0]["manifestHash"] = imported_raw["manifestHash"]
    with pytest.raises((ContractError, ValidationError)):
        compose(parse_request(raw))


def test_trusted_consumer_reruns_and_rejects_fabricated_equivalence(half_adder):
    report = compare(half_adder)
    kwargs = {
        "expected_project_hash": content_hash(half_adder.project),
        "expected_reference_hash": report["report"]["referenceManifestHash"],
    }
    assert consume(half_adder, report, **kwargs)["report"] == report["report"]
    for field in ("projectHash", "referenceManifestHash", "candidateManifestHash"):
        changed = copy.deepcopy(report)
        changed["report"][field] = "0x" + "00" * 32
        with pytest.raises(ContractError):
            consume(half_adder, changed, **kwargs)
    for field in ("referenceIdentity", "candidateManifest", "engineHash", "engine"):
        changed = copy.deepcopy(report)
        changed[field] = {}
        with pytest.raises(ContractError):
            consume(half_adder, changed, **kwargs)
    raw = half_adder.model_dump(mode="json")
    raw["project"]["candidate"]["outputs"].reverse()
    changed_request = parse_request(raw)
    fake = compare(changed_request)
    fake["report"]["verification"].update(verdict="EQUIVALENT", witness=None, solverOutcome="UNSAT")
    with pytest.raises(ContractError):
        consume(
            changed_request,
            fake,
            expected_project_hash=content_hash(changed_request.project),
            expected_reference_hash=kwargs["expected_reference_hash"],
        )


def test_timeout_crash_and_memory_containment():
    timed = run_worker([], [], Limits(solverTimeoutMs=300), _probe="timeout-probe")
    assert timed["outcome"] == "INTERRUPTED" and timed["reason"] == "SOLVER_TIMEOUT"
    assert timed["wallMs"] < 3000
    memory = run_worker([], [], Limits(), _probe="memory-probe")
    assert memory["probe"] == "MEMORY_BLOCKED", memory
    crash = run_worker([], [], Limits(), _probe="crash-probe")
    assert crash["outcome"] == "INTERRUPTED"
    assert run_worker([[1], [-1]], [1], Limits())["outcome"] == "UNSAT"


def test_timeout_never_equivalent_or_unreplayed_sat(half_adder, monkeypatch):
    import flip_core.verification as engine

    monkeypatch.setattr(
        engine, "run_worker", lambda *a: {"outcome": "INTERRUPTED", "reason": "SOLVER_TIMEOUT"}
    )
    result = compare(half_adder)
    assert result["report"]["verification"]["verdict"] == "UNKNOWN"
    monkeypatch.setattr(engine, "run_worker", lambda *a: {"outcome": "SAT", "witness": [0, 0]})
    result = compare(half_adder)
    assert result["report"]["verification"]["verdict"] == "UNKNOWN"
    assert result["report"]["verification"]["reasonCode"] == "WITNESS_REPLAY_FAILED"


def test_zero_input_checks_and_no_zero_output():
    chain = FakeChain()
    root = add_node(chain, 901, nand(1, 1), 0, 1)
    baseline = imported(chain, root)
    request = request_for(
        chain, baseline, [ref_component("constant", "baseline", [])], [pin("constant")], 0
    )
    assert compare(request)["report"]["verification"]["verdict"] == "EQUIVALENT"
    raw = request.model_dump(mode="json")
    raw["project"]["sources"][0]["identity"]["circuitId"] = "902"
    with pytest.raises(ContractError):
        compose(parse_request(raw))
    raw = request.model_dump(mode="json")
    raw["project"]["candidate"]["outputs"] = []
    with pytest.raises(ContractError):
        parse_request(raw)


def test_output_selection_copy_external_and_duplicates(half_adder):
    raw = half_adder.model_dump(mode="json")
    raw["project"]["candidate"]["outputs"] = [pin(None, 0), pin("nand")]
    request = parse_request(raw)
    compiled = compile_project(request.project, request.imports)
    for a in (0, 1):
        for b in (0, 1):
            assert evaluate(compiled.candidate, [a, b]) == [a, 1 - (a & b)]


def test_vectors_intent_and_exhaustive_coverage(half_adder):
    raw = half_adder.model_dump(mode="json")
    raw["vectors"] = [
        {
            "inputs": bitvector(unpack(bytes.fromhex(row["in"]), 2)).model_dump(mode="json"),
            "outputs": bitvector(unpack(bytes.fromhex(row["expected"]), 2)).model_dump(mode="json"),
        }
        for row in HISTORY["truthTable"]
    ]
    result = check_vectors(VectorRequest.model_validate(raw))
    assert (
        result["verdict"] == "VECTORS_MATCH" and result["coverage"] == "EXHAUSTIVE_DECLARED_DOMAIN"
    )
    raw["vectors"].pop()
    result = check_vectors(VectorRequest.model_validate(raw))
    assert result["coverage"] == "PARTIAL_DECLARED_DOMAIN"
    raw["vectors"][0]["outputs"]["bits"] = "11"
    assert check_vectors(VectorRequest.model_validate(raw))["verdict"] == "VECTORS_MISMATCH"
    raw["vectors"].append(raw["vectors"][0])
    with pytest.raises(ContractError):
        check_vectors(VectorRequest.model_validate(raw))


@pytest.mark.parametrize("relation", ["REFERENCE", "PREVIOUS_VERSION"])
def test_explicit_oracle_relation(half_adder, relation):
    raw = half_adder.model_dump(mode="json")
    raw["relation"] = relation
    raw["project"]["comparison"].update(
        intent="TRUSTED_REFERENCE", trustAssertion="User selected this exact baseline."
    )
    result = compare(parse_request(raw))
    assert result["correctness"] == "USER_DECLARED_REFERENCE_RELATIVE"


def test_cli_api_parity_and_default_solver_gate(half_adder, tmp_path, capsys, monkeypatch):
    client = TestClient(app, client=("127.0.0.1", 50000))
    raw = canonical_bytes(half_adder)
    path = tmp_path / "request.json"
    path.write_bytes(raw)
    assert cli(["compose", "--project", str(path)]) == 0
    cli_result = json.loads(capsys.readouterr().out)
    assert client.post("/api/v1/compose", content=raw).json() == cli_result
    monkeypatch.delenv("FLIP_LOCAL_SOLVER", raising=False)
    assert client.post("/api/v1/compare", content=raw).status_code == 501
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    api = client.post("/api/v1/compare", content=raw)
    assert api.status_code == 200, api.text
    assert cli(["compare", "--project", str(path)]) == 0
    actual = json.loads(capsys.readouterr().out)
    for field in ("report", "candidateManifest", "referenceManifest", "engineHash", "requestHash"):
        assert actual[field] == api.json()[field]


def test_genuine_m2_capture_half_adder_and_local_reference():
    path = ROOT / "docs/schema/m3/examples/half-adder.request.json"
    request = parse_request(path.read_bytes())
    assert all(i.manifest.block.number == "76206482" for i in request.imports)
    built = compose(request)
    assert built["netlist"] == HISTORY["composedNetlist"]
    hashes = {content_hash(compose(request)) for _ in range(100)}
    assert len(hashes) == 1
    compiled = compile_project(request.project, request.imports)
    for row in HISTORY["truthTable"]:
        actual = pack(evaluate(compiled.candidate, unpack(bytes.fromhex(row["in"]), 2)))
        assert actual.hex() == row["expected"]
    assert compare(request)["report"]["verification"]["verdict"] == "EQUIVALENT"
    raw = request.model_dump(mode="json")
    raw["project"]["candidate"]["outputs"].reverse()
    mutated = parse_request(raw)
    different = compare(mutated)
    assert different["report"]["verification"]["verdict"] == "DIFFERENT"
    consume(
        mutated,
        different,
        expected_project_hash=content_hash(mutated.project),
        expected_reference_hash=different["report"]["referenceManifestHash"],
    )
    altered = copy.deepcopy(different)
    altered["report"]["verification"]["witness"]["inputs"]["bits"] = "11"
    with pytest.raises(ContractError) as exc:
        consume(
            mutated,
            altered,
            expected_project_hash=content_hash(mutated.project),
            expected_reference_hash=different["report"]["referenceManifestHash"],
        )
    assert exc.value.code == "WITNESS_REPLAY_FAILED"


def test_genuine_captured_wrapper_replays_sequential_primitive():
    capture = json.loads((ROOT / "docs/milestones/M2_A/live-smoke.json").read_bytes())
    for case in capture["cases"]:
        value = ImportResult.model_validate(case["artifact"])
        _, circuit = validated_import(value, ImportBudget())
        ni, ns = circuit.decoded.n_in, circuit.state_width
        state, output = beat(circuit, [0] * ns, [0] * ni)
        assert len(state) == ns and len(output) == circuit.decoded.n_out
        if case["circuitId"] == "4":
            assert ns == 2
            with pytest.raises(ContractError):
                evaluate(circuit, [])


def test_shared_input_literals_and_nontrivial_output_map(half_adder):
    raw = half_adder.model_dump(mode="json")
    raw["project"]["candidate"]["outputs"].reverse()
    raw["project"]["comparison"]["outputMap"] = [1, 0]
    raw["project"]["comparison"]["inputMap"] = [1, 0]
    assert compare(parse_request(raw))["report"]["verification"]["verdict"] == "EQUIVALENT"


def test_solver_matches_independent_exhaustive_small_circuits():
    from flip_core.cnf import Encoder

    for a in (0, 1):
        for b in (0, 1):
            for y in (0, 1):
                enc = Encoder()
                x1, x2, out = enc.fresh(), enc.fresh(), enc.fresh()
                enc.add([x1, out], [x2, out], [-x1, -x2, -out])
                enc.add([x1 if a else -x1], [x2 if b else -x2], [out if y else -out])
                actual = run_worker(enc.clauses, [], Limits())["outcome"]
                assert (actual == "SAT") == (y == 1 - (a & b))


def test_consumer_rejects_environment_substitution(half_adder):
    result = compare(half_adder)
    raw = half_adder.model_dump(mode="json")
    # A consistent substitution can pass structural import validation; the pinned
    # proof binding still must reject it even when every manifest is rehashed.
    for imported_raw in raw["imports"]:
        for snapshot in [
            imported_raw["manifest"]["root"],
            *imported_raw["manifest"]["dependencies"],
        ]:
            snapshot["environment"]["beaconImplementation"]["codeHash"] = "0x" + "ab" * 32
        previous = imported_raw["manifestHash"]
        imported_raw["manifestHash"] = content_hash(imported_raw["manifest"])
        for s in raw["project"]["sources"]:
            if s["manifestHash"] == previous:
                s["manifestHash"] = imported_raw["manifestHash"]
    altered = parse_request(raw)
    with pytest.raises(ContractError):
        consume(
            altered,
            result,
            expected_project_hash=content_hash(half_adder.project),
            expected_reference_hash=result["report"]["referenceManifestHash"],
        )


def test_actual_zero_input_mapping_cannot_hide_real_source_width():
    chain = FakeChain()
    baseline = imported(chain, identity(1))
    request = request_for(
        chain,
        baseline,
        [ref_component("xor0", "baseline", [pin(None, 0), pin(None, 1)])],
        [pin("xor0")],
        2,
    )
    raw = request.model_dump(mode="json")
    raw["project"]["sources"][0]["nIn"] = 0
    raw["project"]["candidate"]["nIn"] = 0
    raw["project"]["candidate"]["components"][0]["inputs"] = []
    raw["project"]["comparison"]["inputMap"] = []
    with pytest.raises(ContractError) as exc:
        compose(parse_request(raw))
    assert exc.value.code == "MISSING_MAPPING"


def test_declared_budget_enforced_by_actual_expansion(half_adder):
    raw = half_adder.model_dump(mode="json")
    raw["project"]["limits"]["gateCap"] = 7
    with pytest.raises(ContractError) as exc:
        compose(parse_request(raw))
    assert exc.value.code == "RESOURCE_LIMIT"


def test_source_alias_never_reinterprets_bytes(half_adder):
    raw = half_adder.model_dump(mode="json")
    first, second = raw["project"]["sources"][1:]
    first["alias"], second["alias"] = second["alias"], first["alias"]
    result = compare(parse_request(raw))
    assert result["report"]["verification"]["verdict"] == "DIFFERENT"


def test_new_api_and_cli_consumer_vectors_and_exit_codes(half_adder, tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    client = TestClient(app, client=("127.0.0.1", 50000))
    result = compare(half_adder)
    consumption = {
        "schemaVersion": "m3-1.0.0",
        "kind": "M3_CONSUMPTION",
        "executionRequest": half_adder.model_dump(mode="json"),
        "claimedResult": result,
        "expectedProjectHash": content_hash(half_adder.project),
        "expectedReferenceHash": result["report"]["referenceManifestHash"],
    }
    path = tmp_path / "consumer.json"
    path.write_bytes(canonical_bytes(consumption))
    assert cli(["consume", "--project", str(path)]) == 0
    cli_result = json.loads(capsys.readouterr().out)
    api = client.post("/api/v1/consume", json=consumption)
    assert api.status_code == 200 and api.json()["report"] == cli_result["report"]
    vectors = half_adder.model_dump(mode="json")
    vectors["vectors"] = [
        {
            "inputs": bitvector([0, 0]).model_dump(mode="json"),
            "outputs": bitvector([0, 0]).model_dump(mode="json"),
        }
    ]
    path.write_bytes(canonical_bytes(vectors))
    assert cli(["vectors", "--project", str(path)]) == 0
    cli_result = json.loads(capsys.readouterr().out)
    api_result = client.post("/api/v1/vectors", json=vectors).json()
    for field in (
        "verdict",
        "candidateManifest",
        "oracleHash",
        "requestHash",
        "engineHash",
        "mismatches",
    ):
        assert api_result[field] == cli_result[field]
    raw = half_adder.model_dump(mode="json")
    raw["project"]["candidate"]["outputs"].reverse()
    path.write_bytes(canonical_bytes(raw))
    assert cli(["compare", "--project", str(path)]) == 1
    capsys.readouterr()
    import flip_core.verification as engine

    monkeypatch.setattr(
        engine, "run_worker", lambda *a: {"outcome": "INTERRUPTED", "reason": "SOLVER_TIMEOUT"}
    )
    assert cli(["compare", "--project", str(path)]) == 2
    assert json.loads(capsys.readouterr().out)["report"]["verification"]["verdict"] == "UNKNOWN"


def test_api_never_publicly_enables_native_solver(half_adder, monkeypatch):
    monkeypatch.setenv("FLIP_LOCAL_SOLVER", "1")
    client = TestClient(app, client=("203.0.113.1", 12345))
    assert client.post("/api/v1/compare", content=canonical_bytes(half_adder)).status_code == 501


def test_full_request_python_node_hash_parity(tmp_path):
    import subprocess

    request = parse_request((ROOT / "docs/schema/m3/examples/half-adder.request.json").read_bytes())
    path = tmp_path / "parity.json"
    path.write_bytes(canonical_bytes(request))
    script = """
const fs=require('node:fs'), crypto=require('node:crypto');
function sort(v) {
  if (Array.isArray(v)) return v.map(sort);
  if (v !== null && typeof v === 'object')
    return Object.fromEntries(Object.keys(v).sort().map(k=>[k,sort(v[k])]));
  return v;
}
const v=JSON.parse(fs.readFileSync(process.argv[1], 'utf8'));
console.log('0x'+crypto.createHash('sha256').update(JSON.stringify(sort(v))).digest('hex'));
"""
    actual = subprocess.check_output(["node", "-e", script, str(path)], text=True).strip()
    assert actual == content_hash(request)
