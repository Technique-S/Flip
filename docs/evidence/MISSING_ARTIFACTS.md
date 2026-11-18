# Missing artifacts and explicit gaps — Flip M1-B

This file records material that is absent, unreachable, or deliberately not reconstructed. Nothing in this file was synthesised. Truncated hashes and abbreviated outputs appearing in the narrative audit reports were **not** expanded from prose; a value is used as a fixture only when full bytes exist in a raw artifact.

## 1. Canonical audited source trees are absent (primary chain-of-custody gap)

| Source path (from task prompt) | Missing material | Affected tests / acceptance | Status |
|---|---|---|---|
| `C:\research\circuitforge-feasibility\experiments` | The entire canonical M0 experiment tree (fixtures, results, src) is not present on this machine. Only a local copy at `C:\Users\Kazi\Documents\Flip\experiments` was found. | All four M0 `RAW_REPLAYED` fixtures; G-02 TAP-02 parity, G-05 composition, G-06 canary semantics, M3 mutation corpus. | **BLOCKER for byte-identity with the originally audited originals.** Fixtures are copied from the local copy; identity with `C:\research` originals is unverifiable here. |
| `C:\research\circuitforge-feasibility\m05-final-verification\experiments` | The entire canonical M0.5 experiment tree is not present. Only a local copy at `C:\Users\Kazi\Documents\Flip\m05-final-verification\experiments` was found. | All eight M0.5 `RAW_REPLAYED` fixtures; G-03/G-04 manifest integrity, G-06 scale, M6 k-beat trace, G-10 pre-flight. | **BLOCKER for byte-identity with the originally audited originals.** |

`C:\research\circuitforge-feasibility` itself exists but contains only the seven markdown research reports, no `experiments/` directory. Neither source tree was modified.

## 2. Missing raw artifacts for specific claims

| Missing material | Expected source / where looked | Affected tests / acceptance | Provenance level | Handling |
|---|---|---|---|---|
| Block-pinned canonical manifest for **NAND#2** and for the **composed 81-byte half-adder**. Only `xor1` and `wrapper4` manifests were produced. | `m05.../experiments/results/gate_b_manifest.json` (`manifests[]` has 2 entries) | G-04 REF integrity for composed circuits; M2 manifest revalidation; M3 composition evidence bundle. | REPORT_ONLY for those circuits' manifest digests | Circuit identity is limited to processor + id + netlist hash (XOR#1/NAND#2 hashes are full and raw-verified). Do not fabricate a manifest hash. |
| Raw log of **100 deterministic composition runs**. | `experiments/results/composition_poc.json` has `deterministic: true` but no 100-run record; no other raw file found. | G-05 / dependency map "100 deterministic runs". | REPORT_ONLY | `deterministic: true` is copied as observed. The count of 100 is a report claim only, not an executable fixture. |
| Raw before/after artifact for the **4-byte selector encoding hazard** (4-byte `keccak(sig)[:4]` vs full 32-byte hash) described in Gate B B4. | No raw file in either local tree records the malformed calldata or the resulting `no circuit` reverts. | Selector/ABI provenance pinning; G-03 read-only X Layer. | REPORT_ONLY | Narrative only. No calldata fixture was invented. (The *correct* selector proof IS raw: `gate_a_probe.json` `errorSelectorCheck.matches: true`.) |
| Full value of the **older TAP-10 factory implementation** hash, printed truncated as `0x74956236…` in `INTEGRITY_VERIFICATION.md`. | `m05.../experiments/fixtures/TAP-10.md` was not copied (large third-party spec); no copied raw record contains the full value. | Factory-upgrade provenance comparison (M2). | REPORT_ONLY / truncated | **Not reconstructed.** The current impl `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a` is full and raw-verified from `gate_b_manifest.json`; the historical one is not. |
| Evidence of **malicious-RPC resistance / TAP-10 §5 multi-operator agreement**. | No such experiment exists in either tree; audits explicitly state it was not demonstrated. | Out of MVP scope; must not be claimed as a passing gate. | REPORT_ONLY (explicit non-claim) | No fixture created. Cache/identity checks only detect synthetic divergence. |
| **Solver worker containment** evidence for 5 s / 64 MiB on the release target. | No worker-process stress artifact in either tree (only in-process timings in `gate_c_scale.json`). | G-07 Runtime limits (not an M1 gate). | REPORT_ONLY | Raw in-process peaks (max 7.44 MiB) are copied; process-level enforcement remains unverified. |
| **Fresh, current** onchain fee / beacon / implementation re-read. | No network RPC was performed by this task. | G-03, G-10 "current fee read each session"; M2 live verification. | REPORT_ONLY for "current" status | All chain data here is historical and block-pinned. Labels must say `HISTORICAL`; do not report as current. |

## 3. Material present at source but excluded from the commit (not missing)

These are **not** gaps; they exist at the read-only source paths and are listed in `SOURCE_INVENTORY.md` §4. They were excluded because they are large, third-party, or non-fixture source code:

- `m05.../experiments/fixtures/tapeout_net_bundle.js` (1,569,344 B) and `TAP-10.md` (109,187 B) — Gate D / spec material, outside M1-B deliverables.
- `m05.../experiments/vendor/**` including `pysolvers.cp314-win_amd64.pyd` (3,663,360 B) and `msvcp140-*.dll` (575,056 B) — solver toolchain binaries, not fixtures.
- `experiments/fixtures/corpus.json` (198,698 B), `experiments/results/corpus_scan2.json` (199,389 B) and other M0 probe outputs.
- Experiment `src/*.py`, `__pycache__/*.pyc`, and console run logs (`gate_b_manifest_run.txt`, `gate_c_scale_run.txt`) — referenced in `REPRODUCIBILITY.md`, left at source.

## 4. Values that were truncated in reports but fully recovered from raw bytes

For transparency, these abbreviated report values were replaced only by full values found in raw artifacts — never by guessing digits:

| Report abbreviation | Full value source | Full value |
|---|---|---|
| `0xd3f8f3a8…a9f` | `gate_b_manifest.json`, `composition_poc.json`, recomputed from netlist bytes | `d3f8f3a8316a49023a82436e92607f77a51e7f1b96b614b3d71417372f3f6a9f` |
| `0x0d6225ff…70ad` | `gate_b_manifest.json` | `0d6225ff61bc8e990c757c9152a136ab580b5630c39317f81b9e05edce8070ad` |
| `0xac765e17…13a0` | `gate_b_manifest.json` (dependency closure) | `ac765e17b369dbfe28b952685404eabb417d537d1d2a2a317827bb0b6e3c13a0` |
| `0x1a02f5cf…` | `gate_b_manifest.json`, `vectors.json` | `1a02f5cf991c130a22dc6cc6ee93d0f8fe0720afed081665fa8b8018aefd203b` |
| `0x336e9f0f…`, `0x977f2178…` | `gate_b_manifest.json` | `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a`, `0x977f217887e085d298cb3819cdad5a0ee35f29b2` |

The older `0x74956236…` value remains truncated and unusable (section 2).
