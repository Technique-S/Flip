"""Deterministically emit M4.5-2L discovery fixtures and a SHA-256 manifest.

All generated cases are explicitly SYNTHETIC. Real observed values are confined to
observations/ and seeds/ with distinct provenance labels. No timestamps or random
values are used, so re-running this script reproduces byte-identical case files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases"
SEEDS = ROOT / "seeds"
OBS = ROOT / "observations"
SCHEMA = "1.0.0"
FACTORY = "0x1f09daefa827f02cbb40967cc91b259763760761"
P_A = "0x1111111111111111111111111111111111111111"
P_B = "0x2222222222222222222222222222222222222222"
P_C = "0x3333333333333333333333333333333333333333"
IMPL_A = "0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
IMPL_B = "0xbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
BEACON_A = "0xcccccccccccccccccccccccccccccccccccccccc"
H_A = "0x" + "11" * 32
H_B = "0x" + "22" * 32
H_C = "0x" + "33" * 32
BLK_A = 1000
BLK_B = 1001


def addr_word(address: str) -> str:
    return "0x" + "0" * 24 + address[2:].lower()


def uint_word(value: int) -> str:
    return "0x" + value.to_bytes(32, "big").hex()


def call(seq: int, to: str, sig: str, args: list[int] | None = None,
         response: str | None = None, error: str | None = None, block: int = BLK_A) -> dict:
    entry = {"seq": seq, "method": "eth_call", "to": to, "selector": sig,
             "args": args or [], "block": block}
    if error is not None:
        entry["response"] = {"error": error}
    else:
        entry["response"] = {"result": response if response is not None else uint_word(0)}
    return entry


def base(case_id: str, title: str, description: str) -> dict:
    return {
        "schemaVersion": SCHEMA,
        "caseId": case_id,
        "title": title,
        "provenance": "SYNTHETIC",
        "provenanceNote": "Mocked RPC and catalog outcomes; not a live chain observation.",
        "description": description,
        "chainId": 196,
        "factory": FACTORY,
        "authorityBoundary": (
            "No fixture grants transaction authority. User labels, favorites and discovered "
            "records are advisory only; executable status requires fresh trusted-importer validation."
        ),
    }


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def build_cases() -> dict[str, dict]:
    cases: dict[str, dict] = {}

    # C01 — multiple processors
    c = base("M45-2L-C01", "Multiple processors discovered from a single factory",
             "cpuCount=3; cpuAt(0..2) returns three distinct registered processors.")
    c["rpcScript"] = [
        call(1, FACTORY, "0xa94da8a7", response=uint_word(3)),
        call(2, FACTORY, "0x4bc7cbbd", [0], addr_word(P_A)),
        call(3, FACTORY, "0x4bc7cbbd", [1], addr_word(P_B)),
        call(4, FACTORY, "0x4bc7cbbd", [2], addr_word(P_C)),
        call(5, FACTORY, "0x5f5a364f", response=uint_word(1)),
    ]
    c["expected"] = {
        "processorRecords": [
            {"processorNumber": 0, "address": P_A, "registration": "ENUMERATED"},
            {"processorNumber": 1, "address": P_B, "registration": "ENUMERATED"},
            {"processorNumber": 2, "address": P_C, "registration": "ENUMERATED"},
        ],
        "search": {"processorAddress": P_B, "resultCount": 1},
        "discoveryComplete": True,
    }
    c["assertions"] = [
        "Processor numbers are append-only indices from cpuAt and are per-chain/factory.",
        "Duplicate addresses across processors are collapsed by (chainId, factory, address).",
    ]
    cases["01_multiple_processors.json"] = c

    # C02 — multiple circuit IDs
    c = base("M45-2L-C02", "Multiple circuit IDs under one processor",
             "nextId=5; circuitInfo/ownerOf succeed for IDs 1,2,3,4.")
    c["rpcScript"] = [
        call(1, P_A, "0x61b8ce8c", response=uint_word(5)),
        call(2, P_A, "0x084d60f1", [1], uint_word(2) + uint_word(1) + uint_word(0) + uint_word(4)),
        call(3, P_A, "0x084d60f1", [2], uint_word(2) + uint_word(1) + uint_word(0) + uint_word(3)),
        call(4, P_A, "0x084d60f1", [3], uint_word(3) + uint_word(2) + uint_word(0) + uint_word(6)),
        call(5, P_A, "0x084d60f1", [4], uint_word(1) + uint_word(1) + uint_word(1) + uint_word(2)),
        call(6, P_A, "0x6352211e", [1], addr_word(P_B)),
    ]
    c["expected"] = {
        "circuitRecords": [
            {"circuitId": "1", "nIn": 2, "nOut": 1, "nState": 0, "gateCount": 4},
            {"circuitId": "2", "nIn": 2, "nOut": 1, "nState": 0, "gateCount": 3},
            {"circuitId": "3", "nIn": 3, "nOut": 2, "nState": 0, "gateCount": 6},
            {"circuitId": "4", "nIn": 1, "nOut": 1, "nState": 1, "gateCount": 2},
        ],
        "search": {"processorAddress": P_A, "circuitId": "3", "resultCount": 1},
        "existenceEvidence": "ownerOf(1) succeeded; circuitInfo decoded at pinned block",
    }
    c["assertions"] = [
        "ID 0 is never emitted (valid circuit IDs start at 1).",
        "Stateful circuits are labeled nState>0 and never treated as stateless-equivalent candidates.",
    ]
    cases["02_multiple_circuit_ids.json"] = c

    # C03 — missing and noncontiguous IDs
    c = base("M45-2L-C03", "Missing and noncontiguous circuit IDs below nextId",
             "nextId=8 but circuitInfo reverts for IDs 3 and 6; scan must skip, not assume contiguity.")
    c["rpcScript"] = [
        call(1, P_A, "0x61b8ce8c", response=uint_word(8)),
        call(2, P_A, "0x084d60f1", [1], uint_word(2) + uint_word(1) + uint_word(0) + uint_word(4)),
        call(3, P_A, "0x084d60f1", [2], uint_word(2) + uint_word(1) + uint_word(0) + uint_word(3)),
        call(4, P_A, "0x084d60f1", [3], error="execution reverted: no circuit"),
        call(5, P_A, "0x084d60f1", [4], uint_word(1) + uint_word(1) + uint_word(0) + uint_word(2)),
        call(6, P_A, "0x084d60f1", [5], uint_word(1) + uint_word(1) + uint_word(0) + uint_word(2)),
        call(7, P_A, "0x084d60f1", [6], error="execution reverted: no circuit"),
        call(8, P_A, "0x084d60f1", [7], uint_word(2) + uint_word(2) + uint_word(0) + uint_word(5)),
    ]
    c["expected"] = {
        "existingIds": ["1", "2", "4", "5", "7"],
        "missingIds": ["3", "6"],
        "nextId": 8,
        "scanStatus": "COMPLETE_WITH_GAPS",
        "catalogNeverClaims": "contiguous 1..7",
    }
    c["assertions"] = [
        "nextId is an exclusive upper bound, not proof that every lower ID exists.",
        "A reverted existence probe is recorded as MISSING, not as a transport failure.",
    ]
    cases["03_missing_noncontiguous_ids.json"] = c

    # C04 — pagination
    c = base("M45-2L-C04", "Bounded pagination of processor and circuit enumeration",
             "cpuCount=7; page size 3; scanner stops after a hard page cap of 3 pages.")
    c["rpcScript"] = [
        call(1, FACTORY, "0xa94da8a7", response=uint_word(7)),
        *[call(2 + i, FACTORY, "0x4bc7cbbd", [i], addr_word(P_A))
          for i in range(7)],
        call(9, P_A, "0x61b8ce8c", response=uint_word(200)),
    ]
    c["expected"] = {
        "pageSize": 3,
        "pagesEmitted": 3,
        "indicesVisited": [0, 1, 2, 3, 4, 5, 6],
        "cursorAfterPage3": {"processorIndex": 7, "circuitId": 51},
        "discoveryStatus": "PARTIAL_BOUNDED",
        "circuitScanCap": 50,
        "assertNoUnboundedScan": True,
    }
    c["assertions"] = [
        "A page cap produces PARTIAL_BOUNDED, never a false COMPLETE.",
        "Cursor and visited-block identity allow resuming without duplicate records.",
    ]
    cases["04_pagination.json"] = c

    # C05 — RPC outages
    c = base("M45-2L-C05", "RPC outage during discovery",
             "eth_call times out mid-scan; discovery stops with UNKNOWN and retains prior snapshot.")
    c["rpcScript"] = [
        call(1, FACTORY, "0xa94da8a7", response=uint_word(3)),
        call(2, FACTORY, "0x4bc7cbbd", [0], addr_word(P_A)),
        call(3, FACTORY, "0x4bc7cbbd", [1], error="transport: TimeoutError after 15s"),
        call(4, FACTORY, "0x4bc7cbbd", [2], error="transport: TimeoutError after 15s"),
    ]
    c["expected"] = {
        "discoveryStatus": "UNKNOWN",
        "retainPriorSnapshot": True,
        "partialResultsLabeled": "INCOMPLETE",
        "favoritesUnchanged": True,
        "retryPolicy": "bounded_backoff_then_stop",
    }
    c["assertions"] = [
        "Timeout is never silently converted to 'processor absent'.",
        "Outage does not delete favorites, recents, or the last verified snapshot.",
    ]
    cases["05_rpc_outages.json"] = c

    # C06 — rate limits
    c = base("M45-2L-C06", "Rate limiting (HTTP 429) with bounded retry",
             "Provider returns 429; scanner applies bounded backoff and stops after max retries.")
    c["rpcScript"] = [
        call(1, FACTORY, "0xa94da8a7", error="http 429: rate limited"),
        call(2, FACTORY, "0xa94da8a7", error="http 429: rate limited"),
        call(3, FACTORY, "0xa94da8a7", response=uint_word(1)),
        call(4, FACTORY, "0x4bc7cbbd", [0], addr_word(P_A)),
    ]
    c["expected"] = {
        "maxRetries": 2,
        "discoveryStatus": "COMPLETE_AFTER_RETRY",
        "throttleEvents": 2,
        "callsUsed": 4,
        "backoffBounded": True,
    }
    c["assertions"] = [
        "429 responses count against the per-session RPC budget.",
        "Retry never reuses a stale block tag across a reorg boundary.",
    ]
    cases["06_rate_limits.json"] = c

    # C07 — changed factory implementation
    c = base("M45-2L-C07", "Factory implementation changed between snapshots",
             "cpuCount enumeration succeeds but factory ERC-1967 implementation and code hash differ.")
    c["baselineSnapshot"] = {
        "blockNumber": BLK_A, "factoryImplementation": IMPL_A,
        "factoryImplementationCodeHash": H_A, "isSealed": 0,
    }
    c["rpcScript"] = [
        call(1, FACTORY, "0xa94da8a7", response=uint_word(2), block=BLK_B),
        call(2, FACTORY, "0x4bc7cbbd", [0], addr_word(P_A), block=BLK_B),
        call(3, FACTORY, "0x4bc7cbbd", [1], addr_word(P_B), block=BLK_B),
    ]
    c["observedEnvironmentChange"] = {
        "blockNumber": BLK_B, "factoryImplementation": IMPL_B,
        "factoryImplementationCodeHash": H_B, "isSealed": 0,
    }
    c["expected"] = {
        "discoveryStatus": "ENVIRONMENT_CHANGED",
        "existingCatalogEntries": "STALE",
        "favorites": "PRESERVED_AS_USER_DATA",
        "compositionAllowed": False,
        "revalidationRequired": True,
    }
    c["assertions"] = [
        "Proxy address alone is not an environment identity.",
        "A verified address is not permanent proof of unchanged implementation.",
    ]
    cases["07_factory_implementation_changed.json"] = c

    # C08 — changed processor implementation
    c = base("M45-2L-C08", "Processor beacon implementation changed",
             "Processor address and proxy code hash are identical; beacon implementation code hash changed.")
    c["baselineSnapshot"] = {
        "blockNumber": BLK_A, "processor": P_A,
        "processorProxyCodeHash": H_A, "beaconImplementationCodeHash": H_B,
    }
    c["rpcScript"] = [
        call(1, P_A, "0x61b8ce8c", response=uint_word(4), block=BLK_B),
        call(2, P_A, "0x084d60f1", [1], uint_word(2) + uint_word(1) + uint_word(0) + uint_word(4), block=BLK_B),
    ]
    c["observedEnvironmentChange"] = {
        "blockNumber": BLK_B, "processor": P_A,
        "processorProxyCodeHash": H_A, "beaconImplementationCodeHash": H_C,
    }
    c["expected"] = {
        "discoveryStatus": "ENVIRONMENT_CHANGED",
        "circuitRecords": "STALE",
        "compositionAllowed": False,
        "note": "processor proxy bytecode is a constant beacon proxy and is insufficient for identity",
    }
    c["assertions"] = [
        "Beacon implementation code hash is part of the environment key.",
        "Cached netlists are not accepted as current after beacon change.",
    ]
    cases["08_processor_implementation_changed.json"] = c

    # C09 — chain reorganization
    c = base("M45-2L-C09", "Chain reorganization invalidates a pinned snapshot",
             "Snapshot at block 1000/hash H_A is re-read at the same height with a different canonical hash.")
    c["rpcScript"] = [
        call(1, FACTORY, "0xa94da8a7", response=uint_word(2), block=BLK_A),
        {"seq": 2, "method": "eth_getBlockByNumber", "params": [hex(BLK_A), False],
         "response": {"hash": H_A}},
        {"seq": 3, "method": "eth_getBlockByNumber", "params": [hex(BLK_A), False],
         "response": {"hash": H_B}},
        call(4, FACTORY, "0xa94da8a7", response=uint_word(2), block=BLK_A),
    ]
    c["expected"] = {
        "reorgDetected": True,
        "snapshotInvalidated": True,
        "affectedRecords": "REORGED",
        "rescanFrom": BLK_A,
        "favorites": "PRESERVED_BUT_FLAGGED",
        "compositionAllowed": False,
    }
    c["assertions"] = [
        "Block hash, not just block number, is part of snapshot identity.",
        "Event logs alone cannot drive reorg recovery; state is re-read at the new canonical block.",
    ]
    cases["09_chain_reorganization.json"] = c

    # C10 — duplicate discovery records
    c = base("M45-2L-C10", "Duplicate discovery records collapse to one identity",
             "The same processor/circuit appears via factory enumeration, a known seed and a user import.")
    c["rpcScript"] = [
        call(1, FACTORY, "0x4bc7cbbd", [0], addr_word(P_A)),
        call(2, P_A, "0x61b8ce8c", response=uint_word(3)),
        call(3, P_A, "0x084d60f1", [1], uint_word(2) + uint_word(1) + uint_word(0) + uint_word(4)),
    ]
    c["inputRecords"] = [
        {"source": "FACTORY_ENUMERATION", "chainId": 196, "processor": P_A, "circuitId": "1"},
        {"source": "KNOWN_SEED", "chainId": 196, "processor": P_A.lower(), "circuitId": "1"},
        {"source": "USER_IMPORT", "chainId": 196, "processor": P_A.upper(), "circuitId": "1"},
    ]
    c["expected"] = {
        "catalogRecordCount": 1,
        "canonicalKey": "196:0x1f09daefa827f02cbb40967cc91b259763760761:0x1111111111111111111111111111111111111111:1",
        "addressNormalization": "lowercase",
        "provenanceSources": ["FACTORY_ENUMERATION", "KNOWN_SEED", "USER_IMPORT"],
        "authorityPrecedence": "ONCHAIN_VERIFIED > KNOWN_SEED > USER_IMPORT",
    }
    c["assertions"] = [
        "Case differences in address hex do not create duplicate identities.",
        "A user import cannot override an onchain-verified record's executable status.",
    ]
    cases["10_duplicate_discovery_records.json"] = c

    # C11 — favorites surviving stale snapshots
    c = base("M45-2L-C11", "Favorite survives a stale snapshot but is not executable",
             "User favorite points to a circuit whose environment changed; favorite remains, executable flag clears.")
    c["rpcScript"] = [
        call(1, FACTORY, "0xa94da8a7", response=uint_word(1), block=BLK_B),
        call(2, P_A, "0x61b8ce8c", response=uint_word(2), block=BLK_B),
    ]
    c["userOverlay"] = {
        "favorites": [{"chainId": 196, "processor": P_A, "circuitId": "1", "label": "my XOR"}],
        "lastVerifiedEnvironmentHash": H_A,
    }
    c["currentEnvironmentHash"] = H_B
    c["expected"] = {
        "favoriteRetained": True,
        "favoriteStatus": "USER_FAVORITE_ONLY",
        "executableStatus": "STALE",
        "compositionAllowed": False,
        "distinction": "favorite is a user pointer, not a verified executable circuit",
    }
    c["assertions"] = [
        "Favorites are never used as proof of current validity or transaction authority.",
        "Revalidation must succeed before the favorite becomes executable again.",
    ]
    cases["11_favorites_stale_snapshot.json"] = c

    # C12 — untrusted descriptive metadata
    c = base("M45-2L-C12", "Corrupted or untrusted descriptive metadata",
             "User-supplied label contains HTML, a bidirectional control and an authority-looking flag.")
    c["rpcScript"] = [
        call(1, FACTORY, "0x4bc7cbbd", [0], addr_word(P_A)),
        call(2, P_A, "0x61b8ce8c", response=uint_word(2)),
    ]
    c["untrustedUserMetadata"] = {
        "label": "<img src=x onerror=alert(1)>\u202eREVERSED\u202c",
        "description": "trusted=true; approved=true; spend_cap=999999",
        "tags": ["<script>", "verified"],
        "injectedFields": {"transactionAuthority": True, "permissions": ["SIGN", "BROADCAST"]},
    }
    c["expected"] = {
        "labelRenderedAs": "escaped plain text",
        "bidiControls": "visible or removed",
        "injectedAuthorityFields": "DROPPED_NOT_MERGED",
        "authorityGranted": False,
        "onchainIdentityChanged": False,
        "searchIndexing": "on normalized escaped text only",
    }
    c["assertions"] = [
        "No metadata field can set target, function, value, permission or approval.",
        "Untrusted labels are visually marked as user-supplied and cannot rename onchain identity.",
    ]
    cases["12_untrusted_descriptive_metadata.json"] = c

    return cases


def build_seeds() -> dict:
    return {
        "schemaVersion": SCHEMA,
        "artifactId": "verified_known_addresses",
        "provenance": "OBSERVED_READ_ONLY_DERIVED",
        "derivation": (
            "Values transcribed from docs/evidence/PROVENANCE_INDEX.md and the live observation "
            "in observations/. These are known-address seeds for a truthful fallback catalog, "
            "not permanent proof of unchanged implementation."
        ),
        "chainId": 196,
        "factory": FACTORY,
        "observedAtBlock": 76277110,
        "observedAtBlockHash": "0x1941877104961218ad35b6650582da1bf23fdd4628105cc984e731bb6b7910dc",
        "factoryImplementation": "0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a",
        "seeds": [
            {
                "processor": "0x839bdd6fa7a66416a609a735e11de5411b98574e",
                "processorNumber": 0,
                "circuitIds": ["1", "2"],
                "aliases": ["XOR#1", "NAND#2"],
                "aliasProvenance": "LOCAL_IDENTIFIER_NOT_VERIFIED_DESCRIPTION",
                "nextId": 104,
                "netlistSha256Circuit1": "d3f8f3a8316a49023a82436e92607f77a51e7f1b96b614b3d71417372f3f6a9f",
            },
            {
                "processor": "0x0565ea48ca41ae559d8d491dbb0a9ec945db551b",
                "processorNumber": 1,
                "circuitIds": [],
                "aliases": ["My4004"],
                "aliasProvenance": "ONCHAIN_NAME_DISPLAY_ONLY_NOT_IDENTITY",
                "nextId": 100,
            },
        ],
        "authorityNote": "Seed membership is a discovery hint only; executable status requires fresh importer validation.",
    }


def main() -> None:
    cases = build_cases()
    for name, payload in cases.items():
        write_json(CASES / name, payload)
    write_json(SEEDS / "verified_known_addresses.json", build_seeds())

    manifest_items = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()
                       and p.name != "SHA256SUMS.manifest.json"
                       and "__pycache__" not in p.parts and p.suffix != ".pyc"):
        data = path.read_bytes()
        manifest_items.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    manifest = {
        "schemaVersion": SCHEMA,
        "manifestType": "SHA256SUMS",
        "note": "SHA-256 over all committed fixture bytes. Re-run generators then verify_fixtures.py.",
        "files": manifest_items,
    }
    (ROOT / "SHA256SUMS.manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(f"cases={len(cases)} files={len(manifest_items)}")


if __name__ == "__main__":
    main()
