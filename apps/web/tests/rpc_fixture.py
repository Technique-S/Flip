"""Loopback synthetic RPC for browser acceptance only. Never imported by the product."""

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "packages/flip-core/tests"))
from test_m45_library import LibraryChain  # noqa: E402

chain = LibraryChain()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        value = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        record = {"jsonrpc": "2.0", "id": value["id"]}
        try:
            record["result"] = chain.answer(value["method"], value["params"])
        except KeyError:
            record["error"] = {"code": 3, "message": "execution reverted: no circuit"}
        except (ValueError, StopIteration):
            record["error"] = {"code": -32000, "message": "fixture lookup failed"}
        raw = json.dumps(record).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    HTTPServer(
        ("127.0.0.1", int(os.environ.get("FLIP_TEST_RPC_PORT", "18762"))), Handler
    ).serve_forever()
