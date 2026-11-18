"""Deterministic offline RPC transcript emulation, not live chain verification."""

import copy
import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_cli.main import main as cli
from flip_core import abi
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.contracts import ContractError, validate_contract
from flip_core.import_models import ImportBudget, ImportResult
from flip_core.importer import ImportService
from flip_core.integrity import ContentCache
from flip_core.models import CircuitIdentity
from flip_core.rpc import RpcClient, RpcSettings
from flip_core.tap02 import decode
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
PROC = "0x839bdd6fa7a66416a609a735e11de5411b98574e"
CORE = "0xf044d395c91e77459e6b2155015e14f0dd9b349f"
BEACON = "0xf70d1ed4f62cf3780157b0b421b7e2f45bd0991c"


def identity(cid=1, processor=PROC):
    return CircuitIdentity(
        schemaVersion="1.0.0", chainId=196, processor=processor, circuitId=str(cid)
    )


def word(number):
    return "0x" + number.to_bytes(32, "big").hex()


def address_word(address):
    return word(int(address, 16))


def bytes_return(raw):
    return word(32) + word(len(raw))[2:] + raw.hex() + "00" * (-len(raw) % 32)


def ref(cid, processor=PROC, inputs=(2, 3), outputs=1):
    return (
        b"\x02"
        + bytes.fromhex(processor[2:])
        + cid.to_bytes(8, "big")
        + bytes((len(inputs), outputs))
        + b"".join(i.to_bytes(3, "big") for i in inputs)
    )


class FakeChain:
    def __init__(self):
        archive = json.loads((ROOT / "docs/evidence/raw/M05/gate_b_manifest.json").read_bytes())
        composition = json.loads((ROOT / "docs/evidence/raw/M0/composition_poc.json").read_bytes())
        xlayer = json.loads((ROOT / "docs/evidence/raw/M0/xlayer_circuits.json").read_bytes())
        self.nodes = {}
        processors = {address.lower(): data for address, data in xlayer["processors"].items()}
        for sample in processors[PROC]["sample"]:
            if sample["circuitId"] in (1, 2):
                fields = (2, 1, 0, 4 if sample["circuitId"] == 1 else 3)
                self.nodes[(PROC, sample["circuitId"])] = (
                    fields,
                    bytes.fromhex(sample["netlist"][2:]),
                )
        wrapper = archive["manifests"][1]
        target = wrapper["dependencies"][0]["target"]
        self.nodes[(PROC, 4)] = ((0, 1, 2, 10), bytes.fromhex(wrapper["netlist"][2:]))
        self.nodes[(CORE, 102)] = ((0, 1, 2, 10), bytes.fromhex(target["netlist"][2:]))
        self.expected_sources = composition["sources"]
        self.requests = []
        self.chain_id = 196
        self.factory_impl = "0x" + "aa" * 20
        self.beacon_impl = "0x" + "bb" * 20
        self.unregistered = set()
        self.reorg = False
        self.headers = 0
        self.bad_info = False
        self.malformed_netlist = None
        self.failures = 0
        self.bad_envelope = False

    def handler(self, request):
        payload = json.loads(request.content)
        self.requests.append(payload)
        if self.failures:
            self.failures -= 1
            return httpx.Response(503)
        result = self.answer(payload["method"], payload["params"])
        return httpx.Response(
            200,
            json={
                "jsonrpc": "2.0",
                "id": 999999 if self.bad_envelope else payload["id"],
                "result": result,
            },
        )

    def answer(self, method, params):
        if method == "eth_chainId":
            return hex(self.chain_id)
        if method == "eth_getBlockByNumber":
            self.headers += 1
            return {
                "number": "0x64" if params[0] == "latest" else params[0],
                "hash": "0x" + ("22" if self.reorg and self.headers % 2 == 0 else "11") * 32,
            }
        if method == "eth_getCode":
            return "0x60016000"
        if method == "eth_getStorageAt":
            return address_word(
                self.factory_impl if params[1] == abi.IMPLEMENTATION_SLOT else BEACON
            )
        assert method == "eth_call"
        to, data = params[0]["to"], params[0]["data"]
        name = next(k for k, v in abi.SELECTORS.items() if data[2:10] == v)
        arg = int(data[10:], 16) if len(data) > 10 else None
        if name == "isCPU":
            return word(int("0x" + arg.to_bytes(20, "big").hex() not in self.unregistered))
        if name == "factory":
            return address_word(abi.FACTORY)
        if name == "circuitBeacon":
            return address_word(BEACON)
        if name == "implementation":
            return address_word(self.beacon_impl)
        if name == "isSealed":
            return word(0)
        if name == "nextId":
            return word(max(cid for cpu, cid in self.nodes if cpu == to) + 1)
        info, raw = self.nodes[(to, arg)]
        if name == "circuitInfo":
            return word(2**32) if self.bad_info else "0x" + "".join(word(n)[2:] for n in info)
        assert name == "netlist"
        return self.malformed_netlist if self.malformed_netlist is not None else bytes_return(raw)

    def service(self, **budget):
        return ImportService(
            RpcSettings(retries=0), ImportBudget(**budget), httpx.MockTransport(self.handler)
        )


@pytest.fixture
def chain():
    return FakeChain()


def test_import_recorded_xor_and_nand_with_strict_block_context(chain):
    for source in chain.expected_sources:
        result = chain.service().import_circuit(identity(source["id"]))
        assert result.manifest.root.netlistHash == "0x" + source["netlistSha256"]
        assert result.integrity.freshness == "CURRENT"
        assert result.manifestHash == content_hash(result.manifest)
        assert ImportResult.model_validate_json(result.model_dump_json()) == result
    for request in chain.requests:
        if request["method"] not in ("eth_chainId", "eth_getBlockByNumber"):
            assert request["params"][-1] == "0x64"


def test_complete_wrapper_closure_state_and_environment(chain):
    result = chain.service().import_circuit(identity(4))
    assert result.manifest.root.nState == 2
    assert len(result.manifest.dependencies) == len(result.manifest.edges) == 1
    assert result.manifest.dependencies[0].identity == identity(102, CORE)
    assert result.manifest.root.environment.beaconImplementation.address == chain.beacon_impl
    assert result.manifest.dependencies[0].environment.processorCodeHash.startswith("0x")


def test_wrong_chain_fails_before_state_reads(chain):
    chain.chain_id = 8453
    with pytest.raises(ContractError) as error:
        chain.service().import_circuit(identity())
    assert error.value.code == "WRONG_CHAIN"
    assert len(chain.requests) == 1
    with pytest.raises(ValidationError):
        CircuitIdentity(schemaVersion="1.0.0", chainId=8453, processor=PROC, circuitId="1")


@pytest.mark.parametrize("cid", [0, 3, 999])
def test_missing_ids_rejected(chain, cid):
    if cid == 3:
        # Simulate explicit eth_call failure for a gap below nextId.
        original = chain.handler

        def handler(request):
            p = json.loads(request.content)
            if p["method"] == "eth_call" and p["params"][0]["data"].startswith(
                "0x" + abi.SELECTORS["circuitInfo"]
            ):
                return httpx.Response(
                    200,
                    json={
                        "jsonrpc": "2.0",
                        "id": p["id"],
                        "error": {"code": -32000, "message": "no circuit"},
                    },
                )
            return original(request)

        service = ImportService(transport=httpx.MockTransport(handler))
    else:
        service = chain.service()
    with pytest.raises(ContractError):
        service.import_circuit(identity(cid))


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("bad_info", True, "INVALID_INPUT"),
        ("malformed_netlist", "0x" + "00" * 64, "INVALID_INPUT"),
        ("reorg", True, "IMPLEMENTATION_CHANGED"),
    ],
)
def test_malformed_abi_and_reorg(chain, field, value, code):
    setattr(chain, field, value)
    with pytest.raises(ContractError) as error:
        chain.service().import_circuit(identity())
    assert error.value.code == code


def test_decode_malformed_bytes_and_metadata_counts(chain):
    chain.nodes[(PROC, 1)] = ((2, 1, 0, 1), b"\x03")
    with pytest.raises(ContractError, match="Unknown TAP-02"):
        chain.service().import_circuit(identity())
    chain.nodes[(PROC, 1)] = ((2, 1, 0, 2), bytes.fromhex("00000002000003"))
    with pytest.raises(ContractError, match="disagrees"):
        chain.service().import_circuit(identity())


def test_cycle_unregistered_and_arity(chain):
    chain.nodes[(PROC, 5)] = ((2, 1, 0, 1), ref(6))
    chain.nodes[(PROC, 6)] = ((2, 1, 0, 1), ref(5))
    with pytest.raises(ContractError, match="cycle"):
        chain.service().import_circuit(identity(5))
    chain.unregistered.add(CORE)
    with pytest.raises(ContractError, match="not registered"):
        chain.service().import_circuit(identity(4))
    chain.nodes[(PROC, 5)] = ((2, 1, 0, 4), ref(1, inputs=(2,)))
    with pytest.raises(ContractError, match="arity"):
        chain.service().import_circuit(identity(5))


@pytest.mark.parametrize(
    "limit",
    [
        {"maxRequests": 1},
        {"maxNetlistBytes": 1},
        {"maxTotalBytes": 1},
        {"maxRecords": 1},
        {"maxTotalRecords": 1},
        {"maxGates": 1},
        {"maxCircuits": 1},
    ],
)
def test_allocation_and_network_budgets(chain, limit):
    with pytest.raises(ContractError) as error:
        chain.service(**limit).import_circuit(identity(4))
    assert error.value.code == "RESOURCE_LIMIT"


def test_depth_multiplicity_and_memoization(chain):
    chain.nodes[(PROC, 5)] = ((2, 1, 0, 8), ref(1) + ref(1))
    result = chain.service().import_circuit(identity(5))
    assert result.manifest.root.expandedGates == 8
    assert len(result.manifest.dependencies) == 1
    calls = [
        r
        for r in chain.requests
        if r["method"] == "eth_call" and r["params"][0]["data"] == abi.calldata("netlist", 1)
    ]
    assert len(calls) == 1
    chain.nodes[(PROC, 6)] = ((2, 1, 0, 8), ref(5))
    with pytest.raises(ContractError) as error:
        chain.service(maxDepth=1).import_circuit(identity(6))
    assert error.value.code == "REF_DEPTH_EXCEEDED"
    with pytest.raises(ContractError):
        chain.service(maxGates=7).import_circuit(identity(5))


def test_cache_is_immutable_historical_and_bounded(chain):
    service = chain.service()
    result = service.import_circuit(identity())
    old_digest = result.manifestHash
    cached = service.cache.get(old_digest)
    assert cached.integrity.freshness == "HISTORICAL"
    cached.manifest.root.identity.circuitId = "99"
    assert service.cache.get(old_digest).manifest.root.identity.circuitId == "1"
    tiny = ContentCache(max_bytes=1)
    tiny.put(result)
    assert tiny.get(old_digest) is None
    historical = service.import_circuit(identity(), block_number="99")
    assert historical.integrity.freshness == "HISTORICAL"


@pytest.mark.parametrize(
    "change,expected",
    [
        ("factory_impl", "FACTORY_IMPLEMENTATION_CHANGED"),
        ("beacon_impl", "BEACON_IMPLEMENTATION_CHANGED"),
        ("dependency", "NETLIST_CHANGED"),
    ],
)
def test_revalidation_detects_real_closure_changes(chain, change, expected):
    service = chain.service()
    prior = service.import_circuit(identity(4)).manifest
    if change == "dependency":
        fields, raw = chain.nodes[(CORE, 102)]
        chain.nodes[(CORE, 102)] = (fields, raw[:-3] + b"\0\0\0")
    else:
        setattr(chain, change, "0x" + "cc" * 20)
    revalidated = service.revalidate(prior)
    assert revalidated.integrity.freshness == "STALE"
    assert expected in revalidated.changes
    assert prior != revalidated.observed.manifest
    assert service.cache.get(content_hash(prior)).integrity.freshness == "STALE"


def test_revalidation_rejects_noncanonical_historical_block(chain):
    service = chain.service()
    previous = service.import_circuit(identity()).manifest
    previous.block.hash = "0x" + "00" * 32
    result = service.revalidate(previous)
    assert result.integrity.freshness == "STALE"
    assert "BLOCK_CHANGED" in result.changes


def test_revalidation_unchanged_snapshot_needs_new_rpc_observation(chain):
    service = chain.service()
    previous = service.import_circuit(identity()).manifest
    count = len(chain.requests)
    result = service.revalidate(previous)
    assert len(chain.requests) > count
    assert result.integrity.freshness == "CURRENT"
    assert result.changes == []


@pytest.mark.parametrize("mutation", ["id", "hash", "dependency", "factory", "beacon", "width"])
def test_changed_manifest_fields_cannot_pass_fresh_revalidation(chain, mutation):
    service = chain.service()
    previous = service.import_circuit(identity(4 if mutation == "dependency" else 1)).manifest
    if mutation == "id":
        previous.root.identity.circuitId = "2"
    elif mutation == "hash":
        previous.root.netlistHash = "0x" + "00" * 32
    elif mutation == "dependency":
        previous.dependencies[0].identity.circuitId = "101"
        previous.edges[0].child.circuitId = "101"
    elif mutation == "factory":
        previous.root.environment.factoryImplementationSlot = "0x" + "00" * 32
    elif mutation == "width":
        previous.root.nIn = 3
    else:
        previous.root.environment.beaconImplementation.address = "0x" + "cc" * 20
    assert service.revalidate(previous).integrity.freshness == "STALE"


def test_byte_mutation_and_wrong_processor_are_not_current(chain):
    service = chain.service()
    previous = service.import_circuit(identity()).manifest
    fields, raw = chain.nodes[(PROC, 1)]
    chain.nodes[(PROC, 1)] = (fields, raw[:1] + b"\0\0\0" + raw[4:])
    assert service.revalidate(previous).integrity.freshness == "STALE"
    processor = "0x" + "22" * 20
    previous.root.identity.processor = processor
    chain.unregistered.add(processor)
    with pytest.raises(ContractError):
        service.revalidate(previous)


@pytest.mark.parametrize(
    "raw",
    [
        "0x",
        word(0),
        word(32) + word(2**255)[2:],
        word(32) + word(1)[2:] + "01" + "01" * 31,
    ],
)
def test_dynamic_bytes_offsets_lengths_and_padding(raw):
    with pytest.raises(ContractError):
        abi.dynamic_bytes(raw, 100)


@pytest.mark.parametrize(
    "endpoint", ["file:///tmp/x", "https://user:pass@example.com", "http://bad:port", "http://"]
)
def test_endpoint_configuration_validation(endpoint):
    with pytest.raises(ContractError):
        RpcSettings(endpoint)


def test_retry_budget_and_bad_rpc_envelopes(chain):
    chain.failures = 1
    service = ImportService(RpcSettings(retries=1), transport=httpx.MockTransport(chain.handler))
    assert service.import_circuit(identity()).integrity.freshness == "CURRENT"
    chain.bad_envelope = True
    with pytest.raises(ContractError) as error:
        service.import_circuit(identity())
    assert error.value.code == "RPC_UNAVAILABLE"
    with RpcClient(RpcSettings(), ImportBudget(), httpx.MockTransport(chain.handler)) as rpc:
        for method, params in [
            ("eth_sendRawTransaction", []),
            ("eth_call", [{"to": PROC, "data": "0x7bd3ac1d"}, "latest"]),
        ]:
            with pytest.raises(ContractError):
                rpc.call(method, params)


def test_deadline_fails_without_network(monkeypatch):
    with RpcClient(RpcSettings(), ImportBudget()) as rpc:
        monkeypatch.setattr(rpc, "deadline", 0)
        with pytest.raises(ContractError) as error:
            rpc.call("eth_chainId", [])
        assert error.value.code == "RESOURCE_LIMIT"


def test_structural_vectors_without_evaluation():
    vectors = json.loads((ROOT / "docs/evidence/raw/M0/vectors.json").read_bytes())
    for case in vectors["valid"]:
        raw = bytes.fromhex(case["netlist"][2:])
        assert decode(raw, case["nIn"], case["nOut"], ImportBudget()).original == raw
    for case in vectors["illFormed"][:6]:
        with pytest.raises(ContractError):
            decode(bytes.fromhex(case["netlist"][2:]), case["nIn"], case["nOut"], ImportBudget())


def test_corrected_missing_chain_taxonomy():
    for payload in [{}, {"schemaVersion": "1.0.0", "processor": PROC, "circuitId": "1"}]:
        with pytest.raises(ContractError) as error:
            validate_contract("circuit-identity", json.dumps(payload))
        assert error.value.code == "INVALID_INPUT"
    for chain in [8453, "196", True]:
        payload = {**identity().model_dump(), "chainId": chain}
        with pytest.raises(ContractError) as error:
            validate_contract("circuit-identity", json.dumps(payload))
        assert error.value.code == "WRONG_CHAIN"


def test_cli_api_share_import_service_and_historical_hashes(chain, monkeypatch, capsys):
    service = chain.service()
    monkeypatch.setattr("flip_core.importer.ImportService", lambda *args, **kwargs: service)
    monkeypatch.setattr(app.state, "import_service", service, raising=False)
    code = cli(
        [
            "inspect",
            "--processor",
            PROC.upper().replace("0X", "0x"),
            "--id",
            "1",
            "--block-number",
            "100",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    assert code == 0
    response = TestClient(app).post("/api/v1/import?blockNumber=100", json=identity().model_dump())
    assert response.status_code == 200
    assert canonical_bytes(output) == response.content
    assert output["integrity"]["freshness"] == "HISTORICAL"


def test_api_bad_version_chain_and_arbitrary_endpoint_never_fetch(chain, monkeypatch):
    monkeypatch.setattr(app.state, "import_service", chain.service(), raising=False)
    client = TestClient(app)
    for field, value in [
        ("schemaVersion", "2.0.0"),
        ("chainId", 8453),
        ("rpcUrl", "http://localhost"),
    ]:
        response = client.post("/api/v1/import", json={**identity().model_dump(), field: value})
        assert response.status_code == 422
    assert chain.requests == []


def test_proof_and_empty_revert_consumers_remain_blocked():
    # M3 must bind project/manifest hashes, actual widths, mappings and witnesses;
    # M4 must classify actual non-empty known reverts. No flag unlocks those gates.
    client = TestClient(app)
    for route, payload in [
        ("compare", {"mappingValidation": "PASSED", "verdict": "EQUIVALENT", "inputMap": []}),
        ("preflight", {"status": "STRUCTURALLY_ACCEPTED", "revertData": "0x"}),
    ]:
        response = client.post("/api/v1/" + route, json=payload)
        assert response.status_code == 501
        assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"


def test_import_result_refuses_tampered_hashes_and_missing_bytes(chain):
    raw = chain.service().import_circuit(identity(4)).model_dump(mode="json")
    for mutation in ("hash", "bytes"):
        data = copy.deepcopy(raw)
        if mutation == "hash":
            data["manifestHash"] = "0x" + "00" * 32
        else:
            data["circuits"] = []
        with pytest.raises(ValidationError):
            ImportResult.model_validate(data)


def test_shared_subgraph_still_counts_against_deeper_paths(chain):
    chain.nodes[(PROC, 7)] = ((2, 1, 0, 4), ref(1))
    chain.nodes[(PROC, 8)] = ((2, 1, 0, 4), ref(7))
    chain.nodes[(PROC, 9)] = ((2, 1, 0, 8), ref(7) + ref(8))
    with pytest.raises(ContractError) as error:
        chain.service(maxDepth=2).import_circuit(identity(9))
    assert error.value.code == "REF_DEPTH_EXCEEDED"


def test_decoder_does_not_discard_trailing_bytes():
    with pytest.raises(ContractError):
        decode(bytes.fromhex("00000002000003") + b"\0", 2, 1, ImportBudget())


def test_cli_rejects_wrong_chain_even_with_identity_file(chain, monkeypatch, tmp_path, capsys):
    file = tmp_path / "identity.json"
    file.write_bytes(canonical_bytes(identity()))
    monkeypatch.setattr("flip_core.importer.ImportService", lambda *a, **k: chain.service())
    assert cli(["import", "--identity", str(file), "--chain-id", "8453"]) == 3
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "WRONG_CHAIN"
    assert chain.requests == []


def test_importer_schemas_are_valid_and_have_no_drift(chain):
    from flip_core.import_schema_export import rendered_schemas
    from jsonschema import Draft202012Validator

    for name, text in rendered_schemas().items():
        assert (ROOT / "docs/schema/m2/1.0.0" / name).read_text(encoding="utf-8") == text
        Draft202012Validator.check_schema(json.loads(text))
    result = chain.service().import_circuit(identity(4))
    schema = json.loads(rendered_schemas()["import-result.schema.json"])
    Draft202012Validator(schema).validate(result.model_dump(mode="json"))


def test_live_captures_are_archived_historical_inputs_not_fresh_requests():
    capture = json.loads((ROOT / "docs/milestones/M2_A/live-smoke.json").read_bytes())
    assert capture["status"] == "MATCH"
    assert len(capture["cases"]) == 3
    for case in capture["cases"]:
        artifact = ImportResult.model_validate(case["artifact"])
        assert artifact.integrity.freshness == "HISTORICAL"
        assert artifact.manifest.root.netlistHash == case["expectedNetlistHash"]
        with pytest.raises(ContractError):
            validate_contract("circuit-identity", canonical_bytes(artifact))


def test_readonly_api_openapi_documents_request_and_errors():
    schema = TestClient(app).get("/openapi.json").json()
    operation = schema["paths"]["/api/v1/import"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith(
        "/CircuitIdentity"
    )
    assert "503" in operation["responses"]
