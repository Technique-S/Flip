# Flip M3-B — independent composition and SAT verification corpus handoff

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).
**Branch:** `opencode/flip-m3-verification-corpus`. **Worktree:** `flip-m3-verification`.
**Base commit:** `b71e48e4ad29b352a166230b8644a26f11c5fba8`.
**Scope:** fixtures and evidence only. No production package, schema, lockfile,
CI configuration, Codex branch, raw M0/M0.5 evidence or accepted fixture bytes
was modified. No merge into `main`. No wallet, signing, transaction, onchain
publication or live RPC call. **Stop at M3-B.**

## 0. Setup deviation (recorded, not silently reconciled)

The task required confirming that PR #2 was merged into `main`. At corpus
creation GitHub reported:

- PR #2 (`codex/flip-m2-integration`, "Integrate M2 importer and adversarial
  acceptance with verified fixes") was **OPEN**, `mergedAt: null`,
  `mergeCommit: null`.
- `main` was still the PR #1 merge commit
  `8e9b6b928b5d08b7383ae2413dec26d6068ea44e`.

I therefore treated the head of PR #2, `b71e48e…`, as the accepted M2 commit and
based this isolated branch on it. This is the same class of recorded deviation
used by M2-B (which was based on `5f8a04b` while `main` lagged). The deviation
is intentional, visible in the branch ancestry, and does not alter `main`.

## 1. Fixture inventory

All authored artifacts are under `fixtures/m3-verification/` and
`docs/evidence/m3-verification/`. Generators are stdlib-only Python 3.14.6.

| File | Bytes | SHA-256 | Purpose |
|---|---:|---|---|
| `fixtures/m3-verification/circuits/golden-compositions.json` | 162,585 | `fac7da30ba27047af1dbfef3f0bcfe43c93a82e0cf8609824b2354aacd7285c0` | Task A: 10 golden compositions |
| `fixtures/m3-verification/sat/sat-corpus.json` | 57,965 | `5823c5af97f4970aae2284a8f997856048f7bdbf98e135f8668c4ee356411fd2` | Task B: 17 SAT cases |
| `fixtures/m3-verification/witnesses/witness-corpus.json` | 12,796 | `fa5a6642fffeddb971c1a93b07ab31fb2a2a0759cec0d6283103cd40a71f312d` | Task C: 8 replayed witnesses |
| `fixtures/m3-verification/proof-attacks/attack-corpus.json` | 22,072 | `753e20b37111491e73caee1befa4ef24c59801ed4c018d8c58e95be3338ba3a8` | Task D: 12 attack specs |
| `fixtures/m3-verification/benchmarks/benchmark-corpus.json` | 534,927 | `795a3b2cccc429dbc9ee3efd1f4eeb5d019974eeb64b34249954135d8b4e76f8` | Task E: 7 sizes × 3 modes |
| `fixtures/m3-verification/results/verification-results.json` | 1,001 | `76e53063d825038cb9f6ecd9c91981ef4a996b54166ba077ed68710acbd8f3b0` | Generation-time summary |
| `fixtures/m3-verification/results/benchmark-measurements.json` | 60,352 | `b75bf4af43b28758b362f1ea666b38726aa1be472dff3daa04fc645fe7cc1fc8` | Benchmark observations |
| `fixtures/m3-verification/MANIFEST.json` | — | register | Hash/size register |
| `fixtures/m3-verification/BUILD_INFO.json` | — | — | Seeds, generator/core hashes, base commit |
| `fixtures/m3-verification/generators/build_corpus.py` | — | `89dc4cac79bf298540c4acaa24ac4e59d5e4507071e128f4ba65f2d323d06c73` | Deterministic builder |
| `fixtures/m3-verification/generators/m3_core.py` | — | `84895734a14862178989b659e2bd0e05c9c6c8b8ad498e6ad162831066c0ad85` | TAP-02 core + dual evaluator + DPLL |
| `fixtures/m3-verification/generators/verify_corpus.py` | 8,613 | `18c2c3d42f15a2b80c10e298930d34adf603f02cb80c9b9a39b1808f6ef37646` | Independent verifier |
| `docs/evidence/m3-verification/manifest.json` | 2,301 | `71cc0c49cbad68757f30f3851397bdb9bb966073450e8f10da083e52a2cc5cbb` | Machine-readable handoff manifest |
| `docs/evidence/m3-verification/verification-transcript.json` | 2,471 | `80f8686aac09358c8f7f205b905d16a1f8ca5cd243d79e818cc5e9a2b0e7d0d2` | Executed-check transcript |

`fixtures/m3-verification/.gitattributes` (`* -text`) preserves exact fixture
bytes on Windows and Linux. Authored fixtures contain no timestamps or host-dependent
values; only `results/*.json` carry timing.

## 2. Exact regeneration commands

```powershell
# from the flip-m3-verification worktree root; Python 3.14.6, stdlib only
python fixtures/m3-verification/generators/build_corpus.py
python fixtures/m3-verification/generators/verify_corpus.py
```

Generation seed: `20261118` (`BUILD_INFO.json`, `MANIFEST.json`, benchmark
per-size seeds `20261118 + target_gates`). `verify_corpus.py` copies the
generators into a disposable scratch tree, reruns the builder, and requires all
six authored fixtures byte-identical before writing its transcript.

## 3. Reference implementations used

1. **Archived TAP-02 `reference.py` (MIT)** — encoding, section 3
   well-formedness and section 4 beat semantics; used as the specification
   source, not imported at runtime.
2. **M0 audit `independent_eval.py`** — independently structured TAP-02
   evaluator; used as a design cross-check.
3. **`m3_core.py` (this corpus)** — self-contained reimplementation used for
   every generated result. It provides two evaluators (`eval_recursive`,
   `eval_flat` via REF inlining) plus a Tseitin miter and DPLL solver.
4. **Trusted data:** the archived onchain evaluation vectors for XOR#1
   (`0,1,1,0`) and NAND#2 (`1,1,1,0`) in
   `docs/evidence/raw/M0/xlayer_circuits.json` were reproduced exactly by the
   independent evaluator (see §6). No Codex uncommitted M3 code was used as an
   expected-result oracle.

## 4. Expected outcomes

### Task A — 10 golden compositions

| ID | Scenario | Key expected property | Result class |
|---|---|---|---|
| A01 | Real XOR + NAND combination | `XOR(NAND(a,b),1)=a AND b`; 2 REFs, 7 expanded NAND | valid |
| A02 | Half-adder composition | exactly **81 bytes**, 2 REF + 1 NAND glue, outputs `(carry,sum)`, 4/4 truth table | valid |
| A03 | Commutative-input rewiring | reversed both REFs → EQUIVALENT to A02 over 4 inputs | equivalent |
| A04 | Non-equivalent output permutation | outputs `(sum,NAND)` → DIFFERENT from A02 | different |
| A05 | Duplicated-input fan-out | 8-input parity vs fault at 3rd XOR; both 28 NAND, structurally valid, DIFFERENT over 256 inputs | different |
| A06 | Multiple REF levels | top → synthetic wrapper → real XOR#1 (depth 2); `(xor,NAND)` | valid |
| A07 | Invalid external pin mapping | REF input signal 4 at first_out 4 → `signal … not available` | reject |
| A08 | Unsupported cycles | two-node A→B→A and self-cycle → `REF cycle` | reject |
| A09 | Wrong output-width mapping | REF `n_out=2` on 1-output target → arity mismatch; second variant → too few signals | reject |
| A10 | Dependency substitution | XOR identity → NAND netlist: DIFFERENT witness `[0,0]`; equivalent-but-different XOR bytes: same behavior, `DEPENDENCY_CHANGED`/STALE | integrity |

Truth tables are stored for every case with `n_in ≤ 8`; A05 stores both full
256-row tables. Source identities, widths, netlist properties and reproduction
recipes are per-case fields.

### Task B — 17 SAT cases

| ID | Case | Expected | Exactness |
|---|---|---|---|
| B01 | EQUIVALENT (symmetric rewiring) | EQUIVALENT | exhaustive + UNSAT |
| B02 | DIFFERENT (glue wired to input) | DIFFERENT | exhaustive + replayed witness |
| B03 | UNKNOWN (missing oracle) | UNKNOWN | resolution failure |
| B04 | Self-equivalence | EQUIVALENT | self-miter UNSAT |
| B05 | Equivalent symmetric gates | EQUIVALENT | exhaustive + UNSAT |
| B06 | Non-equivalent behavior (parity fan-out) | DIFFERENT | SAT + 256-input cross-check |
| B07 | Output permutation | DIFFERENT | exhaustive + witness |
| B08 | Multiple output differences | DIFFERENT | both output positions differ |
| B09 | Constant outputs | DIFFERENT | exhaustive + witness |
| B10 | Zero-input circuits | DIFFERENT | empty witness vector |
| B11 | Zero-output boundary | UNKNOWN | `nOut=0` rejected |
| B12 | Wrong input width | INVALID_INPUT | compatibility check |
| B13 | Wrong output width | INVALID_INPUT | compatibility check |
| B14 | Unbound REF input | INVALID_INPUT | forward-reference rejection |
| B15 | Faulty REF expansion | DIFFERENT | witness replayed by both evaluators |
| B16 | Changed circuit reference | DIFFERENT | exhaustive + witness |
| B17 | Solver timeout | UNKNOWN | forced decision budget (harness only) |

**No case is labelled EQUIVALENT from sampling alone.** EQUIVALENT conclusions
are exact over a fully enumerated domain or an UNSAT miter proof; DIFFERENT
conclusions carry a replayed witness.

### Task C — witnesses

Eight replayed witnesses, one per DIFFERENT case: B02, B06 (the 8-input case),
B07, B08, B09, B10 (empty input vector), B15 and B16. Each record stores the distinguishing input, both outputs
from **both** independent evaluators, the differing output positions, and a
greedy-minimized witness explicitly **not** claimed mathematically minimal.
Examples: B02 `[0,0]` → reference `(0,0)` vs candidate `(1,0)`; B08 `[0,0]` →
`(0,0)` vs `(1,1)` (two differing positions); B15 `[0,0]` → `(0,0)` vs `(0,1)`;
B10 witness `[]` (zero-input). A04 and A10 witnesses are recorded separately.

### Task D — proof-integrity attacks

12 specifications: empty self-declared width map, forged EQUIVALENT report,
replaced reference identity, replaced candidate identity, altered netlist hash,
changed implementation hash, stale dependency closure, swapped chain ID
(8453), false CURRENT freshness, non-differing SAT witness, UNKNOWN relabelled
EQUIVALENT after timeout, and proof reused for a different project. Each has a
crafted report based on `docs/schema/examples/comparison-report.json`, the
expected safe behavior and expected code. All are marked
`SPEC_ONLY_NOT_EXECUTED_AGAINST_PRODUCTION` because no M3 consumer exists yet.

### Task E — benchmark corpus

| Target gates | Actual gates | nIn | REF uses | CNF clauses | CNF vars | Netlist bytes |
|---:|---:|---:|---:|---:|---:|---:|
| 50 | 48 | 13 | 12 | 293 | 112 | 444 |
| 100 | 100 | 26 | 25 | 605 | 229 | 925 |
| 250 | 248 | 63 | 62 | 1,493 | 562 | 2,294 |
| 500 | 500 | 126 | 125 | 3,005 | 1,129 | 4,625 |
| 1,000 | 1,000 | 251 | 250 | 6,005 | 2,254 | 9,250 |
| 2,500 | 2,500 | 626 | 625 | 15,005 | 5,629 | 23,125 |
| 5,000 | 5,000 | 1,251 | 1,250 | 30,005 | 11,254 | 46,250 |

Each size has `self`, `equivalent` (symmetric port reversal) and `different`
(duplicated-input fan-out) variants. CNF counts match the historical M0.5 audit
table exactly — an independent structural cross-check, not a replay of the old
solver timings. Generation is a shallow depth-1 REF fan-out with a fixed seed;
all netlist bytes and SHA-256 hashes are in `benchmark-corpus.json`.

## 5. Executed checks

From `docs/evidence/m3-verification/verification-transcript.json`:

| Check | Outcome |
|---|---|
| Hash/size register | all match |
| Byte-identical regeneration in scratch (6 authored files) | exact, return code 0 |
| Trusted onchain vectors for XOR#1 and NAND#2 | 2/2 match |
| Negative rejection reasons (A07/A08/A09) | 3/3 rejected |
| SAT verdict agreement | 17/17 |
| Witness replay by both evaluators | 8/8 verified |
| Benchmark CNF counts recomputed | 7/7 match |

Fixture-generation observations in `benchmark-measurements.json`: exhaustive
verdicts were executed at 48 gates (`nIn=13`); for all larger sizes verdicts were
not exhaustively executed and `different` variants carry a targeted single-bit
witness replayed by both evaluators. A 200-decision capped stdlib DPLL run was
recorded verbatim for every size/mode; `UNKNOWN` on hard UNSAT instances is the
expected honest outcome of that cap.

## 6. Cases not yet executable

- **Task D (12 cases):** no M3 proof consumer is implemented; these remain
  specifications with expected safe behavior, not executed accept/reject tests.
- **Large-size EQUIVALENT proofs (100–5,000 gates):** the independent stdlib
  DPLL cannot complete UNSAT proofs on XOR chains within the task budget. Only
  structural CNF counts, sampled evaluation and targeted existence witnesses
  were executed. No EQUIVALENT verdict is claimed from sampling at those sizes.
- **Production solver behavior, WASM/native parity, 5 s / 64 MiB enforcement,
  worker isolation:** outside this task; no such result is claimed.
- **Live X Layer state, fresh fee, publication:** out of scope and prohibited.

## 7. Provenance and custody limitations

- Real circuits are **archived copies** from `docs/evidence/raw/M0/`
  (chainId 196, block 76020961). This is copied-byte integrity, not a fresh
  chain observation; original `C:\research\...` experiment directories remain
  absent.
- All composed circuits, mutations, benchmarks and attack reports are
  **SYNTHETIC**. **No synthetic circuit was deployed on X Layer** and no live
  RPC was contacted.
- The independent core was written from the TAP-02 specification text and
  checked against the archived onchain vectors; it is not Codex's uncommitted
  M3 implementation.
- `main` lag and PR #2's open state are recorded in §0; this branch does not
  resolve repository integration.

## 8. Security-relevant cases

A07–A09 (malformed pin/REF mappings and cycles), A10 (dependency substitution),
B03/B11/B12/B13/B14/B17 (UNKNOWN and invalid-input paths), all 12 Task D
attacks (forged/relabelled/transplanted proof reports), and the B15 faulty-REF-
expansion witness. The corpus enforces that a timeout or resource cap maps to
UNKNOWN, that a DIFFERENT witness must replay under two evaluators, and that
self-declared report fields cannot stand in for bound artifact hashes.

## 9. Recommendations for Codex integration

1. Wire `sat-corpus.json` into a data-driven M3 test; require all 17 expected
   verdicts and reject any EQUIVALENT produced from a timeout or a witness that
   fails replay (`D10`, `D11`).
2. Bind every comparison to actual reference/candidate manifest hashes and
   real `nIn`/`nOut`/pin maps; reject empty maps and swapped chain IDs
   (`D01`, `D03`–`D08`, `D12`).
3. Treat A10-equivalent substitutions as behaviorally equal but integrity-STALE;
   never badge them CURRENT.
4. Use the benchmark corpus for **structural** CNF-size and witness-existence
   regressions only. Do not publish these generation-time numbers as production
   solver performance; measure the actual deployment separately.
5. Implement the 12 Task D checks in the M3 proof consumer, then convert them
   from specifications to executable acceptance cases.
6. Integrate only after PR #2 is merged and Codex re-runs the combined tree
   checks; this branch must not be merged directly to `main`.

## 10. Machine-readable manifest

`docs/evidence/m3-verification/manifest.json` records branch, base commit,
counts, seed, core version, authored-file hashes, provenance and execution
summary. `fixtures/m3-verification/MANIFEST.json` is the full byte register;
`verification-transcript.json` records every executed check.

**End of M3-B deliverables. No merge into `main`. No onchain publication.**
