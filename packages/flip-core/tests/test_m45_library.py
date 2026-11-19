"""Executable M45 scenarios, with explicit adapters for narrative research fixtures."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_core import abi
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.import_models import ImportBudget, ImportResult
from flip_core.library import LibraryService, merge_record, search, seed_catalog
from flip_core.library_models import (
    Catalog,
    Favorite,
    LibraryIdentity,
    LibraryRecord,
    LibraryRequest,
)
from flip_core.rpc import RpcClient, RpcSettings
from pydantic import ValidationError
from test_m2_import import PROC, FakeChain, address_word, bytes_return, word

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "fixtures/m45-library-discovery"
CASES = sorted((RESEARCH / "cases").glob("*.json"))


def case(number):
    return json.loads(CASES[number - 1].read_bytes())


class LibraryChain(FakeChain):
    def __init__(self, scenario=None):
        super().__init__()
        self.scenario = scenario
        self.processors = [PROC]
        self.scripts = scenario.get("rpcScript", []) if scenario else []
        self.consumed = set()
        self.owner_ids = []
        self.rate_limits = 0
        self.force_timeout = False

    def handler(self, request):
        payload = json.loads(request.content)
        self.requests.append(payload)
        if self.force_timeout:
            raise httpx.ReadTimeout("synthetic", request=request)
        if self.rate_limits:
            self.rate_limits -= 1
            return httpx.Response(429)
        try:
            result = self.answer(payload["method"], payload["params"])
            reply = {"result": result}
        except KeyError:
            reply = {"error": {"code": 3, "message": "execution reverted: no circuit"}}
        except TimeoutError as exc:
            raise httpx.ReadTimeout("synthetic", request=request) from exc
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": payload["id"], **reply})

    def answer(self, method, params):
        if method == "eth_call":
            data, to = params[0]["data"], params[0]["to"]
            name = next(k for k, v in abi.SELECTORS.items() if data[2:10] == v)
            arg = int(data[10:], 16) if len(data) > 10 else None
            # Research scripts omit environment reads, include partial registration args,
            # and repeat 0x in ABI tuples. Supply inherited synthetic environments;
            # normalize tuple delimiters only HERE, never in production or source bytes.
            for i, entry in enumerate(self.scripts):
                if i in self.consumed or entry.get("selector") != data[:10]:
                    continue
                args = entry.get("args", [])
                if entry.get("to") != to or (args and args[0] != arg):
                    continue
                if name == "isCPU":
                    continue
                self.consumed.add(i)
                response = entry["response"]
                if "error" in response:
                    if "transport" in response["error"]:
                        raise TimeoutError
                    if "429" in response["error"]:
                        # HTTP response injection is separately tested below.
                        continue
                    raise KeyError(arg)
                raw = response["result"]
                return "0x" + raw[2:].replace("0x", "")
            if name == "cpuCount":
                scripted = [
                    e["response"]["result"]
                    for e in self.scripts
                    if e.get("selector") == data[:10] and "result" in e["response"]
                ]
                if scripted:
                    return scripted[-1]
                return word(len(self.processors))
            if name == "cpuAt":
                return address_word(self.processors[arg])
            if name in ("name", "symbol"):
                return bytes_return(b"Processor <display only>")
            if name == "nextId" and to != PROC:
                return word(1)
            if name == "ownerOf":
                self.owner_ids.append(arg)
                if self.scenario and self.scenario["caseId"].endswith(("C02", "C03")):
                    if arg in self.scenario["expected"].get("missingIds", []):
                        raise KeyError(arg)
                    if str(arg) in self.scenario["expected"].get("missingIds", []):
                        raise KeyError(arg)
                    return address_word(PROC)
                if (to, arg) not in self.nodes:
                    raise KeyError(arg)
                return address_word(PROC)
        return super().answer(method, params)

    def library(self, retries=0, **budget):
        return LibraryService(
            RpcSettings(retries=retries), ImportBudget(**budget), httpx.MockTransport(self.handler)
        )


def request(operation="discover", **kwargs):
    return LibraryRequest(operation=operation, **kwargs)


def identity(processor=PROC, cid=None):
    return LibraryIdentity(processor=processor, circuitId=cid)


def test_independent_selectors_and_fixture_blob_custody():
    spec = importlib.util.spec_from_file_location(
        "independent_keccak", RESEARCH / "generators/keccak_selectors.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.self_test()["verified_signatures"] == 11
    for sig, selector in module.self_test()["selectors"].items():
        name = sig.split("(")[0]
        if name in abi.SELECTORS:
            assert abi.SELECTORS[name] == selector
    for name in ("factory", "circuitBeacon", "implementation", "isSealed"):
        assert module.selector(name + "()") == abi.SELECTORS[name]
    import hashlib

    manifest = json.loads((RESEARCH / "SHA256SUMS.manifest.json").read_bytes())
    for item in manifest["files"]:
        assert hashlib.sha256((RESEARCH / item["path"]).read_bytes()).hexdigest() == item["sha256"]


@pytest.mark.parametrize("number", [1, 2, 3])
def test_research_enumeration(number):
    fixture = case(number)
    chain = LibraryChain(fixture)
    proc = fixture["rpcScript"][0]["to"]
    result = chain.library().execute(
        request(
            "discover" if number == 1 else "circuits",
            **({} if number == 1 else {"identity": identity(proc)}),
        )
    )
    if number == 1:
        assert result.status == "COMPLETE"
        assert [r.identity.processor for r in result.results] == [
            r["address"] for r in fixture["expected"]["processorRecords"]
        ]
        found = search(result.catalog, fixture["expected"]["search"]["processorAddress"])
        assert len(found) == 1
    elif number == 2:
        assert [r.identity.circuitId for r in result.results] == [
            r["circuitId"] for r in fixture["expected"]["circuitRecords"]
        ]
        assert result.results[-1].nState == 1
    else:
        assert result.status == "COMPLETE_WITH_GAPS"
        assert [r.identity.circuitId for r in result.results] == fixture["expected"]["existingIds"]
        assert result.missingIds == fixture["expected"]["missingIds"]
    assert result.block.hash and result.rpcCallsUsed <= result.rpcCallBudget
    for record in result.results:
        assert record.environmentDigest == content_hash(record.environment)
        assert record.freshness != "CURRENT"


def test_C04_pages_large_ranges_and_dedup():
    chain = LibraryChain(case(4))
    service = chain.library()
    catalog, cursor = Catalog(), None
    visited = []
    for _ in range(case(4)["expected"]["pagesEmitted"]):
        result = service.execute(request(catalog=catalog, cursor=cursor, limit=3))
        catalog, cursor = result.catalog, result.cursor
    for payload in chain.requests:
        if payload["method"] == "eth_call" and payload["params"][0]["data"].startswith(
            "0x" + abi.SELECTORS["cpuAt"]
        ):
            visited.append(int(payload["params"][0]["data"][10:], 16))
    assert visited == case(4)["expected"]["indicesVisited"]
    assert cursor is None
    assert len([r for r in catalog.records if r.identity.processor == "0x" + "11" * 20]) == 1
    chain = LibraryChain()
    chain.nodes[(PROC, 2**64)] = chain.nodes[(PROC, 1)]
    result = chain.library().execute(request("circuits", identity=identity(), limit=50))
    assert result.status == "PARTIAL_BOUNDED"
    assert result.cursor.offset == "51"
    assert len(chain.owner_ids) == 50


def test_C05_outage_retains_snapshot_and_overlay():
    chain = LibraryChain(case(5))
    prior = seed_catalog()
    prior.overlay.favorites.append(Favorite(identity=identity(cid="1")))
    result = chain.library().execute(request(catalog=prior))
    assert result.status == case(5)["expected"]["discoveryStatus"]
    assert result.catalog == prior
    assert result.errorCode == "RPC_UNAVAILABLE"


def test_C06_rate_limits_retry_budget():
    chain = LibraryChain()
    chain.rate_limits = case(6)["expected"]["throttleEvents"]
    result = chain.library(retries=case(6)["expected"]["maxRetries"]).execute(request())
    assert result.status == "COMPLETE"
    assert result.retriesUsed == 2
    assert result.rpcCallsUsed == len(chain.requests)
    assert result.rpcCallsUsed <= result.rpcCallBudget
    chain.rate_limits = 9
    result = chain.library(retries=2, maxRequests=2).execute(request())
    assert result.status == "UNKNOWN" and result.rpcCallsUsed == 2


@pytest.mark.parametrize("number", [7, 8])
def test_environment_changes_invalidate_old_circuits(number):
    fixture = case(number)
    chain = LibraryChain()
    service = chain.library()
    prior = service.execute(request("circuits", identity=identity())).catalog
    if number == 7:
        chain.factory_impl = fixture["observedEnvironmentChange"]["factoryImplementation"]
    else:
        chain.beacon_impl = "0x" + "cc" * 20
    result = service.execute(request(catalog=prior))
    assert result.status == fixture["expected"]["discoveryStatus"]
    assert all(
        r.freshness == "STALE"
        for r in result.catalog.records
        if r.identity.circuitId and r.environment
    )


def test_C09_reorg_and_cursor_mismatch():
    fixture = case(9)
    chain = LibraryChain()
    first = chain.library().execute(request("circuits", identity=identity(), limit=1))
    chain.reorg = True
    chain.headers = 0
    result = chain.library().execute(
        request("circuits", identity=identity(), catalog=first.catalog, cursor=first.cursor)
    )
    assert result.status == "REORGED"
    assert any(
        r.freshness == fixture["expected"]["affectedRecords"] for r in result.catalog.records
    )
    with pytest.raises(Exception, match="different scan"):
        chain.library().execute(request(cursor=first.cursor))


def test_C10_identity_dedup_provenance():
    fixture = case(10)
    catalog = Catalog()
    for value in fixture["inputRecords"]:
        merge_record(
            catalog,
            LibraryRecord(
                identity=LibraryIdentity(
                    processor=value["processor"], circuitId=value["circuitId"]
                ),
                sources=[value["source"]],
            ),
        )
    assert len(catalog.records) == fixture["expected"]["catalogRecordCount"]
    assert catalog.records[0].key == fixture["expected"]["canonicalKey"]
    assert catalog.records[0].sources == fixture["expected"]["provenanceSources"]


def test_C11_favorite_survives_stale_eviction_and_roundtrip():
    fixture = case(11)
    value = fixture["userOverlay"]["favorites"][0]
    favorite = Favorite(
        identity=identity(value["processor"], value["circuitId"]), label=value["label"]
    )
    catalog = Catalog()
    catalog.overlay.favorites.append(favorite)
    catalog = Catalog.model_validate_json(canonical_bytes(catalog))
    result = LibraryService().execute(request("search", catalog=catalog, query="my XOR"))
    assert len(result.results) == 1
    assert result.results[0].sources == [fixture["expected"]["favoriteStatus"]]
    assert result.results[0].freshness == "UNKNOWN"
    assert result.catalog.overlay.favorites == [favorite]


def test_C12_metadata_rejects_authority_and_removes_controls():
    metadata = case(12)["untrustedUserMetadata"]
    with pytest.raises(ValidationError):
        Favorite(identity=identity(), **metadata)
    safe = Favorite(
        identity=identity(), **{k: metadata[k] for k in ("label", "description", "tags")}
    )
    assert "\u202e" not in safe.label
    assert "<img" in safe.label  # Plain text, escaped by React; never interpreted here.
    assert safe.identity == identity()
    with pytest.raises(ValidationError):
        LibraryRecord(identity=identity(), sources=["USER_IMPORT"], executable=True)


def test_wrong_chain_invalid_address_abort_and_read_allowlist():
    chain = LibraryChain()
    chain.chain_id = 8453
    result = chain.library().execute(request())
    assert result.status == "UNKNOWN" and result.errorCode == "WRONG_CHAIN"
    assert len(chain.requests) == 1
    with pytest.raises(ValidationError):
        identity("bad")
    chain = LibraryChain()
    chain.unregistered.add(PROC)
    assert (
        chain.library().execute(request("circuits", identity=identity())).errorCode
        == "MISSING_REFERENCE"
    )
    service = chain.library()
    service.aborted = lambda: True
    result = service.execute(request())
    assert result.status == "ABORTED" and result.rpcCallsUsed <= 1
    with RpcClient(RpcSettings(), ImportBudget(), httpx.MockTransport(chain.handler)) as rpc:
        with pytest.raises(Exception, match="allowlisted"):
            rpc.call("eth_sendRawTransaction", ["0x00"])


def test_import_revalidation_and_bounded_recents():
    chain = LibraryChain()
    service = chain.library()
    first = service.execute(request("import", identity=identity(cid="1")))
    assert first.status == "COMPLETE"
    imported = ImportResult.model_validate(first.imported)
    assert imported.integrity.freshness == "CURRENT"
    assert first.catalog.overlay.recents[0].manifestHash == imported.manifestHash
    chain.beacon_impl = "0x" + "cc" * 20
    changed = service.execute(
        request("revalidate", identity=identity(cid="1"), catalog=first.catalog)
    )
    assert changed.status == "ENVIRONMENT_CHANGED" and changed.imported is None
    assert changed.catalog.overlay.recents == first.catalog.overlay.recents
    for cid in range(5, 39):
        chain.nodes[(PROC, cid)] = chain.nodes[(PROC, 1)]
        fresh = service.execute(
            request("import", identity=identity(cid=str(cid)), catalog=first.catalog)
        )
        first.catalog = fresh.catalog
    assert len(first.catalog.overlay.recents) == 30
    assert first.catalog.overlay.recents[0].identity.circuitId == "38"
    chain.force_timeout = True
    failed = service.execute(
        request("revalidate", identity=identity(cid="38"), catalog=first.catalog)
    )
    assert failed.status == "VERIFICATION_FAILED" and failed.imported is None


def test_api_core_cli_parity_persistence_and_frozen_schema(tmp_path):
    body = request(
        "favorite",
        identity=identity(cid="1"),
        metadata=Favorite(identity=identity(cid="1"), label="XOR"),
    )
    expected = LibraryService().execute(body)
    with TestClient(app) as client:
        response = client.post("/api/library/v1/execute", json=body.model_dump(mode="json"))
        assert response.status_code == 200
        assert response.json() == expected.model_dump(mode="json")
        assert client.post("/api/library/v1/execute", json={"operation": "sign"}).status_code == 422
    path, saved = tmp_path / "request.json", tmp_path / "catalog.json"
    path.write_bytes(canonical_bytes(body))
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "flip_cli",
            "library",
            "--request",
            str(path),
            "--catalog",
            str(saved),
        ],
        capture_output=True,
    )
    assert completed.returncode == 0, completed.stdout
    assert json.loads(completed.stdout) == expected.model_dump(mode="json")
    assert Catalog.model_validate_json(saved.read_bytes()) == expected.catalog


def test_discovery_api_core_parity_and_metadata_boundaries():
    chain = LibraryChain()
    app.state.library_service = chain.library()
    try:
        with TestClient(app) as client:
            result = client.post("/api/library/v1/execute", json=request().model_dump(mode="json"))
            assert result.status_code == 200
            assert result.json() == LibraryChain().library().execute(request()).model_dump(
                mode="json"
            )
    finally:
        del app.state.library_service
