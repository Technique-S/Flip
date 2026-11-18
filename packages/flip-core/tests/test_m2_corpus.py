"""Execute all M2-B specifications at their actual Flip system boundaries."""

import copy
import hashlib
import json
import shutil
import socket
import subprocess
import sys

import httpx
import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_core import abi
from flip_core.canonical import content_hash
from flip_core.contracts import ContractError, validate_contract
from flip_core.import_models import ImportBudget, ImportResult
from flip_core.importer import ImportService
from flip_core.rpc import RpcSettings
from flip_core.tap02 import decode
from pydantic import ValidationError
from test_m2_import import PROC, ROOT, identity, ref, word
from test_m2_import import FakeChain as M2Chain

FIX = ROOT / "fixtures/m2-adversarial"
B_COMMIT = "3cdbf14f59eb842f395da368e2e08d1f5708aa28"


class FakeChain(M2Chain):
    def answer(self, method, params):
        if method == "eth_getCode":
            # Distinct synthetic code identities so hash-swap mutations exercise
            # the actual supplied swapped hashes, not an unrelated replacement.
            return "0x60" + params[0][2:]
        return super().answer(method, params)


def corpus(name):
    return json.loads((FIX / (name + ".json")).read_bytes())["cases"]


TAP = corpus("tap02-malformed")
RPC = corpus("rpc-failures")
INTEGRITY = corpus("integrity-negatives")
REGRESSIONS = corpus("m1-regressions")


def case_number(case):
    return int(case["id"].split("-")[-1])


def injected_service(chain, intercept, *, retries=0, budget=None):
    def handler(request):
        payload = json.loads(request.content)
        answer = intercept(payload)
        if answer is None:
            return chain.handler(request)
        chain.requests.append(payload)
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, httpx.Response):
            return answer
        response = copy.deepcopy(answer)
        response["id"] = payload["id"]  # JSON-RPC correlation, not a fixture rewrite
        return httpx.Response(200, json=response)

    return ImportService(RpcSettings(retries=retries), budget, httpx.MockTransport(handler))


def add_fixture_nodes(chain, case, root_id=200):
    raw = bytes.fromhex(case["netlist"][2:])
    chain.nodes[(PROC, root_id)] = ((case["nIn"], case["nOut"], 0, 1), raw)
    for target in [*case.get("refs", []), *case.get("resolver", {}).values()]:
        if not isinstance(target, dict) or "netlist" not in target:
            continue
        data = bytes.fromhex(target["netlist"][2:])
        parsed = decode(data, target["nIn"], target["nOut"], ImportBudget())
        # Graph fixtures need only reach cycle/depth checks. Leaf counts are exact;
        # no complete valid manifest is claimed for their intentionally bad graph.
        chain.nodes[(target["cpu"].lower(), target["id"])] = (
            (target["nIn"], target["nOut"], parsed.local_state, parsed.local_gates or 1),
            data,
        )
    if case["id"] == "TAP-MAL-008":
        chain.unregistered.add(case["refs"][0]["cpu"].lower())


@pytest.mark.parametrize("case", TAP[:14], ids=lambda c: c["id"])
def test_decoder_safe_corpus(case):
    number = case_number(case)
    raw = bytes.fromhex(case["netlist"][2:])
    assert len(raw) == case["netlist_bytes"]
    assert hashlib.sha256(raw).hexdigest() == case["netlist_sha256"]
    # Twelve cases are locally malformed; REF arity/registration necessarily
    # require the resolver. Execute the local decoder for those two as well.
    if number in (4, 8):
        assert decode(raw, case["nIn"], case["nOut"], ImportBudget()).original == raw
        chain = FakeChain()
        add_fixture_nodes(chain, case)
        with pytest.raises(ContractError) as error:
            chain.service().import_circuit(identity(200))
        expected_code, expected_message = {
            4: ("BAD_NETLIST", "arity"),
            8: ("MISSING_REFERENCE", "not registered"),
        }[number]
    else:
        with pytest.raises(ContractError) as error:
            decode(raw, case["nIn"], case["nOut"], ImportBudget())
        expected_code = "BAD_NETLIST"
        expected_message = {
            1: "Truncated",
            2: "Unknown",
            3: "forward",
            5: "counts",
            6: "Too few",
            7: "Too few",
            9: "Truncated",
            10: "Truncated",
            11: "Truncated",
            12: "counts",
            13: "counts",
            14: "counts",
        }[number]
    assert error.value.code == expected_code
    assert expected_message in error.value.message


@pytest.mark.parametrize("case", TAP[14:], ids=lambda c: c["id"])
def test_transport_graph_and_expansion_boundaries(case):
    number = case_number(case)
    chain = FakeChain()
    if number == 18:
        with pytest.raises(ContractError) as error:
            abi.hex_bytes(case["netlist"], 250_000)
        assert error.value.code == "INVALID_INPUT"
        return
    if number == 17:
        # The fixture contains a symbolic 1,251-link pattern, not complete graph
        # bytes. Its declared 5,004-gate root must be refused before expansion.
        spec = case["resolver"]
        assert spec["links"] * 4 == spec["expanded_gates"] == 5004
        chain.nodes[(PROC, 200)] = (
            (0, 1, 0, spec["expanded_gates"]),
            bytes.fromhex(case["netlist"][2:]),
        )
        with pytest.raises(ContractError) as error:
            chain.service(maxGates=case["expected_outcome"]["cap"]).import_circuit(identity(200))
        assert error.value.code == "RESOURCE_LIMIT"
        assert not any(
            p["method"] == "eth_call" and p["params"][0]["data"] == abi.calldata("netlist", 200)
            for p in chain.requests
        )
        return
    add_fixture_nodes(chain, case)
    # Supply enough read attempts to reach the depth boundary itself; other hard
    # ceilings remain unchanged. No 65/1,251-deep archived decoder is executed.
    with pytest.raises(ContractError) as error:
        chain.service(maxRequests=2048).import_circuit(identity(200))
    code, message = {15: ("BAD_NETLIST", "cycle"), 16: ("REF_DEPTH_EXCEEDED", "depth")}[number]
    assert error.value.code == code
    assert message in error.value.message.lower()


@pytest.mark.parametrize("case", RPC, ids=lambda c: c["id"])
def test_rpc_corpus(case):
    number = case_number(case)
    chain = FakeChain()
    responses = 0
    if number in (9, 10):
        # Symbolic fixture method/storage labels map to the actual read selectors
        # and ERC-1967 slot; only the supplied response value is substituted.
        if number == 9:
            chain.beacon_impl = case["pinned_observed_value"]
        else:
            chain.factory_impl = case["pinned_observed_value"]
        service = chain.service()
        before = service.import_circuit(identity()).manifest
        value = abi.address(case["response"]["result"])
        if number == 9:
            chain.beacon_impl = value
        else:
            chain.factory_impl = value
        result = service.revalidate(before)
        assert result.integrity.freshness == "STALE"
        assert (
            "BEACON_IMPLEMENTATION_CHANGED" if number == 9 else "FACTORY_IMPLEMENTATION_CHANGED"
        ) in result.changes
        assert service.cache.get(content_hash(before)).integrity.freshness == "STALE"
        return

    def intercept(payload):
        nonlocal responses
        method, params = payload["method"], payload["params"]
        data = params[0].get("data", "") if method == "eth_call" else ""
        match = {
            1: method == "eth_chainId",
            2: method == "eth_getCode" and params[0] == PROC,
            3: data.startswith("0x" + abi.SELECTORS["circuitInfo"]),
            4: data.startswith("0x" + abi.SELECTORS["netlist"]),
            5: method == "eth_getBlockByNumber",
            6: data.startswith("0x" + abi.SELECTORS["nextId"]),
            7: method == "eth_getStorageAt",
            8: data.startswith("0x" + abi.SELECTORS["netlist"]),
        }[number]
        if not match:
            return None
        responses += 1
        if number == 6:
            return httpx.ReadTimeout("synthetic recorded timeout")
        if number == 5 and responses > 1:
            return case["second_response"]
        return case["response"]

    service = injected_service(chain, intercept, retries=2)
    with pytest.raises(ContractError) as error:
        service.import_circuit(identity())
    expected = {
        1: "WRONG_CHAIN",
        2: "MISSING_REFERENCE",
        3: "MISSING_REFERENCE",
        4: "INVALID_INPUT",
        5: "IMPLEMENTATION_CHANGED",
        6: "RPC_UNAVAILABLE",
        7: "RPC_UNAVAILABLE",
        8: "INVALID_INPUT",
    }[number]
    assert error.value.code == expected
    if number == 6:
        assert responses == 3
    if number == 7:
        assert responses == 1  # RPC error is not an HTTP retry signal
    assert service.cache._entries == {}


@pytest.mark.parametrize("case", INTEGRITY, ids=lambda c: c["id"])
def test_integrity_corpus(case):
    chain = FakeChain()
    extended = case["id"].startswith("INT-EXT")
    number = case_number(case)
    service = chain.service()
    before_result = service.import_circuit(
        identity(4 if (extended and number == 4) or (not extended and number == 4) else 1)
    )
    previous = before_result.manifest.model_copy(deep=True)
    if (not extended and number == 1) or (extended and number == 7):
        raw = previous.model_dump(mode="json")
        raw["root"]["identity"]["chainId"] = 8453
        with pytest.raises(ContractError) as error:
            validate_contract("manifest", json.dumps(raw))
        assert error.value.code == "WRONG_CHAIN"
        return
    if extended and number in (1, 2, 6):
        raw = previous.model_dump(mode="json")
        if number == 1:
            raw["root"]["identity"].pop("chainId")
        elif number == 2:
            raw["root"]["environment"]["processorCodeHash"] = "11" * 32
        else:
            raw["dependencies"].append(copy.deepcopy(raw["root"]))
        with pytest.raises(ContractError) as error:
            validate_contract("manifest", json.dumps(raw))
        assert error.value.code == "INVALID_INPUT"
        return
    if extended and number in (5, 9):
        raw = before_result.model_dump(mode="json")
        raw["circuits"][0]["netlist"] = "0x" if number == 9 else "0x00000000000000"
        with pytest.raises(ValidationError, match="bind"):
            ImportResult.model_validate(raw)
        return
    if extended:
        if number == 3:
            previous.block.hash = "0x" + "00" * 32
            expected = "BLOCK_CHANGED"
        elif number == 4:
            previous.dependencies[0].netlistHash = "0x" + "00" * 32
            expected = "NETLIST_CHANGED"
        elif number == 8:
            previous.root.environment.factoryImplementation.codeHash = (
                previous.root.environment.beaconImplementation.codeHash
            )
            assert (
                previous.root.environment.factoryImplementation.codeHash
                != before_result.manifest.root.environment.factoryImplementation.codeHash
            )
            expected = "FACTORY_IMPLEMENTATION_CHANGED"
        else:
            raise AssertionError(case["id"])
    else:
        expected = {
            2: "NETLIST_CHANGED",
            3: "NETLIST_CHANGED",
            4: "DEPENDENCIES_CHANGED",
            5: "FACTORY_IMPLEMENTATION_CHANGED",
            6: "BEACON_IMPLEMENTATION_CHANGED",
            8: "BLOCK_CHANGED",
            9: "NETLIST_CHANGED",
        }.get(number)
        if number == 2:
            previous.root.identity.circuitId = "2"
        elif number == 3:
            previous.root.netlistHash = "0x" + "00" * 32
        elif number == 4:
            previous.dependencies[0].identity.circuitId = "101"
            previous.edges[0].child.circuitId = "101"
        elif number == 5:
            previous.root.environment.factoryImplementationSlot = "0x" + "00" * 32
        elif number == 6:
            previous.root.environment.beaconImplementation.address = "0x" + "cc" * 20
        elif number == 7:
            previous.root.identity.processor = "0x" + "22" * 20
            chain.unregistered.add(previous.root.identity.processor)
            with pytest.raises(ContractError):
                service.revalidate(previous)
            return
        elif number == 8:
            previous.block.hash = "0x" + "00" * 32
        elif number == 9:
            fields, raw = chain.nodes[(PROC, 1)]
            chain.nodes[(PROC, 1)] = (fields, raw[:1] + b"\0\0\0" + raw[4:])
    result = service.revalidate(previous)
    assert result.integrity.freshness == "STALE"
    assert expected in result.changes
    assert before_result.integrity.freshness == "CURRENT"  # old object was not rewritten


@pytest.mark.parametrize("case", REGRESSIONS, ids=lambda c: c["id"])
def test_m1_regression_corpus(case):
    number = case_number(case)
    if number in (1, 4):
        raw = identity().model_dump(mode="json")
        if number == 1:
            raw.pop("chainId")
        else:
            raw["chainId"] = 196.0
        with pytest.raises(ContractError) as error:
            validate_contract("circuit-identity", json.dumps(raw))
        assert error.value.code == "INVALID_INPUT"
        return
    name = "comparison-report" if number == 2 else "preflight"
    raw = json.loads((ROOT / f"docs/schema/examples/{name}.json").read_bytes())
    if number == 2:
        raw["verification"].update(
            verdict="EQUIVALENT",
            reasonCode=None,
            solverBackend="Minisat22",
            solverOutcome="UNSAT",
            sourceValidation="PASSED",
            mappingValidation="PASSED",
        )
        raw["integrity"]["freshness"] = "HISTORICAL"
        raw["inputMap"] = []
        raw["outputMap"] = [0]
    else:
        block = {"number": "1", "hash": "0x" + "11" * 32}
        raw.update(
            status="STRUCTURALLY_ACCEPTED",
            reasonCode=None,
            observation={
                "block": block,
                "feeWei": "0",
                "manifestRevalidated": True,
                "revertData": "0x",
                "classification": "KNOWN_BURN_STAGE",
            },
            integrity={"freshness": "CURRENT", "checkedBlock": block},
        )
    # Explicitly retain the distinction: v1 shape can accept these assertions;
    # the actual consumers cannot accept them or manufacture trusted results.
    validate_contract(name, json.dumps(raw))
    response = TestClient(app).post(
        "/api/v1/compare" if number == 2 else "/api/v1/preflight", json=raw
    )
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"
    if number == 3:
        raw["observation"]["revertData"] = "0xdeadbeef"
        raw["observation"]["classification"] = "UNRECOGNIZED"
        assert TestClient(app).post("/api/v1/preflight", json=raw).status_code == 501


def test_corpus_register_and_exact_regeneration(tmp_path):
    manifest = json.loads((FIX / "MANIFEST.json").read_bytes())
    for item in manifest["artifacts"]:
        raw = (ROOT / item["path"]).read_bytes()
        assert len(raw) == item["bytes"]
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
        assert (
            subprocess.check_output(["git", "show", B_COMMIT + ":" + item["path"]], cwd=ROOT) == raw
        )
    generator = ROOT / manifest["generated_by"]
    assert hashlib.sha256(generator.read_bytes()).hexdigest() == manifest["generator_sha256"]
    scratch = tmp_path / "regeneration"
    shutil.copytree(ROOT / "docs/evidence/raw", scratch / "docs/evidence/raw")
    copied = scratch / manifest["generated_by"]
    copied.parent.mkdir(parents=True)
    shutil.copy2(generator, copied)
    subprocess.run([sys.executable, "-B", str(copied)], check=True, capture_output=True, timeout=20)
    for path in [*(ROOT / i["path"] for i in manifest["artifacts"]), FIX / "MANIFEST.json"]:
        assert (scratch / path.relative_to(ROOT)).read_bytes() == path.read_bytes()


def test_corpus_coverage_and_provenance_are_not_promoted():
    assert [len(TAP), len(RPC), len(INTEGRITY), len(REGRESSIONS)] == [18, 10, 18, 4]
    assert (
        sum(c["archived_reference_decoder_execution"] == "reference_decoder_safe" for c in TAP)
        == 14
    )
    assert all(c["not_an_observation"] for c in RPC)
    assert all(c["status"] == "SPEC_ONLY_NOT_PASSING_AGAINST_FROZEN_M1" for c in REGRESSIONS)
    assert all(c["not_an_observation"] for c in INTEGRITY if c["id"].startswith("INT-EXT"))


def test_pytest_blocks_external_dns_and_sockets():
    with pytest.raises(AssertionError, match="External DNS"):
        socket.getaddrinfo("rpc.xlayer.tech", 443)
    with socket.socket() as sock, pytest.raises(AssertionError, match="External network"):
        sock.connect(("8.8.8.8", 443))


@pytest.mark.parametrize("boundary", ["bytes", "records"])
def test_aggregate_budget_stops_before_fetch_and_decode_of_extra_node(boundary, monkeypatch):
    import flip_core.importer as importer

    chain = FakeChain()
    chain.nodes[(PROC, 1)] = ((0, 1, 0, 1), bytes.fromhex("00000000000001"))
    raw_root = ref(1, inputs=())
    chain.nodes[(PROC, 5)] = ((0, 1, 0, 1), raw_root)
    calls = []
    original = importer.decode

    def observed_decode(*args, **kwargs):
        calls.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(importer, "decode", observed_decode)
    limits = {"maxTotalBytes": len(raw_root)} if boundary == "bytes" else {"maxTotalRecords": 1}
    with pytest.raises(ContractError) as error:
        chain.service(**limits).import_circuit(identity(5))
    assert error.value.code == "RESOURCE_LIMIT"
    assert calls == [raw_root]
    assert not any(
        p["method"] == "eth_call" and p["params"][0]["data"] == abi.calldata("netlist", 1)
        for p in chain.requests
    )


def test_expansion_checks_actual_multiplicity_when_declared_count_is_understated():
    chain = FakeChain()
    spec = TAP[16]["resolver"]
    leaf = bytes.fromhex("00000000000001") * 4
    chain.nodes[(PROC, 1)] = ((0, 1, 0, 4), leaf)
    # Additional synthetic shallow DAG: use the symbolic case's multiplicity,
    # keep depth=1, and understate metadata to force computed expansion checking.
    chain.nodes[(PROC, 200)] = ((0, 1, 0, 5000), ref(1, inputs=()) * spec["links"])
    with pytest.raises(ContractError) as error:
        chain.service(maxGates=5000).import_circuit(identity(200))
    assert error.value.code == "RESOURCE_LIMIT"
    assert "Expanded gate/state" in error.value.message


@pytest.mark.parametrize("declared_state,accepted", [(2, True), (1, False)])
def test_duplicate_dependencies_count_state_and_gates_per_use(declared_state, accepted):
    chain = FakeChain()
    chain.nodes[(PROC, 1)] = ((0, 1, 1, 1), bytes.fromhex("01000000"))
    chain.nodes[(PROC, 200)] = ((0, 1, declared_state, 2), ref(1, inputs=()) * 2)
    if accepted:
        result = chain.service().import_circuit(identity(200))
        assert result.manifest.root.nState == result.manifest.root.expandedGates == 2
        assert len(result.manifest.dependencies) == len(result.manifest.edges) == 1
    else:
        with pytest.raises(ContractError) as error:
            chain.service().import_circuit(identity(200))
        assert error.value.code == "BAD_NETLIST"


def test_rpc_failure_does_not_fall_back_to_current_cached_result(monkeypatch):
    chain = FakeChain()
    service = chain.service()
    prior = service.import_circuit(identity())
    chain.failures = 3
    cache_reads = []
    original = service.cache.get
    monkeypatch.setattr(
        service.cache, "get", lambda digest: (cache_reads.append(digest), original(digest))[1]
    )
    with pytest.raises(ContractError) as error:
        service.import_circuit(identity())
    assert error.value.code == "RPC_UNAVAILABLE"
    assert cache_reads == []
    assert original(prior.manifestHash).integrity.freshness == "HISTORICAL"


@pytest.mark.parametrize(
    "value,decoder",
    [
        ("0x" + word(2**32)[2:] * 4, abi.info),
        (word(2**160), abi.address),
        ("0x01", abi.uint),
    ],
)
def test_abi_does_not_truncate_out_of_range_words(value, decoder):
    with pytest.raises(ContractError) as error:
        decoder(value)
    assert error.value.code == "INVALID_INPUT"
