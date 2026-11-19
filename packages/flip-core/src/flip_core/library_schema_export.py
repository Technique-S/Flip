"""Export additive library schemas; --check is deterministic and offline."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--version", choices=("1.0.0", "1.1.0"), default="1.0.0")
    args = parser.parse_args()
    if args.version == "1.0.0":
        from flip_core.library_models_v1 import Catalog, LibraryRequest, LibraryResult
    else:
        from flip_core.library_models import Catalog, LibraryRequest, LibraryResult
    for name, model in (
        ("catalog", Catalog),
        ("request", LibraryRequest),
        ("result", LibraryResult),
    ):
        raw = (json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n").encode()
        path = args.out / f"{name}.schema.json"
        if args.check:
            if not path.exists() or path.read_bytes() != raw:
                raise SystemExit(f"Schema drift: {path}")
        else:
            args.out.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)


if __name__ == "__main__":
    main()
