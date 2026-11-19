"""Additive agent protocol; instructions and metadata never convey authority."""

from typing import Annotated, Literal

from pydantic import Field, model_validator

from flip_core.debugging_models import TraceBudget
from flip_core.import_models import ImportBudget
from flip_core.library_models import LibraryRequest
from flip_core.models import Candidate, CircuitIdentity, Contract, Digest, Name, Quantity
from flip_core.verification import ExpectedVector, VerificationRequest

VERSION = "m45-agent-workflow-1.0.0"
Status = Literal[
    "PREPARED",
    "RUNNING",
    "COMPLETE",
    "DIFFERENT",
    "UNKNOWN",
    "STALE",
    "BUDGET_EXHAUSTED",
    "STOP_AUTHORIZATION",
    "CANCELLED",
    "INVALID_INPUT",
]
Operation = Literal[
    "sample",
    "discover",
    "import",
    "build",
    "test",
    "compare",
    "inspect",
    "propose_correction",
    "verify",
    "apply",
    "export",
    "verify_bundle",
    "revalidate",
    "stop_authorization",
]


class WorkflowBudget(Contract):
    maxIterations: int = Field(default=24, ge=1, le=64)
    maxRequests: int = Field(default=32, ge=1, le=64)
    maxRpcRequests: int = Field(default=256, ge=0, le=8192)
    deadlineMs: int = Field(default=300000, ge=1, le=300000)
    maxReceiptBytes: int = Field(default=8388608, ge=4096, le=16777216)


class OperationBudget(Contract):
    deadlineMs: int = Field(default=15000, ge=1, le=30000)
    maxOutputBytes: int = Field(default=1048576, ge=1024, le=4194304)
    imports: ImportBudget = Field(default_factory=ImportBudget)
    trace: TraceBudget = Field(default_factory=TraceBudget)


class RetryPolicy(Contract):
    maxRetries: int = Field(default=0, ge=0, le=2)
    # The policy never changes a project, deadline ceiling or proof budget.
    on: list[Literal["RPC_UNAVAILABLE", "SOLVER_TIMEOUT", "WORKER_FAILURE"]] = Field(
        default_factory=list, max_length=3
    )


class WorkflowStep(Contract):
    id: Name
    op: Operation
    source: Name | None = None
    expectedExecutionHash: Digest | None = None
    actionId: Digest | None = None
    candidate: Candidate | None = None
    libraryRequest: LibraryRequest | None = None
    identity: CircuitIdentity | None = None
    blockNumber: Quantity | None = None
    variant: Literal["half-adder", "swapped"] | None = None
    vectors: list[ExpectedVector] | None = Field(default=None, min_length=1, max_length=4096)
    bundle: dict | None = None
    budget: OperationBudget = Field(default_factory=OperationBudget)
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    continueOn: list[Literal["DIFFERENT", "UNKNOWN"]] = Field(default_factory=list, max_length=2)

    @model_validator(mode="after")
    def arguments(self):
        fields = {
            "sample": {"variant"},
            "discover": {"libraryRequest"},
            "import": {"identity", "blockNumber"},
            "build": {"source"},
            "test": {"vectors"},
            "compare": set(),
            "inspect": set(),
            "propose_correction": {"candidate", "expectedExecutionHash", "actionId"},
            "verify": {"source", "expectedExecutionHash", "actionId"},
            "apply": {"source", "expectedExecutionHash", "actionId"},
            "export": set(),
            "verify_bundle": {"source", "bundle"},
            "revalidate": {"source"},
            "stop_authorization": set(),
        }
        arguments = {
            "variant",
            "libraryRequest",
            "identity",
            "blockNumber",
            "source",
            "candidate",
            "expectedExecutionHash",
            "actionId",
            "vectors",
            "bundle",
        }
        if any(getattr(self, name) is not None for name in arguments - fields[self.op]):
            raise ValueError("Arguments do not belong to the selected operation")
        required = {
            "sample": ("variant",),
            "discover": ("libraryRequest",),
            "import": ("identity",),
            "test": ("vectors",),
            "propose_correction": ("expectedExecutionHash",),
            "verify": ("source", "expectedExecutionHash", "actionId"),
            "apply": ("source", "expectedExecutionHash", "actionId"),
        }.get(self.op, ())
        if any(getattr(self, name) is None for name in required):
            raise ValueError("Missing operation argument")
        if self.op == "verify_bundle" and (self.source is None) == (self.bundle is None):
            raise ValueError("Select one earlier export or one external bundle")
        if self.op == "discover" and self.libraryRequest.operation not in (
            "discover",
            "circuits",
            "search",
        ):
            raise ValueError("Discovery only accepts read-only catalog queries")
        return self


class WorkflowRequest(Contract):
    schemaVersion: Literal["m45-agent-workflow-1.0.0"] = VERSION
    kind: Literal["AGENT_WORKFLOW_REQUEST"] = "AGENT_WORKFLOW_REQUEST"
    executionRequest: VerificationRequest | None = None
    steps: Annotated[list[WorkflowStep], Field(min_length=1, max_length=64)]
    budget: WorkflowBudget = Field(default_factory=WorkflowBudget)
    stopOn: list[Literal["EQUIVALENT", "EXPORTED"]] = Field(default_factory=list, max_length=2)

    @model_validator(mode="after")
    def ordered_steps(self):
        seen = set()
        for step in self.steps:
            if step.id in seen or (step.source is not None and step.source not in seen):
                raise ValueError("Step IDs must be unique; sources must precede consumers")
            seen.add(step.id)
        return self


class WorkflowError(Contract):
    code: str
    message: str
    retryable: bool = False
    recovery: Literal["NEW_REQUEST", "REIMPORT", "EXPLICIT_REVISION", "NONE"] = "NEW_REQUEST"


class Usage(Contract):
    iterations: int = 0
    toolRequests: int = 0
    rpcRequests: int = 0
    rpcAccounting: Literal["EXACT", "RESERVED_ON_INTERRUPTION"] = "EXACT"


class OperationResult(Contract):
    step: Name
    op: Operation
    attempt: int
    status: Status
    inputHash: Digest
    outputHash: Digest
    projectHash: Digest | None
    executionHash: Digest | None
    error: WorkflowError | None = None
    output: dict | None = None
    usage: Usage
    budgetRemaining: dict[str, int]
    previousHash: Digest
    entryHash: Digest


class WorkflowResult(Contract):
    schemaVersion: Literal["m45-agent-workflow-1.0.0"] = VERSION
    kind: Literal["AGENT_WORKFLOW_RESULT"] = "AGENT_WORKFLOW_RESULT"
    status: Status
    requestHash: Digest
    engineHash: Digest
    originalExecutionHash: Digest | None
    originalExecutionRequest: VerificationRequest | None
    finalExecutionHash: Digest | None
    executionRequest: VerificationRequest | None
    logs: list[OperationResult] = Field(default_factory=list, max_length=64)
    usage: Usage
    error: WorkflowError | None = None
    receiptHash: Digest
    reproductionHash: Digest
    scope: Literal["LOCAL_BOUNDED_HISTORICAL_REFERENCE_RELATIVE"] = (
        "LOCAL_BOUNDED_HISTORICAL_REFERENCE_RELATIVE"
    )
