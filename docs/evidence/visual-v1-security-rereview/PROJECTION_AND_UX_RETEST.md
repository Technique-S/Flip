# Projection and UX retest — corrected head `53a7f1cdd729188c7bfd593d37049836b6ed6a12`

## Method

- Bundled the corrected `apps/web/src/visual/projection.ts` with esbuild into `projection-rereview.bundle.mjs`.
- Re-ran the original 54-case independent harness with only two expectation updates (empty/XSS aliases now correctly REJECT).
- Added a 13-case boundary harness for alias syntax and budget boundaries.
- Re-ran the independent read-only browser attack against the corrected production build.
- Used the genuine `docs/schema/m3/examples/half-adder.request.json` sample; every case deep-clones it and verifies the input is byte-unchanged.

## Original 54 cases

**54/54 expected, 0 failures, 0 input mutations.** All accepted cases still accept (baseline sample, empty-component-with-external-output, zero inputs, large uint64 IDs, detached copies, derived locator resolution, copied pin mappings). All rejected cases still reject (null, forward/self/unknown references, invalid/fractional/Negative/string pin indices, unsupported kinds, stateful sources, malformed processor/circuitId, manifest mismatch, duplicate aliases, out-of-bounds budgets, XSS/unicode instance IDs).

The two cases that previously exposed PROJ-01 now reject with `invalid source alias`, confirming the guard.

## Alias boundaries (PROJ-01 RESOLVED)

| Case | Expected | Observed |
|---|---|---|
| 1-char alias `a` | ACCEPT | ACCEPT |
| 64-char alias | ACCEPT | ACCEPT |
| 65-char alias | REJECT | REJECT (`invalid source alias`) |
| `a_b-c9` (hyphen/underscore/digits) | ACCEPT | ACCEPT |
| leading digit `0abc` | REJECT | REJECT |
| dot `a.b`, space `a b`, empty, `<script>…` | REJECT | REJECT (all) |
| used REF alias `bad.alias` while source alias valid | REJECT | REJECT (`invalid REF source alias`) |

Request bytes were unchanged in every case. Display strings remain React-escaped text; no HTML injection path was introduced.

## Budget boundaries (PROJ-02 RESOLVED)

| Case | Expected | Observed |
|---|---|---|
| 499 NAND components × 2 inputs + 2 outputs = exactly 1,000 edges | ACCEPT | ACCEPT (501 nodes / 1,000 edges) |
| 500 NAND components × 2 inputs + 1 output = 1,001 edges | REJECT | REJECT (`connection budget exceeded before allocation`) |
| 17 REF components with `nOut=255` → 4,337 visible pins | REJECT | REJECT (`visible pin budget exceeded before allocation`) |

The counters are incremented before each `ports()`/`connections()` allocation, so oversized graphs fail early with a single explicit `Visual view unavailable` message. No partial graph is returned; no canonical field is truncated.

## UX-01 — Advanced navigation

`Composer.tsx` now renders, inside Visual mode, the text "Build and comparison actions remain in Advanced. Viewing this recipe runs no execution." and a "Return to Advanced actions" button that calls `setVisual(false)`. The hidden Advanced block still contains Build netlist, wiring controls, reference design, result details and "Compare circuits →".

Verified by the workbench browser suite (44/44, including the new focused test at `visual-readonly.spec.ts:339`) and by re-running the independent read-only attack (1/1 pass): no mutation, zero network requests, no page errors, stored request byte-identical after drag/connect/reconnect/delete/clipboard/12 rapid mode switches.

## V1 correctness preservation

- NAND requires 2 scalar inputs; REF requires stateless source, matching import/manifest identity and exact `nIn` inputs.
- Edge IDs remain `<target>/in/<index>` with reserved banks that cannot collide with `candidate/component/*`.
- Decimal identifiers `9007199254740993` and `18446744073709551615` retain exact string identity.
- Zero-input and multioutput REF cases pass; derived locators still resolve real fields.
- Visual ↔ Advanced parity: stored execution bytes, netlist, project/manifest hashes and trusted compose responses unchanged (original parity evidence re-read; browser test re-run).
- No semantic editing callbacks, no invented verification heading, no unauthorized requests, no change to `packages`, `fixtures`, `docs/schema` or accepted R3 evidence (Git object equality verified).

Machine-readable results: `projection-rereview-results.json`, `projection-boundary-results.json`.
