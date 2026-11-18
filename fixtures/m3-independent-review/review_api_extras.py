"""API gate and vectors-endpoint trust checks."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_common as rc  # noqa: E402

PY = sys.executable
REPO = rc.REPO
ENV = dict(os.environ)
ENV["PYTHONPATH"] = os.pathsep.join(str(REPO / "packages" / p / "src")
                                    for p in ("flip-core", "flip-cli", "flip-api"))
REQ = json.loads((HERE / "requests/valid_equivalent.json").read_bytes())


def start(port, solver):
    env = dict(ENV)
    if solver:
        env["FLIP_LOCAL_SOLVER"] = "1"
    else:
        env.pop("FLIP_LOCAL_SOLVER", None)
    p = subprocess.Popen([PY, "-m", "uvicorn", "flip_api.app:app", "--host", "127.0.0.1",
                          "--port", str(port)], cwd=REPO, env=env,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with httpx.Client(base_url=f"http://127.0.0.1:{port}", timeout=5) as c:
        for _ in range(40):
            try:
                if c.get("/healthz").status_code == 200:
                    return p
            except Exception:  # noqa: BLE001
                time.sleep(0.25)
    p.terminate()
    raise RuntimeError("server not ready")


def main():
    out = {}
    server = start(8767, False)
    try:
        with httpx.Client(base_url="http://127.0.0.1:8767", timeout=60) as c:
            r = c.post("/api/v1/compare", content=json.dumps(REQ).encode(),
                       headers={"content-type": "application/json"})
            out["compare_without_local_solver_flag"] = {
                "status": r.status_code, "body": r.json()}
            out["gate_blocks_unsafe_compare"] = r.status_code == 501
    finally:
        server.terminate(); server.wait(timeout=15)

    # Vectors: caller-supplied oracle must never produce a conclusive EQUIVALENT.
    base = rc.base_request()
    comp = rc.compile_project(base.project, base.imports)
    n = base.project.candidate.nIn
    rows = []
    for v in range(1 << n):
        bits = [(v >> i) & 1 for i in range(n)]
        outs = rc.ic.eval_recursive(
            rc.production_to_independent(comp.candidate), bits)
        rows.append({"inputs": {"encoding": "tap02-lsb0-v1", "width": n,
                                "bits": "".join(map(str, bits))},
                     "outputs": {"encoding": "tap02-lsb0-v1", "width": len(outs),
                                 "bits": "".join(map(str, outs))}})
    req = base.model_dump(mode="json")
    req["vectors"] = rows
    result = rc.execute("vectors", json.dumps(req, sort_keys=True,
                                              separators=(",", ":")).encode())
    out["vectors"] = {
        "verdict": result["verdict"], "coverage": result["coverage"],
        "solver": result["solver"], "rows": result["rows"],
        "freshness": result["freshness"],
        "never_equivalent": result["verdict"] in ("VECTORS_MATCH", "VECTORS_MISMATCH"),
    }
    (HERE / "api-gate-and-vectors.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
