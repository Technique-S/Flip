"""Deterministic REF compiler consuming actual validated M2 imports."""

from dataclasses import dataclass

from flip_core import abi
from flip_core.canonical import content_hash
from flip_core.composition_models import LocalProject
from flip_core.contracts import ContractError
from flip_core.execution import Circuit, execution_cost, validated_import
from flip_core.import_models import ImportBudget, ImportResult
from flip_core.importer import key, sha
from flip_core.models import Project
from flip_core.tap02 import decode


def nand(a, b):
    return b"\x00" + a.to_bytes(3, "big") + b.to_bytes(3, "big")


def ref(identity, inputs, outputs):
    if len(inputs) > 255 or not 1 <= outputs <= 255 or int(identity.circuitId) >= 2**64:
        raise ContractError("BAD_NETLIST", "REF interface or ID exceeds native encoding.")
    return (
        b"\x02"
        + bytes.fromhex(identity.processor[2:])
        + int(identity.circuitId).to_bytes(8, "big")
        + bytes((len(inputs), outputs))
        + b"".join(i.to_bytes(3, "big") for i in inputs)
    )


@dataclass(frozen=True)
class Composition:
    project: Project | LocalProject
    imports: dict[str, ImportResult]
    reference: Circuit
    candidate: Circuit
    manifest: dict
    local_reference_manifest: dict | None = None


def compile_project(
    project: Project | LocalProject, imports: list[ImportResult], *, _reference_only=False
) -> Composition:
    project = type(project).model_validate(project.model_dump(mode="json"))
    budget = ImportBudget(maxGates=project.limits.gateCap, maxDepth=project.limits.refDepthCap)
    if len(imports) != len(project.sources):
        raise ContractError("MISSING_REFERENCE", "Exactly one import per source is required.")
    by_hash, circuits = {}, {}
    for imported in imports:
        imported, circuit = validated_import(imported, budget)
        if imported.manifest.block != imports[0].manifest.block:
            raise ContractError("IMPLEMENTATION_CHANGED", "Sources must share one pinned block.")
        expected_environment = imports[0].manifest.root.environment
        for snapshot in [imported.manifest.root, *imported.manifest.dependencies]:
            env = snapshot.environment
            if env.factory.address != abi.FACTORY or (
                env.factory,
                env.factoryImplementationSlot,
                env.factoryImplementation,
                env.factorySealed,
                env.beacon,
                env.beaconImplementation,
            ) != (
                expected_environment.factory,
                expected_environment.factoryImplementationSlot,
                expected_environment.factoryImplementation,
                expected_environment.factorySealed,
                expected_environment.beacon,
                expected_environment.beaconImplementation,
            ):
                raise ContractError(
                    "IMPLEMENTATION_CHANGED", "Inconsistent factory/beacon execution context."
                )
        if imported.manifestHash in by_hash:
            raise ContractError("INVALID_INPUT", "Duplicate source manifest.")
        by_hash[imported.manifestHash] = imported
        circuits[imported.manifestHash] = circuit
    bound, children, closure = {}, {}, {}
    total_bytes = total_records = 0
    for source in project.sources:
        imported = by_hash.get(source.manifestHash)
        if imported is None:
            raise ContractError("MISSING_REFERENCE", "Source manifest not supplied.")
        actual = imported.manifest.root
        if actual.identity != source.identity:
            raise ContractError(
                "INVALID_INPUT", "Source identity differs from actual imported root."
            )
        if (actual.nIn, actual.nOut, actual.nState) != (source.nIn, source.nOut, source.nState):
            raise ContractError("MISSING_MAPPING", "Declared source widths differ from actual I/O.")
        for snapshot in [actual, *imported.manifest.dependencies]:
            identity = key(snapshot.identity)
            if identity in closure and closure[identity] != snapshot:
                raise ContractError(
                    "IMPLEMENTATION_CHANGED", "Conflicting dependency execution identity."
                )
            closure[identity] = snapshot
        for item in imported.circuits:
            total_bytes += len(item.netlist[2:]) // 2
        total_records += sum(
            len(c.decoded.records) for c in _unique_circuits(circuits[source.manifestHash])
        )
        bound[source.alias] = imported
    if total_bytes > budget.maxTotalBytes or total_records > budget.maxTotalRecords:
        raise ContractError("RESOURCE_LIMIT", "Combined source closure budget exceeded.")
    signals = {}
    used = set()
    chunks = []
    cursor, gates, height = 2 + project.candidate.nIn, 0, 0

    def signal(pin):
        return 2 + pin.pin if pin.component is None else signals[pin.component][pin.pin]

    for component in project.candidate.components:
        inputs = [signal(pin) for pin in component.inputs]
        if component.kind == "NAND":
            # Canonical inverter: NAND(x,x) == NAND(x,constant-one). This permits
            # frozen v1 PinSource recipes to reproduce the audited glue bytes.
            chunks.append(nand(inputs[0], 1 if inputs[0] == inputs[1] else inputs[1]))
            width = 1
            gates += 1
        else:
            imported = bound[component.sourceAlias]
            used.update(
                key(s.identity) for s in [imported.manifest.root, *imported.manifest.dependencies]
            )
            source = imported.manifest.root
            child = circuits[imported.manifestHash]
            if child.state_width:
                raise ContractError(
                    "UNSUPPORTED_STATEFUL_PROOF", "Stateful composition is unsupported."
                )
            width = source.nOut
            chunks.append(ref(source.identity, inputs, width))
            children[key(source.identity)] = child
            gates += child.gates
            height = max(height, 1 + _height(child))
        signals[component.instanceId] = list(range(cursor, cursor + width))
        cursor += width
    selected = [signal(pin) for pin in project.candidate.outputs]
    # TAP-02 outputs are the final nOut produced signals. Preserve the audited
    # 81-byte layout when already final; otherwise copy explicitly with NANDs.
    if (
        selected != list(range(cursor - len(selected), cursor))
        or cursor - len(selected) < 2 + project.candidate.nIn
    ):
        gates += 2 * len(selected)
        inverses = []
        for value in selected:
            chunks.append(nand(value, 1))
            inverses.append(cursor)
            cursor += 1
        for value in inverses:
            chunks.append(nand(value, 1))
            cursor += 1
    if gates > budget.maxGates or height > budget.maxDepth:
        raise ContractError("RESOURCE_LIMIT", "Composed gate/depth budget exceeded.")
    raw = b"".join(chunks)
    decoded = decode(raw, project.candidate.nIn, len(selected), budget)
    if (
        len(raw) + total_bytes > budget.maxTotalBytes
        or len(decoded.records) + total_records > budget.maxTotalRecords
    ):
        raise ContractError("RESOURCE_LIMIT", "Composition plus closure budget exceeded.")
    candidate = Circuit(decoded, 0, gates, children)
    execution_cost(candidate)
    manifest = {
        "schemaVersion": "m3-1.0.0",
        "kind": "LOCAL_COMPOSITION",
        "projectHash": content_hash(project),
        "netlistHash": sha(raw),
        "nIn": decoded.n_in,
        "nOut": decoded.n_out,
        "nState": 0,
        "expandedGates": gates,
        "sourceManifestHashes": sorted(by_hash),
        "dependencies": [closure[k].model_dump(mode="json") for k in sorted(used)],
        "semantics": imports[0].manifest.semantics.model_dump(mode="json"),
        "registration": "HISTORICAL_IMPORTED_ASSERTIONS",
        "freshness": "HISTORICAL",
    }
    local_reference = None
    if isinstance(project, LocalProject):
        if _reference_only:
            reference = candidate
        else:
            reference_project = project.model_copy(update={"candidate": project.referenceCandidate})
            reference_composition = compile_project(
                reference_project, imports, _reference_only=True
            )
            reference = reference_composition.candidate
            local_reference = reference_composition.manifest
    else:
        reference = circuits[bound[project.comparison.referenceAlias].manifestHash]
    return Composition(
        project,
        bound,
        reference,
        candidate,
        manifest,
        local_reference,
    )


def _unique_circuits(root):
    found = {}

    def visit(circuit):
        if id(circuit) in found:
            return
        found[id(circuit)] = circuit
        for child in circuit.children.values():
            visit(child)

    visit(root)
    return list(found.values())


def _height(circuit):
    memo = {}

    def visit(c):
        if id(c) not in memo:
            memo[id(c)] = max((1 + visit(child) for child in c.children.values()), default=0)
        return memo[id(c)]

    return visit(circuit)
