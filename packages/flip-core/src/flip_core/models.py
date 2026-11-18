"""Version 1 contracts. Validation establishes consistency, never observed chain truth."""

from typing import Annotated, Literal, Self

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from flip_core.canonical import content_hash

Version = Literal["1.0.0"]
UInt = Annotated[int, Field(ge=0, le=2**32 - 1)]
Pin = Annotated[int, Field(ge=0, le=65535)]
Digest = Annotated[str, Field(pattern=r"^0x[0-9a-f]{64}$")]
HexBytes = Annotated[str, Field(pattern=r"^0x(?:[0-9a-f]{2})*$", max_length=2_000_002)]
Name = Annotated[str, Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")]


def _uint256(value: str) -> str:
    if int(value) >= 2**256:
        raise ValueError("quantity exceeds uint256")
    return value


Quantity = Annotated[
    str, Field(pattern=r"^(0|[1-9][0-9]*)$", max_length=78), AfterValidator(_uint256)
]
Address = Annotated[str, Field(pattern=r"^0x[0-9a-fA-F]{40}$"), AfterValidator(str.lower)]


def _chain(value: object) -> object:
    if type(value) is not int or value != 196:
        raise ValueError("WRONG_CHAIN: expected integer chainId=196")
    return value


Chain = Annotated[Literal[196], BeforeValidator(_chain)]
Reason = Literal[
    "NOT_IMPLEMENTED",
    "INVALID_INPUT",
    "UNSUPPORTED_SCHEMA_VERSION",
    "WRONG_CHAIN",
    "BAD_NETLIST",
    "REF_DEPTH_EXCEEDED",
    "RESOURCE_LIMIT",
    "RPC_UNAVAILABLE",
    "IMPLEMENTATION_CHANGED",
    "SOLVER_TIMEOUT",
    "WITNESS_REPLAY_FAILED",
    "UNSUPPORTED_STATEFUL_PROOF",
    "MISSING_REFERENCE",
    "MISSING_MAPPING",
    "INTERNAL_ERROR",
    "UNRECOGNIZED_REVERT",
    "STRUCTURAL_REJECTION",
]
Freshness = Literal["CURRENT", "HISTORICAL", "STALE", "UNVERIFIED"]
Intent = Literal["TRUSTED_REFERENCE", "UNDECLARED"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_default=True)


class CircuitIdentity(Contract):
    schemaVersion: Version
    chainId: Chain
    processor: Address
    circuitId: Quantity


class Block(Contract):
    number: Quantity
    hash: Digest


class Limits(Contract):
    gateCap: Annotated[int, Field(ge=1, le=5000)] = 2500
    refDepthCap: Annotated[int, Field(ge=1, le=64)] = 64
    solverTimeoutMs: Annotated[int, Field(ge=1, le=5000)] = 5000
    solverMemoryMiB: Annotated[int, Field(ge=1, le=64)] = 64


class BitVector(Contract):
    """Text character i is vector bit i, packed into byte i//8 at bit i%8."""

    encoding: Literal["tap02-lsb0-v1"]
    width: Annotated[int, Field(ge=0, le=65536)]
    bits: Annotated[str, Field(pattern=r"^[01]*$", max_length=65536)]

    @model_validator(mode="after")
    def width_matches(self) -> Self:
        if len(self.bits) != self.width:
            raise ValueError("bitvector width must match text length")
        return self


class Semantics(Contract):
    tap02Version: Literal["draft-2026-10-04"]
    encoding: Literal["tap02-lsb0-v1"]
    specificationHash: Literal["0x8db03f6298c58aae5a9adeaa3774c30ecdf9db1f276c3efd0079648444d8850f"]
    referenceHash: Literal["0x0e8515948981361c7db57373e8986eab63056f1ce0fad5a3ec070c1887919fa9"]
    testSuiteHash: Literal["0x1a02f5cf991c130a22dc6cc6ee93d0f8fe0720afed081665fa8b8018aefd203b"]


class CodeIdentity(Contract):
    address: Address
    codeHash: Digest


class Environment(Contract):
    factory: CodeIdentity
    factoryImplementationSlot: Digest
    factoryImplementation: CodeIdentity
    factorySealed: bool
    beacon: CodeIdentity
    beaconImplementation: CodeIdentity
    processorCodeHash: Digest


class Snapshot(Contract):
    identity: CircuitIdentity
    netlistHash: Digest
    nIn: Annotated[int, Field(ge=0, le=65536)]
    nOut: Annotated[int, Field(ge=1, le=65536)]
    nState: UInt
    expandedGates: Annotated[int, Field(ge=0, le=5000)]
    environment: Environment


class Dependency(Contract):
    parent: CircuitIdentity
    child: CircuitIdentity


class Manifest(Contract):
    schemaVersion: Version
    chainId: Chain
    block: Block
    root: Snapshot
    dependencies: Annotated[list[Snapshot], Field(max_length=1250)]
    edges: Annotated[list[Dependency], Field(max_length=5000)]
    semantics: Semantics
    toolVersion: Literal["0.1.0"]
    observation: Literal["SINGLE_RPC", "OFFLINE_SNAPSHOT"]

    @model_validator(mode="after")
    def unique_closure(self) -> Self:
        snapshots = [self.root, *self.dependencies]
        keys = [content_hash(s.identity) for s in snapshots]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate circuit in manifest closure")
        adjacency: dict[str, list[str]] = {key: [] for key in keys}
        for edge in self.edges:
            parent, child = content_hash(edge.parent), content_hash(edge.child)
            if parent not in adjacency or child not in adjacency:
                raise ValueError("edge references absent closure member")
            if child in adjacency[parent]:
                raise ValueError("duplicate dependency edge")
            adjacency[parent].append(child)
        depths: dict[str, int] = {}

        def visit(key: str, path: frozenset[str]) -> int:
            if key in path or len(path) > 64:
                raise ValueError("cyclic or over-depth manifest closure")
            if key not in depths:
                depths[key] = max(
                    (1 + visit(child, path | {key}) for child in adjacency[key]), default=0
                )
            return depths[key]

        if visit(keys[0], frozenset()) > 64:
            raise ValueError("over-depth manifest closure")
        if set(depths) != set(keys):
            raise ValueError("unreachable dependency in manifest")
        return self


class Source(Contract):
    alias: Name
    identity: CircuitIdentity
    manifestHash: Digest
    nIn: Annotated[int, Field(ge=0, le=65536)]
    nOut: Annotated[int, Field(ge=1, le=65536)]
    nState: UInt


class PinSource(Contract):
    component: Name | None  # null means external input
    pin: Pin


class RefComponent(Contract):
    kind: Literal["REF"]
    instanceId: Name
    sourceAlias: Name
    inputs: Annotated[list[PinSource], Field(max_length=255)]


class NandComponent(Contract):
    kind: Literal["NAND"]
    instanceId: Name
    inputs: Annotated[list[PinSource], Field(min_length=2, max_length=2)]


Component = Annotated[RefComponent | NandComponent, Field(discriminator="kind")]


class Candidate(Contract):
    nIn: Annotated[int, Field(ge=0, le=65536)]
    components: Annotated[list[Component], Field(max_length=5000)]
    outputs: Annotated[list[PinSource], Field(min_length=1, max_length=65536)]


class ComparisonPlan(Contract):
    kind: Literal["PAIRWISE_EQUIVALENCE"]
    referenceAlias: Name
    intent: Intent
    trustAssertion: Annotated[str, Field(min_length=1, max_length=1000)] | None
    inputMap: Annotated[list[Pin], Field(max_length=65536)]
    outputMap: Annotated[list[Pin], Field(min_length=1, max_length=65536)]

    @model_validator(mode="after")
    def intent_asserted(self) -> Self:
        if (self.intent == "TRUSTED_REFERENCE") != (self.trustAssertion is not None):
            raise ValueError("trust assertion required exactly for trusted reference intent")
        return self


class Project(Contract):
    schemaVersion: Version
    projectId: Name
    chainId: Chain
    toolVersion: Literal["0.1.0"]
    sources: Annotated[list[Source], Field(min_length=1, max_length=1251)]
    candidate: Candidate
    comparison: ComparisonPlan
    limits: Limits

    @model_validator(mode="after")
    def references_and_pins(self) -> Self:
        sources = {s.alias: s for s in self.sources}
        if len(sources) != len(self.sources):
            raise ValueError("duplicate source alias")
        widths: dict[str, int] = {}

        def check(pin: PinSource) -> None:
            width = self.candidate.nIn if pin.component is None else widths.get(pin.component)
            if width is None or pin.pin >= width:
                raise ValueError("pin out of range or forward/undefined component")

        for component in self.candidate.components:
            if component.instanceId in widths:
                raise ValueError("duplicate component instance")
            for pin in component.inputs:
                check(pin)
            if component.kind == "REF":
                source = sources.get(component.sourceAlias)
                if source is None or len(component.inputs) != source.nIn or source.nState:
                    raise ValueError("unknown REF, wrong arity or unsupported stateful composition")
                if int(source.identity.circuitId) >= 2**64:
                    raise ValueError("TAP-02 REF circuitId must fit uint64")
                widths[component.instanceId] = source.nOut
            else:
                widths[component.instanceId] = 1
        for pin in self.candidate.outputs:
            check(pin)
        reference = sources.get(self.comparison.referenceAlias)
        if reference is None:
            raise ValueError("missing reference source")
        if reference.nState:
            raise ValueError("UNSUPPORTED_STATEFUL_PROOF")
        if sorted(self.comparison.inputMap) != list(range(self.candidate.nIn)):
            raise ValueError("inputMap must be a complete bijection")
        if len(self.comparison.inputMap) != reference.nIn:
            raise ValueError("reference and candidate input widths differ")
        if sorted(self.comparison.outputMap) != list(range(len(self.candidate.outputs))):
            raise ValueError("outputMap must be a complete bijection")
        if len(self.comparison.outputMap) != reference.nOut:
            raise ValueError("reference and candidate output widths differ")
        return self


class Integrity(Contract):
    freshness: Freshness
    checkedBlock: Block | None

    @model_validator(mode="after")
    def current_observed(self) -> Self:
        if self.freshness == "CURRENT" and self.checkedBlock is None:
            raise ValueError("CURRENT requires a revalidation block")
        return self


class Witness(Contract):
    inputs: BitVector
    referenceOutputs: BitVector
    candidateOutputs: BitVector
    replay: Literal["REF_BEAT_REPRODUCED"]
    minimization: Literal["NONE", "HEURISTIC"]

    @model_validator(mode="after")
    def distinguishing(self) -> Self:
        a, b = self.referenceOutputs, self.candidateOutputs
        if a.width != b.width or a.bits == b.bits:
            raise ValueError("witness must distinguish equal-width outputs")
        return self


class Proof(Contract):
    kind: Literal["PAIRWISE_EQUIVALENCE"]
    verdict: Literal["EQUIVALENT", "DIFFERENT", "UNKNOWN"]
    reasonCode: Reason | None
    solverBackend: Literal["Minisat22", "NONE"]
    solverOutcome: Literal["UNSAT", "SAT", "NOT_RUN", "INTERRUPTED"]
    referenceNState: UInt
    candidateNState: UInt
    sourceValidation: Literal["PASSED", "UNVERIFIED"]
    mappingValidation: Literal["PASSED", "UNVERIFIED"]
    witness: Witness | None

    @model_validator(mode="after")
    def evidence_required(self) -> Self:
        if self.verdict == "UNKNOWN":
            if self.reasonCode is None or self.witness is not None:
                raise ValueError("UNKNOWN requires reason and cannot carry a trusted witness")
            return self
        if self.reasonCode is not None or self.solverBackend != "Minisat22":
            raise ValueError("conclusive proof requires backend and no failure reason")
        if self.referenceNState or self.candidateNState:
            raise ValueError("stateful circuits cannot have unbounded proof verdicts")
        if self.sourceValidation != "PASSED" or self.mappingValidation != "PASSED":
            raise ValueError("conclusive proof requires source and mapping validation")
        if self.verdict == "EQUIVALENT":
            if self.solverOutcome != "UNSAT" or self.witness is not None:
                raise ValueError("EQUIVALENT requires UNSAT without witness")
        elif self.solverOutcome != "SAT" or self.witness is None:
            raise ValueError("DIFFERENT requires SAT and reproduced witness")
        return self


class ComparisonReport(Contract):
    schemaVersion: Version
    chainId: Chain
    projectHash: Digest
    referenceManifestHash: Digest
    candidateManifestHash: Digest
    toolVersion: Literal["0.1.0"]
    semantics: Semantics
    limits: Limits
    verification: Proof
    intent: Intent
    trustAssertion: Annotated[str, Field(min_length=1, max_length=1000)] | None
    inputMap: Annotated[list[Pin], Field(max_length=65536)]
    outputMap: Annotated[list[Pin], Field(min_length=1, max_length=65536)]
    integrity: Integrity

    @model_validator(mode="after")
    def report_consistent(self) -> Self:
        if (self.intent == "TRUSTED_REFERENCE") != (self.trustAssertion is not None):
            raise ValueError("trust assertion required exactly for trusted reference intent")
        if self.verification.verdict != "UNKNOWN":
            if self.integrity.freshness == "UNVERIFIED":
                raise ValueError("conclusive historical evidence requires validated manifests")
            if sorted(self.inputMap) != list(range(len(self.inputMap))):
                raise ValueError("invalid input mapping")
            if sorted(self.outputMap) != list(range(len(self.outputMap))):
                raise ValueError("invalid output mapping")
            witness = self.verification.witness
            if witness and (
                witness.inputs.width != len(self.inputMap)
                or witness.referenceOutputs.width != len(self.outputMap)
            ):
                raise ValueError("witness widths do not match mapping")
        return self


def _true(value: object) -> object:
    if type(value) is not bool or value is not True:
        raise ValueError("manifestRevalidated requires boolean true")
    return value


class CallObservation(Contract):
    block: Block
    feeWei: Quantity
    manifestRevalidated: Annotated[Literal[True], BeforeValidator(_true)]
    revertData: HexBytes
    classification: Literal["KNOWN_BURN_STAGE", "KNOWN_STRUCTURAL_REJECTION", "UNRECOGNIZED"]


class Preflight(Contract):
    schemaVersion: Version
    chainId: Chain
    candidateNetlistHash: Digest
    manifestHash: Digest
    mode: Literal["READ_ONLY_ETH_CALL"]
    status: Literal["STRUCTURALLY_ACCEPTED", "REJECTED", "UNKNOWN"]
    reasonCode: Reason | None
    observation: CallObservation | None
    integrity: Integrity

    @model_validator(mode="after")
    def observed_only(self) -> Self:
        if self.status == "UNKNOWN":
            if self.reasonCode is None:
                raise ValueError("UNKNOWN preflight requires reason")
            return self
        if self.observation is None or self.integrity.freshness != "CURRENT":
            raise ValueError("structural verdict requires fresh read-only observation")
        if self.integrity.checkedBlock != self.observation.block:
            raise ValueError("preflight and revalidation blocks must match")
        expected = (
            "KNOWN_BURN_STAGE"
            if self.status == "STRUCTURALLY_ACCEPTED"
            else "KNOWN_STRUCTURAL_REJECTION"
        )
        if self.observation.classification != expected:
            raise ValueError("revert classification does not support status")
        if self.status == "STRUCTURALLY_ACCEPTED" and self.reasonCode is not None:
            raise ValueError("structural acceptance cannot have failure reason")
        if self.status == "REJECTED" and self.reasonCode != "STRUCTURAL_REJECTION":
            raise ValueError("rejection requires structural rejection reason")
        return self


class ErrorDetail(Contract):
    code: Reason
    message: Annotated[str, Field(min_length=1, max_length=1000)]


class ErrorEnvelope(Contract):
    schemaVersion: Version
    error: ErrorDetail


CONTRACTS = {
    "circuit-identity": CircuitIdentity,
    "project": Project,
    "manifest": Manifest,
    "comparison-report": ComparisonReport,
    "preflight": Preflight,
    "error-envelope": ErrorEnvelope,
}
