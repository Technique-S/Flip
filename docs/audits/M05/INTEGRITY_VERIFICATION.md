# Gate B — Dependency Integrity and Cross-Chain Safety

## Status: **PASS** — realistic integrity-checking prototype detects all 9 mandatory negative fixtures.

## B1. Identity model (VERIFIED / INFERRED)

The live manifest generator (`experiments/src/gate_b_manifest.py`, output `experiments/results/gate_b_manifest.json`) captures:

| Field class | Fields | Why required |
|---|---|---|
| Circuit identity | `chainId`, `processor`, `circuitId`, `netlistHash`, `nIn/nOut/nState`, `gateCount` | Native REF records carry only (cpu, id) — no chain; the same address exists on X Layer (196) and Base (8453) with **different state** (`nextId`: 104 vs 10, verified). |
| Observation point | `blockNumber`, `blockHash` | Reads must be pinned; factory impl can change between blocks. |
| Execution environment | `factory`, `factoryImplSlot`, `factoryImplCodeHash`, `isSealed`, `cpuCount`; `beacon`, `beaconImplementation`, `beaconImplementationCodeHash`, `beaconOwner`; `processorCodeHash` | **Hashing the processor proxy bytecode is NOT sufficient** — every processor is a 295-byte beacon proxy; the code lives behind `circuitBeacon.implementation()` and can change there (`isSealed=0`, factory impl already upgraded once — TAP-10 documents 0x74956236…, chain shows 0x336e9f0f…). |
| Dependency closure | per-REF `cpu`, `id`, arity + full target manifest (`netlistHash`, `nState`, gates) | Behavior of a parent circuit depends on sub-circuit contents; a change to *any* dependency invalidates verification. |
| Verification context | `tap02Version` (`draft-2026-10-04`), `testSuiteHash` (`0x1a02f5cf…`, matches TAP-02's published vectors SHA-256) | A proof is meaningful only relative to a semantics version and test suite. |
| Manifest digest | `manifestHash` = SHA-256 of canonical JSON (`sort_keys=True`, compact separators, UTF-8) | Deterministic content-addressed snapshot. |

Live manifest produced at block `76,056,232`:
- `xor1`: netlist hash `0xd3f8f3a8…a9f`, no deps, 4 gates.
- `wrapper4`: netlist hash `0x0d6225ff…70ad`, 1 REF → core processor `0xf044d395…39f` #102, whose 64-byte netlist hash is `0xac765e17…13a0` (10 gates, nState=2); factory impl `0x336e9f0f…`, beacon impl `0x977f2178…`.

## B2. Negative tests (VERIFIED — `experiments/results/gate_b_negative.json`)

| # | Fixture | Detected by | Result |
|---|---|---|---|
| 1 | Same processor address on wrong chain (8453) | `chain-mismatch` | ✓ |
| 2 | Changed circuit ID (1→2) | `circuit-id-mismatch` | ✓ |
| 3 | Changed netlist hash | `netlist-hash-changed` + hash-vs-bytes inconsistency | ✓ |
| 4 | Changed REF dependency (core#102→#101) | `dependency-set-changed` | ✓ |
| 5 | Changed factory implementation slot | `factory-implementation-changed` | ✓ |
| 6 | Changed beacon implementation | `beacon-implementation-changed` | ✓ |
| 7 | Unexpected processor identity | `processor-mismatch` | ✓ |
| 8 | Stale verification snapshot (old block/hash) | `block-hash-changed` | ✓ |
| 9 | Inconsistent RPC result (mutated netlist bytes) | `netlist-hash-vs-bytes-inconsistent` | ✓ |

**All 9 detected** (`allNegativeDetected: true`). Live cross-checks: chain IDs 196 vs 8453 distinct; `netlist(1)` byte-identical across head, head−5, head−50.

## B3. Trust-boundary analysis & caching rules

| Question | Answer |
|---|---|
| Can we reliably identify an upgraded processor? | **YES if** beacon owner/impl and impl code hash are pinned; **NO** from proxy bytecode alone (295-byte proxy, code lives behind beacon). |
| Distinguish code change from block change? | YES — impl address/code hash changed ⇒ code change; only block/hash changed ⇒ ordinary new block. |
| Are imported netlists immutable? | **NOT guaranteed** — factory `isSealed=0` and beacon upgradeable; TAP-10: "stored netlists and their evaluation could change after tape-out" [Open]. |
| Can dependency behavior change with unchanged netlist? | **YES** — sub-circuit processor may be upgraded behind its beacon. Pin sub-circuit's beacon impl + code hash too. |
| Can imports be cached? | **YES, keyed by content hash** `(chainId, processor, id, netlistHash, beaconImplCodeHash, factoryImplCodeHash)`, with hash re-verification on use. |
| What requires revalidation before export/deploy? | Fee, impl slots + code hashes, dependency closure, `isSealed`, RPC `chainId`, and (for publication) transistor balance. |
| If RPC lies / inconsistent responses? | Prototype detects *synthetic* divergence; **no protection against a malicious RPC provider was independently demonstrated** (would require TAP-10 §5 multi-operator agreement — recommended for production but not proven here). |

## B4. Adverse finding encountered during this gate

An early draft of the probe scripts computed 4-byte selectors as the **full 32-byte keccak hash**, producing malformed calldata that made every `circuitInfo()` call revert `"no circuit"` even though `nextId()=104`. After correcting the encoding (`keccak256(sig)[:4]`), all reads succeeded. This is a **client-side encoding hazard**, not an onchain anomaly — and a concrete argument for pinning selector/ABI provenance in the manifest and for validating decoded results (netlist hash vs bytes) as the checker does.

## B5. Acceptance

Gate B criteria met: the prototype detected all 9 mandatory negative fixtures and accurately describes its limits. Caveat: the live cross-chain test used the same processor address on Base only to demonstrate `chainId`/state divergence — it does not prove immunity to malicious RPC operators.
