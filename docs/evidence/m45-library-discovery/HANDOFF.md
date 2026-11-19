# M4.5-2L — Library discovery research handoff

**Agent:** OpenCode / HY4 Flash (supporting research agent)
**Date:** 2026-11-19
**Base:** `09f2482beae84be6d919ecd6957c4153d1924cca` (merged M4 main)
**Branch:** `opencode/flip-m45-library-discovery-research` (created from the base; not merged)
**Commit SHA:** the exact final commit SHA is reported in this task's completion response;
this document is included in that commit.

## Deliverables

| Path | Purpose |
|---|---|
| `docs/evidence/m45-library-discovery/PROTOCOL_DISCOVERY.md` | Task A findings, selector proof, live observation, metadata classification, limitations |
| `docs/evidence/m45-library-discovery/LIBRARY_DESIGN.md` | Task B bounded, block-aware catalog model with approaches and authority boundary |
| `docs/evidence/m45-library-discovery/ACCEPTANCE_MATRIX.md` | Task E integration-test specification with explicit classification |
| `docs/evidence/m45-library-discovery/HANDOFF.md` | This summary |
| `fixtures/m45-library-discovery/README.md` | Fixture layout and reproduction |
| `fixtures/m45-library-discovery/generators/*.py` | Selector proof, bounded live capture, deterministic fixture build and verification |
| `fixtures/m45-library-discovery/cases/*.json` | 12 synthetic mocked cases (C01–C12) |
| `fixtures/m45-library-discovery/seeds/verified_known_addresses.json` | Verified-address fallback seeds |
| `fixtures/m45-library-discovery/observations/live_xlayer_observation_0x48be576.json` | One bounded live observation |
| `fixtures/m45-library-discovery/SHA256SUMS.manifest.json` | SHA-256 + byte count for all 19 fixture files |

## Verified protocol findings (Task A)

1. **Enumeration exists onchain but is absent from Flip.** Factory `cpuCount()`, `cpuAt(uint256)`
   and `isCPU(address)` are specified by TAP-10 Appendix A and verified by a pinned-block read
   (`cpuCount=430` at block `76277110`). Flip's `abi.py` exposes `isCPU` only. New discovery
   adapter work requires a Codex-owned interface.
2. **No authoritative factory registration event.** TAP-10 documents none; `eth_getLogs` is
   available on the sampled provider but was recorded as an availability observation only and
   not interpreted. Event indexing cannot be primary discovery or reorg recovery.
3. **Circuit scanning is bounded and sparse.** `nextId` is an exclusive upper bound,
   `ownerOf` is the existence check, and reverts/gaps must be skipped. No unbounded scans.
4. **Processor numbers are append-only and never reused** per TAP-10; circuit contiguity is
   not guaranteed and burn/deletion semantics are UNKNOWN.
5. **Implementations are mutable.** Factory `isSealed=0`, implementation already upgraded
   versus the local TAP-10 copy; beacon implementation mutable; processor proxy bytecode is
   constant across processors. Environment identity must include impl and beacon code hashes.
6. **Metadata split.** Onchain verified: chainId, factory/impl/beacon identities, `cpuCount`,
   `cpuAt`, `isCPU`, `nextId`, `circuitInfo`, `netlist`, `ownerOf`. Display-only onchain:
   processor `name()`/`symbol()`. Untrusted local: aliases, user labels, favorites, recents.

All 11 relied-on selectors were independently recomputed with a self-checking Keccak-256
implementation and matched the registered values.

## Unresolved discovery limitations

- No registration event; no reverse address→index lookup.
- Sparse circuit IDs; deletion/burn behavior cannot be established from available evidence.
- Single untrusted RPC; no multi-operator agreement or consensus verification.
- `eth_getLogs` availability varies across providers; logs cannot drive reorg recovery.
- No semantic pin names (TAP issue #44 unresolved); interface metadata is numeric only.
- The observation is one block; `cpuCount` moved from 423 to 430 between the M0 audit and
  this capture, so any catalog must treat discovery as time-bound.

## Fixture counts

- Synthetic cases: **12** (`M45-2L-C01` … `M45-2L-C12`), all labeled `SYNTHETIC`.
- Seeds: **1** (`OBSERVED_READ_ONLY_DERIVED`).
- Live observations: **1** (`OBSERVED_READ_ONLY`, chain 196, block `76277110`).
- Manifest files: **19** (12 cases + 1 seed + 1 observation + 4 generators + README + manifest
  covering all of them).
- Manifest verification result: `PASS`, zero errors.

## Recommendations for Codex

1. Treat `PROTOCOL_DISCOVERY.md` §6 as the fallback rule: verified seeds + bounded discovery +
   user imports, with truthful freshness labels; never a silently authoritative list.
2. Add `cpuCount`/`cpuAt`/`ownerOf` behind a new Codex-owned interface; keep the selector proof
   in CI. Do not modify `flip_core.abi` from this research branch.
3. Pin every catalog record to block number/hash plus factory impl, beacon impl, processor
   proxy and closure digests. A favorite may outlive a snapshot; an executable circuit may not.
4. Keep untrusted labels in a separate overlay; escape all text; drop any injected authority
   fields. Catalog metadata must never grant transaction authority (M4.5-0/M4.5-4 remain the
   only authority sources).
5. Implement `ACCEPTANCE_MATRIX.md` against RPC/catalog doubles, then run a separate live
   read-only acceptance that records endpoint, chain, block, hash, ABI provenance and code
   identities. A passing fixture is not proof of current chain truth or publication.

## Validation executed in this task

| Command / check | Result |
|---|---|
| `python fixtures/m45-library-discovery/generators/keccak_selectors.py` | PASS — empty-message KAN + SHA3 permutation cross-check + 11 selectors matched |
| `python fixtures/m45-library-discovery/generators/capture_live_readonly.py` | PASS — 33/40 calls, chain 196, block `76277110`, hash recorded, no signing/overrides |
| `python fixtures/m45-library-discovery/generators/build_fixtures.py` | PASS — 12 cases, 19 manifest files |
| `python fixtures/m45-library-discovery/generators/verify_fixtures.py` | PASS — zero errors |
| `git status --porcelain` scoped to owned paths | Only the two approved directories changed |
| Credential pattern scan over new text files | No private keys, mnemonics, API keys, bearer tokens or wallet secrets |

## Ownership and policy attestation

- Wrote only under `docs/evidence/m45-library-discovery/` and `fixtures/m45-library-discovery/`.
- Did not edit production packages, frontend, schemas, CI, locks or archived fixtures.
- No signing keys, wallet connection, broadcast, payment, state override or live publication.
- No unverified proof claims; unavailable or time-limited observations are labeled UNKNOWN.
- No merge into `main`; branch is pushed only after the commit.
