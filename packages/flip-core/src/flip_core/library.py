"""Read-only, bounded library operations shared by HTTP, CLI and browser storage.

Persisted catalog data is advisory and always historical. Full M2 import is the
only path to executable input. No catalog field can bypass that boundary.
"""

from collections.abc import Callable

from flip_core import abi
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.contracts import ContractError
from flip_core.import_models import ImportBudget
from flip_core.importer import ImportService, PinnedReader
from flip_core.library_models import (
    Catalog,
    Cursor,
    Favorite,
    LibraryIdentity,
    LibraryRecord,
    LibraryRequest,
    LibraryResult,
    Recent,
    display_text,
)
from flip_core.library_models_v1 import LibraryRequest as RequestV1
from flip_core.library_models_v1 import LibraryResult as ResultV1
from flip_core.models import Block, CircuitIdentity
from flip_core.rpc import RpcClient, RpcSettings

SOURCE_ORDER = ["FACTORY_ENUMERATION", "KNOWN_SEED", "USER_IMPORT", "USER_FAVORITE_ONLY"]
MAX_CATALOG_BYTES = 786_432


def compact(catalog):
    if len(canonical_bytes(catalog.overlay)) > MAX_CATALOG_BYTES // 2:
        raise ContractError("RESOURCE_LIMIT", "User metadata storage quota exceeded.")
    while len(canonical_bytes(catalog)) > MAX_CATALOG_BYTES and catalog.records:
        catalog.records.pop(0)


def historical(catalog: Catalog) -> Catalog:
    value = Catalog.model_validate(catalog.model_dump(mode="json"))
    # Caller-provided observations never grant CURRENT, even in the same session.
    return value


def merge_record(catalog: Catalog, record: LibraryRecord):
    prior = next((r for r in catalog.records if r.key == record.key), None)
    if prior:
        record.sources = [s for s in SOURCE_ORDER if s in prior.sources + record.sources]
        catalog.records.remove(prior)
    elif len(catalog.records) >= 1000:
        catalog.records.pop(0)  # Favorites are stored independently and never evicted here.
    catalog.records.append(record)
    compact(catalog)


def seed_catalog() -> Catalog:
    # Verified research seed addresses; hints only. No historical count used for enumeration.
    block = Block(
        number="76277110", hash="0x1941877104961218ad35b6650582da1bf23fdd4628105cc984e731bb6b7910dc"
    )
    catalog = Catalog()
    for proc, ids in (
        ("0x839bdd6fa7a66416a609a735e11de5411b98574e", [None, "1", "2"]),
        ("0x0565ea48ca41ae559d8d491dbb0a9ec945db551b", [None]),
    ):
        for cid in ids:
            catalog.records.append(
                LibraryRecord(
                    identity=LibraryIdentity(processor=proc, circuitId=cid),
                    sources=["KNOWN_SEED"],
                    block=block,
                )
            )
    return catalog


def search(catalog: Catalog, query: str, identity=None):
    records = {r.key: r for r in catalog.records}
    labels = {}
    for item in [*catalog.overlay.aliases, *catalog.overlay.favorites]:
        text = " ".join([item.label, item.description, *item.tags])
        labels[item.identity.key] = " ".join([labels.get(item.identity.key, ""), text])
        if item.identity.key not in records:
            records[item.identity.key] = LibraryRecord(
                identity=item.identity,
                sources=["USER_FAVORITE_ONLY"],
                existence="USER_POINTER",
                metadataTrust="USER_SUPPLIED",
            )
    tokens = display_text(query).casefold().split()
    return [
        r
        for r in records.values()
        if (
            identity is None
            or (
                r.identity.processor == identity.processor
                and (identity.circuitId is None or r.identity.circuitId == identity.circuitId)
            )
        )
        and all(
            t
            in " ".join(
                [
                    r.key,
                    r.onchainName,
                    r.onchainSymbol,
                    r.processorNumber or "",
                    labels.get(r.key, ""),
                ]
            ).casefold()
            for t in tokens
        )
    ]


class LibraryRpc(RpcClient):
    def __init__(self, *args, aborted: Callable[[], bool], **kwargs):
        super().__init__(*args, **kwargs)
        self.aborted = aborted

    def remaining(self):
        if self.aborted():
            raise ContractError("RESOURCE_LIMIT", "Library operation aborted.")
        return super().remaining()


class LibraryService:
    def __init__(self, settings=None, budget=None, transport=None, aborted=None):
        self.settings = settings or RpcSettings()
        self.budget = budget or ImportBudget()
        self.transport = transport
        self.aborted = aborted or (lambda: False)

    def execute(self, request: LibraryRequest | RequestV1) -> LibraryResult | ResultV1:
        from flip_core.library_protocol import legacy_result, upgrade_request

        if isinstance(request, RequestV1):
            return legacy_result(self._execute(upgrade_request(request)))
        return self._execute(request)

    def _execute(self, request: LibraryRequest) -> LibraryResult:
        req = LibraryRequest.model_validate(request.model_dump(mode="json"))
        catalog = historical(req.catalog)
        compact(catalog)
        if not catalog.records:
            catalog.records = seed_catalog().records
        if req.operation in ("discover", "circuits"):
            return self.discover(req, catalog)
        if req.operation in ("import", "revalidate"):
            return self.import_selected(req, catalog)
        if req.operation in ("favorite", "alias", "unfavorite"):
            if req.identity is None:
                raise ContractError("INVALID_INPUT", "Select a library identity.")
            target = (
                catalog.overlay.aliases if req.operation == "alias" else catalog.overlay.favorites
            )
            target[:] = [f for f in target if f.identity != req.identity]
            if req.operation != "unfavorite":
                metadata = req.metadata or Favorite(identity=req.identity)
                if metadata.identity != req.identity:
                    raise ContractError("INVALID_INPUT", "Alias identity mismatch.")
                if len(target) >= 256:
                    raise ContractError("RESOURCE_LIMIT", "User collection is full.")
                target.append(metadata)
                compact(catalog)
        results = search(catalog, req.query, req.identity)
        return LibraryResult(
            status="COMPLETE",
            catalog=catalog,
            results=results[: req.limit],
            total=str(len(results)),
        )

    def discover(self, req, catalog):
        selected = req.identity.processor if req.identity else None
        if req.operation == "circuits" and selected is None:
            raise ContractError("INVALID_INPUT", "Circuit discovery requires a processor.")
        if req.operation == "discover" and req.identity is not None:
            raise ContractError("INVALID_INPUT", "Factory discovery takes no processor.")
        result = LibraryResult(
            status="UNKNOWN", catalog=catalog, rpcCallBudget=self.budget.maxRequests
        )
        pending = []
        cursor = req.cursor
        offset = int(cursor.offset) if cursor else (1 if selected else 0)
        if cursor and (cursor.processor != selected or (selected and offset < 1)):
            raise ContractError("INVALID_INPUT", "Cursor belongs to a different scan.")
        with LibraryRpc(self.settings, self.budget, self.transport, aborted=self.aborted) as rpc:
            try:
                reader = PinnedReader(rpc, self.budget, cursor.block.number if cursor else None)
                result.block = reader.block
                result.sharedEnvironment = {
                    k: v.model_dump(mode="json") if hasattr(v, "model_dump") else v
                    for k, v in reader.shared_environment.items()
                }
                shared_digest = content_hash(result.sharedEnvironment)
                environment = reader.environment(selected) if selected else None
                digest = content_hash(environment) if environment else shared_digest
                if cursor and reader.block != cursor.block:
                    result.status, result.errorCode = "REORGED", "BLOCK_IDENTITY_MISMATCH"
                    return self.invalidate(result, selected, "REORGED")
                if cursor and digest != cursor.environmentDigest:
                    result.status, result.errorCode = (
                        "ENVIRONMENT_CHANGED",
                        "IMPLEMENTATION_CHANGED",
                    )
                    return self.invalidate(result, selected, "STALE")
                # Check prior canonical blocks too, even when starting a fresh scan.
                prior_blocks = {
                    r.block.number: r.block
                    for r in catalog.records
                    if r.block
                    and r.environment
                    and (selected is None or r.identity.processor == selected)
                }
                for block in list(prior_blocks.values())[:4]:
                    if reader.header(hex(int(block.number))) != block:
                        self.invalidate(result, selected, "REORGED")
                        result.status, result.errorCode = "REORGED", "BLOCK_IDENTITY_MISMATCH"
                for record in catalog.records:
                    if not record.environment:
                        continue
                    old_shared = record.environment.model_dump(mode="json")
                    old_shared.pop("processorCodeHash")
                    changed = content_hash(old_shared) != shared_digest
                    if selected == record.identity.processor:
                        changed |= record.environmentDigest != digest
                    if changed:
                        record.freshness = "STALE"
                        result.status = "ENVIRONMENT_CHANGED"
                        result.errorCode = "IMPLEMENTATION_CHANGED"
                total = abi.uint(
                    reader.call(selected or abi.FACTORY, "nextId" if selected else "cpuCount")
                )
                result.total = str(total)
                end = min(total, offset + req.limit)
                for index in range(offset, end):
                    rpc.remaining()
                    if selected:
                        try:
                            abi.address(reader.call(selected, "ownerOf", index))
                        except ContractError as exc:
                            if exc.code != "MISSING_REFERENCE":
                                raise
                            result.missingIds.append(str(index))
                            continue
                        fields = abi.info(reader.call(selected, "circuitInfo", index))
                        record = LibraryRecord(
                            identity=LibraryIdentity(processor=selected, circuitId=str(index)),
                            sources=["FACTORY_ENUMERATION"],
                            block=reader.block,
                            environment=environment,
                            environmentDigest=digest,
                            nIn=fields[0],
                            nOut=fields[1],
                            nState=fields[2],
                            gateCount=fields[3],
                            nextId=str(total),
                            freshness="HISTORICAL",
                            existence="OWNER_OF",
                        )
                    else:
                        proc = abi.address(reader.call(abi.FACTORY, "cpuAt", index))
                        env = reader.environment(proc)
                        processor_digest = content_hash(env)
                        for cached in catalog.records:
                            if (
                                cached.identity.processor == proc
                                and cached.environment is not None
                                and cached.environmentDigest != processor_digest
                            ):
                                cached.freshness = "STALE"
                                result.status = "ENVIRONMENT_CHANGED"
                                result.errorCode = "IMPLEMENTATION_CHANGED"
                        record = LibraryRecord(
                            identity=LibraryIdentity(processor=proc),
                            sources=["FACTORY_ENUMERATION"],
                            processorNumber=str(index),
                            block=reader.block,
                            environment=env,
                            environmentDigest=processor_digest,
                            nextId=str(abi.uint(reader.call(proc, "nextId"))),
                            freshness="HISTORICAL",
                            existence="REGISTERED_PROCESSOR",
                        )
                        for method, field in (("name", "onchainName"), ("symbol", "onchainSymbol")):
                            try:
                                raw = abi.dynamic_bytes(reader.call(proc, method), 256)
                                setattr(record, field, display_text(raw.decode("utf-8", "replace")))
                            except ContractError as exc:
                                if exc.code not in (
                                    "RPC_UNAVAILABLE",
                                    "INVALID_INPUT",
                                    "MISSING_REFERENCE",
                                ):
                                    raise
                                # Optional display metadata does not establish absence.
                                pass
                    pending.append(record)
                reader.finish()
                rpc.remaining()
                for record in pending:
                    merge_record(catalog, record)
                result.results = list({r.key: r for r in pending}.values())
                if result.status not in ("ENVIRONMENT_CHANGED", "REORGED"):
                    result.status = (
                        "PARTIAL_BOUNDED"
                        if end < total
                        else "COMPLETE_WITH_GAPS"
                        if result.missingIds
                        else "COMPLETE"
                    )
                if end < total:
                    result.cursor = Cursor(
                        offset=str(end),
                        block=reader.block,
                        environmentDigest=digest,
                        processor=selected,
                    )
            except ContractError as exc:
                result.errorCode = exc.code
                result.status = (
                    "ABORTED"
                    if self.aborted()
                    else "REORGED"
                    if exc.code == "IMPLEMENTATION_CHANGED"
                    else "UNKNOWN"
                )
                if result.status == "REORGED":
                    self.invalidate(result, selected, "REORGED")
                # Do not commit a partially verified page or turn a timeout into absence.
                result.results = search(catalog, "", req.identity)[: req.limit]
            finally:
                result.rpcCallsUsed = rpc.calls
                result.retriesUsed = rpc.retries_used
        return result

    @staticmethod
    def invalidate(result, selected, freshness):
        for record in result.catalog.records:
            if selected is None or record.identity.processor == selected:
                record.freshness = freshness
        return result

    def import_selected(self, req, catalog):
        if req.identity is None or req.identity.circuitId is None:
            raise ContractError("INVALID_INPUT", "Select a circuit to import or revalidate.")
        if self.aborted():
            return LibraryResult(status="ABORTED", errorCode="RESOURCE_LIMIT", catalog=catalog)
        identity = CircuitIdentity(
            schemaVersion="1.0.0",
            chainId=196,
            processor=req.identity.processor,
            circuitId=req.identity.circuitId,
        )
        service = ImportService(self.settings, self.budget, self.transport, aborted=self.aborted)
        try:
            prior = next((r for r in catalog.records if r.key == req.identity.key), None)
            # Reuse M2's prior-block canonical check as well as its fresh closure import.
            imported, canonical = service._import(
                identity, None, prior.block if prior and prior.environment else None
            )
            root = imported.manifest.root
            changed = prior is not None and (
                (
                    prior.environmentDigest is not None
                    and prior.environmentDigest != content_hash(root.environment)
                )
                or (prior.netlistHash is not None and prior.netlistHash != root.netlistHash)
                or (
                    prior.dependencyHashes
                    and prior.dependencyHashes
                    != [content_hash(d) for d in imported.manifest.dependencies]
                )
            )
            record = LibraryRecord(
                identity=req.identity,
                sources=["USER_IMPORT"],
                block=imported.manifest.block,
                environment=root.environment,
                environmentDigest=content_hash(root.environment),
                nIn=root.nIn,
                nOut=root.nOut,
                nState=root.nState,
                gateCount=root.expandedGates,
                freshness="STALE" if changed else "HISTORICAL",
                existence="IMPORTED",
                manifestHash=imported.manifestHash,
                netlistHash=root.netlistHash,
                dependencyHashes=[content_hash(d) for d in imported.manifest.dependencies],
            )
            merge_record(catalog, record)
            if not canonical:
                record.freshness = "REORGED"
                return LibraryResult(
                    status="REORGED",
                    errorCode="BLOCK_IDENTITY_MISMATCH",
                    catalog=catalog,
                    results=[record],
                )
            if changed:
                return LibraryResult(
                    status="ENVIRONMENT_CHANGED",
                    errorCode="IMPLEMENTATION_CHANGED",
                    catalog=catalog,
                    results=[record],
                )
            if req.operation == "import":
                recent = Recent(
                    identity=req.identity,
                    manifestHash=imported.manifestHash,
                    block=imported.manifest.block,
                )
                catalog.overlay.recents = [
                    recent,
                    *[r for r in catalog.overlay.recents if r.identity != req.identity],
                ][:30]
            return LibraryResult(
                status="COMPLETE",
                catalog=catalog,
                results=[record],
                imported=imported.model_dump(mode="json"),
            )
        except ContractError as exc:
            for record in catalog.records:
                if record.key == req.identity.key:
                    record.freshness = "VERIFICATION_FAILED"
            return LibraryResult(
                status="ABORTED" if self.aborted() else "VERIFICATION_FAILED",
                errorCode=exc.code,
                catalog=catalog,
            )
