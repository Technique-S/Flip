# CircuitForge — M0.5 MVP Technical Constraints (planning contract)

This document defines **what may safely be specified** during product planning. It is not a design document. All constraints are derived from the M0.5 verification evidence; items marked TBD will be finalized from `experiments/results/gate_c_scale.json`.

## 1. Supported network
- **X Layer mainnet only** (`chainId = 196`, RPC `https://rpc.xlayer.tech`). No testnet for MVP: X Layer testnet reports `chainId = 1952` and has no factory at the shared address (M0 audit).
- Every imported circuit must carry `(chainId, processor, circuitId)`; native REF records (cpu,id) are chain-blind and the same addresses exist on Base (8453) with different state. Reject cross-chain inputs explicitly.
- RPC `eth_chainId` must be verified per session; do not trust labels from URLs.

## 2. Supported circuit types
- **Stateless (`nState = 0`) netlists**: full import, compose, simulate, and SAT equivalence proof.
- **Stateful (`LATCH`, nState > 0)**: bounded **k-beat trace comparison only** (zero-state convention + user-supplied input sequence); never claim unbounded equivalence.
- Import must reject malformed netlists (TAP-02 §3) before simulation and before REF resolution.

## 3. Import behavior
- Read-only `eth_call` for `nextId`, `circuitInfo`, `netlist`, factory/beacon state; all results decoded with explicit ABI validation.
- Pin an integrity manifest per circuit: chainId, processor, id, block number/hash, netlist hash, dependency closure, factory implementation slot + code hash, beacon implementation + code hash, processor code hash, TAP-02 version, test-suite hash.
- Cache only content-addressed by netlist hash **plus** environment hashes; revalidate environment hashes before export/pre-flight. Treat beacons as mutable (`isSealed = 0`).
- Defend against decoder resource exhaustion: bound records, REF depth, total expanded gates before evaluation (TAP-02 §7).

## 4. Composition limitations
- Deterministic netlist generation with automatic backward-reference ordering; reject forward refs except LATCH `d`.
- REF targets must be registered processors with existing circuits at compose time (`isCPU`, `circuitInfo`).
- No semantic port names (TAP issue #44 is unresolved/no deployment): require explicit pin-index intent from the user; otherwise report "behavioral diff only, intent unknown".

## 5. Verification guarantees
- **EQUIVALENT**: only when the SAT backend returns UNSAT for two stateless nets over the same TAP-02 §4 semantics; proof is relative to the declared reference version + test suite.
- **DIFFERENT**: only when a SAT witness is reproduced by the trusted `ref.beat` evaluator on both circuits; show minimized counterexample.
- **UNKNOWN**: on timeout, resource ceiling, malformed input, missing oracle/reference, or stateful unbounded request. A timeout must never be reported as EQUIVALENT.
- No claim of correctness without an oracle (spec vector, trusted reference circuit, or previous version).

## 6. Solver limits & runtime architecture (set from Gate C measurements)
- Default backend: **Minisat22/CDCL** (isolated wheel verified; use WASM/native build for browser). Pure-Python DPLL only as a ≤50-gate reference fallback (timed out at 100 gates).
- **Verified maxima:** 5,000 equivalent gates (30,005 clauses, 11,254 vars, 1.4 s, 7.9 MiB peak); 1,250 chained REFs; 1,251 external input bits — all with 100% correct verdicts and simulation-verified witnesses.
- **Recommended MVP caps:** default 2,500 gates (≈0.6 s); allow manual raise to 5,000; conservative REF nesting cap 64 (deep nested trees not separately measured); 5 s hard timeout/check; 64 MiB memory ceiling.
- Execution: local-first (WASM/browser feasible at measured sizes); backend optional for larger.
- Hard rule: timeout / limit breach / missing oracle ⇒ UNKNOWN (never EQUIVALENT). Every DIFFERENT witness must be reproduced by `ref.beat` before display.
- Stateful: bounded k-beat trace diff only (PoC k=8 at zero state, reproducible); unbounded equivalence excluded.

## 7. Dependency integrity requirements
- Every verification report must embed the canonical manifest (or its hash) of both compared circuits, including dependency closure and environment hashes.
- The checker from Gate B must be applied before any report is marked valid; all 9 negative fixtures must continue to be detected in CI.
- Cross-chain address collisions and processor impl changes must invalidate cached reports.
- Do not claim protection against malicious RPC operators; TAP-10 multi-operator agreement is a future requirement, not an MVP claim.

## 8. Pre-flight capabilities
- Read-only `eth_call` at the **current onchain fee** (verified 0.0013 OKB at time of audit; re-read `TAPEOUT_FEE()` each session because `isSealed = 0`).
- Allowed labels: **STRUCTURALLY ACCEPTED** (passed §3 to burn), **REJECTED** (specific §3 reason), **UNKNOWN** (RPC failure/override unavailable).
- Never claim SIMULATION SUCCESS or REAL PUBLICATION. No transaction broadcast, no wallet connection, no token acquisition, no fee payment in MVP.

## 9. Explicit exclusions
- Generic NAND drawing canvas, BLIF/Verilog editor/compiler, task-challenge verifier (all covered by existing tools).
- Wallet/signing flows, transistor mint/purchase, publication transactions.
- Unbounded sequential equivalence, malicious-RPC resistance, mobile native apps.
- Any 10× productivity claim (no user-based measurement performed).

## 10. Remaining unresolved assumptions (must be tracked in planning)
- Transistor token acquisition path on X Layer (documented as ERC-1155 mint; not executed here).
- Gas cost of a real `tapeout()` transaction (`eth_estimateGas` blocked by burn revert); cost in OKB beyond the 0.0013 fee unknown.
- Whether TapeOut fee/burn rules change via factory upgrade before hackathon deadline (Dec 7, 2026 23:59 UTC).
- Competitive overlap: official `tapeout.net` already implements much of import/compose/preflight — positioning must stay on refactor-equivalence + integrity manifests.
