"""Execute real CLI commands for the portability cases and record observed behavior."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/flip-core/tests"))
from test_m2_import import FakeChain, address_word, word  # noqa: E402


class StaleChain(FakeChain):
    """Loopback double whose beacon implementation differs from the archived manifest."""

    def __init__(self):
        super().__init__()
        self.beacon_impl = "0x" + "dd" * 20

    def answer(self, method, params):
        if method == "eth_call" and params[0]["data"].startswith("0x5c60da1b"):
            return address_word(self.beacon_impl)
        return super().answer(method, params)


class StaleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        try:
            payload = {"jsonrpc": "2.0", "id": body["id"],
                       "result": STALE_CHAIN.answer(body["method"], body["params"])}
        except KeyError:
            payload = {"jsonrpc": "2.0", "id": body["id"],
                       "error": {"code": 3, "message": "execution reverted: no circuit"}}
        raw = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args):
        pass


STALE_CHAIN = StaleChain()

EVID = ROOT / "docs/evidence/m45-portable-project"
RUN = EVID / "results/run"
FLIP = str(ROOT / ".venv/Scripts/flip.exe")
OUT = EVID / "results/executed-cases.json"


def invoke(argv, out_file=None):
    args = [FLIP] + argv
    if out_file:
        args += ["--out", str(RUN / out_file)]
    proc = subprocess.run(args, cwd=ROOT, env=dict(os.environ, FLIP_LOCAL_SOLVER="1"),
                          capture_output=True, timeout=120)
    result = None
    if out_file and (RUN / out_file).exists():
        try:
            result = json.loads((RUN / out_file).read_bytes())
        except ValueError:
            result = None
    stdout = proc.stdout.decode("utf-8", "replace")
    try:
        parsed_stdout = json.loads(stdout)
    except ValueError:
        parsed_stdout = None
    return {"argv": args, "exit": proc.returncode,
            "result": result, "stdout": parsed_stdout,
            "stderrTail": proc.stderr.decode("utf-8", "replace")[-200:]}


def req(name):
    return str(EVID / "requests" / name)


def summarize(record):
    r = record["result"] or record["stdout"] or {}
    return {"exit": record["exit"],
            "status": r.get("status") or (r.get("error") or {}).get("code"),
            "kind": r.get("kind"),
            "classification": r.get("classification"),
            "differingBits": r.get("differingOutputBits"),
            "netlistHash": (r.get("manifest") or {}).get("netlistHash")
                           or r.get("netlistHash"),
            "freshness": (r.get("chainObservation") or {}).get("integrity", {}).get("freshness")
                         if isinstance(r.get("chainObservation"), dict) else None,
            "contentHash": r.get("contentHash"),
            "stderrTail": record["stderrTail"]}


def main():
    server = ThreadingHTTPServer(("127.0.0.1", 18762), StaleHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    rows = []

    # P01 web export -> CLI import
    a = invoke(["compose", "--project", req("web-export.json")], "p01-compose.json")
    rows.append({"caseId": "P01", "steps": [summarize(a)],
                 "passed": a["exit"] == 0})
    # P02 CLI export -> web import (compose is web's validation path)
    a = invoke(["compose", "--project", req("cli-export.json")], "p02-compose.json")
    rows.append({"caseId": "P02", "steps": [summarize(a)],
                 "passed": a["exit"] == 0})
    # P03 edits and re-import
    a = invoke(["compose", "--project", req("edited.json")], "p03-compose.json")
    rows.append({"caseId": "P03", "steps": [summarize(a)],
                 "passed": a["exit"] == 0})
    # P04 vectors are separate
    a = invoke(["vectors", "--project", req("vector-request.json")], "p04-vectors.json")
    base = json.loads(Path(req("web-export.json")).read_bytes())
    rows.append({"caseId": "P04", "vectorsEmbeddedInProject": "vectors" in base,
                 "steps": [summarize(a)], "passed": a["exit"] == 0
                 and "vectors" not in base})
    # P05 changed implementation -> revalidate stale (local manifest double via CLI revalidate)
    a = invoke(["revalidate", "--manifest", str(EVID / "requests/changed-impl.manifest.json"),
                "--rpc-url", "http://127.0.0.1:18762"], "p05-revalidate.json")
    rows.append({"caseId": "P05", "steps": [summarize(a)],
                 "passed": a["exit"] in (2, 7)})
    # P06 missing dependency closure
    a = invoke(["compose", "--project", req("missing-dep.json")], "p06-compose.json")
    rows.append({"caseId": "P06", "steps": [summarize(a)],
                 "passed": a["exit"] == 3})
    # P07/P09/P10 need evidence bundle derived from the run evidence
    evidence = json.loads((RUN / "evidence.json").read_bytes())
    stale = json.loads(json.dumps(evidence))
    stale["chainObservation"] = {
        "schemaVersion": "1.0.0", "chainId": 196,
        "candidateNetlistHash": "0x" + "11" * 32,
        "manifestHash": "0x" + "11" * 32,
        "mode": "READ_ONLY_ETH_CALL", "status": "UNKNOWN",
        "reasonCode": "IMPLEMENTATION_CHANGED", "observation": None,
        "integrity": {"freshness": "STALE", "checkedBlock": None},
    }
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "packages/flip-core/src"))
    from flip_core.canonical import content_hash
    stale["contentHash"] = content_hash({k: v for k, v in stale.items() if k != "contentHash"})
    (RUN / "stale-evidence.json").write_text(json.dumps(stale, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    a = invoke(["verify-bundle", "--project", req("web-export.json"),
                "--bundle", str(RUN / "stale-evidence.json")], "p07-replay.json")
    rows.append({"caseId": "P07", "steps": [summarize(a)],
                 "passed": a["exit"] in (0, 7)})
    a = invoke(["verify-bundle", "--project", req("other-project.json"),
                "--bundle", str(RUN / "evidence.json")], "p09-replay.json")
    rows.append({"caseId": "P09", "steps": [summarize(a)],
                 "passed": a["exit"] in (3, 7)})
    corrupt = json.loads(json.dumps(evidence))
    corrupt["contentHash"] = "0x" + "00" * 32
    (RUN / "corrupt-hash.json").write_text(json.dumps(corrupt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    a = invoke(["verify-bundle", "--project", req("web-export.json"),
                "--bundle", str(RUN / "corrupt-hash.json")], "p10-replay.json")
    rows.append({"caseId": "P10", "steps": [summarize(a)],
                 "passed": a["exit"] == 3})
    # P08 incorrect schema version
    a = invoke(["compose", "--project", req("invalid-version.json")], "p08-compose.json")
    rows.append({"caseId": "P08", "steps": [summarize(a)],
                 "passed": a["exit"] == 3})
    # P11 incompatible revision
    a = invoke(["compose", "--project", req("bad-revision.json")], "p11-compose.json")
    rows.append({"caseId": "P11", "steps": [summarize(a)],
                 "passed": a["exit"] == 3})
    # P12 complete historical reproduction
    a = invoke(["compare", "--project", req("web-export.json")], "p12-compare.json")
    rows.append({"caseId": "P12", "steps": [summarize(a)],
                 "passed": a["exit"] == 0 and (a["result"] or {}).get("report", {}).get("verification", {}).get("verdict") == "EQUIVALENT"})

    server.shutdown()
    record = {"artifactType": "EXECUTED_PORTABILITY_CASES",
              "baselineSha": "bba6f3d301b08c0dcbbfd0b363b99a15179414db",
              "productionEntrypoint": "flip CLI (real subprocess)",
              "rows": rows, "passed": sum(1 for r in rows if r["passed"]),
              "total": len(rows)}
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps({"passed": record["passed"], "total": record["total"],
                      "failures": [r["caseId"] for r in rows if not r["passed"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
