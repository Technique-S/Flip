"""Content-bound historical cache and fresh full-closure manifest revalidation."""

from collections import OrderedDict
from threading import Lock

from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.import_models import ImportResult, RevalidationResult
from flip_core.models import Integrity, Manifest


class ContentCache:
    def __init__(self, max_bytes: int = 8_388_608, max_entries: int = 16):
        if (
            type(max_bytes) is not int
            or type(max_entries) is not int
            or min(max_bytes, max_entries) < 1
        ):
            raise ValueError("invalid cache budget")
        self.max_bytes, self.max_entries = max_bytes, max_entries
        self._entries: OrderedDict[str, bytes] = OrderedDict()
        self._size = 0
        self._stale: set[str] = set()
        self._lock = Lock()

    def put(self, result: ImportResult) -> None:
        result = ImportResult.model_validate(result.model_dump(mode="json"))
        raw = canonical_bytes(result)
        if len(raw) > self.max_bytes:
            return
        digest = result.manifestHash
        with self._lock:
            previous = self._entries.pop(digest, b"")
            self._size -= len(previous)
            self._entries[digest] = raw
            self._size += len(raw)
            while self._size > self.max_bytes or len(self._entries) > self.max_entries:
                evicted_key, evicted = self._entries.popitem(last=False)
                self._size -= len(evicted)
                self._stale.discard(evicted_key)

    def mark_stale(self, digest: str) -> None:
        with self._lock:
            if digest in self._entries:
                self._stale.add(digest)

    def get(self, digest: str) -> ImportResult | None:
        with self._lock:
            raw = self._entries.get(digest)
            stale = digest in self._stale
        if raw is None:
            return None
        result = ImportResult.model_validate(load_json(raw))
        # Cache retrieval is historical, even if the original RPC observation was current.
        return result.model_copy(
            update={
                "integrity": Integrity(
                    freshness="STALE" if stale else "HISTORICAL", checkedBlock=result.manifest.block
                )
            }
        )


def compare_manifests(
    previous: Manifest, fresh: ImportResult, *, block_changed: bool = False
) -> RevalidationResult:
    """Compare against an independently imported closure, never a user freshness flag."""
    current = fresh.manifest
    changes = set()
    if block_changed:
        changes.add("BLOCK_CHANGED")
    if previous.root.identity != current.root.identity:
        changes.add("ROOT_CHANGED")
    old = {content_hash(s.identity): s for s in [previous.root, *previous.dependencies]}
    new = {content_hash(s.identity): s for s in [current.root, *current.dependencies]}
    if old.keys() != new.keys() or previous.edges != current.edges:
        changes.add("DEPENDENCIES_CHANGED")
    if previous.semantics != current.semantics:
        changes.add("SEMANTICS_CHANGED")
    for digest in old.keys() & new.keys():
        a, b = old[digest], new[digest]
        if a.netlistHash != b.netlistHash:
            changes.add("NETLIST_CHANGED")
        if (a.nIn, a.nOut, a.nState, a.expandedGates) != (b.nIn, b.nOut, b.nState, b.expandedGates):
            changes.add("INTERFACE_CHANGED")
        ea, eb = a.environment, b.environment
        if (ea.factory, ea.factoryImplementationSlot, ea.factoryImplementation) != (
            eb.factory,
            eb.factoryImplementationSlot,
            eb.factoryImplementation,
        ):
            changes.add("FACTORY_IMPLEMENTATION_CHANGED")
        if (ea.beacon, ea.beaconImplementation) != (eb.beacon, eb.beaconImplementation):
            changes.add("BEACON_IMPLEMENTATION_CHANGED")
        if ea.processorCodeHash != eb.processorCodeHash:
            changes.add("PROCESSOR_CODE_CHANGED")
        if ea.factorySealed != eb.factorySealed:
            changes.add("ENVIRONMENT_CHANGED")
    return RevalidationResult(
        schemaVersion="1.0.0",
        kind="MANIFEST_REVALIDATION",
        previousManifestHash=content_hash(previous),
        observed=fresh,
        integrity=Integrity(
            freshness="STALE" if changes else fresh.integrity.freshness, checkedBlock=current.block
        ),
        changes=sorted(changes),
    )
