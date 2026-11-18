"""M4-B fixture register, semantic transcript summary and regeneration check.

    uv run --frozen python fixtures/m4-ux-acceptance/generators/verify_fixtures.py --write
    uv run --frozen python fixtures/m4-ux-acceptance/generators/verify_fixtures.py

The regeneration check rebuilds neutral request fixtures into a temporary tree
and requires byte equality. Executed stdout captures contain noncanonical timing
fields and are registered as EXECUTED_CAPTURE, not as regenerable fixtures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "fixtures/m4-ux-acceptance"
EVID = ROOT / "docs/evidence/m4-ux-acceptance"
MANIFEST = FIX / "MANIFEST.json"
TRANSCRIPT = EVID / "executed/transcript.json"
SUMMARY = EVID / "executed/summary.json"


def digest(path: Path) -> str:
    return "0x" + hashlib.sha256(path.read_bytes()).hexdigest()


def semantic(stdout_path: Path) -> dict:
    raw = stdout_path.read_bytes()
    try:
        value = json.loads(raw)
    except ValueError:
        return {"parse": "NOT_JSON"}
    if isinstance(value, dict) and "error" in value:
        return {"errorCode": value["error"].get("code")}
    if isinstance(value, dict) and "report" in value:
        verification = value["report"]["verification"]
        return {
            "kind": value.get("kind"),
            "verdict": verification.get("verdict"),
            "reasonCode": verification.get("reasonCode"),
            "solverOutcome": verification.get("solverOutcome"),
            "freshness": value["report"]["integrity"]["freshness"],
            "witnessReplay": (verification.get("witness") or {}).get("replay"),
        }
    if isinstance(value, dict) and "netlist" in value:
        return {"kind": value.get("kind"), "netlistHash": value["candidateIdentity"]["netlistHash"]}
    if isinstance(value, dict) and "distinctNetlistHashes" in value:
        return value
    if isinstance(value, dict) and "integrity" in value:
        return {"freshness": value["integrity"].get("freshness")}
    if isinstance(value, dict) and "verdict" in value:
        return {
            "kind": value.get("kind"),
            "verdict": value.get("verdict"),
            "coverage": value.get("coverage"),
            "freshness": value.get("freshness"),
        }
    return {"keys": sorted(value)[:8]}


def write_summary() -> None:
    transcript = json.loads(TRANSCRIPT.read_text(encoding="utf-8-sig"))
    cases = []
    for case in transcript["cases"]:
        stdout = ROOT / Path(case["stdoutFile"])
        cases.append(
            {
                "id": case["id"],
                "exitCode": case["exitCode"],
                "command": case["command"],
                "semantic": semantic(stdout),
                "provenance": case.get("provenance", "PINNED_M3_BASELINE"),
            }
        )
    SUMMARY.write_text(
        json.dumps(
            {
                "schemaVersion": "m4-ux-acceptance-1",
                "baseline": transcript["baseline"],
                "caseCount": len(cases),
                "cases": cases,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


PLANNED_CASES = [
    {
        "id": "P01",
        "command": "flip preflight --project <project> --format json",
        "precondition": "live read-only RPC and fresh TAPEOUT_FEE observation",
        "expectedM4": "STRUCTURALLY_ACCEPTED / REJECTED(reason) / UNKNOWN only; no PUBLISHED",
        "baselineObservation": "exit 6 NOT_IMPLEMENTED (C18)",
    },
    {
        "id": "P02",
        "command": "flip export --project <project> --out bundle.zip",
        "precondition": "completed comparison",
        "expectedM4": "path-safe bundle with SHA256SUMS; no secrets; HISTORICAL retained",
        "baselineObservation": "exit 6 NOT_IMPLEMENTED (C19)",
    },
    {
        "id": "P03",
        "command": "flip verify-bundle --bundle bundle.zip --format json",
        "precondition": "exported bundle in a clean environment",
        "expectedM4": "checksum and repeated local checks; never upgrades HISTORICAL",
        "baselineObservation": "no M3 implementation; specification only",
    },
    {
        "id": "P04",
        "command": "flip sample --out sample.flip.json",
        "precondition": "none",
        "expectedM4": "emits the pinned offline sample request for onboarding",
        "baselineObservation": "exit 6 NOT_IMPLEMENTED (C20)",
    },
    {
        "id": "P05",
        "command": "flip import --processor <address> --id <id> --rpc-url <live endpoint>",
        "precondition": "authorized RPC with per-session chain verification",
        "expectedM4": "CURRENT single-RPC observation pinned to block number and hash",
        "baselineObservation": "not executed; no live RPC authorized in M4-B",
    },
    {
        "id": "P06",
        "command": "Playwright E2E scenarios B01-B11",
        "precondition": "M4 web application available",
        "expectedM4": "see browser/ACCESSIBILITY_ACCEPTANCE_PLAN.md",
        "baselineObservation": "no web application in this branch",
    },
]


def write_cases_json() -> None:
    transcript = json.loads(TRANSCRIPT.read_text(encoding="utf-8-sig"))
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in summary["cases"]}
    executed = []
    for case in transcript["cases"]:
        executed.append(
            {
                "id": case["id"],
                "description": case["description"],
                "command": case["command"],
                "exitCode": case["exitCode"],
                "semantic": by_id[case["id"]]["semantic"],
                "provenance": case.get("provenance", "PINNED_M3_BASELINE"),
                "stdoutFile": case["stdoutFile"],
            }
        )
    (FIX / "cli-cases/CASES.json").write_text(
        json.dumps(
            {
                "schemaVersion": "m4-ux-acceptance-1",
                "baseline": transcript["baseline"],
                "executed": executed,
                "plannedUnexecuted": PLANNED_CASES,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def register() -> dict:
    authored = {}
    captured = {}
    for base, target in ((FIX, authored), (EVID, captured)):
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.name == "MANIFEST.json":
                continue
            rel = path.relative_to(ROOT).as_posix()
            target[rel] = {
                "bytes": path.stat().st_size,
                "sha256": digest(path),
            }
    return {
        "schemaVersion": "m4-ux-acceptance-1",
        "baseline": "af8ba1f109a2a1c59fe36be044bc025a127ea025",
        "classes": {
            "authored": "deterministic fixtures, generators and documentation",
            "captured": "CLI captures with noncanonical timing; not regenerable",
        },
        "authored": authored,
        "captured": captured,
    }


def regeneration_check() -> None:
    """Rebuild every neutral request in a scratch directory and compare bytes."""
    import importlib.util

    script = FIX / "generators/build_fixtures.py"
    spec = importlib.util.spec_from_file_location("m4b_build_fixtures", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    original = module.OUT
    with tempfile.TemporaryDirectory() as tmp:
        module.OUT = Path(tmp)
        try:
            module.build()
        finally:
            module.OUT = original
        sources = json.loads((FIX / "cli-cases/requests/SOURCES.json").read_text())
        names = sorted(sources["derivations"])
        for name in names:
            committed = FIX / "cli-cases/requests" / name
            rebuilt = Path(tmp) / name
            if not rebuilt.exists() or committed.read_bytes() != rebuilt.read_bytes():
                raise SystemExit(f"non-reproducible fixture: {name}")
    print(f"regeneration exact for {len(names)} request fixtures")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="rewrite summary and MANIFEST")
    args = parser.parse_args()
    write_summary()
    write_cases_json()
    regeneration_check()
    if args.write:
        MANIFEST.write_text(json.dumps(register(), indent=2) + "\n", encoding="utf-8")
    register_data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for section in ("authored", "captured"):
        for rel, entry in register_data[section].items():
            path = ROOT / rel
            if not path.exists() or digest(path) != entry["sha256"]:
                raise SystemExit(f"hash mismatch: {rel}")
    print(
        f"verified {len(register_data['authored'])} authored and "
        f"{len(register_data['captured'])} captured files; "
        f"summary cases: {json.loads(SUMMARY.read_text(encoding='utf-8'))['caseCount']}"
    )


if __name__ == "__main__":
    main()
