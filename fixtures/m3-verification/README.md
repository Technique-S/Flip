# Flip M3 independent verification corpus (M3-B)

**Owner:** OpenCode / HY4 Flash (supporting verification engineer).
**Branch:** `opencode/flip-m3-verification-corpus`.
**Base:** `b71e48e4ad29b352a166230b8644a26f11c5fba8` (head of PR #2).
**Scope:** fixtures + evidence only. No production package, schema, lockfile, CI
config, raw evidence or Codex branch was modified. No live RPC, no wallet, no
onchain publication.

## Contents

| Path | Purpose |
|---|---|
| `generators/m3_core.py` | Self-contained TAP-02 encoder/decoder/loader, two independent evaluators, Tseitin miter + DPLL. Stdlib only. |
| `generators/build_corpus.py` | Deterministic corpus builder (Tasks A–E). |
| `generators/verify_corpus.py` | Independent hash/regeneration/behavior verifier; writes `docs/evidence/m3-verification/verification-transcript.json`. |
| `circuits/golden-compositions.json` | Task A: 10 golden composition cases. |
| `sat/sat-corpus.json` | Task B: 17 SAT correctness cases. |
| `witnesses/witness-corpus.json` | Task C: replayed distinguishing witnesses. |
| `proof-attacks/attack-corpus.json` | Task D: 12 hostile report specifications. |
| `benchmarks/benchmark-corpus.json` | Task E: 7 sizes × 3 modes, seeds and hashes. |
| `results/*.json` | Generation-time observations (timing; excluded from byte-determinism). |
| `MANIFEST.json`, `BUILD_INFO.json` | Hash register and build provenance. |

## Regeneration

```powershell
# from the worktree root, Python 3.14.6, stdlib only
python fixtures/m3-verification/generators/build_corpus.py
python fixtures/m3-verification/generators/verify_corpus.py
```

`verify_corpus.py` copies the generators into a disposable scratch tree, reruns
the builder there, and requires byte-identical authored fixtures. It also
replays the onchain-vector cross-check, negative-fixture rejections, SAT
verdicts, both evaluators on every witness, and recomputed benchmark CNF sizes.

## Trust boundary

- Real source circuits are archived X Layer mainnet reads (chainId 196, block
  76020961) for `0x839BDD6f…#1` (XOR, 4 NAND) and `…#2` (NAND, 3 NAND).
- **Every composed circuit, mutation, benchmark chain and attack report is
  synthetic.** None was deployed on X Layer and no live RPC was contacted.
- `m3_core.py` is an independent reimplementation from the TAP-02 spec, cross-
  checked against the archived onchain evaluation vectors for both real
  circuits and against a second, differently structured evaluator.
- DPLL timings are host observations, not production solver performance.
  `UNKNOWN` from a capped DPLL run is the expected honest outcome, not a verdict.
- Task D cases are report specifications only: no M3 proof consumer exists yet.
