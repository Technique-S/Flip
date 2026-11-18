# Fixture map (proposal only — no schema imported or invented)

**Status:** NON-EXECUTABLE mapping. Codex has not yet frozen the M1 schema (target `1.0.0` per `docs/architecture/FLIP_IMPLEMENTATION_DEPENDENCIES.md`). This file deliberately defines **no** new format, field name, enum, or validator. It records where each raw artifact lives today and which *already-named* future schema concept it is expected to feed. Actual field names, decimal-string IDs, address normalization, bit order, and verdict semantics must come from Codex's frozen schema, not from this file.

Raw bytes are committed under `docs/evidence/raw/M0/` and `docs/evidence/raw/M05/` (see `docs/evidence/SOURCE_INVENTORY.md`). Provenance levels and verified facts are in `docs/evidence/PROVENANCE_INDEX.md`; gaps are in `docs/evidence/MISSING_ARTIFACTS.md`.

## Future concepts named in existing architecture docs (not defined here)

| Concept named in Codex-owned docs | Source of the name |
|---|---|
| project / circuit identity, manifest, comparison result, pre-flight status, error codes, canonical serialization + hash | `FLIP_AGENT_OWNERSHIP_MATRIX.md` §6, M1-A prompt |
| golden fixtures for circuit identity / manifest / compare / pre-flight | `FLIP_IMPLEMENTATION_DEPENDENCIES.md` §1–2, G-01…G-10 |

## Mapping table (observed raw keys → intended future consumer)

| Raw artifact (committed path) | Observed top-level keys (verbatim from raw file) | Intended future schema concept | Level |
|---|---|---|---|
| `raw/M0/xlayer_circuits.json` | `rpc, chainId, headBlock, generated_utc, processors` | Circuit identity + chain/block context; source of XOR#1 / NAND#2 netlist bytes | RAW_REPLAYED |
| `raw/M0/vectors.json` | `chainVerified, format, illFormed, packing, packingEdgeCases, valid` | TAP-02 parser / validator golden and malformed-vector cases | RAW_REPLAYED |
| `raw/M0/composition_poc.json` | `sources, composedNetlist, composedNetlistBytes, deterministic, records, officialLoad, independentLoad, truthTable, semanticsPass, faultInjection, faultSummary` | Composition result, 81-byte netlist, truth table, mutation corpus, structural rejections | RAW_REPLAYED |
| `raw/M0/wiring_canary.json` | `experiment, circuits, satSelfTest, rows, scaleTest, wallSeconds` | Comparison result / SAT witness cases; behavioural mutation corpus | RAW_REPLAYED |
| `raw/M05/gate_a_compose_rerun.json` | same content as `composition_poc.json` (UTF-16 LE with BOM, preserved verbatim) | Independent rerun of the composed 81-byte netlist | RAW_REPLAYED |
| `raw/M05/gate_a_probe.json` | `errorSelectorCheck, proc0Getters, factoryGetters, circuitImplBytecode, push20CandidateProbes, proc0NonZeroLowSlots` | Read-only chain adapter / ABI + selector provenance context | RAW_REPLAYED |
| `raw/M05/gate_a_probe2.json` | `tokenCodeLen, tokenDirect, uri_0, overrideTest, overrideSupported, overrideBalanceResult, tapeoutSimFull, tapeoutEstimateGas, gasPriceWei, revertArgDecode` | Pre-flight structural classification + revert evidence (UNKNOWN, never success) | RAW_REPLAYED |
| `raw/M05/gate_b_manifest.json` | `rpcX, rpcBase, chainIdX, blockNumberX, blockHashX, tap02Version, testSuiteHash, manifests` | Manifest / circuit identity / dependency closure / environment hashes | RAW_REPLAYED |
| `raw/M05/gate_b_negative.json` | `baseline, negativeTests, liveChecks, allNegativeDetected` | Manifest negative test corpus (9 cases) | RAW_REPLAYED |
| `raw/M05/gate_c_scale.json` | `environment, timeouts, scales, correctnessSafeguards, statefulKBeat` | Comparison result verdict matrix (28 cases), safeguards, stateful traces | RAW_REPLAYED |
| `raw/M05/gate_c_scale_partial.json` | same keys as `gate_c_scale.json` | Checkpoint input to scale finalization | RAW_REPLAYED |
| `raw/M05/gate_c_stateful.json` | `circuit, mutant, initialState, inputSequence, beats, firstDifferenceBeat, traceOriginal, traceMutant, reproducible, scope, findings` | Bounded k-beat trace fixture (P1 / M6) | RAW_REPLAYED |
| `derived/recomputed_checks.json` | `label, generated_by, chain_block_provenance, recomputed_netlist_digests, counts, stateful_trace_matches_embedded_copy, preflight_revert_evidence` | Reviewer-facing sanity check only; not a golden input | READ_ONLY_REGENERATED |

## Rules for future Codex integration

1. Do **not** copy field names from this table into schema code. Read them from the frozen schema instead.
2. `REPORT_ONLY` claims in `MISSING_ARTIFACTS.md` must not be turned into fixtures by filling in values from prose.
3. `gate_a_compose_rerun.json` must not be transcoded; its SHA-256 in `SOURCE_INVENTORY.md` assumes the original UTF-16 LE bytes.
4. Decimal-string IDs, address normalization, bit-order annotation, and verdict semantics stay Codex-owned (`FLIP_AGENT_OWNERSHIP_MATRIX.md` §6).
5. No file in `fixtures/` or `docs/evidence/` is production code or a schema artifact.
