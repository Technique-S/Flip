# P7-V2-B0 implementation handoff

Prepared 2026-11-27 (Africa/Lagos). **B0 only; keep draft PR #15 open and unmerged for independent OpenCode review. SEC-01 remains OPEN/HIGH.**

## Exact source and scope

- Accepted main / implementation base: **`2fa7281ba01557f484cef2878e484b6e16f3ffd2`**. Fetch confirmed main still matches; no rebase or reconciliation over new production changes was needed.
- Approved planning: `3ab3d4fdbf8748fbc88c2a0d091022b195a76ab6`; architecture evidence: `b65140670f1207501d1db165c8bce353bdbbeb36`. Original branch `codex/flip-visual-v2-b-architecture` is unchanged. [Approved contract](https://github.com/Technique-S/Flip/blob/3ab3d4fdbf8748fbc88c2a0d091022b195a76ab6/docs/ux/P7_V2_B_WIRING_CONTRACT.md).
- **Implementation and regression head: `35d997aa161fa7ce5fa1e156453bb69f33ef80c1`.** Initial runtime foundation: `7f67a53d1eca3f75be6d225d8570db7fafa14952`; sample-load synchronization: `b4ff854c1b4b5e2164f8dee1bebd5575cf98e227`; original guard evaluation order restored: `35550556d29081a506ddff2e5d9899dd08e21889`; shared-reference isolation at the final implementation head.
- Implementation branch `codex/flip-visual-v2-b0` starts from accepted main, rather than copying the unmerged architecture branch into the PR. The final evidence commit introducing this handoff adds documentation only after the implementation SHA; its exact SHA is reported on PR #15 and in the delivery response.

Only production changes: `apps/web/src/visual/commands.ts` and new `apps/web/src/visual/wiring.ts`. One new test file: `apps/web/tests/visual-wiring.spec.ts` (17 cases). Existing tests, API/CLI/Python production, schemas, fixtures, architecture, dependencies/locks, UI controls/CSS, release/trust/checker, CI and repository rules remain unchanged. Protected-path diff and exact source blob hashes are recorded in [provenance](b0-evidence/provenance.json).

## Delivered behavior and findings

| Item | Implementation / disposition |
|---|---|
| F1 — MEDIUM | Pure capacity metrics use the exact existing P×W formula and source lookup/nullish fallback. Original 65,000/255/255/1 MiB limits, separate display/history caps and table/count-before-serialization denial order retained. Error messages report actual measured values and distinguish UI from native/solver limits. **Implemented and regression-tested; independent closure pending OpenCode review.** |
| F2 — LOW | Exact own string keys and enumerable own data descriptors; no inherited required values, accessors, unknown own fields, symbol extras, sparse tuples or unsafe pin values. Explicit clean records preserve object-literal versus own `__proto__` semantics and valid canonical names. **Implemented and regression-tested; independent closure pending OpenCode review.** |
| ReplaceBinding | Pure one-slot proposal for existing NAND input, stateless REF input or final-output slot. Enforces direction/range/order; preserves fan-out and every unrelated request field. Returns the exact input object on a no-op. Full request clone plus detached target path preserves aliased reference designs and input/output arrays. |
| Native authority | An already native-accepted base is a precondition; changed full proposal must pass the real existing compose endpoint before any future commit. Local display metadata does not authenticate bytes/closure/environment. No second circuit engine. |
| Integration seam | **Specified, not enabled.** Captures session/revision/full UI fingerprint/previous binding; future native response/base/generation checks precede one authorized atomic commit. No B0 UI/session/commit adapter or active wiring editor. |

[Command and transaction contract](B0_COMMAND_AND_TRANSACTION_CONTRACT.md) · [B0 mapping to the approved 29-case acceptance architecture](B0_ACCEPTANCE_MAP.md).

The latest authorization requires successful-commit-only wiring proof invalidation; the seam explicitly records that refinement from the older Review-time proposal. Existing V2-A NAND/Advanced proof behavior is unchanged. No-op identity must be checked before any POST/history/revision/dirty/proof operation. No new current-proof claim is made by compose.

## Actual verification

| Run | Observed outcome |
|---|---|
| Clean accepted-main baseline | 72 browser cases PASS before production edits. |
| Current implementation complete browser retry | **89/89 PASS**, zero skipped/flaky/unexpected, 222.403s report duration; includes unchanged 72 and new 17, real native compose/compare, alias and serialization-order regressions. |
| Current implementation complete showcase retry | **28/28 PASS**, 1.1m reporter duration; limits/assertions unchanged. |
| Initial full local Python | **691 passed / 11 failed in 2051.05s**. Retained as a failed full run. |
| Separate failed-Python-case retry | **11/11 PASS in 180.28s** at the current implementation head. This is not relabeled as a clean single 702-test local run. |
| Initial local workflow | 28/33 commands PASS; browser, showcase, pytest and derived M3/M4 acceptance reports FAIL. All nine schema exports, three canonical parity checks, release bootstrap/integrity, fixture verification, Ruff, agent/authorization/adapter/portability, clean custody, smoke and benchmark commands passed. |
| Derived local acceptance reports | Original M3/M4 reports remain FAIL from the original full Python result. M4 reprocessing with the passing browser report still reports FAIL because that Python input is unchanged. No manufactured merged JUnit or success relabeling. |
| Implementation-head hosted push [45913094979](https://github.com/Technique-S/Flip/actions/runs/45913094979) and PR [45913100097](https://github.com/Technique-S/Flip/actions/runs/45913100097) | **All four Windows/Ubuntu jobs SUCCESS** at `35d997aa161fa7ce5fa1e156453bb69f33ef80c1`; every workflow step succeeded. Push logs directly record 702 Python / 89 browser / 28 showcase per OS. Exact final documentation-head CI will be observed and linked on PR #15 after pushing; older green runs are not substituted. |

Final native archived capture is byte-identical to the accepted V1/V2-A capture: SHA-256 **`b4c5aa157ef966f7022c880bb637c7ea0d121c4710f5610c2614c0759158b933`**. Project `0xff70814e174ae2dc841eef4a9e6367bb5318bccd069307c3afdce1adaa329959`, netlist `0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`, manifest `0x10a2616767a30352158c32aae8cdb85b44cd7f5f04b168c462f41a8789b6f299` remain unchanged. Fresh arbitrary runtime receipts with timing/outcome/engine context are not claimed universally byte-identical.

Native evidence includes exact one-slot request equality, unchanged reference/maps/imports/dependencies, real multi-output REF fan-out, native rejection of bad identities/state/bytes/closure, and unchanged UI capacity with native output-copy overflow (8 accepted gates → 12 required, gateCap 8 rejection). Shared design/input-output aliases are accepted as base values by real compose and remain isolated after replacement. Canonical JSON, hashing and registration semantics are unchanged.

## Preserved failures and corrections

1. Initial development build failed TypeScript narrowing inside a target lookup callback; retaining a narrowed local target fixed it before acceptance. The output is preserved.
2. Initial targeted run: **16 PASS / 1 FAIL**. Its synthetic display profile retained removed component names in outputs; the test fixture was corrected to valid external bindings, without changing a production guard or assertion. Corrected targeted run: 17 PASS. Later hostile cases are included in the complete passing 89-case run.
3. Initial source-head hosted matrices: Ubuntu **88 PASS / 1 FAIL** in the new read-only test; Windows siblings cancelled by existing fail-fast. The test captured null session storage before Open sample completed. It now waits for the actual loaded request, preserving exact equality/network assertions; three repeats passed. No sleep, retry policy or timeout increase. Raw failure and source-head job metadata retained.
4. Initial complete local browser: **88 PASS / 1 FAIL**, unchanged portable-agent journey returned BUDGET_EXHAUSTED instead of COMPLETE. Initial showcase: **27 PASS / 1 FAIL**, unchanged seven-page axe test exceeded its 30s limit. Both complete suite retries passed under unchanged bounds after the earlier workload finished.
5. Eleven local Python failures include interrupted 5,000-gate results, a 120s corpus-regeneration timeout, native/CLI outcomes returning UNKNOWN, and agent budget/cancellation/receipt parity assertions. Exact per-test messages are retained; all eleven passed separately later. Timing/resource sensitivity is observed, not a proved root-cause diagnosis. No native limit, fixture, expected verdict, test or guard was changed.
6. Code review found guard serialization order and structural-sharing issues in intermediate B0 code. Git-blob-pinned before/after probes reproduce and verify both corrections, with additive regressions in the passing current suite. An initial unpinned scratch order probe raced with edits and is excluded from acceptance; pinned probes are authoritative.

The initial local workflow spanned source/test refinements (per-command HEADs retained); Python production was byte-identical to accepted main throughout. It is not described as one clean immutable-head local run. Final stable-head hosted matrices supply the complete reproducible full-suite result. Original failed target text/JSON remains, but its transient trace directory was reused before a separate trace copy was made; the later full browser failure trace was separately preserved. No binary traces/screenshots or encoded-image workaround is committed.

## Evidence custody, remaining work and stop

[b0-evidence](b0-evidence/) contains original command reports/logs, current passing retries, native captures, Git-pinned regressions, CI metadata/counts, exact source provenance and raw-capture inventory. Text copies normalize CRLF to LF only; raw originals and their SHA-256 hashes/local paths are retained. XML, large raw CI logs and binary traces stay in ignored scratch, with hashes in the inventory; ordinary tracked files stay below the existing size cap. The evidence manifest hashes exact LF Git bytes and is verified after commit. No accepted historical artifact is edited.

B1 requires separate authorization and independent B0 acceptance: a real base-bound transaction adapter/response validation, pending lock/generation cancellation, successful-commit proof/history transition, retry/recovery, native keyboard/tap review flow and only later explicit editing/drag interaction. These are NOT IMPLEMENTED / NOT TESTED as new production wiring behavior. Physical touch, screen-reader speech and gesture-performance budgets are likewise not claimed.

Independent OpenCode review should assess the full final PR head, own-property hostile corpus, alias isolation, unchanged budgets/canonical identities and all retained failure/retry evidence. F1/F2 independent disposition remains pending; **SEC-01 remains OPEN/HIGH** under the approved solo-maintainer policy. No new API route/schema, REF/LATCH authoring, component reorder, active editor, Visual Wiring Canary, V2-C, wallet/signing/transactions, public solver hosting, deployment or own merge.
