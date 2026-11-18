"""JSON-first CLI. Reserved product operations always fail explicitly in M1-A."""

import argparse
import os
import sys
import tempfile
from enum import IntEnum
from pathlib import Path

from flip_core import __version__
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.contracts import ContractError, not_implemented, validate_contract
from flip_core.models import CONTRACTS
from pydantic import ValidationError


def import_operation(args):
    from flip_core.import_models import ImportBudget
    from flip_core.importer import ImportService
    from flip_core.models import CircuitIdentity
    from flip_core.rpc import RpcSettings

    try:
        if args.chain_id != 196:
            raise ContractError("WRONG_CHAIN", "Only integer chainId 196 is supported.")

        def read_contract(kind, path):
            with path.open("rb") as handle:
                data = handle.read(4_194_305)
            if len(data) > 4_194_304:
                raise ContractError("RESOURCE_LIMIT", "Import contract file exceeds 4 MiB.")
            return validate_contract(kind, data)

        service = ImportService(
            RpcSettings(args.rpc_url, args.timeout_ms, args.retries),
            ImportBudget(maxGates=args.gate_cap, maxDepth=args.max_depth),
        )
        if args.command == "revalidate":
            if args.identity or args.processor or args.circuit_id or args.block_number:
                raise ContractError(
                    "INVALID_INPUT", "Revalidation accepts only a manifest and settings."
                )
            result = service.revalidate(read_contract("manifest", args.manifest))
        else:
            if args.identity:
                if args.processor or args.circuit_id:
                    raise ContractError(
                        "INVALID_INPUT", "Use an identity file or processor/ID flags."
                    )
                identity = read_contract("circuit-identity", args.identity)
            else:
                identity = validate_contract(
                    "circuit-identity",
                    canonical_bytes(
                        {
                            "schemaVersion": "1.0.0",
                            "chainId": args.chain_id,
                            "processor": args.processor,
                            "circuitId": args.circuit_id,
                        }
                    ),
                )
            if not isinstance(identity, CircuitIdentity):
                raise ContractError("INVALID_INPUT", "Expected a circuit identity.")
            result = service.import_circuit(identity, args.block_number)
        if args.out:
            # Complete validated JSON only, replaced atomically in the requested directory.
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=args.out.parent, delete=False) as handle:
                    temporary = handle.name
                    handle.write(canonical_bytes(result) + b"\n")
                os.replace(temporary, args.out)
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        return result
    except (ValidationError, OSError) as exc:
        raise ContractError(
            "INVALID_INPUT", "Invalid import settings, identity, block or file."
        ) from exc


class ExitCode(IntEnum):
    OK = 0
    DIFFERENT = 1
    UNKNOWN = 2
    INVALID_INPUT = 3
    INFRASTRUCTURE = 4
    INTERNAL = 5
    NOT_IMPLEMENTED = 6
    STALE = 7
    STRUCTURALLY_REJECTED = 8


def emit(value: object) -> None:
    sys.stdout.buffer.write(canonical_bytes(value) + b"\n")


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ContractError("INVALID_INPUT", "Invalid command arguments; see flip --help.")


def main(argv: list[str] | None = None) -> int:
    parser = Parser(
        description="Flip: read-only imports, REF composition and bounded local verification."
    )
    parser.add_argument("--version", action="version", version=f"Flip {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    for operation in ("validate", "canonical", "hash"):
        command = commands.add_parser(operation, help=f"{operation} a versioned contract")
        command.add_argument("kind", choices=CONTRACTS)
        command.add_argument("file", type=Path)
    for operation in (
        "sample",
        "import",
        "inspect",
        "compose",
        "compare",
        "vectors",
        "consume",
        "preflight",
        "revalidate",
        "export",
        "verify-bundle",
    ):
        supported = operation in (
            "import",
            "inspect",
            "revalidate",
            "compose",
            "compare",
            "vectors",
            "consume",
        )
        command = commands.add_parser(
            operation,
            help="shared core operation" if supported else "reserved; returns NOT_IMPLEMENTED",
        )
        command.add_argument("--project", type=Path)
        command.add_argument("--out", type=Path)
        command.add_argument("--format", choices=["json"], default="json")
        if operation in ("import", "inspect", "revalidate"):
            command.add_argument("--processor")
            command.add_argument("--id", dest="circuit_id")
            command.add_argument("--identity", type=Path)
            command.add_argument("--manifest", type=Path)
            command.add_argument("--chain-id", type=int, default=196)
            command.add_argument("--block-number")
            command.add_argument(
                "--rpc-url", default=os.getenv("FLIP_RPC_URL", "https://rpc.xlayer.tech")
            )
            command.add_argument("--timeout-ms", type=int, default=5000)
            command.add_argument("--retries", type=int, default=1)
            command.add_argument("--gate-cap", type=int, default=2500)
            command.add_argument("--max-depth", type=int, default=64)
    try:
        args = parser.parse_args(argv)
        if args.command in ("compose", "compare", "vectors", "consume") and args.project:
            from flip_core.verification import execute

            try:
                with args.project.open("rb") as handle:
                    raw = handle.read(4_194_305)
                if len(raw) > 4_194_304:
                    raise ContractError("RESOURCE_LIMIT", "M3 request file exceeds 4 MiB.")
                result = execute(args.command, raw)
                if args.out:
                    args.out.write_bytes(canonical_bytes(result) + b"\n")
            except OSError as exc:
                raise ContractError(
                    "INVALID_INPUT", "Cannot read/write M3 request/result file."
                ) from exc
            emit(result)
            verdict = (
                result.get("report", {})
                .get("verification", {})
                .get("verdict", result.get("verdict"))
            )
            if verdict in ("DIFFERENT", "VECTORS_MISMATCH"):
                return ExitCode.DIFFERENT
            return ExitCode.UNKNOWN if verdict == "UNKNOWN" else ExitCode.OK
        if args.command in ("import", "inspect", "revalidate") and (
            args.processor or args.circuit_id or args.identity or args.manifest
        ):
            if args.command == "revalidate" and args.manifest is None:
                raise ContractError("INVALID_INPUT", "Revalidation requires --manifest.")
            if args.command != "revalidate" and args.manifest:
                raise ContractError("INVALID_INPUT", "Use revalidate for manifest inputs.")
            result = import_operation(args)
            emit(result)
            return ExitCode.STALE if result.integrity.freshness == "STALE" else ExitCode.OK
        if args.command not in ("validate", "canonical", "hash"):
            emit(not_implemented())
            return ExitCode.NOT_IMPLEMENTED
        try:
            data = args.file.read_bytes()
        except OSError as exc:
            raise ContractError("INVALID_INPUT", "Cannot read input file.") from exc
        model = validate_contract(args.kind, data)
        if args.command == "hash":
            emit({"profile": "flip-json-v1", "hash": content_hash(model)})
        else:
            emit(model)
        return ExitCode.OK
    except ContractError as exc:
        emit(exc.envelope())
        if exc.code == "RPC_UNAVAILABLE":
            return ExitCode.INFRASTRUCTURE
        if exc.code in ("RESOURCE_LIMIT", "REF_DEPTH_EXCEEDED"):
            return ExitCode.UNKNOWN
        if exc.code == "IMPLEMENTATION_CHANGED":
            return ExitCode.STALE
        return ExitCode.INVALID_INPUT


if __name__ == "__main__":
    raise SystemExit(main())
