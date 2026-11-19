"""Independent corpus bytes -> production decoder, M2 import and M3 project contracts.

No fixture evaluator or expected verdict is used to construct a production result.
Synthetic registry/environment reads reuse the existing offline M2 transport.
"""

import json
from pathlib import Path

from flip_core.composition import nand, ref
from flip_core.import_models import ImportBudget
from flip_core.models import Limits
from flip_core.tap02 import decode
from flip_core.verification import parse_request
from test_m2_import import FakeChain, identity
from test_m3_engine import add_node, imported, pin, source

ROOT = Path(__file__).resolve().parents[3]
CORPUS = ROOT / "fixtures/m45-debugging"
CASES = json.loads((CORPUS / "cases/debugging-corpus.json").read_bytes())["cases"]
GUIDANCE = json.loads((CORPUS / "diagnostics/correction-guidance.json").read_bytes())["suggestions"]


def bank():
    # Exact declared dependency recipes in the frozen build_corpus.py BANK.
    result = {}
    for cpu, cid, pairs in (
        ("aa", 1, [(2, 3), (2, 4), (3, 4), (5, 6)]),
        ("bb", 2, [(2, 3)]),
        ("cc", 3, [(2, 3), (4, 4)]),
        ("dd", 4, [(2, 2), (3, 3), (4, 5)]),
        ("ee", 5, [(3, 3), (2, 4), (5, 5)]),
    ):
        result[("0x" + cpu * 20, cid)] = (2, 1, b"".join(nand(a, b) for a, b in pairs))
    for cpu, order in (("11", [2, 3]), ("12", [3, 2])):
        raw = ref(identity(5, "0x" + "ee" * 20), order, 1)
        raw += ref(identity(3, "0x" + "cc" * 20), [2, 3], 1)
        result[("0x" + cpu * 20, 10 if cpu == "11" else 11)] = (2, 2, raw)
    return result


def execution(case):
    chain = FakeChain()
    chain.nodes.clear()
    declared = bank()
    for (cpu, cid), (ni, no, raw) in declared.items():
        add_node(chain, cid, raw, ni, no, cpu)
    decoded = {
        side: decode(
            bytes.fromhex(case[side]["netlistHex"][2:]),
            case[side]["nIn"],
            case[side]["nOut"],
            ImportBudget(maxGates=5000),
        )
        for side in ("reference", "candidate")
    }
    used = sorted(
        {
            (r.processor, r.circuit_id)
            for net in decoded.values()
            for r in net.records
            if r.opcode == 2
        }
    )
    used = used or [
        next(iter(declared))
    ]  # M3 requires a pinned import, even for NAND-only designs.
    imports = [imported(chain, identity(cid, cpu)) for cpu, cid in used]
    aliases = {key: f"source{i}" for i, key in enumerate(used)}

    def design(side):
        net = decoded[side]
        signals = {i + 2: pin(None, i) for i in range(net.n_in)}
        components, cursor = [], 2 + net.n_in
        for index, record in enumerate(net.records):
            name = f"element{index}"
            inputs = list(record.inputs)
            if record.opcode == 0 and 1 in inputs:
                # Frozen PinSource has no constants: NAND(x,1) == NAND(x,x).
                inputs = [s for s in inputs if s != 1] * 2
            pins = [signals[s] for s in inputs]
            component = dict(
                kind="REF" if record.opcode == 2 else "NAND", instanceId=name, inputs=pins
            )
            if record.opcode == 2:
                component["sourceAlias"] = aliases[(record.processor, record.circuit_id)]
            components.append(component)
            for output in range(record.outputs):
                signals[cursor + output] = pin(name, output)
            cursor += record.outputs
        return dict(
            nIn=net.n_in,
            components=components,
            outputs=[signals[s] for s in case[side]["outputMap"]],
        )

    trusted = case["intentOracle"] == "DECLARED_PRIOR_MAPPING"
    return parse_request(
        dict(
            schemaVersion="m3-1.0.0",
            kind="M3_EXECUTION",
            relation="PREVIOUS_VERSION" if trusted else "BEHAVIORAL",
            imports=[i.model_dump(mode="json") for i in imports],
            project=dict(
                schemaVersion="m3-1.0.0",
                projectId=case["caseId"],
                chainId=196,
                toolVersion="0.1.0",
                sources=[
                    source(aliases[key], value) for key, value in zip(used, imports, strict=True)
                ],
                candidate=design("candidate"),
                referenceCandidate=design("reference"),
                comparison=dict(
                    kind="PAIRWISE_EQUIVALENCE",
                    referenceAlias=None,
                    intent="TRUSTED_REFERENCE" if trusted else "UNDECLARED",
                    trustAssertion="Declared synthetic prior mapping; not a chain observation"
                    if trusted
                    else None,
                    inputMap=list(range(case["candidate"]["nIn"])),
                    outputMap=list(range(case["candidate"]["nOut"])),
                ),
                limits=Limits(gateCap=5000).model_dump(mode="json"),
            ),
        )
    )


def request(case):
    return dict(
        schemaVersion="m45-debugging-1.0.0",
        kind="DEBUG_REQUEST",
        executionRequest=execution(case).model_dump(mode="json"),
    )
