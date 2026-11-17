"""Rebuild synthetic contract examples; these are not audit or chain fixtures."""

import hashlib
import json
from pathlib import Path

from flip_core.models import CONTRACTS, Semantics

HERE = Path(__file__).resolve().parent
DIGEST = "0x" + "11" * 32
ADDRESS = "0x" + "ab" * 20
IDENTITY = {
    "schemaVersion": "1.0.0",
    "chainId": 196,
    "processor": ADDRESS,
    "circuitId": "18446744073709551615",
}
SEMANTICS = {name: info.annotation.__args__[0] for name, info in Semantics.model_fields.items()}
BLOCK = {"number": "9007199254740993", "hash": DIGEST}
CODE = {"address": ADDRESS, "codeHash": DIGEST}
EXAMPLES = {
    "circuit-identity": IDENTITY,
    "project": {
        "schemaVersion": "1.0.0",
        "projectId": "synthetic",
        "chainId": 196,
        "toolVersion": "0.1.0",
        "sources": [
            {
                "alias": "baseline",
                "identity": IDENTITY,
                "manifestHash": DIGEST,
                "nIn": 2,
                "nOut": 1,
                "nState": 0,
            }
        ],
        "candidate": {
            "nIn": 2,
            "components": [
                {
                    "kind": "REF",
                    "instanceId": "componentA",
                    "sourceAlias": "baseline",
                    "inputs": [{"component": None, "pin": 0}, {"component": None, "pin": 1}],
                }
            ],
            "outputs": [{"component": "componentA", "pin": 0}],
        },
        "comparison": {
            "kind": "PAIRWISE_EQUIVALENCE",
            "referenceAlias": "baseline",
            "intent": "UNDECLARED",
            "trustAssertion": None,
            "inputMap": [0, 1],
            "outputMap": [0],
        },
        "limits": {
            "gateCap": 2500,
            "refDepthCap": 64,
            "solverTimeoutMs": 5000,
            "solverMemoryMiB": 64,
        },
    },
    "manifest": {
        "schemaVersion": "1.0.0",
        "chainId": 196,
        "block": BLOCK,
        "root": {
            "identity": IDENTITY,
            "netlistHash": DIGEST,
            "nIn": 2,
            "nOut": 1,
            "nState": 0,
            "expandedGates": 1,
            "environment": {
                "factory": CODE,
                "factoryImplementationSlot": DIGEST,
                "factoryImplementation": CODE,
                "factorySealed": False,
                "beacon": CODE,
                "beaconImplementation": CODE,
                "processorCodeHash": DIGEST,
            },
        },
        "dependencies": [],
        "edges": [],
        "semantics": SEMANTICS,
        "toolVersion": "0.1.0",
        "observation": "OFFLINE_SNAPSHOT",
    },
    "comparison-report": {
        "schemaVersion": "1.0.0",
        "chainId": 196,
        "projectHash": DIGEST,
        "referenceManifestHash": DIGEST,
        "candidateManifestHash": DIGEST,
        "toolVersion": "0.1.0",
        "semantics": SEMANTICS,
        "limits": {
            "gateCap": 2500,
            "refDepthCap": 64,
            "solverTimeoutMs": 5000,
            "solverMemoryMiB": 64,
        },
        "verification": {
            "kind": "PAIRWISE_EQUIVALENCE",
            "verdict": "UNKNOWN",
            "reasonCode": "NOT_IMPLEMENTED",
            "solverBackend": "NONE",
            "solverOutcome": "NOT_RUN",
            "referenceNState": 0,
            "candidateNState": 0,
            "sourceValidation": "UNVERIFIED",
            "mappingValidation": "UNVERIFIED",
            "witness": None,
        },
        "intent": "UNDECLARED",
        "trustAssertion": None,
        "inputMap": [0, 1],
        "outputMap": [0],
        "integrity": {"freshness": "UNVERIFIED", "checkedBlock": None},
    },
    "preflight": {
        "schemaVersion": "1.0.0",
        "chainId": 196,
        "candidateNetlistHash": DIGEST,
        "manifestHash": DIGEST,
        "mode": "READ_ONLY_ETH_CALL",
        "status": "UNKNOWN",
        "reasonCode": "NOT_IMPLEMENTED",
        "observation": None,
        "integrity": {"freshness": "UNVERIFIED", "checkedBlock": None},
    },
    "error-envelope": {
        "schemaVersion": "1.0.0",
        "error": {"code": "NOT_IMPLEMENTED", "message": "M1-A only."},
    },
}


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    for name, value in EXAMPLES.items():
        model = CONTRACTS[name].model_validate(value)
        write(HERE / "examples" / f"{name}.json", model.model_dump(mode="json"))
    # Independent literal inputs; expected bytes use stdlib rather than the production serializer.
    values = [
        {},
        [],
        {"b": 2, "a": 1},
        {"chainId": 196, "circuitId": "18446744073709551615", "processor": ADDRESS},
        {"unicode": "café\n雪", "nested": {"z": None, "a": [True, False, 0]}},
        {"2": "two", "10": "ten", "string": 'line\tquote"slash/\\'},
    ]
    vectors = []
    for value in values:
        text = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        raw = text.encode("utf-8")
        vectors.append(
            {
                "input": value,
                "canonical": text,
                "utf8Hex": raw.hex(),
                "sha256": "0x" + hashlib.sha256(raw).hexdigest(),
            }
        )
    write(HERE / "canonical-golden.json", {"profile": "flip-json-v1", "vectors": vectors})


if __name__ == "__main__":
    main()
