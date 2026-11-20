"""Replay pinned independent checks into scratch; never update archived observations."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence/m45-agent-workflow-independent-review"


def run(name, key, expected_count):
    source = ROOT / f"fixtures/m45-agent-workflow-independent-review/harness/{name}.py"
    scratch = ROOT / ".test-tmp/agent-independent" / name
    scratch.mkdir(parents=True, exist_ok=True)
    namespace = {"__file__": str(source), "__name__": "pinned_independent_review"}
    exec(compile(source.read_bytes(), str(source), "exec"), namespace)
    output_name = (
        "independent-acceptance.json"
        if name == "independent_acceptance"
        else "authorization-checks.json"
    )
    namespace["OUT"] = scratch / output_name
    namespace["RUN"] = scratch
    if "FLIP" in namespace:
        namespace["FLIP"] = str(
            ROOT / (".venv/Scripts/flip.exe" if sys.platform == "win32" else ".venv/bin/flip")
        )
    namespace["main"]()
    original = json.loads((EVIDENCE / "results" / output_name).read_bytes())[key]
    observed = json.loads(namespace["OUT"].read_bytes())[key]
    if len(observed) != expected_count or [r["id"] for r in observed] != [
        r["id"] for r in original
    ]:
        raise AssertionError("Independent case inventory changed")
    for actual, expected in zip(observed, original, strict=True):
        if actual["error"] is not None:
            raise AssertionError(actual)
        if actual["id"] == "D02":
            if not re.fullmatch(r"0x[0-9a-f]{64}", actual["observed"]["engineHash"]):
                raise AssertionError("Invalid native engine hash")
            expected = {
                **expected,
                "observed": {
                    **expected["observed"],
                    "engineHash": actual["observed"]["engineHash"],
                },
            }
        if actual["observed"] != expected["observed"]:
            raise AssertionError(
                {"id": actual["id"], "expected": expected["observed"], "actual": actual["observed"]}
            )
    print(f"{name}: {expected_count}/{expected_count} exact semantic checks PASS")


def main():
    run("independent_acceptance", "results", 27)
    run("authorization_checks", "rows", 10)


if __name__ == "__main__":
    main()
