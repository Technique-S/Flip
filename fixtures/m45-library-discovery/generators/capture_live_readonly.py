"""Bounded, read-only X Layer mainnet observation for M4.5-2L discovery research.

Allowed RPC methods: eth_chainId, eth_blockNumber, eth_getBlockByNumber,
eth_getCode, eth_getStorageAt, eth_call, eth_getLogs (availability probe only).
No signing, no wallet, no transactions, no state overrides, no large scans.
All state reads are pinned to one observed block. Provider is untrusted.

Usage: python fixtures/m45-library-discovery/generators/capture_live_readonly.py
Optional: FLIP_M45_RPC_URL (must be a credential-free http(s) URL).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from keccak_selectors import self_test, selector  # noqa: E402

FACTORY = "0x1f09daefa827f02cbb40967cc91b259763760761"
IMPL_SLOT = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
BEACON_SLOT = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50"
DEFAULT_RPC = "https://rpc.xlayer.tech"
PROC0 = "0x839bdd6fa7a66416a609a735e11de5411b98574e"
PROC1 = "0x0565ea48ca41ae559d8d491dbb0a9ec945db551b"
OUT_DIR = Path(__file__).resolve().parents[1] / "observations"
TIMEOUT = 15.0
CALL_BUDGET = 40
_calls = 0


def rpc(endpoint: str, method: str, params: list) -> dict:
    global _calls
    _calls += 1
    if _calls > CALL_BUDGET:
        raise RuntimeError("RPC call budget exhausted")
    if method not in {
        "eth_chainId", "eth_blockNumber", "eth_getBlockByNumber", "eth_getCode",
        "eth_getStorageAt", "eth_call", "eth_getLogs",
    }:
        raise ValueError(f"method not allowed: {method}")
    body = json.dumps({"jsonrpc": "2.0", "id": _calls, "method": method, "params": params}).encode()
    request = urllib.request.Request(endpoint, data=body, headers={
        "Content-Type": "application/json",
        "User-Agent": "flip-m45-library-discovery-research/0.1 (read-only)",
    })
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def result_or_error(out: dict):
    if "error" in out:
        return {"ok": False, "error": out["error"]}
    return {"ok": True, "value": out.get("result")}


def call(endpoint: str, to: str, sig: str, block: str, *args: int) -> dict:
    data = "0x" + selector(sig)
    for number in args:
        data += number.to_bytes(32, "big").hex()
    return result_or_error(rpc(endpoint, "eth_call", [{"to": to, "data": data}, block]))


def hex_int(result: dict) -> int | None:
    """Decode a short quantity result (eth_chainId / eth_blockNumber)."""
    if not result.get("ok") or not isinstance(result["value"], str):
        return None
    raw = result["value"][2:]
    return int(raw, 16) if raw and all(c in "0123456789abcdefABCDEF" for c in raw) else None


def word_int(result: dict) -> int | None:
    """Decode an ABI-encoded 32-byte uint word."""
    if not result.get("ok") or not isinstance(result["value"], str):
        return None
    raw = result["value"][2:]
    return int(raw, 16) if len(raw) == 64 else None


def word_address(result: dict) -> str | None:
    if not result.get("ok") or not isinstance(result["value"], str):
        return None
    raw = result["value"][2:]
    return "0x" + raw[-40:].lower() if len(raw) >= 40 else None


def code_hash(endpoint: str, address: str | None, block: str) -> dict:
    if not address:
        return {"ok": False, "error": "no address"}
    out = result_or_error(rpc(endpoint, "eth_getCode", [address, block]))
    if not out.get("ok") or not isinstance(out["value"], str):
        return out
    raw = out["value"][2:]
    return {"ok": True, "bytes": len(raw) // 2,
            "sha256": hashlib.sha256(bytes.fromhex(raw)).hexdigest() if raw else None}


def main() -> int:
    proof = self_test()
    endpoint = os.environ.get("FLIP_M45_RPC_URL", DEFAULT_RPC)
    if "@" in endpoint or "key" in endpoint.lower() or "token" in endpoint.lower():
        print("Refusing endpoint containing credential-like material")
        return 2
    report = {
        "artifactType": "OBSERVED_READ_ONLY",
        "provenance": "LIVE_RPC_SINGLE_UNTRUSTED_PROVIDER",
        "providerTrustAssumption": (
            "One public RPC endpoint; response truth is NOT consensus-verified. "
            "No multi-operator agreement, no independent node cross-check."
        ),
        "endpointHost": urllib.parse.urlparse(endpoint).netloc,
        "abiSourceProvenance": (
            "Selectors recomputed locally with dependency-free Keccak-256 (self_test passed); "
            "cpuCount/cpuAt from experiments/src/xlayer_probe.py (M0 audit), "
            "nextId/circuitInfo/netlist/isCPU from packages/flip-core/src/flip_core/abi.py, "
            "ownerOf from EIP-721, factory interface from TAP-10 Appendix A."
        ),
        "selectorProof": proof,
        "methodsUsed": ["eth_chainId", "eth_blockNumber", "eth_getBlockByNumber",
                        "eth_getCode", "eth_getStorageAt", "eth_call", "eth_getLogs"],
        "signingOrBroadcast": False,
        "stateOverrides": False,
    }
    chain = result_or_error(rpc(endpoint, "eth_chainId", []))
    head = result_or_error(rpc(endpoint, "eth_blockNumber", []))
    report["chainId"] = hex_int(chain)
    report["headBlockHex"] = head.get("value") if head.get("ok") else None
    if report["chainId"] != 196 or not report["headBlockHex"]:
        report["abort"] = "chainId != 196 or head unavailable"
        _write(report)
        return 1
    block = report["headBlockHex"]
    blk = result_or_error(rpc(endpoint, "eth_getBlockByNumber", [block, False]))
    report["blockNumber"] = int(block, 16)
    report["blockHash"] = (blk.get("value") or {}).get("hash") if blk.get("ok") else None
    report["blockTimestampHex"] = (blk.get("value") or {}).get("timestamp") if blk.get("ok") else None

    factory_code = code_hash(endpoint, FACTORY, block)
    impl_slot = result_or_error(rpc(endpoint, "eth_getStorageAt", [FACTORY, IMPL_SLOT, block]))
    factory_impl = word_address(impl_slot)
    report["factory"] = {
        "address": FACTORY,
        "proxyCode": factory_code,
        "erc1967Implementation": factory_impl,
        "erc1967ImplementationCode": code_hash(endpoint, factory_impl, block),
        "isSealed": word_int(call(endpoint, FACTORY, "isSealed()", block)),
        "cpuCount": word_int(call(endpoint, FACTORY, "cpuCount()", block)),
    }

    count = report["factory"]["cpuCount"]
    indices = []
    if count and count > 0:
        indices = sorted(set([0, 1, count - 1]))
    report["factory"]["cpuAtSample"] = {
        str(i): word_address(call(endpoint, FACTORY, "cpuAt(uint256)", block, i)) for i in indices
    }

    def call_address(to: str, sig: str, address: str, block_tag: str) -> dict:
        data = "0x" + selector(sig) + address[2:].rjust(64, "0")
        out = result_or_error(rpc(endpoint, "eth_call", [{"to": to, "data": data}, block_tag]))
        return out

    report["factory"]["isCpuSample"] = {
        addr: word_int(call_address(FACTORY, "isCPU(address)", addr, block))
        for addr in sorted(set([PROC0, PROC1] + [a for a in report["factory"]["cpuAtSample"].values() if a]))
    }

    report["processors"] = {}
    for label, address in [("proc0", PROC0), ("proc1", PROC1)]:
        beacon_slot = result_or_error(rpc(endpoint, "eth_getStorageAt", [address, BEACON_SLOT, block]))
        beacon = word_address(beacon_slot)
        beacon_impl = word_address(call(endpoint, beacon, "implementation()", block)) if beacon else None
        entry = {
            "address": address,
            "proxyCode": code_hash(endpoint, address, block),
            "beacon": beacon,
            "beaconImplementation": beacon_impl,
            "beaconImplementationCode": code_hash(endpoint, beacon_impl, block),
            "nameRaw": call(endpoint, address, "name()", block).get("value"),
            "symbolRaw": call(endpoint, address, "symbol()", block).get("value"),
            "nextId": word_int(call(endpoint, address, "nextId()", block)),
        }
        if label == "proc0":
            entry["circuitInfo1"] = call(endpoint, address, "circuitInfo(uint256)", block, 1).get("value")
            entry["circuitInfo2"] = call(endpoint, address, "circuitInfo(uint256)", block, 2).get("value")
            entry["netlist1Sha256"] = _netlist_hash(call(endpoint, address, "netlist(uint256)", block, 1))
            entry["ownerOf1"] = word_address(call(endpoint, address, "ownerOf(uint256)", block, 1))
        report["processors"][label] = entry

    # eth_getLogs availability probe only. Raw output is recorded but NOT interpreted
    # as registration evidence; no event signature is asserted.
    log_start = hex(max(0, int(block, 16) - 4))
    logs = result_or_error(rpc(endpoint, "eth_getLogs", [{
        "fromBlock": log_start, "toBlock": block, "address": FACTORY,
    }]))
    report["eventLogProbe"] = {
        "fromBlock": log_start, "toBlock": block, "address": FACTORY,
        "supported": logs.get("ok", False),
        "rawResult": logs.get("value") if logs.get("ok") else logs.get("error"),
        "interpretation": "NONE - no factory registration event signature is defined in TAP-10; "
                          "raw logs are recorded only as an availability observation.",
    }
    report["rpcCallsUsed"] = _calls
    report["rpcCallBudget"] = CALL_BUDGET
    _write(report)
    return 0


def _netlist_hash(result: dict) -> str | None:
    if not result.get("ok") or not isinstance(result.get("value"), str):
        return None
    raw = result["value"][2:]
    try:
        data = bytes.fromhex(raw)
    except ValueError:
        return None
    if len(data) < 64:
        return None
    offset = int.from_bytes(data[:32], "big")
    size = int.from_bytes(data[32:64], "big")
    if offset != 32 or size > 100_000 or len(data) < 64 + size:
        return None
    return hashlib.sha256(data[64:64 + size]).hexdigest()


def _write(report: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = report.get("headBlockHex") or "unknown"
    path = OUT_DIR / f"live_xlayer_observation_{suffix}.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {path.relative_to(OUT_DIR.parents[1])} (rpc_calls={report.get('rpcCallsUsed')})")


if __name__ == "__main__":
    sys.exit(main())
