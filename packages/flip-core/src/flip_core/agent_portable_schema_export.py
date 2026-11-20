"""Versioned adapter contracts and language-neutral identity/plan goldens."""

import argparse
import json
from pathlib import Path

from flip_core.agent_portable_adapter import (
    AgentPortableRequest,
    AgentPortableResult,
    PreparationRequest,
    prepare_adapter,
)
from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.portable import create_package


def artifacts():
    source = (
        Path(__file__).resolve().parents[4]
        / "docs/schema/m45-debugging/examples/swapped-prior.execution.json"
    )
    package = create_package(load_json(source.read_bytes()))
    prepared = prepare_adapter(dict(package=package, action="correct"))["request"]
    result = {}
    for name, model in [
        ("request", AgentPortableRequest),
        ("result", AgentPortableResult),
        ("preparation", PreparationRequest),
    ]:
        schema = model.model_json_schema()
        for field in ("package", "originalPackage", "revisedPackage"):
            if field in schema.get("properties", {}):
                ref = {"$ref": "../../m45-portable-project/1.1.0/package.schema.json"}
                schema["properties"][field] = (
                    {"anyOf": [ref, {"type": "null"}]} if field == "revisedPackage" else ref
                )
        result[f"{name}.schema.json"] = schema
    result["golden.json"] = dict(
        profile="flip-json-v1",
        request=prepared,
        hash=content_hash(prepared),
        canonical=canonical_bytes(prepared).decode(),
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, value in artifacts().items():
        raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()
        target = args.out / name
        if args.check:
            if not target.exists() or target.read_bytes() != raw:
                raise SystemExit(f"Adapter schema/golden drift: {target}")
        else:
            args.out.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)


if __name__ == "__main__":
    main()
