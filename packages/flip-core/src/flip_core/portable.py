"""Versioned project transport; validation establishes integrity, never proof authority."""

from __future__ import annotations

from time import monotonic
from typing import Literal, Self

from pydantic import Field, model_validator

from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.contracts import ContractError
from flip_core.models import Contract, Digest, Name
from flip_core.verification import ExpectedVector, parse_request

VERSION = "flip-portable-project-1.1.0"


class NamedTests(Contract):
    name: Name
    declaredIntent: str = Field(min_length=1, max_length=2000)
    expectedCoverage: Literal["SELECTED_INPUTS", "EXHAUSTIVE_DECLARED_DOMAIN"]
    vectors: list[ExpectedVector] = Field(min_length=1, max_length=4096)


class EvidenceRef(Contract):
    kind: Literal["FLIP_EVIDENCE"]
    digest: Digest
    executionRequestHash: Digest
    reproduce: str = Field(min_length=1, max_length=300)
    engineHash: Digest


class Provenance(Contract):
    sourceFreshness: Literal["UNSPECIFIED", "HISTORICAL", "STALE"] = "UNSPECIFIED"
    observationBlock: str | None = Field(default=None, pattern=r"^(0|[1-9][0-9]*)$")
    syntheticFlags: list[str] = Field(default_factory=list, max_length=32)


class Edit(Contract):
    beforeHash: Digest | None
    afterHash: Digest
    description: str = Field(min_length=1, max_length=2000)


class Revision(Contract):
    projectId: Name
    sequence: int = Field(ge=0, le=1023)
    parentHash: Digest | None
    executionRequestHash: Digest
    metadataHash: Digest
    editLog: list[Edit] = Field(min_length=1, max_length=128)
    revisionHash: Digest


class PortableRequest(Contract):
    schemaVersion: Literal["flip-portable-project-1.1.0"]
    kind: Literal["PORTABLE_REQUEST"]
    operation: Literal["wrap", "validate", "open", "downgrade", "test", "replay-evidence"]
    package: PortableProject | None = None
    executionRequest: dict | None = None
    previous: PortableProject | None = None
    expectedRevisionHash: Digest | None = None
    tests: list[NamedTests] | None = None
    evidenceRefs: list[EvidenceRef] | None = None
    provenance: Provenance | None = None
    agentTaskRef: Digest | None = None
    description: str | None = Field(default=None, min_length=1, max_length=2000)
    allowLossy: bool | None = None
    artifacts: dict[str, dict] | None = None


def record_hash(record):
    value = record.model_dump(mode="json") if isinstance(record, Revision) else record
    return content_hash({k: v for k, v in value.items() if k != "revisionHash"})


def metadata_hash(value):
    return content_hash(
        {
            k: value[k]
            for k in (
                "schemaVersion",
                "kind",
                "tests",
                "noDeclaredTests",
                "evidenceRefs",
                "provenance",
                "agentTaskRef",
            )
        }
    )


class PortableProject(Contract):
    schemaVersion: Literal["flip-portable-project-1.1.0"]
    kind: Literal["PORTABLE_PROJECT"]
    # Preserve the supplied request's canonical bytes, including omitted default fields.
    executionRequest: dict
    executionRequestHash: Digest
    tests: list[NamedTests] = Field(max_length=64)
    noDeclaredTests: bool
    evidenceRefs: list[EvidenceRef] = Field(max_length=128)
    provenance: Provenance = Field(default_factory=Provenance)
    agentTaskRef: Digest | None = None
    ancestors: list[Revision] = Field(max_length=1023)
    revision: Revision

    @model_validator(mode="after")
    def integrity(self) -> Self:
        request = parse_request(self.executionRequest)
        if content_hash(self.executionRequest) != self.executionRequestHash:
            raise ValueError("execution request hash mismatch")
        if self.noDeclaredTests != (not self.tests):
            raise ValueError("empty tests require explicit noDeclaredTests=true")
        if len({t.name for t in self.tests}) != len(self.tests):
            raise ValueError("duplicate test names")
        if sum(len(t.vectors) for t in self.tests) > 4096:
            raise ValueError("aggregate vector budget exceeded")
        for test in self.tests:
            seen = set()
            for vector in test.vectors:
                if (
                    vector.inputs.width != request.project.candidate.nIn
                    or vector.outputs.width != len(request.project.candidate.outputs)
                    or vector.inputs.bits in seen
                ):
                    raise ValueError("test width or duplicate input domain mismatch")
                seen.add(vector.inputs.bits)
            if test.expectedCoverage == "EXHAUSTIVE_DECLARED_DOMAIN" and (
                request.project.candidate.nIn > 12 or len(seen) != 2**request.project.candidate.nIn
            ):
                raise ValueError("exhaustive declaration does not cover the input domain")
        if len({r.digest for r in self.evidenceRefs}) != len(self.evidenceRefs):
            raise ValueError("duplicate evidence reference")
        for ref in self.evidenceRefs:
            if ref.executionRequestHash != self.executionRequestHash:
                raise ValueError("evidence belongs to a different execution request")
            from flip_core.workflow import REPRODUCE

            if ref.reproduce != REPRODUCE:
                raise ValueError("unsupported reproduction identity")
        previous = None
        for index, record in enumerate([*self.ancestors, self.revision]):
            if record.projectId != request.project.projectId or record.sequence != index:
                raise ValueError("incompatible or cross-project ancestry")
            if record.parentHash != (previous.revisionHash if previous else None):
                raise ValueError("broken revision parent")
            before = previous.executionRequestHash if previous else None
            for edit in record.editLog:
                if edit.beforeHash != before:
                    raise ValueError("broken or reordered edit chain")
                before = edit.afterHash
            if before != record.executionRequestHash or record_hash(record) != record.revisionHash:
                raise ValueError("revision checksum or final edit mismatch")
            previous = record
        if self.revision.executionRequestHash != self.executionRequestHash:
            raise ValueError("head execution mismatch")
        if self.revision.metadataHash != metadata_hash(self.model_dump(mode="json")):
            raise ValueError("head metadata mismatch")
        return self


def parse_package(value):
    if isinstance(value, (str, bytes)):
        value = load_json(value)
    if not isinstance(value, dict) or value.get("schemaVersion") != VERSION:
        raise ContractError("INVALID_INPUT", "UNSUPPORTED_SCHEMA_VERSION: expected portable 1.1.0.")
    return PortableProject.model_validate(value)


def create_package(
    execution,
    *,
    previous=None,
    tests=None,
    evidence_refs=None,
    provenance=None,
    agent_task_ref=None,
    description="Create portable project",
):
    request = parse_request(execution)
    before = parse_package(previous).model_dump(mode="json") if previous is not None else None
    if before and before["revision"]["projectId"] != request.project.projectId:
        raise ContractError("INVALID_INPUT", "Incompatible project ancestry.")
    value = dict(
        schemaVersion=VERSION,
        kind="PORTABLE_PROJECT",
        executionRequest=execution,
        executionRequestHash=content_hash(execution),
        tests=tests if tests is not None else (before["tests"] if before else []),
        evidenceRefs=evidence_refs
        if evidence_refs is not None
        else (before["evidenceRefs"] if before else []),
        provenance=provenance
        if provenance is not None
        else (before["provenance"] if before else Provenance().model_dump(mode="json")),
        agentTaskRef=agent_task_ref
        if agent_task_ref is not None
        else (before["agentTaskRef"] if before else None),
    )
    value["provenance"] = Provenance.model_validate(value["provenance"]).model_dump(mode="json")
    value["tests"] = [NamedTests.model_validate(t).model_dump(mode="json") for t in value["tests"]]
    value["evidenceRefs"] = [
        EvidenceRef.model_validate(r).model_dump(mode="json") for r in value["evidenceRefs"]
    ]
    value["noDeclaredTests"] = not value["tests"]
    # A changed request makes old references historical dependencies, not evidence for this head.
    # Require explicit removal or replacement; never silently drop them.
    value["ancestors"] = [*before["ancestors"], before["revision"]] if before else []
    record = dict(
        projectId=request.project.projectId,
        sequence=len(value["ancestors"]),
        parentHash=before["revision"]["revisionHash"] if before else None,
        executionRequestHash=value["executionRequestHash"],
        metadataHash=metadata_hash(value),
        editLog=[
            dict(
                beforeHash=before["executionRequestHash"] if before else None,
                afterHash=value["executionRequestHash"],
                description=description,
            )
        ],
    )
    record["revisionHash"] = record_hash(record)
    value["revision"] = record
    return parse_package(value).model_dump(mode="json")


def require_executable(package):
    if package.provenance.sourceFreshness == "STALE" or any(
        i.integrity.freshness == "STALE" for i in parse_request(package.executionRequest).imports
    ):
        raise ContractError(
            "IMPLEMENTATION_CHANGED", "STALE portable dependency; reimport before composition."
        )


def executable(value):
    if isinstance(value, (str, bytes)):
        try:
            value = load_json(value)
        except (ValueError, TypeError, RecursionError) as exc:
            raise ContractError("INVALID_INPUT", "Invalid project JSON.") from exc
    if isinstance(value, dict) and value.get("kind") == "PORTABLE_PROJECT":
        package = parse_package(value)
        require_executable(package)
        return package.executionRequest
    parse_request(value)
    return value


def portable_operation(body):
    """Single structured CLI/API contract. No filesystem or network access."""
    from flip_core.verification import check_vectors, compose
    from flip_core.workflow import product

    allowed = {
        "schemaVersion",
        "kind",
        "operation",
        "package",
        "executionRequest",
        "previous",
        "tests",
        "evidenceRefs",
        "provenance",
        "agentTaskRef",
        "description",
        "allowLossy",
        "artifacts",
        "expectedRevisionHash",
    }
    if (
        not isinstance(body, dict)
        or set(body) - allowed
        or body.get("schemaVersion") != VERSION
        or body.get("kind") != "PORTABLE_REQUEST"
    ):
        raise ContractError(
            "INVALID_INPUT", "Invalid portable request or unsupported schema version."
        )
    operation = body.get("operation")
    common = {"schemaVersion", "kind", "operation"}
    fields = {
        "wrap": {
            "executionRequest",
            "previous",
            "expectedRevisionHash",
            "tests",
            "evidenceRefs",
            "provenance",
            "agentTaskRef",
            "description",
        },
        "validate": {"package", "expectedRevisionHash"},
        "open": {"package", "expectedRevisionHash"},
        "downgrade": {"package", "expectedRevisionHash", "allowLossy"},
        "test": {"package", "expectedRevisionHash"},
        "replay-evidence": {"package", "expectedRevisionHash", "artifacts"},
    }
    if operation not in fields or set(body) - common - fields[operation]:
        raise ContractError("INVALID_INPUT", "Unknown operation or irrelevant portable fields.")
    for key in ("package", "previous"):
        if (
            key in body
            and isinstance(body[key], dict)
            and body[key].get("schemaVersion") != VERSION
        ):
            raise ContractError(
                "UNSUPPORTED_SCHEMA_VERSION", "Unsupported portable package version."
            )
    PortableRequest.model_validate(body)
    if operation == "wrap":
        if "previous" in body:
            old = parse_package(body["previous"])
            if body.get("expectedRevisionHash") != old.revision.revisionHash:
                raise ContractError(
                    "INVALID_INPUT", "Expected parent revision required for local edits."
                )
        return create_package(
            body["executionRequest"],
            previous=body.get("previous"),
            tests=body.get("tests"),
            evidence_refs=body.get("evidenceRefs"),
            provenance=body.get("provenance"),
            agent_task_ref=body.get("agentTaskRef"),
            description=body.get("description", "Save portable revision"),
        )
    package = parse_package(body["package"])
    if (
        "expectedRevisionHash" in body
        and body["expectedRevisionHash"] != package.revision.revisionHash
    ):
        raise ContractError(
            "INVALID_INPUT", "Selected revision differs from the expected revision."
        )
    value = package.model_dump(mode="json")
    request = parse_request(package.executionRequest)
    if operation == "validate":
        return value
    if operation == "open":
        require_executable(package)
        compose(request)  # validate imports, closure, freshness and executable semantics
        return {
            "executionRequest": package.executionRequest,
            "package": value,
            "trust": "LOCAL_DATA_INTEGRITY_ONLY",
        }
    if operation == "downgrade":
        discarded = [
            "tests",
            "noDeclaredTests",
            "evidenceRefs",
            "revision",
            "ancestors",
            "provenance",
            "agentTaskRef",
        ]
        if body.get("allowLossy") is not True:
            raise ContractError("INVALID_INPUT", "LOSSY_CONVERSION_REQUIRES_ACKNOWLEDGEMENT")
        return {
            "executionRequest": package.executionRequest,
            "discardedFields": discarded,
            "warning": "LOSSY_DOWNGRADE: portable metadata and history discarded.",
        }
    if operation == "test":
        from flip_core.composition import compile_project
        from flip_core.execution import execution_cost

        require_executable(package)
        composition = compile_project(request.project, request.imports)
        if (
            execution_cost(composition.candidate) * sum(len(t.vectors) for t in package.tests)
            > 2_000_000
        ):
            raise ContractError("RESOURCE_LIMIT", "Aggregate named-test work budget exceeded.")
        deadline = monotonic() + 5
        results = []
        for test in package.tests:
            if monotonic() > deadline:
                raise ContractError("RESOURCE_LIMIT", "Named-test deadline exceeded.")
            results.append(
                {
                    "name": test.name,
                    "declaredIntent": test.declaredIntent,
                    "expectedCoverage": test.expectedCoverage,
                    "result": check_vectors(
                        parse_request(
                            {
                                **package.executionRequest,
                                "vectors": [v.model_dump(mode="json") for v in test.vectors],
                            },
                            vectors=True,
                        )
                    ),
                }
            )
        return {"noDeclaredTests": package.noDeclaredTests, "results": results}
    if operation == "replay-evidence":
        artifacts = body.get("artifacts", {})
        if not isinstance(artifacts, dict) or set(artifacts) - {
            r.digest for r in package.evidenceRefs
        }:
            raise ContractError("INVALID_INPUT", "Unexpected evidence artifact identity.")
        results = []
        deadline = monotonic() + 15
        for ref in package.evidenceRefs:
            if monotonic() > deadline:
                raise ContractError("RESOURCE_LIMIT", "Evidence replay deadline exceeded.")
            artifact = artifacts.get(ref.digest)
            if artifact is None:
                results.append({"digest": ref.digest, "status": "MISSING_EVIDENCE"})
                continue
            if (
                not isinstance(artifact, dict)
                or artifact.get("contentHash") != ref.digest
                or content_hash({k: v for k, v in artifact.items() if k != "contentHash"})
                != ref.digest
                or artifact.get("reproduce") != ref.reproduce
                or not isinstance(artifact.get("comparison"), dict)
                or artifact["comparison"].get("engineHash") != ref.engineHash
            ):
                raise ContractError(
                    "INVALID_INPUT", "Evidence digest, reproduction or engine mismatch."
                )
            result = product(
                "verify-bundle",
                dict(
                    schemaVersion="m4-1.0.0",
                    kind="PRODUCT_REQUEST",
                    executionRequest=package.executionRequest,
                    bundle=artifact,
                ),
            )
            results.append({"digest": ref.digest, "status": "REPLAYED", "result": result})
        return {
            "results": results,
            "freshness": "STALE"
            if (
                package.provenance.sourceFreshness == "STALE"
                or any(i.integrity.freshness == "STALE" for i in request.imports)
                or any(
                    r.get("result", {}).get("report", {}).get("integrity", {}).get("freshness")
                    == "STALE"
                    for r in results
                )
            )
            else "HISTORICAL",
            "trust": "TRUSTED_ENGINE_REPLAY_ONLY",
        }
    raise ContractError("INVALID_INPUT", "Unknown portable operation.")


def bounded_operation(body):
    if len(canonical_bytes(body)) > 1_048_576:
        raise ContractError("RESOURCE_LIMIT", "Portable request exceeds 1 MiB.")
    try:
        return portable_operation(body)
    except ContractError:
        raise
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        raise ContractError("INVALID_INPUT", "Invalid portable package or operation.") from exc


PortableRequest.model_rebuild()
