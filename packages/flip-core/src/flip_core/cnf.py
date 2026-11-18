"""Bounded Tseitin NAND/REF expansion, independent from local evaluation."""

from dataclasses import dataclass, field

from flip_core.contracts import ContractError


@dataclass
class Encoder:
    variables: int = 0
    clauses: list[list[int]] = field(default_factory=list)

    def fresh(self):
        self.variables += 1
        if self.variables > 150_000:
            raise ContractError("RESOURCE_LIMIT", "CNF variable budget exceeded.")
        return self.variables

    def add(self, *clauses):
        if len(self.clauses) + len(clauses) > 300_000:
            raise ContractError("RESOURCE_LIMIT", "CNF clause budget exceeded.")
        self.clauses.extend(clauses)

    def circuit(self, circuit, inputs, constants):
        if circuit.state_width:
            raise ContractError("UNSUPPORTED_STATEFUL_PROOF", "Only stateless CNF is supported.")
        values = [*constants, *inputs]
        for record in circuit.decoded.records:
            if record.opcode == 0:
                a, b = [values[i] for i in record.inputs]
                y = self.fresh()
                self.add([a, y], [b, y], [-a, -b, -y])
                values.append(y)
            elif record.opcode == 2:
                values.extend(
                    self.circuit(
                        circuit.children[(record.processor, record.circuit_id)],
                        [values[i] for i in record.inputs],
                        constants,
                    )
                )
            else:
                raise ContractError(
                    "UNSUPPORTED_STATEFUL_PROOF", "LATCH cannot enter stateless CNF."
                )
        return values[-circuit.decoded.n_out :]


def miter(reference, candidate, input_map, output_map):
    if (
        reference.decoded.n_in != candidate.decoded.n_in
        or reference.decoded.n_out != candidate.decoded.n_out
        or sorted(input_map) != list(range(reference.decoded.n_in))
        or sorted(output_map) != list(range(reference.decoded.n_out))
    ):
        raise ContractError(
            "MISSING_MAPPING", "Actual circuit interfaces require complete bijections."
        )
    enc = Encoder()
    zero, one = enc.fresh(), enc.fresh()
    enc.add([-zero], [one])
    inputs = [enc.fresh() for _ in range(candidate.decoded.n_in)]
    a = enc.circuit(reference, [inputs[i] for i in input_map], (zero, one))
    b = enc.circuit(candidate, inputs, (zero, one))
    differences = []
    for index, mapped in enumerate(output_map):
        x, y = a[index], b[mapped]
        d = enc.fresh()
        enc.add([-d, x, y], [-d, -x, -y], [d, -x, y], [d, x, -y])
        differences.append(d)
    enc.add(differences)
    return enc, inputs
