# M4.5-2D — independent debugging corpus handoff

**Agent:** OpenCode / HY4 Flash (supporting verification engineer)
**Date:** 2026-11-19
**Base:** accepted M4 main `09f2482beae84be6d919ecd6957c4153d1924cca` (`origin/main`)
**Branch:** `opencode/flip-m45-debugging-fixtures` (created from the accepted baseline; not merged)
**Commit SHA:** reported in this task's completion response; this document is part of that commit.

## Scope and custody

Wrote only under `fixtures/m45-debugging/` and `docs/evidence/m45-debugging/`.
No production package, shared schema, frontend component, CI file, dependency or Codex
branch was edited. No production diagnostic or transaction feature was implemented. No
signing, wallet, broadcast, payment, live RPC or publication occurred.

## Deliverables

| Path | Purpose |
|---|---|
| `docs/evidence/m45-debugging/DIAGNOSTIC_MODEL.md` | Task B–D attribution model, correction classes, UX contract, worked cases |
| `docs/evidence/m45-debugging/ACCEPTANCE_MATRIX.md` | Task A coverage and Task E executed/specification-only checks |
| `docs/evidence/m45-debugging/HANDOFF.md` | This summary |
| `docs/evidence/m45-debugging/verification-transcript.json` | Executed check transcript |
| `fixtures/m45-debugging/README.md` | Index and reproduction |
| `fixtures/m45-debugging/MANIFEST.json`, `BUILD_INFO.json` | Hash register and build provenance |
| `fixtures/m45-debugging/generators/*.py` | Core, deterministic builder, independent verifier |
| `fixtures/m45-debugging/cases/debugging-corpus.json` | Ten SYNTHETIC cases |
| `fixtures/m45-debugging/diagnostics/*.json` | Diagnostic rules and correction guidance |
| `fixtures/m45-debugging/ux/ux-expectations.json` | Structured output and accessibility expectations |
| `fixtures/m45-debugging/acceptance/acceptance-corpus.json` | Nine executable checks + six specification-only cases |

## Fixture counts

- **10** debugging cases (D01–D10), all labeled `SYNTHETIC`, covering the ten required categories.
- **8** correction-guidance items across exactly three allowed classifications
  (2 verified, scoped corrections; 3 candidate diagnostic actions; 3 explanation-only).
- **9** executable check rows (V01–V03, E01–E10) and **6** specification-only cases (S01–S06).
- **9** manifest-hashed authored files (3 generators, 5 JSON products, README).
- Verifier result: `PASS`, zero errors, nine check groups.

## Executed checks

Commands:

```powershell
python fixtures/m45-debugging/generators/build_corpus.py
python fixtures/m45-debugging/generators/verify_corpus.py
```

Outcome: deterministic build; byte-identical scratch regeneration of all authored JSON;
trusted XOR#1/NAND#2 vector calibration; full truth-table and witness re-derivation for
every case; cone membership checks; D10 indistinguishable-alternative re-evaluation;
prior-mapping corrections re-compared; missing-closure and cone-cap meta cases; guidance
vocabulary and no-unique-fault-claim invariants. All recorded in `verification-transcript.json`.

## Limitations

- No production Flip code was exercised; the evaluator is an independent stdlib reference,
  not the trusted production solver. Production replay/engine parity remains unverified.
- All circuits and identities are synthetic. Archived XOR#1/NAND#2 vectors were used only
  to calibrate the independent evaluator, not as deployed-fixture claims.
- No UI, CLI diagnostic command, browser assistive-technology session or human usability
  study was executed; those remain specification-only (S01–S06).
- `VERIFIED_CORRECTION` is scoped to equivalence with the declared synthetic reference;
  it is not a claim about absolute intended behavior.
- Timeouts, truncation and missing closure remain UNKNOWN; the corpus never relabels them
  to force a pass. No unique defective connection is claimed in any case.

## Recommendations for Codex

1. Bind every displayed diagnostic to a path-qualified `connectionRef`, the candidate
   `netlistSha256` and the replayed witness; keep suspect highlighting separate from the
   authoritative verdict.
2. Implement the cone tracer with the `nodeCap` stop and the seven attribution classes in
   `DIAGNOSTIC_MODEL.md` §4; never emit a unique fault claim from cone membership alone.
3. Treat D08/D10 as regression guards: EQUIVALENT designs must show zero suspects, and
   indistinguishable causes must stay `AMBIGUOUS_MULTIPLE_CAUSES`.
4. Require explicit user application of any candidate repair followed by a fresh trusted
   full comparison before calling it verified; keep that flow outside transaction authority.
5. Convert S01–S06 to executable product tests when the M4.5-2D UI/CLI exists, and run
   human keyboard/screen-reader review with an unfamiliar mutation.

## Attestation

- Only owned paths changed; no merge into `main`.
- Credential scan over all authored files found no private keys, mnemonics, API keys,
  tokens or wallet secrets.
- All hashes are SHA-256 over committed bytes; no fabricated or truncated hashes.
- No LLM was used as a proof or fault oracle (`llmOracle: NONE`).
