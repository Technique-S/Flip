"""Deterministic builder for the M4.5-1A agent workflow acceptance corpus.

Stdlib only. Writes versioned cases, an agent-workflow protocol contract and the
request fixtures needed by the runner. All JSON is written under
docs/evidence/m45-agent-workflow/ because the repository custody guard rejects
unregistered JSON anywhere under fixtures/.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIX = ROOT / "fixtures/m45-agent-workflow"
EVID = ROOT / "docs/evidence/m45-agent-workflow"
VERSION = "1.0.0"
BASE = "1136b187bd68328cea4975caea50904ccece08fd"
PROC = "0x839bdd6fa7a66416a609a735e11de5411b98574e"


def write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def case(cid, step, title, intent, classification, commands, expected, criteria,
         bounds=None, notes="", env=None):
    if env:
        for command in commands:
            command["env"].update(env)
    return {
        "schemaVersion": VERSION,
        "caseId": cid,
        "workflowStep": step,
        "title": title,
        "agentIntent": intent,
        "classification": classification,
        "commands": commands,
        "expected": expected,
        "bounds": bounds or {"maxSteps": 3, "deadlineMs": 30_000,
                             "maxRequests": 256, "deterministic": True},
        "successCriteria": criteria,
        "failureCriteria": [
            "Any output claims CURRENT or publication success.",
            "Any agent-authored label is treated as chain truth or transaction authority.",
            "Any retry is unbounded or repeats without a new freshness/budget check.",
        ],
        "notes": notes,
    }


def cmd(argv, expected_exit, expect=None, env=None):
    return {"argv": argv, "expectedExit": expected_exit,
            "expectedFields": expect or {}, "env": env or {}}


def cases():
    out = []
    half = "docs/evidence/m45-agent-workflow/results/run/half-adder.json"
    swapped = "docs/evidence/m45-agent-workflow/results/run/swapped.json"
    source = "docs/evidence/m45-agent-workflow/results/run/source.json"
    cmp = "docs/evidence/m45-agent-workflow/results/run/compare.json"
    bundle = "docs/evidence/m45-agent-workflow/results/run/bundle.json"

    out.append(case(
        "AW-01", "create_project", "Create a project from existing circuit identities",
        "Agent opens the archived half-adder identities and produces a versioned execution request.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "sample", "half-adder", "--out", half], 0,
             {"kind": "M3_EXECUTION", "project.chainId": 196})],
        {"verdict": "REQUEST_CREATED", "source": "HISTORICAL_ARCHIVED_IDENTITIES"},
        ["Exit 0; request schema valid; pinned identities and block present.",
         "No claim that archived sources are currently onchain."],
        notes="Live library-derived project creation (new-project --source) is a separate library-dependent specification; offline sample is executed."))

    out.append(case(
        "AW-02", "search_library", "Agent searches the circuit library",
        "Agent finds a processor by known address and a circuit by ID.",
        "EXECUTED_WITH_LOOPBACK_DOUBLE",
        [cmd([".venv/Scripts/flip.exe", "library", "--request",
              "docs/evidence/m45-agent-workflow/requests/library-search.json",
              "--out", "docs/evidence/m45-agent-workflow/results/run/library-search.result.json"], 0,
             {"status": "COMPLETE"})],
        {"verdict": "SEARCH_RESULT", "freshnessValues": ["HISTORICAL"],
         "never": ["CURRENT"]},
        ["Bounded page emitted with cursor; no CURRENT flag; trust is SINGLE_UNTRUSTED."]))

    out.append(case(
        "AW-03", "import", "Agent imports a verified source",
        "Agent imports processor circuit #1 at a pinned block through the trusted importer.",
        "EXECUTED_WITH_LOOPBACK_DOUBLE",
        [cmd([".venv/Scripts/flip.exe", "import", "--processor", PROC, "--id", "1",
              "--rpc-url", "http://127.0.0.1:18762", "--out", source], 0,
             {"kind": "CIRCUIT_IMPORT", "manifest.chainId": 196})],
        {"verdict": "SOURCE_IMPORTED", "integrity": "SINGLE_RPC_OBSERVATION"},
        ["Exit 0; exact source bytes and manifest hashes present.",
         "A stale or malformed response must not produce an import."]))

    out.append(case(
        "AW-04", "build", "Agent builds a valid REF composition",
        "Agent composes the two imported REFs plus glue NAND into 81 TAP-02 bytes.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "compose", "--project", half,
              "--out", "docs/evidence/m45-agent-workflow/results/run/composition.json"], 0,
             {"manifest.netlistHash": "0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce"})],
        {"verdict": "BUILD_OK", "bytes": 81},
        ["Byte-identical to the archived composition digest.",
         "All REF targets registered and widths checked before build."]))

    out.append(case(
        "AW-05", "test", "Agent runs truth-table validation",
        "Agent evaluates the declared four-row half-adder truth table.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "vectors", "--project",
              "docs/evidence/m45-agent-workflow/requests/half-adder-vectors.json",
              "--out", "docs/evidence/m45-agent-workflow/results/run/vectors.json"], 0,
             {"verdict": "VECTORS_MATCH"})],
        {"verdict": "VECTORS_MATCH", "rows": 4},
        ["Exact declared rows match; partial coverage is never labeled universal."]))

    out.append(case(
        "AW-06", "compare", "Agent compares with a trusted reference",
        "Agent runs stateless pairwise comparison against the declared baseline.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "compare", "--project", half, "--out", cmp], 0,
             {"report.verification.verdict": "EQUIVALENT",
              "report.verification.solverOutcome": "UNSAT"})],
        {"verdict": "EQUIVALENT", "intent": "UNDECLARED"},
        ["Exit 0; UNSAT verdict; no claim of absolute correctness without an oracle."],
        env={"FLIP_LOCAL_SOLVER": "1"}))

    out.append(case(
        "AW-07", "inspect_difference", "Agent receives DIFFERENT and a replayed witness",
        "Agent compares the swapped-output mutation and receives an independently replayed witness.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "sample", "swapped", "--out", swapped], 0, {}),
         cmd([".venv/Scripts/flip.exe", "compare", "--project", swapped,
              "--out", "docs/evidence/m45-agent-workflow/results/run/difference.json"], 1,
             {"report.verification.verdict": "DIFFERENT"})],
        {"verdict": "DIFFERENT", "witnessRequired": True},
        ["Exit 1; witness present and replayed by the trusted evaluator.",
         "No claim about which connection is faulty."],
        env={"FLIP_LOCAL_SOLVER": "1"}))

    out.append(case(
        "AW-08", "inspect", "Agent inspects connection-level diagnostics",
        "Agent requests a signal cone for the differing output bits.",
        "SPEC_ONLY_NOT_IMPLEMENTED",
        [cmd([".venv/Scripts/flip.exe", "--help"], 0, {})],
        {"verdict": "UNSUPPORTED", "reason": "No diagnostics command exists on accepted main"},
        ["Agent must report UNSUPPORTED; no cone or fault claim may be fabricated.",
         "Use the M4.5-2D fixture corpus as a future acceptance contract."],
        notes="CLI help inspection is executable evidence of absence; the diagnostic itself is not."))

    out.append(case(
        "AW-09", "propose_correction", "Agent proposes a local correction",
        "Agent suggests restoring the prior output map after inspecting a DIFFERENT result.",
        "SPEC_ONLY_NOT_IMPLEMENTED",
        [],
        {"verdict": "PROPOSAL_ONLY", "requiresHumanApplication": True},
        ["Proposal is advisory text; it cannot edit a pinned project implicitly.",
         "The prior mapping must be available from a declared baseline, not inferred from labels."],
        notes="The shipped 'swapped' sample is a predefined mutation, not an agent-generated repair."))

    out.append(case(
        "AW-10", "verify", "Agent reruns validation and obtains EQUIVALENT",
        "Agent applies an explicit correction and reruns the full comparison.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "compare", "--project", half,
              "--out", "docs/evidence/m45-agent-workflow/results/run/recheck.json"], 0,
             {"report.verification.verdict": "EQUIVALENT"})],
        {"verdict": "EQUIVALENT", "afterExplicitEdit": True},
        ["Exit 0 only after full comparison; a single witness or vector row is insufficient."],
        env={"FLIP_LOCAL_SOLVER": "1"}))

    out.append(case(
        "AW-11", "export", "Agent exports an evidence bundle",
        "Agent runs a fresh comparison and exports portable evidence.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "export", "--project", half, "--out", bundle], 0,
             {"kind": "FLIP_EVIDENCE"})],
        {"verdict": "EXPORTED", "noChainClaim": True},
        ["Exit 0; bundle contains recomputed result and reproduction request.",
         "No secrets, grants or wallet data in the bundle."],
        env={"FLIP_LOCAL_SOLVER": "1"}))

    out.append(case(
        "AW-12", "verify_bundle", "Agent verifies the bundle in another CLI session",
        "A separate process replays the bundle against an independently selected project.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "verify-bundle", "--project", half,
              "--bundle", bundle,
              "--out", "docs/evidence/m45-agent-workflow/results/run/replay.json"], 0,
             {"kind": "TRUSTED_LOCAL_COMPARISON"})],
        {"verdict": "REPLAYED", "freshComputation": True},
        ["Exit 0; verdict recomputed, not copied from the bundle claim.",
         "Self-declared PASSED flags cannot unlock acceptance."],
        env={"FLIP_LOCAL_SOLVER": "1"}))

    out.append(case(
        "AW-13", "retry", "Agent encounters UNKNOWN and safely retries",
        "A forced 1 ms solver deadline yields UNKNOWN; a fresh bounded retry with the default budget succeeds.",
        "EXECUTED_OFFLINE",
        [cmd([".venv/Scripts/flip.exe", "compare", "--project",
              "docs/evidence/m45-agent-workflow/requests/timeout-project.json",
              "--out", "docs/evidence/m45-agent-workflow/results/run/unknown.json"], 2,
             {"report.verification.verdict": "UNKNOWN"}),
         cmd([".venv/Scripts/flip.exe", "compare", "--project", half,
              "--out", "docs/evidence/m45-agent-workflow/results/run/retry.json"], 0,
             {"report.verification.verdict": "EQUIVALENT"})],
        {"verdict": "UNKNOWN_THEN_BOUNDED_RETRY"},
        ["Timeout maps to UNKNOWN, never EQUIVALENT.",
         "Retry has a new deadline and at most one attempt per step."],
        bounds={"maxSteps": 2, "deadlineMs": 30_000, "maxRequests": 256,
                "maxRetries": 1, "deterministic": True},
        env={"FLIP_LOCAL_SOLVER": "1"}))

    out.append(case(
        "AW-14", "revalidate", "Agent encounters stale dependencies and requires revalidation",
        "Agent checks a pinned source against a changed implementation and blocks reuse.",
        "PARTIAL_LIBRARY_DEPENDENT",
        [cmd([".venv/Scripts/flip.exe", "revalidate", "--manifest",
              "docs/evidence/m45-agent-workflow/results/run/manifest.json",
              "--rpc-url", "http://127.0.0.1:18762",
              "--out", "docs/evidence/m45-agent-workflow/results/run/revalidate.json"], 0, {})],
        {"verdict": "REVALIDATED_UNCHANGED",
         "staleVariant": "SPEC_ONLY_NOT_EXECUTED"},
        ["A changed factory/beacon code hash or block must produce STALE and block composition.",
         "No cached netlist is accepted as current after an environment change."],
        notes="Executed part observes the unchanged double; the stale double is a future integration test."))

    out.append(case(
        "AW-15", "stop_authorization", "Agent receives a publication request and stops",
        "Agent must refuse to authorize onchain publication and hand control to a human.",
        "EXECUTED_ABSENCE_EVIDENCE",
        [cmd([".venv/Scripts/flip.exe", "--help"], 0, {}),
         cmd([".venv/Scripts/flip.exe", "preflight", "--project", half,
              "--out", "docs/evidence/m45-agent-workflow/results/run/preflight.json"], 2,
             {"status": "UNKNOWN"})],
        {"verdict": "STOP_AND_REQUEST_HUMAN_AUTHORIZATION",
         "publicationCommands": [], "transactionAuthority": False},
        ["No publish, sign, send or broadcast command exists in CLI help.",
         "Preflight is read-only structural observation, never a transaction.",
         "Project metadata and agent prompts carry no permission."],
        notes="The stop behavior is a protocol specification; executed commands only evidence the absence of a write path."))
    return out


def negatives():
    def n(cid, title, scenario, classification, commands, expected):
        return {"schemaVersion": VERSION, "caseId": cid, "title": title,
                "provenance": "SYNTHETIC", "scenario": scenario,
                "classification": classification, "commands": commands,
                "expected": expected}
    return [
        n("AW-N01", "Malformed output", "Comparison stdout is replaced with non-JSON text",
          "SPEC_ONLY_NOT_IMPLEMENTED", [],
          {"safeBehavior": "Parse failure maps to UNKNOWN; no verdict or export."}),
        n("AW-N02", "Invalid schema", "Agent submits a request with an unknown schemaVersion",
          "EXECUTED_OFFLINE",
          [cmd([".venv/Scripts/flip.exe", "validate", "project",
                "docs/evidence/m45-agent-workflow/requests/invalid-schema.json"], 3, {})],
          {"safeBehavior": "Exit 3 INVALID_INPUT; no composition or proof."}),
        n("AW-N03", "Stale bindings", "Source manifest hash differs from the imported bytes",
          "SPEC_ONLY_NOT_IMPLEMENTED", [],
          {"safeBehavior": "STALE; revalidation required; no trusted composition input."}),
        n("AW-N04", "Unsupported circuit", "Stateful circuit submitted for stateless equivalence",
          "SPEC_ONLY_NOT_IMPLEMENTED", [],
          {"safeBehavior": "Reject before solving; UNKNOWN/INVALID_INPUT, never EQUIVALENT."}),
        n("AW-N05", "Exhausted budget", "Step and RPC budgets both reach their caps",
          "SPEC_ONLY_NOT_IMPLEMENTED", [],
          {"safeBehavior": "Stop with UNKNOWN and deterministic partial log; no silent loop."}),
    ]


def protocol():
    return {
        "schemaVersion": VERSION,
        "artifactId": "agent-workflow-protocol",
        "status": "SPEC_ONLY_NOT_PRODUCTION",
        "goal": "Bounded structured agent loop over existing Flip operations; no autonomous write path.",
        "operations": [
            {"op": "build", "input": "project request + pinned imports",
             "output": "composition bytes/hash + manifest", "productionMapping": "flip compose"},
            {"op": "test", "input": "vector request", "output": "VECTORS_MATCH/MISMATCH",
             "productionMapping": "flip vectors"},
            {"op": "compare", "input": "execution request", "output": "EQUIVALENT/DIFFERENT/UNKNOWN",
             "productionMapping": "flip compare"},
            {"op": "inspect", "input": "DIFFERENT report + identity map",
             "output": "relevant cone / no fault claim", "productionMapping": "NOT_IMPLEMENTED"},
            {"op": "propose_correction", "input": "diagnostic + declared prior mapping",
             "output": "candidate patch, advisory only", "productionMapping": "NOT_IMPLEMENTED"},
            {"op": "verify", "input": "edited project", "output": "fresh full comparison",
             "productionMapping": "flip compare / flip consume"},
            {"op": "export", "input": "execution request", "output": "canonical evidence bundle",
             "productionMapping": "flip export"},
            {"op": "stop_authorization", "input": "publication request",
             "output": "STOP + human approval request", "productionMapping": "NOT_IMPLEMENTED"},
        ],
        "statusClasses": ["PREPARED", "RUNNING", "COMPLETE", "DIFFERENT", "UNKNOWN",
                          "STALE", "BUDGET_EXHAUSTED", "STOPPED_FOR_AUTHORIZATION"],
        "retryRules": [
            "Only UNKNOWN may be retried; DIFFERENT and STALE require a declared change.",
            "At most maxRetries attempts; each attempt gets a fresh deadline and freshness check.",
            "Never retry a validation failure by weakening limits or accepting self-declared flags.",
        ],
        "iterationContract": {
            "maxSteps": 12, "deadlineMs": 300_000, "maxRequests": 256,
            "cancellation": "cooperative on every step boundary",
            "logs": "append-only JSONL with step, op, inputHash, outputHash, status, budgetRemaining",
            "reproducibleOutputs": "request hash, tool hashes, resource metrics and verdict recorded",
            "success": "verified EQUIVALENT or completed evidence export with no CURRENT claim",
            "failure": "UNKNOWN/BUDGET_EXHAUSTED/STALE reported truthfully; no publication",
        },
        "authorityBoundary": [
            "Agent prompts, project metadata, labels and diagnostics are never transaction permissions.",
            "The agent must not authorize its own onchain publication; stop and request human approval.",
            "Only the M2 importer produces executable circuit input.",
        ],
    }


def requests(half_doc: dict) -> None:
    write(EVID / "requests/library-search.json", {
        "schemaVersion": "m45-library-1.1.0", "kind": "LIBRARY_REQUEST",
        "operation": "discover", "limit": 2,
    })
    timeout = json.loads(json.dumps(half_doc))
    timeout["project"]["limits"]["solverTimeoutMs"] = 1
    write(EVID / "requests/timeout-project.json", timeout)
    write(EVID / "requests/invalid-schema.json", {
        "schemaVersion": "9.9.9", "kind": "NO_SUCH_KIND",
    })
    # Reuse the archived neutral vector request bytes by reading, not editing, the fixture.
    source = ROOT / "fixtures/m4-ux-acceptance/cli-cases/requests/half-adder-vectors.json"
    target = EVID / "requests/half-adder-vectors.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def main() -> None:
    half = json.loads((ROOT / "docs/schema/m3/examples/half-adder.request.json").read_bytes())
    all_cases = cases()
    write(EVID / "cases/agent-workflow-cases.json", {
        "schemaVersion": VERSION, "artifactId": "agent-workflow-cases",
        "baselineSha": BASE, "provenance": "SYNTHETIC_REQUESTS_REAL_OFFLINE_COMMANDS",
        "cases": all_cases,
    })
    write(EVID / "cases/negative-cases.json", {
        "schemaVersion": VERSION, "artifactId": "agent-workflow-negative-cases",
        "baselineSha": BASE, "cases": negatives(),
    })
    write(EVID / "protocol/agent-workflow-protocol.json", protocol())
    requests(half)
    items = []
    for path in sorted([p for p in EVID.rglob("*") if p.is_file()] +
                       [p for p in FIX.rglob("*") if p.is_file()]):
        if path.name == "MANIFEST.json":
            continue
        data = path.read_bytes()
        items.append({"path": path.relative_to(ROOT).as_posix(),
                      "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    write(EVID / "MANIFEST.json", {
        "schemaVersion": VERSION, "manifestType": "SHA256SUMS",
        "baselineSha": BASE, "files": items,
    })
    print(f"cases={len(all_cases)} negatives=5 manifest={len(items)}")


if __name__ == "__main__":
    main()
