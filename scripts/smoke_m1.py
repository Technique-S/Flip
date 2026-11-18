"""Bounded CLI and real ASGI loopback smoke; never contact a chain endpoint."""

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    fixture = ROOT / "docs/schema/examples/project.json"
    cli = subprocess.run(
        [sys.executable, "-m", "flip_cli", "canonical", "project", str(fixture)],
        capture_output=True,
        check=True,
        timeout=10,
    )
    deferred = subprocess.run(
        [sys.executable, "-m", "flip_cli", "compare"],
        capture_output=True,
        timeout=10,
    )
    if (
        deferred.returncode != 6
        or json.loads(deferred.stdout)["error"]["code"] != "NOT_IMPLEMENTED"
    ):
        raise RuntimeError("CLI compare did not return NOT_IMPLEMENTED / exit 6")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
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
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + 15
        while True:
            try:
                with urllib.request.urlopen(base + "/healthz", timeout=1) as response:
                    if json.load(response) != {"status": "M1_CONTRACTS_ONLY"}:
                        raise RuntimeError("unexpected liveness contract")
                break
            except urllib.error.URLError:
                if server.poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError("ASGI startup failed") from None
                time.sleep(0.1)
        request = urllib.request.Request(
            base + "/api/v1/contracts/project/validate",
            data=fixture.read_bytes(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5) as response:
            if response.read() + b"\n" != cli.stdout:
                raise RuntimeError("CLI/API canonical contract bytes differ")
        request = urllib.request.Request(base + "/api/v1/compare", data=b"{}", method="POST")
        try:
            urllib.request.urlopen(request, timeout=5)
        except urllib.error.HTTPError as error:
            if error.code != 501 or json.load(error)["error"]["code"] != "NOT_IMPLEMENTED":
                raise RuntimeError("unexpected compare response") from error
        else:
            raise RuntimeError("API compare did not return HTTP 501")
    finally:
        server.terminate()
        try:
            server.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.communicate(timeout=5)
    print("PASS: CLI/API canonical bytes, CLI exit 6, real ASGI liveness and HTTP 501; no RPC.")


if __name__ == "__main__":
    main()
