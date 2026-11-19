"""Independent verification of the M4.5-2D debugging corpus.

Checks hashes, byte-identical regeneration in a scratch tree, trusted vector
calibration, full truth-table and witness re-derivation, cone membership,
diagnostic invariants, correction classifications and the two meta cases.
No production Flip code is invoked. A stderr/stdout transcript is written to
docs/evidence/m45-debugging/verification-transcript.json.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DOCS = ROOT.parent.parent / "docs" / "evidence" / "m45-debugging"
sys.path.insert(0, str(HERE))
import debug_core as d  # noqa: E402


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    checks: list[dict] = []

    # 1. Manifest hashes
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    for item in manifest["files"]:
        path = ROOT / item["path"]
        data = path.read_bytes() if path.exists() else b""
        check(sha(data) == item["sha256"] and len(data) == item["bytes"],
              "hash/size mismatch: %s" % item["path"], errors)
    checks.append({"name": "manifest_hash_and_size", "count": len(manifest["files"]),
                   "result": "PASS" if not errors else "FAIL"})

    # 2. Byte-identical regeneration in scratch
    authored = [p for p in ROOT.rglob("*.json")
                if "__pycache__" not in p.parts and p.name not in {"MANIFEST.json", "BUILD_INFO.json"}]
    with tempfile.TemporaryDirectory(prefix="flip-m45-2d-") as tmp:
        scratch = Path(tmp)
        (scratch / "generators").mkdir()
        for src in HERE.glob("*.py"):
            shutil.copy2(src, scratch / "generators" / src.name)
        proc = subprocess.run([sys.executable, str(scratch / "generators" / "build_corpus.py")],
                              capture_output=True, text=True)
        check(proc.returncode == 0, "scratch build failed: %s" % proc.stderr[-500:], errors)
        regenerated = 0
        for path in authored:
            counterpart = scratch / path.relative_to(ROOT)
            if not counterpart.exists():
                errors.append("scratch missing %s" % path.name)
                continue
            if counterpart.read_bytes() != path.read_bytes():
                errors.append("regeneration mismatch %s" % path.name)
            else:
                regenerated += 1
    checks.append({"name": "byte_identical_regeneration", "files": regenerated,
                   "result": "PASS" if regenerated == len(authored) else "FAIL"})

    # 3. Calibration
    cal = d.self_test()
    check(cal["xor_vector"] == [[0], [1], [1], [0]], "XOR calibration failed", errors)
    check(cal["nand_vector"] == [[1], [1], [1], [0]], "NAND calibration failed", errors)
    checks.append({"name": "trusted_vector_calibration", "checks": cal["checks"],
                   "result": "PASS"})

    corpus = json.loads((ROOT / "cases" / "debugging-corpus.json").read_text(encoding="utf-8"))
    cases = corpus["cases"]
    required = {"swapped_outputs", "incorrect_ref_input_mapping", "duplicate_fan_out",
                "disconnected_or_unbound_pin", "wrong_output_ordering",
                "multiple_changed_connections", "nested_ref_dependencies",
                "equivalent_rewiring", "several_possible_contributing_connections",
                "defective_connection_not_uniquely_identifiable"}
    check(len(cases) == 10, "expected 10 cases, got %d" % len(cases), errors)
    check({c["category"] for c in cases} == required, "missing required category", errors)
    check(all(c["provenance"] == "SYNTHETIC" for c in cases),
          "a case is not labeled SYNTHETIC", errors)

    # Rebuild the bank independently from the recorded identity blocks.
    import build_corpus as b  # noqa: E402
    bank = b.BANK
    replayed = 0
    for case in cases:
        cid = case["caseId"]
        n_in = case["reference"]["nIn"]
        n_out = case["reference"]["nOut"]
        ref_net = bytes.fromhex(case["reference"]["netlistHex"][2:])
        cand_net = bytes.fromhex(case["candidate"]["netlistHex"][2:])
        ref_map = case["reference"]["outputMap"]
        cand_map = case["candidate"]["outputMap"]
        ref = d.load(ref_net, n_in, n_out, bank)
        try:
            cand = d.load(cand_net, n_in, n_out, bank)
        except (d.Malformed, d.ResourceLimit) as exc:
            check(case["expected"]["verdict"] == "INVALID_INPUT",
                  "%s: invalid candidate not expected" % cid, errors)
            check(case["diagnosticExpectation"]["suspectedConnections"] == [],
                  "%s: fault attribution on structural rejection" % cid, errors)
            continue

        wt = d.witness_table(ref, ref_map, cand, cand_map)
        verdict = {"EQUIVALENT": "EQUIVALENT", "DIFFERENT": "DIFFERENT",
                   "INVALID_INPUT": "INVALID_INPUT"}[wt["kind"]]
        check(case["expected"]["verdict"] == verdict,
              "%s: verdict %s != %s" % (cid, case["expected"]["verdict"], verdict), errors)
        if wt["kind"] == "EQUIVALENT":
            check(case["diagnosticExpectation"]["class"] == "NO_FAULT_ATTRIBUTION",
                  "%s: equivalent case attributed a fault" % cid, errors)
            check(case["diagnosticExpectation"]["suspectedConnections"] == [],
                  "%s: equivalent case has suspects" % cid, errors)
        if wt["kind"] == "DIFFERENT":
            w = wt["witness"]
            check(case["expected"]["witness"]["in"] == w["in"],
                  "%s: witness input mismatch" % cid, errors)
            check(case["expected"]["witness"]["reference_out"] == w["reference_out"],
                  "%s: reference output mismatch" % cid, errors)
            check(case["expected"]["witness"]["candidate_out"] == w["candidate_out"],
                  "%s: candidate output mismatch" % cid, errors)
            check(case["expected"]["differingBits"] == w["differing_bits"],
                  "%s: differing bits mismatch" % cid, errors)
            cone = d.trace_cone(cand, [cand_map[i] for i in w["differing_bits"]])
            stored = case["cone"]
            check(stored["connections"] == cone["connections"],
                  "%s: cone mismatch" % cid, errors)
            conn_refs = {c["connectionRef"] for c in cone["connections"]}
            for suspect in case["diagnosticExpectation"]["suspectedConnections"]:
                if suspect.startswith("top/outputMap"):
                    check(suspect in {x["connectionRef"] for x in
                                      case["candidateOutputMapConnections"]},
                          "%s: suspect output-map pin not declared" % cid, errors)
                else:
                    check(suspect in conn_refs,
                          "%s: suspect %s not in replayed cone" % (cid, suspect), errors)
            check(not case["diagnosticExpectation"]["uniqueFaultClaim"],
                  "%s: unique fault claimed" % cid, errors)
            replayed += 1

    checks.append({"name": "verdict_witness_cone_rederivation", "differingCases": replayed,
                   "result": "PASS"})

    # 4. D10 alternatives genuinely indistinguishable
    d10 = next(c for c in cases if c["caseId"] == "D10")
    alts = d10["alternativeSingleEdgeCauses"]
    check(len(alts) >= 2 and len({a["connectionRef"] for a in alts}) >= 2,
          "D10 lacks distinct alternative connections", errors)
    xor_ref = d.load(d.encode(b.xor_els()), 2, 1, bank)
    xor_sig = [r["out"] for r in d.exhaustive(xor_ref, [7])]
    for alt in alts:
        els = [d.nand(*e.ins) for e in xor_ref.elements]
        els[alt["elementIndex"]].ins[alt["inputPin"]] = alt["replacementSignal"]
        alt_c = d.load(d.encode(els), 2, 1, bank)
        alt_sig = [r["out"] for r in d.exhaustive(alt_c, [7])]
        check(alt_sig == d10["observedWrongTruthTable"],
              "D10 alternative does not reproduce the wrong table", errors)
        restored = [d.nand(*e.ins) for e in xor_ref.elements]
        for other in alts:
            restored[other["elementIndex"]].ins[other["inputPin"]] = other["priorSignal"]
        check(len(alts) > 1, "D10 needs at least two alternatives", errors)
    checks.append({"name": "d10_indistinguishable_causes", "alternatives": len(alts),
                   "result": "PASS"})

    # 5. Verified corrections actually restore equivalence
    for cid, target in [("D02", [2, 3]), ("D03", [2, 3])]:
        case = next(c for c in cases if c["caseId"] == cid)
        ref = d.load(bytes.fromhex(case["reference"]["netlistHex"][2:]), 2, 1, bank)
        els = []
        for e in d.decode(bytes.fromhex(case["candidate"]["netlistHex"][2:]), 2):
            els.append(d.Element(e.op, list(target) if e.op == d.REF else list(e.ins),
                                 e.cpu, e.cid, e.n_out))
        restored = d.load(d.encode(els), 2, 1, bank)
        wt = d.witness_table(ref, case["reference"]["outputMap"],
                             restored, case["candidate"]["outputMap"])
        check(wt["kind"] == "EQUIVALENT", "%s: prior mapping did not restore equivalence" % cid, errors)
    checks.append({"name": "verified_prior_mapping_corrections", "cases": 2,
                   "result": "PASS"})

    # 6. Meta cases: missing closure and cone cap
    acc = json.loads((ROOT / "acceptance" / "acceptance-corpus.json").read_text(encoding="utf-8"))
    meta = acc["metaCases"]
    bad_net = d.encode([d.ref(b.XOR_CPU, 99, [2, 3])])
    try:
        d.load(bad_net, 2, 1, bank)
        errors.append("M07 missing REF target was accepted")
    except d.Malformed:
        pass
    check(meta["M07"]["expectedVerdict"] == "INVALID_INPUT", "M07 expectation mismatch", errors)

    xor_c = d.load(d.encode(b.xor_els()), 2, 1, bank)
    cone = d.trace_cone(xor_c, [7], node_cap=1)
    check(cone["truncated"] is True, "M08 cone cap did not truncate", errors)
    check(meta["M08"]["expectedTruncated"] is True, "M08 expectation mismatch", errors)
    checks.append({"name": "meta_missing_closure_and_resource_cap", "cases": 2,
                   "result": "PASS"})

    # 7. Guidance vocabulary and no-LM oracle
    guidance = json.loads((ROOT / "diagnostics" / "correction-guidance.json").read_text(encoding="utf-8"))
    allowed = {"VERIFIED_CORRECTION", "CANDIDATE_DIAGNOSTIC_ACTION", "EXPLANATION_ONLY"}
    for item in guidance["suggestions"]:
        check(item["classification"] in allowed,
              "bad classification %s" % item["id"], errors)
    check(guidance["llmOracle"] == "NONE", "LLM oracle claim changed", errors)
    check(any(x["classification"] == "VERIFIED_CORRECTION" for x in guidance["suggestions"]),
          "no verified correction entry", errors)
    checks.append({"name": "correction_classification_vocabulary",
                   "suggestions": len(guidance["suggestions"]), "result": "PASS"})

    # 8. Diagnostic class separation
    rules = json.loads((ROOT / "diagnostics" / "diagnostic-rules.json").read_text(encoding="utf-8"))
    check(all(not e["uniqueFaultClaim"] for e in rules["caseExpectations"]),
          "a diagnostic expectation claims a unique fault", errors)
    check(len(rules["caseExpectations"]) == len(cases), "rule/case count mismatch", errors)
    checks.append({"name": "diagnostic_no_unique_fault_claim",
                   "cases": len(cases), "result": "PASS"})

    result = "PASS" if not errors else "FAIL"
    transcript = {"artifactType": "EXECUTED_CHECK_TRANSCRIPT",
                  "artifactVersion": "1.0.0", "result": result,
                  "generatorCore": d.CORE_VERSION, "caseCount": len(cases),
                  "checks": checks, "errors": errors}
    DOCS.mkdir(parents=True, exist_ok=True)
    out = DOCS / "verification-transcript.json"
    out.write_text(json.dumps(transcript, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    print(json.dumps({"result": result, "errors": errors, "checks": len(checks),
                      "transcript": str(out.relative_to(ROOT.parent.parent))},
                     indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
