# Provenance index — Flip M1-B fixtures

Every entry below names the committed raw artifact(s), the provenance level, the observed chain/block context where the raw data supports it, and exactly what was verified. Full hashes only; abbreviated hashes from the narrative reports were not used to build fixtures.

## 0. Chain / block context actually present in raw data

| Raw source | chainId | Block | Block hash / timestamp | Notes |
|---|---:|---|---|---|
| `raw/M0/xlayer_circuits.json` | 196 (X Layer mainnet) | head `76,020,961` | generated `2026-11-16T00:46:40Z` | RPC `https://rpc.xlayer.tech`; source of XOR#1 and NAND#2 netlist bytes. |
| `raw/M05/gate_b_manifest.json` | 196 | `76,056,306` | `0x198e4a83d2cd97e06b56d60f787eaf3b29cb55042e086e8c6639d217f81a3e1f` | Canonical manifest snapshot (`tap02Version` `draft-2026-10-04`, `testSuiteHash` `0x1a02f5cf991c130a22dc6cc6ee93d0f8fe0720afed081665fa8b8018aefd203b`). |
| `raw/M05/gate_b_negative.json` | 196 vs 8453 (Base) | `0x488875b`, `0x4888756`, `0x4888729` | netlist byte-identical at all three | Live cross-chain/divergence checks are historical, not a fresh read. |
| `raw/M05/gate_a_probe.json` | 196 | not block-pinned in file | — | `nextId()` `0x68` (104), `TAPEOUT_FEE()` `0x00000000000000000000000000000000000000000000000000049e57d6354000`, factory `isSealed()` `0`, selector proof `matches: true`. |

XOR#1 is block-pinned by the Gate B manifest. NAND#2 and the composed half-adder have chain identity only via the M0 xlayer fixture; no block-pinned manifest was generated for them (see `MISSING_ARTIFACTS.md`).

## 1. XOR#1

- **Artifacts:** `raw/M0/xlayer_circuits.json`, `raw/M0/composition_poc.json`, `raw/M05/gate_b_manifest.json`.
- **Level:** `RAW_REPLAYED`. Netlist digest independently re-derived as `READ_ONLY_REGENERATED`.
- **Observed bytes:** processor `0x839BDD6fA7A66416a609A735E11DE5411b98574E`, circuitId `1`, `nIn=2, nOut=1, nState=0`, `gateCount=4`, netlist `0x00000002000003000000020000040000000300000400000005000006` (28 bytes), opCounts `{NAND: 4}`, four on-chain eval cases `00→00, 01→01, 02→01, 03→00`.
- **Hashes:** netlist SHA-256 `d3f8f3a8316a49023a82436e92607f77a51e7f1b96b614b3d71417372f3f6a9f` (matches `composition_poc.json` `sources[0]` and `gate_b_manifest.json` `netlistHash`); manifest digest `0xb7c6e18daf408462f3fd23dd11ac40be96a696e5791b44667773bf89959601e3`.
- **Environment pinning (from manifest):** `processorCodeHash 2ea683e2…ea02ee`, `factory 0x1f09daef…760761`, `factoryImplAddress 0x336e9f0f…3f4ae2a`, `beaconImplementation 0x977f2178…35f29b2`, `factoryIsSealed` `0`.
- **Verified:** SHA-256 of the 28 raw netlist bytes equals the recorded hash; eval cases are present in the raw file.

## 2. NAND#2

- **Artifacts:** `raw/M0/xlayer_circuits.json`, `raw/M0/composition_poc.json`.
- **Level:** `RAW_REPLAYED`. Netlist digest independently re-derived as `READ_ONLY_REGENERATED`.
- **Observed bytes:** processor `0x839BDD6fA7A66416a609A735E11DE5411b98574E`, circuitId `2`, `nIn=2, nOut=1, nState=0`, `gateCount=3`, netlist `0x000000020000030000000400000400000005000005` (21 bytes), opCounts `{NAND: 3}`, eval cases `00→01, 01→01, 02→01, 03→00`.
- **Hash:** netlist SHA-256 `91c81eb018919169c97a8b7e10f4ab9bb2792960f53c0f4de3e3d2681939fd8e` (matches `composition_poc.json` `sources[1]`).
- **Verified:** SHA-256 of the 21 raw netlist bytes equals the recorded hash. Chain identity 196 / head block 76,020,961 from the xlayer fixture; **no block-pinned manifest exists for NAND#2**.

## 3. Composed 81-byte half-adder

- **Artifacts:** `raw/M0/composition_poc.json`, `raw/M05/gate_a_compose_rerun.json`, `raw/M05/gate_a_probe2.json`.
- **Level:** `RAW_REPLAYED` (all three). Length/digest re-derived as `READ_ONLY_REGENERATED`.
- **Observed bytes:** composed netlist `0x02839bdd6fa7a66416a609a735e11de5411b98574e000000000000000202010000020000030000000400000102839bdd6fa7a66416a609a735e11de5411b98574e00000000000000010201000002000003`.
- **Verified facts from raw data:** `composedNetlistBytes = 81`; recomputed byte length = 81 and SHA-256 = `3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`; `deterministic: true`; `officialLoad`/`independentLoad` = `ok`; `semanticsPass: true`; truth table `00→00, 01→02, 02→02, 03→01`, all four rows `pass: true`.
- **Structure:** `REF(NAND#2)` → glue `NAND(4,1)` → `REF(XOR#1)`; automatic backward-reference ordering.
- **`gate_a_compose_rerun.json`** is the M0.5 rerun of the same composition (UTF-16 LE with BOM in the original); `gate_a_probe2.json` independently records `tapeoutSimFull.netlistBytes = 81`.
- **Limitation:** no canonical manifest hash is present for the composed circuit; its inputs XOR#1/NAND#2 are identified by processor + id + netlist hash only.

## 4. Mutation cases

- **Artifacts:** `raw/M0/wiring_canary.json`, `raw/M0/composition_poc.json` (`faultInjection`).
- **Level:** `RAW_REPLAYED`.
- **Four behavioural wiring mutations (all structurally valid):** mutant1 reversed inputs into both REFs → EQUIVALENT (UNSAT, 55 clauses); mutant2 XOR inputs swapped → EQUIVALENT (UNSAT, 55 clauses); mutant3 glue NAND wired to input bit → DIFFERENT, SAT witness `[0,0]`, sim-verified; mutant4 outputs `(sum, nand)` → DIFFERENT, SAT witness `[0,0]`, sim-verified. `satSelfTest.baseVsBase.diffFound = false`.
- **Scale mutation:** `parity8` (7 XOR REFs, 28 NAND gates) vs duplicated-input mutant → DIFFERENT, SAT witness `[0,1,0,0,0,0,0,0]`, sim-verified; exhaustive witness `[1,0,0,0,0,0,0,0]`.
- **Six composition faults in `faultInjection`:** 2 structurally valid + behaviourally equivalent, 2 structurally valid + behaviourally different, 2 structurally rejected (`REF arity does not match the target circuit`; `signal 4 referenced by element at 4 is not available`).
- **Oracle modes:** declared spec / trusted reference / unknown intent all recorded per mutation; unknown intent yields `AMBIGUOUS` or `EQUIVALENT: no behavioral difference exists`, never a fabricated intent.

## 5. Nine integrity negatives

- **Artifacts:** `raw/M05/gate_b_negative.json`, `raw/M05/gate_b_manifest.json`.
- **Level:** `RAW_REPLAYED`. Count re-derived as `READ_ONLY_REGENERATED`.
- **Baseline:** `xor1`, manifestHash `0xb7c6e18daf408462f3fd23dd11ac40be96a696e5791b44667773bf89959601e3`.
- **All 9 detected (`allNegativeDetected: true`):** wrong chain 8453 (`chain-mismatch`), changed circuit ID (`circuit-id-mismatch`), changed netlist hash (`netlist-hash-changed` + `netlist-hash-vs-bytes-inconsistent`), changed REF dependency core#102→#101 (`dependency-set-changed`), changed factory impl slot (`factory-implementation-changed`), changed beacon implementation (`beacon-implementation-changed`), unexpected processor identity (`processor-mismatch`), stale block (`block-hash-changed`), inconsistent RPC netlist bytes (`netlist-hash-vs-bytes-inconsistent`).
- **Live checks:** chainIds distinct (196 vs 8453); Base `nextId` `0x…0a` (10) vs X Layer 104; XOR#1 netlist identical at three historical blocks.
- **Scope note:** these are synthetic mutations of a captured manifest plus historical cross-chain reads. The raw data does **not** demonstrate protection against a malicious RPC operator.

## 6. 28 scale verdicts

- **Artifacts:** `raw/M05/gate_c_scale.json`, `raw/M05/gate_c_scale_partial.json`.
- **Level:** `RAW_REPLAYED`. Counts re-derived as `READ_ONLY_REGENERATED`.
- **Matrix:** 7 target gate counts (50, 100, 250, 500, 1,000, 2,500, 5,000) × 4 modes (`self`, `equivalent`, `different`, `fault_reverse_one`) = **28 case verdicts**. Expected sequence EQUIVALENT / EQUIVALENT / DIFFERENT / EQUIVALENT; every Minisat22 case has `matchesExpected: true`. Every `different` witness was `witnessVerifiedBySim: true`.
- **Measured points (Minisat22, `self` case):** 48 gates/293 clauses/112 vars at 3.24 MiB → 5,000 gates/30,005 clauses/11,254 vars at 7.44 MiB. The 5,000-gate case carries `refs = 1,250` and `nIn = 1,251`.
- **DPLL backend in the same raw file:** `OK` at 48 gates; `TIMEOUT → UNKNOWN` at 100/250/500; `SKIPPED → UNKNOWN` at 1,000/2,500/5,000. Per-case timeout 8 s; policy `timeout -> UNKNOWN (never EQUIVALENT)`.
- **Correctness safeguards:** 7 present, all `passed: true` (malformed source rejected, wrong REF resolver detected, symmetric rewiring EQUIVALENT, duplicated fan-out DIFFERENT + witness, output permutation DIFFERENT, timeout→UNKNOWN, half-adder self-equivalence regression).
- `gate_c_scale_partial.json` is the checkpoint from which `gate_c_scale.json` was finalized.

## 7. Stateful k-beat fixture

- **Artifacts:** `raw/M05/gate_c_stateful.json` and the embedded `statefulKBeat` object inside `raw/M05/gate_c_scale.json`.
- **Level:** `RAW_REPLAYED`; equality of the two traces re-derived as `READ_ONLY_REGENERATED` (`stateful_trace_matches_embedded_copy: true`).
- **Content:** official TAP-02 `toggle` vector (LATCH, `nState=1`); mutant rewires LATCH `d` to constant-1; all-zero initial state; inputs `[k & 1 for k in 0..7]`; `beats = 8`; `firstDifferenceBeat = 0`; `reproducible = true`. Full `traceOriginal` and `traceMutant` (beat/in/out/state) are present.
- **Scope label:** bounded k-beat trace comparison only; **not** unbounded sequential equivalence.

## 8. Structural pre-flight revert

- **Artifacts:** `raw/M05/gate_a_probe2.json`, `raw/M05/gate_a_probe.json`, `raw/M0/composition_poc.json` (`faultInjection`).
- **Level:** `RAW_REPLAYED`.
- **Revert evidence:** `tapeoutSimFull` on the 81-byte netlist → `status: "reverted"`, `result: null`, `error: "Invalid params"`; `revertArgDecode[0].args = [61453, 0, 1, 0]` (sender `0xf00d`, balance `0`, needed `1`, id `0`); `overrideSupported: false`; `tapeoutEstimateGas.code = -32003` (`OutOfFunds`); ERC-1155 error selector proof `computedSelector == observedRevertSelector == 0x03dee4c5`, `matches: true`.
- **Live-ish environment facts:** `TAPEOUT_FEE()` `0x49e57d6354000`; factory `isSealed()` `0`; `nextId()` 104.
- **Required honesty label:** this is structural-only evidence. Allowed report labels are **STRUCTURALLY ACCEPTED**, **REJECTED** (specific §3 reason), or **UNKNOWN** (RPC/override unavailable). It is **not** SIMULATION SUCCESS and **not** publication. `composition_poc.json` supplies two concrete structural rejections (REF arity mismatch, NAND forward reference).
