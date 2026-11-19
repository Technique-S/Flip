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


def write_result(path, result):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(canonical_bytes(result) + b"\n")
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


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
            write_result(args.out, result)
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
    debugging = commands.add_parser(
        "debug", help="Trace a replayed mismatch; test an explicit candidate revision"
    )
    debugging.add_argument("--request", type=Path, required=True)
    debugging.add_argument("--out", type=Path)
    library = commands.add_parser("library", help="Read-only processor/circuit catalog operations")
    library.add_argument(
        "--request", type=Path, required=True, help="Versioned LIBRARY_REQUEST JSON"
    )
    library.add_argument(
        "--catalog", type=Path, help="Local catalog; atomically updated after operation"
    )
    library.add_argument("--out", type=Path)
    for operation in ("validate", "canonical", "hash"):
        command = commands.add_parser(operation, help=f"{operation} a versioned contract")
        command.add_argument("kind", choices=CONTRACTS)
        command.add_argument("file", type=Path)
    operations = {
        "sample": "Open the historical half-adder or swapped-output project",
        "import": "Read and pin an X Layer circuit and its dependency closure",
        "inspect": "Inspect an X Layer circuit by processor address and ID",
        "new-project": "Wrap an imported stateless circuit as a candidate and baseline",
        "compose": "Build deterministic TAP-02 bytes from a pinned project",
        "compare": "Run bounded local stateless verification and replay differences",
        "vectors": "Evaluate user-supplied input/output rows",
        "consume": "Replay an M3 report against externally pinned identities",
        "preflight": "Probe current X Layer structure with a read-only call",
        "revalidate": "Re-read a manifest and report changed dependencies",
        "export": "Run comparison and save portable evidence",
        "inspect-evidence": "Inspect recorded evidence claims without trusting them",
        "verify-bundle": "Recompute evidence against a separately selected project",
    }
    for operation, help_text in operations.items():
        command = commands.add_parser(operation, help=help_text, description=help_text)
        if operation == "new-project":
            command.add_argument("--source", type=Path, help="Validated circuit import JSON")
        if operation == "sample":
            command.add_argument(
                "variant",
                nargs="?",
                choices=["half-adder", "swapped"],
                help="Historical half-adder or its swapped-output mutation",
            )
        if operation in ("inspect-evidence", "verify-bundle"):
            command.add_argument("--bundle", type=Path, help="Evidence to replay against --project")
        if operation == "export":
            command.add_argument(
                "--observe-chain",
                action="store_true",
                help="Attach a fresh read-only structural observation",
            )
        command.add_argument(
            "--project", type=Path, help="Execution request with project and pinned source imports"
        )
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
        if args.command == "debug":
            from flip_core.debugging import execute as debug_execute

            try:
                with args.request.open("rb") as handle:
                    raw = handle.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise ContractError("RESOURCE_LIMIT", "Diagnostic input exceeds 1 MiB.")
                result = debug_execute(raw)
                if args.out:
                    write_result(args.out, result)
            except OSError as exc:
                raise ContractError(
                    "INVALID_INPUT", "Cannot read or save diagnostic file."
                ) from exc
            emit(result)
            if result.classification == "UNKNOWN":
                return ExitCode.UNKNOWN
            if result.correction is not None:
                return (
                    ExitCode.OK
                    if result.correction.classification == "VERIFIED_CORRECTION"
                    else ExitCode.UNKNOWN
                )
            return (
                ExitCode.DIFFERENT
                if result.classification == "VERIFIED_DIFFERENCE"
                else ExitCode.OK
            )
        if args.command == "library":
            from flip_core.canonical import load_json
            from flip_core.library import LibraryService
            from flip_core.library_models import Catalog
            from flip_core.library_models_v1 import Catalog as CatalogV1
            from flip_core.library_models_v1 import LibraryRequest as RequestV1
            from flip_core.library_protocol import parse_library_request
            from flip_core.rpc import RpcSettings

            def library_file(path):
                with path.open("rb") as handle:
                    raw = handle.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise ContractError("RESOURCE_LIMIT", "Library input exceeds 1 MiB.")
                return load_json(raw)

            try:
                model = parse_library_request(library_file(args.request))
                if args.catalog and args.catalog.exists():
                    catalog_type = CatalogV1 if isinstance(model, RequestV1) else Catalog
                    model.catalog = catalog_type.model_validate(library_file(args.catalog))
                result = LibraryService(RpcSettings.from_environment()).execute(model)
                if args.catalog:
                    write_result(args.catalog, result.catalog)
                if args.out:
                    write_result(args.out, result)
            except (OSError, ValueError, TypeError, RecursionError) as exc:
                if isinstance(exc, ContractError):
                    raise
                raise ContractError(
                    "INVALID_INPUT", "Invalid library contract or local file."
                ) from exc
            emit(result)
            if result.status in ("UNKNOWN", "ABORTED", "VERIFICATION_FAILED"):
                return ExitCode.UNKNOWN
            if result.status in ("ENVIRONMENT_CHANGED", "REORGED"):
                return ExitCode.STALE
            return ExitCode.OK
        if (
            (args.command == "inspect-evidence" and args.bundle)
            or (args.command == "new-project" and args.source)
            or (args.command == "sample" and args.variant)
            or (args.command in ("export", "verify-bundle", "preflight") and args.project)
        ):
            from flip_core.canonical import load_json
            from flip_core.workflow import VERSION, inspect_evidence, product, sample

            def read_file(path):
                if path is None:
                    raise ContractError(
                        "INVALID_INPUT", "Evidence replay requires --bundle and --project."
                    )
                with path.open("rb") as handle:
                    raw = handle.read(1_048_577)
                if len(raw) > 1_048_576:
                    raise ContractError("RESOURCE_LIMIT", "Product input exceeds 1 MiB.")
                return load_json(raw)

            try:
                if args.command == "inspect-evidence":
                    result = inspect_evidence(read_file(args.bundle))
                elif args.command == "new-project":
                    result = product(
                        "new-project",
                        dict(
                            kind="PRODUCT_REQUEST",
                            schemaVersion=VERSION,
                            source=read_file(args.source),
                        ),
                    )
                elif args.command == "sample":
                    result = sample(args.variant)
                else:
                    body = dict(
                        schemaVersion=VERSION,
                        kind="PRODUCT_REQUEST",
                        executionRequest=read_file(args.project),
                    )
                    if args.command == "verify-bundle":
                        body["bundle"] = read_file(args.bundle)
                    if args.command == "export":
                        body["observeChain"] = args.observe_chain
                    result = product(args.command, body)
                if args.out:
                    write_result(args.out, result)
            except ContractError:
                raise
            except (OSError, ValueError, RecursionError) as exc:
                raise ContractError(
                    "INVALID_INPUT", "Invalid product input or output file."
                ) from exc
            emit(result)
            outcome = (
                result.get("comparison", result)
                .get("report", {})
                .get("verification", {})
                .get("verdict")
            )
            if outcome == "DIFFERENT":
                return ExitCode.DIFFERENT
            if result.get("status") == "REJECTED":
                return ExitCode.STRUCTURALLY_REJECTED
            return ExitCode.UNKNOWN if "UNKNOWN" in (outcome, result.get("status")) else ExitCode.OK
        if args.command in ("compose", "compare", "vectors", "consume") and args.project:
            from flip_core.verification import execute

            try:
                with args.project.open("rb") as handle:
                    raw = handle.read(4_194_305)
                if len(raw) > 4_194_304:
                    raise ContractError("RESOURCE_LIMIT", "M3 request file exceeds 4 MiB.")
                result = execute(args.command, raw)
                if args.out:
                    write_result(args.out, result)
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
    except KeyboardInterrupt:
        emit(
            ContractError(
                "RESOURCE_LIMIT", "Operation aborted; no partial catalog saved."
            ).envelope()
        )
        return ExitCode.UNKNOWN
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
