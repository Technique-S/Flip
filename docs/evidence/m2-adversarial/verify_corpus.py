"""Offline verification of the M2-B corpus. No network, no signing, no product code.

Checks:
  1. fixture bytes vs MANIFEST.json SHA-256;
  2. exact regeneration (generator run against scratch copies);
  3. archived TAP-02 reference decoder reasons for reference_decoder_safe cases only;
  4. current frozen-M1 behaviour for the M1 review regression specs (baseline only);
  5. bounded credential-pattern scan of all authored files.

Outputs docs/evidence/m2-adversarial/corpus_verification.json.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import tempfile
from pathlib import Path

WT = Path(__file__).resolve().parents[3]
FIX = WT / "fixtures" / "m2-adversarial"
DOC = WT / "docs" / "evidence" / "m2-adversarial"
REF_SRC = Path(r"C:\Users\Kazi\Documents\Flip\experiments\src\tap02_reference.py")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    manifest = load(FIX / "MANIFEST.json")
    artifacts = manifest["artifacts"]

    # 1. byte/hash verification
    hash_checks = []
    for item in artifacts:
        path = WT / item["path"]
        raw = path.read_bytes()
        hash_checks.append({
            "path": item["path"],
            "bytes": len(raw),
            "expected_sha256": item["sha256"],
            "actual_sha256": hashlib.sha256(raw).hexdigest(),
            "match": len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"],
        })

    # 2. exact regeneration: copy authored tree to scratch, run generator there, compare
    with tempfile.TemporaryDirectory() as td:
        scratch = Path(td) / "wt"
        (scratch / "fixtures" / "m2-adversarial").mkdir(parents=True)
        (scratch / "docs" / "evidence").mkdir(parents=True)
        shutil.copytree(DOC, scratch / "docs" / "evidence" / "m2-adversarial")
        shutil.copytree(WT / "docs" / "evidence" / "raw", scratch / "docs" / "evidence" / "raw")
        for f in FIX.glob("*.json"):
            shutil.copy2(f, scratch / "fixtures" / "m2-adversarial" / f.name)
        script = scratch / "docs" / "evidence" / "m2-adversarial" / "build_corpus.py"
        # The generator resolves WT by parents[3]; the scratch layout mirrors the worktree.
        import subprocess
        import sys
        proc = subprocess.run([sys.executable, str(script)], capture_output=True, check=False)
        regen_ok = proc.returncode == 0
        regen_diffs = []
        if regen_ok:
            for item in artifacts:
                rel = Path(item["path"])
                a = (WT / rel).read_bytes()
                b = (scratch / rel).read_bytes()
                if a != b:
                    regen_diffs.append(str(rel))
        else:
            regen_diffs = [proc.stderr.decode("utf-8", "replace")[:500]]

    # 3. archived reference decoder checks (safe cases only)
    spec = importlib.util.spec_from_file_location("tap02_reference", REF_SRC)
    assert spec and spec.loader
    tap = importlib.util.module_from_spec(spec)
    import sys
    sys.modules["tap02_reference"] = tap  # dataclasses needs the module registered
    spec.loader.exec_module(tap)

    corpus = load(FIX / "tap02-malformed.json")
    decoder_checks = []
    for case in corpus["cases"]:
        if case["archived_reference_decoder_execution"] != "reference_decoder_safe":
            decoder_checks.append({
                "id": case["id"],
                "executed": False,
                "reason": case["archived_reference_decoder_execution"],
                "expected_outcome": case["expected_outcome"],
            })
            continue
        raw = bytes.fromhex(case["netlist"][2:])
        refs = case.get("refs") or []
        resolve = None
        if refs:
            lookup = {}
            for r in refs:
                sub = bytes.fromhex(r["netlist"][2:])
                lookup[(bytes.fromhex(r["cpu"][2:]), r["id"])] = tap.load(
                    sub, r["nIn"], r["nOut"], None
                )
            resolve = lambda cpu, cid: lookup.get((cpu, cid))
        try:
            tap.load(raw, case["nIn"], case["nOut"], resolve)
            decoder_checks.append({"id": case["id"], "executed": True, "rejected": False,
                                   "detail": "accepted by archived decoder (unexpected)"})
        except tap.IllFormed as exc:
            message = str(exc)
            prefix = case["expected_outcome"].get("reason_prefix", "")
            decoder_checks.append({
                "id": case["id"], "executed": True, "rejected": True,
                "reason": message,
                "reason_prefix_expected": prefix,
                "reason_prefix_match": bool(prefix) and message.startswith(prefix),
            })
        except Exception as exc:  # noqa: BLE001 - record any non-IllFormed failure
            decoder_checks.append({"id": case["id"], "executed": True, "rejected": True,
                                   "reason": f"{type(exc).__name__}: {exc}"[:300]})

    # 4. current frozen-M1 behaviour (baseline observation, not a passing test)
    m1_observed = []
    try:
        from flip_core.contracts import ContractError, validate_contract

        ex = WT / "docs" / "schema" / "examples"

        def code(fn):
            try:
                fn()
                return {"outcome": "ACCEPTED"}
            except ContractError as exc:
                return {"outcome": "REJECTED", "code": exc.code}

        ident = json.loads((ex / "circuit-identity.json").read_text(encoding="utf-8"))
        missing = dict(ident)
        missing.pop("chainId", None)
        m1_observed.append({"id": "M1-REG-001", "observed": code(
            lambda: validate_contract("circuit-identity", json.dumps(missing)))})

        rep = json.loads((ex / "comparison-report.json").read_text(encoding="utf-8"))
        rep["verification"].update(verdict="EQUIVALENT", reasonCode=None,
                                   solverBackend="Minisat22", solverOutcome="UNSAT",
                                   sourceValidation="PASSED", mappingValidation="PASSED")
        rep["integrity"]["freshness"] = "HISTORICAL"
        rep["inputMap"] = []
        rep["outputMap"] = [0]
        m1_observed.append({"id": "M1-REG-002", "observed": code(
            lambda: validate_contract("comparison-report", json.dumps(rep)))})

        pre = json.loads((ex / "preflight.json").read_text(encoding="utf-8"))
        block = {"number": "1", "hash": "0x" + "11" * 32}
        pre.update(status="STRUCTURALLY_ACCEPTED", reasonCode=None,
                   observation={"block": block, "feeWei": "0", "manifestRevalidated": True,
                                "revertData": "0x", "classification": "KNOWN_BURN_STAGE"},
                   integrity={"freshness": "CURRENT", "checkedBlock": block})
        m1_observed.append({"id": "M1-REG-003", "observed": code(
            lambda: validate_contract("preflight", json.dumps(pre)))})
    except ImportError as exc:
        m1_observed.append({"error": f"flip_core unavailable: {exc}"})

    # 5. credential pattern scan
    patterns = [
        re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
        re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        re.compile(r"(?:mnemonic|seed[_-]?phrase|api[_-]?key|password)[\"']?\s*[:=]\s*[\"'][A-Za-z0-9+/_=-]{12,}",
                   re.IGNORECASE),
    ]
    authored = [p for p in FIX.rglob("*") if p.is_file()] + [p for p in DOC.rglob("*") if p.is_file()]
    credential_hits = []
    for path in authored:
        if path.suffix == ".pyc":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(p.search(text) for p in patterns):
            credential_hits.append(str(path.relative_to(WT)))

    result = {
        "scope": "M2-B offline corpus verification; not importer/integrity-engine integration",
        "hash_checks": hash_checks,
        "all_hashes_match": all(x["match"] for x in hash_checks),
        "exact_regeneration": proc.returncode == 0 and not regen_diffs,
        "regeneration_differences": regen_diffs,
        "decoder_checks": decoder_checks,
        "safe_cases_rejected": sum(1 for x in decoder_checks if x.get("rejected")),
        "safe_cases_total": sum(1 for x in decoder_checks if x.get("executed")),
        "m1_current_behaviour": m1_observed,
        "credential_pattern_hits": credential_hits,
        "largest_fixture_bytes": max(x["bytes"] for x in hash_checks),
    }
    out = DOC / "corpus_verification.json"
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(json.dumps({
        "all_hashes_match": result["all_hashes_match"],
        "exact_regeneration": result["exact_regeneration"],
        "safe_cases_rejected": result["safe_cases_rejected"],
        "safe_cases_total": result["safe_cases_total"],
        "credential_pattern_hits": credential_hits,
        "largest_fixture_bytes": result["largest_fixture_bytes"],
        "m1_current_behaviour": m1_observed,
    }, indent=2))


if __name__ == "__main__":
    main()
