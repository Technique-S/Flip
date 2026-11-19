"""Independent verifier for the M4.5-1 portability evidence package."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-portable-project"
sys.path.insert(0, str(ROOT / "fixtures/m45-library-discovery/generators"))


def main():
    errors, checks = [], []
    m = json.loads((EVID / "MANIFEST.json").read_bytes())
    for item in m["files"]:
        p = EVID / item["path"]
        data = p.read_bytes() if p.exists() else b""
        # Git blobs are LF; Windows checkouts may convert to CRLF. Normalize for
        # verification so the committed LF-byte register is compared correctly.
        if b"\r\n" in data:
            data = data.replace(b"\r\n", b"\n")
        if hashlib.sha256(data).hexdigest() != item["sha256"] or len(data) != item["bytes"]:
            errors.append(f"hash mismatch {item['path']}")
    checks.append({"name": "manifest", "files": len(m["files"])})

    cases = json.loads((EVID / "cases/portability-cases.json").read_bytes())
    ids = [c["caseId"] for c in cases["cases"]]
    if ids != [f"P{i:02d}" for i in range(1, 13)]:
        errors.append("case ids incomplete")
    checks.append({"name": "cases", "count": len(ids)})

    executed = json.loads((EVID / "results/executed-cases.json").read_bytes())
    if executed["passed"] != 12 or executed["total"] != 12:
        errors.append("executed cases incomplete")
    checks.append({"name": "executed", "passed": executed["passed"]})

    browser = json.loads((EVID / "results/browser-roundtrip.json").read_bytes())
    saved = {s["name"]: s["value"] for s in browser["steps"]}
    if saved.get("savedSchemaVersion") != "m3-1.0.0" or saved.get("savedHasVectors") is not False:
        errors.append("browser saved shape changed")
    if saved.get("reimportedVerdict") != "EQUIVALENT":
        errors.append("browser reimport did not reproduce")
    checks.append({"name": "browser_roundtrip", "steps": len(browser["steps"])})

    # Core portability finding: vectors and revision ancestry are not embedded.
    base = json.loads((EVID / "requests/web-export.json").read_bytes())
    if "vectors" in base or any(k in base["project"] for k in ("revision", "revisions")):
        errors.append("unexpected embedded vectors/revision")
    checks.append({"name": "no_embedded_vectors_or_revision", "ok": True})

    print(json.dumps({"checks": checks, "errors": errors,
                      "result": "PASS" if not errors else "FAIL"},
                     indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
