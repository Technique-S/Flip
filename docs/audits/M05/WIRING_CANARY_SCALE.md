# Gate C — Wiring Canary Scalability and Correctness

## Status: **PASS** (with explicit, measured MVP limits)

All experiments use deterministic chains of real `REF(XOR#1)` imports from X Layer processor 0 (each REF flattens to 4 NAND gates). Environment: Python 3.14.6, Windows 11, Intel64; solvers: **python-sat 1.9.dev22 Minisat22** (isolated `vendor/` wheel) and the original **pure-Python DPLL** from `wiring_canary.py`. Hard per-case timeout: **8 s** → verdict UNKNOWN on breach. Evidence: `experiments/results/gate_c_scale.json`, `gate_c_scale_partial.json`, `gate_c_stateful.json`.

## C1. Reproduction of earlier findings (VERIFIED)
- Half-adder self-equivalence (false-positive regression): `diffFound=False` ✓
- Original 4 half-adder mutations + 8-input parity scale test: re-run and confirmed from the prior audit (`wiring_canary.json`); SAT witnesses verified by `ref.beat`.
- Reversed symmetric-gate rewiring → UNSAT EQUIVALENT; duplicated fan-out / output permutation → SAT DIFFERENT with witnesses; all confirmed again here.

## C2/C3. Scale benchmarks (VERDICT SUMMARY)

4 modes at each target: `self` (identical), `equivalent` (symmetric port reversal), `different` (duplicated fan-out), `fault_reverse_one` (structurally valid symmetric rewiring). Expected: EQUIVALENT / EQUIVALENT / DIFFERENT / EQUIVALENT.

| Gates (actual) | nIn | CNF clauses / vars | Minisat22 verdicts (4 modes) | Minisat22 median time | Minisat22 peak mem |
|---|---|---|---|---|---|
| 50 (48) | 13 | 293 / 112 | E / E / D / E — all match | 147–160 ms | ~3.25 MiB |
| 100 | 26 | 605 / 229 | E / E / D / E — all match | 147–160 ms | ~3.29 MiB |
| 250 (248) | 63 | 1,493 / 562 | E / E / D / E — all match | 157–191 ms | ~3.4 MiB |
| 500 | 126 | 3,005 / 1,129 | E / E / D / E — all match | 184–222 ms | ~3.6 MiB |
| 1,000 | 251 | 6,005 / 2,254 | E / E / D / E — all match | 272–303 ms | ~4.1 MiB |
| 2,500 | 626 | 15,005 / 5,629 | E / E / D / E — all match | 389–600 ms | ~5.3 MiB |
| 5,000 | 1,251 | 30,005 / 11,254 | E / E / D / E — all match | 684–1,384 ms | 7.4–7.9 MiB |

- **Every SAT witness for the `different` mode was independently verified by direct `ref.beat` evaluation** (both circuits, same input) — no unverified counterexample is reported.
- Minisat22 decisions are **100% correct vs expected** across all 28 scale cases.
- Scaling is near-linear in gate count; the 5,000-gate case completes in ~1.4 s with <8 MiB peak memory.

### Pure-Python DPLL comparison (measured, not inferred)
| Gates | Result |
|---|---|
| 48 | UNSAT cases ~3.2–3.5 s; SAT case ~22 ms |
| 100 | all UNSAT cases hit the 8 s timeout → **UNKNOWN** (correct behavior, unusable speed) |
| ≥250 | all cases timeout → UNKNOWN; backend skipped above 500 gates (marked SKIPPED/UNKNOWN) |

CDCL Minisat22 is ~20× faster at 48 gates and is the only viable backend beyond ~50 gates. Timeout correctly maps to UNKNOWN in every case — never to EQUIVALENT.

## C4. Correctness safeguards (`gate_c_scale.json`, all 7 PASS)
1. Malformed source (NAND forward ref) rejected by `ref.load` ✓
2. Incorrect REF expansion (wrong resolver) detected by output mismatch on a distinguishing input ✓ *(initial test input [1,1] could not distinguish XOR from NAND — fixed to [0,0]; test-fixture bug, documented)*
3. Reversed symmetric ports → EQUIVALENT (UNSAT) ✓
4. Duplicated fan-out → DIFFERENT + sim-verified witness ✓
5. Output permutation → DIFFERENT ✓
6. Solver timeout → UNKNOWN (enforced by harness construction) ✓
7. Half-adder self-equivalence regression → False positive absent ✓

## C5. Stateful circuit decision (VERIFIED PoC)
- Bounded **k-beat trace comparison** is feasible with zero new solver machinery: using the official TAP-02 `toggle` vector (LATCH, nState=1) and a mutant (LATCH `d` → const 1), 8 beats from all-zero state with deterministic inputs produced a first output/state difference at **beat 0**, and the trace is **fully reproducible** (`gate_c_stateful.json`).
- Initial state is a user/oracle choice (zero-state is a convention); input sequences are explicit vectors; mismatches reproducible from recorded trace.
- **Recommendation: include bounded k-beat trace diff in MVP (k ≤ 8); DEFER unbounded stateful equivalence.**

## C6. Evidence-based MVP limits (adopted in `MVP_CONSTRAINTS.md` §6)
- **Default solver:** Minisat22/CDCL (WASM or local native); pure-Python DPLL fallback ONLY for ≤50 gates.
- **Verified max circuit size:** 5,000 equivalent gates (30k clauses, 11.3k vars, 1.4 s, <8 MiB). Recommended default cap **2,500 gates** (2× headroom, ~0.6 s); allow manual raise to 5,000.
- **Verified max REF count / depth:** 1,250链式 REFs (linear chain depth 1,250). Deep *nested* REF trees not separately measured — cap nesting conservatively (e.g., 64) pending further tests.
- **Verified max external input width:** 1,251 bits.
- **Hard timeout:** 5 s/check for MVP (measured worst case 1.4 s); memory ceiling 64 MiB (measured worst case 7.9 MiB).
- **Execution:** local-first (WASM/browser feasible at measured sizes); backend only for larger/enterprise use.
- **Bounded testing:** stateful k ≤ 8; return UNKNOWN for unbounded stateful or missing oracle.
