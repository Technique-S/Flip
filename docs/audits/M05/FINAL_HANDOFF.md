# CircuitForge M0.5 — Final Handoff to Product Planning

**Decision:** CONDITIONAL GO — proceed only with the narrow **composition + behavioral diff + integrity manifest + X Layer pre-flight** scope (see `MVP_CONSTRAINTS.md`). Do not build a generic canvas.

## Top five findings that must shape architecture and scope

1. **Publication cannot be fully simulated read-only on the available RPC.** The 81-byte half-adder is STRUCTURALLY ACCEPTED by live X Layer §3 validation at the verified 0.0013 OKB fee, but `eth_call` storage overrides are rejected ("Invalid params") and `eth_estimateGas` fails with OutOfFunds at the transistor burn. Product must never present pre-flight as "simulation success" or "published" — only structural acceptance. (Gate A: PARTIAL)

2. **Processor proxy bytecode is not identity.** Every processor is a 295-byte beacon proxy; behavior lives behind a mutable beacon (`isSealed = 0`, factory impl already upgraded). A canonical manifest with chainId, block, netlist hash, dependency closure, factory impl slot, beacon impl + code hashes is REQUIRED; the prototype detected all 9 negative integrity fixtures. Cache imports by content hash + environment hashes and revalidate before every report/pre-flight. (Gate B: PASS)

3. **Wiring Canary is viable for stateless circuits but bounded.** SAT UNSAT proofs and simulation-verified minimized counterexamples work (including on an 8-input parity chain of 7 real XOR REFs); stateful LATCH equivalence needs bounded k-beat traces only. Solver timeouts must return UNKNOWN, never EQUIVALENT. Exact measured limits are in `WIRING_CANARY_SCALE.md`. (Gate C: see that report)

4. **The official canvas already covers far more than expected.** `tapeout.net` has on-chain REF loading, REF-authenticity/RPC-failure checks, BLIF import, X Layer support with 5 RPCs, cross-chain mismatch warnings, sub-circuit simulation limits, burn-cost estimation, and pre-send transaction simulation. `tapeout.pro` provides exhaustive verification vs a fixed task reference (BNB only). CircuitForge's only defensible gap is **arbitrary user-defined refactor-equivalence proofs + portable integrity manifests** for composed X Layer circuits. (Gate D: PARTIALLY DIFFERENTIATED)

5. **Native REF records are chain-blind.** Identical factory/processor addresses exist on X Layer (196) and Base (8453) with different state (nextId 104 vs 10). Every import, cache entry, and report must bind chainId explicitly.

## Architecture decisions to lock before implementation
- Backend-first verification service with local/cache-first simulation; browser UI is a thin client (see solver backend decision in `MVP_CONSTRAINTS.md` §6).
- Manifest-generation and integrity-check modules are mandatory shared components, not optional telemetry.
- Oracle/intent model must be explicit: spec vectors, trusted reference circuit, or previous version; otherwise report "behavioral diff only".
- Pre-flight uses read-only RPC with exact, honest status labels; no wallet/signing code in MVP.

## Blocking vs acceptable risks
- **Blocking for GO:** none that invalidate the narrow MVP; the two hard external unknowns (transistor acquisition path, real tapeout gas cost) affect the *authorized publication test*, not planning/implementation.
- **Acceptable implementation-stage risks:** competitive overlap (mitigate by strict scope), RPC endpoint reliability (configurable + multi-node later), stateful equivalence (explicitly deferred), fee mutability (re-read at runtime).

## Planning authorization
The evidence is sufficient to begin full MVP planning **provided the team accepts the exact boundaries in `MVP_CONSTRAINTS.md`**. If the team insists on a generic canvas/editor or unbounded stateful equivalence, this authorization is withdrawn and a pivot/redo cycle is required.
