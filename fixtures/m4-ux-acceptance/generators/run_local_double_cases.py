"""Execute import CLI cases against a LOCAL RPC DOUBLE (never a live chain).

The double reuses the repository's committed offline transport from
`packages/flip-core/tests/test_m2_import.py`. It serves archived M0/M0.5 bytes on
loopback only. Results are labelled LOCAL_DOUBLE_OFFLINE in the transcript and
must never be presented as current X Layer observations.

Usage from repository root:
    uv run --frozen python fixtures/m4-ux-acceptance/generators/run_local_double_cases.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/flip-core/tests"))
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))

from flip_core import abi  # noqa: E402
from test_m2_import import PROC, FakeChain, word  # noqa: E402


class NotFoundChain(FakeChain):
    """Same archived double, but nextId reports that circuit 1 does not exist."""

    def answer(self, method, params):
        if method == "eth_call" and params[0]["data"].startswith("0x" + abi.SELECTORS["nextId"]):
            return word(1)
        return super().answer(method, params)


EXEC = ROOT / "docs/evidence/m4-ux-acceptance/executed"
FLIP = ROOT / ".venv/Scripts/flip.exe"
PROCESSOR = PROC


class DoubleHandler(BaseHTTPRequestHandler):
    chain: FakeChain

    def do_POST(self):  # noqa: N802 - stdlib API spelling
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        try:
            result = self.chain.answer(payload["method"], payload["params"])
            body = json.dumps({"jsonrpc": "2.0", "id": payload["id"], "result": result}).encode()
        except Exception as exc:  # the double reports structured failures, not tracebacks
            body = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": payload.get("id"),
                    "error": {"code": -32000, "message": type(exc).__name__},
                }
            ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


def serve(chain: FakeChain):
    handler = type("BoundedDouble", (DoubleHandler,), {"chain": chain})
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run_command(case_id: str, description: str, argv: list[str]) -> dict:
    out = EXEC / f"{case_id}.stdout.txt"
    err = EXEC / f"{case_id}.stderr.txt"
    completed = subprocess.run([str(FLIP)] + argv, capture_output=True, cwd=ROOT, check=False)
    out.write_bytes(completed.stdout)
    err.write_bytes(completed.stderr)
    return {
        "id": case_id,
        "description": description,
        "command": "flip " + " ".join(argv),
        "exitCode": completed.returncode,
        "stdoutFile": f"docs/evidence/m4-ux-acceptance/executed/{case_id}.stdout.txt",
        "stdoutSha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr": completed.stderr.decode("utf-8", "replace").strip(),
        "provenance": "LOCAL_DOUBLE_OFFLINE_ARCHIVED_BYTES",
    }


def run_case(case_id: str, description: str, url: str, circuit_id: str) -> dict:
    return run_command(
        case_id,
        description,
        [
            "import",
            "--processor",
            PROCESSOR,
            "--id",
            circuit_id,
            "--rpc-url",
            url,
            "--timeout-ms",
            "2000",
            "--retries",
            "0",
        ],
    )


def main() -> None:
    EXEC.mkdir(parents=True, exist_ok=True)
    results = []

    normal = FakeChain()
    server, thread = serve(normal)
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        results.append(run_case("C27", "import success via local double", url, "1"))
    finally:
        server.shutdown()
        thread.join(timeout=5)

    # nextId == 1 makes circuit 1 absent; the importer's real not-found path
    # raises MISSING_REFERENCE before any netlist is read.
    missing = NotFoundChain()
    server, thread = serve(missing)
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        results.append(
            run_case("C28", "circuit not found (MISSING_REFERENCE) via local double", url, "1")
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    # Revalidate the genuine local-double import manifest after a simulated
    # beacon implementation upgrade. No netlist is rewritten.
    captured = json.loads((EXEC / "C27.stdout.txt").read_bytes())
    manifest_path = (
        ROOT / "fixtures/m4-ux-acceptance/cli-cases/requests/import-manifest-local-double.json"
    )
    manifest_path.write_text(json.dumps(captured["manifest"], indent=2) + "\n", encoding="utf-8")
    upgraded = FakeChain()
    upgraded.beacon_impl = "0x" + "cd" * 20
    server, thread = serve(upgraded)
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        results.append(
            run_command(
                "C30",
                "revalidate after beacon implementation change via local double",
                [
                    "revalidate",
                    "--manifest",
                    str(manifest_path.relative_to(ROOT)),
                    "--rpc-url",
                    url,
                    "--timeout-ms",
                    "2000",
                    "--retries",
                    "0",
                ],
            )
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    path = EXEC / "transcript.json"
    transcript = json.loads(path.read_text(encoding="utf-8-sig"))
    fresh_ids = {item["id"] for item in results}
    transcript["cases"] = [c for c in transcript["cases"] if c["id"] not in fresh_ids]
    transcript["cases"].extend(results)
    path.write_text(json.dumps(transcript, indent=2) + "\n", encoding="utf-8")
    for item in results:
        print(f"{item['id']} exit={item['exitCode']} {item['description']}")


if __name__ == "__main__":
    main()
