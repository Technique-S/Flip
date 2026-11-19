"""Independent CLI vs API semantic parity for M4.5-2D debug operations."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-debugging-independent-review"
RUN = EVID / "results/run"
sys.path.insert(0, str(ROOT / "packages/flip-api/src"))
OUT = EVID / "results/debug-parity.json"


def main():
    os.environ["FLIP_LOCAL_SOLVER"] = "1"
    from fastapi.testclient import TestClient
    from flip_api.app import app

    client = TestClient(app, client=("127.0.0.1", 12345))
    rows = []
    for name in ("base", "D08", "B08", "verified-correction"):
        request_path = RUN / f"{name}.request.json"
        if not request_path.exists():
            continue
        payload = json.loads(request_path.read_bytes())
        if name == "verified-correction":
            # Reuse the genuine action from the base result.
            action = json.loads((RUN / "base.result.json").read_bytes())["actions"][0]["actionId"]
            payload["operation"] = "verify-correction"
            payload["actionId"] = action
        out = RUN / f"{name}.cli-parity.json"
        proc = subprocess.run([str(ROOT / ".venv/Scripts/flip.exe"), "debug",
                               "--request", str(request_path), "--out", str(out)],
                              cwd=ROOT, env=dict(os.environ), capture_output=True, timeout=120)
        cli = json.loads(out.read_bytes()) if out.exists() else None
        response = client.post("/api/v1/debug", json=payload)
        api = response.json()
        keep = ("classification", "attribution", "differingOutputBits", "semanticHash",
                "projectHash", "executionHash", "diagnosticEngineHash")

        def shape(value):
            return {k: value.get(k) for k in keep} if isinstance(value, dict) else value

        rows.append({"name": name, "cliExit": proc.returncode,
                     "apiStatus": response.status_code,
                     "shapesMatch": shape(cli) == shape(api),
                     "cliShape": shape(cli), "apiShape": shape(api)})

    # Boundary: solver disabled returns 501.
    os.environ["FLIP_LOCAL_SOLVER"] = "0"
    disabled = client.post("/api/v1/debug", json=json.loads(
        (RUN / "base.request.json").read_bytes()))
    record = {"artifactType": "DEBUG_CLI_API_PARITY",
              "testedSha": "b9d3fc3f87d34cc6bd46e2a716504fe113f44f48",
              "rows": rows, "solverDisabledStatus": disabled.status_code,
              "passed": all(r["shapesMatch"] and r["apiStatus"] == 200 for r in rows)
                        and disabled.status_code == 501}
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps({"passed": record["passed"], "rows": len(rows),
                      "solverDisabledStatus": disabled.status_code}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
