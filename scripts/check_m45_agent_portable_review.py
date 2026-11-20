"""Replay the immutable final adapter review into scratch, never into its archive."""

import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

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
    # C10 inherits the RPC endpoint; a live successful read is not a metadata attack.
    # Reuse the accepted changed-dependency fixture for this negative environment.
    from test_m45_agent_workflow import chain_server
    from test_m45_library import LibraryChain

    chain = LibraryChain()
    chain.beacon_impl = "0x" + "cc" * 20
    with (
        chain_server(chain) as (_, settings),
        patch.dict(os.environ, {"FLIP_RPC_URL": settings.endpoint, "FLIP_RPC_RETRIES": "0"}),
        (scratch / "execution.log").open("w", encoding="utf-8") as log,
        redirect_stdout(log),
    ):
        code = namespace["main"]()
    assert chain.received, "Negative freshness test must actually perform trusted RPC reads"
    (scratch / "replay-context.json").write_text(
        json.dumps(
            {
                "defaultRpc": "LOOPBACK_CHANGED_BEACON_FIXTURE",
                "harnessRevision": "4ad32846a995255105aa027e9809599e2cb9562f",
                "trustedRpcRequests": len(chain.received),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
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
