# P7-V2-B integration, risks and inherited findings

Architecture checkpoint only. Baseline `2fa7281ba01557f484cef2878e484b6e16f3ffd2`; [command contract](P7_V2_B_WIRING_CONTRACT.md), [interaction/accessibility spec](../ux/P7_V2_B_INTERACTION_SPEC.md), [acceptance matrix](../ux/P7_V2_B_ACCEPTANCE.md), [verification record](../milestones/P7_V2_B_ARCHITECTURE_CHECKPOINT.md). All stages below require a later implementation authorization. No assignment is dispatched by this plan.

## V2A-F1 — MEDIUM, OPEN

Actual code: [commands.ts:11](https://github.com/Technique-S/Flip/blob/2fa7281ba01557f484cef2878e484b6e16f3ffd2/apps/web/src/visual/commands.ts#L11). Let `O = candidate.outputs.length`, `I(c) = c.inputs.length`, and `A(c) = project.sources.find(s => s.alias === c.sourceAlias)?.nOut ?? 1`. The implementation computes:

```text
P = O + sum I(c)                 // number of destination binding slots
W = candidate.nIn + sum A(c)     // all source pin options, conservative across rows
reject when P * W > 65,000 OR nIn > 255 OR O > 255
then reject UTF8(JSON.stringify(full Execution)).byteLength > 1,048,576
```

This is a conservative **interactive pin-table option-product limit**, not a NAND count, expanded-gate budget or solver complexity guarantee. For valid NANDs, A(c)=1; for valid REF, A(c)=its source's nOut. Preserve the exact baseline lookup/fallback behavior while centralizing explanatory metrics; malformed source metadata must still fail structural validation. For the retained boundary case with 2 external inputs, 2 outputs and N NANDs: N=178 gives P=358, W=180, product=64,440; N=179 gives P=360, W=181, product=65,160 and fails. “Maximum 178 NANDs” would be inaccurate for other interfaces/REFs.

Separate display limits still apply through `projectExecution`: 500 components, 1,000 connections, 4,096 allocated visible pins; nIn/output display bounds 512 and REF scalar-interface checks, including nOut in 1..255. Display connections equal P and visible pins equal P+W for validated recipes. Interactive entrypoints intersect these limits; the compiler supports some larger recipes that this UI does not. Full-request size includes imports, referenceCandidate, comparison and other execution data. History has its separate 100 transactions / 4 MiB request/checkpoint budget; recovery records have separate limits. None of these may silently substitute for native gate/depth/closure/record/worker limits.

Proposed message for option-product failure (actual metrics interpolated):

> Connection not applied. This project needs 65,160 pin-table options (360 destination pins × 181 source pins); the interactive limit is 65,000. Your accepted wiring is unchanged. Reduce the design or export it for CLI work; the CLI still enforces compiler and solver limits.

Separate messages for nIn/O exceeding 255, UTF-8 request bytes exceeding 1,048,576, and display caps must name the actual breached limit, measured value and preserved accepted state. Do not blame the option product when it passes. For native gate/depth/closure failures retain native code/detail and say validation could not accept the proposal; an unchanged option product can still incur output-copy gate overhead. A successful compose never promises a future comparison can finish.

Remediation implementation: a pure metrics/diagnostics helper in the Codex-owned visual command layer; identical acceptance thresholds/order; use it consistently for Add/Remove/wiring/Advanced/history/recovery entrypoints that already enforce these guards. Keep generic rendering failure separate from rejected mutation. Add boundary regressions at product 65,000 and 65,001, interface 255/256, request bytes 1,048,576/+1 with multibyte strings, REF nOut weighting, metadata fallback, display allocation limits and native output-copy gate overflow. Use synthetic requests and native parse/compose where valid; do not edit accepted fixtures or force an impossible native interface to pass. Assert accurate UI wording and accepted-state preservation.

Closure gate: implemented fix, targeted regressions, unchanged existing tests, independent acceptance. **Documentation and the reproducer do not resolve F1.**

## V2A-F2 — LOW, OPEN

Actual code: [commands.ts:63–116](https://github.com/Technique-S/Flip/blob/2fa7281ba01557f484cef2878e484b6e16f3ffd2/apps/web/src/visual/commands.ts#L63). The nested pin check combines `Object.keys(v).length === 2` with `"component" in v` and `"pin" in v`; it does not verify exact own keys. The checkpoint reproduced acceptance of a pin whose only own keys are `a,b`, with `component,pin` inherited from its prototype. The function later copies those inherited values into a fresh plain pin. Native JSON/schema validation still enforces canonical meaning; this is an overly permissive local command-input boundary, not evidence of prototype pollution or a canonical bypass.

Normalize all command/target/pin records **before value access**:

1. Require a non-null non-array record; obtain own property descriptors and `Reflect.ownKeys` under a typed-error catch. Require exactly the expected own string keys for the discriminated shape. Missing fields, symbol keys, non-enumerable extras and any unknown own key fail closed.
2. Require expected keys to be enumerable own data properties. Reject getters/setters rather than invoking them. Read descriptor `.value`, validate discriminants/scalars/tuple density, then build an explicit clean record from the whitelist; do not spread or Object.assign arbitrary input into a trusted object. Ignore inherited fields entirely. Use fresh records or null-prototype internal lookup maps/Map, never dynamic assignment to a prototype-sensitive dictionary.
3. **Object-literal `__proto__` is distinct from an own key.** `{component:null, pin:0, __proto__:{extra:true}}` normally has exactly the two own data keys; the prototype is not a JSON field. Normalize its two own values to the same clean PinSource as a plain record. `{__proto__: {component:null,pin:0}, a:1,b:2}` fails for missing required own keys. A null-prototype record with the exact own keys may normalize successfully.
4. JSON.parse of `{"component":null,"pin":0,"__proto__":{}}`, a computed `['__proto__']`, or defineProperty produces an actual extra own key and must be rejected. Own `constructor`/`prototype` extras are likewise not schema fields. No blanket ban on otherwise valid canonical string values or instance names is introduced. Inherited extras never become emitted fields.
5. The accepted JSON request/schema/hashing/compiler remain unchanged. This normalization is confined to UI-local command objects. Exotic proxies may execute traps during reflection; arbitrary executable JS objects are not a supported transport. Catch reflection errors, do not claim to sandbox proxies or accept callbacks from project JSON.

Regressions must cover plain JSON, null prototype, object-literal prototype-only cases, inherited required fields with decoy own keys, own JSON/computed/defined `__proto__`, enumerable/non-enumerable/symbol extras, throwing accessor (assert not invoked), sparse arrays, malformed discriminants, negative/bool/NaN/Infinity/unsafe pins and canonical round-trip parity. Add/Remove and the new replacement command share the boundary, with unchanged canonical outputs for valid inputs.

Closure gate: implemented normalization and regression results independently reviewed. **F2 remains OPEN; this branch contains no fix.**

## Risk and dependency register

| ID / severity | Dependency or failure | Mitigation / gate | Owner and current status |
|---|---|---|---|
| SEC-01 / HIGH | PR-controlled workflow/checker/trust root has no independent enforcement under approved solo-maintainer policy. | Keep OPEN/HIGH; no workflow/trust/rules changes here. Functional green is not a security-risk closure. Reassess before contributor expansion/public release. | Repository maintainer; OPEN, retained development risk. |
| F1 / MEDIUM | Misleading capacity feedback; output-copy gates differ from UI table cost. | Metrics/messages/regressions above, before enabling wiring. | Codex implement / OpenCode independent acceptance; OPEN. |
| F2 / LOW | Inherited values accepted by current local pin parser. | Own-descriptor normalization above; no schema mutation. | Codex / independent review; OPEN. |
| WB-01 / HIGH | React Flow optimistic store treated as circuit authority. | Controlled accepted graph; pure one-slot proposal; native validation before commit. Never addEdge into accepted state. | Codex; implementation gate. |
| WB-02 / HIGH | Lost ordering, shifted indexes or stale gestures target a different slot. | Stable IDs, captured base/session/revision/previous binding, strict earlier-source rule; no reorder. | Codex; adversarial matrix. |
| WB-03 / HIGH | Stale response, duplicate events, StrictMode replay or retry double commits. | Synchronous lock, one gesture token, abort + generation guard, idempotent cleanup and no-op suppression. | Codex; delayed-response tests. |
| WB-04 / HIGH | Proof/build/vector/preflight/replay authority survives a semantic edit. | Shared invalidation on Review, historical proof retention, no automatic proof restoration by Undo. | Codex; real compare regression. |
| WB-05 / HIGH | Forged REF metadata/identity, closure or state accepted by previews. | Local eligibility only; existing native imports/environment validation remains authoritative. No network fetching from gestures. | Codex command / OpenCode corpus; gate. |
| WB-06 / MEDIUM | Dense/zoomed pins are unusable with keyboard/touch; false hover validity. | Native inspector picker, reason text, fixed-size equivalent controls and physical-device/AT audit. | Codex UI / OpenCode QA; untested future feature. |
| WB-07 / MEDIUM | Output replacement needs extra native copies or changes identities. | Native output-copy and limit probes; preserve maps/count/order; exact compare/export parity; no hash fabrication. | Codex; output-target stage gate. |
| WB-08 / MEDIUM | V2-A focus/dirty/recovery behavior regresses in Advanced. | Retain unchanged 72 browser cases; shared accepted request and review outside graph subtree; focus tests and refresh/reset tests. | Codex; inherited-test gate. |
| WB-09 / MEDIUM | Pointer-move work amplifies option-product/render cost. | Cached indexes, no network/full cloning per move, bounded profile, measure p95 before acceptance. | Codex / OpenCode measurements; targets unmeasured. |
| WB-10 / MEDIUM | Local/hosted native timing varies; retry hides failure. | Preserve first logs/traces; record every retry separately, unchanged limits; UNKNOWN stays inconclusive. | Lead acceptance owner; known timing limitation. |
| WB-11 / LOW | API documentation diverges from locked React Flow 13.0.2. | Verify installed source/types and integration events, especially cancel/click/drag; no dependency upgrade in scope. | Codex; pinned API gate. |
| WB-12 / MEDIUM | Portable envelope or layout persistence changes canonical format. | Keep gestures/layout/review state private and ephemeral; pending complete proposals use existing base-bound recovery only. | Codex; schema parity gate. |

## Proposed stages and exit gates

1. **V2-B0 — findings and command seam.** After implementation authorization, fix F1/F2 with regressions, introduce the pure ReplaceBinding proposal and captured-base transaction contract, no enabled canvas wiring. Validate NAND/REF/output targets directly against real compose. No accepted fixture changes. Independent review of the local command boundary is the first implementation milestone recommended by this checkpoint.
2. **V2-B1 — native picker and NAND replacement.** Add source/destination Review and shared state in the existing editor, including proof invalidation, no-op, cancel/retry, recovery/history and Advanced parity. Establish keyboard-only and tap-only paths before drag. Real API acceptance and failure tests must pass.
3. **V2-B2 — drag adapter.** Enable only source-to-target handles, ephemeral preview/reason feedback, token cleanup and occupied-target replacement-to-review. Keep delete/reconnect endpoints and node dragging disabled. Test wrong directions, empty drops, Escape, duplicate callbacks, pointer cancellation and narrow layouts.
4. **V2-B3 — existing REF inputs and output bank.** Enable the already-defined target types only after manifest-bound REF/ordering/native-copy-budget tests pass. No new REF, source, output or stateful authoring. Ensure target-specific explanations and compare maps remain exact. All target classes are part of proposed V2-B, not silently deferred to an implemented release.
5. **V2-B4 — adversarial integration and independent acceptance.** Run the full inherited Python/browser/showcase/schema/release/custody pipeline and dual-OS CI on the combined immutable head; record accessibility/performance/touch evidence and honest limitations. Create a draft implementation PR, preserve original failures and stop unmerged for independent review. SEC-01 remains OPEN/HIGH.

Hackathon-critical: F1/F2, atomic one-slot replacement, explicit preview/review, real compose, stale-proof protection, undo/redo, Advanced parity, keyboard/tap alternatives and tests. Deferred: endpoint reconnection, wire deletion, multi-edit batching, component reorder/auto-sort, automatic correction/routing semantics, bus editing, persistent layout, collaborative editing, new guide content, Visual Wiring Canary and V2-C. No release/deployment commitment is made by this schedule.

## Non-overlapping implementation assignments (not dispatched)

Both start from the later authorized implementation base; record exact SHA in each handoff. Freeze the ReplaceBinding shape and expected output/error contract before parallel work. Only Codex integrates; no agent merges its own PR.

| Agent | Exclusive writable paths | Deliverable / stop condition |
|---|---|---|
| Codex lead | `apps/web/src/visual/commands.ts`, proposed `apps/web/src/visual/wiring.ts`, proposed `apps/web/src/visual/WiringControls.tsx`, `apps/web/src/visual/useCandidateEditor.ts`, `apps/web/src/visual/VisualComposer.tsx`, `apps/web/src/visual/visual.css`, `apps/web/src/Composer.tsx`, `apps/web/src/App.tsx`; new `apps/web/tests/visual-wiring.spec.ts`; new `docs/ux/visual-v2-b/implementation/**` | F1/F2 fixes, replacement command, UI/adapter/transaction integration, focused integration tests and evidence. Keep all other paths unchanged. Stop at draft PR and independent review. `projection.ts` is read-only initially; if an actual implementation requires a new projection interface, document and authorize that exact addition before editing. |
| OpenCode independent support | New `apps/web/tests/visual-wiring-adversarial.spec.ts`, new `packages/flip-core/tests/test_p7_v2b_wiring_acceptance.py`, new `docs/ux/visual-v2-b/independent/**` | Native compiler/hostile-command parity, independent input cases generated in tests, black-box UI/network/keyboard/touch/performance observations and exact outputs. No production/interface/config edits; no accepted-fixture or old-test rewrites. Block on frozen command test seam, request Codex fixes rather than patching its files. |

Frozen/read-only for both: all existing schemas/fixtures/evidence, dependencies/locks, Python production, API/CLI, release/trust/checker, CI, main rules. No future test file is created in this checkpoint. Neither assignment permits wallets, transactions, RPC expansion, public solver hosting, deployment, Canary or V2-C. Independent reviewer should assess the final combined head, not only either assignment in isolation.
