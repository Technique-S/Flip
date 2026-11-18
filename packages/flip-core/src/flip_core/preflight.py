"""Read-only TAP-02 structural probe against a freshly checked X Layer snapshot."""

from flip_core import abi
from flip_core.canonical import content_hash
from flip_core.composition import compile_project
from flip_core.contracts import ContractError
from flip_core.import_models import ImportBudget
from flip_core.importer import PinnedReader, key
from flip_core.models import Preflight
from flip_core.rpc import RpcClient, RpcSettings

CALLER = "0x000000000000000000000000000000000000f00d"
# M0.5 Gate A implementation, bound to the code identity in the M2 live capture.
IMPLEMENTATION = "0x0a5259a8b5a69197cde6dce70a4446fe807b622277bdae9e79919d5d8e9828a5"
PROXY = "0x2ea683e275cbe6e51928a9bdefe80b6ff6a6a6e8535436bbe7eea02ee18306ae"


def word(value):
    return value.to_bytes(32, "big")


def abi_bytes(raw):
    return word(len(raw)) + raw + bytes(-len(raw) % 32)


def classify(raw, local_gates):
    if len(raw) == 132 and raw[:4].hex() == "03dee4c5":
        sender, balance, needed, token = (
            int.from_bytes(raw[i : i + 32]) for i in range(4, 132, 32)
        )
        if sender == int(CALLER, 16) and balance < needed == local_gates and token == 0:
            return "STRUCTURALLY_ACCEPTED", None, "KNOWN_BURN_STAGE"
    for reason in (b"REF: pin mismatch", b"NAND: future signal", b"bad opcode"):
        if raw == bytes.fromhex("08c379a0") + word(32) + abi_bytes(reason):
            return "REJECTED", "STRUCTURAL_REJECTION", "KNOWN_STRUCTURAL_REJECTION"
    return "UNKNOWN", "UNRECOGNIZED_REVERT", "UNRECOGNIZED"


class StructuralReader(RpcClient):
    def probe(self, target, tag, circuit):
        decoded = circuit.decoded
        fee = abi.uint(self._read("eth_call", [{"to": target, "data": "0xadfb2b69"}, tag]))
        arguments = (
            word(96) + word(decoded.n_in) + word(decoded.n_out) + abi_bytes(decoded.original)
        )
        call = {
            "to": target,
            "from": CALLER,
            "value": hex(fee),
            "data": "0x7bd3ac1d" + arguments.hex(),
        }
        # Synthetic balance only inside eth_call, for the fixed caller and exact fee.
        reply = self._read(
            "eth_call", [call, tag, {CALLER: {"balance": hex(fee)}}], capture_revert=True
        )
        data = reply.get("revert") if isinstance(reply, dict) else None
        return fee, abi.hex_bytes(data, 4096) if isinstance(data, str) else b""


def preflight(request, settings=None, transport=None):
    design = compile_project(request.project, request.imports)
    target = request.project.sources[0].identity.processor
    result = dict(
        schemaVersion="1.0.0",
        chainId=196,
        mode="READ_ONLY_ETH_CALL",
        candidateNetlistHash=design.manifest["netlistHash"],
        manifestHash=content_hash(design.manifest),
        status="UNKNOWN",
        reasonCode="RPC_UNAVAILABLE",
        observation=None,
        integrity={"freshness": "UNVERIFIED", "checkedBlock": None},
    )
    budget = ImportBudget(
        maxGates=request.project.limits.gateCap, maxDepth=request.project.limits.refDepthCap
    )
    try:
        with StructuralReader(settings or RpcSettings.from_environment(), budget, transport) as rpc:
            reader = PinnedReader(rpc, budget, None)
            prior = request.imports[0].manifest.block
            if reader.header(hex(int(prior.number))) != prior:
                raise ContractError(
                    "IMPLEMENTATION_CHANGED", "Source block is no longer canonical."
                )
            for imported in request.imports:
                root = imported.manifest.root
                reader.resolve(root.identity, (), 0)
                for old in [root, *imported.manifest.dependencies]:
                    node = reader.nodes.get(key(old.identity))
                    if node is None or node.snapshot != old:
                        raise ContractError("IMPLEMENTATION_CHANGED", "Source closure has changed.")
            env = reader.environment(target)
            if (
                env.beaconImplementation.codeHash != IMPLEMENTATION
                or env.processorCodeHash != PROXY
            ):
                raise ContractError(
                    "IMPLEMENTATION_CHANGED", "Unreviewed structural validator implementation."
                )
            fee, data = rpc.probe(target, reader.tag, design.candidate)
            reader.finish()
            status, reason, classification = classify(data, design.candidate.decoded.local_gates)
            result.update(
                status=status,
                reasonCode=reason,
                integrity={"freshness": "CURRENT", "checkedBlock": reader.block},
                observation=dict(
                    block=reader.block,
                    feeWei=str(fee),
                    manifestRevalidated=True,
                    revertData="0x" + data.hex(),
                    classification=classification,
                ),
            )
    except ContractError as exc:
        result["reasonCode"] = exc.code
        if exc.code == "IMPLEMENTATION_CHANGED":
            result["integrity"]["freshness"] = "STALE"
    return Preflight.model_validate(result).model_dump(mode="json")
