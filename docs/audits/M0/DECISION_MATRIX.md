# Decision Matrix

Criteria weighted for pre-development feasibility of **CircuitForge** targeting the OKX **X Layer TapeOut Accelerate** hackathon (deadline **Dec 7, 2026 23:59 UTC** — ~3 weeks remaining from Nov 16, 2026).

| Dimension | Weight | Score (1–10) | Rationale (Evidence-Backed) |
|-----------|--------|--------------|-----------------------------|
| **1. Core Technical Feasibility** | 30% | **9 / 10** | TAP-02 semantics 18/18 vectors + 35/35 corpus circuits (224 evals, 15 stateful, 2 `REF` wrappers) verified with 0 mismatches; real X Layer `REF` composition + live `eth_call` §3 acceptance verified; pure-Python sim runs at ~0.3 µs/gate; SAT Wiring Canary works in 0.3–11 ms. |
| **2. X Layer Readiness & Economics** | 20% | **7 / 10** | Mainnet `196` works cleanly, gas is negligible (~0.02 gwei, 56k gas/eval), `TAPEOUT_FEE` verified at `0.0013 OKB`. Deducted 3 pts for: no testnet factory at shared address (`1952`), unsealed/upgradeable factory (`isSealed=0`), and 1.3s public RPC latency. |
| **3. Ecosystem Differentiation** | 25% | **6 / 10** | `tapeout.net`, `TapeOut.build`, and `tapeout.pro` already cover basic editing, BLIF export, and task-spec verification. Differentiation exists specifically in **multi-`REF` composition, dependency inspection, and refactor/wiring diffing** (validated by TAP issues #44 & #50). |
| **4. Hackathon Fit & 3-Week Delivery** | 15% | **8 / 10** | Developer tools explicitly eligible for the 100,000 USDT pool; requires X Layer processor address + circuit ID + ≤3 min video. A focused composition + Wiring Canary + pre-flight CLI/web tool is realistic in <3 weeks; full stateful SAT is not. |
| **5. Security & Trust Boundaries** | 10% | **6 / 10** | Read-only client-side architecture avoids custody risk, but `isSealed=0` + cross-chain `REF` address collisions (X Layer vs Base) require explicit integrity checks and chain-binding in metadata. |

**Weighted Score:** `0.30(9) + 0.20(7) + 0.25(6) + 0.15(8) + 0.10(6) = 2.70 + 1.40 + 1.50 + 1.20 + 0.60 =` **7.40 / 10**

## Verdict Mapping

- **GO** (≥ 8.0, low overlap, no major caveats)
- **CONDITIONAL GO** (6.5 – 7.9, technically sound, requires tight scope/differentiation) ← **CircuitForge is here**
- **PIVOT** (4.5 – 6.4, core thesis blocked or redundant)
- **NO-GO** (< 4.5, infeasible)

**Verdict: CONDITIONAL GO** — Proceed **only** with the scoped **Composition + Wiring Canary + X Layer Pre-Flight** MVP; do **not** build another generic NAND drawing canvas.
