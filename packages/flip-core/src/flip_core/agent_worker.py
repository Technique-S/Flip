"""Private fixed-operation bootstrap. No workflow-supplied code or import path."""

import os
import sys


def main():
    # Start containment before importing the application or reading its request.
    if sys.platform.startswith("linux"):
        import ctypes
        import resource

        parent = int(sys.argv[1])
        if ctypes.CDLL(None, use_errno=True).prctl(1, 9, 0, 0, 0) or os.getppid() != parent:
            raise RuntimeError("Parent lifetime containment unavailable")
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2,) * 2)
        resource.setrlimit(resource.RLIMIT_CPU, (35, 35))
    elif os.name != "nt":
        raise RuntimeError("Unsupported workflow platform")
    from pathlib import Path

    sys.path.insert(0, sys.argv[2])  # trusted parent's locked environment, never workflow input
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from flip_core.agent_models import WorkflowStep
    from flip_core.agent_operations import MeteredTransport, run_operation
    from flip_core.canonical import canonical_bytes, load_json
    from flip_core.contracts import ContractError

    payload = load_json(sys.stdin.buffer.read(4194305))
    step = WorkflowStep.model_validate(payload["step"])
    transport = MeteredTransport(payload["rpcLimit"])
    try:
        result = run_operation(payload, transport)
        result["error"] = None
        raw = canonical_bytes(result)
        if len(raw) > step.budget.maxOutputBytes:
            raise ContractError("RESOURCE_LIMIT", "Operation output exceeds its byte budget.")
    except ContractError as exc:
        result = dict(
            output=None, executionRequest=None, error=dict(code=exc.code, message=exc.message)
        )
    except Exception:
        # No provider, stack trace, credential or arbitrary exception text in receipts.
        result = dict(
            output=None,
            executionRequest=None,
            error=dict(code="WORKER_FAILURE", message="Trusted operation failed closed."),
        )
    finally:
        transport.inner.close()
    result["rpcUsed"] = transport.calls
    sys.stdout.buffer.write(canonical_bytes(result))


if __name__ == "__main__":
    main()
