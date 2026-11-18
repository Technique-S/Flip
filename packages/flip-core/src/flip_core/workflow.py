"""Product operations used by both the local HTTP application and CLI."""

from pathlib import Path

from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.composition import compile_project
from flip_core.contracts import ContractError
from flip_core.import_models import ImportResult
from flip_core.models import ComparisonReport, Preflight
from flip_core.preflight import preflight
from flip_core.verification import compare, consume, parse_request

VERSION = "m4-1.0.0"
SAMPLE = Path(__file__).resolve().parents[4] / "docs/schema/m3/examples/half-adder.request.json"
LIMITATIONS = (
    "Stateless comparison over pinned inputs. Chain observations use one RPC. "
    "Replay requires compatible engine bytes."
)
REPRODUCE = "flip verify-bundle --project project.json --bundle evidence.json"


def sample(variant):
    value = load_json(SAMPLE.read_bytes())
    if variant == "swapped":
        value["project"]["candidate"]["outputs"].reverse()
    elif variant != "half-adder":
        raise ContractError("INVALID_INPUT", "Unknown historical sample.")
    return value


def project_from_import(value):
    imported = ImportResult.model_validate(value)
    root = imported.manifest.root
    if root.nState:
        raise ContractError(
            "UNSUPPORTED_STATEFUL_PROOF", "Composition requires a stateless source."
        )
    if root.nIn > 255 or root.nOut > 255:
        raise ContractError("BAD_NETLIST", "TAP-02 REF interfaces allow up to 255 pins.")
    source = dict(
        alias="source1",
        identity=root.identity.model_dump(),
        manifestHash=imported.manifestHash,
        nIn=root.nIn,
        nOut=root.nOut,
        nState=root.nState,
    )
    design = dict(
        nIn=root.nIn,
        components=[
            dict(
                kind="REF",
                sourceAlias="source1",
                instanceId="ref1",
                inputs=[dict(component=None, pin=i) for i in range(root.nIn)],
            )
        ],
        outputs=[dict(component="ref1", pin=i) for i in range(root.nOut)],
    )
    project = dict(
        schemaVersion="m3-1.0.0",
        projectId="importedCircuit",
        chainId=196,
        toolVersion="0.1.0",
        sources=[source],
        candidate=design,
        referenceCandidate=design,
        comparison=dict(
            kind="PAIRWISE_EQUIVALENCE",
            referenceAlias=None,
            intent="UNDECLARED",
            trustAssertion=None,
            inputMap=list(range(root.nIn)),
            outputMap=list(range(root.nOut)),
        ),
        limits={},
    )
    request = parse_request(
        dict(
            schemaVersion="m3-1.0.0",
            kind="M3_EXECUTION",
            relation="BEHAVIORAL",
            project=project,
            imports=[value],
        )
    )
    compile_project(request.project, request.imports)
    return request.model_dump(mode="json")


def inspect_evidence(bundle):
    if (
        not isinstance(bundle, dict)
        or bundle.get("kind") != "FLIP_EVIDENCE"
        or bundle.get("schemaVersion") != VERSION
        or not isinstance(bundle.get("comparison"), dict)
    ):
        raise ContractError("INVALID_INPUT", "Unknown evidence bundle.")
    claim = ComparisonReport.model_validate(bundle["comparison"].get("report"))
    return {
        "trust": "UNVERIFIED_FILE_CLAIMS",
        "claimedVerdict": claim.verification.verdict,
        "projectHash": claim.projectHash,
        "referenceManifestHash": claim.referenceManifestHash,
        "candidateManifestHash": claim.candidateManifestHash,
        "recordedFreshness": claim.integrity.freshness,
        "replayCommand": REPRODUCE,
    }


def preserve_staleness(request, observation):
    if (
        observation is not None
        and Preflight.model_validate(observation).integrity.freshness == "STALE"
    ):
        request = request.model_copy(deep=True)
        for item in request.imports:
            item.integrity.freshness = "STALE"
    return request


def product(operation, body):
    if (
        operation == "new-project"
        and isinstance(body, dict)
        and set(body) == {"schemaVersion", "kind", "source"}
        and body.get("schemaVersion") == VERSION
        and body.get("kind") == "PRODUCT_REQUEST"
    ):
        return project_from_import(body["source"])
    allowed = {"schemaVersion", "kind", "executionRequest"}
    if operation == "verify-bundle":
        allowed.update(("bundle", "bundleText"))
    elif operation == "export":
        allowed.add("observeChain")
    if (
        not isinstance(body, dict)
        or body.get("schemaVersion") != VERSION
        or body.get("kind") != "PRODUCT_REQUEST"
        or body.keys() - allowed
    ):
        raise ContractError("INVALID_INPUT", "Invalid product request or version.")
    request = parse_request(body.get("executionRequest"))
    if operation == "preflight":
        return preflight(request)
    if operation == "export":
        observe = body.get("observeChain", False)
        if type(observe) is not bool:
            raise ContractError("INVALID_INPUT", "observeChain must be a boolean.")
        observation = preflight(request) if observe else None
        request = preserve_staleness(request, observation)
        result = compare(request)
        bundle = {
            "schemaVersion": VERSION,
            "kind": "FLIP_EVIDENCE",
            "comparison": result,
            "chainObservation": observation,
            "limitations": LIMITATIONS,
            "reproduce": REPRODUCE,
        }
        bundle["contentHash"] = content_hash(bundle)
        # Keep exported files usable through the bounded browser replay endpoint.
        replay = dict(
            schemaVersion=VERSION,
            kind="PRODUCT_REQUEST",
            executionRequest=request.model_dump(mode="json"),
            bundleText=canonical_bytes(bundle).decode(),
        )
        if len(canonical_bytes(replay)) > 1_048_576:
            raise ContractError("RESOURCE_LIMIT", "Evidence exceeds the portable replay budget.")
        return bundle
    if operation == "verify-bundle":
        bundle = body.get("bundle")
        if "bundleText" in body:
            if "bundle" in body or not isinstance(body["bundleText"], str):
                raise ContractError("INVALID_INPUT", "Supply exactly one evidence file.")
            bundle = load_json(body["bundleText"])
        if (
            not isinstance(bundle, dict)
            or bundle.get("kind") != "FLIP_EVIDENCE"
            or bundle.get("schemaVersion") != VERSION
            or bundle.get("limitations") != LIMITATIONS
            or bundle.get("reproduce") != REPRODUCE
            or not isinstance(bundle.get("comparison"), dict)
            or set(bundle)
            != {
                "schemaVersion",
                "kind",
                "comparison",
                "chainObservation",
                "limitations",
                "reproduce",
                "contentHash",
            }
            or content_hash({k: v for k, v in bundle.items() if k != "contentHash"})
            != bundle["contentHash"]
        ):
            raise ContractError("INVALID_INPUT", "Invalid evidence format or checksum.")
        # The file may conservatively reduce freshness. It cannot promote it.
        request = preserve_staleness(request, bundle["chainObservation"])
        # Compute both pins from the caller's separately selected project.
        design = compile_project(request.project, request.imports)
        reference = (
            content_hash(design.local_reference_manifest)
            if design.local_reference_manifest
            else design.imports[request.project.comparison.referenceAlias].manifestHash
        )
        actual = consume(
            request,
            bundle["comparison"],
            expected_project_hash=content_hash(request.project),
            expected_reference_hash=reference,
        )
        claim = bundle["comparison"]
        if set(claim) != set(actual) or any(
            claim[k] != actual[k] for k in ("kind", "schemaVersion", "coverage", "correctness")
        ):
            raise ContractError(
                "INVALID_INPUT", "Evidence scope differs from the recomputed scope."
            )
        # Historical resource readings and optional chain observations cannot be replayed offline.
        return actual
    raise ContractError("INVALID_INPUT", "Unknown product operation.")
