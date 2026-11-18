"""Local contract API. Product routes have no execution implementation."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from flip_core.canonical import canonical_bytes
from flip_core.contracts import ContractError, not_implemented, validate_contract
from flip_core.models import ErrorEnvelope

app = FastAPI(title="Flip M1-A contracts", version="0.1.0")
MAX_BODY_BYTES = 1_048_576


def json_response(value: object, status: int = 200) -> Response:
    return Response(canonical_bytes(value), status_code=status, media_type="application/json")


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError) -> Response:
    return json_response(ContractError("INVALID_INPUT", "Invalid request.").envelope(), 422)


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "M1_CONTRACTS_ONLY"}


@app.post("/api/v1/contracts/{kind}/validate", responses={422: {"model": ErrorEnvelope}})
async def validate(kind: str, request: Request) -> Response:
    chunks = bytearray()
    async for chunk in request.stream():
        if len(chunks) + len(chunk) > MAX_BODY_BYTES:
            return json_response(
                ContractError("RESOURCE_LIMIT", "Contract body exceeds 1 MiB.").envelope(), 413
            )
        chunks.extend(chunk)
    try:
        return json_response(validate_contract(kind, bytes(chunks)))
    except ContractError as exc:
        return json_response(exc.envelope(), 422)


async def unavailable() -> Response:
    return json_response(not_implemented(), 501)


for operation in ("import", "compose", "compare", "revalidate", "preflight", "export"):
    app.add_api_route(
        f"/api/v1/{operation}",
        unavailable,
        methods=["POST"],
        name=operation,
        status_code=501,
        response_model=ErrorEnvelope,
        responses={501: {"model": ErrorEnvelope}},
    )
