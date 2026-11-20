"""Additive portable-to-agent boundary. Revision integrity is never permission or proof."""

from copy import deepcopy
from pathlib import Path
from time import monotonic
from typing import Literal

from pydantic import Field, model_validator

from flip_core import agent_workflow
from flip_core.agent_models import Status, WorkflowRequest, WorkflowResult
from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.composition import compile_project
from flip_core.contracts import ContractError
from flip_core.execution import execution_cost
from flip_core.models import Contract, Digest
from flip_core.portable import create_package, parse_package, record_hash, require_executable
from flip_core.verification import parse_request

VERSION = "m45-agent-portable-1.0.0"
ALLOWED = {
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
}


class AgentPortableRequest(Contract):
    schemaVersion: Literal["m45-agent-portable-1.0.0"] = VERSION
    kind: Literal["AGENT_PORTABLE_REQUEST"] = "AGENT_PORTABLE_REQUEST"
    package: dict
    expectedPackageHash: Digest
    expectedRevisionHash: Digest
    expectedExecutionRequestHash: Digest
    workflow: WorkflowRequest
    createRevision: bool
    runNamedTests: bool = True
    continueOnTestMismatch: bool = False
    continueOnEvidenceDifference: bool = False
    purpose: Literal["LOCAL", "PUBLISH", "DEPLOY"] = "LOCAL"
    evidenceArtifacts: dict[str, dict] = Field(default_factory=dict, max_length=128)

    @model_validator(mode="after")
    def bindings(self):
        package = parse_package(self.package)
        if (
            content_hash(self.package) != self.expectedPackageHash
            or package.revision.revisionHash != self.expectedRevisionHash
            or package.executionRequestHash != self.expectedExecutionRequestHash
        ):
            raise ValueError("Selected package, revision or execution identity changed")
        if self.workflow.executionRequest is not None:
            raise ValueError("Execution comes only from the selected portable package")
        if (
            self.createRevision
            and package.tests
            and not self.runNamedTests
            and self.purpose == "LOCAL"
        ):
            raise ValueError("Revision creation must evaluate every declared named test set")
        for step in self.workflow.steps:
            if step.id.startswith("pp_") or step.op not in ALLOWED:
                raise ValueError("Reserved ID or project-replacing operation in portable workflow")
            if step.op in ("build", "revalidate") and step.source is not None:
                raise ValueError(
                    "Cannot select a foreign import or manifest as the current project"
                )
        if set(self.evidenceArtifacts) - {r.digest for r in package.evidenceRefs}:
            raise ValueError("Unselected evidence artifact")
        return self


class AgentPortableResult(Contract):
    schemaVersion: Literal["m45-agent-portable-1.0.0"]
    kind: Literal["AGENT_PORTABLE_RESULT"]
    status: Status
    originalPackage: dict
    revisedPackage: dict | None
    revisionCreated: bool
    receipt: WorkflowResult | None
    evidenceArtifacts: dict[str, dict]
    inputEvidence: list[dict[str, str]]
    requestHash: Digest
    adapterHash: Digest
    reproductionHash: Digest
    resultHash: Digest
    error: dict[str, str] | None
    trust: Literal["LOCAL_BOUNDED_HISTORICAL_REFERENCE_RELATIVE"]


def parse_adapter(raw):
    try:
        data = load_json(raw) if isinstance(raw, (str, bytes)) else raw
        encoded = canonical_bytes(data)
        if len(encoded) > 1048576:
            raise ContractError("RESOURCE_LIMIT", "Portable workflow exceeds 1 MiB.")
        data = load_json(encoded)  # isolate caller-owned mutable objects before pin validation
        if isinstance(data, dict):
            if data.get("schemaVersion", VERSION) != VERSION:
                raise ContractError("UNSUPPORTED_SCHEMA_VERSION", "Unsupported adapter version.")
            if (
                isinstance(data.get("package"), dict)
                and data["package"].get("schemaVersion") != "flip-portable-project-1.1.0"
            ):
                raise ContractError(
                    "UNSUPPORTED_SCHEMA_VERSION", "Unsupported portable package version."
                )
        return AgentPortableRequest.model_validate(data)
    except ContractError:
        raise
    except (ValueError, TypeError, RecursionError) as exc:
        raise ContractError(
            "INVALID_INPUT", "Invalid portable workflow or exact input bindings."
        ) from exc


def raw_candidate(original, normalized):
    """Change only candidate wiring, preserving original sparse request representation."""
    before = parse_request(original).model_dump(mode="json")
    after = parse_request(normalized).model_dump(mode="json")
    before["project"]["candidate"] = after["project"]["candidate"]
    if before != after:
        raise ContractError(
            "INVALID_INPUT", "Workflow substituted project/reference/import/intent bindings."
        )
    if parse_request(original).model_dump(mode="json") == after:
        return deepcopy(original)
    result = deepcopy(original)
    result["project"]["candidate"] = after["project"]["candidate"]
    if parse_request(result).model_dump(mode="json") != after:
        raise ContractError(
            "INVALID_INPUT", "Candidate cannot preserve the embedded execution request."
        )
    return result


def prepare(model, package, boundary):
    raw = deepcopy(package.executionRequest)
    request = parse_request(raw)
    require_executable(package)
    if model.purpose != "LOCAL":
        workflow = model.workflow.model_dump(mode="json")
        workflow["executionRequest"] = raw
        workflow["steps"] = [
            dict(id="pp_authorization", op="stop_authorization"),
            *workflow["steps"],
        ]
        if len(workflow["steps"]) > 64:
            raise ContractError("RESOURCE_LIMIT", "Publication handoff exceeds 64 steps.")
        return workflow, []
    cost = execution_cost(compile_project(request.project, request.imports).candidate)
    costs = [cost]
    if model.createRevision and package.tests:
        candidates = [
            s.candidate.model_dump(mode="json") for s in model.workflow.steps if s.candidate
        ]
        if hasattr(request.project, "referenceCandidate"):
            candidates.append(request.project.referenceCandidate.model_dump(mode="json"))
        for candidate in candidates:
            boundary()
            revised = deepcopy(raw)
            revised["project"]["candidate"] = candidate
            r = parse_request(revised)
            costs.append(execution_cost(compile_project(r.project, r.imports).candidate))
    rows = sum(len(t.vectors) for t in package.tests) if model.runNamedTests else 0
    passes = 2 if model.createRevision else 1
    if max(costs) * rows * passes > 2_000_000:
        raise ContractError("RESOURCE_LIMIT", "Aggregate portable named-test work budget exceeded.")
    workflow = model.workflow.model_dump(mode="json")
    steps = workflow["steps"]
    availability = []
    if model.purpose != "LOCAL":
        steps = [dict(id="pp_authorization", op="stop_authorization"), *steps]
    else:
        prefix = []
        for i, ref in enumerate(package.evidenceRefs):
            artifact = model.evidenceArtifacts.get(ref.digest)
            availability.append(
                {
                    "digest": ref.digest,
                    "status": "MISSING_EVIDENCE" if artifact is None else "SCHEDULED_REPLAY",
                }
            )
            if artifact is None:
                continue
            if (
                artifact.get("contentHash") != ref.digest
                or content_hash({k: v for k, v in artifact.items() if k != "contentHash"})
                != ref.digest
                or artifact.get("reproduce") != ref.reproduce
                or not isinstance(artifact.get("comparison"), dict)
                or artifact["comparison"].get("engineHash") != ref.engineHash
            ):
                raise ContractError(
                    "INVALID_INPUT", "Evidence identity does not match the selected reference."
                )
            prefix.append(
                dict(
                    id=f"pp_evidence{i}",
                    op="verify_bundle",
                    bundle=artifact,
                    continueOn=["DIFFERENT"] if model.continueOnEvidenceDifference else [],
                )
            )

        def tests(phase, continue_mismatch=False):
            return [
                dict(
                    id=f"pp_{phase}{i}",
                    op="test",
                    vectors=[v.model_dump(mode="json") for v in test.vectors],
                    continueOn=["DIFFERENT"] if continue_mismatch else [],
                )
                for i, test in enumerate(package.tests)
            ]

        if model.runNamedTests:
            prefix.extend(tests("before", model.continueOnTestMismatch))
        steps = [*prefix, *steps]
        if model.createRevision:
            if model.runNamedTests:
                steps.extend(tests("after"))
            steps.append(dict(id="pp_export", op="export"))
    if len(steps) > 64:
        raise ContractError(
            "RESOURCE_LIMIT", "Expanded named tests/evidence/workflow exceed 64 steps."
        )
    workflow["steps"], workflow["executionRequest"] = steps, raw
    return workflow, availability


def execute(raw, *, settings=None, cancelled=None):
    """One controller invocation, one shared budget, explicit final revision commit."""
    start = monotonic()
    model = parse_adapter(raw)
    cancelled = cancelled or (lambda: False)
    package = parse_package(model.package)
    original = deepcopy(model.package)
    deadline = model.workflow.budget.deadlineMs
    request_hash = content_hash(model)
    from flip_core.importer import sha

    adapter_hash = content_hash(
        {
            name: sha(Path(__file__).with_name(name).read_bytes())
            for name in ("agent_portable_adapter.py", "portable.py")
        }
    )
    receipt, revised, artifacts, evidence = None, None, {}, []
    status, error = "PREPARED", None

    def boundary():
        if cancelled():
            raise ContractError("RESOURCE_LIMIT", "CANCELLED")
        if (monotonic() - start) * 1000 >= deadline:
            raise ContractError("RESOURCE_LIMIT", "ADAPTER_DEADLINE")

    def response():
        result = dict(
            schemaVersion=VERSION,
            kind="AGENT_PORTABLE_RESULT",
            status=status,
            originalPackage=original,
            revisedPackage=revised,
            revisionCreated=revised is not None,
            receipt=receipt,
            evidenceArtifacts=artifacts,
            inputEvidence=evidence,
            requestHash=request_hash,
            adapterHash=adapter_hash,
            error=error,
            trust="LOCAL_BOUNDED_HISTORICAL_REFERENCE_RELATIVE",
        )
        result["reproductionHash"] = content_hash(
            dict(
                requestHash=request_hash,
                adapterHash=adapter_hash,
                workflowReproductionHash=receipt.get("reproductionHash") if receipt else None,
                status=status,
                originalRevisionHash=package.revision.revisionHash,
                finalExecutionHash=revised["executionRequestHash"] if revised else None,
                edits=revised["revision"]["editLog"] if revised else [],
            )
        )
        result["resultHash"] = content_hash(result)
        return AgentPortableResult.model_validate(result).model_dump(mode="json")

    if len(canonical_bytes(original)) + 4096 > model.workflow.budget.maxReceiptBytes:
        raise ContractError(
            "RESOURCE_LIMIT", "Result budget cannot preserve the selected original package."
        )
    try:
        boundary()
        workflow, evidence = prepare(model, package, boundary)
        boundary()
        receipt = agent_workflow.execute(
            workflow,
            settings=settings,
            cancelled=lambda: cancelled() or (monotonic() - start) * 1000 >= deadline,
        ).model_dump(mode="json")
        status = receipt["status"]
        if receipt["error"]:
            error = {k: receipt["error"][k] for k in ("code", "message")}
        for item in evidence:
            if item["status"] == "SCHEDULED_REPLAY":
                ref_index = next(
                    i for i, r in enumerate(package.evidenceRefs) if r.digest == item["digest"]
                )
                event = next(
                    (e for e in receipt["logs"] if e["step"] == f"pp_evidence{ref_index}"), None
                )
                item["status"] = (
                    "REPLAYED"
                    if event and event["status"] in ("COMPLETE", "DIFFERENT")
                    else "NOT_REPLAYED"
                )
        if status != "STOP_AUTHORIZATION":
            boundary()
        if status == "COMPLETE" and model.createRevision:
            # stopOn or an early exit cannot bypass post-tests and the fresh trusted export.
            event = receipt["logs"][-1] if receipt["logs"] else None
            if not event or event["step"] != "pp_export" or event["status"] != "COMPLETE":
                raise ContractError(
                    "INVALID_INPUT", "Required final verification/export was not completed."
                )
            final = raw_candidate(package.executionRequest, receipt["executionRequest"])
            normalized_hash = content_hash(parse_request(final))
            output = event["output"]
            if (
                output.get("kind") != "FLIP_EVIDENCE"
                or output["comparison"]["requestHash"] != normalized_hash
                or output["comparison"]["report"]["verification"]["verdict"] != "EQUIVALENT"
            ):
                raise ContractError("INVALID_INPUT", "Final revision lacks its trusted comparison.")
            edits, current = [], deepcopy(package.executionRequest)
            for log in receipt["logs"]:
                if log["op"] == "apply" and log["status"] == "COMPLETE":
                    value = log["output"]
                    if value.get("classification") != "VERIFIED_CORRECTION":
                        raise ContractError(
                            "INVALID_INPUT", "Apply did not independently verify its candidate."
                        )
                    target = raw_candidate(current, value["proposal"]["proposedRevision"])
                    edits.append(
                        dict(
                            beforeHash=content_hash(current),
                            afterHash=content_hash(target),
                            description=(
                                f"Apply {log['step']} action {value['proposal']['actionId']}"
                            ),
                        )
                    )
                    current = target
            if current != final:
                raise ContractError(
                    "INVALID_INPUT", "Revision changed without an explicit verified apply."
                )
            refs = []
            for log in receipt["logs"]:
                b = log["output"]
                if log["op"] != "export" or log["status"] != "COMPLETE" or not b:
                    continue
                if b["comparison"]["requestHash"] != normalized_hash:
                    continue
                digest = b["contentHash"]
                if content_hash({k: v for k, v in b.items() if k != "contentHash"}) != digest:
                    raise ContractError("INVALID_INPUT", "Trusted export checksum mismatch.")
                if digest not in artifacts:
                    refs.append(
                        dict(
                            kind="FLIP_EVIDENCE",
                            digest=digest,
                            executionRequestHash=content_hash(final),
                            reproduce=b["reproduce"],
                            engineHash=b["comparison"]["engineHash"],
                        )
                    )
                    artifacts[digest] = b
            boundary()
            revised = create_package(
                final,
                previous=original,
                evidence_refs=refs,
                agent_task_ref=receipt["requestHash"],
                description="Verified portable workflow revision",
            )
            if edits:
                revised["revision"]["editLog"] = edits
                revised["revision"]["revisionHash"] = record_hash(revised["revision"])
            parse_package(revised)
            if len(canonical_bytes(revised)) > 1048576:
                raise ContractError("RESOURCE_LIMIT", "New portable package exceeds 1 MiB.")
            boundary()  # cancellation wins even after hashing the candidate revision
    except ContractError as exc:
        revised, artifacts = None, {}
        status = (
            "CANCELLED"
            if exc.message == "CANCELLED"
            else "BUDGET_EXHAUSTED"
            if exc.code == "RESOURCE_LIMIT"
            else "STALE"
            if exc.code == "IMPLEMENTATION_CHANGED"
            else "INVALID_INPUT"
        )
        error = dict(code=exc.code, message=exc.message)
    result = response()
    if len(canonical_bytes(result)) > model.workflow.budget.maxReceiptBytes:
        revised, artifacts, receipt = None, {}, None
        status, error = (
            "BUDGET_EXHAUSTED",
            dict(
                code="RESOURCE_LIMIT",
                message="Adapter result exceeds receipt budget; no revision returned.",
            ),
        )
        result = response()
        if len(canonical_bytes(result)) > model.workflow.budget.maxReceiptBytes:
            evidence = []
            error = dict(
                code="RESOURCE_LIMIT",
                message="Result budget exceeded; diagnostics omitted; original retained.",
            )
            result = response()
    if revised is not None and (cancelled() or (monotonic() - start) * 1000 >= deadline):
        revised, artifacts = None, {}
        status = "CANCELLED" if cancelled() else "BUDGET_EXHAUSTED"
        error = dict(
            code="RESOURCE_LIMIT", message="Revision publication cancelled or deadline exhausted."
        )
        result = response()
    return result


class PreparationRequest(Contract):
    schemaVersion: Literal["m45-agent-portable-1.0.0"] = VERSION
    kind: Literal["AGENT_PORTABLE_PREPARATION"] = "AGENT_PORTABLE_PREPARATION"
    package: dict
    action: Literal["inspect", "correct", "verify-edit", "publish"]
    draftExecutionRequest: dict | None = None
    continueOnTestMismatch: bool = False


def prepare_adapter(raw):
    """Hash/plan preparation only; no verification or authority is created here."""
    try:
        value = load_json(raw) if isinstance(raw, (str, bytes)) else raw
        encoded = canonical_bytes(value)
        if len(encoded) > 1048576:
            raise ContractError("RESOURCE_LIMIT", "Preparation exceeds 1 MiB.")
        value = load_json(encoded)
        model = PreparationRequest.model_validate(value)
        package = parse_package(model.package)
        request = parse_request(package.executionRequest)
        normalized = request.model_dump(mode="json")
        expected = content_hash(request)
        if model.action in ("correct", "verify-edit"):
            if model.action == "correct":
                if not hasattr(request.project, "referenceCandidate"):
                    raise ContractError("INVALID_INPUT", "No declared local reference candidate.")
                target = deepcopy(normalized)
                target["project"]["candidate"] = request.project.referenceCandidate.model_dump(
                    mode="json"
                )
            else:
                if model.draftExecutionRequest is None:
                    raise ContractError("INVALID_INPUT", "Select the current explicit draft.")
                raw_candidate(package.executionRequest, model.draftExecutionRequest)
                target = parse_request(model.draftExecutionRequest).model_dump(mode="json")
            action_id = content_hash(dict(original=expected, revision=content_hash(target)))
            steps = [
                dict(id="compare", op="compare", continueOn=["DIFFERENT"]),
                dict(id="inspect", op="inspect", continueOn=["DIFFERENT"]),
                dict(
                    id="propose",
                    op="propose_correction",
                    candidate=target["project"]["candidate"],
                    expectedExecutionHash=expected,
                ),
                dict(
                    id="verify",
                    op="verify",
                    source="propose",
                    expectedExecutionHash=expected,
                    actionId=action_id,
                ),
                dict(
                    id="apply",
                    op="apply",
                    source="verify",
                    expectedExecutionHash=expected,
                    actionId=action_id,
                ),
            ]
        elif model.action == "publish":
            steps = [dict(id="queuedExport", op="export")]
        else:
            steps = [
                dict(id="compare", op="compare", continueOn=["DIFFERENT"]),
                dict(id="inspect", op="inspect"),
            ]
        prepared = AgentPortableRequest(
            package=model.package,
            expectedPackageHash=content_hash(model.package),
            expectedRevisionHash=package.revision.revisionHash,
            expectedExecutionRequestHash=package.executionRequestHash,
            workflow=WorkflowRequest(steps=steps),
            createRevision=model.action in ("correct", "verify-edit"),
            continueOnTestMismatch=model.continueOnTestMismatch,
            purpose="PUBLISH" if model.action == "publish" else "LOCAL",
        )
        return dict(
            request=prepared.model_dump(mode="json"), trust="UNVERIFIED_PLAN_AND_IDENTITIES_ONLY"
        )
    except ContractError:
        raise
    except (ValueError, TypeError, RecursionError) as exc:
        raise ContractError("INVALID_INPUT", "Invalid portable workflow preparation.") from exc
