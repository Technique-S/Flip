"""Real loopback ASGI server + external CLI; historical inputs, no live RPC."""

import copy
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
from flip_core.canonical import content_hash

ROOT = Path(__file__).resolve().parents[1]


def semantic(value):
    if isinstance(value, dict):
        return {k: semantic(v) for k, v in value.items() if k not in ("verifiedAt", "resources")}
    if isinstance(value, list):
        return [semantic(v) for v in value]
    return value


def main():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = dict(os.environ, FLIP_LOCAL_SOLVER="1")
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "flip_api.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-access-log",
            "--log-level",
            "error",
        ],
        cwd=ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )
    cases = []
    try:
        with httpx.Client(
            base_url=f"http://127.0.0.1:{port}", timeout=10, trust_env=False
        ) as client:
            deadline = time.monotonic() + 10
            while True:
                try:
                    if client.get("/healthz").status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                if server.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("Local ASGI server did not become ready")
                time.sleep(0.05)
            original = json.loads(
                (ROOT / "docs/schema/m3/examples/half-adder.request.json").read_bytes()
            )
            for operation, expected in (
                ("compose", None),
                ("compare", "EQUIVALENT"),
                ("compare", "DIFFERENT"),
            ):
                payload = copy.deepcopy(original)
                if expected == "DIFFERENT":
                    payload["project"]["candidate"]["outputs"].reverse()
                with tempfile.TemporaryDirectory(prefix="flip-m3-smoke-") as temporary:
                    path = Path(temporary) / "request.json"
                    path.write_text(json.dumps(payload), encoding="utf-8")
                    command = subprocess.run(
                        [sys.executable, "-m", "flip_cli", operation, "--project", str(path)],
                        cwd=ROOT,
                        capture_output=True,
                        timeout=15,
                    )
                    assert command.returncode == (1 if expected == "DIFFERENT" else 0), (
                        command.stderr
                    )
                    local = json.loads(command.stdout)
                response = client.post(f"/api/v1/{operation}", json=payload)
                assert response.status_code == 200, response.text
                remote = response.json()
                assert content_hash(semantic(local)) == content_hash(semantic(remote))
                if expected:
                    assert remote["report"]["verification"]["verdict"] == expected
                    assert remote["report"]["integrity"]["freshness"] == "HISTORICAL"
                cases.append(
                    {
                        "operation": operation,
                        "verdict": expected,
                        "semanticHash": content_hash(semantic(local)),
                    }
                )
    finally:
        server.terminate()
        try:
            server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.communicate()
    print(
        json.dumps(
            {"result": "PASS", "scope": "External CLI / real loopback ASGI, no RPC", "cases": cases}
        )
    )


if __name__ == "__main__":
    main()
