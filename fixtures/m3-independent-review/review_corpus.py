"""Task E: confirm M3-B fixtures were integrated without alteration."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import review_common as rc  # noqa: E402

M3B = "4822a05163166ec67b791328e2d1de490fa1c35f"
INTEGRATED = "59751e20590117f0cbc4ef41b9b30d836e533f84"


def blob(commit, path):
    cp = subprocess.run(["git", "rev-parse", f"{commit}:{path}"], cwd=rc.REPO,
                        capture_output=True, text=True)
    return cp.stdout.strip() if cp.returncode == 0 else None


def main():
    manifest = json.loads((rc.REPO / "fixtures/m3-verification/MANIFEST.json").read_bytes())
    paths = [item["path"] for item in
             manifest["authored_files"] + manifest["result_files"]]
    paths += ["fixtures/m3-verification/MANIFEST.json",
              "fixtures/m3-verification/BUILD_INFO.json",
              "fixtures/m3-verification/README.md",
              "fixtures/m3-verification/.gitattributes",
              "fixtures/m3-verification/generators/build_corpus.py",
              "fixtures/m3-verification/generators/m3_core.py",
              "fixtures/m3-verification/generators/verify_corpus.py",
              "docs/evidence/m3-verification/M3_B_HANDOFF.md",
              "docs/evidence/m3-verification/manifest.json",
              "docs/evidence/m3-verification/verification-transcript.json",
              "docs/evidence/m3-verification/.gitattributes"]
    comparisons = []
    for p in sorted(set(paths)):
        a, b = blob(M3B, p), blob(INTEGRATED, p)
        comparisons.append({"path": p, "m3b_blob": a, "integrated_blob": b,
                            "identical": a is not None and a == b})

    base = rc.REPO / "fixtures/m3-verification"
    a = json.loads((base / "circuits/golden-compositions.json").read_bytes())
    b = json.loads((base / "sat/sat-corpus.json").read_bytes())
    c = json.loads((base / "witnesses/witness-corpus.json").read_bytes())
    d = json.loads((base / "proof-attacks/attack-corpus.json").read_bytes())
    e = json.loads((base / "benchmarks/benchmark-corpus.json").read_bytes())

    all_fixture_text = "\n".join(
        p.read_text(encoding="utf-8", errors="ignore")
        for p in base.rglob("*.json"))
    suspicious = [
        phrase for phrase in
        ("CLAIM_LIVE", "LIVE_CHAIN_PROOF", "PRODUCTION_SOLVER_READY",
         "PROVEN_ONCHAIN", "CURRENT_ONCHAIN")
        if phrase in all_fixture_text
    ]
    # The phrase "No synthetic circuit was deployed on X Layer" is an explicit
    # denial and is expected; check it is present rather than absent.
    denial_present = "No synthetic circuit was deployed on X Layer" in all_fixture_text

    out = {
        "schema": "flip-m3-independent-corpus-review/1",
        "m3b_commit": M3B, "integrated_commit": INTEGRATED,
        "files_compared": len(comparisons),
        "all_blobs_identical": all(x["identical"] for x in comparisons),
        "differing_files": [x["path"] for x in comparisons if not x["identical"]],
        "counts": {
            "task_a": len(a["cases"]), "task_b": len(b["cases"]),
            "witnesses": len(c["witnesses"]), "attacks": len(d["attacks"]),
            "benchmarks": len(e["specs"]),
        },
        "attack_ids": [x["id"] for x in d["attacks"]],
        "all_attacks_spec_only": all(
            "SPEC_ONLY" in x["status"] for x in d["attacks"]),
        "all_sat_expected_present": all("expected_result" in x for x in b["cases"]),
        "synthetic_denial_present": denial_present,
        "suspicious_live_claim_phrases": suspicious,
    }
    (HERE / "corpus-integration.json").write_text(
        json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("files_compared", "differing_files", "attack_ids")}, indent=2))
    print("differing files:", out["differing_files"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
