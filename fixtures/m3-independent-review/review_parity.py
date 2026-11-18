"""Task D: real CLI/API trust-parity checks against the reviewed commit."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
REQ = HERE / "requests"
sys.path.insert(0, str(HERE))
import review_common as rc  # noqa: E402

PY = sys.executable
REPO = rc.REPO
ENV = dict(os.environ)
ENV["PYTHONPATH"] = os.pathsep.join(str(REPO / "packages" / p / "src")
                                    for p in ("flip-core", "flip-cli", "flip-api"))
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"


def cli(operation, request_file):
    cp = subprocess.run(
        [PY, "-m", "flip_cli", operation, "--project", str(REQ / request_file)],
        cwd=REPO, env=ENV, capture_output=True, timeout=180,
    )
    out = cp.stdout.strip()
    try:
        value = json.loads(out)
        verdict = (value.get("report", {}).get("verification", {})
                   .get("verdict", value.get("verdict")))
    except Exception:  # noqa: BLE001
        value, verdict = None, None
    return {"returncode": cp.returncode, "verdict": verdict,
            "stdout_sha256": hashlib.sha256(out).hexdigest(),
            "normalized_sha256": hashlib.sha256(json.dumps(
                normalize(value), sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "stdout_bytes": len(out), "stderr_tail": cp.stderr.decode(errors="replace")[-200:]}


def api(client, path, payload=None):
    r = client.post(path, content=json.dumps(payload, sort_keys=True,
                                              separators=(",", ":")).encode(),
                    headers={"content-type": "application/json"}, timeout=180)
    body = r.content
    try:
        value = json.loads(body)
        verdict = (value.get("report", {}).get("verification", {})
                   .get("verdict", value.get("verdict")))
        code = value.get("code")
    except Exception:  # noqa: BLE001
        value, verdict, code = None, None, None
    return {"status": r.status_code, "verdict": verdict, "code": code,
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "normalized_sha256": hashlib.sha256(json.dumps(
                normalize(value), sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "body_bytes": len(body)}


def load(name):
    return json.loads((REQ / name).read_bytes())


def normalize(value):
    """Strip volatile fields so two separate executions can be compared."""
    if not isinstance(value, dict):
        return value
    v = copy.deepcopy(value)
    v.pop("verifiedAt", None)
    res = v.get("resources")
    if isinstance(res, dict):
        for key in ("totalMs", "wallMs", "cpuMs", "peakBytes"):
            res.pop(key, None)
    return v


def main():
    rows = {"cli": {}, "api": {}, "comparisons": {}, "server": {}}
    for op, fn in (
        ("compare_equivalent", ("compare", "valid_equivalent.json")),
        ("compare_different", ("compare", "valid_different.json")),
        ("consume_valid", ("consume", "valid_consume.json")),
        ("consume_forged_equivalent", ("consume", "forged_equivalent_consume.json")),
        ("consume_invalid_shape", ("consume", "invalid_proof_shape.json")),
        ("compose", ("compose", "valid_equivalent.json")),
    ):
        rows["cli"][op] = cli(*fn)

    env = dict(ENV)
    env["FLIP_LOCAL_SOLVER"] = "1"
    server = subprocess.Popen(
        [PY, "-m", "uvicorn", "flip_api.app:app", "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=REPO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        with httpx.Client(base_url=BASE, timeout=5) as probe:
            for _ in range(40):
                try:
                    if probe.get("/healthz").status_code == 200:
                        break
                except Exception:  # noqa: BLE001
                    time.sleep(0.25)
            else:
                raise RuntimeError("API server did not become ready")
        with httpx.Client(base_url=BASE, timeout=180) as client:
            rows["server"]["healthz"] = client.get("/healthz").status_code
            rows["api"]["compare_equivalent"] = api(client, "/api/v1/compare",
                                                      load("valid_equivalent.json"))
            rows["api"]["compare_different"] = api(client, "/api/v1/compare",
                                                     load("valid_different.json"))
            rows["api"]["consume_valid"] = api(client, "/api/v1/consume",
                                                load("valid_consume.json"))
            rows["api"]["consume_forged_equivalent"] = api(
                client, "/api/v1/consume", load("forged_equivalent_consume.json"))
            rows["api"]["consume_invalid_shape"] = api(
                client, "/api/v1/consume", load("invalid_proof_shape.json"))
            rows["api"]["frozen_v1_report"] = api(
                client, "/api/v1/compare", load("frozen_v1_report.json"))
            # Caller-supplied proof status at top level must not change the verdict.
            injected = load("valid_equivalent.json")
            injected["verdict"] = "EQUIVALENT"
            injected["report"] = {"verification": {"verdict": "EQUIVALENT"}}
            rows["api"]["injected_verdict_field"] = api(
                client, "/api/v1/compare", injected)
    finally:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()

    rows["comparisons"]["cli_vs_api_equivalent_canonical"] = (
        rows["cli"]["compare_equivalent"]["normalized_sha256"]
        == rows["api"]["compare_equivalent"]["normalized_sha256"])
    rows["comparisons"]["cli_vs_api_different_canonical"] = (
        rows["cli"]["compare_different"]["normalized_sha256"]
        == rows["api"]["compare_different"]["normalized_sha256"])
    rows["comparisons"]["freshness_never_current"] = True  # verified in engine outputs below

    # Freshness and interface checks from the actual result payloads.
    eq = rc.run("compare", rc.base_request())
    rows["freshness"] = eq["report"]["integrity"]["freshness"]
    rows["comparisons"]["freshness_never_current"] = rows["freshness"] != "CURRENT"

    out = {"schema": "flip-m3-independent-parity-review/1",
           "commit": "59751e20590117f0cbc4ef41b9b30d836e533f84", **rows}
    (HERE / "cli-api-parity.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"cli": rows["cli"], "api": rows["api"],
                      "comparisons": rows["comparisons"], "freshness": rows["freshness"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
