"""Developer harness, not a service. Fresh measurements, no archived result reuse."""

import argparse
import json
import platform
import sys
from pathlib import Path

from flip_core.verification import compare

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages/flip-core/tests"))
from test_m3_engine import benchmark_request  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    cases = []
    engine = None
    for target in (50, 100, 250, 500, 1000, 2500, 5000):
        for mode, expected in (
            ("self", "EQUIVALENT"),
            ("equivalent", "EQUIVALENT"),
            ("different", "DIFFERENT"),
            ("fault_reverse_one", "EQUIVALENT"),
        ):
            result = compare(benchmark_request(target, mode))
            actual = result["report"]["verification"]["verdict"]
            engine = result["engine"]
            witness = result["report"]["verification"]["witness"]
            case = {
                "target": target,
                "mode": mode,
                "expected": expected,
                "actual": actual,
                "resources": {k: v for k, v in result["resources"].items() if k != "witness"},
                "verifiedAt": result["verifiedAt"],
                "engineHash": result["engineHash"],
                "requestHash": result["requestHash"],
                "witnessBits": witness["inputs"]["bits"] if witness else None,
                "witnessReplay": witness["replay"] if witness else None,
            }
            cases.append(case)
            print(json.dumps(case), flush=True)
    output = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "provenance": "SYNTHETIC_TRANSPORT_REAL_ARCHIVED_XOR_BYTES_NOT_CHAIN_OBSERVATIONS",
        "cases": cases,
        "engine": engine,
        "allMatched": all(c["actual"] == c["expected"] for c in cases),
    }
    args.out.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    return 0 if output["allMatched"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
