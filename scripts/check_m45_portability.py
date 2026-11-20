"""Run pinned OpenCode cases without rewriting independent evidence or its harness."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "2f3d6263edf4e62ad4e94718c99f6c1a79e350a1"
HARNESS = "fixtures/m45-portable-project/generators/run_portability_cases.py"


def main():
    source = (
        ROOT / "docs/evidence/m45-portable-project/harness/run_portability_cases.py.txt"
    ).read_bytes()
    if (
        hashlib.sha256(source).hexdigest()
        != "83551951a7b8d242f54cc3309968684fd4ab0d8b51bce4f3360a8fe1f08bae06"
    ):
        raise SystemExit("Independent harness checksum mismatch")
    namespace = {"__file__": str(ROOT / HARNESS), "__name__": "pinned_portability_cases"}
    exec(compile(source, HARNESS, "exec"), namespace)
    run = ROOT / ".test-tmp/portable-independent"
    run.mkdir(parents=True, exist_ok=True)
    namespace["RUN"] = run
    namespace["OUT"] = run / "executed-cases.json"
    namespace["FLIP"] = str(
        ROOT / (".venv/Scripts/flip.exe" if sys.platform == "win32" else ".venv/bin/flip")
    )
    # Evidence contains native engine identity: generate it with this run's actual engine.
    subprocess.run(
        [
            namespace["FLIP"],
            "export",
            "--project",
            str(ROOT / "docs/evidence/m45-portable-project/requests/web-export.json"),
            "--out",
            str(run / "evidence.json"),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    # The independent harness hardcodes its loopback port. Redirect only that
    # transport address, keeping all synthetic chain behavior and case assertions.
    server_factory = namespace["ThreadingHTTPServer"]
    invoke_case = namespace["invoke"]
    port = []

    def server(address, handler):
        instance = server_factory((address[0], 0), handler)
        port.append(instance.server_port)
        return instance

    def invoke(args, out_file=None):
        args = [f"http://127.0.0.1:{port[0]}" if a == "http://127.0.0.1:18762" else a for a in args]
        return invoke_case(args, out_file)

    namespace["ThreadingHTTPServer"] = server
    namespace["invoke"] = invoke
    namespace["main"]()
    observed = json.loads(namespace["OUT"].read_bytes())
    return 0 if observed["passed"] == observed["total"] == 12 else 1


if __name__ == "__main__":
    raise SystemExit(main())
