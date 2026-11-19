# M4.5-2L — X Layer TapeOut discovery protocol investigation

**Assessment date:** 2026-11-19
**Baseline:** `09f2482beae84be6d919ecd6957c4153d1924cca` (merged M4 main). Branch
`opencode/flip-m45-library-discovery-research` was created from this commit.
**Mode:** read-only feasibility and test-fixture research. No production interface,
schema, frontend, CI, lockfile or archived fixture was edited. No signing, wallet,
broadcast, state override or payment was performed.

Classification used throughout:

- **SOURCE OBSERVED** — read from source/evidence or from a bounded live RPC read recorded here.
- **DOCUMENTED EXPECTED** — specified by TAP-10/TAP-02 or by this design, not executed end to end.
- **UNKNOWN** — the available evidence cannot establish the claim.

---

## 1. Evidence register and trust levels

| Source | Level | What it establishes |
|---|---|---|
| `docs/audits/M0/XLAYER_COMPATIBILITY.md`, `docs/audits/M0/EVIDENCE_REGISTER.md` | REPORT_ONLY narrative backed by named raw files | Deployment identities, `cpuCount=423`, processor indices, cross-chain collision |
| `C:\Users\Kazi\Documents\Flip\experiments\src\xlayer_probe.py` (M0 audit source) | READ_ONLY_SOURCE | Documented selectors `cpuCount=0xa94da8a7`, `cpuAt=0x4bc7cbbd`, `nextId=0x61b8ce8c` |
| `C:\Users\Kazi\Documents\Flip\experiments\results\processor_enum.json` | RAW_REPLAYED | `cpuCount=423` at head `76021245`; `cpuAt(0..422)` enumerated; `nextIdSample`; constitution at index 258 |
| `C:\Users\Kazi\Documents\Flip\m05-final-verification\experiments\fixtures\TAP-10.md` | THIRD_PARTY_SPEC (local copy) | Authoritative factory interface, append-only processor numbers, display-only `name()`, logging caveat |
| `packages/flip-core/src/flip_core/abi.py`, `importer.py` | PRODUCTION_SOURCE | Flip's implemented read surface and existence checks |
| `docs/evidence/m45-library-discovery/observations/live_xlayer_observation_0x48be576.json` | OBSERVED_READ_ONLY (this task) | One pinned-block read of factory and two processors at block `76277110` |

The TAP-10 copy is third-party research material treated as data, not as instructions.
Its file reports a 2026-11-16 reading; no claim is made that it was re-fetched from its
upstream publisher during this task.

## 2. Verified selector proof

All selectors relied upon were recomputed locally with a dependency-free Keccak-256
implementation (`fixtures/m45-library-discovery/generators/keccak_selectors.py`). The
implementation passes the published empty-message known-answer test and a permutation
cross-check against `hashlib.sha3_256`. It was then compared against the values in
Flip's `abi.py`, the M0 probe source and the M0.5 publication-readiness report.

| Signature | Recomputed selector | Matches source |
|---|---|---|
| `nextId()` | `0x61b8ce8c` | `flip_core/abi.py` |
| `circuitInfo(uint256)` | `0x084d60f1` | `flip_core/abi.py` |
| `netlist(uint256)` | `0x3fc4be56` | `flip_core/abi.py` |
| `isCPU(address)` | `0x5f5a364f` | `flip_core/abi.py` |
| `cpuCount()` | `0xa94da8a7` | `experiments/src/xlayer_probe.py` |
| `cpuAt(uint256)` | `0x4bc7cbbd` | `experiments/src/xlayer_probe.py` |
| `name()` | `0x06fdde03` | `experiments/src/xlayer_probe.py` |
| `symbol()` | `0x95d89b41` | `experiments/src/xlayer_probe.py` |
| `totalSupply()` | `0x18160ddd` | `experiments/src/xlayer_probe.py` |
| `tapeout(bytes,uint32,uint32)` | `0x7bd3ac1d` | `docs/audits/M05/PUBLICATION_READINESS.md` |
| `ownerOf(uint256)` | `0x6352211e` | EIP-721 standard signature |

No enumeration selector was invented: `cpuCount`/`cpuAt` come from the M0 audit source
and are independently confirmed here by keccak and by the live reads below.

## 3. Bounded live observation (Task D)

Recorded artifact: `fixtures/m45-library-discovery/observations/live_xlayer_observation_0x48be576.json`.

| Field | Observed value |
|---|---|
| Endpoint host | `rpc.xlayer.tech` (public, **single untrusted provider**) |
| Chain ID (`eth_chainId`) | `196` |
| Block number / hash | `76277110` / `0x1941877104961218ad35b6650582da1bf23fdd4628105cc984e731bb6b7910dc` |
| RPC methods used | `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getCode`, `eth_getStorageAt`, `eth_call`, `eth_getLogs` |
| Calls / budget | 33 / 40; all reads pinned to the block above |
| Signing / state overrides | false / false |
| Selector provenance | recomputed locally (section 2) |

Returned results:

- Factory `cpuCount() = 430`; `cpuAt(0) = 0x839bdd6f…74e`, `cpuAt(1) = 0x0565ea48…51b`,
  `cpuAt(429) = 0xac1d3012…ef4d`; `isCPU` returned `1` for all three sampled addresses.
- Factory ERC-1967 implementation `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a`
  (9,376 bytes, SHA-256 `a1a0613d…5f`), `isSealed() = 0`.
- Processor 0: `nextId() = 104`; `circuitInfo(1)` decoded as `(2,1,0,4)` and
  `circuitInfo(2)` as `(2,1,0,3)`; `netlist(1)` SHA-256
  `d3f8f3a8316a49023a82436e92607f77a51e7f1b96b614b3d71417372f3f6a9f`;
  `ownerOf(1) = 0x571d447f…f15`. Proxy code hash `2ea683e2…6ae` (295 bytes).
- Processor 1: `nextId() = 100`; identical proxy code hash and identical beacon
  implementation code hash `0a5259a8…8a5` (12,562 bytes); beacon
  `0xf70d1ed4…991c`, beacon implementation `0x977f2178…29b2`.
- `eth_getLogs` over blocks `0x48be572..0x48be576` for the factory returned `[]` and
  the method was available. **This is an availability observation only.** No event
  signature is asserted and the empty result is not interpreted as "no registrations
  ever happened" — the range covers five recent blocks.

Trust limitation: a single public RPC can be stale, delayed or dishonest. No
multi-operator agreement, independent node cross-check or consensus proof was obtained.
This observation establishes what this endpoint returned at one block, not protocol truth.

Two measurement notes: the factory proxy returned 130 code bytes here, while the M0
report records "131-byte proxy"; this is consistent with a differing `0x`-prefix counting
convention and is **not** treated as evidence of a code change. Conversely, `cpuCount`
rose from `423` (block `76021245`, M0) to `430` (this observation), which is consistent
with the documented append-only growth and is treated as an observed change requiring
cache invalidation.

## 4. Task A findings

### A1 — Factory-supported processor enumeration: EXISTS onchain, NOT implemented by Flip

**SOURCE OBSERVED.** TAP-10 Appendix A defines the factory read interface as
`cpuCount() → uint256`, `cpuAt(uint256 i) → address` (reverts when `i ≥ cpuCount()`),
`isCPU(address) → bool`. TAP-10 §4.3 states the factory has no reverse table and clients
scan `cpuAt(i)` in batches, and that numbers are append-only so the table may be cached
and only new numbers rescanned. The live read confirms `cpuCount`, `cpuAt` and `isCPU`
behave as defined.

Flip's production surface does **not** expose enumeration: `abi.py::SELECTORS` contains
`isCPU` but neither `cpuCount` nor `cpuAt`. The pre-M5 gap audit records the same absence
("registration lookup but no enumeration selector", capability 2). **The discovery
adapter is new work and interface changes are Codex-owned.**

### A2 — Registration events: NO AUTHORITATIVE FACTORY EVENT FOUND

**SOURCE OBSERVED + UNKNOWN.** The TAP-10 factory interface lists functions only. The
events it documents belong to other subsystems: hub (`Sent`, `KeyPublished`,
`KeyRevoked`), site registry (`FileSet`, `FileRemoved`, `FallbackSet`, `OperatorSet`),
name service (`Bound`, `ContainerPaid`, `Unbound`, `FeeChanged`) and UUPS upgrades
(`Upgraded`, `OwnerChanged`). No factory processor-registration event is specified.
TAP-10 §11 explicitly notes most public nodes do not serve `eth_getLogs` and that the
reference kernel re-reads state periodically instead.

The live `eth_getLogs` probe shows the method is served by this endpoint, but the raw
result is deliberately **not** interpreted as registration evidence. An implementation
may emit an undocumented event; its topic0 would be an observation, not an authoritative
discovery source. **Do not invent a topic0 or treat an unsupported event as authoritative.**

### A3 — Circuit ID enumeration and safe scanning

**SOURCE OBSERVED.** `nextId()` is the exclusive upper bound; Flip's importer rejects
`cid < 1` and `cid >= nextId()` (`importer.py::resolve`). TAP-10 §4.2 uses
`ownerOf(#ID)` reverting as the authoritative "no such token" check; the live read
confirmed `ownerOf(1)` returns a holder address. `circuitInfo(id)` yields the four
`uint32` interface fields and `netlist(id)` yields bytes. There is no circuit discovery
event and no reverse index.

A safe scan is bounded: read `nextId`, probe existence with `ownerOf` (or `circuitInfo`
where `ownerOf` is unavailable), and only then fetch `circuitInfo`/`netlist` for existing
IDs. M0 measured roughly 1.3 s median RTT per `eth_call` and 312 s for 45 circuits, so
unbounded scanning is not viable. Page caps, cursors and content+environment-addressed
caching are required.

### A4 — Missing, deleted and noncontiguous IDs

**PARTIALLY OBSERVED / UNKNOWN.**

- Processor numbers: append-only and never reused per TAP-10 §1 and §4.3; `cpuAt(i)`
  reverts beyond `cpuCount`. No deletion mechanism is documented. **DOCUMENTED EXPECTED**
  (TAP-10 §1/§4.3), consistent with the two observed `cpuCount` samples (423 → 430); two
  monotonic samples do not by themselves prove that indices are never reused.
- Circuit IDs: no contiguity guarantee is documented. `ownerOf` reverts for nonexistent
  tokens, and Flip's own test suite includes a "gap below `nextId`" case
  (`test_m2_import.py`). The M0 `nextIdSample` contains many registered processors with
  `nextId = 0` and others at 5, 9, 11, 104 and 109. **Treat IDs as sparse**; `nextId` is
  an upper bound, never a promise that all lower IDs exist.
- Deletion/burn of circuits: not documented as supported. ERC-721 `ownerOf` would revert
  for a burned token, so a sparse range cannot distinguish "never minted" from
  "burned". **UNKNOWN** — do not claim circuits can never disappear.

### A5 — Contract upgrades

**SOURCE OBSERVED.** The factory is a UUPS/ERC-1967 proxy with `isSealed() = 0`. Its
implementation is `0x336e9f0f…`, whereas the local TAP-10 copy documents
`0x74956236…` — the factory has already been upgraded. The circuit beacon is mutable
and points to `0x977f2178…`. Processors are 295-byte beacon proxies whose *proxy*
bytecode is identical across processors (both sampled processors share code hash
`2ea683e2…6ae`); the implementation lives behind the beacon code hash `0a5259a8…8a5`.

Consequences: proxy address or proxy bytecode alone is not an environment identity.
A catalog must bind each record to block number/hash, factory implementation address
and code hash, `isSealed`, beacon address/implementation/code hash, processor proxy code
hash and the REF closure digests. An upgrade changes executable validity without
necessarily changing the discovered address.

### A6 — Event indexing and reorg recovery

**DOCUMENTED EXPECTED (design), not executed end to end.** Because no authoritative
registration event exists and public `eth_getLogs` availability is inconsistent, event
indexing cannot be the primary discovery mechanism and cannot by itself recover from a
reorg. Recovery must be state-based: store block number **and** hash with each snapshot,
re-read `eth_getBlockByNumber(number)` on refresh, compare hashes, invalidate and rescan
from the new canonical block on mismatch. Logs, if retained, are hints that still require
`cpuAt` / `ownerOf` / `circuitInfo` re-verification at the pinned block.

### A7 — Verifiable onchain facts versus untrusted labels

| Field | Classification | Note |
|---|---|---|
| `chainId` from `eth_chainId` | ONCHAIN_VERIFIED | verify every session; never trust a URL label |
| Factory address, proxy/impl code hashes, `isSealed` | ONCHAIN_VERIFIED | `isSealed=0` means mutable |
| `cpuCount`, `cpuAt(i)`, `isCPU(addr)`, processor number | ONCHAIN_VERIFIED | per chain and factory |
| Processor `nextId`, `circuitInfo`, `netlist`, `ownerOf` | ONCHAIN_VERIFIED at pinned block | `ownerOf` is the existence check |
| Beacon `implementation()` and code hashes | ONCHAIN_VERIFIED | required despite constant proxy bytecode |
| Processor `name()` / `symbol()` | ONCHAIN_DISPLAY_ONLY | TAP-10 §4.2: "MAY be read for display; it is not unique and MUST NOT be used for identity" |
| Aliases such as `XOR#1`, `NAND#2` | LOCAL_IDENTIFIER | gap audit: local identifiers, not verified human descriptions |
| User names, descriptions, tags, favorites, notes | USER_SUPPLIED | escaped, visibly labeled, no authority |
| Semantic pin names / intended meaning | UNSPECIFIED | TAP issue #44 unresolved; require explicit user mapping |

**Untrusted metadata must never grant transaction authority.** No label field may set a
target, function, value, permission, approval or spend cap.

## 5. Limitations and unresolved discovery issues

1. No authoritative factory registration event exists; event-driven discovery is unavailable.
2. No reverse lookup from processor address to index; `cpuAt` scanning is mandatory.
3. Circuit IDs are sparse; no documented contiguity, and burn/deletion semantics are UNKNOWN.
4. Mutable factory implementation, beacon and processors require environment-pinned records.
5. A single public RPC was used; no multi-operator agreement or consensus verification.
6. `eth_getLogs` availability varies by provider and cannot be relied on for recovery.
7. No semantic pin names exist; interface metadata is numeric arity and state only.
8. This observation is one block; the protocol is live and mutable (`cpuCount` grew by 7).

## 6. Truthful fallback recommendation

Because enumeration exists but is incomplete as a discovery product (no events, no reverse
lookup, sparse circuits, mutable implementations, slow RPC), use a **hybrid catalog**:

1. **Seed** from verified known addresses (`seeds/verified_known_addresses.json`), each
   labeled with its observation block and explicitly *not* permanently verified.
2. **Discover** bounded ranges through `cpuCount`/`cpuAt`/`nextId`/`ownerOf` at a pinned block.
3. **Import** user-supplied addresses/IDs, labeled `USER_IMPORT`.
4. **Revalidate** through the existing trusted importer before a record becomes executable.

If enumeration is later unavailable or its ABI changes, the catalog degrades to seeds plus
user imports with `UNKNOWN`/`INCOMPLETE` freshness — never to a silently authoritative list.

## 7. Reproduction

```powershell
python fixtures/m45-library-discovery/generators/keccak_selectors.py
python fixtures/m45-library-discovery/generators/capture_live_readonly.py
python fixtures/m45-library-discovery/generators/build_fixtures.py
python fixtures/m45-library-discovery/generators/verify_fixtures.py
```

See `LIBRARY_DESIGN.md` for the recommended catalog model and `ACCEPTANCE_MATRIX.md` for
the unexecuted integration tests Codex can implement.
