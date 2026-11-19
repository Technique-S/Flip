# M4.5-2D — independent circuit debugging corpus

Independent, deterministic fixtures for connection-level circuit debugging. This is
supporting verification evidence only: no production diagnostic, no transaction feature,
no LLM proof oracle and no live chain observation. All circuits and identities are
synthetic.

## Layout

| Path | Contents |
|---|---|
| `generators/debug_core.py` | Self-contained TAP-02 evaluator and path-qualified signal-cone tracer; calibrated against archived XOR#1/NAND#2 vectors |
| `generators/build_corpus.py` | Deterministic builder for all ten cases, diagnostic rules, guidance, UX expectations and acceptance corpus |
| `generators/verify_corpus.py` | Independent verifier: hashes, byte-identical scratch regeneration, truth-table/witness/cone re-derivation, and meta cases |
| `cases/debugging-corpus.json` | Ten SYNTHETIC cases with exact netlists, output maps, exhaustive tables, witnesses and cones |
| `diagnostics/diagnostic-rules.json` | Trace algorithm and attribution classes (Task B) |
| `diagnostics/correction-guidance.json` | Eight guidance items with one of three allowed classifications (Task C) |
| `ux/ux-expectations.json` | Structured-output and accessibility expectations (Task D) |
| `acceptance/acceptance-corpus.json` | Nine executable checks and six specification-only cases (Task E) |
| `MANIFEST.json` | SHA-256 + byte register for every authored file |
| `BUILD_INFO.json` | Base commit, branch, core version and counts |

The executed check transcript is written to
`docs/evidence/m45-debugging/verification-transcript.json`.

## Reproduction

```powershell
python fixtures/m45-debugging/generators/build_corpus.py
python fixtures/m45-debugging/generators/verify_corpus.py
```

No network, no third-party package and no production Flip module is used. The builder
writes LF-terminated JSON with sorted keys; regeneration is byte-identical.

## Rules

- Every case is labeled `SYNTHETIC`. Archived XOR#1/NAND#2 truth vectors are used only
  to calibrate the independent evaluator.
- A replayed witness proves a behavioral difference relative to the selected reference;
  it never proves which connection is defective.
- No case claims a unique faulty connection. Suspects are cone members only and require
  explicit user application plus a fresh trusted comparison.
- `VERIFIED_CORRECTION` is scoped to "restoring this edit restores equivalence to the
  declared synthetic reference", not to absolute intended behavior.
- No diagnostics output is transaction authority.
