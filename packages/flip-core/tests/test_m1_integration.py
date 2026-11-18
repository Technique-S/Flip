"""Offline archive consistency only. No evaluator, chain reader or solver replay."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from flip_api.app import app
from flip_core.contracts import ContractError, validate_contract
from flip_core.models import Integrity
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[3]
RAW = ROOT / "docs/evidence/raw"


def load(relative):
    data = (RAW / relative).read_bytes()
    return json.loads(data.decode("utf-16" if data.startswith(b"\xff\xfe") else "utf-8"))


def test_git_provenance_and_secret_patterns():
    path = ROOT / "scripts/check_m1_repository.py"
    spec = importlib.util.spec_from_file_location("check_m1_repository", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.review()
    assert result["result"] == "PASS"
    assert len(result["registered_blob_checks"]) == 14
    assert result["credential_pattern_findings"] == 0


def test_archived_recomputation_without_rewriting_evidence(tmp_path):
    # The archival script writes a derived file, so run an exact copy against exact
    # raw copies in scratch, never against its tracked evidence directory.
    scratch = tmp_path / "archive"
    shutil.copytree(ROOT / "docs/evidence", scratch / "docs/evidence")
    script = scratch / "docs/evidence/derived/recompute_checks.py"
    subprocess.run([sys.executable, str(script)], check=True, capture_output=True)
    output = scratch / "docs/evidence/derived/recomputed_checks.json"
    assert (
        output.read_bytes() == (ROOT / "docs/evidence/derived/recomputed_checks.json").read_bytes()
    )


def test_netlist_digests_and_recorded_truth_table():
    raw = load("M0/xlayer_circuits.json")
    composition = load("M0/composition_poc.json")
    assert raw["chainId"] == 196
    samples = raw["processors"]["0x839BDD6fA7A66416a609A735E11DE5411b98574E"]["sample"]
    for source in composition["sources"]:
        sample = next(s for s in samples if s["circuitId"] == source["id"])
        netlist = bytes.fromhex(sample["netlist"][2:])
        assert hashlib.sha256(netlist).hexdigest() == source["netlistSha256"]
    composed = bytes.fromhex(composition["composedNetlist"][2:])
    assert len(composed) == composition["composedNetlistBytes"] == 81
    assert hashlib.sha256(composed).hexdigest() == (
        "3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce"
    )
    rerun = load("M05/gate_a_compose_rerun.json")
    assert rerun["composedNetlist"] == composition["composedNetlist"]
    expected = {"00": "00", "01": "02", "02": "02", "03": "01"}
    assert len(composition["truthTable"]) == 4
    for row in composition["truthTable"]:
        assert row["pass"] is True
        assert row["expected"] == row["official"] == row["independent"] == expected[row["in"]]


def test_recorded_scale_and_negative_findings_are_internally_consistent():
    scale = load("M05/gate_c_scale.json")
    negative = load("M05/gate_b_negative.json")
    assert len(scale["scales"]) == 7
    count = 0
    for size in scale["scales"]:
        assert len(size["cases"]) == 4
        for case in size["cases"].values():
            count += 1
            recorded = case["backends"]["minisat"]
            assert recorded["matchesExpected"] is True
            assert recorded["verdict"] == case["expectedVerdict"]
            if recorded["verdict"] == "DIFFERENT":
                assert recorded["solverResult"] == "SAT"
                assert recorded["witnessVerifiedBySim"] is True
            else:
                assert recorded["solverResult"] == "UNSAT"
            fallback = case["backends"]["dpll"]
            if fallback["status"] in ("TIMEOUT", "SKIPPED"):
                assert fallback["verdict"] == "UNKNOWN"
    assert count == 28
    assert len(scale["correctnessSafeguards"]) == 7
    assert all(s["passed"] for s in scale["correctnessSafeguards"])
    assert len(negative["negativeTests"]) == 9
    assert all(n["detected"] and n["issues"] for n in negative["negativeTests"])
    assert negative["allNegativeDetected"] is True
    assert negative["liveChecks"]["chainIds"]["base"] == 8453


def test_legacy_manifest_hashes_and_dependency_netlist_bytes():
    archive = load("M05/gate_b_manifest.json")
    for manifest in archive["manifests"]:
        # Reproduce the legacy audit digest without migrating it into the frozen
        # v1 model. Addresses/IDs in this raw artifact keep their historical form.
        payload = {k: v for k, v in manifest.items() if k != "manifestHash"}
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = "0x" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        assert digest == manifest["manifestHash"]
        assert manifest["blockNumber"] == archive["blockNumberX"]
        assert manifest["blockHash"] == archive["blockHashX"]
        for circuit in [manifest, *[d["target"] for d in manifest["dependencies"]]]:
            raw = bytes.fromhex(circuit["netlist"][2:])
            assert len(raw) == circuit["netlistBytes"]
            assert "0x" + hashlib.sha256(raw).hexdigest() == circuit["netlistHash"]


def test_vectors_traces_and_revert_are_recorded_not_reexecuted():
    vectors = load("M0/vectors.json")
    assert len(vectors["valid"]) == 5
    assert len(vectors["illFormed"]) == 8
    assert len(vectors["packingEdgeCases"]["cases"]) == 5
    assert hashlib.sha256((RAW / "M0/vectors.json").read_bytes()).hexdigest() == (
        "1a02f5cf991c130a22dc6cc6ee93d0f8fe0720afed081665fa8b8018aefd203b"
    )
    stateful = load("M05/gate_c_stateful.json")
    embedded = load("M05/gate_c_scale.json")["statefulKBeat"]
    assert stateful["beats"] == 8
    assert stateful["firstDifferenceBeat"] == 0
    assert stateful["traceOriginal"] == embedded["traceOriginal"]
    assert stateful["traceMutant"] == embedded["traceMutant"]
    revert = load("M05/gate_a_probe2.json")
    assert revert["overrideSupported"] is False
    assert revert["tapeoutSimFull"]["status"] == "reverted"
    assert revert["tapeoutSimFull"]["result"] is None
    assert revert["revertArgDecode"][0]["args"] == [61453, 0, 1, 0]


def test_imported_history_does_not_become_current_chain_verification():
    raw = (RAW / "M05/gate_b_manifest.json").read_bytes()
    historical = json.loads(raw)["manifests"][0]
    assert historical["blockNumber"] == 76056306
    # Legacy audit JSON is not a frozen v1 manifest and has no live revalidation.
    with pytest.raises(ContractError):
        validate_contract("manifest", raw)
    with pytest.raises(ValidationError):
        Integrity(freshness="CURRENT", checkedBlock=None)
    response = TestClient(app).post("/api/v1/import", json=historical)
    assert response.status_code == 501
    assert response.json()["error"]["code"] == "NOT_IMPLEMENTED"
    assert "integrity" not in response.json()


def test_report_only_gaps_are_not_executable_golden_fixtures():
    missing = (ROOT / "docs/evidence/MISSING_ARTIFACTS.md").read_text(encoding="utf-8")
    assert "REPORT_ONLY" in missing
    assert "100 deterministic composition runs" in missing
    assert "BLOCKER for byte-identity" in missing
    # The historical manifest has only these two captured snapshots. Missing
    # NAND/composed manifests must not be synthesized to satisfy the v1 schema.
    assert [m["label"] for m in load("M05/gate_b_manifest.json")["manifests"]] == [
        "xor1",
        "wrapper4",
    ]
    # M2-C/M3-C add registered adversarial specifications, not missing historical
    # observations. Preserve the restriction outside those audited namespaces;
    # each corpus has independent byte-register and provenance checks.
    assert not [
        path
        for path in (ROOT / "fixtures").rglob("*.json")
        if not any(
            path.is_relative_to(ROOT / namespace)
            for namespace in (
                "fixtures/m2-adversarial",
                "fixtures/m3-verification",
                "fixtures/m4-ux-acceptance",
            )
        )
    ]
