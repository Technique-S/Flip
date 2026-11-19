"""Read-only import, composition, local verification and evidence API."""

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
from flip_core.library_models import LibraryRequest, LibraryResult
from flip_core.models import ErrorEnvelope
from flip_core.rpc import RpcSettings
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool

app = FastAPI(title="Flip local workbench", version="0.1.0")
MAX_BODY_BYTES = 1_048_576
_slots = BoundedSemaphore(2)
_cache = ContentCache()


def execute_import(kind, model, block_number):
    if not _slots.acquire(blocking=False):
        raise ContractError("RESOURCE_LIMIT", "Import concurrency budget exceeded.")
    try:
        service = getattr(app.state, "import_service", None)
        if service is None:
            service = ImportService(RpcSettings.from_environment(), cache=_cache)
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


async def m3_request(request: Request, operation: str) -> Response:
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BODY_BYTES:
            return json_response(
                ContractError("RESOURCE_LIMIT", "Request exceeds 1 MiB.").envelope(), 413
            )
        raw.extend(chunk)
    try:
        value = load_json(bytes(raw))
        # Frozen report shapes, fabricated claims and legacy placeholders never
        # opt into execution. New execution requires an explicit additive version.
        product_op = operation in ("export", "verify-bundle", "preflight", "new-project")
        kind = "M3_CONSUMPTION" if operation == "consume" else "M3_EXECUTION"
        if not isinstance(value, dict) or value.get("kind") != (
            "PRODUCT_REQUEST" if product_op else kind
        ):
            return json_response(not_implemented(), 501)
        if request.query_params:
            raise ContractError("INVALID_INPUT", "Unknown M3 query parameter.")
        if operation in ("compare", "consume", "export", "verify-bundle") and (
            os.getenv("FLIP_LOCAL_SOLVER") != "1"
            or request.client is None
            or request.client.host not in ("127.0.0.1", "::1")
        ):
            return json_response(not_implemented(), 501)
        from flip_core.verification import execute

        if not _slots.acquire(blocking=False):
            raise ContractError("RESOURCE_LIMIT", "Local execution concurrency exceeded.")
        try:
            if product_op:
                from flip_core.workflow import product

                result = await run_in_threadpool(product, operation, value)
            else:
                result = await run_in_threadpool(execute, operation, bytes(raw))
        finally:
            _slots.release()
        return json_response(result)
    except ContractError as exc:
        return json_response(exc.envelope(), 429 if exc.code == "RESOURCE_LIMIT" else 422)
    except (ValueError, TypeError, ValidationError, RecursionError):
        return json_response(
            ContractError("INVALID_INPUT", "Invalid M3 execution request.").envelope(), 422
        )


@app.post("/api/v1/compose")
async def compose_circuit(request: Request) -> Response:
    return await m3_request(request, "compose")


@app.post("/api/v1/compare")
async def compare_circuits(request: Request) -> Response:
    return await m3_request(request, "compare")


@app.post("/api/v1/vectors")
async def vector_check(request: Request) -> Response:
    return await m3_request(request, "vectors")


@app.post("/api/v1/consume")
async def consume_proof(request: Request) -> Response:
    return await m3_request(request, "consume")


@app.post("/api/v1/new-project")
async def new_project(request: Request) -> Response:
    return await m3_request(request, "new-project")


@app.post("/api/v1/preflight")
async def structural_preflight(request: Request) -> Response:
    return await m3_request(request, "preflight")


@app.post("/api/v1/export")
async def export_evidence(request: Request) -> Response:
    return await m3_request(request, "export")


@app.post("/api/v1/verify-bundle")
async def replay_evidence(request: Request) -> Response:
    return await m3_request(request, "verify-bundle")


@app.get("/api/v1/sample/{variant}")
async def historical_sample(variant: str) -> Response:
    from flip_core.workflow import sample

    try:
        return json_response(sample(variant))
    except ContractError as exc:
        return json_response(exc.envelope(), 404)


LIBRARY_BODY_SCHEMA = LibraryRequest.model_json_schema(ref_template="#/components/schemas/{model}")
LIBRARY_BODY_SCHEMA.pop("$defs", None)


@app.post(
    "/api/library/v1/execute",
    response_model=LibraryResult,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/json": {"schema": LIBRARY_BODY_SCHEMA}},
        }
    },
)
async def library_operation(request: Request) -> Response:
    from threading import Event

    from flip_core.library import LibraryService
    from flip_core.library_protocol import parse_library_request

    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BODY_BYTES:
            return json_response(
                ContractError("RESOURCE_LIMIT", "Library input exceeds 1 MiB.").envelope(), 413
            )
        raw.extend(chunk)
    acquired = False
    try:
        if request.query_params:
            raise ContractError("INVALID_INPUT", "Unknown library query parameter.")
        model = parse_library_request(load_json(bytes(raw)))
        if not _slots.acquire(blocking=False):
            raise ContractError("RESOURCE_LIMIT", "Library concurrency budget exceeded.")
        acquired = True
        stopped = Event()
        service = getattr(app.state, "library_service", None) or LibraryService(
            RpcSettings.from_environment(),
            aborted=stopped.is_set,
        )
        # Poll for a disconnected browser while the bounded synchronous reader runs.
        import anyio

        async def watch_disconnect():
            while True:
                if await request.is_disconnected():
                    stopped.set()
                    return
                await anyio.sleep(0.1)

        def execute_library():
            # Return domain failures through the task group so its ExceptionGroup
            # wrapper cannot turn an ordinary invalid selection into HTTP 500.
            try:
                return service.execute(model)
            except (ContractError, ValueError, TypeError, RecursionError) as exc:
                return exc

        async with anyio.create_task_group() as group:
            group.start_soon(watch_disconnect)
            result = await run_in_threadpool(execute_library)
            group.cancel_scope.cancel()
        if isinstance(result, Exception):
            raise result
        return json_response(result)
    except ContractError as exc:
        return json_response(exc.envelope(), 429 if exc.code == "RESOURCE_LIMIT" else 422)
    except (ValueError, TypeError, ValidationError, RecursionError):
        return json_response(
            ContractError("INVALID_INPUT", "Invalid library request.").envelope(), 422
        )
    finally:
        if acquired:
            _slots.release()
