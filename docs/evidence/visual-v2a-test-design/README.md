# P7-V2-A independent test design package

Baseline: `fc9c0c1bcb2557169dd89af0c3b2c5a7628c9adf` (accepted `main`, post V1 merge). V1 reviewed head: `53a7f1cdd729188c7bfd593d37049836b6ed6a12`.

**Status: PROSPECTIVE ACCEPTANCE DESIGN.** V2-A controlled visual NAND editing does not exist at this baseline. None of these cases is a passing production test and none should be counted as implementation evidence. This package contains no production code, no implementation of editing and no change to Codex-owned files.

## Ownership

- Evidence: `docs/evidence/visual-v2a-test-design/**`
- Fixtures: `fixtures/visual-v2a-test-design/**` (new namespace; no accepted fixture was edited)
- Branch: `opencode/flip-visual-v2a-test-design`
- No merge; no V2-A implementation; no wallet, transaction, hosting or deployment work.

## Contents

| File | Purpose |
|---|---|
| `COVERAGE_MATRIX.md` | All 15 focus areas mapped to 56 case IDs with expected outcomes and freshness rules |
| `SEMANTIC_BLOCKERS.md` | Ten unresolved V2-A semantic decisions that must be settled before cases can become executable |
| `ACCEPTANCE_CRITERIA.md` | Pass/fail gates the implementation must satisfy for each case family |
| `CANONICAL_CONTRACT.md` | Canonical rules extracted from accepted source with exact file:line references |
| `baseline-vectors.json` | Genuine accepted-main vectors and hashes reused as fixture bases |
| `cases-index.json` | Machine-readable index (generated): case IDs, 15 focus areas, blocker catalogue |
| `../../fixtures/visual-v2a-test-design/MANIFEST.json` | SHA-256/byte manifest for all generated case files |
| `../../fixtures/visual-v2a-test-design/cases/V2A-*.json` | 56 bounded cases: input patch, edit sequence, expected canonical state, outcome, rejection reason, evidence freshness, regression test pointer |
| `../../fixtures/visual-v2a-test-design/generators/build_cases.mjs` | Reproducible generator from the genuine half-adder sample |
| `../../fixtures/visual-v2a-test-design/generators/verify_cases.mjs` | Bounded consistency verifier (uniqueness, required fields, 15-area coverage, blocker usage) |

## Reproduction

```powershell
node fixtures/visual-v2a-test-design/generators/build_cases.mjs
node fixtures/visual-v2a-test-design/generators/verify_cases.mjs
```

Verified locally at generation time: `cases=56 focusAreas=15 blockers=10`, verifier `errors=[]`; 19 ACCEPT cases and 37 REJECT cases. The generator reads only `docs/schema/m3/examples/half-adder.request.json` and `docs/evidence/visual-v1-postmerge/canonical-parity.json`; it never writes outside the two owned namespaces.

## How to read a case

Each case file uses this contract:

- `input.base` + `input.patch` — derive the exact request bytes from the genuine sample. A patch entry is `[pathArray, value]`.
- `editSequence` — ordered prospective commands. Command names are provisional adapters because SB-1 is unresolved; the *semantic effect* is what the case pins.
- `expectedCanonicalState.mode` — `UNCHANGED` means byte-identical to the case input (after patch); `CANDIDATE` gives the exact expected `project.candidate` object. Hashes for edited candidates must be computed by the trusted compose path.
- `expectedOutcome` — `ACCEPT` or `REJECT`; `rejectionReason` names the exact enforcement boundary for rejections.
- `evidenceFreshness` — which build/proof results may be shown as current and which must be hidden or labeled historical.
- `regressionTest` — the prospective Playwright test name to be added by Codex when V2-A exists.
- `semanticBlockers` — unresolved decisions from `SEMANTIC_BLOCKERS.md`.

## Disposition rule

A case may be promoted from `PROSPECTIVE_ACCEPTANCE` to an executable regression test only after (a) the V2-A command contract is published, (b) each referenced blocker is resolved in an approved design document, and (c) the exact implementation head is independently reviewed. Until then, a failing case is expected and carries no merge implication.
