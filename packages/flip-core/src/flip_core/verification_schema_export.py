"""Additive M3 execution schemas, independently versioned from frozen v1/M2."""

import argparse
import json
from pathlib import Path

from flip_core.verification import ConsumptionRequest, VectorRequest, VerificationRequest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, model in (
        ("execution-request", VerificationRequest),
        ("vector-request", VectorRequest),
        ("consumption-request", ConsumptionRequest),
    ):
        raw = (json.dumps(model.model_json_schema(), sort_keys=True, indent=2) + "\n").encode()
        path = args.out / f"{name}.schema.json"
        if args.check:
            if not path.exists() or path.read_bytes() != raw:
                raise SystemExit(f"M3 schema drift: {path}")
        else:
            args.out.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)


if __name__ == "__main__":
    main()
