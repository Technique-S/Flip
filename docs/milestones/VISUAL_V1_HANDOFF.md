# P7-V1 read-only visual composer: acceptance handoff

**Independent OpenCode review: PENDING. Keep PR unmerged; no auto-merge.** V1 only, not P7/P8 completion. No editing, visual Canary, stateful authoring or visual project export.

## Exact revisions

- Accepted main: `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`.
- Approved architecture / branch parent: `39322e49f9fb1aa83a726fe3bbe81921c7e0f21e`; compatible ancestor of implementation; its protected runtime paths equal accepted main.
- Initial implementation: `2d497c93c6365eda5bcdad99f5c439db237139e4`.
- Final visual production/test implementation: **`5cd90f99c359ed9a28066295a8e848b79f16744f`**.
- Authorized narrow release-guard integration: `8fa211118689690df81964fb8c3c6e7389e14a0a`.
- This handoff/results follow as documentation only. Exact final PR head and final-head CI disposition are recorded on the open V1 PR. Do not substitute an earlier successful run for final-head CI.

The owner subsequently authorized the narrow historical release-guard fix described below.

The branch retains the approved architecture and prior audit as ancestors; those documentation commits are not yet on main. Their original files remain unchanged. Against architecture, production delta is only the paths listed below. Against main, inherited planning docs also appear; no inherited report is rewritten.

## Behavior and adapter

In Composition, **Advanced** remains the default and retains its original wiring controls. **Visual** projects candidate NAND/stateless REF, external input bank and final output bank. It offers pan/zoom/fit, component/pin inspector, exact numeric connection table and accessible read-only labels. No mutation callback is passed to the renderer. Nodes cannot be dragged or connected; edges cannot be reconnected/deleted; Delete/Backspace do not alter the graph. View state is ephemeral and absent from project/evidence/Portable 1.1.

`projectExecution(value: unknown): Projection` in `src/visual/projection.ts` is pure/deterministic, adapter version `flip-visual-adapter-1.0.0`. It projects the existing `M3_EXECUTION.project.candidate` in original component order and reads source interface/identity metadata bound to imports. No binary decode, evaluator, REF resolver, compiler, SAT or hashing implementation is added. Python remains the execution authority; these display guards do not replace trusted validation.

Component IDs: `candidate/component/<instanceId>`. Banks: `candidate/external`, `candidate/outputs`. Handles: `in:<decimal index>`, `out:<decimal index>`, all one bit. Edge IDs bind destination instance/input index; reconnect is not implemented. Every edge/input locator references the actual candidate pin field. Derived output locators reference existing `candidate.nIn`, component `.kind` or source `.nOut`, with a `#out:<index>` fragment rather than inventing a component `.outputs` field. Output mapping/order, source identities, decimal circuit IDs, manifests and request bytes are never normalized or rewritten. REF metadata is detached in the projection to prevent aliasing the request.

Unknown/malformed/unsupported/stateful/forward/duplicate/budgeted input yields an explicit Visual-unavailable message, zero partial graph and access to Advanced/original data. Fixed projection bounds: ≤500 components, ≤1,000 connections, ≤4,096 visible pins, ≤512 external/final pins and canonical REF count bounds. These are protective display guards, not new canonical limits or measured stress-performance acceptance. No truncation/export loss. Decoded REF internals and LATCH structure are explicitly deferred because current accepted recipe transport lacks those display records.

## Renderer compatibility and licensing

Exact dependency: **`@xyflow/react@13.0.2`, MIT**, installed with exact root version and integrity-pinned lock. Declared peers include React/types ≥18 and Node ≥20. Actual production build passed with React/react-dom **19.3.1**, TypeScript **7.0.2**, esbuild **0.28.2**, Node **24.18.0**. The visual subtree/provider is wrapped in StrictMode; tests assert correct node/edge counts, no page errors or extra requests across repeated mode mounts. Accessible pin inspection works with keyboard; no duplicate initialization effect or solver invocation occurs.

`src/visual/notices.ts` retains full installed runtime-tree notices (including type-only peer entries), shown under **Renderer and dependency licenses** in the real UI. The 26 entries use MIT, ISC or BSD-3-Clause texts as shipped. `react-compiler-runtime@1.0.0` omits LICENSE from its npm package but its code references React's MIT root; its published npm gitHead is `5c15c1cd3442f28044217703b5625f98c40042ee`. The exact [upstream root LICENSE](https://raw.githubusercontent.com/facebook/react/5c15c1cd3442f28044217703b5625f98c40042ee/LICENSE) supplies the retained notice. No Pro example hooks/source, competitor assets, optional noncommercial Rete plugin, or new Flip source-license decision.

Production JS is about 568 KB / 177 KB gzip versus accepted runtime's 279 KB / 85 KB gzip in the local build (including notices). This is a build-size observation, not a large-graph benchmark. npm installation reported zero vulnerabilities; pending esbuild install-script warning did not require any config/policy override and production builds succeeded. No lock/dependency updates outside apps/web.

## Acceptance evidence

Actual local observations retained under [results](../ux/visual-v1/results/). Full local browser run: **42 passed** (27 inherited + 15 V1), zero skips/flakes/retries, 151.1 seconds. This run precedes the final locator correction; the final implementation then passed the complete **15-case focused V1 suite**, zero failures/skips/retries, 15.9 seconds. Final-head hosted matrices must run all 42 on both OSes before review acceptance. Local full Python was not rerun: four relevant Python tests passed, and hosted CI runs the full accepted 702-case suite. No unexecuted check is labeled PASS.

| Authorized acceptance | Observed test coverage |
|---|---|
| Genuine accepted sample, NAND/REF/banks | Browser opens actual historical half-adder through production API; asserts all nodes and eight rendered edges. |
| Exact source/destination, pins, order, locators | Pure projection compares every edge to ordered canonical inputs/outputs; each displayed port locator resolves an existing field; browser checks each SVG edge and mapping row. |
| Zero inputs, multioutput REF, large decimal IDs | Synthetic **projection-only** test with zero inputs, two output pins and ID `9007199254740993`; not claimed as chain/solver evidence. Genuine sample is separate. |
| Mode parity, hashes/identities | Browser asserts exact stored execution string before/after, original Advanced mapping/build result retained, and independent trusted compose responses exactly equal. Actual [parity observation](../ux/visual-v1/results/canonical-parity.json) includes request/imports, project/manifest hashes and netlist before/after. |
| No create/reconnect/delete | Nonconnectable handles with pointer events disabled, no draggable nodes, disabled reconnection, null delete key, no edit handlers; actual keyboard deletion on node and edge leaves counts/request unchanged. |
| Keyboard, labels, pan/zoom/fit | Node focus, inspector selects, Enter on pin button, actual viewport transform changes and zoom/fit; axe zero violations, 320/390px overflow checks, reduced-motion setting. |
| No invented verifier success / no new network | Rendering creates no EQUIVALENT heading and makes zero additional requests during mode/selection cycles; compiler calls are explicit test setup/parity operations. |
| Malformed/unsupported input | Ten adapter negative cases plus actual UI route-injected unsupported-kind failure with preserved Advanced access. No production fixture rewrite. |

Additional local PASS: frontend lint/build; four Python sample/determinism/stateful rejection/portable roundtrip/mapped diagnosis regressions; all nine frozen schema exporters `--check`; three Node canonical parity checks; Ruff lint/format (88 files). Protected-path Git equality against accepted main passed for core/API/CLI, fixtures, schemas, CI and Python locks. The only shared-script exception is the separately authorized R3 checker below. Final committed-tree custody/credentials and Windows/Ubuntu CI outcomes are recorded on the PR after execution.

Earlier development failures are retained as history: initial exact sample-button selector omitted the existing arrow; a script encoding mistake corrupted one test regex; pin click propagation cleared selected pin; axe identified heading-order and label-content mismatch; added read-only ARIA description made a broad summary selector ambiguous. Those were corrected with the same substantive assertions and no timeout/skip/retry changes. Final self-review corrected derived output locators to real canonical fields and added locator resolution assertions. These were implementation/test defects, not accepted-core failures.

## Real screenshots

Desktop and 390/320px screenshots were captured by actual Chromium against the production build, inspected visually, and retained locally under `.test-tmp/visual-v1-evidence/`. [Manifest](../ux/visual-v1/results/screenshots.json) records absolute paths, bytes and hashes. Screenshots are intentionally ignored binaries: existing custody permits only registered historical image blobs. No guard/allowlist exception or encoded-image workaround is introduced. Reviewers can reproduce all screenshots with the committed test; local screenshots are included in the chat handoff. They are not proof or new permanent golden fixtures.

## Files and reproduction

Production/tests changed relative to architecture: `apps/web/package.json`, `package-lock.json`, `src/Composer.tsx`; new `src/visual/projection.ts`, `VisualComposer.tsx`, `visual.css`, `notices.ts`; new `tests/visual-readonly.spec.ts`. Documentation: this handoff and `docs/ux/visual-v1/results/**`. The authorized scope extension additionally changes `scripts/check_m45_release_package.mjs` and adds `apps/showcase/tests/release-guard.spec.mjs`. No App/main/config/CI/backend/schema/accepted-evidence change.

```powershell
uv sync --locked
npm ci --prefix apps/web
npm run lint --prefix apps/web
npm run build --prefix apps/web
npm exec --prefix apps/web -- playwright install chromium
npm test --prefix apps/web
uv run --frozen pytest -q
uv run --frozen python scripts/check_m1_repository.py --require-clean
```

Existing CI runs production browser plus showcase tests, full Python, all schema/canonical/custody/independent acceptance/smoke/benchmark gates on Windows and Ubuntu. It is unchanged. On Windows this task used an isolated `.bootstrap` uv 0.9.11 and new locked `.venv`; not a first-time human install trial.

## Authorized historical release-guard fix

Initial exact-head push/PR CI runs **45181066145 / 45181184502** failed on Ubuntu with `Release source drift: apps/web/package.json`; Windows was cancelled by matrix fail-fast. The required React Flow dependency conflicted with R3's historical source pins. The original failure is retained in results/initial-ci-failure.txt and those runs, not relabeled as success. The owner explicitly authorized the narrow guard/test scope extension after reviewing the proposal on PR #12.

The R3 inventory remains byte-identical. Only its frontend package/package-lock and checker-source provenance is read at immutable accepted R3 commit `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`. The checker requires that commit in ancestry, pins the entire sourceHashes map to the original Git inventory, validates every original SHA/byte count, and logs the three historical paths explicitly. All other source paths and actual generated static files continue to use current-checkout checks. No configurable bypass or generic fallback; historical dependency metadata is not validation of current V1 dependencies.

Seven new black-box cases exercise the actual checker in isolated temporary copies: valid V1 dependency change, tampered current source, changed static output, altered inventory, injected fallback path, missing history and wrong history. The entire showcase suite passed **26/26** (19 inherited + seven new), zero skips/retries, 35.8 s. The first scratch harness omitted linked documentation targets and failed its positive/asserted-phase cases; it was corrected to copy the exact existing link targets, retaining the original checker assertions. Missing/wrong-history cases explicitly assert Git failure rather than crediting an unrelated failure. No historical fixture/corpus/inventory or existing test was edited. Existing CI discovers the new showcase test automatically; CI configuration is unchanged. Final-head full platform runs remain the review gate and their results are recorded on the PR.

## Independent review and V2 boundary

OpenCode should review the **exact final PR head**, reproduce renderer license provenance, every locator/connection and byte parity, malformed failure, keyboard/pin selection and denied editing/network tests. Inspect hidden Advanced state preservation and StrictMode remounts. Independently rerun core/evidence guards; report failures unchanged. Do not merge or rewrite original fixtures to improve results.

Known unsupported: node/wire creation/mutation, undo/redo, decoded REF/LATCH inspection, latch authoring/trace simulation, visual counterexample overlays, persistent positions/visual portable envelope, P8 walkthrough/glossary/progress/recovery lessons. V2 needs bounded validated decoded structure transport if real internals are required; shared canonical validation remains authoritative. Real screen-reader speech, touch-device interaction and large-graph performance are not accepted by this automated V1 evidence. P3/P4 release/transaction gaps remain unchanged. Stop with PR open pending independent approval; no wallet, transaction, deployment or public solver.
