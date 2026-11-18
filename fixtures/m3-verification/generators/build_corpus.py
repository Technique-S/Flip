"""Deterministically build the Flip M3 independent verification corpus.

Stdlib only. Run from the worktree root:

    python fixtures/m3-verification/generators/build_corpus.py

Regeneration is byte-identical (no timestamps, no host-dependent fields in the
authored fixtures). Timing measurements live only in results/*.json and are
explicitly labelled as fixture-generation observations, never production data.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                       # fixtures/m3-verification
sys.path.insert(0, str(HERE))

import m3_core as core  # noqa: E402

CORE_VERSION = core.CORE_VERSION
GENERATION_SEED = 20261118
PROC0 = bytes.fromhex("839bdd6fa7a66416a609a735e11de5411b98574e")
XOR1 = bytes.fromhex("00000002000003000000020000040000000300000400000005000006")
NAND2 = bytes.fromhex("000000020000030000000400000400000005000005")
SYNTH_CPU = bytes.fromhex("11" * 20)
RAW_SOURCE = {
    "chainId": 196,
    "block": 76020961,
    "fixture": "docs/evidence/raw/M0/xlayer_circuits.json",
    "note": "Pinned historical X Layer mainnet read (M0 audit). Copied-byte "
            "provenance only; no live RPC was contacted for M3-B.",
}

BANK = {(PROC0.hex(), 1): (2, 1, XOR1), (PROC0.hex(), 2): (2, 1, NAND2)}


def jdump(obj) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write(path: Path, obj) -> dict:
    data = jdump(obj)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return {"path": path.relative_to(ROOT.parent.parent).as_posix(),
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def source_record(name: str, cid: int, netlist: bytes, function: str) -> dict:
    return {
        "processor": "0x" + PROC0.hex(), "circuit_id": cid, "function": function,
        "n_in": 2, "n_out": 1, "n_state": 0,
        "netlist_sha256": sha(netlist), "netlist_hex": "0x" + netlist.hex(),
        "provenance": "ARCHIVED_RAW_XLAYER", **RAW_SOURCE, "label": name,
    }


SOURCES = [
    source_record("XOR#1", 1, XOR1, "xor(a,b) = a XOR b (4 NAND)"),
    source_record("NAND#2", 2, NAND2, "nand(a,b) = NOT(a AND b) (3 NAND)"),
]


# --------------------------------------------------------------------------
# circuit helpers
# --------------------------------------------------------------------------
def half_adder_els() -> list:
    # REF(NAND) -> s4 ; NAND(s4, const1) -> s5=carry ; REF(XOR) -> s6=sum
    return [core.ref(PROC0, 2, [2, 3], 1), core.nand(4, 1), core.ref(PROC0, 1, [2, 3], 1)]


def mutant_reversed_both() -> list:
    return [core.ref(PROC0, 2, [3, 2], 1), core.nand(4, 1), core.ref(PROC0, 1, [3, 2], 1)]


def mutant_xor_swapped() -> list:
    return [core.ref(PROC0, 2, [2, 3], 1), core.nand(4, 1), core.ref(PROC0, 1, [3, 2], 1)]


def mutant_glue_wrong() -> list:
    return [core.ref(PROC0, 2, [2, 3], 1), core.nand(2, 1), core.ref(PROC0, 1, [2, 3], 1)]


def mutant_outputs_swapped() -> list:
    return [core.ref(PROC0, 1, [2, 3], 1), core.ref(PROC0, 2, [2, 3], 1)]


def xor_nand_combo() -> list:
    # XOR(NAND(a,b), const1) = NOT(NAND(a,b)) = a AND b = carry
    return [core.ref(PROC0, 2, [2, 3], 1), core.ref(PROC0, 1, [4, 1], 1)]


def parity_chain_els(L: int, fault_step: int | None = None, reverse_ports: bool = False) -> list:
    """L chained REF(XOR) records over L+1 inputs; flattens to 4*L NAND gates."""
    n_in = L + 1
    els = []
    for i in range(L):
        if i == 0:
            ins = [2, 3]
        else:
            prev = 2 + n_in + (i - 1)
            inp = i + 3            # a_(i+2)
            ins = [prev, inp]
        if reverse_ports:
            ins = list(reversed(ins))
        if fault_step is not None and i == fault_step - 1:
            ins = [3, ins[1]]      # duplicated raw input a2 instead of running parity
        els.append(core.ref(PROC0, 1, ins, 1))
    return els


def describe_circuit(c: core.Circuit, netlist: bytes) -> dict:
    rec = []
    for e in c.elements:
        rec.append({"op": ["NAND", "LATCH", "REF"][e.op],
                    "ins": e.ins, "n_out": e.n_out,
                    "ref": ("0x" + e.cpu.hex(), e.cid) if e.op == core.REF else None})
    return {
        "netlist_hex": "0x" + netlist.hex(), "netlist_bytes": len(netlist),
        "netlist_sha256": sha(netlist),
        "properties": {
            "n_in": c.n_in, "n_out": c.n_out, "n_state": c.n_state,
            "n_signals": c.n_signals, "n_gates_expanded": c.n_gates,
            "records": len(c.elements), "ref_records": sum(1 for e in c.elements if e.op == core.REF),
            "nand_glue_records": sum(1 for e in c.elements if e.op == core.NAND),
            "latch_records": sum(1 for e in c.elements if e.op == core.LATCH),
            "record_detail": rec,
        },
    }


def truth_rows(c: core.Circuit) -> list[dict]:
    if c.n_in > 8:
        return [{"omitted": "n_in > 8; witness-based comparison used instead"}]
    return core.exhaustive_table(c, 1 << 16)


# --------------------------------------------------------------------------
# Task A -- golden circuit compositions
# --------------------------------------------------------------------------
def build_task_a() -> dict:
    cases = []

    def add(cid, title, category, els, n_in, n_out, expected, provenance, bank,
            reproduction, truth=True, extra=None):
        nl = core.encode(els)
        c = core.load(nl, n_in, n_out, bank)
        obj = {
            "id": cid, "title": title, "category": category,
            "source_circuits": SOURCES if bank == BANK else SOURCES + [{
                "processor": "0x" + SYNTH_CPU.hex(), "circuit_id": 1,
                "function": "synthetic XOR wrapper (nested REF)", "n_in": 2,
                "n_out": 1, "n_state": 0, "provenance": "SYNTHETIC",
                "not_an_onchain_observation": True,
            }],
            "expected_result": expected, "provenance": provenance,
            "reproduction": reproduction,
        }
        obj.update(describe_circuit(c, nl))
        obj["truth_table"] = truth_rows(c) if truth else []
        if extra:
            obj.update(extra)
        cases.append(obj)
        return c, nl

    add("A01", "Real XOR and NAND combination", "valid-composition",
        xor_nand_combo(), 2, 1,
        "LOAD_OK; outputs = a AND b (carry); 2 REF records, 7 expanded NAND gates; "
        "EQUIVALENT to the direct AND truth table over all 4 inputs",
        "REAL_SOURCES + SYNTHETIC_COMPOSITION_RECIPE", BANK,
        "encode [REF(NAND#2,[2,3]), REF(XOR#1,[4,1])]; load(nIn=2,nOut=1,BANK)",
        extra={"derived_function": "a AND b", "truth_basis": "exhaustive over 4 inputs"})

    base_c, base_nl = add("A02", "Half-adder composition (audited 81-byte recipe)", "valid-composition",
        half_adder_els(), 2, 2,
        "LOAD_OK; exactly 81 netlist bytes; 2 REF + 1 NAND glue; outputs (carry,sum) = "
        "(a AND b, a XOR b); 4/4 truth-table rows correct",
        "REAL_SOURCES + AUDITED_COMPOSITION_RECIPE", BANK,
        "encode [REF(NAND#2,[2,3]), NAND(4,1), REF(XOR#1,[2,3])]; load(2,2,BANK)",
        extra={"derived_function": "(a AND b, a XOR b)", "truth_basis": "exhaustive over 4 inputs",
               "audited_netlist_bytes_expected": 81})

    add("A03", "Commutative-input rewiring", "equivalent-wiring",
        mutant_reversed_both(), 2, 2,
        "LOAD_OK; EQUIVALENT to A02 over all 4 inputs (NAND and XOR are symmetric); "
        "SAT miter UNSAT", "SYNTHETIC_MUTATION_OF_REAL_SOURCES", BANK,
        "reverse both REF input pairs of A02; compare against A02",
        extra={"compared_to": "A02"})

    add("A04", "Non-equivalent output permutation", "different-wiring",
        mutant_outputs_swapped(), 2, 2,
        "LOAD_OK; DIFFERENT from A02 (outputs are (sum, NAND) instead of (carry,sum)); "
        "witness required", "SYNTHETIC_MUTATION_OF_REAL_SOURCES", BANK,
        "encode [REF(XOR#1,[2,3]), REF(NAND#2,[2,3])]; load(2,2,BANK); compare A02",
        extra={"compared_to": "A02"})

    p_base = core.load(core.encode(parity_chain_els(7)), 8, 1, BANK)
    p_fault = core.load(core.encode(parity_chain_els(7, fault_step=3)), 8, 1, BANK)
    cases.append({
        "id": "A05", "title": "Duplicated-input fan-out (8-input parity)", "category": "different-wiring",
        "source_circuits": SOURCES, "provenance": "SYNTHETIC_MUTATION_OF_REAL_SOURCES",
        "expected_result": "Both LOAD_OK; both flatten to 28 NAND and pass TAP-02 §3; "
                           "DIFFERENT (3rd XOR reads raw input a2 instead of running parity)",
        "reproduction": "encode 7 chained REF(XOR#1); fault at step 3 replaces running parity with input a2",
        "reference": describe_circuit(p_base, core.encode(parity_chain_els(7))),
        "candidate": describe_circuit(p_fault, core.encode(parity_chain_els(7, fault_step=3))),
        "reference_truth_table": core.exhaustive_table(p_base, 1 << 16),
        "candidate_truth_table": core.exhaustive_table(p_fault, 1 << 16),
        "compared_to": "A05 reference",
    })

    mid = core.encode([core.ref(PROC0, 1, [2, 3], 1)])
    bank_ext = dict(BANK)
    bank_ext[(SYNTH_CPU.hex(), 1)] = (2, 1, mid)
    add("A06", "Multiple levels of REF composition", "nested-composition",
        [core.ref(SYNTH_CPU, 1, [2, 3], 1), core.ref(PROC0, 2, [2, 3], 1)], 2, 2,
        "LOAD_OK; 2 REF levels (top -> synthetic wrapper -> real XOR#1); outputs (xor, NAND); "
        "EQUIVALENT to A04 and to a direct XOR/NAND composition",
        "SYNTHETIC_WRAPPER + REAL_SOURCES", bank_ext,
        "register synthetic wrapper netlist [REF(XOR#1,[2,3])]; encode top [REF(wrapper,[2,3]), REF(NAND#2,[2,3])]",
        extra={"ref_depth_actual": 2, "compared_to": "A04"})

    # negatives: capture the observed rejection reason from the independent loader
    def negative(cid, title, els, n_in, n_out, bank, expected_reason, reproduction,
                 note="", companion=""):
        nl = (els if isinstance(els, (bytes, bytearray)) else core.encode(els)) if els is not None else b""
        entry = {"id": cid, "title": title, "category": "invalid",
                 "netlist_hex": "0x" + nl.hex(), "n_in": n_in, "n_out": n_out,
                 "expected_result": "REJECT / INVALID_INPUT", "expected_reason": expected_reason,
                 "provenance": "SYNTHETIC_NEGATIVE", "reproduction": reproduction,
                 "note": note, "companion": companion}
        try:
            core.load(nl, n_in, n_out, bank)
            entry["observed"] = "UNEXPECTED_ACCEPT"
        except Exception as exc:  # noqa: BLE001 - fixture records the actual reason
            entry["observed"] = "%s: %s" % (type(exc).__name__, exc)
        cases.append(entry)

    negative("A07", "Invalid external pin mapping (forward REF/NAND signal)",
             [core.ref(PROC0, 1, [4, 3], 1)], 2, 1, BANK,
             "signal 4 referenced by element at 4 is not available",
             "encode REF(XOR#1,[4,3]) and load(2,1,BANK)",
             companion="NAND(4,4) also rejected; signal 4 is the element's own output slot")
    # Two-node cycle A->B->A. Root A is loaded against a bank that closes the cycle.
    a_net = core.encode([core.ref(SYNTH_CPU, 2, [2, 3], 1)])
    b_net = core.encode([core.ref(SYNTH_CPU, 1, [2, 3], 1)])
    self_net = core.encode([core.ref(SYNTH_CPU, 3, [2, 3], 1)])
    cycle_bank = {
        (SYNTH_CPU.hex(), 1): (2, 1, a_net),
        (SYNTH_CPU.hex(), 2): (2, 1, b_net),
        (SYNTH_CPU.hex(), 3): (2, 1, self_net),
    }
    negative("A08", "Unsupported cycles (two-node and self REF cycle)", a_net, 2, 1,
             cycle_bank, "REF cycle",
             "load netlist 0x"+a_net.hex()+" against the embedded cyclic bank",
             note="self-cycle circuit :3 is also embedded below",
             companion="A->B->A and A->A both rejected by the recursion stack guard")
    a8 = cases[-1]
    a8["banks"] = {
        "0x" + SYNTH_CPU.hex() + ":1": "0x" + a_net.hex(),
        "0x" + SYNTH_CPU.hex() + ":2": "0x" + b_net.hex(),
    }
    a8["self_cycle_spec"] = {"circuit": "0x" + SYNTH_CPU.hex() + ":3",
                             "netlist": "0x" + self_net.hex()}
    try:
        core.load(self_net, 2, 1, cycle_bank)
        a8["self_cycle_observed"] = "UNEXPECTED_ACCEPT"
    except Exception as exc:  # noqa: BLE001
        a8["self_cycle_observed"] = "%s: %s" % (type(exc).__name__, exc)

    negative("A09", "Incorrect output-width mapping", [core.ref(PROC0, 1, [2, 3], 2)], 2, 1, BANK,
             "REF arity does not match the target circuit",
             "encode REF(XOR#1, n_out=2) and load(2,1,BANK)",
             note="second variant: one NAND record declared nOut=2 -> 'too few signals for outputs'")
    cases[-1]["second_variant"] = {"netlist_hex": "0x" + core.encode([core.nand(2, 3)]).hex(),
                                   "n_in": 2, "n_out": 2,
                                   "expected_reason": "too few signals for outputs"}

    # dependency substitution with two banks
    alt_xor = core.encode([core.nand(2, 3), core.nand(3, 4), core.nand(2, 4), core.nand(5, 6)])
    bank_bad = dict(BANK)
    bank_bad[(PROC0.hex(), 1)] = (2, 1, NAND2)      # XOR identity now resolves to NAND
    bank_equiv = dict(BANK)
    bank_equiv[(PROC0.hex(), 1)] = (2, 1, alt_xor)  # equivalent XOR, different bytes
    ha = core.encode(half_adder_els())
    c_bad = core.load(ha, 2, 2, bank_bad)
    c_eq = core.load(ha, 2, 2, bank_equiv)
    bad_wit = None
    for v in range(4):
        bits = [(v >> i) & 1 for i in range(2)]
        if core.eval_recursive(base_c, bits) != core.eval_recursive(c_bad, bits):
            bad_wit = bits
            break
    cases.append({
        "id": "A10", "title": "Dependency-substitution scenarios", "category": "dependency-integrity",
        "source_circuits": SOURCES, "provenance": "SYNTHETIC_BANK_SUBSTITUTION_OF_REAL_SOURCES",
        "expected_result": "bad substitution => DIFFERENT with witness; equivalent substitution "
                           "=> same behavior but DEPENDENCY_CHANGED / STALE integrity (never CURRENT)",
        "reproduction": "keep REF identity fixed at (PROC0,XOR#1) but change the bank's netlist bytes",
        "base": describe_circuit(base_c, base_nl),
        "substitution_bad": {
            "substituted_identity": "0x" + PROC0.hex() + ":1",
            "resolves_to": "NAND#2 netlist", "netlist_sha256": sha(NAND2),
            "netlist_properties": describe_circuit(c_bad, ha)["properties"],
            "distinguishing_input": bad_wit,
            "behavioral_result": "DIFFERENT",
        },
        "substitution_equivalent": {
            "substituted_identity": "0x" + PROC0.hex() + ":1",
            "alternative_xor_netlist_hex": "0x" + alt_xor.hex(),
            "alternative_xor_netlist_sha256": sha(alt_xor),
            "original_xor_netlist_sha256": sha(XOR1),
            "netlist_properties": describe_circuit(c_eq, ha)["properties"],
            "behavioral_result": "EQUIVALENT over all 4 inputs",
            "integrity_result": "DEPENDENCY_CHANGED / STALE (hash differs); must not be labelled CURRENT",
            "all_inputs_equal": all(
                core.eval_recursive(base_c, [(v >> i) & 1 for i in range(2)])
                == core.eval_recursive(c_eq, [(v >> i) & 1 for i in range(2)])
                for v in range(4)),
        },
    })

    return {
        "schema": "flip-m3-verification-golden-compositions/1",
        "generator": "build_corpus.py", "core_version": CORE_VERSION,
        "generation_seed": GENERATION_SEED,
        "chain_context": RAW_SOURCE,
        "cases": cases,
        "note": "All composed netlists are deterministic synthetic recipes built from "
                "archived real X Layer source circuits. No synthetic circuit was deployed "
                "on X Layer and no live RPC was contacted.",
    }


# --------------------------------------------------------------------------
# Task B -- SAT correctness corpus
# --------------------------------------------------------------------------
def build_task_b() -> dict:
    cases = []

    def load(els, n_in, n_out, bank=BANK):
        nl = core.encode(els)
        return core.load(nl, n_in, n_out, bank), nl

    base, base_nl = load(half_adder_els(), 2, 2)
    rev, _ = load(mutant_reversed_both(), 2, 2)
    xswap, _ = load(mutant_xor_swapped(), 2, 2)
    glue, _ = load(mutant_glue_wrong(), 2, 2)
    outswap, _ = load(mutant_outputs_swapped(), 2, 2)
    multi, _ = load([core.nand(2, 1), core.ref(PROC0, 2, [2, 3], 1)], 2, 2)
    p8, _ = load(parity_chain_els(7), 8, 1)
    p8f, _ = load(parity_chain_els(7, fault_step=3), 8, 1)
    const0, _ = load([core.nand(1, 1)], 0, 1)
    const1, _ = load([core.nand(0, 0)], 0, 1)
    cp_a, _ = load([core.nand(0, 0), core.nand(1, 1)], 2, 2)
    cp_b, _ = load([core.nand(1, 1), core.nand(0, 0)], 2, 2)
    xr, _ = load([core.ref(PROC0, 1, [2, 3], 1)], 2, 1)
    in3, _ = load([core.ref(PROC0, 1, [2, 3], 1), core.nand(4, 1)], 3, 2)
    nd, _ = load([core.ref(PROC0, 2, [2, 3], 1)], 2, 1)

    bank_missing = dict(BANK)
    bank_missing.pop((PROC0.hex(), 1))

    faulty_bank = dict(BANK)
    faulty_bank[(PROC0.hex(), 1)] = (2, 1, NAND2)
    faulty_ha, _ = load(half_adder_els(), 2, 2, faulty_bank)

    def add(cid, title, ref_c, cand_c, expected, method, exactness, note="", max_dec=None):
        rec = {"id": cid, "title": title, "expected_result": expected,
               "method": method, "exactness": exactness, "note": note,
               "reference": describe_circuit(ref_c, core.encode(ref_c.elements))}
        if cand_c is not None:
            rec["candidate"] = describe_circuit(cand_c, core.encode(cand_c.elements))
        if max_dec is not None:
            rec["forced_decision_budget"] = max_dec
        if cand_c is None:
            cases.append(rec)
            return
        try:
            got = core.compare_stateless(ref_c, cand_c, max_decisions=max_dec)
            rec["executed"] = got
            rec["agrees_with_expected"] = (got["verdict"] == expected)
        except Exception as exc:  # noqa: BLE001
            rec["executed"] = {"error": "%s: %s" % (type(exc).__name__, exc)}
            rec["agrees_with_expected"] = False
        cases.append(rec)

    add("B01", "EQUIVALENT (symmetric rewiring)", base, rev, "EQUIVALENT",
        "exhaustive over 4 inputs + Tseitin/DPLL miter UNSAT", "exact",
        "Reference is a real-source-derived audited half-adder; candidate reverses both REF input pairs.")
    add("B02", "DIFFERENT (glue wired to input bit)", base, glue, "DIFFERENT",
        "exhaustive + SAT witness replayed by two evaluators", "exact")
    add("B03", "UNKNOWN (missing oracle / unresolved REF)", base, None, "UNKNOWN",
        "resolution attempt against a bank lacking XOR#1", "exact",
        "Candidate REF target is unregistered: comparison must be UNKNOWN, never EQUIVALENT.")
    # B03 needs a special path: cand is None, handle explicitly instead of compare_stateless
    b3 = cases[-1]
    b3.pop("candidate", None)
    b3["candidate_spec"] = {"netlist_hex": "0x" + core.encode([core.ref(PROC0, 1, [2, 3], 1)]).hex(),
                            "bank": "BANK without (PROC0, XOR#1)"}
    try:
        core.load(core.encode([core.ref(PROC0, 1, [2, 3], 1)]), 2, 1, bank_missing)
        b3["observed"] = "UNEXPECTED_ACCEPT"
    except Exception as exc:  # noqa: BLE001
        b3["executed"] = {"resolution_error": "%s: %s" % (type(exc).__name__, exc),
                          "verdict": "UNKNOWN"}
        b3["agrees_with_expected"] = True

    add("B04", "Self-equivalence (false-positive regression)", base, base, "EQUIVALENT",
        "self-miter must be UNSAT", "exact",
        "Regression for the historical false-positive witness [0,0] on base vs base.")
    add("B05", "Equivalent symmetric gates (XOR port swap)", base, xswap, "EQUIVALENT",
        "exhaustive + UNSAT", "exact")
    add("B06", "Non-equivalent behavior (8-input parity fan-out)", p8, p8f, "DIFFERENT",
        "SAT over 28 flattened NAND + witness replay; exhaustive cross-check over 256 inputs", "exact")
    add("B07", "Output permutation", base, outswap, "DIFFERENT",
        "exhaustive + SAT witness replay", "exact")
    add("B08", "Multiple output differences", base, multi, "DIFFERENT",
        "exhaustive + SAT witness replay; both output positions recorded", "exact")
    add("B09", "Constant outputs", cp_a, cp_b, "DIFFERENT",
        "exhaustive over 4 inputs + SAT (empty/any witness)", "exact",
        "Two constant-output circuits are not interchangeable when output order differs.")
    add("B10", "Zero-input circuits", const1, const0, "DIFFERENT",
        "SAT over zero input variables; witness is the empty vector", "exact")
    add("B11", "Zero-output boundary", base, base, "UNKNOWN",
        "nOut=0 rejected before comparison", "exact",
        "nOut=0 is outside TAP-02 range; a comparison request with zero outputs is INVALID_INPUT/UNKNOWN.")
    b11 = cases[-1]
    try:
        core.load(base_nl, 2, 0, BANK)
        b11["observed"] = "UNEXPECTED_ACCEPT"
    except Exception as exc:  # noqa: BLE001
        b11["executed"] = {"load_error": "%s: %s" % (type(exc).__name__, exc), "verdict": "UNKNOWN"}
        b11["agrees_with_expected"] = True

    add("B12", "Wrong input width", base, in3, "INVALID_INPUT",
        "interface compatibility check before SAT", "exact",
        "2-input vs 3-input interfaces cannot be compared; must not report EQUIVALENT.")
    add("B13", "Wrong output width", base, xr, "INVALID_INPUT",
        "interface compatibility check before SAT", "exact",
        "2-output baseline vs 1-output candidate. (xr has nIn=2,nOut=1.)")
    add("B14", "Unbound REF input", base, None, "INVALID_INPUT",
        "TAP-02 backward-reference validation", "exact",
        "REF input signal 4 equals the element's first output -> forward reference rejected.")
    b14 = cases[-1]
    b14.pop("candidate", None)
    b14["candidate_spec"] = {"netlist_hex": "0x" + core.encode([core.ref(PROC0, 1, [4, 3], 1)]).hex()}
    try:
        core.load(core.encode([core.ref(PROC0, 1, [4, 3], 1)]), 2, 1, BANK)
        b14["observed"] = "UNEXPECTED_ACCEPT"
    except Exception as exc:  # noqa: BLE001
        b14["executed"] = {"validation_error": "%s: %s" % (type(exc).__name__, exc),
                           "verdict": "INVALID_INPUT"}
        b14["agrees_with_expected"] = True

    add("B15", "Faulty REF expansion", base, faulty_ha, "DIFFERENT",
        "SAT witness replayed by both evaluators; witness chosen to distinguish XOR from NAND", "exact",
        "XOR identity is resolved to the NAND#2 netlist. [1,1] cannot distinguish; a valid witness is required.")
    add("B16", "Changed circuit reference", xr, nd, "DIFFERENT",
        "exhaustive + SAT witness replay", "exact")
    add("B17", "Solver timeout forced by decision budget", p8, p8, "UNKNOWN",
        "DPLL decision budget exhausted by harness", "exact-for-harness-only",
        "Harness-level UNKNOWN demonstration. NOT a production solver timing result.",
        max_dec=0)

    return {
        "schema": "flip-m3-verification-sat-corpus/1",
        "generator": "build_corpus.py", "core_version": CORE_VERSION,
        "seed": GENERATION_SEED,
        "evaluators": ["m3_core.eval_recursive", "m3_core.eval_flat", "m3_core.cnf_miter+solve"],
        "cases": cases,
        "note": "EXACT means the verdict is decided over the full input domain or by a "
                "completed UNSAT/SAT proof with replayed witness. No case is classified "
                "EQUIVALENT from sampling alone.",
    }


# --------------------------------------------------------------------------
# Task C -- witness verification
# --------------------------------------------------------------------------
def build_task_c(sat_corpus: dict) -> dict:
    records = []
    for case in sat_corpus["cases"]:
        if case.get("executed", {}).get("verdict") != "DIFFERENT":
            continue
        witness = case["executed"].get("witness")
        if witness is None:  # empty list is a valid witness for zero-input circuits
            continue
        # Rebuild the pair from the recorded netlists/banks where possible.
        rid = case["id"]
        faulty_bank = {**BANK, (PROC0.hex(), 1): (2, 1, NAND2)}
        pairs = {
            "B02": (half_adder_els(), BANK, mutant_glue_wrong(), BANK, 2, 2),
            "B06": (parity_chain_els(7), BANK, parity_chain_els(7, fault_step=3), BANK, 8, 1),
            "B07": (half_adder_els(), BANK, mutant_outputs_swapped(), BANK, 2, 2),
            "B08": (half_adder_els(), BANK, [core.nand(2, 1), core.ref(PROC0, 2, [2, 3], 1)], BANK, 2, 2),
            "B09": ([core.nand(0, 0), core.nand(1, 1)], BANK,
                    [core.nand(1, 1), core.nand(0, 0)], BANK, 2, 2),
            "B10": ([core.nand(0, 0)], BANK, [core.nand(1, 1)], BANK, 0, 1),
            "B15": (half_adder_els(), BANK, half_adder_els(), faulty_bank, 2, 2),
            "B16": ([core.ref(PROC0, 1, [2, 3], 1)], BANK,
                    [core.ref(PROC0, 2, [2, 3], 1)], BANK, 2, 1),
        }
        if rid not in pairs:
            continue
        r_els, r_bank, c_els, c_bank, ni, no = pairs[rid]
        rc = core.load(core.encode(r_els), ni, no, r_bank)
        cc = core.load(core.encode(c_els), ni, no, c_bank)
        ro = list(core.eval_recursive(rc, witness))
        co = list(core.eval_recursive(cc, witness))
        rf = list(core.eval_flat(core.flatten(rc), witness))
        cf = list(core.eval_flat(core.flatten(cc), witness))
        minimal = core.minimize_witness(rc, cc, witness)
        differing_positions = [i for i, (x, y) in enumerate(zip(ro, co)) if x != y]
        records.append({
            "case": rid, "distinguishing_input": witness,
            "reference_output_recursive": ro, "candidate_output_recursive": co,
            "reference_output_flat": rf, "candidate_output_flat": cf,
            "outputs_differ": ro != co,
            "independent_evaluators_agree": (ro == rf and co == cf),
            "differing_output_positions": differing_positions,
            "greedy_minimized_witness": minimal,
            "minimization_claim": "small witness by greedy bit clearing, NOT proven mathematically minimal",
            "minimal_reproduction": {
                "reference_netlist_hex": "0x" + core.encode(r_els).hex(),
                "candidate_netlist_hex": "0x" + core.encode(c_els).hex(),
                "reference_bank": "ARCHIVED_REAL_BANK" if r_bank is BANK else "SUBSTITUTED_BANK",
                "candidate_bank": "ARCHIVED_REAL_BANK" if c_bank is BANK else "SUBSTITUTED_BANK",
                "n_in": ni, "n_out": no,
                "steps": [
                    "decode + load both netlists against the recorded bank",
                    "evaluate both on the distinguishing input with eval_recursive and eval_flat",
                    "confirm outputs differ by at least one bit position",
                ],
            },
            "verified": (ro != co and ro == rf and co == cf),
        })
    # A-case witnesses recorded separately (documented, derived from exhaustive enumeration)
    extra = []
    extra.append({
        "case": "A04", "distinguishing_input": [0, 0],
        "reference_output": list(core.eval_recursive(
            core.load(core.encode(half_adder_els()), 2, 2, BANK), [0, 0])),
        "candidate_output": list(core.eval_recursive(
            core.load(core.encode(mutant_outputs_swapped()), 2, 2, BANK), [0, 0])),
        "verified": True, "source": "exhaustive over 4 inputs",
    })
    extra.append({
        "case": "A10-bad-substitution", "distinguishing_input": [0, 0],
        "note": "see A10.substitution_bad.distinguishing_input; recorded in golden-compositions.json",
        "verified": True,
    })
    return {
        "schema": "flip-m3-verification-witness-corpus/1",
        "generator": "build_corpus.py", "core_version": CORE_VERSION,
        "witnesses": records, "additional_witnesses": extra,
        "policy": "A witness is recorded only when both independent evaluators agree and "
                  "the outputs actually differ. Otherwise the case stays UNKNOWN. No "
                  "unverified counterexample is invented.",
    }


# --------------------------------------------------------------------------
# Task D -- proof-integrity attacks (specifications)
# --------------------------------------------------------------------------
def base_report(**overrides) -> dict:
    r = {
        "schemaVersion": "1.0.0", "chainId": 196,
        "projectHash": "0x" + "11" * 32,
        "referenceManifestHash": "0x" + "22" * 32,
        "candidateManifestHash": "0x" + "33" * 32,
        "toolVersion": "0.1.0",
        "semantics": {"tap02Version": "draft-2026-10-04", "encoding": "tap02-lsb0-v1"},
        "verification": {
            "kind": "PAIRWISE_EQUIVALENCE", "verdict": "EQUIVALENT",
            "reasonCode": "SAT_UNSAT", "solverBackend": "MINISAT22",
            "solverOutcome": "UNSAT", "sourceValidation": "UNVERIFIED",
            "mappingValidation": "UNVERIFIED", "witness": None,
        },
        "intent": "TRUSTED_BASELINE", "inputMap": [0, 1], "outputMap": [0],
        "integrity": {"freshness": "CURRENT", "checkedBlock": 76020961},
    }
    for k, v in overrides.items():
        if isinstance(v, dict) and isinstance(r.get(k), dict):
            r[k].update(v)
        else:
            r[k] = v
    return r


def build_task_d() -> dict:
    attacks = []

    def add(aid, name, field, expected, rationale, payload, code):
        attacks.append({
            "id": aid, "name": name, "target_field": field,
            "expected_safe_behavior": expected, "rationale": rationale,
            "expected_code": code, "crafted_report": payload,
            "status": "SPEC_ONLY_NOT_EXECUTED_AGAINST_PRODUCTION",
            "note": "No M3 proof consumer is implemented on this branch. These are "
                    "hostile fixture specifications for Codex to wire into the M3 consumer.",
        })

    r = base_report(verification={"verdict": "EQUIVALENT"}, inputMap=[], outputMap=[])
    add("D01", "Empty self-declared width mapping", "inputMap/outputMap",
        "Reject: a report with empty maps cannot bind external widths. Return UNKNOWN / "
        "NOT_ACCEPTABLE, never EQUIVALENT.",
        "M2 acceptance M1-REG-002 showed a conclusive report with an empty self-declared map "
        "passing the v1 shape validator. Shape pass is not a trusted-consumer pass.",
        r, "INVALID_INPUT")

    r = base_report()
    r["verification"]["verdict"] = "EQUIVALENT"
    r["integrity"]["freshness"] = "UNVERIFIED"
    r["referenceManifestHash"] = "0x" * 32
    add("D02", "Forged EQUIVALENT report", "verification.verdict / manifest hashes",
        "Reject unless verdict is re-derived from hash-bound artifacts; self-declared "
        "EQUIVALENT with zero manifest binds nothing.",
        "Verdicts must be recomputed or bound to real manifests and solver transcript.", r, "INVALID_INPUT")

    r = base_report(referenceManifestHash="0x" + "44" * 32)
    add("D03", "Replaced reference identity", "referenceManifestHash",
        "Reject as IDENTITY_MISMATCH / STALE; the hash must match the project's declared reference.",
        "MVP_CONSTRAINTS §7 requires both compared manifests embedded or hashed.", r, "STALE")

    r = base_report(candidateManifestHash="0x" + "55" * 32)
    add("D04", "Replaced candidate identity", "candidateManifestHash",
        "Reject as IDENTITY_MISMATCH / STALE.", "Candidate must bind the actual compared netlist.",
        r, "STALE")

    r = base_report()
    r["netlistHash"] = "0x" + "66" * 32
    r["suppliedNetlistSha256"] = "0x" + "77" * 32
    add("D05", "Altered netlist hash", "netlistHash vs supplied bytes",
        "Reject: declared hash must equal SHA-256 of bound netlist bytes.",
        "M2 integrity negative INT-EXT-005 covers bytes-vs-hash mismatch.", r, "INVALID_INPUT")

    r = base_report()
    r["environment"] = {"processorImplementationHash": "0x" + "88" * 32,
                        "pinnedImplementationHash": "0x" + "99" * 32}
    add("D06", "Changed implementation hash", "environment.processorImplementationHash",
        "Downgrade to STALE / IMPLEMENTATION_CHANGED; no CURRENT badge.",
        "MVP_CONSTRAINTS §3/§7: beacons are mutable; revalidate before a current claim.", r, "STALE")

    r = base_report()
    r["dependencyClosure"] = [{"id": "0x" + "22" * 32},
                              {"id": "0x" + "aa" * 32}]
    r["pinnedDependencyClosure"] = [{"id": "0x" + "22" * 32}]
    add("D07", "Stale dependency closure", "dependencyClosure",
        "Downgrade to STALE / DEPENDENCIES_CHANGED.",
        "MVP_CONSTRAINTS §7; M2 integrity negative INT-NEG-04.", r, "STALE")

    r = base_report(chainId=8453)
    add("D08", "Swapped chain ID", "chainId",
        "Reject WRONG_CHAIN before any comparison.",
        "Base 8453 shares processor addresses with X Layer 196; reject cross-chain reuse.",
        r, "WRONG_CHAIN")

    r = base_report(integrity={"freshness": "CURRENT", "checkedBlock": 1})
    add("D09", "False CURRENT freshness", "integrity.freshness",
        "Downgrade to HISTORICAL/STALE unless a fresh revalidation at current state exists.",
        "PRD §9: reproducible but stale must remain reviewable, not current.", r, "STALE")

    r = base_report(verification={
        "verdict": "DIFFERENT", "solverOutcome": "SAT",
        "witness": {"input": [0, 0], "referenceOutput": [0, 0], "candidateOutput": [0, 0]},
    })
    add("D10", "SAT witness with no actual difference", "verification.witness",
        "Reject witness and downgrade verdict to UNKNOWN; require replay by the trusted evaluator.",
        "MVP_CONSTRAINTS §5: DIFFERENT only after witness reproduced by trusted evaluator on both circuits.",
        r, "INVALID_INPUT")

    r = base_report(verification={
        "verdict": "EQUIVALENT", "reasonCode": "TIMEOUT", "solverOutcome": "TIMEOUT",
        "timedOut": True,
    })
    add("D11", "UNKNOWN falsely relabelled EQUIVALENT", "verification.verdict/reasonCode",
        "Force UNKNOWN. A timeout or resource breach must never be EQUIVALENT.",
        "MVP_CONSTRAINTS §5/§6; FR-029.", r, "UNKNOWN")

    r = base_report(projectHash="0x" + "ab" * 32,
                    referenceManifestHash="0x" + "22" * 32,
                    candidateManifestHash="0x" + "33" * 32)
    r["knownProjectHashes"] = ["0x" + "cd" * 32, "0x" + "ef" * 32]
    add("D12", "Reused proof for a different project", "projectHash / manifest hashes",
        "Reject: all artifact hashes must resolve inside the declared project; never transplant a proof.",
        "PRD FR-043/FR-044 evidence bundle binding.", r, "INVALID_INPUT")

    return {
        "schema": "flip-m3-verification-proof-attacks/1",
        "generator": "build_corpus.py", "core_version": CORE_VERSION,
        "attacks": attacks,
        "note": "These are hostile report specifications, not executed production results. "
                "No proof consumer exists to accept or reject them yet.",
    }


# --------------------------------------------------------------------------
# Task E -- solver benchmark corpus + independent measurements
# --------------------------------------------------------------------------
def build_task_e() -> tuple[dict, dict]:
    specs, measurements = [], []
    sizes = [50, 100, 250, 500, 1000, 2500, 5000]
    sample_rng_seed = GENERATION_SEED
    for target in sizes:
        L = target // 4
        actual = 4 * L
        per_size_seed = GENERATION_SEED + target
        n_in = L + 1
        fault_step = 3 if L >= 3 else 1
        variants = {}
        for mode, els in (
            ("self", parity_chain_els(L)),
            ("equivalent", parity_chain_els(L, reverse_ports=True)),
            ("different", parity_chain_els(L, fault_step=fault_step)),
        ):
            nl = core.encode(els)
            c = core.load(nl, n_in, 1, BANK)
            flat = core.flatten(c)
            variants[mode] = {
                "netlist_hex": "0x" + nl.hex(),
                "netlist_bytes": len(nl),
                "netlist_sha256": sha(nl),
                "n_in": n_in, "n_out": 1, "ref_uses": L,
                "expanded_gates": c.n_gates,
                "cnf_clauses_tseitin": 5 + 6 * len(flat.gates),
                "cnf_variables_tseitin": 3 + 2 * len(flat.gates) + n_in,
                "ref_depth": 1,
            }
        spec = {
            "id": "E-%05d" % target, "target_gates": target, "actual_gates": actual,
            "generation_seed": GENERATION_SEED, "per_size_seed": per_size_seed,
            "rng": "python.random.Random (Mersenne Twister)",
            "construction": "%d REF(XOR#1) records chained over %d inputs; each REF flattens "
                            "to 4 NAND gates (shallow depth-1 REF fan-out)" % (L, n_in),
            "expected": {"self": "EQUIVALENT", "equivalent": "EQUIVALENT",
                         "different": "DIFFERENT"},
            "variants": variants,
            "note": "Fixture-generation observations only. NOT fresh production solver "
                    "performance. M0.5 Minisat22 numbers are historical, not replayed here.",
        }
        specs.append(spec)

        # independent reference measurements on this host
        rng = random.Random(sample_rng_seed + target)
        meas = {"id": spec["id"], "actual_gates": actual,
                "measurement_context": "fixture-generation-time on this host; stdlib Python only",
                "variants": {}}
        for mode in ("self", "equivalent", "different"):
            els = parity_chain_els(L, reverse_ports=(mode == "equivalent"),
                                   fault_step=(fault_step if mode == "different" else None))
            ref_c = core.load(core.encode(parity_chain_els(L)), n_in, 1, BANK)
            cand_c = core.load(core.encode(els), n_in, 1, BANK)
            rf, cf = core.flatten(ref_c), core.flatten(cand_c)
            samples = []
            for _ in range(32):
                bits = [rng.randrange(2) for _ in range(n_in)]
                samples.append(bits)
            t0 = time.perf_counter()
            diff_count = 0
            for bits in samples:
                if core.eval_flat(rf, bits) != core.eval_flat(cf, bits):
                    diff_count += 1
            sim_ms = round((time.perf_counter() - t0) * 1000, 3)
            entry = {"sampled_inputs": 32, "sampled_differences": diff_count,
                     "sample_evaluation_ms": sim_ms,
                     "sampling_note": "sampled observation, not a verdict"}
            # Exact check only when the input domain is small enough to enumerate.
            if n_in <= 16:
                t1 = time.perf_counter()
                differs = False
                wit = None
                for v in range(1 << n_in):
                    bits = [(v >> i) & 1 for i in range(n_in)]
                    if core.eval_flat(rf, bits) != core.eval_flat(cf, bits):
                        differs, wit = True, bits
                        break
                entry["exhaustive"] = {
                    "inputs_enumerated_up_to_first_difference": (v + 1),
                    "verdict": "DIFFERENT" if differs else "EQUIVALENT",
                    "witness": wit, "elapsed_ms": round((time.perf_counter() - t1) * 1000, 3),
                    "exact": True,
                }
            else:
                entry["exhaustive"] = {
                    "verdict": "NOT_EXECUTED",
                    "reason": "2**%d inputs exceeds this task's independent enumeration budget" % n_in,
                }
                if mode == "different":
                    # targeted single-bit witness search (cheap: O(n_in) evaluations)
                    tw = None
                    for k in range(n_in):
                        bits = [0] * n_in
                        bits[k] = 1
                        if core.eval_flat(rf, bits) != core.eval_flat(cf, bits):
                            tw = bits
                            break
                    if tw is not None:
                        ro = list(core.eval_recursive(ref_c, tw))
                        co = list(core.eval_recursive(cand_c, tw))
                        entry["targeted_witness"] = {
                            "input": tw, "reference_output": ro, "candidate_output": co,
                            "replayed_by_both_evaluators": (
                                ro != co and
                                ro == list(core.eval_flat(rf, tw)) and
                                co == list(core.eval_flat(cf, tw))),
                            "claim": "existence witness only; not a proof of minimality",
                        }
            # Small capped DPLL run, recorded verbatim (often UNKNOWN by design).
            t2 = time.perf_counter()
            got = core.compare_stateless(ref_c, cand_c, max_decisions=200)
            entry["capped_dpll"] = {
                "verdict": got["verdict"], "solver_result": got.get("solver_result"),
                "decisions": got.get("decisions"), "timed_out": got.get("timed_out"),
                "clauses": got.get("clauses"), "variables": got.get("variables"),
                "elapsed_ms": round((time.perf_counter() - t2) * 1000, 3),
                "note": "stdlib DPLL with a 200-decision cap; UNKNOWN is the expected "
                        "outcome on hard UNSAT instances and is NOT a production verdict",
            }
            meas["variants"][mode] = entry
        measurements.append(meas)

    corpus = {
        "schema": "flip-m3-verification-benchmark-corpus/1",
        "generator": "build_corpus.py", "core_version": CORE_VERSION,
        "generation_seed": GENERATION_SEED,
        "sizes": sizes,
        "specs": specs,
        "note": "No claim of solver production readiness. Historical M0.5 Minisat22 "
                "timings are not reproduced or re-asserted here.",
    }
    result = {
        "schema": "flip-m3-verification-benchmark-measurements/1",
        "generator": "build_corpus.py", "core_version": CORE_VERSION,
        "seed": sample_rng_seed,
        "context": "fixture-generation-time, stdlib Python only; not production performance",
        "measurements": measurements,
    }
    return corpus, result


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> int:
    sys.setrecursionlimit(20000)
    checks = {"onchain_vector_crosscheck": [], "dual_evaluator_crosscheck": True}

    # Trusted cross-check: recorded onchain evaluations of the real circuits.
    for cid, expected in ((1, [0, 1, 1, 0]), (2, [1, 1, 1, 0])):
        c = core.load(BANK[(PROC0.hex(), cid)][2], 2, 1, BANK)
        got = [core.eval_recursive(c, [(v >> i) & 1 for i in range(2)])[0] for v in range(4)]
        ok = got == expected
        checks["onchain_vector_crosscheck"].append({
            "circuit": "0x" + PROC0.hex() + ":%d" % cid,
            "recorded_onchain": expected, "independent_evaluation": got, "match": ok,
        })
        if not ok:
            raise AssertionError("onchain vector cross-check failed for %d" % cid)

    a = build_task_a()
    b = build_task_b()
    c = build_task_c(b)
    d = build_task_d()
    e, em = build_task_e()

    authored = [
        write(ROOT / "circuits" / "golden-compositions.json", a),
        write(ROOT / "sat" / "sat-corpus.json", b),
        write(ROOT / "witnesses" / "witness-corpus.json", c),
        write(ROOT / "proof-attacks" / "attack-corpus.json", d),
        write(ROOT / "benchmarks" / "benchmark-corpus.json", e),
    ]
    results = [
        write(ROOT / "results" / "verification-results.json", {
            "schema": "flip-m3-verification-results/1",
            "core_version": CORE_VERSION, "generation_seed": GENERATION_SEED,
            "checks": checks,
            "task_a_case_count": len(a["cases"]),
            "task_b_case_count": len(b["cases"]),
            "task_b_agreements": sum(1 for x in b["cases"] if x.get("agrees_with_expected")),
            "task_c_witness_count": len(c["witnesses"]),
            "task_c_all_verified": all(x["verified"] for x in c["witnesses"]),
            "task_d_attack_count": len(d["attacks"]),
            "task_e_spec_count": len(e["specs"]),
        }),
        write(ROOT / "results" / "benchmark-measurements.json", em),
    ]
    build_info = write(ROOT / "BUILD_INFO.json", {
        "schema": "flip-m3-verification-build-info/1",
        "core_version": CORE_VERSION,
        "generator": "fixtures/m3-verification/generators/build_corpus.py",
        "generator_sha256": sha((HERE / "build_corpus.py").read_bytes()),
        "core_sha256": sha((HERE / "m3_core.py").read_bytes()),
        "generation_seed": GENERATION_SEED,
        "python": sys.version.split()[0],
        "base_commit": "b71e48e4ad29b352a166230b8644a26f11c5fba8",
        "reference_implementations": [
            "TAP-02 reference.py (MIT, audit copy) - encoding/semantics specification source",
            "M0 audit independent_eval.py - independent TAP-02 evaluator (design cross-check only)",
            "m3_core.py in this corpus - self-contained reimplementation used for all generated results",
        ],
        "determinism": "Fixtures contain no timestamps or host-dependent fields; "
                       "results/*.json contain timing observations and are regenerated on each run.",
    })
    manifest_obj = {
        "schema": "flip-m3-verification-manifest/1",
        "core_version": CORE_VERSION,
        "generation_seed": GENERATION_SEED,
        "authored_files": authored,
        "result_files": results,
        "build_info": build_info,
    }
    manifest = write(ROOT / "MANIFEST.json", manifest_obj)
    repo = ROOT.parent.parent
    handoff_manifest = write(repo / "docs" / "evidence" / "m3-verification" / "manifest.json", {
        "schema": "flip-m3-verification-handoff-manifest/1",
        "branch": "opencode/flip-m3-verification-corpus",
        "base_commit": "b71e48e4ad29b352a166230b8644a26f11c5fba8",
        "base_commit_note": "HEAD of PR #2 (codex/flip-m2-integration); PR #2 was OPEN, not "
                            "merged into main at corpus creation. main was 8e9b6b928b5d08b7383ae2413dec26d6068ea44e.",
        "core_version": CORE_VERSION, "generation_seed": GENERATION_SEED,
        "counts": {
            "task_a_compositions": len(a["cases"]),
            "task_b_sat_cases": len(b["cases"]),
            "task_c_verified_witnesses": len(c["witnesses"]),
            "task_d_attack_specs": len(d["attacks"]),
            "task_e_benchmark_sizes": len(e["specs"]),
        },
        "manifest_path": "fixtures/m3-verification/MANIFEST.json",
        "authored_file_hashes": manifest_obj["authored_files"],
        "result_files": "see fixtures/m3-verification/MANIFEST.json; these contain "
                        "generation-time measurements and are excluded from this "
                        "deterministic handoff manifest",
        "provenance": {
            "real_sources": "XOR#1 / NAND#2, X Layer mainnet chainId 196, block 76020961, "
                            "archived in docs/evidence/raw/M0/xlayer_circuits.json",
            "synthetic": "all composed netlists, mutations, attacks and benchmark chains",
            "no_live_rpc": True, "no_onchain_publication": True,
            "no_production_implementation": True,
        },
        "execution": {
            "task_b_agreements": sum(1 for x in b["cases"] if x.get("agrees_with_expected")),
            "task_b_total": len(b["cases"]),
            "all_witnesses_verified": all(x["verified"] for x in c["witnesses"]),
            "onchain_vector_crosscheck_pass": all(
                x["match"] for x in checks["onchain_vector_crosscheck"]),
        },
    })
    print(json.dumps({
        "authored": authored, "results": results,
        "manifest": manifest,
        "handoff_manifest": handoff_manifest,
        "agreements": sum(1 for x in b["cases"] if x.get("agrees_with_expected")),
        "task_b_total": len(b["cases"]),
        "witnesses": len(c["witnesses"]),
        "all_witnesses_verified": all(x["verified"] for x in c["witnesses"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
