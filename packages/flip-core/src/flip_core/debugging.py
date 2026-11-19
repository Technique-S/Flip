"""Deterministic bounded signal cones and explicit, reference-relative candidate replay.

Cone membership is structural relevance, never causation or a unique faulty wire.
Every verdict comes from M3's trusted comparator and independently replayed witness.
No supplied report, alias or archived diagnostic is consumed as proof.
"""

from copy import deepcopy
from pathlib import Path

from pydantic import ValidationError

from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.composition import compile_project
from flip_core.composition_models import LocalProject
from flip_core.contracts import ContractError
from flip_core.debugging_models import (
    CandidateAction,
    Connection,
    Correction,
    DebugRequest,
    DebugResult,
    Edit,
    TraceBudget,
)
from flip_core.execution import Deadline
from flip_core.importer import sha
from flip_core.verification import compare, mapped_outputs, parse_request


def stable_comparison(value):
    return {k: v for k, v in value.items() if k not in ("resources", "verifiedAt")}


class ConeTracer:
    def __init__(self, budget: TraceBudget):
        self.budget = budget
        self.deadline = Deadline(budget.deadlineMs)
        self.nodes = self.indexed = 0
        self.connections = {}

    def edge(self, scope, side, ref, kind, signal, destination, *, source_scope=None, **fields):
        key = side, ref
        if key not in self.connections:
            if len(self.connections) >= self.budget.maxConnections:
                raise ContractError("RESOURCE_LIMIT", "Connection trace budget exceeded.")
            source = source_scope or scope
            self.connections[key] = Connection(
                side=side,
                path=scope["path"],
                connectionRef=ref,
                kind=kind,
                sourceSignal=signal,
                sourcePath=source["path"],
                sourceNetlistHash=source["hash"],
                sourceIdentity=source["identity"],
                destination=destination,
                netlistHash=scope["hash"],
                identity=scope["identity"],
                **fields,
            )

    def scope(self, circuit, path, parent=None, record=None, index=None, identity=None):
        depth = path.count("/ref[")
        if depth > self.budget.maxDepth:
            raise ContractError("REF_DEPTH_EXCEEDED", "Diagnostic REF depth exceeded.")
        if circuit.state_width:
            raise ContractError("UNSUPPORTED_STATEFUL_PROOF", "Diagnostics require stateless nets.")
        producers, cursor = {}, 2 + circuit.decoded.n_in
        self.indexed += cursor
        if self.indexed > self.budget.maxIndexedSignals:
            raise ContractError("RESOURCE_LIMIT", "Diagnostic indexing budget exceeded.")
        for i, item in enumerate(circuit.decoded.records):
            self.deadline.remaining()
            if self.indexed + item.outputs > self.budget.maxIndexedSignals:
                raise ContractError("RESOURCE_LIMIT", "Diagnostic indexing budget exceeded.")
            for pin in range(item.outputs):
                producers[cursor + pin] = i, pin
            cursor += item.outputs
            self.indexed += item.outputs
        return dict(
            hash=sha(circuit.decoded.original),
            circuit=circuit,
            path=path,
            parent=parent,
            record=record,
            index=index,
            identity=identity,
            producers=producers,
            end=cursor,
        )

    def trace(self, circuit, output_pins, side, design=None, identity=None):
        if len(output_pins) > self.budget.maxNodes:
            raise ContractError("RESOURCE_LIMIT", "Too many diagnostic output roots.")
        root = self.scope(circuit, "top", identity=identity)
        scopes, stack, visited = {"top": root}, [], set()
        for pin in output_pins:
            signal = root["end"] - circuit.decoded.n_out + pin
            self.edge(
                root,
                side,
                f"top/outputMap[{pin}]",
                "OUTPUT_MAP",
                signal,
                f"output[{pin}]",
                outputPin=pin,
                projectPin=design.outputs[pin] if design else None,
            )
            stack.append((root, signal))
        while stack:
            self.deadline.remaining()
            scope, signal = stack.pop()
            mark = scope["path"], signal
            if mark in visited:
                continue
            if self.nodes >= self.budget.maxNodes:
                raise ContractError("RESOURCE_LIMIT", "Diagnostic traversal budget exceeded.")
            visited.add(mark)
            self.nodes += 1
            path, net = scope["path"], scope["circuit"]
            if signal < 2:
                continue
            if signal < 2 + net.decoded.n_in:
                if scope["parent"] is not None:
                    pin, parent, item = signal - 2, scope["parent"], scope["record"]
                    index = scope["index"]
                    component = (
                        design.components[index]
                        if parent is root and design and index < len(design.components)
                        else None
                    )
                    self.edge(
                        parent,
                        side,
                        f"{parent['path']}/element[{index}].in[{pin}]",
                        "REF_INPUT",
                        item.inputs[pin],
                        f"{path}/input[{pin}]",
                        elementIndex=index,
                        inputPin=pin,
                        instanceId=component.instanceId if component else None,
                        projectPin=component.inputs[pin] if component else None,
                    )
                    stack.append((parent, item.inputs[pin]))
                continue
            index, output_pin = scope["producers"][signal]
            item = net.decoded.records[index]
            component = (
                design.components[index]
                if scope is root and design and index < len(design.components)
                else None
            )
            if item.opcode == 0:
                for pin, source in enumerate(item.inputs):
                    self.edge(
                        scope,
                        side,
                        f"{path}/element[{index}].in[{pin}]",
                        "NAND",
                        source,
                        f"{path}/element[{index}].in[{pin}]",
                        elementIndex=index,
                        inputPin=pin,
                        outputPin=output_pin,
                        instanceId=component.instanceId if component else None,
                        projectPin=component.inputs[pin] if component else None,
                    )
                    stack.append((scope, source))
            else:
                child_path = f"{path}/ref[{index}]"
                if child_path not in scopes:
                    scopes[child_path] = self.scope(
                        net.children[(item.processor, item.circuit_id)],
                        child_path,
                        scope,
                        item,
                        index,
                        dict(
                            schemaVersion="1.0.0",
                            chainId=196,
                            processor=item.processor,
                            circuitId=str(item.circuit_id),
                        ),
                    )
                child = scopes[child_path]
                child_signal = child["end"] - child["circuit"].decoded.n_out + output_pin
                self.edge(
                    scope,
                    side,
                    f"{path}/element[{index}].out[{output_pin}]",
                    "REF_OUTPUT",
                    child_signal,
                    f"{path}/element[{index}].out[{output_pin}]",
                    source_scope=child,
                    elementIndex=index,
                    outputPin=output_pin,
                    instanceId=component.instanceId if component else None,
                )
                stack.append((child, child_signal))


def prior_action(request):
    """A declared local reference permits a proposal, never an inferred intended wiring."""
    project = request.project
    if not isinstance(project, LocalProject) or request.relation == "BEHAVIORAL":
        return None
    before, after = project.candidate, project.referenceCandidate

    def shape(design):
        return [(c.instanceId, c.kind, getattr(c, "sourceAlias", None)) for c in design.components]

    if before.nIn != after.nIn or shape(before) != shape(after):
        return None
    edits = []
    for a, b in zip(before.components, after.components, strict=True):
        if len(a.inputs) != len(b.inputs):
            return None
        for pin, (old, new) in enumerate(zip(a.inputs, b.inputs, strict=True)):
            if old != new:
                edits.append(Edit(location=f"{a.instanceId}.in[{pin}]", before=old, after=new))
    # The comparison alignment itself remains unchanged; do not silently change the oracle.
    for i, mapped in enumerate(project.comparison.outputMap):
        old, new = before.outputs[mapped], after.outputs[i]
        if old != new:
            edits.append(Edit(location=f"output[{mapped}]", before=old, after=new))
    if not edits or len(edits) > 10000:
        return None
    raw = request.model_dump(mode="json")
    raw["project"]["candidate"] = after.model_dump(mode="json")
    for i, mapped in enumerate(project.comparison.outputMap):
        raw["project"]["candidate"]["outputs"][mapped] = after.outputs[i].model_dump(mode="json")
    revised = parse_request(raw)
    compile_project(revised.project, revised.imports)
    return CandidateAction(
        actionId=content_hash(
            {"original": content_hash(request), "revision": content_hash(revised)}
        ),
        title="Test the declared reference mappings",
        reasoning="Restore the declared local reference's numeric mappings in a separate revision. "
        "This is a candidate action, not evidence that any individual connection is defective.",
        edits=edits,
        proposedRevision=revised,
    )


def execute(raw):
    try:
        encoded = raw.encode("utf-8") if isinstance(raw, str) else raw
        if not isinstance(encoded, bytes):
            encoded = canonical_bytes(encoded)
        if len(encoded) > 1_048_576:
            raise ContractError("RESOURCE_LIMIT", "Diagnostic input exceeds 1 MiB.")
        request = DebugRequest.model_validate(
            load_json(raw) if isinstance(raw, (str, bytes)) else raw
        )
    except ContractError:
        raise
    except (ValueError, TypeError, ValidationError, RecursionError) as exc:
        raise ContractError(
            "INVALID_INPUT", "Invalid versioned diagnostic request or structure."
        ) from exc
    execution = request.executionRequest
    deadline = Deadline(request.budget.operationDeadlineMs)
    original = deepcopy(execution.model_dump(mode="json"))
    result = DebugResult(
        classification="UNKNOWN",
        attribution="UNKNOWN_NO_ATTRIBUTION",
        reasoning="Insufficient evidence for attribution.",
        projectHash=content_hash(execution.project),
        executionHash=content_hash(execution),
        diagnosticEngineHash=content_hash(
            {
                name: sha(Path(__file__).with_name(name).read_bytes())
                for name in ("debugging.py", "debugging_models.py")
            }
        ),
    )
    try:
        size = sum(len(c.netlist[2:]) // 2 for i in execution.imports for c in i.circuits)
        members = sum(len(i.circuits) for i in execution.imports)
        if (
            size > request.budget.maxCircuitBytes
            or members > request.budget.maxCircuits
            or len(execution.imports) > 64
        ):
            raise ContractError("RESOURCE_LIMIT", "Diagnostic aggregate source budget exceeded.")
        deadline.remaining()
        if request.operation == "diagnose" and request.actionId is not None:
            raise ContractError(
                "INVALID_INPUT", "Action IDs require explicit correction verification."
            )
        if any(i.integrity.freshness not in ("HISTORICAL", "CURRENT") for i in execution.imports):
            raise ContractError(
                "IMPLEMENTATION_CHANGED", "Stale or unverified imports cannot diagnose."
            )
        composition = compile_project(execution.project, execution.imports)
        if (
            composition.candidate.gates + composition.reference.gates
            > request.budget.maxExpandedGates
        ):
            raise ContractError("RESOURCE_LIMIT", "Diagnostic expanded-gate budget exceeded.")
        deadline.remaining()
        comparison = compare(execution)
        deadline.remaining()
        result.comparison = stable_comparison(comparison)
        proof = comparison["report"]["verification"]
        if proof["verdict"] == "UNKNOWN":
            raise ContractError(
                proof["reasonCode"] or "INCONCLUSIVE", "Comparison is inconclusive."
            )
        if proof["verdict"] == "EQUIVALENT":
            if request.operation == "verify-correction":
                raise ContractError(
                    "INVALID_INPUT", "An equivalent design has no correction action."
                )
            result.classification = "NO_FAULT_ATTRIBUTION"
            result.attribution = "NO_FAULT_ATTRIBUTION"
            result.reasoning = (
                "The selected stateless designs are equivalent. No faults are attributed."
            )
        else:
            witness = proof["witness"]
            bits = list(map(int, witness["inputs"]["bits"]))
            reference, candidate = mapped_outputs(composition, bits)
            if (
                reference == candidate
                or reference != list(map(int, witness["referenceOutputs"]["bits"]))
                or candidate != list(map(int, witness["candidateOutputs"]["bits"]))
            ):
                raise ContractError("WITNESS_REPLAY_FAILED", "Diagnostic witness replay failed.")
            differing = [
                i for i, (a, b) in enumerate(zip(reference, candidate, strict=True)) if a != b
            ]
            tracer = ConeTracer(request.budget)
            tracer.trace(
                composition.candidate,
                [execution.project.comparison.outputMap[i] for i in differing],
                "candidate",
                execution.project.candidate,
            )
            reference_design = getattr(execution.project, "referenceCandidate", None)
            reference_identity = comparison["referenceIdentity"]
            tracer.trace(
                composition.reference,
                differing,
                "reference",
                reference_design,
                reference_identity if "processor" in reference_identity else None,
            )
            result.differingOutputBits = differing
            result.connections = [tracer.connections[k] for k in sorted(tracer.connections)]
            result.nodesVisited, result.indexedSignals = tracer.nodes, tracer.indexed
            result.classification = "VERIFIED_DIFFERENCE"
            result.attribution = "AMBIGUOUS_MULTIPLE_CAUSES"
            result.reasoning = (
                "The trusted evaluator replayed the mismatch. These connections lie "
                "in its structural signal cones; relevance does not prove a defective connection. "
                "Causes remain ambiguous. Scope: selected reference, "
                "pinned historical snapshots only."
            )
            action = prior_action(execution)
            deadline.remaining()
            if action:
                result.actions = [action]
                if len(action.edits) == 1:
                    result.attribution = "SUSPECTED_CANDIDATE"
            if request.operation == "verify-correction":
                if action is None or request.actionId != action.actionId:
                    raise ContractError(
                        "INVALID_INPUT", "Correction does not match a bound candidate action."
                    )
                revised = parse_request(action.proposedRevision.model_dump(mode="json"))
                # Both the original and revision are recompiled through M2's validated snapshot
                # resolver. Sources, closure, hashes, reference and comparison intent cannot change.
                compile_project(revised.project, revised.imports)
                checked = compare(revised)
                deadline.remaining()
                verdict = checked["report"]["verification"]["verdict"]
                result.correction = Correction(
                    classification="VERIFIED_CORRECTION"
                    if verdict == "EQUIVALENT"
                    else "UNKNOWN"
                    if verdict == "UNKNOWN"
                    else "CANDIDATE_ACTION",
                    actionId=action.actionId,
                    originalProjectHash=content_hash(execution.project),
                    revisedProjectHash=content_hash(revised.project),
                    comparison=stable_comparison(checked),
                    revalidation="PINNED_IDENTITIES_HASHES_AND_CLOSURE_REPLAYED",
                    scope="EXACT_STATELESS_SELECTED_REFERENCE_HISTORICAL",
                )
    except ContractError as exc:
        result.classification = "UNKNOWN"
        result.attribution = "UNKNOWN_NO_ATTRIBUTION"
        result.reasonCode, result.reasoning = exc.code, exc.message
        result.connections, result.actions, result.differingOutputBits = [], [], []
        result.correction = None
        result.comparison = None
    if execution.model_dump(mode="json") != original:
        raise RuntimeError("Diagnostic operation mutated its input")
    result.semanticHash = content_hash(result.model_dump(mode="json", exclude={"semanticHash"}))
    return DebugResult.model_validate(result.model_dump(mode="json"))
