"""Opt-in, bounded live READS. Never imported by deterministic tests or CI."""

import argparse
from pathlib import Path
from urllib.parse import urlsplit

from flip_core.canonical import canonical_bytes
from flip_core.import_models import ImportBudget
from flip_core.library import LibraryService
from flip_core.library_models import LibraryIdentity, LibraryRequest
from flip_core.rpc import RpcSettings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    settings = RpcSettings.from_environment()
    service = LibraryService(settings, ImportBudget(maxRequests=64, deadlineMs=60_000))
    processors = service.execute(LibraryRequest(operation="discover", limit=1))
    record = dict(
        classification="OBSERVED_READ_ONLY",
        signingOrBroadcast=False,
        endpointHost=urlsplit(settings.endpoint).hostname,
        processors=processors.model_dump(mode="json"),
    )
    if processors.results and processors.status in ("COMPLETE", "PARTIAL_BOUNDED"):
        identity = LibraryIdentity(processor=processors.results[0].identity.processor)
        circuits = service.execute(LibraryRequest(operation="circuits", identity=identity, limit=2))
        record["circuits"] = circuits.model_dump(mode="json")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical_bytes(record) + b"\n")
    print(processors.status, processors.errorCode, processors.rpcCallsUsed)


if __name__ == "__main__":
    main()
