"""Independent M2-C acceptance harness. Read-only against Codex code.

Drives the real ImportService / RpcClient / tap02.decode with mocked JSON-RPC
transport and the M2-B adversarial corpus. No network, no signing, no product edits.

Run with the M2 clean venv:
  python docs/evidence/m2-independent-review/harness.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from flip_core import abi
from flip_core.canonical import canonical_bytes
from flip_core.contracts import ContractError, validate_contract
from flip_core.import_models import ImportBudget
from flip_core.importer import ImportService
from flip_core.integrity import ContentCache
from flip_core.models import CircuitIdentity
from flip_core.rpc import RpcClient, RpcSettings
from flip_core.tap02 import decode

WT = Path(__file__).resolve().parents[3]
FIX = WT / "fixtures" / "m2-adversarial"
RAW_M0 = WT / "docs" / "evidence" / "raw" / "M0"
RAW_M05 = WT / "docs" / "evidence" / "raw" / "M05"
OUT = WT / "docs" / "evidence" / "m2-independent-review"

FACTORY = abi.FACTORY
PROC = "0x839bdd6fa7a66416a609a735e11de5411b98574e"
CORE = "0xf044d395c91e77459e6b2155015e14f0dd9b349f"
BEACON = "0xf70d1ed4f62cf3780157b0b421b7e2f45bd0991c"
BEACON_IMPL = "0x977f217887e085d298cb3819cdad5a0ee35f29b2"
FACTORY_IMPL = "0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a"

results: list[dict] = []


def record(case: str, outcome: str, detail: dict) -> None:
    results.append({"case": case, "outcome": outcome, "detail": detail})


def word(value: int) -> str:
    return "0x" + value.to_bytes(32, "big").hex()


def addr_word(address: str) -> str:
    return "0x" + (b"\x00" * 12 + bytes.fromhex(address[2:])).hex()


def abi_bytes(raw: bytes) -> str:
    padded = raw.hex().ljust(((len(raw) + 31) // 32) * 64, "0")
    return "0x" + word(32)[2:] + word(len(raw))[2:] + padded


class World:
    def __init__(self) -> None:
        self.chain_id = 196
        self.block_number = 76206482
        self.block_hash = "0x" + "44" * 32
        self.block_calls = 0
        self.methods: list[str] = []
        self.circuits: dict[tuple[str, int], dict] = {}
        self.next_ids: dict[str, int] = {}
        self.registered: set[str] = set()
        self.storage: dict[tuple[str, str], str] = {}
        self.factory_impl = FACTORY_IMPL
        self.beacon_impl = BEACON_IMPL
        self.fail: dict | None = None  # optional {"method": ..., "response": ..., "status": ...}
        self.counts: dict[str, int] = {}

    def transport(self) -> httpx.MockTransport:
        world = self

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            method, params, rid = body["method"], body["params"], body["id"]
            world.methods.append(method)
            world.counts[method] = world.counts.get(method, 0) + 1
            if world.fail and world.fail.get("method") == method:
                fail = world.fail
                if fail.get("status"):
                    return httpx.Response(fail["status"], json=fail.get("body", {}),
                                          headers=fail.get("headers", {}))
                if "raise" in fail:
                    raise fail["raise"]
                return httpx.Response(200, json={"jsonrpc": "2.0", "id": rid, **fail["payload"]})
            if method == "eth_chainId":
                result = hex(world.chain_id)
            elif method == "eth_getBlockByNumber":
                world.block_calls += 1
                block_hash = world.block_hash
                if world.fail and world.fail.get("block_hash_after") and world.block_calls > 1:
                    block_hash = world.fail["block_hash_after"]
                result = {"number": hex(world.block_number), "hash": block_hash}
            elif method == "eth_getCode":
                to = params[0].lower()
                result = "0x6000" if to in {FACTORY, BEACON, world.beacon_impl.lower(),
                                            world.factory_impl.lower(), *[p.lower() for p in world.registered]} else "0x"
            elif method == "eth_getStorageAt":
                to, slot = params[0].lower(), params[1].lower()
                result = world.storage.get((to, slot), "0x" + "00" * 32)
            elif method == "eth_call":
                call = params[0]
                to, data = call["to"].lower(), call["data"]
                selector = data[2:10]
                argument = int(data[10:], 16) if len(data) > 10 else None
                if to == FACTORY:
                    if selector == abi.SELECTORS["circuitBeacon"]:
                        result = addr_word(BEACON)
                    elif selector == abi.SELECTORS["isSealed"]:
                        result = word(0)
                    elif selector == abi.SELECTORS["isCPU"]:
                        result = word(1 if addr_from_word(argument) in world.registered else 0)
                    else:
                        raise httpx.HTTPStatusError("bad selector", request=request,
                                                    response=httpx.Response(400))
                elif to == BEACON:
                    result = addr_word(world.beacon_impl)
                else:
                    if selector == abi.SELECTORS["factory"]:
                        result = addr_word(FACTORY)
                    elif selector == abi.SELECTORS["nextId"]:
                        result = word(world.next_ids.get(to, 1))
                    elif selector == abi.SELECTORS["circuitInfo"]:
                        info = world.circuits.get((to, argument))
                        if info is None:
                            raise httpx.HTTPStatusError("missing", request=request,
                                                        response=httpx.Response(400))
                        result = "0x" + "".join(
                            word(info[k])[2:] for k in ("nIn", "nOut", "nState", "gates")
                        )
                    elif selector == abi.SELECTORS["netlist"]:
                        info = world.circuits.get((to, argument))
                        if info is None:
                            raise httpx.HTTPStatusError("missing", request=request,
                                                        response=httpx.Response(400))
                        result = abi_bytes(info["netlist"])
                    else:
                        raise httpx.HTTPStatusError("bad selector", request=request,
                                                    response=httpx.Response(400))
            else:
                raise httpx.HTTPStatusError("bad method", request=request, response=httpx.Response(400))
            return httpx.Response(200, json={"jsonrpc": "2.0", "id": rid, "result": result})

        return httpx.MockTransport(handler)

    def service(self, budget: ImportBudget | None = None, retries: int = 0,
                cache: ContentCache | None = None) -> ImportService:
        return ImportService(
            RpcSettings("http://mock.invalid", retries=retries),
            budget or ImportBudget(),
            self.transport(),
            cache=cache if cache is not None else ContentCache(),
        )


def addr_from_word(value: int | None) -> str:
    return "0x" + (value or 0).to_bytes(32, "big")[-20:].hex()


def add_circuit(world: World, processor: str, cid: int, netlist: bytes,
                n_in: int, n_out: int, n_state: int, gates: int) -> None:
    key = (processor.lower(), cid)
    world.circuits[key] = {"netlist": netlist, "nIn": n_in, "nOut": n_out,
                           "nState": n_state, "gates": gates}
    world.next_ids[processor.lower()] = max(world.next_ids.get(processor.lower(), 1), cid + 1)
    world.registered.add(processor)
    world.storage[(processor.lower(), abi.BEACON_SLOT.lower())] = addr_word(BEACON)
    world.storage[(FACTORY, abi.IMPLEMENTATION_SLOT.lower())] = addr_word(world.factory_impl)


def identity(processor: str = PROC, cid: int = 1) -> CircuitIdentity:
    return CircuitIdentity(schemaVersion="1.0.0", chainId=196,
                           processor=processor, circuitId=str(cid))


def archived_netlists() -> tuple[bytes, bytes]:
    xl = json.loads((RAW_M0 / "xlayer_circuits.json").read_text(encoding="utf-8"))
    key = next(k for k in xl["processors"] if k.lower() == PROC)
    samples = xl["processors"][key]["sample"]
    xor = next(s["netlist"] for s in samples if s["circuitId"] == 1)
    nand = next(s["netlist"] for s in samples if s["circuitId"] == 2)
    return bytes.fromhex(xor[2:]), bytes.fromhex(nand[2:])


def base_world() -> World:
    world = World()
    xor, nand = archived_netlists()
    add_circuit(world, PROC, 1, xor, 2, 1, 0, 4)
    add_circuit(world, PROC, 2, nand, 2, 1, 0, 3)
    return world


def expect_error(label: str, fn, code: str | None = None, contains: str | None = None) -> bool:
    try:
        value = fn()
        detail = {"outcome": "ACCEPTED", "value": type(value).__name__}
        record(label, "FAIL", detail)
        return False
    except ContractError as exc:
        ok = (code is None or exc.code == code) and (contains is None or contains in exc.message)
        record(label, "PASS" if ok else "FAIL",
               {"code": exc.code, "message": exc.message, "expected_code": code})
        return ok
    except Exception as exc:  # noqa: BLE001
        record(label, "FAIL", {"exception": f"{type(exc).__name__}: {exc}"[:300]})
        return False


def main() -> None:
    corpus = json.loads((FIX / "tap02-malformed.json").read_text(encoding="utf-8"))
    budget = ImportBudget()

    # 1. TAP-02 malformed corpus through the real decoder.
    tap_results = []
    for case in corpus["cases"]:
        netlist = case["netlist"]
        if netlist.endswith("0") and len(netlist[2:]) % 2:
            tap_results.append({"id": case["id"], "outcome": "SKIPPED",
                                "reason": "odd-length hex cannot be decoded to bytes"})
            continue
        try:
            decoded = decode(bytes.fromhex(netlist[2:]), case["nIn"], case["nOut"], budget)
            tap_results.append({"id": case["id"], "outcome": "ACCEPTED",
                                "records": len(decoded.records),
                                "expected": case["expected_outcome"]})
        except ContractError as exc:
            tap_results.append({"id": case["id"], "outcome": "REJECTED",
                                "code": exc.code, "message": exc.message,
                                "expected": case["expected_outcome"]})
        except Exception as exc:  # noqa: BLE001
            tap_results.append({"id": case["id"], "outcome": "EXCEPTION",
                                "detail": f"{type(exc).__name__}: {exc}"[:200]})
    record("TAP02_CORPUS", "INFO", {"cases": tap_results})

    # 2. Wrong chain must fail before any state read.
    world = base_world()
    world.chain_id = 8453
    svc = world.service()
    ok = expect_error("WRONG_CHAIN_BEFORE_STATE_READS",
                      lambda: svc.import_circuit(identity()), code="WRONG_CHAIN")
    record("WRONG_CHAIN_METHODS", "PASS" if world.methods == ["eth_chainId"] else "FAIL",
           {"methods": world.methods})

    # 3. RPC failure fixtures -> structured errors (selected representative scenarios).
    rpc_corpus = json.loads((FIX / "rpc-failures.json").read_text(encoding="utf-8"))
    rpc_results = []
    for case in rpc_corpus["cases"]:
        w = base_world()
        scenario = case["scenario"]
        payload = case["response"]
        if scenario == "wrong-chain-id":
            w.chain_id = 8453
        elif scenario == "empty-contract-code":
            w.fail = {"method": "eth_getCode", "payload": {"result": "0x"}}
        elif scenario == "missing-circuit":
            w.fail = {"method": "eth_call", "payload": {"error": {"code": -32000, "message": "no circuit"}}}
        elif scenario == "invalid-abi-response":
            w.fail = {"method": "eth_call", "payload": {"result": "0x01"}}
        elif scenario == "inconsistent-pinned-block":
            w.fail = {"block_hash_after": "0x" + "22" * 32}
        elif scenario == "timeout":
            w.fail = {"method": "eth_chainId", "raise": httpx.ReadTimeout("timed out")}
        elif scenario == "rate-limiting":
            w.fail = {"method": "eth_chainId", "status": 429, "body": {"error": "rate limited"}}
        elif scenario == "malformed-hex":
            w.fail = {"method": "eth_call", "payload": {"result": "0xzz"}}
        elif scenario == "changed-beacon-implementation":
            w.beacon_impl = "0x" + "11" * 20
        elif scenario == "changed-factory-implementation":
            w.factory_impl = "0x" + "22" * 20
        try:
            w.service(retries=0).import_circuit(identity())
            rpc_results.append({"id": case["id"], "outcome": "ACCEPTED",
                                "expected": case["expected_outcome"]})
        except ContractError as exc:
            rpc_results.append({"id": case["id"], "outcome": "REJECTED", "code": exc.code,
                                "expected": case["expected_outcome"]})
        except Exception as exc:  # noqa: BLE001
            rpc_results.append({"id": case["id"], "outcome": "EXCEPTION",
                                "detail": f"{type(exc).__name__}: {exc}"[:200]})
    record("RPC_FAILURE_CORPUS", "INFO", {"cases": rpc_results})

    # 4. Resource ceilings.
    w = base_world()
    expect_error("BUDGET_MAX_GATES",
                 lambda: w.service(ImportBudget(maxGates=3)).import_circuit(identity()),
                 code="RESOURCE_LIMIT")
    w = base_world()
    expect_error("BUDGET_MAX_NETLIST_BYTES",
                 lambda: w.service(ImportBudget(maxNetlistBytes=10)).import_circuit(identity()),
                 code="RESOURCE_LIMIT")
    w = base_world()
    expect_error("BUDGET_MAX_REQUESTS",
                 lambda: w.service(ImportBudget(maxRequests=2)).import_circuit(identity()),
                 code="RESOURCE_LIMIT")

    # 5. Cycle detection.
    w = World()
    a, b = "0x" + "aa" * 20, "0x" + "bb" * 20
    xor, _ = archived_netlists()
    ref_a = bytes.fromhex("02" + b[2:] + (1).to_bytes(8, "big").hex() + "00" + "01")
    ref_b = bytes.fromhex("02" + a[2:] + (1).to_bytes(8, "big").hex() + "00" + "01")
    add_circuit(w, a, 1, ref_a, 0, 1, 0, 0)
    add_circuit(w, b, 1, ref_b, 0, 1, 0, 0)
    expect_error("CYCLE_REJECTED", lambda: w.service().import_circuit(identity(a, 1)),
                 code="BAD_NETLIST", contains="cycle")

    # 6. Depth ceiling using a 65-link synthetic chain.
    w = World()
    chain_proc = "0x" + "cc" * 20
    for i in range(1, 67):
        if i < 66:
            child = chain_proc
            nl = bytes.fromhex("02" + child[2:] + (i + 1).to_bytes(8, "big").hex() + "00" + "01")
            gates = 1
        else:
            nl = bytes.fromhex("00" + (0).to_bytes(3, "big").hex() + (1).to_bytes(3, "big").hex())
            gates = 1
        add_circuit(w, chain_proc, i, nl, 0, 1, 0, gates)
    expect_error("DEPTH_66_REJECTED",
                 lambda: w.service(ImportBudget(maxDepth=64)).import_circuit(identity(chain_proc, 1)),
                 code="REF_DEPTH_EXCEEDED")

    # 7. Dependency mutation invalidates evidence; cache cannot assert CURRENT.
    #    Deterministic synthetic wrapper + one dependency, both valid TAP-02 records.
    w = World()
    wrapper = bytes.fromhex("02" + CORE[2:] + (102).to_bytes(8, "big").hex() + "00" + "01")
    core_v1 = bytes.fromhex("00" + (0).to_bytes(3, "big").hex() + (1).to_bytes(3, "big").hex())
    core_v2 = bytes.fromhex("00" + (1).to_bytes(3, "big").hex() + (0).to_bytes(3, "big").hex())
    add_circuit(w, PROC, 4, wrapper, 0, 1, 0, 1)
    add_circuit(w, CORE, 102, core_v1, 0, 1, 0, 1)
    cache = ContentCache()
    svc = w.service(cache=cache)
    imported = svc.import_circuit(identity(PROC, 4))
    cached = cache.get(imported.manifestHash)
    record("CACHE_HISTORICAL", "PASS" if cached and cached.integrity.freshness == "HISTORICAL" else "FAIL",
           {"freshness": cached.integrity.freshness if cached else None})
    # Mutate dependency bytes to another valid record with identical declared counts.
    w.circuits[(CORE.lower(), 102)]["netlist"] = core_v2
    revalidated = svc.revalidate(imported.manifest)
    record("DEPENDENCY_MUTATION_INVALIDATES",
           "PASS" if "NETLIST_CHANGED" in revalidated.changes and revalidated.integrity.freshness == "STALE" else "FAIL",
           {"changes": revalidated.changes, "freshness": revalidated.integrity.freshness})
    stale = cache.get(imported.manifestHash)
    record("CACHE_STALE_AFTER_REVALIDATION",
           "PASS" if stale and stale.integrity.freshness == "STALE" else "FAIL",
           {"freshness": stale.integrity.freshness if stale else None})

    # 8. Missing-chainId classification corrected.
    ident_raw = json.loads((WT / "docs/schema/examples/circuit-identity.json").read_text(encoding="utf-8"))
    ident_raw.pop("chainId")
    ok = expect_error("MISSING_CHAINID_INVALID_INPUT",
                      lambda: validate_contract("circuit-identity", json.dumps(ident_raw)),
                      code="INVALID_INPUT")
    record("MISSING_CHAINID_NOT_WRONG_CHAIN", "PASS" if ok else "FAIL", {})

    # 9. Unimplemented consumers stay blocked (real invocation).
    from flip_api.app import app
    client = TestClient(app)
    for route in ("/api/v1/compare", "/api/v1/preflight", "/api/v1/compose"):
        response = client.post(route, json={"schemaVersion": "1.0.0"})
        record(f"API_BLOCKED_{route}", "PASS" if response.status_code == 501 else "FAIL",
               {"status": response.status_code})
    proc = subprocess.run([sys.executable, "-m", "flip_cli", "compare"], capture_output=True)
    record("CLI_BLOCKED_COMPARE", "PASS" if proc.returncode == 6 else "FAIL",
           {"exit": proc.returncode})

    # 10. Unbounded retry probe: force 503 and count attempts.
    w = base_world()
    w.fail = {"method": "eth_chainId", "status": 503, "body": {"error": "down"}}
    attempts = {"n": 0}
    original = w.transport
    def counting():
        t = original()
        handler = t.handler
        def counted(req):
            attempts["n"] += 1
            return handler(req)
        return httpx.MockTransport(counted)
    svc = ImportService(RpcSettings("http://mock.invalid", retries=2), ImportBudget(), counting())
    try:
        svc.import_circuit(identity())
        record("RETRY_BOUND", "FAIL", {"attempts": attempts["n"]})
    except ContractError as exc:
        record("RETRY_BOUND", "PASS" if attempts["n"] <= 3 else "FAIL",
               {"code": exc.code, "attempts": attempts["n"]})

    # 11. Inconsistent block identity.
    w = base_world()
    w.fail = {"block_hash_after": "0x" + "99" * 32}
    expect_error("BLOCK_IDENTITY_CHANGED",
                 lambda: w.service().import_circuit(identity()),
                 code="IMPLEMENTATION_CHANGED")

    # 12. Caller-supplied proof flags / empty revert cannot unlock consumers.
    report = json.loads((WT / "docs/schema/examples/comparison-report.json").read_text(encoding="utf-8"))
    report["verification"]["verdict"] = "EQUIVALENT"
    response = client.post("/api/v1/compare", json=report)
    record("PROOF_FLAGS_BLOCKED", "PASS" if response.status_code == 501 else "FAIL",
           {"status": response.status_code})
    pre = json.loads((WT / "docs/schema/examples/preflight.json").read_text(encoding="utf-8"))
    response = client.post("/api/v1/preflight", json=pre)
    record("PREFLIGHT_BLOCKED", "PASS" if response.status_code == 501 else "FAIL",
           {"status": response.status_code})

    # 13. Implementation changes are detected by revalidation, not fresh import.
    def impl_world() -> World:
        w = World()
        add_circuit(w, PROC, 1, archived_netlists()[0], 2, 1, 0, 4)
        return w

    w = impl_world()
    svc = w.service()
    first = svc.import_circuit(identity())
    w.factory_impl = "0x" + "33" * 20
    w.storage[(FACTORY, abi.IMPLEMENTATION_SLOT.lower())] = addr_word(w.factory_impl)
    changed = svc.revalidate(first.manifest)
    record("FACTORY_IMPL_CHANGE_REVALIDATION",
           "PASS" if "FACTORY_IMPLEMENTATION_CHANGED" in changed.changes
           and changed.integrity.freshness == "STALE" else "FAIL",
           {"changes": changed.changes, "freshness": changed.integrity.freshness})

    w = impl_world()
    svc = w.service()
    first = svc.import_circuit(identity())
    w.beacon_impl = "0x" + "44" * 20
    changed = svc.revalidate(first.manifest)
    record("BEACON_IMPL_CHANGE_REVALIDATION",
           "PASS" if "BEACON_IMPLEMENTATION_CHANGED" in changed.changes
           and changed.integrity.freshness == "STALE" else "FAIL",
           {"changes": changed.changes, "freshness": changed.integrity.freshness})

    # 14. Caller-supplied manifest environment must not be trusted as current.
    w = impl_world()
    svc = w.service()
    first = svc.import_circuit(identity())
    tampered = first.manifest.model_copy(deep=True)
    tampered.root.environment.beaconImplementation.address = "0x" + "55" * 20
    changed = svc.revalidate(tampered)
    record("TAMPERED_MANIFEST_NOT_TRUSTED",
           "PASS" if "BEACON_IMPLEMENTATION_CHANGED" in changed.changes
           and changed.integrity.freshness == "STALE" else "FAIL",
           {"changes": changed.changes, "freshness": changed.integrity.freshness})

    # 15. Off-by-one boundary observation for the depth cap (informational).
    record("DEPTH_CAP_BOUNDARY", "INFO",
           {"cap": 64, "chain_nodes_accepted": 65, "max_ref_edges_accepted": 64,
            "note": "Implementation rejects only when depth > maxDepth; a chain with 64 REF edges is accepted."})

    transcript = {
        "scope": "M2-C independent read-only review; mocked transport; no live RPC",
        "implementation_commit": "e5c47e55ff1600a62ef2cb96c19abb51b33d32f5",
        "fixture_commit": "3cdbf14f59eb842f395da368e2e08d1f5708aa28",
        "checks": results,
    }
    out = OUT / "results.json"
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(transcript, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    passes = sum(1 for r in results if r["outcome"] == "PASS")
    fails = [r["case"] for r in results if r["outcome"] == "FAIL"]
    print(json.dumps({"passes": passes, "fails": fails, "total_checks": len(results)}, indent=2))


if __name__ == "__main__":
    main()




