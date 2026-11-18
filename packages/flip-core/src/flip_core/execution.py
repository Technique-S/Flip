"""Local TAP-02 execution. No network, labels, or solver code in this evaluator."""

from dataclasses import dataclass
from time import monotonic

from flip_core.canonical import content_hash
from flip_core.contracts import ContractError
from flip_core.import_models import ImportBudget, ImportResult
from flip_core.importer import PinnedReader, Resolved, key
from flip_core.tap02 import Decoded


class Deadline:
    def __init__(self, milliseconds):
        self.end = monotonic() + milliseconds / 1000

    def remaining(self):
        if monotonic() >= self.end:
            raise ContractError("RESOURCE_LIMIT", "Local validation deadline exceeded.")


class SnapshotReader(PinnedReader):
    """Feed M2's exact resolver immutable snapshot bytes, never an RPC fallback.

    Registration/environment are historical assertions from the imported manifest.
    They are content-bound, not independent observations of the blockchain.
    """

    def __init__(self, imported, budget):
        self.budget = budget
        self.rpc = Deadline(budget.deadlineMs)
        self.nodes, self.edges, self.loading = {}, set(), set()
        self.total_bytes = self.total_records = 0
        self.snapshots = {
            key(s.identity): s for s in [imported.manifest.root, *imported.manifest.dependencies]
        }
        self.raw = {key(c.identity): bytes.fromhex(c.netlist[2:]) for c in imported.circuits}

    def environment(self, processor):
        found = [s.environment for k, s in self.snapshots.items() if k[0] == processor]
        if not found:
            raise ContractError("MISSING_REFERENCE", "REF processor absent from imported closure.")
        if any(e != found[0] for e in found):
            raise ContractError("IMPLEMENTATION_CHANGED", "Conflicting processor environments.")
        return found[0]

    def call(self, processor, name, cid=None):
        if name == "nextId":
            return (
                "0x"
                + (max(k[1] for k in self.snapshots if k[0] == processor) + 1).to_bytes(32).hex()
            )
        snapshot = self.snapshots.get((processor, cid))
        if snapshot is None:
            raise ContractError("MISSING_REFERENCE", "REF target absent from imported closure.")
        if name == "circuitInfo":
            return (
                "0x"
                + b"".join(
                    n.to_bytes(32)
                    for n in (snapshot.nIn, snapshot.nOut, snapshot.nState, snapshot.expandedGates)
                ).hex()
            )
        raw = self.raw[(processor, cid)]
        return (
            "0x" + ((32).to_bytes(32) + len(raw).to_bytes(32) + raw + bytes(-len(raw) % 32)).hex()
        )


@dataclass(frozen=True)
class Circuit:
    decoded: Decoded
    state_width: int
    gates: int
    children: dict[tuple[str, int], Circuit]


def validated_import(imported: ImportResult, budget: ImportBudget) -> tuple[ImportResult, Circuit]:
    imported = ImportResult.model_validate(imported.model_dump(mode="json"))
    reader = SnapshotReader(imported, budget)
    root = reader.resolve(imported.manifest.root.identity, (), 0)
    declared = {
        key(s.identity): s for s in [imported.manifest.root, *imported.manifest.dependencies]
    }
    edges = {(key(e.parent), key(e.child)) for e in imported.manifest.edges}
    if declared != {k: n.snapshot for k, n in reader.nodes.items()} or edges != reader.edges:
        raise ContractError("BAD_NETLIST", "Manifest closure/edges disagree with decoded REF data.")
    circuit = resolved_circuit(root, reader.nodes)
    execution_cost(circuit)
    return imported, circuit


def execution_cost(root):
    """Also bound zero-gate REF expansion; gate counts alone are insufficient."""
    memo = {}

    def cost(c):
        if id(c) not in memo:
            value = 2 + c.decoded.n_in + sum(r.outputs + 1 for r in c.decoded.records)
            for r in c.decoded.records:
                if r.opcode == 2:
                    value += cost(c.children[(r.processor, r.circuit_id)])
                if value > 250_000:
                    raise ContractError(
                        "RESOURCE_LIMIT", "Expanded execution signal/work budget exceeded."
                    )
            if value > 250_000:
                raise ContractError(
                    "RESOURCE_LIMIT", "Expanded execution signal/work budget exceeded."
                )
            memo[id(c)] = value
        return memo[id(c)]

    return cost(root)


def resolved_circuit(root: Resolved, nodes) -> Circuit:
    memo = {}

    def build(node):
        identity = content_hash(node.snapshot.identity)
        if identity not in memo:
            children = {
                (r.processor, r.circuit_id): build(nodes[(r.processor, r.circuit_id)])
                for r in node.decoded.records
                if r.opcode == 2
            }
            memo[identity] = Circuit(
                node.decoded, node.snapshot.nState, node.snapshot.expandedGates, children
            )
        return memo[identity]

    return build(root)


def bits_checked(bits, width):
    if len(bits) != width or any(type(b) is not int or b not in (0, 1) for b in bits):
        raise ContractError("INVALID_INPUT", "Bit vector width/value mismatch.")
    return list(bits)


def pack(bits) -> bytes:
    values = bits_checked(bits, len(bits))
    raw = bytearray((len(values) + 7) // 8)
    for index, bit in enumerate(values):
        raw[index // 8] |= bit << (index % 8)
    return bytes(raw)


def unpack(raw: bytes, width: int) -> list[int]:
    if type(width) is not int or not 0 <= width <= 65536 or type(raw) is not bytes:
        raise ContractError("INVALID_INPUT", "Invalid packed bit vector.")
    return [(raw[i // 8] >> (i % 8)) & 1 if i // 8 < len(raw) else 0 for i in range(width)]


def evaluate(circuit: Circuit, inputs) -> list[int]:
    if circuit.state_width:
        raise ContractError("UNSUPPORTED_STATEFUL_PROOF", "Stateless evaluation requires nState=0.")
    return beat(circuit, [], inputs)[1]


def beat(circuit: Circuit, state, inputs) -> tuple[list[int], list[int]]:
    """Isolated sequential primitive for official vector parity, not a proof API."""
    state = bits_checked(state, circuit.state_width)
    values = [0, 1, *bits_checked(inputs, circuit.decoded.n_in)]
    next_state = list(state)
    latches = []
    cursor = 0
    for record in circuit.decoded.records:
        if record.opcode == 0:
            a, b = (values[i] for i in record.inputs)
            values.append(1 - (a & b))
        elif record.opcode == 1:
            values.append(state[cursor])
            latches.append((cursor, record.inputs[0]))
            cursor += 1
        else:
            child = circuit.children[(record.processor, record.circuit_id)]
            child_state, outputs = beat(
                child,
                state[cursor : cursor + child.state_width],
                [values[i] for i in record.inputs],
            )
            next_state[cursor : cursor + child.state_width] = child_state
            cursor += child.state_width
            values.extend(outputs)
    for position, signal in latches:
        next_state[position] = values[signal]
    return next_state, values[-circuit.decoded.n_out :]
