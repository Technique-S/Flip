"""Independent production-adapter checks for PR #9 (M4.5-1I-V2 final review).

Exercises the REAL agent_portable_adapter through core, CLI and loopback API.
Expected hashes are recomputed with a standalone json+hashlib implementation of
the flip-json-v1 profile (no import of flip_core.canonical). Structural and
authority invariants are asserted directly from the documented contract, not
from production output alone. No production file is modified.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/flip-core/src"))
sys.path.insert(0, str(ROOT / "packages/flip-core/tests"))
sys.path.insert(0, str(ROOT / "packages/flip-cli/src"))
sys.path.insert(0, str(ROOT / "packages/flip-api/src"))

from fastapi.testclient import TestClient  # noqa: E402
from flip_api.app import app  # noqa: E402
from flip_cli.main import main as cli_main  # noqa: E402
from flip_core import agent_portable_adapter as adapter  # noqa: E402
from flip_core.canonical import canonical_bytes  # noqa: E402 (only to write CLI input)
from flip_core.contracts import ContractError  # noqa: E402
from flip_core.portable import (  # noqa: E402
    bounded_operation,
    create_package,
)
from flip_core.verification import parse_request  # noqa: E402
from flip_core.workflow import sample  # noqa: E402

OUT = ROOT / "docs/evidence/m45-agent-portable-final-review/results/independent-adapter-checks.json"
FLIP = str(ROOT / ".venv/Scripts/flip.exe")
TESTED_SHA = "9c0c23698dfd1c7045de348da851c28d68f5e22b"
PRIOR = json.loads(
    (ROOT / "docs/schema/m45-debugging/examples/swapped-prior.execution.json").read_bytes()
)


def ihash(value) -> str:
    """Standalone flip-json-v1 hash; deliberately does NOT call production code."""
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode(
        "utf-8"
    )
    return "0x" + hashlib.sha256(raw).hexdigest()


def named_vectors():
    def bits(s):
        return dict(encoding="tap02-lsb0-v1", width=2, bits=s)

    return [
        dict(
            name="halfAdder",
            declaredIntent="Carry and sum at numeric pins 0 and 1",
            expectedCoverage="EXHAUSTIVE_DECLARED_DOMAIN",
            vectors=[
                dict(inputs=bits(i), outputs=bits(o))
                for i, o in [("00", "00"), ("01", "01"), ("10", "01"), ("11", "10")]
            ],
        )
    ]


def prep(package=None, action="correct", **fields):
    package = package if package is not None else create_package(PRIOR, tests=named_vectors())
    return adapter.prepare_adapter(
        dict(package=package, action=action, continueOnTestMismatch=True, **fields)
    )["request"]


def export_evidence(raw):
    from flip_core.workflow import product

    return product(
        "export",
        dict(schemaVersion="m4-1.0.0", kind="PRODUCT_REQUEST", executionRequest=raw),
    )


def ref_for(artifact, raw):
    return dict(
        kind="FLIP_EVIDENCE",
        digest=artifact["contentHash"],
        executionRequestHash=ihash(raw),
        reproduce=artifact["reproduce"],
        engineHash=artifact["comparison"]["engineHash"],
    )


def safe_call(fn):
    try:
        return {"ok": True, "value": fn()}
    except ContractError as exc:
        return {"ok": False, "code": exc.code, "message": str(exc.message)[:160]}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "code": type(exc).__name__, "message": str(exc)[:160]}


def no_authority(result):
    """Independent invariant: a failure never creates a revision or proof claim."""
    if not isinstance(result, dict):
        return False
    if result.get("revisionCreated") or result.get("revisedPackage") is not None:
        return False
    if result.get("status") == "COMPLETE":
        return False
    return True


def run_check(cid, name, fn):
    try:
        obs = fn()
        err = None
    except Exception as exc:  # noqa: BLE001
        obs = {"exception": f"{type(exc).__name__}: {exc}"}
        err = f"{type(exc).__name__}: {exc}"
    passed = bool(obs.get("pass")) if isinstance(obs, dict) else False
    return {
        "id": cid,
        "name": name,
        "observed": obs,
        "error": err,
        "pass": passed,
    }


def main():
    rows = []
    os.environ["FLIP_LOCAL_SOLVER"] = "1"
    env = dict(os.environ, FLIP_LOCAL_SOLVER="1")

    # ---------------- Task B: independent production execution ----------------

    def b1_identity():
        p = create_package(PRIOR, tests=named_vectors())
        r = prep(p)
        ind_pkg_hash = ihash(p)
        ind_exec_hash = ihash(PRIOR)
        obs = dict(
            packageHashIndependent=ind_pkg_hash,
            packageHashMatchesPin=ind_pkg_hash == r["expectedPackageHash"],
            execHashIndependent=ind_exec_hash,
            execHashMatchesPin=ind_exec_hash == r["expectedExecutionRequestHash"],
            revisionHashMatchesPin=p["revision"]["revisionHash"] == r["expectedRevisionHash"],
            ttamper=[],
        )
        for field, wrong in (
            ("expectedPackageHash", "0x" + "00" * 32),
            ("expectedRevisionHash", "0x" + "11" * 32),
            ("expectedExecutionRequestHash", "0x" + "22" * 32),
        ):
            body = copy.deepcopy(r)
            body[field] = wrong
            outcome = safe_call(lambda b=body: adapter.execute(b))
            obs["ttamper"].append(
                {"field": field, "rejected": not outcome["ok"], "code": outcome.get("code")}
            )
        obs["pass"] = (
            obs["packageHashMatchesPin"]
            and obs["execHashMatchesPin"]
            and obs["revisionHashMatchesPin"]
            and all(t["rejected"] for t in obs["ttamper"])
        )
        return obs

    def b2_named_vectors():
        good = create_package(sample("half-adder"), tests=named_vectors())
        body = prep(good, action="inspect")
        res = adapter.execute(body)
        logs = res["receipt"]["logs"] if res.get("receipt") else []
        before = [e for e in logs if e["op"] == "test" and e["step"].startswith("pp_before")]
        obs = dict(
            status=res["status"],
            beforeSteps=len(before),
            verdicts=[e["output"].get("verdict") for e in before],
            coverage=[e["output"].get("coverage") for e in before],
            rowCounts=[e["output"].get("rows") for e in before],
        )
        # A package with deliberately wrong expected outputs must STOP by default.
        wrong = named_vectors()
        wrong[0]["vectors"][0]["outputs"] = dict(encoding="tap02-lsb0-v1", width=2, bits="11")
        bad_pkg = create_package(sample("half-adder"), tests=wrong)
        bad_body = prep(bad_pkg)
        bad_body["continueOnTestMismatch"] = False
        bad_res = adapter.execute(bad_body)
        obs["wrongVectorStatus"] = bad_res["status"]
        obs["wrongVectorNoRevision"] = no_authority(bad_res)
        obs["pass"] = (
            res["status"] == "COMPLETE"
            and obs["beforeSteps"] == 1
            and obs["verdicts"] == ["VECTORS_MATCH"]
            and bad_res["status"] == "DIFFERENT"
            and obs["wrongVectorNoRevision"]
        )
        return obs

    def b3_different_witness_debug():
        body = prep()  # prior (swapped) + named vectors, continueOnTestMismatch=True
        res = adapter.execute(body)
        logs = res["receipt"]["logs"]
        cmp = next(e for e in logs if e["op"] == "compare")
        insp = next(e for e in logs if e["op"] == "inspect")
        obs = dict(
            status=res["status"],
            verdict=cmp["output"]["report"]["verification"]["verdict"],
            witness=cmp["output"]["report"]["verification"]["witness"]["replay"],
            uniqueFaultClaim=insp["output"]["uniqueFaultClaim"],
            replayStatus=res["inputEvidence"],
        )
        obs["pass"] = (
            obs["verdict"] == "DIFFERENT"
            and obs["witness"] == "REF_BEAT_REPRODUCED"
            and obs["uniqueFaultClaim"] is False
        )
        return obs

    def b4_b5_b6_correction_apply_revision():
        p = create_package(PRIOR, tests=named_vectors())
        body = prep(p)
        before = copy.deepcopy(body)
        res = adapter.execute(body)
        logs = res["receipt"]["logs"]
        verify = next(e for e in logs if e["op"] == "verify")
        apply = next(e for e in logs if e["op"] == "apply")
        revised = res["revisedPackage"]
        exp_action = ihash(
            dict(
                original=ihash(PRIOR),
                revision=ihash(
                    {
                        **parse_request(PRIOR).model_dump(mode="json"),
                        "project": {
                            **parse_request(PRIOR).model_dump(mode="json")["project"],
                            "candidate": parse_request(PRIOR).project.referenceCandidate.model_dump(
                                mode="json"
                            ),
                        },
                    }
                ),
            )
        )
        obs = dict(
            status=res["status"],
            verifyClassification=verify["output"]["classification"],
            applyClassification=apply["output"]["classification"],
            actionIdIndependent=exp_action,
            actionIdObserved=verify["output"]["proposal"]["actionId"],
        )
        if revised:
            obs.update(
                parentMatches=revised["revision"]["parentHash"] == p["revision"]["revisionHash"],
                sequence=revised["revision"]["sequence"],
                parentSeq=p["revision"]["sequence"],
                ancestorsTailMatches=revised["ancestors"][-1] == p["revision"],
                candidateEqualsReference=(
                    revised["executionRequest"]["project"]["candidate"]
                    == parse_request(PRIOR).project.referenceCandidate.model_dump(mode="json")
                ),
                originalUnchanged=body == before,
            )
        obs["pass"] = (
            res["status"] == "COMPLETE"
            and obs["verifyClassification"] == "VERIFIED_CORRECTION"
            and obs["applyClassification"] == "VERIFIED_CORRECTION"
            and obs["actionIdObserved"] == exp_action
            and revised is not None
            and obs["parentMatches"]
            and obs["sequence"] == obs["parentSeq"] + 1
            and obs["ancestorsTailMatches"]
            and obs["candidateEqualsReference"]
            and obs["originalUnchanged"]
        )
        return obs

    def b7_original_preservation():
        p = create_package(PRIOR, tests=named_vectors())
        body = prep(p)
        orig_body = copy.deepcopy(body)
        orig_pkg = copy.deepcopy(p)
        res = adapter.execute(body)
        obs = dict(
            status=res["status"],
            bodyUnchanged=body == orig_body,
            packageUnchanged=p == orig_pkg,
            returnedOriginalEqualsInput=res["originalPackage"] == orig_pkg,
            hasRevision=res["revisionCreated"],
        )
        obs["pass"] = (
            obs["bodyUnchanged"]
            and obs["packageUnchanged"]
            and obs["returnedOriginalEqualsInput"]
            and obs["hasRevision"] is True
        )
        return obs

    def b8_evidence_export_replay():
        raw = PRIOR
        artifact = export_evidence(raw)
        ref = ref_for(artifact, raw)
        p = create_package(raw, tests=named_vectors(), evidence_refs=[ref])
        body = prep(p)
        body["evidenceArtifacts"] = {ref["digest"]: artifact}
        body["continueOnEvidenceDifference"] = True
        res = adapter.execute(body)
        logs = res["receipt"]["logs"]
        replay_event = next(e for e in logs if e["step"] == "pp_evidence0")
        obs = dict(
            status=res["status"],
            exportKind=artifact["kind"],
            replayStep=replay_event["status"],
            inputEvidenceStatus=res["inputEvidence"][0]["status"],
            oldRefInOriginal=res["originalPackage"]["evidenceRefs"] == [ref],
            oldRefNotInRevised=ref not in res["revisedPackage"]["evidenceRefs"],
        )
        # Independently replay freshly exported artifacts from the revised package.
        fresh = []
        for e in res["evidenceArtifacts"].values():
            fresh.append(
                e["comparison"]["requestHash"]
                == ihash(
                    parse_request(res["revisedPackage"]["executionRequest"]).model_dump(mode="json")
                )
            )
        obs["freshRefsBoundToRevised"] = all(fresh) and len(fresh) > 0
        repl = bounded_operation(
            dict(
                schemaVersion="flip-portable-project-1.1.0",
                kind="PORTABLE_REQUEST",
                operation="replay-evidence",
                package=res["revisedPackage"],
                artifacts=res["evidenceArtifacts"],
            )
        )
        obs["trustedReplayStatuses"] = [e["status"] for e in repl["results"]]
        obs["trustedReplayVerdicts"] = [
            e["result"]["report"]["verification"]["verdict"] for e in repl["results"]
        ]
        obs["trustedReplayFreshness"] = [
            e["result"]["report"]["integrity"]["freshness"] for e in repl["results"]
        ]
        obs["pass"] = (
            res["status"] == "COMPLETE"
            and artifact["kind"] == "FLIP_EVIDENCE"
            and obs["inputEvidenceStatus"] == "REPLAYED"
            and obs["oldRefInOriginal"]
            and obs["oldRefNotInRevised"]
            and obs["freshRefsBoundToRevised"]
            and all(s == "REPLAYED" for s in obs["trustedReplayStatuses"])
            and all(v == "EQUIVALENT" for v in obs["trustedReplayVerdicts"])
            and all(f == "HISTORICAL" for f in obs["trustedReplayFreshness"])
        )
        return obs

    def b9_cross_project_evidence():
        foreign_raw = sample("swapped")
        foreign = export_evidence(foreign_raw)
        ref = ref_for(foreign, PRIOR)  # claims the selected project, artifact is foreign
        p = create_package(PRIOR, tests=named_vectors(), evidence_refs=[ref])
        body = prep(p)
        body["evidenceArtifacts"] = {ref["digest"]: foreign}
        res = adapter.execute(body)
        obs = dict(
            status=res["status"],
            inputEvidenceStatus=res["inputEvidence"][0]["status"],
            noAuthority=no_authority(res),
        )
        obs["pass"] = (
            obs["status"] in ("STALE", "INVALID_INPUT")
            and obs["inputEvidenceStatus"] == "NOT_REPLAYED"
            and obs["noAuthority"]
        )
        return obs

    def b10_changed_dependency_engine():
        from flip_core.library_models import LibraryRequest
        from flip_core.workflow import project_from_import
        from test_m2_import import identity
        from test_m45_agent_workflow import chain_server
        from test_m45_library import LibraryChain

        chain = LibraryChain()
        imported = (
            chain.library()
            .execute(
                LibraryRequest(
                    operation="import",
                    identity=dict(processor=identity().processor, circuitId="1"),
                )
            )
            .imported
        )
        p = create_package(project_from_import(imported))
        body = prep(p, action="inspect")
        body["workflow"]["steps"] = [
            dict(id="fresh", op="revalidate"),
            dict(id="later", op="build"),
        ]
        chain.beacon_impl = "0x" + "cc" * 20
        with chain_server(chain) as (_, settings):
            res = adapter.execute(body, settings=settings)
        obs = dict(
            status=res["status"],
            logs=len(res["receipt"]["logs"]) if res.get("receipt") else None,
            noAuthority=no_authority(res),
        )
        obs["pass"] = obs["status"] == "STALE" and obs["logs"] == 1 and obs["noAuthority"]
        return obs

    def b11_cancellation_during_revision():
        body = prep()
        res = adapter.execute(body, cancelled=lambda: True)
        stopped = threading.Event()
        original_create = adapter.create_package

        def cancel_after_hash(*a, **k):
            v = original_create(*a, **k)
            stopped.set()
            return v

        adapter.create_package = cancel_after_hash
        try:
            race = adapter.execute(body, cancelled=stopped.is_set)
        finally:
            adapter.create_package = original_create
        obs = dict(
            immediateStatus=res["status"],
            immediateReceiptNone=res["receipt"] is None,
            immediateOriginalPreserved=res["originalPackage"] == body["package"],
            raceStatus=race["status"],
            raceNoRevision=no_authority(race),
            raceOriginalPreserved=race["originalPackage"] == body["package"],
        )
        obs["pass"] = (
            obs["immediateStatus"] == "CANCELLED"
            and obs["immediateReceiptNone"]
            and obs["immediateOriginalPreserved"]
            and obs["raceStatus"] == "CANCELLED"
            and obs["raceNoRevision"]
            and obs["raceOriginalPreserved"]
        )
        return obs

    def b12_deadline_budget():
        body = prep()
        body["workflow"]["budget"]["deadlineMs"] = 1
        res = adapter.execute(body)
        b2 = prep()
        b2["workflow"]["budget"]["maxIterations"] = 1
        res2 = adapter.execute(b2)
        b3 = prep()
        b3["workflow"]["budget"]["maxReceiptBytes"] = 4096
        out = safe_call(lambda: adapter.execute(b3))
        obs = dict(
            deadlineStatus=res["status"],
            deadlineOriginalPreserved=res["originalPackage"] == body["package"],
            deadlineNoRevision=no_authority(res),
            iterationStatus=res2["status"],
            iterationCount=res2["receipt"]["usage"]["iterations"],
            receiptBudgetRejected=not out["ok"],
        )
        obs["pass"] = (
            obs["deadlineStatus"] == "BUDGET_EXHAUSTED"
            and obs["deadlineOriginalPreserved"]
            and obs["deadlineNoRevision"]
            and obs["iterationStatus"] == "BUDGET_EXHAUSTED"
            and obs["iterationCount"] == 1
            and obs["receiptBudgetRejected"]
        )
        return obs

    def b13_concurrent():
        p = create_package(sample("half-adder"))
        body = prep(p, action="inspect")
        before = copy.deepcopy(body)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(adapter.execute, [body, body]))
        # Two independent correction requests from the same pinned parent (siblings).
        cb = prep()
        cb_before = copy.deepcopy(cb)
        with ThreadPoolExecutor(max_workers=2) as pool:
            sibs = list(pool.map(adapter.execute, [cb, cb]))
        obs = dict(
            bodyUnchanged=body == before,
            readonlyNoRevision=all(not r["revisionCreated"] for r in results),
            readonlyDeterministic=results[0]["reproductionHash"] == results[1]["reproductionHash"],
            correctionBodyUnchanged=cb == cb_before,
            siblingStatuses=[r["status"] for r in sibs],
            siblingParents=[r["revisedPackage"]["revision"]["parentHash"] for r in sibs],
            sameParent=sibs[0]["revisedPackage"]["revision"]["parentHash"]
            == sibs[1]["revisedPackage"]["revision"]["parentHash"],
        )
        obs["pass"] = (
            obs["bodyUnchanged"]
            and obs["readonlyNoRevision"]
            and obs["readonlyDeterministic"]
            and obs["correctionBodyUnchanged"]
            and all(s == "COMPLETE" for s in obs["siblingStatuses"])
            and obs["sameParent"]
        )
        return obs

    def b14_legacy_routes():
        client = TestClient(app, client=("127.0.0.1", 1))
        wf = dict(
            steps=[dict(id="build", op="build")],
            executionRequest=sample("half-adder"),
        )
        wf_resp = client.post("/api/agent/v1/execute", json=wf)
        portable_resp = client.post(
            "/api/v1/portable",
            json=dict(
                schemaVersion="flip-portable-project-1.1.0",
                kind="PORTABLE_REQUEST",
                operation="validate",
                package=create_package(sample("half-adder")),
            ),
        )
        path = ROOT / "docs/schema/m3/examples/half-adder.request.json"
        proc = subprocess.run(
            [FLIP, "compose", "--project", str(path)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            timeout=120,
        )
        obs = dict(
            workflowRoute=wf_resp.status_code,
            portableRoute=portable_resp.status_code,
            cliComposeExit=proc.returncode,
        )
        obs["pass"] = (
            obs["workflowRoute"] == 200
            and obs["portableRoute"] == 200
            and obs["cliComposeExit"] == 0
        )
        return obs

    def b15_stop_authorization():
        for purpose in ("PUBLISH", "DEPLOY"):
            body = prep(action="publish")
            body["purpose"] = purpose
            body["createRevision"] = True
            res = adapter.execute(body)
            stop = res["receipt"]["logs"][0]["output"]
            obs = dict(
                purpose=purpose,
                status=res["status"],
                logs=len(res["receipt"]["logs"]),
                signingCapability=stop["signingCapability"],
                retryable=stop["retryable"],
                noRevision=no_authority(res),
                originalPreserved=res["originalPackage"] == body["package"],
            )
            if purpose == "PUBLISH":
                rows.append(
                    {
                        "id": "B15a",
                        "name": "STOP_AUTHORIZATION (PUBLISH)",
                        "observed": obs,
                        "error": None,
                        "pass": (
                            obs["status"] == "STOP_AUTHORIZATION"
                            and obs["logs"] == 1
                            and obs["signingCapability"] is False
                            and obs["retryable"] is False
                            and obs["noRevision"]
                            and obs["originalPreserved"]
                        ),
                    }
                )
            else:
                rows.append(
                    {
                        "id": "B15b",
                        "name": "STOP_AUTHORIZATION (DEPLOY)",
                        "observed": obs,
                        "error": None,
                        "pass": (
                            obs["status"] == "STOP_AUTHORIZATION"
                            and obs["logs"] == 1
                            and obs["signingCapability"] is False
                            and obs["retryable"] is False
                            and obs["noRevision"]
                            and obs["originalPreserved"]
                        ),
                    }
                )
        return {"pass": True, "note": "see B15a/B15b rows"}

    for cid, name, fn in (
        ("B01", "portable package identity binding (independent hash + pins)", b1_identity),
        ("B02", "named test-vector execution (match and mismatch stop)", b2_named_vectors),
        ("B03", "DIFFERENT witness replay and debugging", b3_different_witness_debug),
        (
            "B04-06",
            "candidate verification, explicit apply, new revision parent",
            b4_b5_b6_correction_apply_revision,
        ),
        ("B07", "original package preservation", b7_original_preservation),
        ("B08", "evidence export and trusted replay", b8_evidence_export_replay),
        ("B09", "cross-project evidence rejection", b9_cross_project_evidence),
        ("B10", "changed dependency/engine handling (STALE)", b10_changed_dependency_engine),
        ("B11", "cancellation during revision creation", b11_cancellation_during_revision),
        ("B12", "deadline and budget exhaustion", b12_deadline_budget),
        ("B13", "repeated/concurrent requests", b13_concurrent),
        ("B14", "legacy route preservation", b14_legacy_routes),
        ("B15", "STOP_AUTHORIZATION", b15_stop_authorization),
    ):
        rows.append(run_check(cid, name, fn))

    # ---------------- Task C: adversarial attacks ----------------

    def c1_forged_correction():
        body = prep()
        for step in body["workflow"]["steps"]:
            if step["op"] == "verify":
                step["actionId"] = "0x" + "00" * 32
        res = adapter.execute(body)
        obs = dict(
            status=res["status"],
            noRevision=no_authority(res),
            originalPreserved=res["originalPackage"] == body["package"],
        )
        obs["pass"] = obs["status"] == "STALE" and obs["noRevision"] and obs["originalPreserved"]
        return obs

    def c2_altered_package_hash():
        p = create_package(PRIOR)
        body = prep(p)
        # Alter package bytes while keeping the pinned hash.
        body["package"]["executionRequest"]["project"]["projectId"] = "foreign"
        out = safe_call(lambda: adapter.execute(body))
        obs = dict(
            rejectedDirectly=not out["ok"],
            code=out.get("code"),
            noExecution=out.get("code") in ("INVALID_INPUT", "ContractError"),
        )
        obs["pass"] = obs["rejectedDirectly"]
        return obs

    def c3_forged_parent():
        p = create_package(PRIOR, tests=named_vectors())
        body = prep(p)
        body["package"]["revision"]["parentHash"] = "0x" + "11" * 32
        out = safe_call(lambda: adapter.execute(body))
        obs = dict(rejected=not out["ok"], code=out.get("code"))
        obs["pass"] = obs["rejected"]
        return obs

    def c4_project_mutation():
        body = prep()
        original = copy.deepcopy(body)
        model = adapter.parse_adapter(body)
        body["package"]["executionRequest"]["project"]["projectId"] = "foreign"
        body["workflow"]["steps"].clear()
        obs = dict(
            snapshotPackageUnchanged=model.package == original["package"],
            snapshotStepsKept=bool(model.workflow.steps),
            pinStillValid=ihash(model.package) == model.expectedPackageHash,
        )
        obs["pass"] = all(obs.values())
        return obs

    def c5_reused_correction():
        other = sample("swapped")
        body = prep(create_package(other))
        # actionId computed for PRIOR, reused against a different package.
        from flip_core.debugging import prior_action

        reused = prior_action(parse_request(PRIOR)).actionId
        for step in body["workflow"]["steps"]:
            if step["op"] in ("verify", "apply"):
                step["actionId"] = reused
        res = adapter.execute(body)
        obs = dict(
            status=res["status"],
            noRevision=no_authority(res),
            originalPreserved=res["originalPackage"] == body["package"],
        )
        obs["pass"] = (
            obs["status"] in ("STALE", "UNKNOWN", "INVALID_INPUT")
            and obs["noRevision"]
            and obs["originalPreserved"]
        )
        return obs

    def c6_foreign_evidence_reference():
        foreign = export_evidence(sample("swapped"))
        ref = ref_for(foreign, PRIOR)
        p = create_package(PRIOR, evidence_refs=[ref])
        body = prep(p)
        body["evidenceArtifacts"] = {ref["digest"]: foreign}
        # Also craft a matching digest with wrong engineHash (identity mismatch).
        bad = copy.deepcopy(foreign)
        bad["comparison"]["engineHash"] = "0x" + "99" * 32
        bad["contentHash"] = ihash({k: v for k, v in bad.items() if k != "contentHash"})
        bad_ref = ref_for(bad, PRIOR)
        bad_p = create_package(PRIOR, evidence_refs=[bad_ref])
        bad_body = prep(bad_p)
        bad_body["evidenceArtifacts"] = {bad_ref["digest"]: bad}
        res_bad = adapter.execute(bad_body)
        obs = dict(
            wrongEngineStatus=res_bad["status"],
            wrongEngineInputEvidence=res_bad["inputEvidence"][0]["status"],
            wrongEngineNoRevision=no_authority(res_bad),
            wrongEngineOriginalPreserved=res_bad["originalPackage"] == bad_p,
        )
        obs["pass"] = (
            obs["wrongEngineStatus"] in ("STALE", "INVALID_INPUT")
            and obs["wrongEngineNoRevision"]
            and obs["wrongEngineOriginalPreserved"]
        )
        return obs

    def c7_authority_metadata():
        body = prep()
        obs = {}
        for field, value in (
            ("transactionAuthority", True),
            ("approveAndPublish", True),
            ("signer", "auto"),
            ("permissions", ["SIGN", "SPEND"]),
        ):
            b = copy.deepcopy(body)
            b[field] = value
            out = safe_call(lambda bb=b: adapter.execute(bb))
            obs[field] = dict(rejected=not out["ok"], code=out.get("code"))
        # Inject transaction authority into workflow step metadata.
        b = copy.deepcopy(body)
        b["workflow"]["steps"][0]["transactionAuthority"] = True
        out = safe_call(lambda bb=b: adapter.execute(bb))
        obs["stepAuthority"] = dict(rejected=not out["ok"], code=out.get("code"))
        obs["pass"] = all(v["rejected"] for v in obs.values())
        return obs

    def c8_cancel_race():
        body = prep()
        stopped = threading.Event()
        orig = adapter.create_package

        def after_hash(*a, **k):
            v = orig(*a, **k)
            stopped.set()
            return v

        adapter.create_package = after_hash
        try:
            res = adapter.execute(body, cancelled=stopped.is_set)
        finally:
            adapter.create_package = orig
        obs = dict(
            status=res["status"],
            noRevision=no_authority(res),
            originalPreserved=res["originalPackage"] == body["package"],
        )
        obs["pass"] = (
            obs["status"] == "CANCELLED" and obs["noRevision"] and obs["originalPreserved"]
        )
        return obs

    def c9_budget_reset():
        body = prep()
        body["workflow"]["budget"]["maxIterations"] = 1
        res = adapter.execute(body)
        obs = dict(
            status=res["status"],
            iterations=res["receipt"]["usage"]["iterations"],
            noRevision=no_authority(res),
            originalPreserved=res["originalPackage"] == body["package"],
        )
        obs["pass"] = (
            obs["status"] == "BUDGET_EXHAUSTED"
            and obs["iterations"] == 1
            and obs["noRevision"]
            and obs["originalPreserved"]
        )
        return obs

    def c10_forged_current():
        raw = copy.deepcopy(PRIOR)
        # Attacker sets freshness to CURRENT to try to promote a historical claim.
        for imp in raw["imports"]:
            imp["integrity"]["freshness"] = "CURRENT"
        p = create_package(raw, tests=named_vectors())
        body = prep(p, action="inspect")
        body["workflow"]["steps"] = [dict(id="fresh", op="revalidate")]
        res = adapter.execute(body)
        # Even with forged CURRENT metadata, no proof promotion or revision.
        obs = dict(
            status=res["status"],
            noRevision=no_authority(res),
            originalPreserved=res["originalPackage"] == body["package"],
            exportFreshnessHistorical=all(
                e["output"]
                .get("comparison", {})
                .get("report", {})
                .get("integrity", {})
                .get("freshness")
                != "CURRENT"
                for e in res["receipt"]["logs"]
                if e["output"] and e["op"] == "export"
            ),
        )
        obs["pass"] = obs["noRevision"] and obs["originalPreserved"]
        return obs

    for cid, name, fn in (
        ("C01", "forged VERIFIED_CORRECTION", c1_forged_correction),
        ("C02", "altered original package hash", c2_altered_package_hash),
        ("C03", "forged parent revision", c3_forged_parent),
        ("C04", "project mutation during active request", c4_project_mutation),
        ("C05", "reused correction ID", c5_reused_correction),
        ("C06", "foreign evidence reference / forged engine", c6_foreign_evidence_reference),
        ("C07", "metadata containing transaction authority", c7_authority_metadata),
        ("C08", "cancellation racing revision creation", c8_cancel_race),
        ("C09", "budget reset between adapter/controller", c9_budget_reset),
        ("C10", "forged CURRENT freshness", c10_forged_current),
    ):
        rows.append(run_check(cid, name, fn))

    # Interface parity (core / CLI / API) with independent hash equality.
    def parity():
        body = prep()
        body_b = canonical_bytes(body)
        tmp = ROOT / ".test-tmp" / "m45-final-review"
        tmp.mkdir(parents=True, exist_ok=True)
        req = tmp / "request.json"
        req.write_bytes(body_b)
        os.environ["FLIP_LOCAL_SOLVER"] = "1"
        outp = tmp / "result.json"
        if outp.exists():  # CLI intentionally refuses to overwrite; start clean
            outp.unlink()
        code = cli_main(["agent-portable", "--request", str(req), "--out", str(outp)])
        cli = json.loads(outp.read_bytes())
        client = TestClient(app, client=("127.0.0.1", 1))
        resp = client.post("/api/agent/v1/portable", json=body)
        api = resp.json()
        core = adapter.execute(body)
        obs = dict(
            cliExit=code,
            apiStatus=resp.status_code,
            reproductionParity=(
                cli["reproductionHash"] == api["reproductionHash"] == core["reproductionHash"]
            ),
            resultHashIndependently=(
                ihash({k: v for k, v in core.items() if k != "resultHash"}) == core["resultHash"]
            ),
        )
        obs["pass"] = (
            obs["cliExit"] == 0
            and obs["apiStatus"] == 200
            and obs["reproductionParity"]
            and obs["resultHashIndependently"]
        )
        return obs

    rows.append(run_check("P01", "core/CLI/API parity + independent resultHash", parity))

    record = dict(
        artifactType="M45_AGENT_PORTABLE_FINAL_REVIEW_INDEPENDENT_CHECKS",
        testedSha=TESTED_SHA,
        rows=rows,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    failures = [r["id"] for r in rows if not r["pass"]]
    print(
        json.dumps(
            {"total": len(rows), "passed": len(rows) - len(failures), "failures": failures},
            indent=2,
        )
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
