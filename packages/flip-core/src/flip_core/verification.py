"""Trusted construction and consumption, distinct from frozen report shape validation."""

from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from platform import python_version
from time import monotonic
from typing import Annotated, Literal

from pydantic import Field, ValidationError, model_validator

from flip_core.canonical import content_hash, load_json
from flip_core.cnf import miter
from flip_core.composition import compile_project
from flip_core.composition_models import LocalProject
from flip_core.contracts import ContractError
from flip_core.execution import evaluate
from flip_core.import_models import ImportResult
from flip_core.importer import sha
from flip_core.isolation import run_worker
from flip_core.models import (
    BitVector,
    ComparisonReport,
    Contract,
    Digest,
    Integrity,
    Project,
    Proof,
    Witness,
)


class VerificationRequest(Contract):
    schemaVersion: Literal["m3-1.0.0"]
    kind: Literal["M3_EXECUTION"]
    project: Annotated[Project | LocalProject, Field(discriminator="schemaVersion")]
    imports: Annotated[list[ImportResult], Field(min_length=1, max_length=1251)]
    relation: Literal["REFERENCE", "PREVIOUS_VERSION", "BEHAVIORAL"]

    @model_validator(mode="after")
    def aggregate_import_budget(self):
        members = sum(len(i.circuits) for i in self.imports)
        size = sum(len(c.netlist[2:]) // 2 for i in self.imports for c in i.circuits)
        if members > 1251 or size > 1_000_000:
            raise ValueError("aggregate execution import budget exceeded")
        return self


class ExpectedVector(Contract):
    inputs: BitVector
    outputs: BitVector


class VectorRequest(VerificationRequest):
    vectors: Annotated[list[ExpectedVector], Field(min_length=1, max_length=4096)]


class ConsumptionRequest(Contract):
    schemaVersion: Literal["m3-1.0.0"]
    kind: Literal["M3_CONSUMPTION"]
    executionRequest: VerificationRequest
    claimedResult: dict
    expectedProjectHash: Digest
    expectedReferenceHash: Digest


def parse_request(raw, *, vectors=False):
    try:
        value = load_json(raw) if isinstance(raw, (str, bytes)) else raw
        return (VectorRequest if vectors else VerificationRequest).model_validate(value)
    except (ValidationError, ValueError, TypeError, RecursionError) as exc:
        raise ContractError(
            "INVALID_INPUT", "Invalid M3 request; source widths/maps must be explicit."
        ) from exc


def engine_identity():
    files = (
        "execution.py",
        "composition.py",
        "cnf.py",
        "verification.py",
        "isolation.py",
        "solver_worker.py",
        "tap02.py",
        "importer.py",
        "models.py",
        "import_models.py",
        "canonical.py",
        "composition_models.py",
        "abi.py",
    )
    # Include native implementation bytes, not only a caller's version label.
    import pysat.solvers
    import pysolvers

    return {
        "profile": "flip-m3-engine-v1",
        "sources": {name: sha(Path(__file__).with_name(name).read_bytes()) for name in files},
        "pythonSatVersion": version("python-sat"),
        "pythonVersion": python_version(),
        "solverWrapperHash": sha(Path(pysat.solvers.__file__).read_bytes()),
        "nativeSolverHash": sha(Path(pysolvers.__file__).read_bytes()),
    }


def compose(request: VerificationRequest):
    request = parse_request(request.model_dump(mode="json"))
    composition = compile_project(request.project, request.imports)
    return {
        "schemaVersion": "m3-1.0.0",
        "kind": "COMPOSITION_RESULT",
        "projectHash": content_hash(request.project),
        "candidateIdentity": {
            "kind": "LOCAL_COMPOSITION",
            "netlistHash": composition.manifest["netlistHash"],
        },
        "netlist": "0x" + composition.candidate.decoded.original.hex(),
        "manifest": composition.manifest,
        "manifestHash": content_hash(composition.manifest),
    }


def mapped_outputs(composition, bits):
    plan = composition.project.comparison
    a = evaluate(composition.reference, [bits[i] for i in plan.inputMap])
    b = evaluate(composition.candidate, bits)
    return a, [b[i] for i in plan.outputMap]


def bitvector(bits):
    return BitVector(encoding="tap02-lsb0-v1", width=len(bits), bits="".join(map(str, bits)))


def compare(request: VerificationRequest):
    request = parse_request(request.model_dump(mode="json"))
    if (request.relation == "BEHAVIORAL") != (request.project.comparison.intent == "UNDECLARED"):
        raise ContractError(
            "INVALID_INPUT",
            "Behavioral relation requires undeclared intent; "
            "reference/version requires a trust assertion.",
        )
    start = monotonic()
    composition = compile_project(request.project, request.imports)
    project, plan = composition.project, composition.project.comparison
    if composition.local_reference_manifest is not None:
        reference_manifest = composition.local_reference_manifest
        reference_hash = content_hash(reference_manifest)
        reference_identity = {
            "kind": "LOCAL_COMPOSITION",
            "netlistHash": reference_manifest["netlistHash"],
        }
        semantics = request.imports[0].manifest.semantics
    else:
        reference_import = composition.imports[plan.referenceAlias]
        reference_manifest = reference_import.manifest.model_dump(mode="json")
        reference_hash = reference_import.manifestHash
        reference_identity = reference_import.manifest.root.identity.model_dump(mode="json")
        semantics = reference_import.manifest.semantics
    enc, inputs = miter(composition.reference, composition.candidate, plan.inputMap, plan.outputMap)
    solver = run_worker(enc.clauses, inputs, project.limits)
    outcome = solver["outcome"]
    witness = None
    reason = solver.get("reason")
    verdict = "UNKNOWN"
    if outcome == "UNSAT":
        verdict = "EQUIVALENT"
    elif outcome == "SAT":
        bits = solver["witness"]
        a, b = mapped_outputs(composition, bits)
        if a == b:
            reason = "WITNESS_REPLAY_FAILED"
        else:
            verdict = "DIFFERENT"
            witness = Witness(
                inputs=bitvector(bits),
                referenceOutputs=bitvector(a),
                candidateOutputs=bitvector(b),
                replay="REF_BEAT_REPRODUCED",
                minimization="HEURISTIC",
            )
    report = ComparisonReport(
        schemaVersion="1.0.0",
        chainId=196,
        projectHash=content_hash(project),
        referenceManifestHash=reference_hash,
        candidateManifestHash=content_hash(composition.manifest),
        toolVersion="0.1.0",
        semantics=semantics,
        limits=project.limits,
        verification=Proof(
            kind="PAIRWISE_EQUIVALENCE",
            verdict=verdict,
            reasonCode=reason,
            solverBackend="Minisat22",
            solverOutcome=outcome,
            referenceNState=composition.reference.state_width,
            candidateNState=0,
            sourceValidation="PASSED",
            mappingValidation="PASSED",
            witness=witness,
        ),
        intent=plan.intent,
        trustAssertion=plan.trustAssertion,
        inputMap=plan.inputMap,
        outputMap=plan.outputMap,
        integrity=Integrity(
            freshness="STALE"
            if any(i.integrity.freshness == "STALE" for i in request.imports)
            else "HISTORICAL",
            checkedBlock=None,
        ),
    )
    # Cached import flags cannot grant freshness. Local composition has no onchain ID.
    engine = engine_identity()
    return {
        "schemaVersion": "m3-1.0.0",
        "kind": "TRUSTED_LOCAL_COMPARISON",
        "report": report.model_dump(mode="json"),
        "referenceIdentity": reference_identity,
        "candidateIdentity": {
            "kind": "LOCAL_COMPOSITION",
            "netlistHash": composition.manifest["netlistHash"],
        },
        "referenceManifest": reference_manifest,
        "candidateManifest": composition.manifest,
        "engine": engine,
        "engineHash": content_hash(engine),
        "relation": request.relation,
        "coverage": "EXACT_STATELESS_PAIRWISE" if verdict != "UNKNOWN" else "INCONCLUSIVE",
        "correctness": "USER_DECLARED_REFERENCE_RELATIVE"
        if plan.intent == "TRUSTED_REFERENCE"
        else "INTENT_UNKNOWN",
        "resources": {
            "referenceGates": composition.reference.gates,
            "candidateGates": composition.candidate.gates,
            "variables": enc.variables,
            "clauses": len(enc.clauses),
            **solver,
            "totalMs": int((monotonic() - start) * 1000),
        },
        "verifiedAt": datetime.now(UTC).isoformat(),
        "context": "LOCAL_OFFLINE_REPLAY_SINGLE_RPC_ASSERTIONS_NOT_REVALIDATED",
        "reproduction": request.model_dump(mode="json"),
        "requestHash": content_hash(request),
    }


def consume(
    request: VerificationRequest,
    untrusted: dict,
    *,
    expected_project_hash: str,
    expected_reference_hash: str,
):
    """Trusted caller pins project/reference; recompute, never promote serialized flags.

    Even UNSAT is rerun. A portable report is evidence to reproduce, not a signed
    certificate. DIFFERENT witnesses are independently replayed before acceptance.
    """
    request = parse_request(request.model_dump(mode="json"))
    if content_hash(request.project) != expected_project_hash:
        raise ContractError("INVALID_INPUT", "Project differs from consumer's pinned project.")
    try:
        claim = ComparisonReport.model_validate(untrusted["report"])
        if (
            claim.referenceManifestHash != expected_reference_hash
            or claim.projectHash != expected_project_hash
        ):
            raise ContractError(
                "INVALID_INPUT", "Report differs from consumer's pinned identities."
            )
        actual = compare(request)
        for name in (
            "referenceIdentity",
            "candidateIdentity",
            "referenceManifest",
            "candidateManifest",
            "engine",
            "engineHash",
            "relation",
            "requestHash",
            "reproduction",
            "context",
        ):
            if untrusted.get(name) != actual[name]:
                raise ContractError(
                    "IMPLEMENTATION_CHANGED", "Proof binding or execution implementation changed."
                )
        expected = ComparisonReport.model_validate(actual["report"])
        if expected.referenceManifestHash != expected_reference_hash:
            raise ContractError("INVALID_INPUT", "Substituted reference manifest.")
        if claim.verification.verdict == "DIFFERENT":
            composition = compile_project(request.project, request.imports)
            w = claim.verification.witness
            a, b = mapped_outputs(composition, [int(bit) for bit in w.inputs.bits])
            if a == b or bitvector(a) != w.referenceOutputs or bitvector(b) != w.candidateOutputs:
                raise ContractError(
                    "WITNESS_REPLAY_FAILED", "Serialized witness failed independent replay."
                )
        # Compare all frozen report fields; witness minimization may be solver dependent.
        old, new = claim.model_dump(mode="json"), expected.model_dump(mode="json")
        old["verification"]["witness"] = new["verification"]["witness"]
        if old != new or expected.verification.verdict == "UNKNOWN":
            raise ContractError(
                "INVALID_INPUT", "Recomputed proof does not validate the claimed result."
            )
        return actual
    except (KeyError, TypeError, ValidationError) as exc:
        raise ContractError("INVALID_INPUT", "Untrusted report is incomplete or invalid.") from exc


def check_vectors(request: VectorRequest):
    start = monotonic()
    request = VectorRequest.model_validate(request.model_dump(mode="json"))
    composition = compile_project(request.project, request.imports)
    n_in, n_out = composition.candidate.decoded.n_in, composition.candidate.decoded.n_out
    seen, mismatches = set(), []
    deadline = monotonic() + 5
    # Bound aggregate work as well as the number of rows.
    from flip_core.execution import execution_cost

    if execution_cost(composition.candidate) * len(request.vectors) > 2_000_000:
        raise ContractError("RESOURCE_LIMIT", "Vector evaluation work budget exceeded.")
    for vector in request.vectors:
        if monotonic() > deadline:
            raise ContractError("RESOURCE_LIMIT", "Vector evaluation deadline exceeded.")
        if (
            vector.inputs.width != n_in
            or vector.outputs.width != n_out
            or vector.inputs.bits in seen
        ):
            raise ContractError(
                "MISSING_MAPPING", "Vector widths or duplicate input domain are invalid."
            )
        seen.add(vector.inputs.bits)
        actual = bitvector(evaluate(composition.candidate, [int(b) for b in vector.inputs.bits]))
        if actual != vector.outputs:
            mismatches.append(
                {
                    "inputs": vector.inputs.model_dump(mode="json"),
                    "expected": vector.outputs.model_dump(mode="json"),
                    "actual": actual.model_dump(mode="json"),
                }
            )
    oracle_hash = content_hash([v.model_dump(mode="json") for v in request.vectors])
    engine = engine_identity()
    return {
        "schemaVersion": "m3-1.0.0",
        "kind": "USER_VECTOR_RESULT",
        "verdict": "VECTORS_MISMATCH" if mismatches else "VECTORS_MATCH",
        "intent": "USER_VECTORS",
        "rows": len(seen),
        "coverage": "EXHAUSTIVE_DECLARED_DOMAIN"
        if n_in <= 12 and len(seen) == 2**n_in
        else "PARTIAL_DECLARED_DOMAIN",
        "mismatches": mismatches,
        "projectHash": content_hash(request.project),
        "candidateManifest": composition.manifest,
        "freshness": "STALE"
        if any(i.integrity.freshness == "STALE" for i in request.imports)
        else "HISTORICAL",
        "oracleHash": oracle_hash,
        "referenceIdentity": {"kind": "USER_VECTORS", "oracleHash": oracle_hash},
        "candidateIdentity": {
            "kind": "LOCAL_COMPOSITION",
            "netlistHash": composition.manifest["netlistHash"],
        },
        "solver": {"backend": "NONE", "outcome": "NOT_RUN"},
        "resources": {
            "candidateGates": composition.candidate.gates,
            "workUnits": execution_cost(composition.candidate) * len(request.vectors),
            "totalMs": int((monotonic() - start) * 1000),
        },
        "verifiedAt": datetime.now(UTC).isoformat(),
        "context": "LOCAL_OFFLINE_USER_VECTORS_NOT_CHAIN_REVALIDATED",
        "engine": engine,
        "engineHash": content_hash(engine),
        "reproduction": request.model_dump(mode="json"),
        "requestHash": content_hash(request),
    }


def execute(operation, raw):
    if operation == "consume":
        try:
            value = load_json(raw) if isinstance(raw, (str, bytes)) else raw
            request = ConsumptionRequest.model_validate(value)
        except (ValidationError, ValueError, TypeError, RecursionError) as exc:
            raise ContractError("INVALID_INPUT", "Invalid proof consumption request.") from exc
        return consume(
            request.executionRequest,
            request.claimedResult,
            expected_project_hash=request.expectedProjectHash,
            expected_reference_hash=request.expectedReferenceHash,
        )
    request = parse_request(raw, vectors=operation == "vectors")
    try:
        return {"compose": compose, "compare": compare, "vectors": check_vectors}[operation](
            request
        )
    except ValidationError as exc:
        raise ContractError("INVALID_INPUT", "Invalid project or imported evidence.") from exc
