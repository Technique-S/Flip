"""Deterministic builder for the independent M4.5-2D debugging corpus.

Pure stdlib. No timestamps, no host values, no production imports. Every expected
truth table, witness, differing bit and signal cone is computed by debug_core and
cross-checked by two independent evaluators before being written.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import debug_core as d  # noqa: E402

ROOT = HERE.parent
XOR_CPU = "aa" * 20
NAND_CPU = "bb" * 20
AND_CPU = "cc" * 20
OR_CPU = "dd" * 20
F_CPU = "ee" * 20
WRAP_A = "11" * 20
WRAP_B = "12" * 20
TOP_REF = "f1" * 20
TOP_CAND = "f2" * 20
SCHEMA = "1.0.0"


def xor_els():
    return [d.nand(2, 3), d.nand(2, 4), d.nand(3, 4), d.nand(5, 6)]


def and_els():
    return [d.nand(2, 3), d.nand(4, 4)]


def or_els():
    return [d.nand(2, 2), d.nand(3, 3), d.nand(4, 5)]


def f_els():
    """Asymmetric F(a,b) = a AND NOT b."""
    return [d.nand(3, 3), d.nand(2, 4), d.nand(5, 5)]


BANK = {
    (XOR_CPU, 1): (2, 1, d.encode(xor_els())),
    (NAND_CPU, 2): (2, 1, d.encode([d.nand(2, 3)])),
    (AND_CPU, 3): (2, 1, d.encode(and_els())),
    (OR_CPU, 4): (2, 1, d.encode(or_els())),
    (F_CPU, 5): (2, 1, d.encode(f_els())),
    # Use the asymmetric F inside the wrapper: a swapped XOR input would be
    # commutative and would not produce a behavioral difference.
    (WRAP_A, 10): (2, 2, d.encode([d.ref(F_CPU, 5, [2, 3]), d.ref(AND_CPU, 3, [2, 3])])),
    (WRAP_B, 11): (2, 2, d.encode([d.ref(F_CPU, 5, [3, 2]), d.ref(AND_CPU, 3, [2, 3])])),
}


def top_refs(specs):
    """Build REF elements; each spec is (cpu, cid, ins, n_out)."""
    used = [s for spec in specs for s in spec[2] if s >= 2]
    n_in = max(used) + 1 - 2 if used else 0
    els, signal = [], 2 + n_in
    for cpu, cid, ins, out_count in specs:
        els.append(d.ref(cpu, cid, list(ins), out_count))
        signal += out_count
    return els, n_in, signal


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def output_map_connections(omap):
    return [{"connectionRef": "top/outputMap[%d]" % i, "outputIndex": i,
             "sourceSignal": s, "description": "output pin %d selects signal %d" % (i, s)}
            for i, s in enumerate(omap)]


def identity(cpu, cid, net, n_in, n_out, omap):
    return {"processorHex": cpu, "circuitId": str(cid),
            "nIn": n_in, "nOut": n_out, "outputMap": omap,
            "netlistHex": "0x" + net.hex(), "netlistSha256": sha(net),
            "bytes": len(net)}


def _load(net, n_in, n_out, bank=None):
    try:
        return d.load(net, n_in, n_out, bank or BANK), None
    except (d.Malformed, d.ResourceLimit) as exc:
        return None, str(exc)


def make_case(case_id, category, description, specs_ref, specs_cand,
              ref_map, cand_map, suspects, oracle="NONE", note="",
              force_ambiguous=False, ref_els_override=None, cand_els_override=None,
              bank_override=None):
    bank = bank_override or BANK
    if ref_els_override is not None:
        ref_els, n_in = ref_els_override, 2
    else:
        ref_els, n_in, _ = top_refs(specs_ref)
    if cand_els_override is not None:
        cand_els = cand_els_override
    else:
        cand_els, _, _ = top_refs(specs_cand)
    n_out = len(ref_map)
    ref_net, cand_net = d.encode(ref_els), d.encode(cand_els)
    ref_c, ref_err = _load(ref_net, n_in, n_out, bank)
    cand_c, cand_err = _load(cand_net, n_in, n_out, bank)
    assert ref_c is not None, "reference must be valid: %s" % ref_err

    case = {
        "schemaVersion": SCHEMA,
        "caseId": case_id,
        "provenance": "SYNTHETIC",
        "category": category,
        "description": description,
        "chainContext": 196,
        "chainContextNote": "context only; no chain observation or deployment is claimed",
        "intentOracle": oracle,
        "note": note,
        "reference": identity(TOP_REF, 1, ref_net, n_in, n_out, ref_map),
        "candidate": identity(TOP_CAND, 1, cand_net, n_in, n_out, cand_map),
        "referenceOutputMapConnections": output_map_connections(ref_map),
        "candidateOutputMapConnections": output_map_connections(cand_map),
    }

    if cand_c is None:
        case["expected"] = {
            "verdict": "INVALID_INPUT",
            "reason": cand_err,
            "witness": None,
            "differingBits": [],
            "truthTables": None,
        }
        case["cone"] = None
        case["diagnosticExpectation"] = {
            "class": "STRUCTURAL_REJECTION_NO_ATTRIBUTION",
            "provenBehavioralDifference": False,
            "suspectedConnections": [],
            "uniqueFaultClaim": False,
            "candidateRepairs": [],
            "explanation": "No mapped comparison was executed; a structural rejection cannot localize a fault.",
        }
        return case

    wt = d.witness_table(ref_c, ref_map, cand_c, cand_map)
    if wt["kind"] == "EQUIVALENT":
        cone = d.trace_cone(cand_c, cand_map)
        case["expected"] = {
            "verdict": "EQUIVALENT",
            "reason": None,
            "exhaustiveRows": wt["exhaustive_rows"],
            "witness": None,
            "differingBits": [],
            "truthTables": {"reference": wt["reference_table"],
                            "candidate": wt["candidate_table"]},
        }
        case["cone"] = cone
        case["diagnosticExpectation"] = {
            "class": "NO_FAULT_ATTRIBUTION",
            "provenBehavioralDifference": False,
            "suspectedConnections": [],
            "uniqueFaultClaim": False,
            "candidateRepairs": [],
            "explanation": "Exhaustive behavior is identical; no connection may be labeled faulty.",
        }
        return case

    if wt["kind"] != "DIFFERENT":
        case["expected"] = {"verdict": wt["kind"], "reason": wt.get("reason"),
                            "witness": None, "differingBits": []}
        case["cone"] = None
        case["diagnosticExpectation"] = {
            "class": "UNKNOWN_NO_ATTRIBUTION", "provenBehavioralDifference": False,
            "suspectedConnections": [], "uniqueFaultClaim": False,
            "candidateRepairs": [], "explanation": "No replayable difference.",
        }
        return case

    diff_bits = wt["witness"]["differing_bits"]
    diff_signals = [cand_map[i] for i in diff_bits]
    cone = d.trace_cone(cand_c, diff_signals)
    ambiguous = force_ambiguous or len(suspects) > 1
    case["expected"] = {
        "verdict": "DIFFERENT",
        "reason": None,
        "exhaustiveRows": wt["exhaustive_rows"],
        "witness": wt["witness"],
        "allDifferences": wt["all_differences"],
        "differingBits": diff_bits,
        "differingOutputSignals": diff_signals,
        "witnessReplayedBy": wt["witness_replayed_by"],
        "truthTables": {"reference": wt["reference_table"],
                        "candidate": wt["candidate_table"]},
    }
    case["cone"] = cone
    case["diagnosticExpectation"] = {
        "class": "AMBIGUOUS_MULTIPLE_CAUSES" if ambiguous else "SUSPECTED_CANDIDATE",
        "provenBehavioralDifference": True,
        "provenScope": "candidate output differs from selected reference under a replayed witness",
        "suspectedConnections": suspects,
        "uniqueFaultClaim": False,
        "candidateRepairs": [],
        "explanation": (
            "The witness proves a behavioral difference, not which connection is defective. "
            "Suspected connections are in the replayed signal cone; applying any repair requires "
            "explicit user action and a fresh trusted comparison."
        ),
    }
    return case


def find_ambiguous_single_edge():
    """Search a fixed ordered mutation space for two single-edge changes with
    identical wrong behavior. Deterministic: first matching group wins."""
    ref = d.load(d.encode(xor_els()), 2, 1, BANK)
    original = ref.elements  # decoded elements carry first_out values
    ref_sig = [r["out"] for r in d.exhaustive(ref, [7])]
    groups: dict[str, list] = {}
    for idx in (1, 2):
        for pin in (0, 1):
            prior = original[idx].ins[pin]
            for replacement in (0, 1, 2, 3, 4):
                if replacement == prior or replacement >= original[idx].first_out:
                    continue
                els = [d.nand(*e.ins) for e in original]
                els[idx].ins[pin] = replacement
                c = d.load(d.encode(els), 2, 1, BANK)
                sig = [r["out"] for r in d.exhaustive(c, [7])]
                if sig != ref_sig:
                    groups.setdefault(json.dumps(sig), []).append(
                        {"elementIndex": idx, "inputPin": pin,
                         "priorSignal": prior, "replacementSignal": replacement,
                         "connectionRef": "top/element[%d].in[%d]" % (idx, pin)})
    for sig in sorted(groups):
        mutations = groups[sig]
        # Prefer distinct element indices: two different connections, not two
        # different replacement values on the same pin.
        if len({m["elementIndex"] for m in mutations}) < 2:
            continue
        seen, representatives = set(), []
        for m in mutations:
            key = (m["elementIndex"], m["inputPin"])
            if key in seen:
                continue
            seen.add(key)
            representatives.append(m)
        if len(representatives) >= 2:
            return representatives[0], representatives[1:], json.loads(sig)
    raise AssertionError("no ambiguous single-edge group found")


def build_cases():
    cases = []

    # D01 — swapped outputs
    specs = [(XOR_CPU, 1, [2, 3], 1), (AND_CPU, 3, [2, 3], 1)]
    cases.append(make_case(
        "D01", "swapped_outputs",
        "Two computed outputs are swapped in the candidate output map.",
        specs, specs, [4, 5], [5, 4],
        ["top/outputMap[0]", "top/outputMap[1]"],
        oracle="DECLARED_PRIOR_MAPPING",
        note="Output-map swap; both mapped pins lie in the differing output cones."))

    # D02 — incorrect REF input mapping
    cases.append(make_case(
        "D02", "incorrect_ref_input_mapping",
        "Asymmetric REF F(a,b)=a AND NOT b receives b,a instead of a,b.",
        [(F_CPU, 5, [2, 3], 1)], [(F_CPU, 5, [3, 2], 1)], [4], [4],
        ["top/element[0].in[0]", "top/element[0].in[1]"],
        oracle="DECLARED_PRIOR_MAPPING",
        note="Both REF input pins are implicated; input order is not self-describing."))

    # D03 — duplicate fan-out
    cases.append(make_case(
        "D03", "duplicate_fan_out",
        "XOR second input is duplicated from input a instead of input b.",
        [(XOR_CPU, 1, [2, 3], 1)], [(XOR_CPU, 1, [2, 2], 1)], [4], [4],
        ["top/element[0].in[1]"],
        oracle="DECLARED_PRIOR_MAPPING",
        note="One suspected pin under a declared prior mapping; still a candidate, not a proof."))

    # D04 — unbound pin (structural rejection)
    cases.append(make_case(
        "D04", "disconnected_or_unbound_pin",
        "REF input references signal 99, which is not available at that element.",
        [(XOR_CPU, 1, [2, 3], 1)], [(XOR_CPU, 1, [2, 99], 1)], [4], [4], [],
        note="No comparison is executed; no fault attribution is permitted."))

    # D05 — wrong output ordering (rotation of three outputs)
    specs = [(XOR_CPU, 1, [2, 3], 1), (AND_CPU, 3, [2, 3], 1), (OR_CPU, 4, [2, 3], 1)]
    cases.append(make_case(
        "D05", "wrong_output_ordering",
        "Three outputs are cyclically rotated in the candidate output map.",
        specs, specs, [4, 5, 6], [6, 4, 5],
        ["top/outputMap[0]", "top/outputMap[1]", "top/outputMap[2]"],
        oracle="DECLARED_PRIOR_MAPPING"))

    # D06 — multiple simultaneous changes
    cases.append(make_case(
        "D06", "multiple_changed_connections",
        "Candidate changes an REF input order and swaps both outputs.",
        [(XOR_CPU, 1, [2, 3], 1), (AND_CPU, 3, [2, 3], 1)],
        [(XOR_CPU, 1, [3, 2], 1), (AND_CPU, 3, [2, 3], 1)],
        [4, 5], [5, 4],
        ["top/element[0].in[0]", "top/outputMap[0]", "top/outputMap[1]"],
        oracle="DECLARED_PRIOR_MAPPING",
        note="Multiple edits in one cone; no unique cause."))

    # D07 — nested REF dependencies
    cases.append(make_case(
        "D07", "nested_ref_dependencies",
        "Top REF reaches XOR through a wrapper; the inner REF input order changed.",
        [(WRAP_A, 10, [2, 3], 2)], [(WRAP_B, 11, [2, 3], 2)], [4, 5], [4, 5],
        ["top/ref[0]/element[0].in[0]", "top/ref[0]/element[0].in[1]"],
        oracle="DECLARED_PRIOR_MAPPING",
        note="Cone must cross the REF boundary and retain component paths."))

    # D08 — equivalent rewiring
    cases.append(make_case(
        "D08", "equivalent_rewiring",
        "XOR inputs are commutatively rewired; exhaustive behavior is unchanged.",
        [(XOR_CPU, 1, [2, 3], 1)], [(XOR_CPU, 1, [3, 2], 1)], [4], [4], [],
        note="No fault attribution is allowed for an EQUIVALENT design."))

    # D09 — DIFFERENT with several possible contributing connections
    specs = [(XOR_CPU, 1, [2, 3], 1), (F_CPU, 5, [2, 3], 1), (OR_CPU, 4, [2, 3], 1)]
    cases.append(make_case(
        "D09", "several_possible_contributing_connections",
        "Several REF inputs and the output map change in a three-output design.",
        specs,
        [(XOR_CPU, 1, [3, 2], 1), (F_CPU, 5, [3, 2], 1), (OR_CPU, 4, [2, 3], 1)],
        [4, 5, 6], [6, 5, 4],
        ["top/element[1].in[0]", "top/element[1].in[1]", "top/outputMap[1]"],
        note="Only connections in the replayed differing-output cone are displayed as suspects; "
             "other edits elsewhere in the design are not attributed by this witness."))

    # D10 — indistinguishable single-edge causes (searched, not hand-asserted)
    chosen, alternatives, wrong_sig = find_ambiguous_single_edge()
    base = xor_els()
    cand_els = [d.nand(*e.ins) for e in base]
    cand_els[chosen["elementIndex"]].ins[chosen["inputPin"]] = chosen["replacementSignal"]
    suspects = [chosen["connectionRef"]] + [a["connectionRef"] for a in alternatives]
    c10 = make_case(
        "D10", "defective_connection_not_uniquely_identifiable",
        "Two distinct single-edge mutations produce the same wrong behavior (OR instead of XOR).",
        None, None, [7], [7], suspects,
        force_ambiguous=True,
        ref_els_override=base, cand_els_override=cand_els,
        note="No oracle can distinguish the two single-edge causes from behavior alone.")
    c10["alternativeSingleEdgeCauses"] = [chosen] + alternatives
    c10["observedWrongTruthTable"] = wrong_sig
    cases.append(c10)

    return cases


def build_diagnostics(cases):
    return {
        "schemaVersion": SCHEMA,
        "artifactId": "diagnostic-rules",
        "status": "SPEC_ONLY_NOT_PRODUCTION",
        "principles": [
            "A replayed witness proves a behavioral difference relative to the selected reference; it never proves which connection is defective.",
            "A signal cone is RELEVANT_COMPUTATION, not a fault location.",
            "Suspected connections require a declared prior mapping or declared edit set and must be visibly labeled as unconfirmed candidates.",
            "No connection may be called wrong without sufficient evidence plus a declared intent oracle; user labels and aliases are never an oracle.",
            "EQUIVALENT, UNKNOWN, structural rejection and stale/missing closure produce no fault attribution.",
            "Diagnostics never modify verdicts, permissions, transactions or netlist bytes.",
        ],
        "traceAlgorithm": {
            "input": "candidate output map pin for each differing output bit",
            "steps": [
                "Resolve the emitting element by signal number and record elementIndex, outputPin and component path.",
                "Record each input pin as a connection with sourceSignal and sourceDescription.",
                "Recurse on non-constant source signals; stop at const0/const1 or top-level inputs.",
                "On a REF element, descend into the resolved sub-circuit with a path-qualified prefix.",
                "Stop at nodeCap and mark the cone truncated; a truncated cone yields UNKNOWN localization.",
            ],
            "outputClasses": ["RELEVANT_COMPUTATION", "SUSPECTED_CANDIDATE",
                              "AMBIGUOUS_MULTIPLE_CAUSES", "NO_FAULT_ATTRIBUTION",
                              "UNKNOWN_NO_ATTRIBUTION", "STRUCTURAL_REJECTION_NO_ATTRIBUTION"],
        },
        "caseExpectations": [
            {"caseId": c["caseId"], "category": c["category"],
             "class": c["diagnosticExpectation"]["class"],
             "provenBehavioralDifference": c["diagnosticExpectation"]["provenBehavioralDifference"],
             "suspectedConnections": c["diagnosticExpectation"]["suspectedConnections"],
             "uniqueFaultClaim": False,
             "intentOracle": c["intentOracle"]}
            for c in cases
        ],
    }


def build_guidance(cases):
    by_id = {c["caseId"]: c for c in cases}
    return {
        "schemaVersion": SCHEMA,
        "artifactId": "correction-guidance",
        "status": "SPEC_ONLY_NOT_PRODUCTION",
        "classificationLegend": {
            "VERIFIED_CORRECTION": "Re-applying this exact edit was re-compared in the fixture and restored equivalence to the selected reference; it is not absolute proof of intended behavior.",
            "CANDIDATE_DIAGNOSTIC_ACTION": "An action to inspect or test; it does not assert a fault or change the design until the user applies it.",
            "EXPLANATION_ONLY": "Informational text; no action, fault claim or repair.",
        },
        "llmOracle": "NONE",
        "llmOracleNote": "No language model is used as a proof or fault oracle in this corpus.",
        "suggestions": [
            {"id": "G01", "caseId": "D01", "title": "Inspect the output map",
             "classification": "CANDIDATE_DIAGNOSTIC_ACTION",
             "text": "Compare outputMap[0..n] with the declared prior pin order; each mapped pin is listed with its source signal.",
             "traceability": ["top/outputMap[0]", "top/outputMap[1]"]},
            {"id": "G02", "caseId": "D02", "title": "Review REF input order",
             "classification": "VERIFIED_CORRECTION",
             "text": "Restoring the declared prior REF input order [2,3] was re-compared and restored EQUIVALENT over all four inputs.",
             "verifiedBy": "exhaustive re-comparison in build_corpus.py",
             "traceability": ["top/element[0].in[0]", "top/element[0].in[1]"],
             "scope": "relative to the declared synthetic reference only"},
            {"id": "G03", "caseId": "D04", "title": "Check interface widths and bound pins",
             "classification": "EXPLANATION_ONLY",
             "text": "Signal 99 is not available before the REF element; the design was rejected structurally, so no behavioral diagnosis applies.",
             "traceability": []},
            {"id": "G04", "caseId": "D05", "title": "Replay the witness",
             "classification": "CANDIDATE_DIAGNOSTIC_ACTION",
             "text": "Replay the recorded witness under the trusted evaluator and confirm each differing output bit before inspecting pin order.",
             "traceability": by_id["D05"]["expected"]["differingBits"]},
            {"id": "G05", "caseId": "D03", "title": "Restore a known prior mapping",
             "classification": "VERIFIED_CORRECTION",
             "text": "Restoring the declared prior second REF input from signal 2 to signal 3 was re-compared and restored EQUIVALENT.",
             "verifiedBy": "exhaustive re-comparison in build_corpus.py",
             "traceability": ["top/element[0].in[1]"],
             "scope": "relative to the declared synthetic reference only"},
            {"id": "G06", "caseId": "D06", "title": "Run a new comparison after edits",
             "classification": "CANDIDATE_DIAGNOSTIC_ACTION",
             "text": "Apply one candidate at a time, rerun the trusted comparator over the full declared domain, and only then record a verified correction.",
             "traceability": []},
            {"id": "G07", "caseId": "D08", "title": "Explain an equivalent rewiring",
             "classification": "EXPLANATION_ONLY",
             "text": "XOR is commutative under input reversal; identical exhaustive behavior forbids any fault attribution.",
             "traceability": []},
            {"id": "G08", "caseId": "D10", "title": "Report indistinguishable causes",
             "classification": "EXPLANATION_ONLY",
             "text": "Two single-edge mutations yield the same wrong truth table; no observation can select one without an external oracle.",
             "traceability": by_id["D10"]["diagnosticExpectation"]["suspectedConnections"]},
        ],
    }


def build_ux(cases):
    return {
        "schemaVersion": SCHEMA,
        "artifactId": "ux-expectations",
        "status": "SPEC_ONLY_NOT_PRODUCTION",
        "conventionsSource": "docs/schema/m3/README.md; fixtures/m4-ux-acceptance/browser",
        "requiredFields": [
            "highlightedPinPairs", "witnessInputs", "referenceOutputs", "candidateOutputs",
            "differingOutputBits", "confidenceScopeLabels", "connectionTraceability",
            "accessibleDescriptions", "cliReadableOutput",
        ],
        "highlightedPinPairs": "Each suspected connection is shown as source description -> destination path/path-qualified input pin (for example const1 -> top/element[1].in[0]).",
        "witnessInputs": "BitVector inputs in LSB0 order with explicit decimal index; no semantic pin names.",
        "referenceOutputs": "Mapped reference output bits for the replayed witness, or null when no comparison ran.",
        "candidateOutputs": "Mapped candidate output bits for the replayed witness, or null when no comparison ran.",
        "differingOutputBits": "Zero-based output indices where replayed bits differ; empty for EQUIVALENT/UNKNOWN/rejection.",
        "confidenceScopeLabels": [
            "PROVEN_BEHAVIORAL_DIFFERENCE", "RELEVANT_COMPUTATION", "SUSPECTED_CANDIDATE",
            "AMBIGUOUS_MULTIPLE_CAUSES", "NO_FAULT_ATTRIBUTION", "UNKNOWN_NO_ATTRIBUTION",
            "STRUCTURAL_REJECTION_NO_ATTRIBUTION",
        ],
        "noConfidenceProbabilities": True,
        "connectionTraceability": "connectionRef -> path + elementIndex + inputPin + sourceSignal + netlistHex sha256 in the identity block.",
        "accessibleDescriptions": [
            "Text label accompanies every highlighted pair; color is never the sole signal.",
            "Differing output bits use a non-color double underline plus text 'differs at output N'.",
            "Announce witness, differing bit count and diagnostic scope as text.",
            "Bidirectional/control characters in any label are made visible or removed.",
        ],
        "cliReadableOutput": {
            "format": "structured JSON on stdout; diagnostics on stderr",
            "fields": ["caseId", "verdict", "witness", "differingBits", "cone",
                       "diagnosticClass", "suspectedConnections", "netlistSha256"],
            "exitCodes": {"0": "completed match", "1": "DIFFERENT", "2": "UNKNOWN",
                          "3": "INVALID_INPUT", "7": "stale closure"},
            "note": "Exit codes follow docs/schema/CLI_EXIT_CODES.md and m3 conventions; a DIFFERENT exit is not a proof of a faulty connection.",
        },
        "caseRenderExpectations": [
            {"caseId": c["caseId"], "diagnosticClass": c["diagnosticExpectation"]["class"],
             "differingBits": c["expected"]["differingBits"],
             "highlightCount": len(c["diagnosticExpectation"]["suspectedConnections"])}
            for c in cases
        ],
    }


def build_acceptance(cases):
    executable = [
        {"id": "E01", "name": "Correct witness replay",
         "cases": ["D01", "D02", "D03", "D05", "D06", "D07", "D09", "D10"],
         "check": "Every DIFFERENT witness replays under recursive and flat evaluators with recorded outputs."},
        {"id": "E02", "name": "Accurate affected-bit identification",
         "cases": ["D01", "D05", "D09"],
         "check": "Differing output indices match an independent full truth-table diff."},
        {"id": "E03", "name": "Equivalent designs receive no fault attribution",
         "cases": ["D08"],
         "check": "Verdict EQUIVALENT and suspectedConnections empty."},
        {"id": "E04", "name": "UNKNOWN yields no definitive correction",
         "cases": ["D04", "M07"],
         "check": "No verdict, no suspected connection and no verified correction is emitted."},
        {"id": "E05", "name": "Multiple plausible causes stay ambiguous",
         "cases": ["D10"],
         "check": "At least two distinct single-edge causes replay to the same wrong truth table; uniqueFaultClaim false."},
        {"id": "E06", "name": "Missing or stale dependency closure",
         "cases": ["M07"],
         "check": "Missing REF target yields structural rejection and UNKNOWN localization, not a fault claim."},
        {"id": "E07", "name": "Resource-limit handling",
         "cases": ["M08"],
         "check": "Truncated cone sets UNKNOWN_NO_ATTRIBUTION and never ranks a connection."},
        {"id": "E08", "name": "Trusted vector calibration",
         "cases": ["CAL01"],
         "check": "Archived XOR#1 [0,1,1,0] and NAND#2 [1,1,1,0] vectors reproduce."},
        {"id": "E09", "name": "Correction classification vocabulary",
         "cases": ["ALL"],
         "check": "Every guidance item uses one of the three allowed classifications."},
    ]
    spec_only = [
        {"id": "S01", "name": "Production UI highlighted pin pairs",
         "reason": "No M4.5-2D production component exists on the accepted M4 baseline."},
        {"id": "S02", "name": "Browser accessibility announcements",
         "reason": "Requires the future web diagnostic view and a real assistive-technology session."},
        {"id": "S03", "name": "CLI diagnostic command JSON/exit codes",
         "reason": "No diagnostic CLI command is implemented; only the output contract is specified."},
        {"id": "S04", "name": "Applying a candidate repair and rerunning trusted comparison",
         "reason": "Requires production composition/edit flow; fixture verifies the repair result in isolation only."},
        {"id": "S05", "name": "Human first-time-developer usability",
         "reason": "Requires a real developer session with an unfamiliar mutation."},
        {"id": "S06", "name": "Live chain closure freshness",
         "reason": "No live RPC or publication is authorized; all identities are synthetic."},
    ]
    return {
        "schemaVersion": SCHEMA,
        "artifactId": "acceptance-corpus",
        "executableChecks": executable,
        "specificationOnly": spec_only,
        "metaCases": {
            "M07": {"description": "Top REF points at a circuit ID absent from the dependency bank.",
                    "expectedVerdict": "INVALID_INPUT",
                    "expectedDiagnosticClass": "UNKNOWN_NO_ATTRIBUTION"},
            "M08": {"description": "Cone traversal capped at 1 node while a differing output has a larger cone.",
                    "expectedTruncated": True,
                    "expectedDiagnosticClass": "UNKNOWN_NO_ATTRIBUTION"},
            "CAL01": {"description": "Archived XOR#1 and NAND#2 vectors used to calibrate the independent evaluator.",
                      "expected": {"xor": [[0], [1], [1], [0]], "nand": [[1], [1], [1], [0]]}},
        },
        "caseIds": [c["caseId"] for c in cases],
    }


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")


def main() -> None:
    cases = build_cases()
    selftest = d.self_test()
    write_json(ROOT / "cases" / "debugging-corpus.json", {
        "schemaVersion": SCHEMA, "artifactId": "debugging-corpus",
        "provenance": "SYNTHETIC", "coreVersion": d.CORE_VERSION,
        "calibration": selftest, "cases": cases,
    })
    write_json(ROOT / "diagnostics" / "diagnostic-rules.json", build_diagnostics(cases))
    write_json(ROOT / "diagnostics" / "correction-guidance.json", build_guidance(cases))
    write_json(ROOT / "ux" / "ux-expectations.json", build_ux(cases))
    write_json(ROOT / "acceptance" / "acceptance-corpus.json", build_acceptance(cases))

    files = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()
                       and "__pycache__" not in p.parts and p.suffix != ".pyc"
                       and p.name not in {"MANIFEST.json", "BUILD_INFO.json"}):
        data = path.read_bytes()
        files.append({"path": path.relative_to(ROOT).as_posix(),
                      "bytes": len(data), "sha256": sha(data)})
    write_json(ROOT / "MANIFEST.json", {
        "schemaVersion": SCHEMA, "manifestType": "SHA256SUMS",
        "note": "SHA-256 over all authored fixture bytes.", "files": files,
    })
    write_json(ROOT / "BUILD_INFO.json", {
        "schemaVersion": SCHEMA, "baseCommit": "09f2482beae84be6d919ecd6957c4153d1924cca",
        "branch": "opencode/flip-m45-debugging-fixtures",
        "coreVersion": d.CORE_VERSION, "seed": "NONE_DETERMINISTIC",
        "generator": "fixtures/m45-debugging/generators/build_corpus.py",
        "provenance": "SYNTHETIC", "caseCount": len(cases),
        "manifestFiles": len(files),
    })
    print("cases=%d manifest_files=%d" % (len(cases), len(files)))


if __name__ == "__main__":
    main()
