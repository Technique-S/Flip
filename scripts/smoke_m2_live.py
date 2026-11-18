"""Opt-in live read-only smoke. Never executed by deterministic CI."""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from flip_core.canonical import canonical_bytes
from flip_core.contracts import ContractError
from flip_core.importer import ImportService
from flip_core.models import CircuitIdentity, Integrity
from flip_core.rpc import RpcSettings

PROCESSOR = "0x839bdd6fa7a66416a609a735e11de5411b98574e"
EXPECTED = {
    "1": "0xd3f8f3a8316a49023a82436e92607f77a51e7f1b96b614b3d71417372f3f6a9f",
    "2": "0x91c81eb018919169c97a8b7e10f4ab9bb2792960f53c0f4de3e3d2681939fd8e",
    "4": "0x0d6225ff61bc8e990c757c9152a136ab580b5630c39317f81b9e05edce8070ad",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rpc-url", default="https://rpc.xlayer.tech")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    service = ImportService(RpcSettings(args.rpc_url, timeout_ms=10_000))
    result = {
        "generatedUTC": datetime.now(UTC).isoformat(),
        "scope": "Historical capture of an opt-in single-RPC import; no proof or publication.",
        "cases": [],
        "status": "MATCH",
    }
    pinned = None
    try:
        for cid, expected in EXPECTED.items():
            imported = service.import_circuit(
                CircuitIdentity(
                    schemaVersion="1.0.0", chainId=196, processor=PROCESSOR, circuitId=cid
                ),
                block_number=pinned,
            )
            pinned = imported.manifest.block.number
            actual = imported.manifest.root.netlistHash
            if actual != expected:
                result["status"] = "LIVE_DISCREPANCY"
            # Archival captures are historical even when first observed at the head.
            archived = imported.model_copy(
                update={
                    "integrity": Integrity(
                        freshness="HISTORICAL", checkedBlock=imported.manifest.block
                    )
                }
            )
            result["cases"].append(
                {
                    "circuitId": cid,
                    "expectedNetlistHash": expected,
                    "matchesRecordedHash": actual == expected,
                    "artifact": archived.model_dump(mode="json"),
                }
            )
    except ContractError as exc:
        result["status"] = "RPC_OR_IMPORT_FAILURE"
        result["error"] = exc.envelope().model_dump(mode="json")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical_bytes(result) + b"\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "capturedCircuits": len(result["cases"]),
                "path": str(args.out),
            }
        )
    )
    return 0 if result["status"] == "MATCH" else 1


if __name__ == "__main__":
    raise SystemExit(main())
