# Cross-Gate Security Review (architecture-relevant findings only)

| Issue | Severity | Evidence | Mandatory MVP mitigation | Containable by scope? |
|---|---|---|---|---|
| Malformed / malicious imported netlist (huge REF arity, deep REF chain, forward refs, oversized signals) | High | TAP-02 §7 explicitly requires bounded decoding/evaluation; `decode()` allocates by count fields | Validate §3 before simulation; cap records, REF depth, expanded gates, input width; reject on breach | Yes — reject anything outside declared limits |
| Recursive REF dependency exhaustion | High | REF records are 32 bytes but can expand to thousands of gates (core #9 = 2,355 gates); canvas has `cv.refTooBig`, `mn.e.REF_TOO_DEEP` | Cycle/depth budget + memoized expansion; UNKNOWN on breach | Yes |
| Misleading interface metadata / missing pin names | Medium | TAP issue #44 claims an undeployed circuit; no onchain port metadata | Never infer intent from pin order alone; require explicit oracle; label Mode C as "behavioral diff only" | Yes |
| Incorrect chain binding | High | Same processor addresses on X Layer (196) and Base (8453), different nextId (104 vs 10) | Manifest chainId + RPC eth_chainId check; reject cross-chain | Yes |
| Processor / factory implementation upgrade | High | factory isSealed=0; impl differs from TAP-10 docs; beacon mutable | Pin impl slots + code hashes in manifest; revalidate before report/pre-flight | Partially — upgrades remain possible, must be detected |
| False equivalence claim | Critical | Solver timeout would otherwise be mistaken for UNSAT; stateful unbounded proof unsupported | Only UNSAT ⇒ EQUIVALENT; witness must reproduce under ref.beat; timeout/missing oracle ⇒ UNKNOWN; stateful = k-beat only | Yes |
| Solver denial of service | Medium | Pure-Python DPLL timed out at hundreds of gates in early runs | Hard per-check timeout + memory budget; prefer CDCL Minisat22; return UNKNOWN on breach | Yes |
| Cached-data integrity | Medium | Beacon can change while netlist hash stays constant | Content-addressed cache keyed by netlist hash + env hashes; hash re-verify on use | Yes |
| RPC inconsistency / malicious provider | Medium–High (unproven) | Prototype detects synthetic divergence only; live multi-node agreement not implemented | Treat single-RPC reads as unverified; do not claim malicious-RPC resistance; adopt TAP-10 §5 multi-operator agreement later | Deferred to post-MVP, explicitly disclaimed |
| Unsafe publication assumptions | High | `eth_call` storage override unsupported; estimateGas OutOfFunds; real gas/token acquisition unverified | Pre-flight labels STRUCTURALLY ACCEPTED / REJECTED / UNKNOWN only; never broadcast; re-read fee each session | Yes |
