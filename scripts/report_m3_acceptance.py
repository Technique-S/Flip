"""Extract actual JUnit case evidence, never infer a pass from fixture metadata."""

import argparse
import hashlib
import json
import platform
import xml.etree.ElementTree as ET
from pathlib import Path

from flip_core.verification import engine_identity

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    tree = ET.parse(args.junit)
    cases, counts = [], {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for case in tree.iter("testcase"):
        outcome = (
            "failed"
            if case.find("failure") is not None
            else "errors"
            if case.find("error") is not None
            else "skipped"
            if case.find("skipped") is not None
            else "passed"
        )
        counts[outcome] += 1
        for prop in case.findall("./properties/property"):
            if prop.get("name") != "m3_case":
                continue
            entry = json.loads(prop.get("value"))
            entry["test"] = case.get("name")
            entry["outcome"] = outcome.upper()
            node = f"packages/flip-core/tests/test_m3_acceptance.py::{case.get('name')}"
            entry["command"] = f'python -m pytest "{node}" -q'
            resources = entry.get("resources", {})
            if isinstance(resources.get("witness"), list):
                resources["witnessBits"] = "".join(map(str, resources.pop("witness")))
            cases.append(entry)
    hashes = {}
    for relative in (
        "packages/flip-core/tests/m3_c_adapter.py",
        "packages/flip-core/tests/test_m3_acceptance.py",
        "scripts/check_m1_repository.py",
        "fixtures/m3-verification/MANIFEST.json",
    ):
        hashes[relative] = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    result = {
        "scope": "M3-C production execution; historical/synthetic fixture contexts, no live RPC",
        "sourceCommits": {
            "main": "02463b1f370d39f6abab897d54d3438cd6056458",
            "M3A": "d4adf809f2576a1e14e64adce0b04c914049a50f",
            "M3B": "4822a05163166ec67b791328e2d1de490fa1c35f",
        },
        "platform": platform.platform(),
        "python": platform.python_version(),
        "suite": counts,
        "caseCount": len(cases),
        "cases": cases,
        "engine": engine_identity(),
        "inputHashes": hashes,
        "result": "PASS"
        if not (counts["failed"] or counts["errors"] or counts["skipped"]) and len(cases) == 75
        else "FAIL",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"result": result["result"], "suite": counts, "productionCases": len(cases)}))
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
