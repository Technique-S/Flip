"""Shared read-only importer API; composition/proof/preflight remain unimplemented."""

import os
from threading import BoundedSemaphore

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from flip_core.canonical import canonical_bytes, load_json
from flip_core.contracts import ContractError, not_implemented, validate_contract
from flip_core.import_models import ImportResult, RevalidationResult
from flip_core.importer import ImportService
from flip_core.integrity import ContentCache
from flip_core.models import ErrorEnvelope
from flip_core.rpc import RpcSettings
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

app = FastAPI(title="Flip M1-A contracts", version="0.1.0")
MAX_BODY_BYTES = 1_048_576
_slots = BoundedSemaphore(2)
_cache = ContentCache()


def execute_import(kind, model, block_number):
    if not _slots.acquire(blocking=False):
        raise ContractError("RESOURCE_LIMIT", "Import concurrency budget exceeded.")
    try:
        service = getattr(app.state, "import_service", None)
        if service is None:
            try:
                settings = RpcSettings(
                    os.getenv("FLIP_RPC_URL", "https://rpc.xlayer.tech"),
                    int(os.getenv("FLIP_RPC_TIMEOUT_MS", "5000")),
                    int(os.getenv("FLIP_RPC_RETRIES", "1")),
                )
            except (ValueError, ContractError) as exc:
                raise ContractError("RPC_UNAVAILABLE", "Invalid server RPC configuration.") from exc
            service = ImportService(settings, cache=_cache)
        if kind == "manifest":
            return service.revalidate(model)
        return service.import_circuit(model, block_number)
    finally:
        _slots.release()


async def import_request(request: Request, kind: str) -> Response:
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BODY_BYTES:
            return json_response(
                ContractError("RESOURCE_LIMIT", "Request exceeds 1 MiB.").envelope(), 413
            )
        raw.extend(chunk)
    try:
        value = load_json(bytes(raw))
        # Preserve the M1 legacy/unversioned placeholder behavior. Only the frozen
        # versioned identity/manifest shape can opt into the new read-only operation.
        if isinstance(value, dict) and "schemaVersion" not in value:
            return json_response(not_implemented(), 501)
        model = validate_contract(kind, bytes(raw))
        if any(k != "blockNumber" for k in request.query_params):
            raise ContractError("INVALID_INPUT", "Unknown import query parameter.")
        if kind == "manifest" and request.query_params:
            raise ContractError("INVALID_INPUT", "Revalidation always observes a fresh block.")
        result = await run_in_threadpool(
            execute_import, kind, model, request.query_params.get("blockNumber")
        )
        return json_response(result)
    except ContractError as exc:
        status = {
            "RPC_UNAVAILABLE": 503,
            "RESOURCE_LIMIT": 429,
            "REF_DEPTH_EXCEEDED": 429,
            "IMPLEMENTATION_CHANGED": 409,
        }.get(exc.code, 422)
        return json_response(exc.envelope(), status)
    except (ValueError, TypeError, ValidationError, RecursionError):
        return json_response(
            ContractError("INVALID_INPUT", "Invalid import request.").envelope(), 422
        )


IMPORT_BODY = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {"schema": {"$ref": "#/components/schemas/CircuitIdentity"}}
        },
    },
    "parameters": [
        {
            "name": "blockNumber",
            "in": "query",
            "required": False,
            "schema": {"type": "string", "pattern": "^(0|[1-9][0-9]*)$"},
            "description": "Explicit historical block, never automatically CURRENT.",
        }
    ],
}
IMPORT_ERRORS = {status: {"model": ErrorEnvelope} for status in (409, 413, 422, 429, 501, 503)}


@app.post(
    "/api/v1/import",
    response_model=ImportResult,
    openapi_extra=IMPORT_BODY,
    responses=IMPORT_ERRORS,
)
@app.post(
    "/api/v1/inspect",
    response_model=ImportResult,
    openapi_extra=IMPORT_BODY,
    responses=IMPORT_ERRORS,
)
async def import_circuit(request: Request) -> Response:
    return await import_request(request, "circuit-identity")


@app.post(
    "/api/v1/revalidate",
    response_model=RevalidationResult,
    responses=IMPORT_ERRORS,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Manifest"}}},
        }
    },
)
async def revalidate_manifest(request: Request) -> Response:
    return await import_request(request, "manifest")


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


for operation in ("compose", "compare", "preflight", "export"):
    app.add_api_route(
        f"/api/v1/{operation}",
        unavailable,
        methods=["POST"],
        name=operation,
        status_code=501,
        response_model=ErrorEnvelope,
        responses={501: {"model": ErrorEnvelope}},
    )
