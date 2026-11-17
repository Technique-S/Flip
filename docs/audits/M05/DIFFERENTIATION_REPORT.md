# Gate D — Competitive Differentiation

## Status: **PARTIALLY DIFFERENTIATED**

## D1. Direct competitor feature comparison (evidence-based)

Evidence: direct fetch/inspection on 2026-11-16 — official `tapeout.net` HTML + its 1.47 MB Vite JS bundle (`experiments/fixtures/tapeout_net_bundle.js`, feature strings in `experiments/results/bundle_features.json`); `tapeout.pro` homepage text; `tapeout.link` (TapeOut.build) description; TapeKit README from GitHub.

| Capability | `tapeout.net` (official canvas) | `tapeout.link` / TapeOut.build | `tapeout.pro` | CircuitForge PoC (this audit) |
|---|---|---|---|---|
| Import deployed TapeOut circuits | **YES** — loads referenced sub-circuits from chain (`cv.refLoading`, `cv.refFail`); BLIF import (Yosys/ABC/SIS) | BLIF export/simulation, not onchain import | UNKNOWN | YES (X Layer `eth_call` + local cache) |
| Recursive REF dependency inspection | **YES** (`cv.refTooBig`, `mn.e.REF_TOO_DEEP`, sub-circuit fetch + integrity checks) | UNKNOWN | UNKNOWN | YES (manifest closure) |
| REF integrity checks | **YES** — `cv.refNotRegistered` (fake processor), `cv.refUnverified` (RPC-failure → refuse), pre-flight fetch before burn | UNKNOWN | UNKNOWN | YES (9 negative fixtures) |
| Connect independently deployed circuits | Partial — canvas advises "split into multiple circuits and compose with REF" (`cv.blifNearLimit`, `cv.msgTooBig`) | UNKNOWN | NO | YES (deterministic 81-byte composition) |
| Automatic signal ordering | YES (canvas compiler; BLIF goes through "exactly the same compile path") | YES (wire editor) | N/A | YES (backward-reference build) |
| Deterministic composed-netlist generation | YES (canvas compile) | YES | N/A | YES (100× identical) |
| Named interface mapping | UNKNOWN (pin names in BLIF/canvas; no onchain port metadata per TAP issue #44) | UNKNOWN | UNKNOWN | NOT IMPLEMENTED |
| Behavioral equivalence checking | **NO arbitrary user-facing feature** (0 occurrences of "equivalent" in bundle; CE features are PoD-task-specific) | NO | **YES** — exhaustive vs on-chain task reference, all inputs, exact differing input (BNB Chain only) | YES — SAT UNSAT proof + verified counterexamples (stateless) |
| Automatic counterexample generation | PoD-only (`pod.ce.*`: verify/register on-chain CE for leaders) | NO | YES (task CE) | YES (minimized, sim-verified) |
| Refactor-regression checking (arbitrary circuits) | NO | NO | Partial (vs fixed reference only) | YES (Mode B) |
| X Layer publication pre-flight | YES (X Layer chain config with 5 RPCs; tx simulated before sending; fee/burn checks) | UNKNOWN | NO (BNB-focused) | YES (read-only §3 validation via `eth_call`) |
| Cross-chain address collision handling | YES — `cv.l2NotFound` / `cv.l2Mismatch` warn that the same address on different chains is a different contract and check wallet-vs-site reads | UNKNOWN | UNKNOWN | YES (manifest chainId binding) |
| Reproducible verification reports | NO (UI state) | NO | Partial | YES (canonical manifest + hashes) |

**Adverse evidence for CircuitForge:** the official canvas is considerably richer than the prior audit assumed. It already performs on-chain REF loading, REF-processor authenticity checks, sub-circuit simulation with depth/size limits, BLIF import, burn-cost estimation, netlist-size warnings with "compose with REF" guidance, X Layer chain config with 5 RPC endpoints, explicit same-address-different-chain warnings (`cv.l2NotFound`, `cv.l2Mismatch`), and transaction re-simulation before sending. A "NAND canvas + simulator + REF loader + chain warning" product would be **REDUNDANT**.

## D2. Demonstrated differentiated workflow (VERIFIED locally)

Using the same artifacts as the audit:
1. **Import** real X Layer processor 0 #1 (XOR) and #2 (NAND) — manifest with hashes (`gate_b_manifest.json`).
2. **Compose** into 81-byte half-adder (`gate_a_compose_rerun.json`).
3. **Inject valid wiring defect** — duplicated fan-out / glue-to-input / output permutation (`wiring_canary.json`, `gate_c_scale.json`).
4. **Generate counterexample** — SAT witness, verified by `ref.beat` (e.g., `[0,1,0,0,0,0,0,0]` on the 8-input parity chain), minimized.
5. **Correct defect → verify** — SAT UNSAT proves equivalence of symmetric-gate rewiring; self-equivalence regression check passes.
6. **Publication pre-flight** — `eth_call` at 0.0013 OKB: well-formed netlist passes §3 to transistor burn; controls rejected (`gate_a_probe*.json`).

Existing tools already cover steps 1–2 (canvas REF loading + composition advice), parts of 3–4 (`tapeout.pro` vs a *fixed* task reference; canvas PoD CEs), and part of 6 (canvas tx re-simulation). The integrated combination for **arbitrary user-defined refactor/regression comparisons**, with a **portable integrity manifest** and a **stateless SAT UNSAT equivalence proof**, is not established in any inspected tool.

## D3. Honest uniqueness assessment

- **Genuinely missing from inspected tools:** arbitrary circuit-vs-circuit (*not task-reference*) equivalence proofs with minimized, simulation-verified counterexamples; portable canonical dependency/execution-integrity manifests for X Layer verification snapshots.
- **Integration of existing techniques:** SAT/Tseitin equivalence checking is a standard technique (not novel); TAP-10 already defines multi-node agreement and pinned-block identity that CircuitForge should adopt rather than reinvent.
- **Solves a documented failure:** yes — TAP issue #44 (semantic port mapping) leaves mapping intent ambiguous; TAP-02 §7 requires verifiers to record block/ref closure/beacon impl, which the manifest does; the official canvas itself disables tape-out while REF sub-circuits are unverified, showing the need.
- **Competitor reproduction difficulty:** low-to-medium for equivalence (tapeout.pro could extend beyond task references); medium for a full X Layer composition + manifest workflow.
- **No user-based measurement** was performed: **10× productivity claims are explicitly NOT made**.

## D4. Verdict & narrowest positioning

**PARTIALLY DIFFERENTIATED.** Recommend positioning CircuitForge as:

> **An X Layer circuit-composition and behavioral-diff workbench: import deployed circuits as chain-bound REF dependencies, compose deterministically, prove stateless refactor equivalence with SAT (or emit minimized counterexamples), pin an integrity manifest of the whole dependency/beacon environment, and run read-only publication pre-flight.**

Do **not** position it as a generic NAND editor, BLIF importer, simulator, or task verifier — those are already served.
