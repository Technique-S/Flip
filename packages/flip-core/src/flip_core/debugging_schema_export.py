"""Export the additive diagnostic contracts without modifying frozen profiles."""

import argparse
import json
from pathlib import Path

from flip_core.debugging_models import DebugRequest, DebugResult


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, model in (("request", DebugRequest), ("result", DebugResult)):
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
