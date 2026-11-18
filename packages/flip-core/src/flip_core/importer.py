"""Pinned X Layer importer and bounded REF DAG inspection. No evaluator."""

import hashlib
from dataclasses import dataclass

from pydantic import TypeAdapter

from flip_core import __version__, abi
from flip_core.canonical import content_hash
from flip_core.contracts import ContractError
from flip_core.import_models import CircuitBytes, ImportBudget, ImportResult
from flip_core.integrity import ContentCache, compare_manifests
from flip_core.models import (
    Block,
    CircuitIdentity,
    CodeIdentity,
    Dependency,
    Environment,
    Integrity,
    Manifest,
    Quantity,
    Semantics,
    Snapshot,
)
from flip_core.rpc import RpcClient, RpcSettings, quantity
from flip_core.tap02 import Decoded, decode


def sha(data: bytes) -> str:
    return "0x" + hashlib.sha256(data).hexdigest()


def key(identity: CircuitIdentity) -> tuple[str, int]:
    return identity.processor, int(identity.circuitId)


@dataclass(frozen=True)
class Resolved:
    snapshot: Snapshot
    decoded: Decoded
    height: int


class ImportService:
    def __init__(
        self,
        settings: RpcSettings | None = None,
        budget: ImportBudget | None = None,
        transport=None,
        cache=None,
    ):
        self.settings = settings or RpcSettings()
        self.budget = ImportBudget.model_validate(
            (budget or ImportBudget()).model_dump(mode="json")
        )
        self.transport = transport
        self.cache = cache if cache is not None else ContentCache()

    def revalidate(self, manifest: Manifest):
        previous = Manifest.model_validate(manifest.model_dump(mode="json"))
        fresh, prior_canonical = self._import(previous.root.identity, None, previous.block)
        result = compare_manifests(previous, fresh, block_changed=not prior_canonical)
        if result.changes:
            self.cache.mark_stale(result.previousManifestHash)
        return result

    def import_circuit(
        self, identity: CircuitIdentity, block_number: str | None = None
    ) -> ImportResult:
        return self._import(identity, block_number, None)[0]

    def _import(
        self, identity: CircuitIdentity, block_number: str | None, prior_block: Block | None
    ):
        # Revalidate typed input even if a caller mutated a previously validated object.
        identity = CircuitIdentity.model_validate(identity.model_dump(mode="json"))
        if block_number is not None:
            TypeAdapter(Quantity).validate_python(block_number)
        with RpcClient(self.settings, self.budget, self.transport) as rpc:
            reader = PinnedReader(rpc, self.budget, block_number)
            resolved = reader.resolve(identity, (), 0)
            prior_canonical = (
                prior_block is None or reader.header(hex(int(prior_block.number))) == prior_block
            )
            reader.finish()
            nodes = sorted(reader.nodes.values(), key=lambda n: key(n.snapshot.identity))
            semantics = Semantics(
                **{
                    name: field.annotation.__args__[0]
                    for name, field in Semantics.model_fields.items()
                }
            )
            manifest = Manifest(
                schemaVersion="1.0.0",
                chainId=196,
                block=reader.block,
                root=resolved.snapshot,
                dependencies=[
                    n.snapshot for n in nodes if key(n.snapshot.identity) != key(identity)
                ],
                edges=[
                    Dependency(
                        parent=reader.nodes[p].snapshot.identity,
                        child=reader.nodes[c].snapshot.identity,
                    )
                    for p, c in sorted(reader.edges)
                ],
                semantics=semantics,
                toolVersion=__version__,
                observation="SINGLE_RPC",
            )
            result = ImportResult(
                schemaVersion="1.0.0",
                kind="CIRCUIT_IMPORT",
                manifest=manifest,
                manifestHash=content_hash(manifest),
                circuits=[
                    CircuitBytes(
                        identity=n.snapshot.identity, netlist="0x" + n.decoded.original.hex()
                    )
                    for n in nodes
                ],
                integrity=Integrity(
                    freshness="HISTORICAL" if block_number is not None else "CURRENT",
                    checkedBlock=reader.block,
                ),
                pinning="NUMBER_WITH_HEADER_RECHECK",
                trust="SINGLE_RPC_OBSERVATION",
            )
            self.cache.put(result)
            rpc.remaining()
            return result, prior_canonical


class PinnedReader:
    def __init__(self, rpc: RpcClient, budget: ImportBudget, block_number: str | None):
        self.rpc, self.budget = rpc, budget
        self._chain()
        tag = "latest" if block_number is None else hex(int(block_number))
        self.block = self.header(tag)
        self.tag = hex(int(self.block.number))
        self.nodes: dict[tuple[str, int], Resolved] = {}
        self.edges: set[tuple[tuple[str, int], tuple[str, int]]] = set()
        self.environments: dict[str, Environment] = {}
        self.codes: dict[str, CodeIdentity] = {}
        self.total_bytes = self.total_records = 0
        self.loading: set[tuple[str, int]] = set()
        factory = self.code(abi.FACTORY)
        slot = self.storage(abi.FACTORY, abi.IMPLEMENTATION_SLOT)
        implementation = self.code(abi.address(slot))
        self.beacon = self.code(abi.address(self.call(abi.FACTORY, "circuitBeacon")))
        beacon_impl = self.code(abi.address(self.call(self.beacon.address, "implementation")))
        sealed = abi.uint(self.call(abi.FACTORY, "isSealed"))
        if sealed not in (0, 1):
            raise abi.malformed("Invalid ABI boolean.")
        self.shared_environment = dict(
            factory=factory,
            factoryImplementationSlot=slot,
            factoryImplementation=implementation,
            factorySealed=bool(sealed),
            beacon=self.beacon,
            beaconImplementation=beacon_impl,
        )

    def _chain(self):
        if quantity(self.rpc.call("eth_chainId", [])) != 196:
            raise ContractError("WRONG_CHAIN", "RPC chainId is not X Layer mainnet 196.")

    def header(self, tag: str) -> Block:
        data = self.rpc.call("eth_getBlockByNumber", [tag, False])
        if not isinstance(data, dict) or "number" not in data or "hash" not in data:
            raise abi.malformed("Missing block identity.")
        number = quantity(data["number"])
        if tag != "latest" and number != int(tag, 16):
            raise abi.malformed("RPC returned a different block.")
        raw = abi.hex_bytes(data["hash"], 32)
        if len(raw) != 32:
            raise abi.malformed("Invalid block hash.")
        return Block(number=str(number), hash="0x" + raw.hex())

    def finish(self):
        self._chain()
        if self.header(self.tag) != self.block:
            raise ContractError(
                "IMPLEMENTATION_CHANGED",
                "Pinned block changed during import; retry from a new snapshot.",
            )

    def call(self, address: str, name: str, argument=None):
        return self.rpc.call(
            "eth_call", [{"to": address, "data": abi.calldata(name, argument)}, self.tag]
        )

    def storage(self, address: str, slot: str) -> str:
        raw = self.rpc.call("eth_getStorageAt", [address, slot, self.tag])
        abi.uint(raw)
        return raw.lower()

    def code(self, address: str) -> CodeIdentity:
        if address not in self.codes:
            raw = abi.hex_bytes(self.rpc.call("eth_getCode", [address, self.tag]), 250_000)
            if not raw:
                raise ContractError("INVALID_INPUT", "Expected contract has empty code.")
            self.codes[address] = CodeIdentity(address=address, codeHash=sha(raw))
        return self.codes[address]

    def environment(self, processor: str) -> Environment:
        if processor not in self.environments:
            registered = abi.uint(self.call(abi.FACTORY, "isCPU", processor))
            if registered != 1:
                raise ContractError(
                    "INVALID_INPUT", "Processor is not registered with the X Layer factory."
                )
            if abi.address(self.call(processor, "factory")) != abi.FACTORY:
                raise ContractError("INVALID_INPUT", "Processor belongs to a different factory.")
            if abi.address(self.storage(processor, abi.BEACON_SLOT)) != self.beacon.address:
                raise ContractError("INVALID_INPUT", "Unsupported processor beacon identity.")
            self.environments[processor] = Environment(
                **self.shared_environment, processorCodeHash=self.code(processor).codeHash
            )
        return self.environments[processor]

    def resolve(self, identity: CircuitIdentity, path: tuple, depth: int) -> Resolved:
        self.rpc.remaining()
        identity_key = key(identity)
        if depth > self.budget.maxDepth:
            raise ContractError("REF_DEPTH_EXCEEDED", "REF depth budget exceeded.")
        if identity_key in path:
            raise ContractError("BAD_NETLIST", "Dependency cycle detected.")
        if identity_key in self.nodes:
            node = self.nodes[identity_key]
            if depth + node.height > self.budget.maxDepth:
                raise ContractError("REF_DEPTH_EXCEEDED", "REF depth budget exceeded.")
            return node
        if len(self.nodes) + len(self.loading) >= self.budget.maxCircuits:
            raise ContractError("RESOURCE_LIMIT", "Dependency circuit budget exceeded.")
        self.loading.add(identity_key)
        environment = self.environment(identity.processor)
        cid = int(identity.circuitId)
        if cid < 1 or cid >= abi.uint(self.call(identity.processor, "nextId")):
            raise ContractError("INVALID_INPUT", "Circuit ID does not exist.")
        n_in, n_out, state, gates = abi.info(self.call(identity.processor, "circuitInfo", cid))
        if gates > self.budget.maxGates or state > 2**24:
            raise ContractError("RESOURCE_LIMIT", "Declared expanded gate/state budget exceeded.")
        raw = abi.dynamic_bytes(
            self.call(identity.processor, "netlist", cid), self.budget.maxNetlistBytes
        )
        decoded = decode(raw, n_in, n_out, self.budget)
        self.total_bytes += len(raw)
        self.total_records += len(decoded.records)
        if (
            self.total_bytes > self.budget.maxTotalBytes
            or self.total_records > self.budget.maxTotalRecords
        ):
            raise ContractError("RESOURCE_LIMIT", "Total closure byte/record budget exceeded.")
        computed_gates, computed_state, height = decoded.local_gates, decoded.local_state, 0
        for record in decoded.records:
            if record.opcode != 2:
                continue
            child_id = CircuitIdentity(
                schemaVersion="1.0.0",
                chainId=196,
                processor=record.processor,
                circuitId=str(record.circuit_id),
            )
            child = self.resolve(child_id, (*path, identity_key), depth + 1)
            if (child.snapshot.nIn, child.snapshot.nOut) != (len(record.inputs), record.outputs):
                raise ContractError("BAD_NETLIST", "REF arity does not match the target circuit.")
            self.edges.add((identity_key, key(child_id)))
            computed_gates += child.snapshot.expandedGates
            computed_state += child.snapshot.nState
            height = max(height, 1 + child.height)
            if computed_gates > self.budget.maxGates or computed_state > 2**24:
                raise ContractError("RESOURCE_LIMIT", "Expanded gate/state budget exceeded.")
        if (computed_gates, computed_state) != (gates, state):
            raise ContractError(
                "BAD_NETLIST", "circuitInfo disagrees with decoded dependency counts."
            )
        node = Resolved(
            Snapshot(
                identity=identity,
                netlistHash=sha(raw),
                nIn=n_in,
                nOut=n_out,
                nState=state,
                expandedGates=gates,
                environment=environment,
            ),
            decoded,
            height,
        )
        self.nodes[identity_key] = node
        self.loading.remove(identity_key)
        return node
