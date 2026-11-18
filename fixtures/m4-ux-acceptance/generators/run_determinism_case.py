"""C29: 100 deterministic half-adder builds through the implemented CLI."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EXEC = ROOT / "docs/evidence/m4-ux-acceptance/executed"
FLIP = ROOT / ".venv/Scripts/flip.exe"
REQUEST = ROOT / "fixtures/m4-ux-acceptance/cli-cases/requests/half-adder-equivalent.json"
AUDITED = "0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce"


def main() -> None:
    hashes = []
    for _ in range(100):
        completed = subprocess.run(
            [str(FLIP), "compose", "--project", str(REQUEST)],
            cwd=ROOT,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise SystemExit(f"compose failed: {completed.stderr.decode('utf-8', 'replace')}")
        hashes.append(json.loads(completed.stdout)["candidateIdentity"]["netlistHash"])
    distinct = sorted(set(hashes))
    exit_code = 0 if distinct == [AUDITED] else 3
    record = {
        "id": "C29",
        "description": "100 repeated compose builds, all bytes identical",
        "command": "flip compose --project .../half-adder-equivalent.json (x100)",
        "exitCode": exit_code,
        "stdoutFile": "docs/evidence/m4-ux-acceptance/executed/C29.stdout.txt",
        "stdoutSha256": hashlib.sha256(json.dumps(distinct).encode()).hexdigest(),
        "stderr": "",
        "semantic": {
            "distinctNetlistHashes": distinct,
            "auditedDigest": AUDITED,
            "builds": len(hashes),
        },
    }
    (EXEC / "C29.stdout.txt").write_text(
        json.dumps(record["semantic"], indent=2) + "\n", encoding="utf-8"
    )
    path = EXEC / "transcript.json"
    transcript = json.loads(path.read_text(encoding="utf-8-sig"))
    transcript["cases"] = [c for c in transcript["cases"] if c["id"] != "C29"]
    transcript["cases"].append(record)
    path.write_text(json.dumps(transcript, indent=2) + "\n", encoding="utf-8")
    print(f"C29 exit={exit_code} distinct={distinct}")


if __name__ == "__main__":
    main()
