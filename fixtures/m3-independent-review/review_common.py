"""Shared helpers for the independent Flip M3 review.

This module lives in OpenCode's owned review fixture directory. It imports
production code read-only (never edits it) and two independently written TAP-02
evaluators: ``independent_core`` (OpenCode M3-B) and the archived official
``tap02_reference_official`` (MIT).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent                  # worktree root
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "packages" / "flip-core" / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import independent_core as ic  # noqa: E402
import tap02_reference_official as official  # noqa: E402
from flip_core.canonical import content_hash  # noqa: E402
from flip_core.composition import compile_project  # noqa: E402
from flip_core.verification import (  # noqa: E402
    ComparisonReport,
    consume,
    execute,
    parse_request,
)


def base_request():
    """Fresh copy of the accepted offline half-adder sample request."""
    from make_m3_sample import sample
    return sample()


def run(op, req):
    """Call the real production engine over canonical bytes."""
    raw = json.dumps(req.model_dump(mode="json"), sort_keys=True, separators=(",", ":")).encode()
    return execute(op, raw)


# --------------------------------------------------------------------------
# project mutations used as adversarial inputs
# --------------------------------------------------------------------------
def ext(pin):
    return {"component": None, "pin": pin}


def comp(name, pin):
    return {"component": name, "pin": pin}


def swap_outputs(req):
    r = copy.deepcopy(req)
    outs = r.project.candidate.outputs
    r.project.candidate.outputs = [outs[1], outs[0]]
    return r


def reversed_refs(req):
    r = copy.deepcopy(req)
    for component in r.project.candidate.components:
        if component.kind == "REF":
            component.inputs = [component.inputs[1], component.inputs[0]]
    return r


def glue_wrong(req):
    r = copy.deepcopy(req)
    for component in r.project.candidate.components:
        if component.kind == "NAND":
            component.inputs = [ext(0), ext(0)]
    return r


def extra_output(req):
    """Add a third output (raw NAND) to exercise multi-output miters."""
    r = copy.deepcopy(req)
    outs = list(r.project.candidate.outputs)
    outs.append(comp("nand0", 0))
    r.project.candidate.outputs = outs
    r.project.comparison.outputMap = [0, 1, 2]
    # reference must expose the same width: use LocalProject reference candidate
    ref = copy.deepcopy(r.project.candidate)
    r.project.referenceCandidate = ref
    return r


def permuted_output_map(req):
    r = copy.deepcopy(req)
    outs = list(r.project.candidate.outputs)
    # candidate emits (sum, carry); reference still emits (carry, sum).
    r.project.candidate.outputs = [outs[1], outs[0]]
    # map reference output 0 -> candidate output 1 and vice versa
    r.project.comparison.outputMap = [1, 0]
    return r


def permuted_input_map(req):
    r = copy.deepcopy(req)
    # both designs read the reversed external pair and the map names that reversal.
    r.project.candidate.components[0].inputs = [ext(1), ext(0)]
    r.project.candidate.components[2].inputs = [ext(1), ext(0)]
    r.project.referenceCandidate.components[0].inputs = [ext(1), ext(0)]
    r.project.referenceCandidate.components[2].inputs = [ext(1), ext(0)]
    r.project.comparison.inputMap = [1, 0]
    return r


def zero_input(req):
    """Two zero-input constant circuits via LocalProject reference candidate."""
    r = copy.deepcopy(req)
    design = {
        "nIn": 0,
        "components": [{"kind": "NAND", "instanceId": "a", "inputs": [ext(0), ext(0)]}],
        "outputs": [comp("a", 0)],
    }
    r.project.candidate = design
    r.project.referenceCandidate = design
    r.project.comparison.inputMap = []
    r.project.comparison.outputMap = [0]
    return r


def zero_input_different(req):
    r = zero_input(req)
    r.project.referenceCandidate = {
        "nIn": 0,
        "components": [{"kind": "NAND", "instanceId": "a", "inputs": [comp("a", 0), comp("a", 0)]}],
        "outputs": [comp("a", 0)],
    }
    return r


# --------------------------------------------------------------------------
# independent circuit conversion + exhaustive ground truth
# --------------------------------------------------------------------------
def _children_bank(circuit):
    """(processor, cid) -> (nIn, nOut, bytes) for every production child."""
    bank = {}

    def visit(c):
        for (proc, cid), child in c.children.items():
            key = (proc.lower().removeprefix("0x"), cid)
            if key not in bank:
                bank[key] = (child.decoded.n_in, child.decoded.n_out, child.decoded.original)
                visit(child)
    visit(circuit)
    return bank


def production_to_independent(circuit):
    """Build OpenCode independent_core Circuit over the production netlist bytes."""
    bank = _children_bank(circuit)
    return ic.load(circuit.decoded.original, circuit.decoded.n_in, circuit.decoded.n_out, bank)


def production_to_official(circuit):
    bank = {}

    def resolve(cpu, cid):
        # Official reference passes cpu as 20 raw bytes; production keys carry 0x.
        raw = cpu.hex() if isinstance(cpu, (bytes, bytearray)) else cpu.lower().removeprefix("0x")
        key = (raw, cid)
        if key not in bank:
            child = circuit.children[("0x" + raw, cid)]
            bank[key] = production_to_official(child)
        return bank[key]
    return official.load(
        circuit.decoded.original, circuit.decoded.n_in, circuit.decoded.n_out, resolve
    )


def exhaustive_ground_truth(req, max_bits=12):
    """Return independent verdict over the full input domain (small n only)."""
    parsed = parse_request(req.model_dump(mode="json"))
    composition = compile_project(parsed.project, parsed.imports)
    ref = production_to_independent(composition.reference)
    cand = production_to_independent(composition.candidate)
    plan = parsed.project.comparison
    n = parsed.project.candidate.nIn
    if n > max_bits:
        return {"verdict": "NOT_COMPUTED", "reason": "nIn too large for exhaustive oracle",
                "n_in": n}
    ref_official = production_to_official(composition.reference)
    cand_official = production_to_official(composition.candidate)
    first = None
    for v in range(1 << n):
        bits = [(v >> i) & 1 for i in range(n)]
        a = ic.eval_recursive(ref, [bits[i] for i in plan.inputMap])
        b = ic.eval_recursive(cand, bits)
        b = [b[i] for i in plan.outputMap]
        # cross-check official evaluator on both sides
        ao = official.beat(ref_official, [], [bits[i] for i in plan.inputMap])[1]
        bo = official.beat(cand_official, [], bits)[1]
        bo = [bo[i] for i in plan.outputMap]
        if tuple(a) != tuple(ao) or tuple(b) != tuple(bo):
            raise AssertionError("independent evaluator disagreement at %s" % bits)
        if tuple(a) != tuple(b) and first is None:
            first = {"input": bits, "reference": list(a), "candidate": list(b)}
    return {
        "verdict": "DIFFERENT" if first else "EQUIVALENT",
        "n_in": n, "inputs_enumerated": 1 << n,
        "distinguishing_input": first,
        "reference_gates": composition.reference.gates,
        "candidate_gates": composition.candidate.gates,
        "netlist_hash": composition.manifest["netlistHash"],
    }


def replay_witness_independently(req, witness):
    """Replay a production witness with both independent evaluators."""
    parsed = parse_request(req.model_dump(mode="json"))
    composition = compile_project(parsed.project, parsed.imports)
    ref = production_to_independent(composition.reference)
    cand = production_to_independent(composition.candidate)
    plan = parsed.project.comparison
    bits = [int(b) for b in witness["inputs"]["bits"]]
    a = list(ic.eval_recursive(ref, [bits[i] for i in plan.inputMap]))
    b = [ic.eval_recursive(cand, bits)[i] for i in plan.outputMap]
    a_off = list(official.beat(production_to_official(composition.reference), [],
                               [bits[i] for i in plan.inputMap])[1])
    b_off = [official.beat(production_to_official(composition.candidate), [], bits)[1][i]
             for i in plan.outputMap]
    return {
        "input": bits, "reference_out": a, "candidate_out": b,
        "official_reference_out": a_off, "official_candidate_out": b_off,
        "differs": a != b,
        "both_independent_evaluators_agree": (a == a_off and b == b_off),
        "matches_production_witness": (
            list(witness["referenceOutputs"]["bits"]) == a
            and list(witness["candidateOutputs"]["bits"]) == b),
    }


def consume_request(req, claimed, project_hash=None, reference_hash=None):
    return {
        "schemaVersion": "m3-1.0.0",
        "kind": "M3_CONSUMPTION",
        "executionRequest": req.model_dump(mode="json"),
        "claimedResult": claimed,
        "expectedProjectHash": project_hash or content_hash(req.project),
        "expectedReferenceHash": reference_hash or claimed["report"]["referenceManifestHash"],
    }
