"""Fixed dispatch to accepted services. No external code, reports or permissions execute."""

from copy import deepcopy

import httpx

from flip_core.agent_models import WorkflowStep
from flip_core.canonical import content_hash
from flip_core.composition import compile_project
from flip_core.contracts import ContractError
from flip_core.debugging import execute as debug
from flip_core.import_models import ImportBudget, ImportResult
from flip_core.importer import ImportService
from flip_core.library import LibraryService
from flip_core.models import ComparisonReport, Manifest
from flip_core.rpc import RpcSettings
from flip_core.verification import check_vectors, compare, compose, parse_request
from flip_core.workflow import VERSION, product, project_from_import, sample


class MeteredTransport(httpx.BaseTransport):
    def __init__(self, limit):
        self.inner = httpx.HTTPTransport(retries=0)
        self.calls, self.limit = 0, limit

    def handle_request(self, request):
        if self.calls >= self.limit:
            raise ContractError("RESOURCE_LIMIT", "Aggregate RPC budget exhausted.")
        self.calls += 1
        return self.inner.handle_request(request)

    # Each service owns a Client, but this shared meter belongs to the operation.
    def close(self):
        pass


def bound_execution(raw, step):
    if raw is None:
        raise ContractError("MISSING_REFERENCE", "Select an execution request before this step.")
    request = parse_request(raw)
    if step.expectedExecutionHash and content_hash(request) != step.expectedExecutionHash:
        raise ContractError("IMPLEMENTATION_CHANGED", "The exact original project changed.")
    if any(i.integrity.freshness not in ("CURRENT", "HISTORICAL") for i in request.imports):
        raise ContractError("IMPLEMENTATION_CHANGED", "Reimport stale or unverified sources.")
    return request


def proposal(request, step):
    if request.project.comparison.intent != "TRUSTED_REFERENCE" or request.relation == "BEHAVIORAL":
        raise ContractError(
            "MISSING_REFERENCE", "Corrections require an explicit trusted reference."
        )
    if step.candidate is None:
        result = debug(
            dict(
                schemaVersion="m45-debugging-1.0.0",
                kind="DEBUG_REQUEST",
                executionRequest=request.model_dump(mode="json"),
                budget=step.budget.trace.model_dump(mode="json"),
            )
        )
        if result.classification == "UNKNOWN":
            raise ContractError(
                "RESOURCE_LIMIT" if result.reasonCode is None else result.reasonCode,
                "No bounded correction proposal is available.",
            )
        if not result.actions:
            raise ContractError("MISSING_REFERENCE", "No declared-prior mapping proposal exists.")
        action = result.actions[0].model_dump(mode="json")
        if step.actionId is not None and step.actionId != action["actionId"]:
            raise ContractError("INVALID_INPUT", "Substituted correction action identifier.")
    else:
        revised = request.model_dump(mode="json")
        revised["project"]["candidate"] = step.candidate.model_dump(mode="json")
        revised = parse_request(revised)
        compile_project(revised.project, revised.imports)
        action = dict(
            actionId=content_hash(
                {"original": content_hash(request), "revision": content_hash(revised)}
            ),
            proposedRevision=revised.model_dump(mode="json"),
        )
    return dict(
        **{k: v for k, v in action.items() if k != "classification"},
        kind="WORKFLOW_CANDIDATE",
        classification="CANDIDATE_ACTION",
        originalExecutionHash=content_hash(request),
        originalProjectHash=content_hash(request.project),
    )


def verify_proposal(request, step, source):
    if not isinstance(source, dict) or source.get("kind") != "WORKFLOW_CANDIDATE":
        raise ContractError("INVALID_INPUT", "Select a proposal created in this workflow.")
    revised = parse_request(source.get("proposedRevision"))
    if (
        source.get("originalExecutionHash") != content_hash(request)
        or source.get("originalProjectHash") != content_hash(request.project)
        or step.actionId != source.get("actionId")
        or step.actionId
        != content_hash({"original": content_hash(request), "revision": content_hash(revised)})
    ):
        raise ContractError("IMPLEMENTATION_CHANGED", "Correction is not bound to this project.")
    # Only the candidate may change. Reference, identities, limits and declared intent are fixed.
    a, b = request.model_dump(mode="json"), revised.model_dump(mode="json")
    a["project"]["candidate"] = b["project"]["candidate"]
    if a != b or request.project.comparison.intent != "TRUSTED_REFERENCE":
        raise ContractError("INVALID_INPUT", "Correction substituted its reference or bindings.")
    checked = compare(revised)
    verdict = checked["report"]["verification"]["verdict"]
    return dict(
        kind="WORKFLOW_CORRECTION",
        classification=(
            "VERIFIED_CORRECTION"
            if verdict == "EQUIVALENT"
            else "UNKNOWN"
            if verdict == "UNKNOWN"
            else "CANDIDATE_ACTION"
        ),
        proposal=source,
        comparison=checked,
        originalExecutionHash=content_hash(request),
        revisedExecutionHash=content_hash(revised),
    )


def run_operation(payload, transport):
    step = WorkflowStep.model_validate(payload["step"])
    op, raw, source = step.op, payload["executionRequest"], payload["source"]
    settings = RpcSettings(**payload["settings"])
    budget = step.budget.imports.model_dump(mode="json")
    budget["maxRequests"] = max(1, min(budget["maxRequests"], payload["rpcLimit"]))
    budget["deadlineMs"] = min(budget["deadlineMs"], step.budget.deadlineMs)
    imports = ImportService(settings, ImportBudget(**budget), transport=transport)
    execution = None
    if op == "sample":
        value = sample(step.variant)
        execution = value
    elif op == "discover":
        value = (
            LibraryService(settings, ImportBudget(**budget), transport=transport)
            .execute(step.libraryRequest)
            .model_dump(mode="json")
        )
    elif op == "import":
        value = imports.import_circuit(step.identity, step.blockNumber).model_dump(mode="json")
    elif op == "revalidate":
        manifests = (
            [Manifest.model_validate(source["manifest"])]
            if source
            else [item.manifest for item in bound_execution(raw, step).imports]
        )
        observations = [
            imports.revalidate(manifest).model_dump(mode="json") for manifest in manifests
        ]
        value = dict(
            kind="WORKFLOW_REVALIDATION",
            observations=observations,
            freshness="STALE"
            if any(x["integrity"]["freshness"] == "STALE" for x in observations)
            else "HISTORICAL",
        )
    else:
        if op == "build" and source:
            # Serialized catalogs and metadata never become imports through this path.
            raw = project_from_import(ImportResult.model_validate(source).model_dump(mode="json"))
            execution = raw
        request = bound_execution(raw, step)
        if op == "build":
            value = compose(request)
        elif op == "test":
            value = check_vectors(
                parse_request(
                    {
                        **request.model_dump(mode="json"),
                        "vectors": [v.model_dump(mode="json") for v in step.vectors],
                    },
                    vectors=True,
                )
            )
        elif op == "compare":
            value = compare(request)
        elif op == "inspect":
            value = debug(
                dict(
                    schemaVersion="m45-debugging-1.0.0",
                    kind="DEBUG_REQUEST",
                    executionRequest=request.model_dump(mode="json"),
                    budget=step.budget.trace.model_dump(mode="json"),
                )
            ).model_dump(mode="json")
        elif op == "propose_correction":
            value = proposal(request, step)
        elif op == "verify":
            value = verify_proposal(request, step, source)
        elif op == "apply":
            if (
                not source
                or source.get("kind") != "WORKFLOW_CORRECTION"
                or source.get("classification") != "VERIFIED_CORRECTION"
            ):
                raise ContractError("INVALID_INPUT", "Apply requires a verified local correction.")
            # Never promote a saved status. Recheck immediately before an explicit local revision.
            value = verify_proposal(request, step, source["proposal"])
            if value["classification"] == "VERIFIED_CORRECTION":
                execution = deepcopy(source["proposal"]["proposedRevision"])
        elif op in ("export", "verify_bundle"):
            body = dict(
                schemaVersion=VERSION,
                kind="PRODUCT_REQUEST",
                executionRequest=request.model_dump(mode="json"),
            )
            if op == "verify_bundle":
                body["bundle"] = step.bundle if step.bundle is not None else source
            value = product("verify-bundle" if op == "verify_bundle" else "export", body)
        elif op == "stop_authorization":
            built = compose(request)
            value = dict(
                kind="STOP_AUTHORIZATION",
                proposedAction="ONCHAIN_PUBLICATION",
                reason="Publication requires a separate human-controlled process. "
                "This terminal handoff grants no permission and has no signing capability.",
                projectHash=content_hash(request.project),
                executionHash=content_hash(request),
                candidateIdentity=built["candidateIdentity"],
                candidateManifestHash=built["manifestHash"],
                sourceManifestHashes=[i.manifestHash for i in request.imports],
                netlist=built["netlist"],
                signingCapability=False,
                retryable=False,
            )
        else:
            raise ContractError("INVALID_INPUT", "Unknown workflow operation.")
    if not isinstance(value, dict):
        raise ContractError("INTERNAL_ERROR", "Malformed trusted operation output.")
    if op in ("compare", "verify_bundle"):
        if value.get("kind") != "TRUSTED_LOCAL_COMPARISON" or value.get(
            "requestHash"
        ) != content_hash(request):
            raise ContractError(
                "INTERNAL_ERROR", "Comparison service returned a different request."
            )
        ComparisonReport.model_validate(value.get("report"))
    return {"output": value, "executionRequest": execution}


def semantic(value):
    """Stable semantic receipts exclude only existing runtime/timestamp observations."""
    if isinstance(value, list):
        return [semantic(v) for v in value]
    if not isinstance(value, dict):
        return value
    # Keep all proof fields, identities and witness bytes; these keys are service observations.
    return {
        k: semantic(v)
        for k, v in value.items()
        if k not in ("resources", "verifiedAt", "contentHash", "semanticHash")
    }


def classify(output):
    if output.get("kind") == "STOP_AUTHORIZATION":
        return "STOP_AUTHORIZATION", None
    if output.get("freshness") == "STALE" or output.get("status") in (
        "ENVIRONMENT_CHANGED",
        "REORGED",
    ):
        return "STALE", "IMPLEMENTATION_CHANGED"
    if output.get("kind") == "WORKFLOW_CORRECTION":
        output = output["comparison"]
    proof = output.get("comparison", output)
    if isinstance(proof, dict):
        proof = proof.get("report", proof)
    if not isinstance(proof, dict):
        proof = {}
    verdict = proof.get("verification", proof).get("verdict")
    if verdict in ("DIFFERENT", "VECTORS_MISMATCH"):
        return "DIFFERENT", None
    if output.get("classification") == "VERIFIED_DIFFERENCE":
        return "DIFFERENT", None
    if (
        verdict == "UNKNOWN"
        or output.get("classification") == "UNKNOWN"
        or output.get("status") in ("UNKNOWN", "ABORTED", "VERIFICATION_FAILED")
    ):
        return "UNKNOWN", (
            proof.get("verification", {}).get("reasonCode")
            or output.get("reasonCode")
            or output.get("errorCode")
            or "INCONCLUSIVE"
        )
    if output.get("status") in ("PARTIAL_BOUNDED", "COMPLETE_WITH_GAPS"):
        return "UNKNOWN", "INCOMPLETE_CATALOG"
    return "COMPLETE", None
