"""Export additive portable package schemas and deterministic canonical vectors."""

import argparse
import json
from pathlib import Path

from flip_core.canonical import canonical_bytes, content_hash
from flip_core.portable import PortableProject, PortableRequest, create_package
from flip_core.verification import VerificationRequest
from flip_core.workflow import sample


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
    return {
        "package.schema.json": contract_schema(PortableProject),
        "request.schema.json": contract_schema(PortableRequest),
        "golden.json": {
            "profile": "flip-json-v1",
            "packages": [package, revision],
            "hashes": [content_hash(p) for p in [package, revision]],
            "canonical": [canonical_bytes(p).decode() for p in [package, revision]],
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
