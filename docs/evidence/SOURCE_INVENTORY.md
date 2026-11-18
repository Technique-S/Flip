# Source inventory and copied-artifact SHA-256 register — Flip M1-B

**Scope:** OpenCode fixture worktree `opencode/flip-m1-fixtures`, base commit `37c39b3cf06edad908a6c579b7b0a78f1b42c202`.
**Write paths used:** `docs/evidence/**` and `fixtures/**` only. No root config, schema, lockfile, package code, PRD, architecture doc or audit report was edited.

## 1. Source discovery result (candidate paths verified)

| Candidate path from task prompt | Exists? | What was found |
|---|---|---|
| `C:\research\circuitforge-feasibility\experiments` | **NO** | Canonical M0 audited location absent on this machine. |
| `C:\research\circuitforge-feasibility\m05-final-verification\experiments` | **NO** | Canonical M0.5 audited location absent on this machine. |
| `C:\research\circuitforge-feasibility` | YES | Contains only the seven markdown research reports (no `experiments/` tree). |
| `C:\Users\Kazi\Documents\Flip\experiments` | YES | Local copy of the M0 experiment tree (fixtures, results, src). Used as read-only source. |
| `C:\Users\Kazi\Documents\Flip\m05-final-verification\experiments` | YES | Local copy of the M0.5 experiment tree (fixtures, results, src, vendor). Used as read-only source. |

**Provenance limitation (important):** all `RAW_REPLAYED` artifacts below are byte-for-byte copies of the **local** `C:\Users\Kazi\Documents\Flip\...` copies. The canonical `C:\research\circuitforge-feasibility\...` originals are not present, so byte-identity with the originally audited files **could not be verified**. This is recorded as a blocker in `MISSING_ARTIFACTS.md`. No source directory was modified.

## 2. Provenance level definitions used here

| Level | Meaning |
|---|---|
| `RAW_REPLAYED` | Byte-for-byte copy of a raw experiment fixture/result file that is present on this machine and was produced by the original M0 / M0.5 runs. Safe to commit; usable as a regression input once a schema consumes it. |
| `READ_ONLY_REGENERATED` | Value or file derived by a bounded, read-only command executed during this task over the committed raw bytes. No network, no RPC, no invented data. |
| `REPORT_ONLY` | Asserted only in the narrative audit reports. No raw bytes/results are available from any accessible source, so it must **not** become an executable golden fixture. |

## 3. Copied artifacts (SHA-256 = original source hash = committed copy hash)

Every row was copied with `Copy-Item` (byte-preserving) and the source and destination SHA-256 values were compared; all 12 returned `MATCH`.

**Git ignore / byte-fidelity note:** the base commit's root `.gitignore` contains `/docs/evidence/raw/` ("avoid accidental large private audit source copies"). Root configs are outside this task's write scope, so `.gitignore` was **not** edited. The 12 specific files below were explicitly force-added; no other file under that ignored path was added. Each is small (< 40 KB), secret-scanned, and hash-registered here.

Git's system-level `core.autocrlf=true` would otherwise convert the source CRLF line endings to LF in the stored blobs, changing the committed bytes. To preserve the originals exactly, the 12 blobs were staged with `git hash-object -w --no-filters` + `git update-index --cacheinfo` (no config or `.gitattributes` file was created or edited). A post-stage `git cat-file blob` check confirmed all 12 staged blobs are byte-identical to their sources and carry the SHA-256 values listed below.

### 3.1 M0 — from `C:\Users\Kazi\Documents\Flip\experiments`

| Committed path | Bytes | SHA-256 | Level |
|---|---:|---|---|
| `docs/evidence/raw/M0/xlayer_circuits.json` | 18,711 | `a2627c31529985f3f97c55865a7adcd97522524477d2101e7a3cf49f5188dc30` | RAW_REPLAYED |
| `docs/evidence/raw/M0/vectors.json` | 22,185 | `1a02f5cf991c130a22dc6cc6ee93d0f8fe0720afed081665fa8b8018aefd203b` | RAW_REPLAYED |
| `docs/evidence/raw/M0/composition_poc.json` | 3,415 | `8c4632c5857e92960e1d861e0ab842397c95eb0af4941659c690f92cccb079b0` | RAW_REPLAYED |
| `docs/evidence/raw/M0/wiring_canary.json` | 7,224 | `7e2ae6a85e381a458b7103642e7848ccf61f4cf0f278ab1d7513b621dbddc5dc` | RAW_REPLAYED |

Source relative paths: `fixtures/xlayer_circuits.json`, `fixtures/vectors.json`, `results/composition_poc.json`, `results/wiring_canary.json`.

Note: `results/circuits_fetch_20261116_014841.json` is byte-identical to `fixtures/xlayer_circuits.json` (same SHA-256 `a2627c31…dc30`); the fixture copy was used.

### 3.2 M0.5 — from `C:\Users\Kazi\Documents\Flip\m05-final-verification\experiments`

| Committed path | Bytes | SHA-256 | Level |
|---|---:|---|---|
| `docs/evidence/raw/M05/gate_a_compose_rerun.json` | 6,836 | `9e9d4a996c8a98a63ea246cadc1a771222f67c8d455bda6772a63a9763fbe4c1` | RAW_REPLAYED |
| `docs/evidence/raw/M05/gate_a_probe.json` | 3,188 | `53ac183d1583f9824195c18f027f94945721b1c51ab4e2737b0859963164c9a2` | RAW_REPLAYED |
| `docs/evidence/raw/M05/gate_a_probe2.json` | 1,325 | `ba799a78a141e25dfb6ebb827fe7366004b56afe838bb8aba75f9a8083a4e9b1` | RAW_REPLAYED |
| `docs/evidence/raw/M05/gate_b_manifest.json` | 4,895 | `1e5a39c7226922c057a07f52fb32b64701f09b66b299aa1671ebbdcd5659a81e` | RAW_REPLAYED |
| `docs/evidence/raw/M05/gate_b_negative.json` | 2,932 | `592a72055c7b9a87097a97cee182b6747d76ba43da9813fecbd9e6147a4b1c31` | RAW_REPLAYED |
| `docs/evidence/raw/M05/gate_c_scale.json` | 36,860 | `3160ef631ee77a3b6d2e517151dc54f4d389490249ced259faa47d86def0850d` | RAW_REPLAYED |
| `docs/evidence/raw/M05/gate_c_scale_partial.json` | 32,210 | `51f27e63d694ab4267a8cffc92ee608249bc20a8522ba5db411d03a77101b15a` | RAW_REPLAYED |
| `docs/evidence/raw/M05/gate_c_stateful.json` | 3,137 | `57a5aa126f74ffaa9858f5d39d7db97e6a6b80a25e90c846fd2417c89d546264` | RAW_REPLAYED |

Source relative path for every M0.5 row above: `results/<filename>`.

`gate_a_compose_rerun.json` is UTF-16 LE with BOM (`FF FE`) in the original; it was copied verbatim, not transcoded. This is why its SHA-256 differs from the UTF-8 `composition_poc.json` even though the composed netlist bytes are identical.

### 3.3 Derived artifacts produced in this task

| Committed path | Bytes | SHA-256 | Level |
|---|---:|---|---|
| `docs/evidence/derived/recompute_checks.py` | 5,249 | `a77a6745489db48e056c05d2bbf514a5c98efb00eab78d0398f70d83e4f5102a` | READ_ONLY_REGENERATED |
| `docs/evidence/derived/recomputed_checks.json` | 2,754 | `6205df25c1e003d6acb3acb7d2356c453aea1e15b5c993c8584bb358b501c499` | READ_ONLY_REGENERATED |

Both derived files are written with explicit LF newlines and staged with `--no-filters`, so the committed blob SHA-256 equals the value above on every platform.

## 4. Observed source material intentionally NOT copied

These files exist in the read-only source trees but are outside the deliverable set, too large, third-party, or non-fixture source code. They remain available at their source paths.

| Source path (relative to source root) | Bytes | Reason not copied |
|---|---:|---|
| `experiments/fixtures/corpus.json` | 198,698 | Large corpus; not a named M1-B deliverable. |
| `experiments/results/corpus_scan2.json` | 199,389 | Large derived scan; not a named deliverable. |
| `experiments/results/*` (15 other result files) | 263–40,609 | Supporting M0 probe outputs (fee, processors, tapeout verdicts, semantics, scan logs). Not required deliverables; available at source. |
| `experiments/src/*.py` and `experiments/src/__pycache__/*.pyc` | up to 28,014 | Experiment source/bytecode, referenced in `REPRODUCIBILITY.md` but not fixture/result bytes. |
| `m05.../experiments/fixtures/TAP-10.md` | 109,187 | Large third-party specification document. |
| `m05.../experiments/fixtures/tapeout_net_bundle.js` | 1,569,344 | Large third-party fetched JS bundle (Gate D). Not committed. |
| `m05.../experiments/results/bundle_chains.json`, `bundle_features.json` | 8,831 / 20,634 | Gate D differentiation results; outside M1-B deliverables. |
| `m05.../experiments/results/gate_b_manifest_run.txt`, `gate_c_scale_run.txt` | 9,796 / 1,886 | Console run logs; originals remain at source path. |
| `m05.../experiments/src/*.py`, `__pycache__/*`, `vendor/**` | up to 3,663,360 | Experiment source and solver toolchain binaries (incl. `pysolvers.cp314-win_amd64.pyd`, `msvcp140*.dll`). Not fixtures/results; large binaries excluded. |
| `m05-final-verification/*.md` | 2,732–6,059 | Duplicate copies of the audit reports already present under `docs/audits/M05/` in the base commit. |

## 5. Secret and size review (performed before copying)

- Scanned 128 text files (`.json`, `.txt`, `.md`, `.py`) in both source trees with regexes for private keys, mnemonics, seed phrases, API keys, secrets, passwords, bearer/authorization headers, keystores, and 64-hex strings.
- **Result: no credentials found.** All matches were public on-chain data: netlist hex, ABI/storage values, ERC-1967 implementation slot constants, event/hash values, revert calldata, and contract bytecode. RPC URLs are public endpoints (`https://rpc.xlayer.tech`, `https://base-pokt.nodies.app`).
- Largest copied file: 36,860 bytes (`gate_c_scale.json`). No file over 40 KB was copied. Large binaries and bundles were excluded (section 4).
