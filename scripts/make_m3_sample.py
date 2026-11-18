"""Generate an offline half-adder recipe from genuine accepted M2 import captures."""

import argparse
from pathlib import Path

from flip_core.canonical import canonical_bytes, load_json
from flip_core.verification import parse_request

ROOT = Path(__file__).resolve().parents[1]


def sample():
    capture = load_json((ROOT / "docs/milestones/M2_A/live-smoke.json").read_bytes())
    imports = [c["artifact"] for c in capture["cases"] if c["circuitId"] in ("1", "2")]
    sources = []
    for alias, value in zip(("xor", "nand"), imports, strict=True):
        root = value["manifest"]["root"]
        sources.append(
            {
                "alias": alias,
                "identity": root["identity"],
                "manifestHash": value["manifestHash"],
                "nIn": root["nIn"],
                "nOut": root["nOut"],
                "nState": root["nState"],
            }
        )
    a, b = {"component": None, "pin": 0}, {"component": None, "pin": 1}
    inverted_carry = {"component": "nand0", "pin": 0}
    candidate = {
        "nIn": 2,
        "components": [
            {"kind": "REF", "instanceId": "nand0", "sourceAlias": "nand", "inputs": [a, b]},
            {"kind": "NAND", "instanceId": "carry", "inputs": [inverted_carry, inverted_carry]},
            {"kind": "REF", "instanceId": "sum", "sourceAlias": "xor", "inputs": [a, b]},
        ],
        "outputs": [{"component": "carry", "pin": 0}, {"component": "sum", "pin": 0}],
    }
    return parse_request(
        {
            "schemaVersion": "m3-1.0.0",
            "kind": "M3_EXECUTION",
            "relation": "BEHAVIORAL",
            "imports": imports,
            "project": {
                "schemaVersion": "m3-1.0.0",
                "projectId": "historicalHalfAdder",
                "chainId": 196,
                "toolVersion": "0.1.0",
                "sources": sources,
                "candidate": candidate,
                "referenceCandidate": candidate,
                "comparison": {
                    "kind": "PAIRWISE_EQUIVALENCE",
                    "referenceAlias": None,
                    "intent": "UNDECLARED",
                    "trustAssertion": None,
                    "inputMap": [0, 1],
                    "outputMap": [0, 1],
                },
                "limits": {
                    "gateCap": 2500,
                    "refDepthCap": 64,
                    "solverTimeoutMs": 5000,
                    "solverMemoryMiB": 64,
                },
            },
        }
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical_bytes(sample()) + b"\n")
