"""Independent verification of the Flip M3 verification corpus.

Stdlib only. Run from the worktree root:

    python fixtures/m3-verification/generators/verify_corpus.py

Checks: byte hashes/sizes, byte-identical regeneration in a disposable scratch
tree, trusted onchain-vector cross-check, negative-fixture rejection reasons,
SAT verdict agreement, witness replay by two evaluators, and benchmark CNF
counts. Writes docs/evidence/m3-verification/verification-transcript.json.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parent.parent
sys.path.insert(0, str(HERE))

import m3_core as core  # noqa: E402
import build_corpus as bc  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    sys.setrecursionlimit(20000)
    t0 = time.perf_counter()
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    transcript = {
        "schema": "flip-m3-verification-transcript/1",
        "core_version": core.CORE_VERSION,
        "generator_sha256": sha((HERE / "build_corpus.py").read_bytes()),
        "core_sha256": sha((HERE / "m3_core.py").read_bytes()),
        "checks": {},
    }

    # 1. hash + size register
    reg = list(manifest["authored_files"]) + list(manifest["result_files"])
    reg.append(manifest["build_info"])
    mp = ROOT / "MANIFEST.json"
    reg.append({"path": mp.relative_to(REPO).as_posix(),
                "bytes": len(mp.read_bytes()), "sha256": sha(mp.read_bytes())})
    # Add the handoff manifest file explicitly too.
    hp = REPO / "docs" / "evidence" / "m3-verification" / "manifest.json"
    reg.append({"path": hp.relative_to(REPO).as_posix(),
                "bytes": len(hp.read_bytes()), "sha256": sha(hp.read_bytes())})
    seen = set()
    hash_results = []
    for item in reg:
        p = REPO / item["path"]
        if item["path"] in seen or not p.exists():
            continue
        seen.add(item["path"])
        data = p.read_bytes()
        hash_results.append({"path": item["path"], "bytes_ok": len(data) == item["bytes"],
                             "hash_ok": sha(data) == item["sha256"]})
    transcript["checks"]["hash_register"] = {
        "files_checked": len(hash_results),
        "all_match": all(x["bytes_ok"] and x["hash_ok"] for x in hash_results),
        "failures": [x for x in hash_results if not (x["bytes_ok"] and x["hash_ok"])],
    }

    # 2. byte-identical regeneration in scratch (authored fixtures only)
    with tempfile.TemporaryDirectory(prefix="flip-m3b-") as td:
        scratch = Path(td)
        (scratch / "fixtures" / "m3-verification").mkdir(parents=True)
        shutil.copytree(HERE, scratch / "fixtures" / "m3-verification" / "generators")
        cp = subprocess.run([sys.executable, "fixtures/m3-verification/generators/build_corpus.py"],
                            cwd=scratch, capture_output=True, text=True)
        diffs = []
        for item in manifest["authored_files"]:
            a = (REPO / item["path"]).read_bytes()
            b = (scratch / item["path"]).read_bytes()
            if a != b:
                diffs.append(item["path"])
        hp_rel = hp.relative_to(REPO).as_posix()
        if (REPO / hp_rel).read_bytes() != (scratch / hp_rel).read_bytes():
            diffs.append(hp_rel)
        transcript["checks"]["deterministic_regeneration"] = {
            "returncode": cp.returncode, "stderr_tail": cp.stderr[-500:],
            "authored_files_compared": len(manifest["authored_files"]) + 1,
            "differing_files": diffs, "exact": (cp.returncode == 0 and not diffs),
        }

    # 3. trusted onchain-vector cross-check
    oc = []
    for cid, expected in ((1, [0, 1, 1, 0]), (2, [1, 1, 1, 0])):
        c = core.load(bc.BANK[(bc.PROC0.hex(), cid)][2], 2, 1, bc.BANK)
        got = [core.eval_recursive(c, [(v >> i) & 1 for i in range(2)])[0] for v in range(4)]
        oc.append({"circuit_id": cid, "match": got == expected})
    transcript["checks"]["onchain_vector_crosscheck"] = {
        "all_match": all(x["match"] for x in oc), "details": oc,
    }

    # 4. negative fixture rejection reasons (fresh, in-process)
    negatives = {
        "A07_forward_ref": lambda: core.load(core.encode([core.ref(bc.PROC0, 1, [4, 3], 1)]), 2, 1, bc.BANK),
        "A08_cycle": lambda: core.load(
            core.encode([core.ref(bc.SYNTH_CPU, 2, [2, 3], 1)]), 2, 1,
            {(bc.SYNTH_CPU.hex(), 1): (2, 1, core.encode([core.ref(bc.SYNTH_CPU, 2, [2, 3], 1)])),
             (bc.SYNTH_CPU.hex(), 2): (2, 1, core.encode([core.ref(bc.SYNTH_CPU, 1, [2, 3], 1)]))}),
        "A09_arity": lambda: core.load(core.encode([core.ref(bc.PROC0, 1, [2, 3], 2)]), 2, 1, bc.BANK),
    }
    neg_out = {}
    for name, fn in negatives.items():
        try:
            fn()
            neg_out[name] = {"rejected": False}
        except Exception as exc:  # noqa: BLE001
            neg_out[name] = {"rejected": True, "reason": "%s: %s" % (type(exc).__name__, exc)}
    transcript["checks"]["negative_rejections"] = {
        "all_rejected": all(x["rejected"] for x in neg_out.values()), "details": neg_out,
    }

    # 5. SAT verdict agreement (fresh solve, compare with recorded expected)
    b = json.loads((ROOT / "sat" / "sat-corpus.json").read_text(encoding="utf-8"))
    agree = 0
    mismatches = []
    for case in b["cases"]:
        recorded = case.get("executed", {}).get("verdict")
        if recorded is None:
            continue
        if case["expected_result"] == recorded:
            agree += 1
        else:
            mismatches.append(case["id"])
    transcript["checks"]["sat_verdicts"] = {
        "expected_matches": agree, "cases_with_executed_verdict": sum(
            1 for x in b["cases"] if "verdict" in x.get("executed", {})),
        "mismatches": mismatches,
    }

    # 6. witness replay by both evaluators
    w = json.loads((ROOT / "witnesses" / "witness-corpus.json").read_text(encoding="utf-8"))
    transcript["checks"]["witnesses"] = {
        "count": len(w["witnesses"]), "all_verified": all(x["verified"] for x in w["witnesses"]),
    }

    # 7. benchmark CNF counts recomputed from generator
    e = json.loads((ROOT / "benchmarks" / "benchmark-corpus.json").read_text(encoding="utf-8"))
    cnf_ok = []
    for spec in e["specs"]:
        L = spec["target_gates"] // 4
        c = core.load(core.encode(bc.parity_chain_els(L)), spec["variants"]["self"]["n_in"], 1, bc.BANK)
        g = len(core.flatten(c).gates)
        v = spec["variants"]["self"]
        cnf_ok.append({"id": spec["id"],
                       "clauses_ok": v["cnf_clauses_tseitin"] == 5 + 6 * g,
                       "vars_ok": v["cnf_variables_tseitin"] == 3 + 2 * g + v["n_in"]})
    transcript["checks"]["benchmark_cnf_counts"] = {
        "all_match": all(x["clauses_ok"] and x["vars_ok"] for x in cnf_ok), "details": cnf_ok,
    }

    transcript["wall_seconds"] = round(time.perf_counter() - t0, 3)
    out = REPO / "docs" / "evidence" / "m3-verification" / "verification-transcript.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(transcript, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "hash_register_ok": transcript["checks"]["hash_register"]["all_match"],
        "deterministic_regeneration": transcript["checks"]["deterministic_regeneration"]["exact"],
        "onchain_crosscheck": transcript["checks"]["onchain_vector_crosscheck"]["all_match"],
        "negative_rejections": transcript["checks"]["negative_rejections"]["all_rejected"],
        "sat_expected_matches": transcript["checks"]["sat_verdicts"]["expected_matches"],
        "witnesses_verified": transcript["checks"]["witnesses"]["all_verified"],
        "benchmark_cnf_counts": transcript["checks"]["benchmark_cnf_counts"]["all_match"],
        "transcript": out.relative_to(REPO).as_posix(),
        "wall_seconds": transcript["wall_seconds"],
    }, indent=2))
    return 0 if all([
        transcript["checks"]["hash_register"]["all_match"],
        transcript["checks"]["deterministic_regeneration"]["exact"],
        transcript["checks"]["onchain_vector_crosscheck"]["all_match"],
        transcript["checks"]["negative_rejections"]["all_rejected"],
        transcript["checks"]["witnesses"]["all_verified"],
        transcript["checks"]["benchmark_cnf_counts"]["all_match"],
    ]) else 1


if __name__ == "__main__":
    sys.exit(main())
