"""Execute the M4.5-1A corpus commands and record observed CLI outcomes.

Only the real `flip` CLI is invoked. A loopback synthetic RPC (Codex-owned
apps/web/tests/rpc_fixture.py) serves the library/import/revalidate/preflight cases.
No live chain, signing or publication. Results are written under docs/evidence.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-agent-workflow"
sys.path.insert(0, str(ROOT / "packages/flip-core/tests"))
from test_m45_library import LibraryChain  # noqa: E402

chain = LibraryChain()
OUT = EVID / "results/executed-commands.json"
PORT = 18762


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        try:
            reply = {"jsonrpc": "2.0", "id": body["id"],
                     "result": chain.answer(body["method"], body["params"])}
        except KeyError:
            reply = {"jsonrpc": "2.0", "id": body["id"],
                     "error": {"code": 3, "message": "execution reverted: no circuit"}}
        raw = json.dumps(reply).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def field(value, dotted):
    node = value
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def main() -> int:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    corpus = json.loads((EVID / "cases/agent-workflow-cases.json").read_bytes())
    negatives = json.loads((EVID / "cases/negative-cases.json").read_bytes())
    entries = []
    work = EVID / "results/run"
    work.mkdir(parents=True, exist_ok=True)
    base_env = dict(os.environ, FLIP_RPC_URL=f"http://127.0.0.1:{PORT}",
                    FLIP_RPC_RETRIES="0")
    for group in (corpus["cases"], negatives["cases"]):
        for case in group:
            if case["caseId"] == "AW-14":
                imported = work / "source.json"
                if imported.exists():
                    payload = json.loads(imported.read_bytes())
                    (work / "manifest.json").write_text(
                        json.dumps(payload["manifest"], indent=2, sort_keys=True) + "\n",
                        encoding="utf-8", newline="\n")
            for index, command in enumerate(case.get("commands", [])):
                env = dict(base_env, **command.get("env", {}))
                def resolve_arg(argument):
                    if argument.startswith((".venv/", "docs/", "fixtures/")):
                        return str(ROOT / argument)
                    return argument

                argv = [resolve_arg(arg) for arg in command["argv"]]
                started = time.monotonic()
                try:
                    proc = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True,
                                          timeout=120)
                    exit_code, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
                except subprocess.TimeoutExpired as exc:
                    exit_code, stdout, stderr = 124, (exc.stdout or b""), (exc.stderr or b"")
                out_files = [a for a in argv if a.endswith(".json") and "--out" in argv[:argv.index(a)]]
                parsed, sha = None, None
                if out_files:
                    path = Path(out_files[-1])
                    if path.exists():
                        raw = path.read_bytes()
                        sha, size = digest(raw), len(raw)
                        try:
                            parsed = json.loads(raw)
                        except ValueError:
                            parsed = None
                    else:
                        size = None
                else:
                    size = None
                expected_fields = {}
                for key, expected in command.get("expectedFields", {}).items():
                    actual = field(parsed, key) if isinstance(parsed, dict) else None
                    expected_fields[key] = {"expected": expected, "actual": actual,
                                            "matches": actual == expected}
                entries.append({
                    "caseId": case["caseId"], "commandIndex": index,
                    "argv": argv, "expectedExit": command.get("expectedExit"),
                    "exit": exit_code,
                    "exitMatches": exit_code == command.get("expectedExit"),
                    "stdoutSha256": digest(stdout), "stderrSha256": digest(stderr),
                    "stderrTail": stderr.decode("utf-8", "replace")[-300:],
                    "outputFile": out_files[-1] if out_files else None,
                    "outputSha256": sha, "outputBytes": size,
                    "expectedFields": expected_fields,
                    "wallSeconds": round(time.monotonic() - started, 3),
                })
    server.shutdown()
    record = {
        "artifactType": "EXECUTED_CLI_COMMANDS",
        "baselineSha": "1136b187bd68328cea4975caea50904ccece08fd",
        "productionEntrypoint": "flip CLI (real subprocess)",
        "rpcDouble": "loopback synthetic JSON-RPC, chain 196",
        "entries": entries,
        "exitMatches": sum(1 for e in entries if e["exitMatches"]),
        "total": len(entries),
    }
    EVID.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps({"total": len(entries), "exitMatches": record["exitMatches"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
