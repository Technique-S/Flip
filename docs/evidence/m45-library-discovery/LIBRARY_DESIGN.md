# M4.5-2L — Recommended discoverable library model

**Status:** design recommendation only; no production code is implemented here.
**Baseline:** `09f2482`. Companion evidence: `PROTOCOL_DISCOVERY.md`.
**Scope:** M4.5-2L (capability 2) from the M4.5 engineering plan; M4.5-0 authorization is
owned independently by Codex and is explicitly out of scope here.

## 1. Intent and why

A developer who wants to reuse an X Layer TapeOut circuit currently must already know a
processor address and a circuit ID. The M4 pre-M5 audit found a partial capability:
strict, verified import of a caller-supplied identity, but no enumeration, catalog,
search, labels, favorites or recent-import history. The protocol does expose factory
enumeration (`cpuCount`/`cpuAt`) and per-processor `nextId`/`ownerOf`, but it has no
registration event, no reverse lookup, sparse circuit IDs and mutable implementations.

The library must therefore make discovery **useful without making it authoritative**.

## 2. Goals, non-goals, anti-goals

**Goals**

- Processor search and circuit search by `(processor address, circuit ID)`.
- Verified source identities with onchain provenance and pinned block/environment data.
- Interface metadata (nIn/nOut/nState/gateCount) without invented semantic pin names.
- Local filtering/search over escaped, provenance-labeled text.
- User favorites and a bounded recent-import list.
- Freshness and provenance labels; revalidation before composition.
- Bounded, block-aware, reorg-aware discovery with a truthful degraded mode.

**Non-goals**

- No new production interface, schema, CLI/API command or frontend component in this task.
- No transaction preview, approval, signing, broadcast or resource acquisition.
- No unbounded chain scan or full-indexer service.
- No claim that a discovered or favored circuit is currently executable.

**Anti-goals (what would make this fail even if it worked)**

- Treating `name()`/user labels as identity or authority.
- Converting a timeout or a reverted existence probe into "processor/circuit absent".
- Marking a cached netlist as current after an implementation or block change.
- Letting a favorite survive as an executable permission after a stale snapshot.
- Silently presenting a seed-only catalog as fresh chain truth.

## 3. Constraints inherited from evidence

- Chain 196 only; verify `eth_chainId` per session (MVP_CONSTRAINTS §1).
- Identity is `(chainId, factory, processor, circuitId)`; native REF records are chain-blind.
- Read methods only, explicit ABI validation, pinned block context where supported.
- Factory `isSealed = 0`; beacon and implementation code hashes are part of identity.
- Public RPC latency ~1.3 s/call; discovery must be paginated and cached.
- TAP-10: `name()` is display-only; no registration event; `eth_getLogs` often unavailable.
- All UI text is untrusted; render escaped plain text and handle bidi/control characters.

## 4. Approaches considered

| Approach | Description | Tradeoff |
|---|---|---|
| **A. Event-index first** | Subscribe to factory logs, build the catalog from registration events, replay from genesis on reorg | Rejected: no authoritative registration event is specified, public `eth_getLogs` availability is inconsistent, and genesis replay is an unbounded scan. Reorg recovery depends on logs the protocol does not define for this purpose |
| **B. Bounded state enumeration + verified seeds + user imports (recommended)** | Snapshot `cpuCount`/`cpuAt`/`nextId`/`ownerOf` at a pinned block in capped pages; overlay a known-address seed list and user imports; revalidate through the existing importer | Honest about gaps and mutability; works with read-only RPC and no events. Costs repeated state reads and requires careful block/environment pinning. Degrades gracefully to seeds + imports |
| **C. Static verified-address directory only** | Ship a curated list of known processors/circuits with no live reads | Cheapest and always available, but blind to new circuits, unable to detect upgrades, and easy to present stale data as current. Appropriate only as the *fallback layer* inside B |

Approach B is recommended. A is not viable with the observed ABI; C is retained as B's
degraded mode, not as the primary design.

## 5. Recommended data model

All keys use decimal strings for circuit IDs and lowercase hex for addresses. JSON/CBOR
serialization must keep IDs as strings so JS number precision cannot truncate them.

### 5.1 `CatalogSnapshot` (environment identity)

```
schemaVersion, chainId=196, blockNumber, blockHash,
factory, factoryImplementation, factoryImplementationCodeHash, isSealed,
beacon, beaconImplementation, beaconImplementationCodeHash,
abiProvenance, selectorDigests, providerId, providerTrust, observedAt,
discoveryStatus, rpcCallsUsed, rpcCallBudget
```

`providerTrust` is one of `SINGLE_UNTRUSTED`, `MULTI_OPERATOR_AGREEMENT`, `LOCAL_NODE`.
A single public RPC must be labeled `SINGLE_UNTRUSTED`.

### 5.2 `ProcessorRecord`

```
key = (chainId, factory, processorAddress)
processorNumber, source = ENUMERATED | KNOWN_SEED | USER_IMPORT,
nextIdUpperBound, proxyCodeHash, beaconImplementationCodeHash,
onchainNameDisplayOnly, onchainSymbolDisplayOnly,
firstSeenBlock, lastValidatedBlock, environmentDigest, freshness
```

`processorNumber` is a cached hint, not an identity: it is per chain/factory and
append-only, but a new factory implementation could change enumeration semantics.

### 5.3 `CircuitRecord`

```
key = (chainId, factory, processorAddress, circuitId)
existenceEvidence = OWNER_OF | CIRCUIT_INFO | USER_IMPORT,
nIn, nOut, nState, gateCount, netlistSha256, closureDigest,
environmentDigest, firstSeenBlock, lastValidatedBlock,
freshness = CURRENT | STALE | UNKNOWN | REORGED | VERIFICATION_FAILED,
sourceIdentities[]
```

Stateful circuits (`nState > 0`) are labeled and never offered as stateless-equivalence
candidates. No field invents a pin name.

### 5.4 `UserOverlay` (never authoritative)

```
favorites[]: (identity, userLabel, description, tags, addedAt)
recents[]:   (identity, snapshotDigest, importedAt, status)  -- bounded, e.g. 30
schemaVersion, migratedFrom
```

Stored in a separate namespace/key prefix from verified records. On migration, unknown
fields are dropped with a report. On export, active grants/signing data are never included.

### 5.5 Search index

A local index over normalized, escaped text from processor address, processor number,
circuit ID, onchain display name/symbol and user labels. Each token carries its
provenance (`ONCHAIN_DISPLAY_ONLY` vs `USER_SUPPLIED`) so the UI can show the difference.
Case-insensitive substring and token search; no server round trip.

## 6. Discovery pipeline (bounded)

1. Verify `eth_chainId`; if not 196, stop with `WRONG_CHAIN`.
2. Pin one block tag; fetch block hash. Reject if block/hash cannot be read.
3. Read factory proxy code, ERC-1967 implementation and code hash, `isSealed`.
4. `cpuCount()` → total. Walk `cpuAt(i)` in pages of at most P indices (proposed P=50),
   with a hard page cap; address `isCPU` as a consistency check.
5. For each processor, read `nextId()`. Walk IDs `1..nextId-1` in pages of at most Q
   (proposed Q=50), with a per-session ID cap. Probe `ownerOf` (or `circuitInfo`), then
   fetch `circuitInfo`/`netlist` only for existing IDs.
6. Cache netlists by `(chainId, processor, circuitId, netlistSha256, environmentDigest)`.
7. Compare `eth_getBlockByNumber(snapshot.blockNumber).hash` with the stored hash before
   committing; on mismatch mark `REORGED` and rescan from the new canonical block.
8. On outage/rate limit: bounded backoff, then `UNKNOWN` or `PARTIAL_BOUNDED`. Never
   convert a transport failure into absence.
9. Emit `discoveryStatus` and `rpcCallsUsed` with the snapshot. A capped scan is honest.

## 7. Search, favorites, recents and freshness

- **Search** is local and works against the last committed snapshot even offline; results
  carry freshness labels and are clearly marked when the snapshot is not current.
- **Favorites** are user pointers. A favorite may survive an upgrade, a reorg or an RPC
  outage, but its status becomes `USER_FAVORITE_ONLY` / `STALE` / `REORGED` as applicable.
- **Recents** are bounded, ordered by import time, and store the snapshot digest used.
- **Verified executable circuit** is a separate state: the trusted importer must
  re-resolve chain, registration, beacon, implementation, netlist bytes and REF closure
  at a fresh pinned block. Only then is composition allowed. A favorite is not an
  executable circuit and never implies one.

## 8. Authority boundary

- Untrusted metadata is rendered as escaped plain text; bidi/control characters are made
  visible or removed; no HTML/markup interpretation.
- Injected fields such as `transactionAuthority`, `permissions`, `approved`, `spend_cap`
  are dropped, never merged into policy objects.
- Discovery records, favorites, recents and user labels carry no authority. They cannot
  set target, function, value, sender, approval or cap. M4.5-0/M4.5-4 remain the only
  sources of transaction authority.
- A discovered entry becomes executable only after the existing trusted importer validates
  it. This mirrors the plan's rule that "transaction orchestration must not borrow
  unreviewed catalog metadata as authority."

## 9. Storage, migration and failure policy

- Versioned catalog schema; preserve old readers; additive version dispatch.
- Quotas: max processors, circuits, recents and cached netlist bytes; evict recents/cache
  before evicting favorites; report eviction.
- Schema migration reports dropped/unknown fields and never fabricates missing metadata.
- Failure states: `WRONG_CHAIN`, `UNKNOWN`, `PARTIAL_BOUNDED`, `ENVIRONMENT_CHANGED`,
  `REORGED`, `VERIFICATION_FAILED`. None of these may be displayed as a successful proof.

## 10. What is left to the builder (Codex)

1. Add `cpuCount`/`cpuAt`/`ownerOf` selectors and a bounded discovery adapter behind a
   Codex-owned interface, with the selector proof from `PROTOCOL_DISCOVERY.md` §2.
2. Define the frozen catalog schema, canonical hashing and storage location (UI + CLI).
3. Implement pinning, environment digests, page caps, cursor, cache and reorg checks.
4. Wire search/favorites/recents into the existing web and CLI surfaces with provenance labels.
5. Implement the acceptance cases in `ACCEPTANCE_MATRIX.md` against RPC/catalog doubles.
6. Separately perform a live read-only acceptance that records endpoint, chain, block,
   hash and code identities; a passing fixture does not establish current chain truth.
7. Keep all authorization/signing work in the M4.5-0 track; do not grant the catalog authority.
