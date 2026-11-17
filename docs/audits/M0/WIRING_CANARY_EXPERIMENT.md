# Wiring Canary Experiment (Investigation D)

## 1. Objective & Hypothesis

Structural validation (TAP-02 §3) only checks arity, opcode validity, and backward signal references. It **cannot** detect semantic wiring mistakes such as swapped outputs, misrouted pins, or duplicated fan-out. The Wiring Canary experiment tests whether automated behavioral validation (exhaustive, randomized, and exact SAT equivalence checking) can catch these mistakes on real composed X Layer circuits and produce minimal counterexamples.

## 2. Experimental Setup

- **Base circuit:** Composed half-adder (`compose_poc.py`, 81 bytes) built from real X Layer `proc0#2` (NAND) + 1 glue `NAND` + `proc0#1` (XOR), `nIn=2, nOut=2`, outputs `(carry, sum)`.
- **Four structurally valid mutations:**
  1. `mutant1`: reversed inputs `(b, a)` into both `REF`s (behaviorally **equivalent** — NAND and XOR are symmetric).
  2. `mutant2`: swapped inputs `(b, a)` into XOR `REF` only (behaviorally **equivalent**).
  3. `mutant3`: glue `NAND` wired to input bit `a` instead of `NAND` output (`carry = NOT(a)` — **wrong wiring**).
  4. `mutant4`: outputs ordered `(sum, nand)` instead of `(carry, sum)` (**wrong wiring**).
- **Scale test (`nIn=8`):** 8-input parity chain built from **7 real `proc0#1` (XOR) `REF` imports** (flattens to 28 NAND gates), compared against a realistic fan-out bug where the 3rd XOR reads raw input `a2` instead of the running parity. Both pass TAP-02 §3 well-formedness.
- **Techniques compared:**
  1. Exhaustive enumeration (`n <= 16` budget)
  2. Randomized property testing (64 samples)
  3. Exact SAT counterexample search (recursive `REF`-inlining Tseitin CNF encoder + pure-Python DPLL)

## 3. Debugging Note (Caught by Exhaustive Oracle)

The first draft of `exact_search()` produced **false positives** (`DIFFERENT` with witness `[0, 0]`) on `mutant1` and `mutant2`. Root-cause analysis identified four bugs: (1) raw signal indices colliding with CNF variable IDs and constant `1`, (2) `REF` sub-circuit inputs left unbound, (3) broken negative-literal offsetting, and (4) forcing all outputs to differ simultaneously. Replacing it with `_SymEnc` (separate signal→literal map, shared input literals, recursive `REF` inlining, per-output difference indicators `d_i` with `OR(d_i)`) and adding a `base vs base` UNSAT self-test resolved all discrepancies.

## 4. Results (`results/wiring_canary.json`)

| Test Case | Ground Truth (Exhaustive) | Randomized (64) | Exact SAT (Tseitin + DPLL) | Clauses / Time |
|-----------|---------------------------|-----------------|----------------------------|----------------|
| Self-test (`base vs base`) | EQUIVALENT | — | **UNSAT (EQUIVALENT)** | 55 clauses |
| `mutant1` (reversed both REFs) | EQUIVALENT (8 evals) | No diff (8 evals) | **UNSAT (EQUIVALENT)** | 55 clauses / 0.48 ms |
| `mutant2` (XOR swapped) | EQUIVALENT (8 evals) | No diff (8 evals) | **UNSAT (EQUIVALENT)** | 55 clauses / 0.44 ms |
| `mutant3` (glue wired to `a`) | DIFFERENT `[0,0]` | DIFFERENT `[0,0]` | **SAT `[0,0]`** (verified by `beat()`) | 55 clauses / 0.31 ms |
| `mutant4` (outputs swapped) | DIFFERENT `[0,0]` | DIFFERENT `[1,0]` | **SAT `[0,0]`** (verified by `beat()`) | 52 clauses / 0.30 ms |
| **Scale (`parity8` vs dup input)** | DIFFERENT `[1,0,0,0,0,0,0,0]` | — | **SAT `[0,1,0,0,0,0,0,0]`** (verified by `beat()`) | 173 clauses / 11.02 ms |

- **100% agreement** between Exact SAT and exhaustive ground truth across all cases.
- **Scale test proof:** Both `parity8` and its duplicated-input mutant flatten to 28 NAND gates and pass TAP-02 §3 structural validation; SAT locates a 1-bit counterexample in 11.02 ms without enumerating `2^n` inputs.

## 5. Three Oracle Modes & Product Implication

1. **Mode A (Declared Spec / Truth Table / Reference Vector):** Unambiguously flags `mutant3` and `mutant4` as `WIRING DOES NOT MATCH DECLARED SPEC` with exact mismatching input vectors.
2. **Mode B (Trusted Reference Circuit / Refactor Equivalence):** Proves `mutant1`/`mutant2` equivalent (UNSAT) and flags `mutant3`/`mutant4` as regressions.
3. **Mode C (Unknown Intent — No Spec or Reference):** Can only report whether two wirings are distinguishable or equivalent. **Key finding:** Wiring Canary is **not** a magic "find bugs with zero user input" oracle; it requires at least one intent anchor (a spec, test vectors, a previous version, or pin-name/port metadata).

## 6. Known Limitations

- **Stateful (`LATCH`) circuits:** `_SymEnc` currently rejects `LATCH` (`ValueError`). Supporting sequential circuits requires k-step unrolling (bounded model checking) or inductive equivalence checking, which adds solver complexity.
- **Pure-Python DPLL:** Sufficient up to ~hundreds of gates; production CircuitForge should use a WASM/native CDCL solver (e.g., MiniSat/CaDiCaL/Z3) for >1,000-gate compositions.
