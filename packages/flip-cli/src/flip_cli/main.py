"""JSON-first CLI. Reserved product operations always fail explicitly in M1-A."""

import argparse
import sys
from enum import IntEnum
from pathlib import Path

from flip_core import __version__
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.contracts import ContractError, not_implemented, validate_contract
from flip_core.models import CONTRACTS


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
    parser = Parser(description="Flip M1-A contracts only; no RPC, solver or publication.")
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
        "preflight",
        "revalidate",
        "export",
        "verify-bundle",
    ):
        command = commands.add_parser(operation, help="reserved; returns NOT_IMPLEMENTED")
        command.add_argument("--project", type=Path)
        command.add_argument("--out", type=Path)
        command.add_argument("--format", choices=["json"], default="json")
    try:
        args = parser.parse_args(argv)
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
        return ExitCode.INVALID_INPUT


if __name__ == "__main__":
    raise SystemExit(main())
