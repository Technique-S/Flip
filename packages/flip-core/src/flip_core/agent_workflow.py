"""Finite deterministic controller. One contained trusted operation per declared attempt."""

import os
import signal
import subprocess
import sys
import sysconfig
from dataclasses import asdict
from pathlib import Path
from time import monotonic

from pydantic import ValidationError

from flip_core.agent_models import WorkflowRequest, WorkflowResult
from flip_core.agent_operations import classify, semantic
from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.contracts import ContractError
from flip_core.isolation import WindowsJob
from flip_core.rpc import RpcSettings

ZERO = "0x" + "0" * 64
RETRYABLE = {"RPC_UNAVAILABLE", "SOLVER_TIMEOUT", "WORKER_FAILURE"}


def parse_workflow(raw):
    try:
        data = (
            raw
            if isinstance(raw, bytes)
            else canonical_bytes(load_json(raw) if isinstance(raw, str) else raw)
        )
        if len(data) > 1048576:
            raise ContractError("RESOURCE_LIMIT", "Workflow input exceeds 1 MiB.")
        return WorkflowRequest.model_validate(load_json(data))
    except ContractError:
        raise
    except (ValueError, TypeError, ValidationError, RecursionError) as exc:
        raise ContractError(
            "INVALID_INPUT", "Invalid versioned workflow or step arguments."
        ) from exc


def operation_worker(payload, milliseconds, cancelled):
    """Poll cancellation/deadline; kill/reap the operation and contained solver on stop."""
    raw = canonical_bytes(payload)
    if len(raw) > 4194304:
        return dict(
            error=dict(code="RESOURCE_LIMIT", message="Operation input exceeds 4 MiB."),
            output=None,
            executionRequest=None,
            rpcUsed=0,
        )
    start = monotonic()
    process = job = None
    failure = "WORKER_FAILURE"
    try:
        process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                str(Path(__file__).with_name("agent_worker.py")),
                str(os.getpid()),
                sysconfig.get_path("platlib"),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name != "nt",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        if os.name == "nt":
            # Windows venv launcher + operation + native solver. The nested solver
            # keeps its original 64 MiB/one-process Job and five-second ceiling.
            job = WindowsJob(process, 512, max_processes=3)
        while True:
            if cancelled():
                failure = "CANCELLED"
                break
            remaining = milliseconds / 1000 - (monotonic() - start)
            if remaining <= 0:
                failure = "OPERATION_DEADLINE"
                break
            try:
                stdout, _ = process.communicate(raw, timeout=min(0.05, remaining))
                if process.returncode or len(stdout) > 4195328:
                    break
                result = load_json(stdout)
                if (
                    not isinstance(result, dict)
                    or set(result) != {"output", "executionRequest", "error", "rpcUsed"}
                    or type(result["rpcUsed"]) is not int
                    or not 0 <= result["rpcUsed"] <= payload["rpcLimit"]
                ):
                    break
                return result
            except subprocess.TimeoutExpired:
                raw = None  # communicate resumes without resending stdin
    except (OSError, ValueError, TypeError):
        pass
    finally:
        if job is not None:
            job.close()  # kill the whole Windows tree before waiting for inherited pipe handles
            job = None
        if process is not None:
            if process.poll() is None:
                try:
                    if os.name == "nt":
                        process.kill()
                    else:
                        os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.communicate()
    # Interrupted transport usage is unknowable: reserve its entire allowance, never undercount.
    return dict(
        error=dict(code=failure, message="Operation stopped; no revision accepted."),
        output=None,
        executionRequest=None,
        rpcUsed=payload["rpcLimit"],
        interrupted=True,
    )


def controller_identity():
    from flip_core.importer import sha
    from flip_core.verification import engine_identity

    return content_hash(
        dict(
            engine=engine_identity(),
            controller={
                name: sha(Path(__file__).with_name(name).read_bytes())
                for name in (
                    "agent_models.py",
                    "agent_operations.py",
                    "agent_workflow.py",
                    "agent_worker.py",
                    "debugging.py",
                    "debugging_models.py",
                    "library.py",
                    "library_models.py",
                    "rpc.py",
                    "workflow.py",
                )
            },
        )
    )


def execute(raw, *, settings=None, cancelled=None):
    model = parse_workflow(raw)
    settings = settings or RpcSettings.from_environment()
    cancelled = cancelled or (lambda: False)
    request_hash, engine_hash = content_hash(model), controller_identity()
    current = model.executionRequest.model_dump(mode="json") if model.executionRequest else None
    original_request = current
    original = content_hash(current) if current else None
    artifacts, logs, error, status = {}, [], None, "PREPARED"
    usage = dict(iterations=0, toolRequests=0, rpcRequests=0, rpcAccounting="EXACT")
    budget, start, previous, size = model.budget, monotonic(), request_hash, 0

    def issue(code, message):
        return dict(
            code=code,
            message=message,
            retryable=code in RETRYABLE,
            recovery="REIMPORT"
            if code == "IMPLEMENTATION_CHANGED"
            else "NONE"
            if code == "CANCELLED"
            else "NEW_REQUEST",
        )

    def boundary():
        if cancelled():
            return "CANCELLED", issue(
                "CANCELLED", "Workflow cancelled; resume requires a new request."
            )
        if (
            (monotonic() - start) * 1000 >= budget.deadlineMs
            or usage["iterations"] >= budget.maxIterations
            or usage["toolRequests"] >= budget.maxRequests
        ):
            return "BUDGET_EXHAUSTED", issue(
                "RESOURCE_LIMIT", "Workflow execution budget exhausted."
            )
        return None

    for step in model.steps:
        for attempt in range(step.retry.maxRetries + 1):
            stop = boundary()
            if stop:
                status, error = stop
                break
            usage["iterations"] += 1
            usage["toolRequests"] += 1
            rpc_limit = min(
                step.budget.imports.maxRequests, budget.maxRpcRequests - usage["rpcRequests"]
            )
            payload = dict(
                step=step.model_dump(mode="json"),
                executionRequest=current,
                source=artifacts.get(step.source),
                settings=asdict(settings),
                rpcLimit=rpc_limit,
            )
            remaining = max(1, int(budget.deadlineMs - (monotonic() - start) * 1000))
            input_hash = content_hash(
                dict(
                    step=step.model_dump(mode="json"),
                    executionHash=content_hash(current),
                    sourceHash=content_hash(semantic(payload["source"])),
                )
            )
            status = "RUNNING"
            if step.source is not None and step.source not in artifacts:
                result = dict(
                    output=None,
                    executionRequest=None,
                    rpcUsed=0,
                    error=dict(
                        code="INVALID_INPUT", message="Selected step produced no usable artifact."
                    ),
                )
            else:
                result = operation_worker(
                    payload, min(step.budget.deadlineMs, remaining), cancelled
                )
            usage["rpcRequests"] += result["rpcUsed"]
            if result.get("interrupted"):
                usage["rpcAccounting"] = "RESERVED_ON_INTERRUPTION"
            output, err = result["output"], result["error"]
            if err:
                code = err["code"]
                status = (
                    "CANCELLED"
                    if code == "CANCELLED"
                    else "STALE"
                    if code == "IMPLEMENTATION_CHANGED"
                    else "BUDGET_EXHAUSTED"
                    if code in ("RESOURCE_LIMIT", "OPERATION_DEADLINE")
                    else "INVALID_INPUT"
                    if code in ("INVALID_INPUT", "MISSING_MAPPING")
                    else "UNKNOWN"
                )
                error = issue(code, err["message"])
            elif not isinstance(output, dict):
                status, error = (
                    "UNKNOWN",
                    issue("WORKER_FAILURE", "Malformed trusted service output."),
                )
                output = None
            else:
                status, code = classify(output)
                error = issue(code, "Trusted operation is inconclusive.") if code else None
            # The deadline/cancel boundary wins over a late successful operation.
            if cancelled():
                status, error = "CANCELLED", issue("CANCELLED", "Operation cancelled.")
                output = None
            elif (monotonic() - start) * 1000 >= budget.deadlineMs:
                status, error = (
                    "BUDGET_EXHAUSTED",
                    issue("RESOURCE_LIMIT", "Workflow deadline exhausted."),
                )
                output = None
            accepted = status in ("COMPLETE", "DIFFERENT", "STOP_AUTHORIZATION")
            next_current = (
                result["executionRequest"] if accepted and result["executionRequest"] else current
            )
            event = dict(
                step=step.id,
                op=step.op,
                attempt=attempt + 1,
                status=status,
                inputHash=input_hash,
                outputHash=content_hash(semantic(output)),
                projectHash=content_hash(next_current["project"]) if next_current else None,
                executionHash=content_hash(next_current) if next_current else None,
                error=error,
                output=output,
                usage=dict(usage),
                budgetRemaining=dict(
                    iterations=budget.maxIterations - usage["iterations"],
                    toolRequests=budget.maxRequests - usage["toolRequests"],
                    rpcRequests=budget.maxRpcRequests - usage["rpcRequests"],
                ),
                previousHash=previous,
            )
            event["entryHash"] = content_hash({k: v for k, v in event.items() if k != "output"})
            event_size = len(canonical_bytes(event))
            # Reserve space for request/final-state and envelope, not only log entries.
            if (
                size
                + event_size
                + len(canonical_bytes(next_current))
                + len(canonical_bytes(original_request))
                + 4096
                > budget.maxReceiptBytes
            ):
                status, error = (
                    "BUDGET_EXHAUSTED",
                    issue("RESOURCE_LIMIT", "Receipt byte budget exhausted."),
                )
                break
            size += event_size
            logs.append(event)
            previous = event["entryHash"]
            current = next_current
            if accepted:
                artifacts[step.id] = output
            if (
                status == "UNKNOWN"
                and error
                and error["retryable"]
                and error["code"] in step.retry.on
                and attempt < step.retry.maxRetries
            ):
                continue
            break
        if status not in ("COMPLETE", "DIFFERENT", "UNKNOWN"):
            break
        if status in ("DIFFERENT", "UNKNOWN") and status not in step.continueOn:
            break
        if status == "COMPLETE" and logs:
            value = logs[-1]["output"]
            proof = value.get("comparison", value).get("report", {}).get("verification", {})
            if ("EQUIVALENT" in model.stopOn and proof.get("verdict") == "EQUIVALENT") or (
                "EXPORTED" in model.stopOn and step.op == "export"
            ):
                break
    result = dict(
        status=status,
        requestHash=request_hash,
        engineHash=engine_hash,
        originalExecutionHash=original,
        originalExecutionRequest=original_request,
        finalExecutionHash=content_hash(current) if current else None,
        executionRequest=current,
        logs=logs,
        usage=usage,
        error=error,
        receiptHash=ZERO,
        reproductionHash=content_hash(
            dict(
                requestHash=request_hash,
                engineHash=engine_hash,
                trace=[e["entryHash"] for e in logs],
                status=status,
                usage=usage,
            )
        ),
    )
    normalized = WorkflowResult.model_validate(result).model_dump(mode="json")
    if len(canonical_bytes(normalized)) > budget.maxReceiptBytes:
        # Preserve identities and partial logs; oversized original data remains in
        # the caller's content-bound request, never silently replace it with a revision.
        normalized["originalExecutionRequest"] = None
        normalized["executionRequest"] = None
    normalized["receiptHash"] = content_hash(
        {k: v for k, v in normalized.items() if k != "receiptHash"}
    )
    return WorkflowResult.model_validate(normalized)
