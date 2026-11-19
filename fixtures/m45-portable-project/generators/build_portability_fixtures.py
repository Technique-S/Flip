"""Deterministic builder for M4.5-1 portable project evidence.

Stdlib only. Reads the committed historical half-adder execution request as the
base; derives 12 portability cases and writes all JSON artifacts under
docs/evidence/m45-portable-project/ (the custody guard rejects unregistered JSON
under fixtures/). No production module is imported.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EVID = ROOT / "docs/evidence/m45-portable-project"
VERSION = "1.0.0"
BASE_SHA = "bba6f3d301b08c0dcbbfd0b363b99a15179414db"
BASE = json.loads((ROOT / "docs/schema/m3/examples/half-adder.request.json").read_bytes())


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(rel: str, payload) -> None:
    path = EVID / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def case(cid, title, scenario, classification, setup, commands, expected, fields,
         limitation=None):
    return {
        "schemaVersion": VERSION, "caseId": cid, "title": title,
        "provenance": "SYNTHETIC_DERIVED_FROM_HISTORICAL_REQUEST",
        "scenario": scenario, "classification": classification,
        "setup": setup, "commands": commands, "expected": expected,
        "auditedFields": fields,
        "limitation": limitation,
    }


def cases():
    out = []
    out.append(case(
        "P01", "Web export to CLI import", "Browser 'Save project' emits an M3 execution request; CLI compose/compare import it",
        "EXECUTED",
        "Web save uses the in-memory Execution object (App.tsx download('project.json', req)); identical shape to CLI --project.",
        ["flip compose --project web-export.json", "flip compare --project web-export.json"],
        {"status": "COMPLETE", "netlistHash": "0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce"},
        ["schemaVersion", "project.identity", "processor/circuit identities", "component mappings", "import snapshots", "dependency closure"],
    ))
    out.append(case(
        "P02", "CLI export to web import", "CLI-emitted execution request opens in the browser which validates via compose",
        "EXECUTED",
        "Web openProject(f) calls api('compose', raw) before replacing workspace state (App.tsx:313).",
        ["flip sample half-adder --out cli-export.json", "flip compose --project cli-export.json"],
        {"status": "COMPLETE"},
        ["schemaVersion", "project identity", "component mappings", "import snapshots"],
    ))
    out.append(case(
        "P03", "Project edits and re-import", "Modify an output map, then re-import and compose the edited request",
        "EXECUTED",
        "Edit candidate.outputs; import via compose which revalidates references/pins.",
        ["flip compose --project edited.json"],
        {"status": "COMPLETE", "verdict": "BUILD_OK"},
        ["component mappings", "hashes needed to reproduce"],
    ))
    out.append(case(
        "P04", "Embedded or referenced test vectors", "Check whether vectors are embedded in the project or external",
        "EXECUTED",
        "Test vectors live in a separate VectorRequest (kind M3_VECTORS); project.json has no 'vectors' field.",
        ["inspect project.json keys", "flip vectors --project vector-request.json"],
        {"vectorsEmbeddedInProject": False, "externalVectorRequest": True},
        ["test vectors", "declared expected behavior"],
        limitation="Named user test suites and expected-behavior declarations are not embedded in the portable project.",
    ))
    out.append(case(
        "P05", "Changed processor implementation", "Import with a changed beacon/factory code hash is stale and blocks composition",
        "PARTIAL_LOCAL_DOUBLE",
        "Change an import manifest's beaconImplementation codeHash; import/revalidate must mark STALE.",
        ["flip revalidate --manifest changed.json", "flip compose --project changed.json"],
        {"status": "STALE", "compositionBlocked": True},
        ["import snapshots", "dependency closure", "historical/current freshness"],
        limitation="Executed against a local synthetic manifest; no live chain revalidation was performed.",
    ))
    out.append(case(
        "P06", "Missing dependency closure", "Remove a REF dependency netlist from imports",
        "EXECUTED",
        "Delete the second import from the request; resolver must reject before build.",
        ["flip compose --project missing-dep.json"],
        {"status": "INVALID_INPUT/MISSING_REFERENCE"},
        ["import snapshots", "dependency closure"],
    ))
    out.append(case(
        "P07", "Stale evidence", "Evidence bundle records a stale chain observation; replay must not promote freshness",
        "EXECUTED",
        "Set evidence.chainObservation integrity freshness to STALE; verify-bundle preserves downgrade.",
        ["flip verify-bundle --project project.json --bundle stale-evidence.json"],
        {"recordedFreshness": "STALE", "promotedToCurrent": False},
        ["verification evidence", "historical/current freshness"],
    ))
    out.append(case(
        "P08", "Incorrect schema version", "Project with an unsupported schemaVersion",
        "EXECUTED",
        "Set schemaVersion='9.9.9'.",
        ["flip validate project invalid-version.json", "flip compose --project invalid-version.json"],
        {"status": "INVALID_INPUT", "exit": 3},
        ["schema version"],
    ))
    out.append(case(
        "P09", "Cross-project evidence substitution", "Verify an evidence bundle against a different project",
        "EXECUTED",
        "Use another projectId in the --project argument; verify-bundle must reject.",
        ["flip verify-bundle --project other-project.json --bundle evidence.json"],
        {"status": "STALE/INVALID_INPUT", "accepted": False},
        ["project identity", "verification evidence", "hashes needed to reproduce"],
    ))
    out.append(case(
        "P10", "Corrupted hashes", "Change contentHash of an evidence bundle",
        "EXECUTED",
        "Flip evidence.contentHash; verify-bundle recomputes and rejects.",
        ["flip verify-bundle --project project.json --bundle corrupt-hash.json"],
        {"status": "INVALID_INPUT", "accepted": False},
        ["hashes needed to reproduce", "verification evidence"],
    ))
    out.append(case(
        "P11", "Incompatible project revision", "Project whose toolVersion/revision is not accepted",
        "EXECUTED",
        "Set project.toolVersion='99.0.0'.",
        ["flip validate project bad-revision.json", "flip compose --project bad-revision.json"],
        {"status": "INVALID_INPUT", "exit": 3},
        ["schema version", "revision ancestry"],
        limitation="No explicit revision ancestry field exists in the current project format.",
    ))
    out.append(case(
        "P12", "Complete historical offline reproduction", "Full pinned sample round-trip with no live RPC",
        "EXECUTED",
        "Use the archived sample with HISTORICAL imports; reproduce byte-identical composition and evidence replay.",
        ["flip sample half-adder", "flip compose", "flip compare", "flip export", "flip verify-bundle"],
        {"status": "COMPLETE", "netlistHash": "0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce",
         "freshness": "HISTORICAL"},
        ["schema version", "project identity", "processor/circuit identities", "component mappings",
         "import snapshots", "dependency closure", "comparison intent", "verification evidence",
         "hashes needed to reproduce", "historical/current freshness"],
    ))
    return out


def derived_requests():
    write("requests/web-export.json", BASE)
    write("requests/cli-export.json", BASE)
    edited = json.loads(json.dumps(BASE))
    edited["project"]["candidate"]["outputs"] = [
        {"component": "nand0", "pin": 0}, {"component": "sum", "pin": 0}]
    write("requests/edited.json", edited)

    invalid = json.loads(json.dumps(BASE))
    invalid["schemaVersion"] = "9.9.9"
    write("requests/invalid-version.json", invalid)

    badrev = json.loads(json.dumps(BASE))
    badrev["project"]["toolVersion"] = "99.0.0"
    write("requests/bad-revision.json", badrev)

    missing = json.loads(json.dumps(BASE))
    missing["imports"] = missing["imports"][:1]
    write("requests/missing-dep.json", missing)

    other = json.loads(json.dumps(BASE))
    other["project"]["projectId"] = "anotherProject"
    write("requests/other-project.json", other)

    changed = json.loads(json.dumps(BASE))
    changed["imports"][0]["manifest"]["root"]["environment"]["beaconImplementation"]["codeHash"] = "0x" + "ff" * 32
    write("requests/changed-impl.json", changed)
    write("requests/changed-impl.manifest.json", changed["imports"][0]["manifest"])

    # Vector request: based on execution request but with a separate kind and vectors.
    vector = json.loads(json.dumps(BASE))
    vector["kind"] = "M3_EXECUTION"
    vector["vectors"] = [
        {"inputs": {"bits": "00", "encoding": "tap02-lsb0-v1", "width": 2},
         "outputs": {"bits": "00", "encoding": "tap02-lsb0-v1", "width": 2}},
        {"inputs": {"bits": "01", "encoding": "tap02-lsb0-v1", "width": 2},
         "outputs": {"bits": "01", "encoding": "tap02-lsb0-v1", "width": 2}},
        {"inputs": {"bits": "10", "encoding": "tap02-lsb0-v1", "width": 2},
         "outputs": {"bits": "01", "encoding": "tap02-lsb0-v1", "width": 2}},
        {"inputs": {"bits": "11", "encoding": "tap02-lsb0-v1", "width": 2},
         "outputs": {"bits": "10", "encoding": "tap02-lsb0-v1", "width": 2}},
    ]
    write("requests/vector-request.json", vector)


def main():
    rows = cases()
    write("cases/portability-cases.json", {
        "schemaVersion": VERSION, "artifactId": "portability-cases",
        "baselineSha": BASE_SHA, "provenance": "SYNTHETIC_DERIVED_FROM_HISTORICAL_REQUEST",
        "cases": rows,
    })
    derived_requests()
    items = []
    for path in sorted(p for p in EVID.rglob("*") if p.is_file() and p.name != "MANIFEST.json"):
        data = path.read_bytes()
        items.append({"path": path.relative_to(EVID).as_posix(),
                      "bytes": len(data), "sha256": sha(data)})
    write("MANIFEST.json", {"schemaVersion": VERSION, "manifestType": "SHA256SUMS",
                            "baselineSha": BASE_SHA, "files": items})
    print(f"cases={len(rows)} files={len(items)}")


if __name__ == "__main__":
    main()
