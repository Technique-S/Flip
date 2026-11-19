"""Independent CLI/API parity checks against an OpenCode-owned loopback RPC double.

Invokes the real `flip library` CLI subprocess and the real FastAPI application via
TestClient with FLIP_RPC_URL pointed at this harness's bounded fake chain. No live RPC.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))
sys.path.insert(0, str(ROOT / "packages/flip-api/src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient  # noqa: E402
from independent_core_checks import IndependentChain  # noqa: E402

RESULTS = (Path(__file__).resolve().parents[3] / "docs/evidence/m45-library-independent-review"
           / "results")
OUT = RESULTS / "independent-cli-api-checks.json"
WORK = RESULTS / "cli-work"
PORT = 18772
chain = IndependentChain()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        try:
            payload = {"jsonrpc": "2.0", "id": body["id"],
                       "result": chain.answer(body["method"], body["params"])}
        except KeyError:
            payload = {"jsonrpc": "2.0", "id": body["id"],
                       "error": {"code": 3, "message": "execution reverted: no circuit"}}
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    os.environ["FLIP_RPC_URL"] = f"http://127.0.0.1:{PORT}"
    os.environ["FLIP_RPC_RETRIES"] = "0"
    os.environ["FLIP_LOCAL_SOLVER"] = "1"
    env = dict(os.environ)
    WORK.mkdir(parents=True, exist_ok=True)
    request = {"schemaVersion": "m45-library-1.0.0", "kind": "LIBRARY_REQUEST",
               "operation": "discover", "limit": 2}
    req_path = WORK / "discover.request.json"
    req_path.write_text(json.dumps(request), encoding="utf-8")
    catalog_path = WORK / "catalog.json"
    cli_out = WORK / "cli.result.json"
    if catalog_path.exists():
        catalog_path.unlink()

    cli = subprocess.run(
        [str(ROOT / ".venv/Scripts/flip.exe"), "library", "--request", str(req_path),
         "--catalog", str(catalog_path), "--out", str(cli_out)],
        capture_output=True, text=True, env=env, timeout=60,
    )
    cli_result = json.loads(cli_out.read_text(encoding="utf-8")) if cli_out.exists() else None
    saved_catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else None

    from flip_api.app import app
    api = TestClient(app)
    api_response = api.post("/api/library/v1/execute", json=request)
    api_result = api_response.json()
    bad = api.post("/api/library/v1/execute", json={"schemaVersion": "m45-library-1.0.0",
                                                    "kind": "LIBRARY_REQUEST",
                                                    "operation": "unknown"})
    corrupt = api.post("/api/library/v1/execute", json={**request, "catalog": {
        "schemaVersion": "m45-library-1.0.0", "kind": "LIBRARY_CATALOG",
        "records": [], "overlay": {"favorites": [{"label": "missing identity"}]}}})

    def shape(value):
        if not isinstance(value, dict):
            return value
        return {"status": value.get("status"), "total": value.get("total"),
                "errorCode": value.get("errorCode"),
                "keys": [r["identity"]["processor"] + ":" + str(r["identity"]["circuitId"])
                         for r in value.get("results", [])],
                "freshness": sorted({r["freshness"] for r in value.get("catalog", {}).get("records", [])})}

    checks = {
        "cliExit": cli.returncode,
        "cliStatus": cli_result.get("status") if cli_result else None,
        "apiStatus": api_result.get("status"),
        "apiHttpCode": api_response.status_code,
        "shapesMatch": shape(cli_result) == shape(api_result),
        "cliShape": shape(cli_result),
        "apiShape": shape(api_result),
        "catalogPersisted": saved_catalog is not None,
        "persistedKeys": [r["identity"]["processor"] + ":" + str(r["identity"]["circuitId"])
                          for r in (saved_catalog or {}).get("records", [])],
        "invalidOperationHttp": bad.status_code,
        "corruptCatalogHttp": corrupt.status_code,
        "corruptCatalogCode": (corrupt.json().get("error") or {}).get("code"),
        "cliStderrTail": cli.stderr[-300:],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    server.shutdown()
    print(json.dumps({k: checks[k] for k in ("cliExit", "cliStatus", "apiStatus",
                                            "shapesMatch", "invalidOperationHttp",
                                            "corruptCatalogHttp")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
