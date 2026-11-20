"""Diagnose the unchanged M3 archival verifier in a disposable tree.

This diagnostic does not change pytest's 120-second deadline or archived bytes.
Stage wrappers only time the generator's existing task functions in memory.
"""

import argparse
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHILD = r"""
import json, runpy, sys, time
from pathlib import Path
source = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(source.parent))
module = runpy.run_path(str(source), run_name="diagnostic_generator")
namespace = module["main"].__globals__
for name in ("build_task_a", "build_task_b", "build_task_c", "build_task_d", "build_task_e"):
    original = namespace[name]
    def timed(*args, _name=name, _fn=original, **kwargs):
        start = time.perf_counter()
        print(json.dumps({"stage": _name, "event": "start"}), file=sys.stderr, flush=True)
        result = _fn(*args, **kwargs)
        elapsed = round(time.perf_counter()-start, 3)
        print(json.dumps({"stage": _name, "elapsedSeconds": elapsed}),
              file=sys.stderr, flush=True)
        return result
    namespace[name] = timed
sys.exit(module["main"]())
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    scratch_root = ROOT / ".test-tmp"
    scratch_root.mkdir(exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix="archival-diagnostic-", dir=scratch_root))
    shutil.copytree(ROOT / "fixtures/m3-verification", scratch / "fixtures/m3-verification")
    shutil.copytree(
        ROOT / "docs/evidence/m3-verification", scratch / "docs/evidence/m3-verification"
    )
    source = scratch / "fixtures/m3-verification/generators/verify_corpus.py"
    sys.path.insert(0, str(source.parent))
    verifier = runpy.run_path(str(source), run_name="diagnostic_verifier")
    original_run = subprocess.run
    timings = []

    def measured(command, **kwargs):
        if command[1].endswith("build_corpus.py"):
            child = (Path(kwargs["cwd"]) / command[1]).resolve()
            start = time.perf_counter()
            result = original_run([command[0], "-c", CHILD, str(child)], **kwargs)
            timings.append(
                {
                    "stage": "generator_subprocess",
                    "seconds": time.perf_counter() - start,
                    "returncode": result.returncode,
                    "stageOutput": result.stderr,
                }
            )
            return result
        return original_run(command, **kwargs)

    subprocess.run = measured
    start = time.perf_counter()
    try:
        status = verifier["main"]()
    finally:
        subprocess.run = original_run
    record = {
        "scope": "SCRATCH_DIAGNOSTIC_NOT_A_DEADLINE_CHANGE",
        "exit": status,
        "seconds": time.perf_counter() - start,
        "stages": timings,
        "transcript": json.loads(
            (scratch / "docs/evidence/m3-verification/verification-transcript.json").read_bytes()
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"diagnosticSeconds": record["seconds"], "stages": timings, "exit": status}))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
