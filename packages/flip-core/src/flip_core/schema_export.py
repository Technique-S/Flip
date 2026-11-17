"""Generate checked-in schemas, or check them for drift without writing."""

import argparse
import json
from pathlib import Path

from flip_core.models import CONTRACTS


def rendered_schemas() -> dict[str, str]:
    result = {}
    for name, model in CONTRACTS.items():
        schema = model.model_json_schema(mode="validation")
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        schema["$id"] = f"urn:flip:schema:{name}:1.0.0"
        result[f"{name}.schema.json"] = json.dumps(schema, indent=2, sort_keys=True) + "\n"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in rendered_schemas().items():
        path = args.out / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                parser.exit(1, f"Schema drift: {path}\n")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
