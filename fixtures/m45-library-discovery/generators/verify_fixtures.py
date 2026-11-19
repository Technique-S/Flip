"""Deterministic verification of M4.5-2L fixtures: manifest, schema and provenance."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_KEYS = {
    "schemaVersion", "caseId", "title", "provenance", "description",
    "chainId", "factory", "rpcScript", "expected", "assertions", "authorityBoundary",
}


def main() -> int:
    errors: list[str] = []
    manifest = json.loads((ROOT / "SHA256SUMS.manifest.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = ROOT / item["path"]
        if not path.exists():
            errors.append(f"missing {item['path']}")
            continue
        data = path.read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            errors.append(f"hash/size mismatch {item['path']}")

    case_files = sorted((ROOT / "cases").glob("*.json"))
    ids: set[str] = set()
    for path in case_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        missing = REQUIRED_KEYS - set(payload)
        if missing:
            errors.append(f"{path.name}: missing keys {sorted(missing)}")
        if payload.get("provenance") != "SYNTHETIC":
            errors.append(f"{path.name}: synthetic case not labeled SYNTHETIC")
        if payload.get("caseId") in ids:
            errors.append(f"{path.name}: duplicate caseId {payload.get('caseId')}")
        ids.add(payload.get("caseId"))
        if payload.get("chainId") != 196:
            errors.append(f"{path.name}: chainId must be 196")
        if not payload.get("rpcScript"):
            errors.append(f"{path.name}: empty rpcScript")
        if not payload.get("assertions"):
            errors.append(f"{path.name}: no assertions")

    seeds = json.loads((ROOT / "seeds" / "verified_known_addresses.json").read_text(encoding="utf-8"))
    if seeds.get("provenance") != "OBSERVED_READ_ONLY_DERIVED":
        errors.append("seeds: provenance label changed")
    observations = list((ROOT / "observations").glob("*.json"))
    if not observations:
        errors.append("no live observation file")
    for path in observations:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("chainId") != 196 or not payload.get("blockHash"):
            errors.append(f"{path.name}: incomplete live observation")
        if payload.get("signingOrBroadcast") is not False:
            errors.append(f"{path.name}: signingOrBroadcast must be false")
        if payload.get("stateOverrides") is not False:
            errors.append(f"{path.name}: stateOverrides must be false")

    print(json.dumps({
        "caseFiles": len(case_files),
        "caseIds": sorted(ids),
        "seedFiles": 1,
        "observationFiles": len(observations),
        "manifestFiles": len(manifest["files"]),
        "errors": errors,
        "result": "PASS" if not errors else "FAIL",
    }, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
