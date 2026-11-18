"""Single validation boundary shared by the CLI and API."""

from dataclasses import dataclass

from pydantic import ValidationError

from flip_core.canonical import load_json
from flip_core.models import CONTRACTS, Contract, ErrorDetail, ErrorEnvelope, Reason


@dataclass
class ContractError(ValueError):
    code: Reason
    message: str

    def envelope(self) -> ErrorEnvelope:
        return ErrorEnvelope(
            schemaVersion="1.0.0", error=ErrorDetail(code=self.code, message=self.message)
        )


def validate_contract(kind: str, data: str | bytes) -> Contract:
    if kind not in CONTRACTS:
        raise ContractError("INVALID_INPUT", "Unknown contract name.")
    try:
        value = load_json(data)
        return CONTRACTS[kind].model_validate(value)
    except ValidationError as exc:
        errors = exc.errors()
        if any(
            e["loc"][-1:] == ("schemaVersion",) and e["type"] == "literal_error" for e in errors
        ):
            raise ContractError(
                "UNSUPPORTED_SCHEMA_VERSION", "Only schemaVersion 1.0.0 is supported."
            ) from exc
        if any(e["loc"][-1:] == ("chainId",) and e["type"] != "missing" for e in errors):
            raise ContractError("WRONG_CHAIN", "Only integer chainId 196 is supported.") from exc
        raise ContractError("INVALID_INPUT", "Payload violates the contract.") from exc
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        raise ContractError("INVALID_INPUT", "Invalid canonical JSON input.") from exc


def not_implemented() -> ErrorEnvelope:
    return ErrorEnvelope(
        schemaVersion="1.0.0",
        error=ErrorDetail(
            code="NOT_IMPLEMENTED",
            message="This operation is not implemented in M1-A. No verification was performed.",
        ),
    )
