"""M3-B byte fixtures -> real production boundaries, synthetic transport only.

No corpus evaluator or archived verdict is used to compute production results.
The existing deterministic M2 transport supplies registry/environment assertions;
synthetic circuit identities here are never blockchain observations.
"""

import copy
import json
from pathlib import Path

from flip_core.cnf import miter
from flip_core.composition import ref
from flip_core.execution import evaluate, validated_import
from flip_core.import_models import ImportBudget
from flip_core.isolation import run_worker
from flip_core.models import Limits
from flip_core.tap02 import decode
from flip_core.verification import parse_request
from test_m2_import import PROC as PROC
from test_m2_import import FakeChain, identity
from test_m3_engine import pin, ref_component, request_for, source

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "fixtures/m3-verification"
SYNTH = "0x" + "11" * 20
BUDGET = ImportBudget(maxGates=5000, maxCircuits=1251, maxRequests=8192)


def load(relative, key):
    return json.loads((CORPUS / relative).read_bytes())[key]


GOLD = load("circuits/golden-compositions.json", "cases")
SAT = load("sat/sat-corpus.json", "cases")
WITNESSES = load("witnesses/witness-corpus.json", "witnesses")
ATTACKS = load("proof-attacks/attack-corpus.json", "attacks")
BENCHMARKS = load("benchmarks/benchmark-corpus.json", "specs")


def bank():
    result = {
        (s["processor"], s["circuit_id"]): (
            s["n_in"],
            s["n_out"],
            bytes.fromhex(s["netlist_hex"][2:]),
        )
        for s in GOLD[0]["source_circuits"]
    }
    # A06's explicit synthetic wrapper reproduction recipe, not a live circuit.
    result[(SYNTH, 1)] = (2, 1, ref(identity(1), [2, 3], 1))
    return result


def dimensions(spec):
    properties = spec.get("properties", spec)
    return properties["n_in"], properties["n_out"]


def import_fixture(spec, *, cid=9000, overrides=None, missing=()):
    ni, no = dimensions(spec)
    records = bank()
    records.update(overrides or {})
    for target in missing:
        records.pop(target, None)
    root = (SYNTH, cid)
    records[root] = ni, no, bytes.fromhex(spec["netlist_hex"][2:])
    chain = FakeChain()
    chain.nodes.clear()
    counts = {}

    def count(target, path=()):
        if target not in records or target in path:
            return 0, 0  # resolver, not this adapter, rejects missing/cyclic REFs
        if target in counts:
            return counts[target]
        n_in, n_out, raw = records[target]
        decoded = decode(raw, n_in, n_out, BUDGET)
        gates, state = decoded.local_gates, decoded.local_state
        for record in decoded.records:
            if record.opcode == 2:
                child_gates, child_state = count(
                    (record.processor, record.circuit_id), (*path, target)
                )
                gates += child_gates
                state += child_state
        counts[target] = gates, state
        return gates, state

    # Install only the reachable fixture nodes; malformed decode rejection here
    # is itself the production TAP-02 boundary, not an independent oracle.
    count(root)
    for target in counts:
        n_in, n_out, raw = records[target]
        gates, state = counts[target]
        chain.nodes[target] = ((n_in, n_out, state, gates), raw)
    chain.unregistered.update(
        processor for processor, _ in records if not any(cpu == processor for cpu, _ in chain.nodes)
    )
    # Missing target below nextId is an exact known no-circuit RPC rejection.
    original = chain.handler

    def handler(request):
        import httpx
        from flip_core import abi

        payload = json.loads(request.content)
        if payload["method"] == "eth_call":
            call = payload["params"][0]
            data = call["data"]
            if data[2:10] in (abi.SELECTORS["circuitInfo"], abi.SELECTORS["netlist"]):
                target = call["to"], int(data[10:], 16)
                if target not in chain.nodes:
                    return httpx.Response(
                        200,
                        json={
                            "jsonrpc": "2.0",
                            "id": payload["id"],
                            "error": {"code": -32000, "message": "no circuit"},
                        },
                    )
        return original(request)

    chain.handler = handler
    imported = chain.service(maxGates=5000, maxCircuits=1251, maxRequests=8192).import_circuit(
        identity(cid, SYNTH)
    )
    return imported, validated_import(imported, BUDGET)[1]


def pair_request(reference, candidate):
    a, _ = import_fixture(reference)
    b, _ = import_fixture(candidate, cid=9001)
    ni, no = dimensions(candidate)
    component = ref_component("candidate", "candidate", [pin(None, i) for i in range(ni)])
    return request_for(
        None, a, [component], [pin("candidate", i) for i in range(no)], ni, [("candidate", b)]
    )


def recipe(spec):
    """Lossless recipe for native backward REF/NAND wiring supported by v1 pins.

    Constants in general REF inputs have no frozen recipe pin representation;
    such fixtures instead use the production imported-circuit wrapper boundary.
    """
    ni, no = dimensions(spec)
    decoded = decode(bytes.fromhex(spec["netlist_hex"][2:]), ni, no, BUDGET)
    signals = {i + 2: pin(None, i) for i in range(ni)}
    components, targets = [], {}
    cursor = 2 + ni
    for i, record in enumerate(decoded.records):
        name = f"node{i}"
        ins = record.inputs
        if record.opcode == 0 and 1 in ins and ins != (1, 1):
            other = ins[1] if ins[0] == 1 else ins[0]
            inputs = [signals[other], signals[other]]
        else:
            if any(signal < 2 for signal in ins):
                raise ValueError("Use imported-circuit boundary for constant REF/constant circuits")
            inputs = [signals[signal] for signal in ins]
        if record.opcode == 2:
            target = record.processor, record.circuit_id
            alias = f"source{len(targets)}" if target not in targets else targets[target]
            targets[target] = alias
            component = ref_component(name, alias, inputs)
        else:
            component = {"kind": "NAND", "instanceId": name, "inputs": inputs}
        components.append(component)
        for output in range(record.outputs):
            signals[cursor + output] = pin(name, output)
        cursor += record.outputs
    return {
        "nIn": ni,
        "components": components,
        "outputs": [signals[i] for i in range(cursor - no, cursor)],
    }, targets


def recipe_request(reference, candidate):
    a, targets_a = recipe(reference)
    b, targets_b = recipe(candidate)
    # Renumber aliases consistently across both independent recipes.
    targets = {
        target: f"source{i}" for i, target in enumerate(sorted(targets_a.keys() | targets_b.keys()))
    }
    for design, names in ((a, targets_a), (b, targets_b)):
        inverse = {alias: targets[target] for target, alias in names.items()}
        for component in design["components"]:
            if component["kind"] == "REF":
                component["sourceAlias"] = inverse[component["sourceAlias"]]
    imports, sources = [], []
    for (processor, cid), alias in targets.items():
        ni, no, raw = bank()[(processor, cid)]
        # Preserve actual source identities rather than importing a new wrapper.
        chain = FakeChain()
        chain.nodes[(SYNTH, 1)] = ((2, 1, 0, 4), bank()[(SYNTH, 1)][2])
        value = chain.service(maxGates=5000).import_circuit(identity(cid, processor))
        assert (
            next(c.netlist for c in value.circuits if c.identity == value.manifest.root.identity)
            == "0x" + raw.hex()
        )
        imports.append(value.model_dump(mode="json"))
        sources.append(source(alias, value))
    return parse_request(
        {
            "schemaVersion": "m3-1.0.0",
            "kind": "M3_EXECUTION",
            "relation": "BEHAVIORAL",
            "imports": imports,
            "project": {
                "schemaVersion": "m3-1.0.0",
                "projectId": "independentCorpus",
                "chainId": 196,
                "toolVersion": "0.1.0",
                "sources": sources,
                "referenceCandidate": a,
                "candidate": b,
                "comparison": {
                    "kind": "PAIRWISE_EQUIVALENCE",
                    "referenceAlias": None,
                    "intent": "UNDECLARED",
                    "trustAssertion": None,
                    "inputMap": list(range(a["nIn"])),
                    "outputMap": list(range(len(a["outputs"]))),
                },
                "limits": Limits(gateCap=5000).model_dump(mode="json"),
            },
        }
    )


def case_request(case):
    if case["id"] in ("B09", "B10"):
        return pair_request(case["reference"], case["candidate"])
    return recipe_request(case["reference"], case["candidate"])


def separate_context_comparison(reference, candidate, *, overrides):
    _, a = import_fixture(reference)
    _, b = import_fixture(candidate, cid=9001, overrides=overrides)
    enc, inputs = miter(a, b, list(range(a.decoded.n_in)), list(range(a.decoded.n_out)))
    result = run_worker(enc.clauses, inputs, Limits(gateCap=5000))
    if result["outcome"] == "SAT":
        bits = result["witness"]
        assert evaluate(a, bits) != evaluate(b, bits)
    return result, a, b


def attack_claim(attack, good, request):
    """Apply the attack's meaning to a valid bound report; don't repair original bytes."""
    claim = copy.deepcopy(good)
    report = claim["report"]
    fake = "0x" + "ab" * 32
    number = int(attack["id"][1:])
    if number == 1:
        report["inputMap"] = []
        report["verification"].update(
            verdict="EQUIVALENT",
            solverOutcome="UNSAT",
            witness=None,
            reasonCode=None,
            sourceValidation="PASSED",
            mappingValidation="PASSED",
        )
    elif number in (2, 11):
        report["verification"].update(
            verdict="EQUIVALENT",
            solverOutcome="UNSAT",
            witness=None,
            reasonCode=None,
            sourceValidation="PASSED",
            mappingValidation="PASSED",
        )
    elif number == 3:
        report["referenceManifestHash"] = fake
    elif number == 4:
        report["candidateManifestHash"] = fake
    elif number == 5:
        claim["candidateManifest"]["netlistHash"] = fake
    elif number == 6:
        claim["candidateManifest"]["dependencies"][0]["environment"]["beaconImplementation"][
            "codeHash"
        ] = fake
    elif number == 7:
        claim["candidateManifest"]["dependencies"].pop()
    elif number == 8:
        report["chainId"] = 8453
    elif number == 9:
        report["integrity"] = {
            "freshness": "CURRENT",
            "checkedBlock": request.imports[0].manifest.block.model_dump(mode="json"),
        }
    elif number == 10:
        # Outputs claimed to differ remain schema-valid, but [1,1] does not
        # distinguish the B15 XOR->NAND substitution / selected D10 baseline.
        report["verification"]["witness"]["inputs"]["bits"] = "11"
    elif number == 12:
        report["projectHash"] = fake
    return claim
