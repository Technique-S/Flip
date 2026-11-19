"""Additive diagnostics contract. Frozen M1/M3/library contracts are unchanged."""

from typing import Literal

from pydantic import Field

from flip_core.models import CircuitIdentity, Contract, Digest, PinSource
from flip_core.verification import VerificationRequest

VERSION = "m45-debugging-1.0.0"


class TraceBudget(Contract):
    maxCircuitBytes: int = Field(default=250000, ge=1, le=1000000)
    maxCircuits: int = Field(default=128, ge=1, le=256)
    maxExpandedGates: int = Field(default=5000, ge=1, le=10000)
    operationDeadlineMs: int = Field(default=15000, ge=1, le=30000)
    maxNodes: int = Field(default=4096, ge=1, le=8192)
    maxConnections: int = Field(default=4096, ge=1, le=8192)
    maxIndexedSignals: int = Field(default=20000, ge=1, le=100000)
    maxDepth: int = Field(default=32, ge=0, le=64)
    deadlineMs: int = Field(default=1000, ge=1, le=5000)


class DebugRequest(Contract):
    schemaVersion: Literal["m45-debugging-1.0.0"]
    kind: Literal["DEBUG_REQUEST"]
    operation: Literal["diagnose", "verify-correction"] = "diagnose"
    executionRequest: VerificationRequest
    budget: TraceBudget = Field(default_factory=TraceBudget)
    actionId: Digest | None = None


class Connection(Contract):
    classification: Literal["RELEVANT_CONNECTION"] = "RELEVANT_CONNECTION"
    side: Literal["reference", "candidate"]
    path: str = Field(max_length=2048)
    connectionRef: str = Field(max_length=2200)
    kind: Literal["NAND", "REF_INPUT", "REF_OUTPUT", "OUTPUT_MAP"]
    elementIndex: int | None = None
    inputPin: int | None = None
    outputPin: int | None = None
    sourceSignal: int
    destination: str = Field(max_length=2200)
    netlistHash: Digest
    identity: CircuitIdentity | None = None
    instanceId: str | None = None
    projectPin: PinSource | None = None


class Edit(Contract):
    location: str
    before: PinSource
    after: PinSource


class CandidateAction(Contract):
    classification: Literal["CANDIDATE_ACTION"] = "CANDIDATE_ACTION"
    actionId: Digest
    title: str
    reasoning: str
    edits: list[Edit] = Field(max_length=10000)
    proposedRevision: VerificationRequest


class Correction(Contract):
    classification: Literal["VERIFIED_CORRECTION", "UNKNOWN", "CANDIDATE_ACTION"]
    actionId: Digest
    originalProjectHash: Digest
    revisedProjectHash: Digest
    comparison: dict
    revalidation: Literal["PINNED_IDENTITIES_HASHES_AND_CLOSURE_REPLAYED"]
    scope: Literal["EXACT_STATELESS_SELECTED_REFERENCE_HISTORICAL"]


class DebugResult(Contract):
    schemaVersion: Literal["m45-debugging-1.0.0"] = VERSION
    kind: Literal["DEBUG_RESULT"] = "DEBUG_RESULT"
    classification: Literal["VERIFIED_DIFFERENCE", "NO_FAULT_ATTRIBUTION", "UNKNOWN"]
    attribution: Literal[
        "AMBIGUOUS_MULTIPLE_CAUSES",
        "SUSPECTED_CANDIDATE",
        "NO_FAULT_ATTRIBUTION",
        "UNKNOWN_NO_ATTRIBUTION",
    ]
    uniqueFaultClaim: Literal[False] = False
    reasoning: str
    reasonCode: str | None = None
    projectHash: Digest
    executionHash: Digest
    diagnosticEngineHash: Digest
    comparison: dict | None = None
    differingOutputBits: list[int] = Field(default_factory=list, max_length=8192)
    connections: list[Connection] = Field(default_factory=list, max_length=8192)
    nodesVisited: int = 0
    indexedSignals: int = 0
    actions: list[CandidateAction] = Field(default_factory=list, max_length=1)
    correction: Correction | None = None
    revalidation: Literal["PINNED_SNAPSHOT_ONLY_NOT_LIVE"] = "PINNED_SNAPSHOT_ONLY_NOT_LIVE"
    semanticHash: Digest | None = None
