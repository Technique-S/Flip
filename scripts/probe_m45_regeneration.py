"""Opt-in F-03 environment probe. Runs the unchanged custody test serially.

Never imported by production or mandatory CI; does not change the inner 120s limit.
"""

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = "packages/flip-core/tests/test_m3_acceptance.py::test_custody_and_scratch_regeneration"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    scratch = ROOT / ".test-tmp/m45-regeneration-probe"
    scratch.mkdir(parents=True, exist_ok=True)
    source = ROOT / "fixtures/m3-verification"
    hashes = {
        p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in source.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }
    report = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "executable": sys.executable,
        "baseExecutable": sys._base_executable,
        "cpuCount": os.cpu_count(),
        "sourceHashes": hashes,
        "innerTimeoutSeconds": 120,
        "runs": [],
    }
    for layout in ("default", "custom"):
        target = scratch / layout
        target.mkdir(exist_ok=True)
        start = time.perf_counter()
        subprocess.run([sys.executable, "-c", "pass"], cwd=target, check=True, timeout=15)
        startup = time.perf_counter() - start
        start = time.perf_counter()
        shutil.copytree(
            source,
            target / "copy",
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        copy_time = time.perf_counter() - start
        start = time.perf_counter()
        for name, digest in hashes.items():
            assert hashlib.sha256((target / "copy" / name).read_bytes()).hexdigest() == digest
        hashing = time.perf_counter() - start
        command = [
            sys.executable,
            "-m",
            "pytest",
            NODE,
            "-q",
            "--durations=2",
            f"--junitxml={scratch / (layout + '.xml')}",
            "-o",
            "junit_family=legacy",
        ]
        if layout == "custom":
            command.append("--basetemp=.test-tmp/m45-d-custom")
        start = time.perf_counter()
        try:
            done = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=300)
            code, stdout, stderr = done.returncode, done.stdout, done.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
        record = dict(
            layout=layout,
            command=command,
            startupSeconds=startup,
            copySeconds=copy_time,
            hashSeconds=hashing,
            testWallSeconds=time.perf_counter() - start,
            exitCode=code,
            stdout=stdout.decode("utf-8", "replace"),
            stderr=stderr.decode("utf-8", "replace"),
        )
        report["runs"].append(record)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2) + "\n", newline="\n")
        print(
            json.dumps(
                {
                    k: record[k]
                    for k in (
                        "layout",
                        "exitCode",
                        "testWallSeconds",
                        "startupSeconds",
                        "copySeconds",
                        "hashSeconds",
                    )
                }
            ),
            flush=True,
        )
    assert all(
        hashlib.sha256((source / name).read_bytes()).hexdigest() == digest
        for name, digest in hashes.items()
    )


if __name__ == "__main__":
    main()
