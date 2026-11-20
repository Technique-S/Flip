"""Export additive portable package schemas and deterministic canonical vectors."""

import argparse
import json
from pathlib import Path

from flip_core.canonical import canonical_bytes, content_hash
from flip_core.portable import PortableProject, PortableRequest, create_package
from flip_core.verification import VerificationRequest
from flip_core.workflow import REPRODUCE, sample


def contract_schema(model):
    schema = model.model_json_schema()
    execution = VerificationRequest.model_json_schema()
    definitions = execution.pop("$defs")
    for key, value in definitions.items():
        existing = schema.setdefault("$defs", {}).get(key)
        if existing is not None and existing != value:
            raise ValueError(f"Conflicting schema definition: {key}")
        schema["$defs"][key] = value

    def replace(value):
        if isinstance(value, dict):
            properties = value.get("properties", {})
            if "executionRequest" in properties:
                original = properties["executionRequest"]
                properties["executionRequest"] = (
                    {"anyOf": [execution, {"type": "null"}], "default": None}
                    if "anyOf" in original
                    else execution
                )
            for member in value.values():
                replace(member)
        elif isinstance(value, list):
            for member in value:
                replace(member)

    replace(schema)
    return schema


def artifacts():
    package = create_package(sample("half-adder"))
    edited = sample("swapped")
    revision = create_package(edited, previous=package, description="Swap outputs")
    # Deliberately synthetic reference pins exercise metadata hashing, not proof.
    rich = create_package(
        sample("half-adder"),
        tests=[
            {
                "name": "selectedInputs",
                "declaredIntent": "Carry / sum \u2014 explicit user vectors",
                "expectedCoverage": "SELECTED_INPUTS",
                "vectors": [
                    {
                        "inputs": {"encoding": "tap02-lsb0-v1", "width": 2, "bits": "00"},
                        "outputs": {"encoding": "tap02-lsb0-v1", "width": 2, "bits": "00"},
                    }
                ],
            }
        ],
        evidence_refs=[
            {
                "kind": "FLIP_EVIDENCE",
                "digest": content_hash({"fixture": "NOT_A_PROOF"}),
                "executionRequestHash": package["executionRequestHash"],
                "reproduce": REPRODUCE,
                "engineHash": content_hash({"fixture": "UNVERIFIED_ENGINE_PIN"}),
            }
        ],
        provenance={
            "sourceFreshness": "HISTORICAL",
            "observationBlock": "1",
            "syntheticFlags": ["SYNTHETIC_CANONICAL_VECTOR_NOT_PROOF"],
        },
        agent_task_ref=content_hash({"fixture": "NON_AUTHORITATIVE_AGENT_TASK"}),
    )
    packages = [package, revision, rich]
    return {
        "package.schema.json": contract_schema(PortableProject),
        "request.schema.json": contract_schema(PortableRequest),
        "golden.json": {
            "profile": "flip-json-v1",
            "packages": packages,
            "hashes": [content_hash(p) for p in packages],
            "canonical": [canonical_bytes(p).decode() for p in packages],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, value in artifacts().items():
        raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        path = args.out / name
        if args.check:
            if not path.exists() or path.read_bytes() != raw:
                raise SystemExit(f"Schema or golden drift: {path}")
        else:
            args.out.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)


if __name__ == "__main__":
    main()
