"""CLI/API/core parity and security boundaries for Portable 1.1."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-portable-independent-review"
RUN = EVID / "results/run"
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))
sys.path.insert(0, str(ROOT / "packages/flip-api/src"))

from flip_core.canonical import canonical_bytes  # noqa: E402
from flip_core.portable import bounded_operation  # noqa: E402
from flip_core.workflow import sample  # noqa: E402

OUT = EVID / "results/portable-api.json"
FLIP = str(ROOT / ".venv/Scripts/flip.exe")
GOLD = json.loads((ROOT / "docs/schema/m45-portable-project/1.1.0/golden.json").read_bytes())


def main():
    from fastapi.testclient import TestClient
    from flip_api.app import app

    client = TestClient(app, client=("127.0.0.1", 12345))
    body = dict(schemaVersion="flip-portable-project-1.1.0", kind="PORTABLE_REQUEST",
                operation="validate", package=GOLD["packages"][0])
    resp = client.post("/api/v1/portable", json=body)
    api = resp.json()
    core = bounded_operation(copy := json.loads(json.dumps(body)))
    parity = api.get("executionRequestHash") == core.get("executionRequestHash")

    # CLI parity
    path = RUN / "api.request.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_bytes(body).decode() + "\n", encoding="utf-8")
    proc = subprocess.run([FLIP, "portable", "--request", str(path)],
                          cwd=ROOT, env=dict(os.environ), capture_output=True, timeout=120)
    cli = json.loads(proc.stdout)

    # replay-evidence requires solver opt-in + loopback.
    replay = dict(body, operation="replay-evidence", artifacts={})
    os.environ["FLIP_LOCAL_SOLVER"] = "0"
    gated = client.post("/api/v1/portable", json=replay)
    os.environ["FLIP_LOCAL_SOLVER"] = "1"
    allowed = client.post("/api/v1/portable", json=replay)

    record = {
        "artifactType": "PORTABLE_API_CHECK", "testedSha": "136b1115ee0f5ffe0a5583d68c474641fdce1ca1",
        "apiStatus": resp.status_code, "coreApiParity": parity,
        "cliExit": proc.returncode,
        "cliApiParity": cli.get("executionRequestHash") == api.get("executionRequestHash"),
        "replayGatedStatus": gated.status_code, "replayAllowedStatus": allowed.status_code,
    }
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
