"""Independent Portable 1.1 security/compatibility acceptance harness.

Exercises the real flip_core.portable controller via core and CLI. Builds requests
from golden packages and the accepted legacy example. No production code modified.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-portable-independent-review"
RUN = EVID / "results/run"
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))

from flip_core.canonical import canonical_bytes, content_hash  # noqa: E402
from flip_core.contracts import ContractError  # noqa: E402
from flip_core.portable import bounded_operation, create_package, parse_package  # noqa: E402
from flip_core.workflow import sample  # noqa: E402

OUT = EVID / "results/portable-acceptance.json"
FLIP = str(ROOT / ".venv/Scripts/flip.exe")
GOLDEN = json.loads((ROOT / "docs/schema/m45-portable-project/1.1.0/golden.json").read_bytes())
PACKAGES = GOLDEN["packages"]
GENESIS, EDITED, RICH = PACKAGES[0], PACKAGES[1], PACKAGES[2]
LEGACY = sample("half-adder")
LEGACY_HASH = content_hash(LEGACY)


def req(op, **kwargs):
    b = dict(schemaVersion="flip-portable-project-1.1.0", kind="PORTABLE_REQUEST", operation=op)
    b.update(kwargs)
    return b


def run(cid, name, fn):
    try:
        return {"id": cid, "name": name, "observed": fn(), "error": None}
    except Exception as exc:
        return {"id": cid, "name": name,
                "observed": {"exception": f"{type(exc).__name__}: {exc}"},
                "error": f"{type(exc).__name__}: {exc}"}


def safe_call(body):
    try:
        result = bounded_operation(body)
        return {"ok": True, "result": result}
    except ContractError as exc:
        return {"ok": False, "code": exc.code, "message": exc.message[:120]}


def main():
    rows = []

    # === Task A: legacy compatibility ===
    # Legacy files are accepted by flip compose/compare (not the portable converter).
    def legacy_cli():
        path = RUN / "legacy.request.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(LEGACY), encoding="utf-8")
        proc = subprocess.run([FLIP, "compose", "--project", str(path)],
                              cwd=ROOT, env=dict(os.environ), capture_output=True, timeout=120)
        out = None
        try:
            out = json.loads(proc.stdout)
        except ValueError:
            pass
        return {"exit": proc.returncode,
                "netlistHash": out and out.get("manifest", {}).get("netlistHash")}
    rows.append(run("A01", "legacy project files accepted by compose", legacy_cli))
    rows.append(run("A02", "81-byte half-adder byte-identical", lambda: (
        (lambda r: {"exit": r["exit"],
                    "netlistHash": r["netlistHash"],
                    "matchesArchived": r["netlistHash"]
                    == "0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce"})(
            legacy_cli()))))
    rows.append(run("A04", "legacy wrapped in Portable 1.1", lambda: (
        (lambda r: {"ok": r["ok"], "kind": r.get("result", {}).get("kind"),
                    "execHash": r.get("result", {}).get("executionRequestHash")})(
            safe_call(req("wrap", executionRequest=LEGACY))))))
    rows.append(run("A05", "Portable yields exact legacy request", lambda: (
        (lambda r: {"ok": r["ok"], "exact": r.get("result", {}).get("executionRequest") == LEGACY})(
            safe_call(req("open", package=GENESIS))))))
    rows.append(run("A06", "unsupported version fails safely", lambda: (
        (lambda p: {"code": p.get("code"), "message": p.get("message")})(
            safe_call(req("validate", package={**GENESIS, "schemaVersion": "9.9.9"}))))))
    rows.append(run("A07", "downgrade without acknowledgement rejected", lambda: (
        (lambda p: {"code": p.get("code")})(safe_call(req("downgrade", package=GENESIS))))))
    rows.append(run("A08", "lossy downgrade reports discarded fields", lambda: (
        (lambda r: {"ok": r["ok"], "discarded": r.get("result", {}).get("discardedFields"),
                    "warning": r.get("result", {}).get("warning")})(
            safe_call(req("downgrade", package=RICH, allowLossy=True))))))

    # === Task B: named vectors ===
    rows.append(run("B01", "named vector round trip + VECTORS_MATCH", lambda: (
        (lambda r: {"ok": r["ok"],
                    "verdicts": [x["result"]["verdict"] for x in r.get("result", {}).get("results", [])],
                    "coverage": [x["result"]["coverage"] for x in r.get("result", {}).get("results", [])]})(
            safe_call(req("test", package=RICH))))))
    rows.append(run("B02", "duplicate test names rejected", lambda: (
        (lambda p: {"code": p.get("code")})(safe_call(req("wrap", executionRequest=LEGACY,
            tests=[RICH["tests"][0], RICH["tests"][0]]))))))
    rows.append(run("B03", "empty tests require noDeclaredTests", lambda: (
        (lambda p: {"code": p.get("code")})(safe_call(req("validate", package={**GENESIS,
            "tests": [], "noDeclaredTests": False,
            "revision": {**GENESIS["revision"], "revisionHash": "0x" + "00" * 32}}))))))
    # malformed bitstring
    bad_bits = copy.deepcopy(RICH)
    bad_bits["tests"][0]["vectors"][0]["inputs"]["bits"] = "XYZ"
    rows.append(run("B04", "malformed bitstring rejected", lambda: (
        (lambda p: {"code": p.get("code")})(safe_call(req("validate", package=bad_bits))))))
    # incompatible width
    bad_width = copy.deepcopy(RICH)
    bad_width["tests"][0]["vectors"][0]["inputs"]["width"] = 99
    rows.append(run("B05", "incompatible source width rejected", lambda: (
        (lambda p: {"code": p.get("code")})(safe_call(req("validate", package=bad_width))))))

    # === Task C: evidence trust attacks ===
    def evidence_attack(kind):
        pkg = copy.deepcopy(RICH)
        ref = pkg["evidenceRefs"][0]
        if kind == "digest":
            ref["digest"] = "0x" + "11" * 32
            pkg["revision"]["metadataHash"] = "0x" + "00" * 32  # break chain too
            return safe_call(req("validate", package=pkg))
        if kind == "current":
            pkg["provenance"]["sourceFreshness"] = "CURRENT"
            pkg["revision"]["metadataHash"] = "0x" + "00" * 32
            return safe_call(req("validate", package=pkg))
        if kind == "cross_chain":
            pkg["executionRequest"]["chainId"] = 8453
            return safe_call(req("validate", package=pkg))
        if kind == "missing":
            return safe_call(req("replay-evidence", package=pkg, artifacts={}))
        if kind == "fabricated":
            fake = {"contentHash": ref["digest"], "reproduce": ref["reproduce"],
                    "comparison": {"engineHash": ref["engineHash"],
                                   "report": {"verification": {"verdict": "EQUIVALENT"}}},
                    "kind": "FLIP_EVIDENCE", "schemaVersion": "m4-1.0.0"}
            return safe_call(req("replay-evidence", package=pkg,
                                 artifacts={ref["digest"]: fake}))
    for cid, kind in [("C01", "digest"), ("C02", "current"), ("C03", "cross_chain"),
                      ("C04", "missing"), ("C05", "fabricated")]:
        rows.append(run(cid, f"evidence attack: {kind}", lambda kind=kind: evidence_attack(kind)))

    # === Task D: revision-chain attacks ===
    # Build a genuine 2-ancestor chain so reordering/truncation are meaningful.
    chain_g0 = create_package(LEGACY)
    r2 = copy.deepcopy(LEGACY); r2["project"]["limits"]["gateCap"] = 2000
    chain_g1 = create_package(r2, previous=chain_g0, description="cap 2000")
    r3 = copy.deepcopy(r2); r3["project"]["limits"]["gateCap"] = 1500
    CHAIN = create_package(r3, previous=chain_g1, description="cap 1500")

    def chain_attack(kind):
        pkg = copy.deepcopy(CHAIN)
        if kind == "missing_parent":
            pkg["ancestors"] = []
            pkg["revision"]["parentHash"] = "0x" + "99" * 32
        elif kind == "forged_genesis":
            pkg["ancestors"][0]["parentHash"] = "0x" + "99" * 32
        elif kind == "reordered":
            pkg["ancestors"] = list(reversed(pkg["ancestors"]))
        elif kind == "dup_id":
            pkg["revision"]["sequence"] = pkg["ancestors"][0]["sequence"]
        elif kind == "broken_link":
            pkg["revision"]["revisionHash"] = "0x" + "00" * 32
        elif kind == "truncated":
            pkg["ancestors"] = pkg["ancestors"][:-1]
        elif kind == "changed_after":
            pkg["ancestors"][1]["editLog"][0]["afterHash"] = "0x" + "77" * 32
        elif kind == "cross_project":
            pkg["ancestors"][0]["projectId"] = "otherProject"
        elif kind == "rollback":
            # Reuse an ancestor's execution request hash as a new head without a real edit.
            pkg["revision"]["executionRequestHash"] = pkg["ancestors"][0]["executionRequestHash"]
        elif kind == "future":
            pkg["schemaVersion"] = "flip-portable-project-9.9.9"
        return safe_call(req("validate", package=pkg))
    for cid, kind in [("D01", "missing_parent"), ("D02", "forged_genesis"),
                      ("D03", "reordered"), ("D04", "dup_id"), ("D05", "broken_link"),
                      ("D06", "truncated"), ("D07", "future"), ("D08", "changed_after"),
                      ("D09", "cross_project"), ("D10", "rollback")]:
        rows.append(run(cid, f"revision attack: {kind}", lambda kind=kind: chain_attack(kind)))

    # === Task F: limits / security ===
    rows.append(run("F01", "oversized request rejected", lambda: (
        (lambda p: {"code": p.get("code")})(safe_call({"schemaVersion": "flip-portable-project-1.1.0",
            "kind": "PORTABLE_REQUEST", "operation": "wrap", "executionRequest": LEGACY,
            "description": "x" * 1_100_000})))))
    rows.append(run("F02", "no authority field accepted", lambda: (
        (lambda p: {"code": p.get("code")})(safe_call({**req("wrap", executionRequest=LEGACY),
            "transactionAuthority": True})))))

    # CLI execution of validate/open/downgrade.
    def cli():
        body = req("validate", package=GENESIS)
        path = RUN / "portable.request.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(body), encoding="utf-8")
        proc = subprocess.run([FLIP, "portable", "--request", str(path)],
                              cwd=ROOT, env=dict(os.environ), capture_output=True, timeout=120)
        try:
            out = json.loads(proc.stdout)
        except ValueError:
            out = None
        return {"exit": proc.returncode, "kind": out and out.get("kind"),
                "execHash": out and out.get("executionRequestHash")}
    rows.append(run("G01", "CLI portable validate", cli))

    record = {"artifactType": "PORTABLE_INDEPENDENT_ACCEPTANCE",
              "testedSha": "136b1115ee0f5ffe0a5583d68c474641fdce1ca1",
              "corpusSha": "2f3d6263edf4e62ad4e94718c99f6c1a79e350a1",
              "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    errs = [r for r in rows if r["error"]]
    print(json.dumps({"total": len(rows), "errors": [r["id"] for r in errs]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
