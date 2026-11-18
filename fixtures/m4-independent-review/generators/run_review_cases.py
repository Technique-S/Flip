# ruff: noqa: E501
"""M4-C independent CLI/API parity runner.

Executes the frozen M4-B 30-case corpus plus M4 product-command cases against
the checked-out M4 build. Raw stdout/stderr bytes are preserved. No claim is
inferred from process exit alone.

    uv run --frozen python fixtures/m4-independent-review/generators/run_review_cases.py
"""

from __future__ import annotations

import hashlib
import json
import os
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

FLIP = Path(os.environ.get("M4C_FLIP", str(ROOT / ".venv/Scripts/flip.exe")))
REQ = ROOT / "fixtures/m4-independent-review/corpus"
DL = ROOT / "fixtures/m4-independent-review/downloads"
EXEC = Path(
    os.environ.get("M4C_EXEC_DIR", str(ROOT / "docs/evidence/m4-independent-review/executed"))
)
PROCESSOR = PROC


class NotFoundChain(FakeChain):
    def answer(self, method, params):
        if method == "eth_call" and params[0]["data"].startswith("0x" + abi.SELECTORS["nextId"]):
            return word(1)
        return super().answer(method, params)


class Handler(BaseHTTPRequestHandler):
    chain: FakeChain

    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        try:
            result = self.chain.answer(payload["method"], payload["params"])
            body = json.dumps({"jsonrpc": "2.0", "id": payload["id"], "result": result}).encode()
        except Exception as exc:
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


def serve(chain):
    handler = type("BoundedDouble", (Handler,), {"chain": chain})
    server = HTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def run(case_id: str, description: str, argv: list[str], provenance="M3_CORPUS_REPLAY") -> dict:
    out = EXEC / f"{case_id}.stdout.txt"
    err = EXEC / f"{case_id}.stderr.txt"
    completed = subprocess.run([str(FLIP)] + argv, cwd=ROOT, capture_output=True, check=False)
    out.write_bytes(completed.stdout)
    err.write_bytes(completed.stderr)
    record = {
        "id": case_id,
        "description": description,
        "command": "flip " + " ".join(argv),
        "exitCode": completed.returncode,
        "stdoutFile": (EXEC.relative_to(ROOT) / f"{case_id}.stdout.txt").as_posix(),
        "stdoutSha256": hashlib.sha256(completed.stdout).hexdigest(),
        "stderr": completed.stderr.decode("utf-8", "replace").strip(),
        "provenance": provenance,
    }
    print(f"{case_id} exit={completed.returncode} {description}")
    return record


def main() -> None:
    EXEC.mkdir(parents=True, exist_ok=True)
    results: list[dict] = []

    def simple(case_id, desc, argv, prov="M3_CORPUS_REPLAY"):
        results.append(run(case_id, desc, argv, prov))

    req = lambda name: str(REQ / name)  # noqa: E731
    simple("C01", "version", ["--version"])
    simple("C02", "help", ["--help"])
    simple("C03", "compose baseline", ["compose", "--project", req("half-adder-equivalent.json")])
    simple("C04", "compare EQUIVALENT", ["compare", "--project", req("half-adder-equivalent.json")])
    simple(
        "C05",
        "compare DIFFERENT",
        ["compare", "--project", req("half-adder-different-output-order.json")],
    )
    simple(
        "C06",
        "compare UNKNOWN timeout",
        ["compare", "--project", req("half-adder-unknown-timeout.json")],
    )
    simple("C07", "vectors", ["vectors", "--project", req("half-adder-vectors.json")])
    simple(
        "C08",
        "caller CURRENT flag",
        ["compare", "--project", req("half-adder-current-freshness-claim.json")],
    )
    simple("C09", "malformed input", ["compare", "--project", req("malformed-request.json")])
    simple("C10", "unsupported version", ["compare", "--project", req("unsupported-version.json")])
    simple(
        "C11",
        "wrong chain inspect",
        ["inspect", "--chain-id", "8453", "--processor", PROCESSOR, "--id", "1"],
    )
    simple("C12", "invalid pin map", ["compare", "--project", req("invalid-pin-map.json")])
    simple(
        "C13",
        "wrong chain import",
        ["import", "--chain-id", "8453", "--processor", PROCESSOR, "--id", "1"],
    )
    simple(
        "C14",
        "RPC unavailable",
        [
            "inspect",
            "--processor",
            PROCESSOR,
            "--id",
            "1",
            "--rpc-url",
            "http://127.0.0.1:1",
            "--timeout-ms",
            "200",
            "--retries",
            "0",
        ],
    )
    simple(
        "C15",
        "validate contract",
        ["validate", "circuit-identity", "docs/schema/examples/circuit-identity.json"],
    )
    simple(
        "C16",
        "canonical contract",
        ["canonical", "circuit-identity", "docs/schema/examples/circuit-identity.json"],
    )
    simple("C17", "hash manifest", ["hash", "manifest", "docs/schema/examples/manifest.json"])
    simple(
        "C18", "preflight baseline", ["preflight", "--project", req("half-adder-equivalent.json")]
    )
    simple("C19", "export baseline", ["export", "--project", req("half-adder-equivalent.json")])
    simple("C20", "sample baseline", ["sample"])
    simple(
        "C21",
        "revalidate wrong chain",
        ["revalidate", "--chain-id", "8453", "--manifest", req("import-manifest.json")],
    )
    simple("C22", "consume valid claim", ["consume", "--project", req("consumption-valid.json")])
    simple(
        "C23",
        "consume forged verdict",
        ["consume", "--project", req("consumption-forged-verdict.json")],
    )
    simple(
        "C24",
        "consume changed reference",
        ["consume", "--project", req("consumption-changed-reference.json")],
    )
    simple(
        "C25",
        "consume CURRENT relabel",
        ["consume", "--project", req("consumption-current-relabel.json")],
    )
    simple(
        "C26",
        "consume DIFFERENT witness",
        ["consume", "--project", req("consumption-different.json")],
    )

    # C27/C28/C30 use a loopback double built from the repository's own
    # committed offline transport; they are never live chain observations.
    normal = FakeChain()
    server, thread = serve(normal)
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        results.append(
            run(
                "C27",
                "import success local double",
                [
                    "import",
                    "--processor",
                    PROCESSOR,
                    "--id",
                    "1",
                    "--rpc-url",
                    url,
                    "--timeout-ms",
                    "2000",
                    "--retries",
                    "0",
                ],
                "LOCAL_DOUBLE_OFFLINE",
            )
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    missing = NotFoundChain()
    server, thread = serve(missing)
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        results.append(
            run(
                "C28",
                "circuit not found local double",
                [
                    "import",
                    "--processor",
                    PROCESSOR,
                    "--id",
                    "1",
                    "--rpc-url",
                    url,
                    "--timeout-ms",
                    "2000",
                    "--retries",
                    "0",
                ],
                "LOCAL_DOUBLE_OFFLINE",
            )
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    upgraded = FakeChain()
    upgraded.beacon_impl = "0x" + "cd" * 20
    server, thread = serve(upgraded)
    try:
        url = f"http://127.0.0.1:{server.server_port}"
        results.append(
            run(
                "C30",
                "revalidate after beacon upgrade",
                [
                    "revalidate",
                    "--manifest",
                    req("import-manifest-local-double.json"),
                    "--rpc-url",
                    url,
                    "--timeout-ms",
                    "2000",
                    "--retries",
                    "0",
                ],
                "LOCAL_DOUBLE_OFFLINE",
            )
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    # Repeat determinism: ten builds on this M4 build.
    hashes = []
    for _ in range(10):
        completed = subprocess.run(
            [str(FLIP), "compose", "--project", req("half-adder-equivalent.json")],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        hashes.append(json.loads(completed.stdout)["candidateIdentity"]["netlistHash"])
    distinct = sorted(set(hashes))
    (EXEC / "C29.stdout.txt").write_text(
        json.dumps({"distinct": distinct}, indent=2) + "\n", encoding="utf-8"
    )
    results.append(
        {
            "id": "C29",
            "description": "10 deterministic compose builds",
            "command": "flip compose --project .../half-adder-equivalent.json (x10)",
            "exitCode": 0
            if distinct == ["0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce"]
            else 3,
            "stdoutFile": (EXEC.relative_to(ROOT) / "C29.stdout.txt").as_posix(),
            "stdoutSha256": hashlib.sha256(json.dumps(distinct).encode()).hexdigest(),
            "stderr": "",
            "provenance": "M3_CORPUS_REPLAY",
        }
    )
    print(f"C29 distinct={distinct}")

    # New M4 product commands and evidence from the real browser download.
    evidence = str(DL / "evidence.json")
    project = str(DL / "project.json")
    simple(
        "M01",
        "sample half-adder",
        ["sample", "half-adder", "--out", str(EXEC / "M01-project.json")],
        "M4_PRODUCT_COMMAND",
    )
    simple(
        "M02",
        "sample swapped",
        ["sample", "swapped", "--out", str(EXEC / "M02-mutation.json")],
        "M4_PRODUCT_COMMAND",
    )
    simple(
        "M03",
        "export from downloaded project",
        ["export", "--project", project, "--out", str(EXEC / "M03-evidence.json")],
        "M4_PRODUCT_COMMAND",
    )
    simple(
        "M04",
        "inspect browser evidence",
        ["inspect-evidence", "--bundle", evidence],
        "BROWSER_DOWNLOADED_EVIDENCE",
    )
    simple(
        "M05",
        "verify browser evidence",
        ["verify-bundle", "--project", project, "--bundle", evidence],
        "BROWSER_DOWNLOADED_EVIDENCE",
    )
    simple(
        "M06",
        "preflight offline project",
        [
            "preflight",
            "--project",
            project,
            "--rpc-url",
            "http://127.0.0.1:1",
            "--timeout-ms",
            "200",
            "--retries",
            "0",
        ],
        "M4_PRODUCT_COMMAND",
    )
    simple(
        "M07",
        "export with unreachable chain observation",
        [
            "export",
            "--project",
            project,
            "--observe-chain",
            "--rpc-url",
            "http://127.0.0.1:1",
            "--timeout-ms",
            "200",
            "--retries",
            "0",
            "--out",
            str(EXEC / "M07-observe.json"),
        ],
        "M4_PRODUCT_COMMAND",
    )

    path = EXEC / "transcript.json"
    path.write_text(
        json.dumps(
            {
                "schemaVersion": "m4-independent-review-1",
                "reviewTarget": "f4d5b3a981d4cd5906c3ab11942c106f5becc7a9",
                "cases": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"transcript: {path}")


if __name__ == "__main__":
    main()
