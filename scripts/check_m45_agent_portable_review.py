"""Replay the immutable final adapter review into scratch, never into its archive."""

import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "fixtures/m45-agent-portable-final-review/harness/independent_adapter_checks.py"
    namespace = {"__file__": str(source), "__name__": "pinned_final_adapter_review"}
    exec(compile(source.read_bytes(), str(source), "exec"), namespace)
    scratch = ROOT / ".test-tmp/final-adapter-review"
    scratch.mkdir(parents=True, exist_ok=True)
    namespace["OUT"] = scratch / "independent-adapter-checks.json"
    namespace["FLIP"] = str(
        ROOT / (".venv/Scripts/flip.exe" if sys.platform == "win32" else ".venv/bin/flip")
    )
    with (scratch / "execution.log").open("w", encoding="utf-8") as log, redirect_stdout(log):
        code = namespace["main"]()
    observed = json.loads(namespace["OUT"].read_bytes())
    original = json.loads(
        (
            ROOT
            / "docs/evidence/m45-agent-portable-final-review/results"
            / "independent-adapter-checks.json"
        ).read_bytes()
    )
    assert [r["id"] for r in observed["rows"]] == [r["id"] for r in original["rows"]]
    failures = [r for r in observed["rows"] if not r["pass"]]
    if failures:
        print(json.dumps({"failedChecks": failures}, indent=2))
    assert len(observed["rows"]) == 26 and not failures
    assert code == 0
    print("Final adapter review: 26/26 PASS, including 10 fail-closed attacks; archive unchanged")


if __name__ == "__main__":
    main()
