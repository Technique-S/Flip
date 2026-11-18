"""Bounded TAP-02 structural decoding only. No simulation or composition."""

from dataclasses import dataclass

from flip_core.contracts import ContractError
from flip_core.import_models import ImportBudget


@dataclass(frozen=True)
class Record:
    opcode: int
    inputs: tuple[int, ...]
    processor: str | None = None
    circuit_id: int = 0
    outputs: int = 1


@dataclass(frozen=True)
class Decoded:
    original: bytes
    n_in: int
    n_out: int
    records: tuple[Record, ...]
    local_gates: int
    local_state: int


def decode(data: bytes, n_in: int, n_out: int, budget: ImportBudget) -> Decoded:
    if type(data) is not bytes:
        raise ContractError("BAD_NETLIST", "Netlist must be exact bytes.")
    if len(data) > budget.maxNetlistBytes:
        raise ContractError("RESOURCE_LIMIT", "Netlist byte budget exceeded.")
    if (
        type(n_in) is not int
        or type(n_out) is not int
        or not (0 <= n_in <= 65536 and 1 <= n_out <= 65536)
    ):
        raise ContractError("BAD_NETLIST", "Invalid TAP-02 input/output counts.")
    offset, signal, local_gates, local_state = 0, 2 + n_in, 0, 0
    records: list[Record] = []

    def take(size: int) -> bytes:
        nonlocal offset
        if offset + size > len(data):
            raise ContractError("BAD_NETLIST", "Truncated TAP-02 record.")
        value = data[offset : offset + size]
        offset += size
        return value

    while offset < len(data):
        if len(records) >= budget.maxRecords:
            raise ContractError("RESOURCE_LIMIT", "Record budget exceeded.")
        opcode = take(1)[0]
        if opcode in (0, 1):
            raw = take(6 if opcode == 0 else 3)
            inputs = tuple(int.from_bytes(raw[i : i + 3], "big") for i in range(0, len(raw), 3))
            record = Record(opcode, inputs)
            local_gates += 1
            local_state += opcode
        elif opcode == 2:
            header = take(30)
            ni, no = header[28], header[29]
            if no == 0:
                raise ContractError("BAD_NETLIST", "REF has no outputs.")
            raw = take(3 * ni)  # bounded by the u8 count, checked before tuple allocation
            inputs = tuple(int.from_bytes(raw[i : i + 3], "big") for i in range(0, len(raw), 3))
            record = Record(
                2, inputs, "0x" + header[:20].hex(), int.from_bytes(header[20:28], "big"), no
            )
        else:
            raise ContractError("BAD_NETLIST", "Unknown TAP-02 opcode.")
        if opcode != 1 and any(index >= signal for index in inputs):
            raise ContractError("BAD_NETLIST", "NAND/REF contains a forward signal reference.")
        signal += record.outputs
        if signal > 2**24 or local_gates > budget.maxGates:
            raise ContractError("RESOURCE_LIMIT", "Signal/gate budget exceeded.")
        records.append(record)
    if signal < 2 + n_in + n_out:
        raise ContractError("BAD_NETLIST", "Too few produced signals for outputs.")
    if any(r.opcode == 1 and r.inputs[0] >= signal for r in records):
        raise ContractError("BAD_NETLIST", "LATCH d is out of range.")
    return Decoded(data, n_in, n_out, tuple(records), local_gates, local_state)
