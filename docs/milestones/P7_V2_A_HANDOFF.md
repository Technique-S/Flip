# P7-V2-A controlled NAND editing — implementation handoff

**Independent review pending. Keep draft PR #14 unmerged. V2-A only; no P7/V2-B/V2-C completion or release/deployment claim.**

## Exact source and authorization

Accepted main / branch origin: **`fc9c0c1bcb2557169dd89af0c3b2c5a7628c9adf`**. The fetched main matched this pin. Phase 1 checkpoint: `73d70b971b64de899acd9f6d2f49301eda8d6217`. Production implementation: **`b23d3dcf8f98e9b95cd0bc8ca8fbf612045e1daa`**. The following evidence commit is documentation only; its exact final SHA and final-head CI links are reported on [draft PR #14](https://github.com/Technique-S/Flip/pull/14).

The [Phase 1 checkpoint](P7_V2_A_DESIGN_CHECKPOINT.md) and its 24 native compiler observations remain unchanged historical records. The owner then explicitly answered **“Authorize explicit input bindings”** to the question whether Add NAND may collect two numeric source/pin selections and atomically validate/commit them while interactive wiring remains excluded. This resolves the checkpoint's scope boundary; it does not authorize placeholder wiring, REF authoring, output remapping or a new schema. The implementation follows the same accepted main through that checkpoint, without rebasing onto an unrelated source.

## Delivered workflow and private command contract

Composition contains the shared **Add NAND**, **Undo edit**, **Redo edit**, NAND selector and **Remove NAND** controls in both Visual and Advanced. The Visual inspector also offers removal for the selected NAND. Existing build/compare actions remain in Advanced/the existing Canary page; selecting/viewing does not execute anything. React Flow nodes, edges and handles remain non-draggable/non-connectable/non-reconnectable; Delete/Backspace do not edit the graph. No React Flow store is an authoritative project.

`apps/web/src/visual/commands.ts` proposes copied M3 requests using a small deterministic private command layer. These command types are not a new HTTP API, canonical schema or portable format.

| Command | Exact parameters / safety boundary |
|---|---|
| AddNand | `{type:"AddNand", instanceId: Name, inputs:[PinSource,PinSource]}`. Both bindings are explicitly chosen; controls begin empty. A PinSource is the existing `{component:null-or-existing-ID,pin:integer}` contract. Append only, no order inference or default pin. Unique canonical Name, exactly two input objects, integer/in-range preceding outputs, and closed command/pin keys. |
| RemoveNand | `{type:"RemoveNand",instanceId:Name}`. Must target NAND by actual kind, not its name. Enumerate all candidate input and final-output references. A referenced target is blocked with exact locators; an unreferenced target requires explicit confirmation and removes only that array entry. No cascade/remap or REF removal in this command. |
| Undo / Redo | Restore a complete previously accepted request snapshot through **fresh existing compose validation**. Successful movement advances operation revision, invalidates live results and never resurrects old proof as current verification. No layout-driven semantic changes. |

The authoritative boundary is the existing Python parser/compiler through `POST /api/v1/compose`. The browser's reused display guards and interactive budgets reduce work and improve feedback; they never issue a proof or substitute for core validation. No JS compiler, evaluator, REF resolver, solver or canonical hashing implementation was added. `requestKey` is explicitly an exact local JSON snapshot comparison, not a canonical digest or security authority.

## Draft, validation and atomic commit

A NAND form is separate from the accepted execution request. Unselected inputs are only local form fields, never placeholder PinSource values. Complete the form and choose **Validate and add NAND**. The editor clones the full accepted request, proposes the NAND and validates it before changing `App`'s accepted request or `flip-project` storage. Native failure retains the draft and exact last accepted request, with a clear error. A compiler response is validation/build acceptance, not equivalence verification.

Advanced **candidate recipe** changes use the same draft/validation/history boundary. Invalid intermediate wiring remains visible in Advanced, is explicitly blocked from execution/portable export, and cannot overwrite the accepted stored request. Visual shows its existing explicit unavailable state rather than a partial fabricated graph. Discard returns to the accepted candidate. Comparison, debugging and portable actions are blocked during local candidate drafts; current results have already been invalidated.

A synchronous pending guard prevents duplicate transactions. Each validation captures an operation generation and exact cloned request; cancellation/project replacement aborts the browser request and invalidates its token, so a late response cannot commit. Project replacement creates a new component-history session even if its projectId is reused. Prior-render controls and stale external change callbacks are checked against the current accepted snapshot. Existing host/origin/loopback/native opt-in/worker controls remain unchanged.

**Legacy execution setup is a deliberate history boundary:** comparison/reference/intent/limit controls retain their existing validation-at-operation behavior when the candidate itself is unchanged. This preserves, for example, a small execution budget producing the accepted native UNKNOWN behavior instead of turning it into a new editor validation policy. A setup change explicitly resets component undo/redo and invalidates current results; it cannot modify candidate bytes through this path. Importing/opening another project also resets component history. This is component-edit history, not a general undo system for every workbench action.

## Semantic identity and history invariants

History snapshots include the complete request: candidate kind/order/IDs/input sources/final outputs, external input count, sources/imports/REF identities and dependency manifests, local reference, comparison and pin maps, relation/trust assertion and limits. No recipe index renumbering, input/output remapping, source alias rebinding or REF identity change occurs during NAND commands. Python may assign different binary signal offsets and insert final-output copy NANDs; this changes hashes and requires fresh comparison.

Undo/redo preserve the same saved/export checkpoint and restore the full target semantic snapshot atomically. A successful divergent edit clears Redo; rejected edits do not consume history. History is bounded to **100 transactions and 4 MiB serialized request/checkpoint bytes**, with visible eviction. Dirty state compares the full current request to its opening/export checkpoint. Uncommitted local drafts have a separate explicit unsaved/blocked indication. Page/mode switches preserve the App-owned history; reload starts a new in-memory history session.

Saved state means an opening/export-request checkpoint, not proof of a disk write. Browser session persistence is separate. Project export and successful complete-portable download requests update the checkpoint; Undo away from it becomes dirty, and Redo back clears that difference. A bounded, request-bound private browser checkpoint preserves dirty state after reload.

An explicit workspace reset clears the private draft/export checkpoint keys and in-memory comparison history, alongside the existing project/package reset. The reset regression verifies the private keys are absent before another project is opened.

Complete in-flight candidate proposals are stored separately from `flip-project`. On reload the stored accepted request is validated first; a recovered proposal must match that exact base and pass real compose validation before committing. Recovery never restores current proof. Cancellation clears the proposal; malformed/mismatched recovery cannot mutate accepted state. Unsubmitted form fields and undo/redo stacks are session UI state rather than Portable 1.1 data. Storage failures warn users to export; no durability guarantee is made when storage is unavailable.

Current build/comparison/vector/preflight/replay authority is invalidated when a candidate draft/edit/history transition begins. Original comparisons are retained in a separate **Historical comparisons — not current verification** view with their original request and revision. Retaining up to ten comparisons / 4 MiB is explicitly bounded; older in-memory records may be evicted with a notice. Exported evidence files and all previously accepted repository evidence remain untouched. Undo to identical old bytes does not reverify them; a fresh explicit native operation is required.

## Keyboard, focus and render observations

All commands have native buttons, labeled input/select controls and keyboard alternatives. Add focuses the ID field; invalid submit focuses the first incomplete field. Successful add selects the new node/inspector and focuses the visible inspector (or shared NAND selector in Advanced). Removal focuses its confirmation heading; successful removal/history movement returns to the shared selector or Add action when no NAND remains. No global Ctrl/Cmd-Z interception interferes with input editing. Status announcements expose revision, pending validation, dirty state, draft failure and cancellation. Old canvas navigation, exact mapping tables and read-only protections remain usable.

Desktop and 390px renders were inspected from actual test screenshots, including the explicit-input form, committed NAND inspector, narrow graph using the existing Fit circuit control, and blocked removal. The narrow view passes axe and document-overflow checks; the inherited debugger overflow regression also passes after making the new disabled fieldsets width-neutral. No simulated/invented UI or new visual engine. Screenshot hashes, dimensions, exact source binding and local original-file paths are indexed in results; raw PNGs remain in ignored scratch under the existing custody policy, without adding binary exceptions or encoding images to bypass that policy.

## Acceptance mapping and actual execution

`apps/web/tests/visual-edit.spec.ts` adds **28 tests** alongside the unchanged 44 existing browser cases. The new tests execute the real compose API for proposed requests and history moves; copied native requests are explicitly synthetic tests, never replacements for accepted fixtures.

| Required case | Executed coverage |
|---|---|
| 1 Add NAND | Explicit form with empty initial inputs; real compiler proposal/commit; inspector selection. |
| 2 Remove unreferenced NAND | Native compile round-trip and confirmed UI removal restore exact original request. |
| 3 Reject referenced NAND removal | Final-output UI block and native input-reference rejection; REF cannot be removed by NAND commands. |
| 4 Ordering/reference stability | Exact request comparisons; middle unreferenced removal preserves remaining components, maps and references. |
| 5 Multiple undo/redo | Two adds, two undos and two redos through real API, with exact snapshot equality. |
| 6 Divergent edit | Undo then new add invalidates Redo; previous history objects remain unchanged. |
| 7 Rapid/interrupted operations | Two immediate submits make one transaction; delayed real compiler response ignored after cancel; in-flight refresh proposal revalidated before recovery. |
| 8 Visual/Advanced parity | Exact source values/storage/request equality across mode switches and shared draft behavior. |
| 9 Malformed command parameters | Eleven reject cases: null/unsupported kind/duplicate or bad ID/arity/null binding/bool/negative/forward/extra command or pin fields. |
| 10 Boundary graphs/history | Native compiler accepts the 178-component test baseline; the next edit hits the unchanged interactive table budget. Bounded history eviction and byte/count invariants. |
| 11 Stale evidence | A real EQUIVALENT comparison stays historical after edit and Undo; current evidence export remains disabled until a fresh result. |
| 12 REF dependencies | Full imports/sources/comparison/output bindings unchanged, including actual native manifest dependency equality. |
| 13 Keyboard-only actions | Native keyboard add, source selection, inspector focus and confirmed removal; no mouse command required. |
| 14 Saved/dirty/invalid draft | Export checkpoint, Undo/Redo dirty transitions, native-invalid Advanced draft, real RESOURCE_LIMIT failure and request-bound refresh recovery. |
| 15 No unapproved operations | New controls make only existing compose POSTs; mode/selection stay local. Existing publication-handoff test still reaches STOP_AUTHORIZATION, not a transaction. |

Latest complete local browser execution: **72/72 passed**, zero skips/flakes/unexpected results. This includes the workspace-reset and two focus regressions after earlier complete 69- and 70-case passes. Web lint and TypeScript/production build pass. Post-implementation showcase, release bootstrap/integrity, all nine schema exports, three Node parity checks, Ruff and clean committed-tree custody results are retained in the results bundle. The pre-implementation checkpoint also executed all **33** workflow commands locally, including **702/702 Python**, agent/authorization/adapter/portability checks, smoke checks and benchmark, all successfully. Python/API/CLI sources are byte-identical between that checkpoint and this implementation; these earlier Python results are not relabeled as a new final-head run. Final-head hosted CI independently runs the entire current workflow on Windows and Ubuntu; its exact run links/disposition are recorded on PR #14 after completion, never inferred from the earlier green checkpoint.

Initial failures remain visible in the results. An initial full browser run was **67 passed / 2 failed**: the debugger overflow fixed by scoped fieldset styling, and the unchanged portable-agent journey timing out at its existing 60-second bound. Its trace showed 11.9s and 29.8s native workflow calls before the final handoff request; timing contention is an observation/remaining local risk, not a proved root cause. The unchanged journey passed isolated in 27.8s and in the complete successful 69-case run in 22.5s and final 70-case run in 25.1s. No timeout, fixture or accepted test was changed. The first new keyboard test opened a native select popup unintentionally; its corrected sequence asserts actual selected values/focus and passes. A test launch after a caught local JSX build error was stopped to avoid stale assets; it is not acceptance evidence. Final lint/build and full browser results are clean.

## Hosted CI focus regression and correction

The first final-head push run [45896495418](https://github.com/Technique-S/Flip/actions/runs/45896495418) at `e92ae1e21c8c3ea0fd7e713c1a643ed642a906e7` exposed an inherited Advanced keyboard focus race: Ubuntu npm test recorded 69 passes / 1 failure at `workflow.spec.ts:92`; the sibling Windows job was cancelled by the unchanged fail-fast policy. The original log is retained in the final results directory.

Advanced now keeps the accepted recipe visible while validation is pending, so future disabled rows cannot be focused before commit. Ordinary Advanced commits do not trigger NAND inspector focus; an existing originating field is restored only when focus otherwise fell to the document body. Two deterministic regressions validate both new-row and existing-field focus using real authoritative validation. The unchanged inherited assertion remains intact. Final complete local execution is 72/72 passed, including the corrected case. Final-head hosted results must be observed on PR #14 before reporting them as green; older green matrices are not substitutes.

## Provenance, limits and review handoff

The fresh V1 canonical-before/after attachment remains byte-identical to the accepted capture, SHA-256 **`b4c5aa157ef966f7022c880bb637c7ea0d121c4710f5610c2614c0759158b933`**. Original project/netlist/manifest identities remain `0xff70814e174ae2dc841eef4a9e6367bb5318bccd069307c3afdce1adaa329959`, `0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`, and `0x10a2616767a30352158c32aae8cdb85b44cd7f5f04b168c462f41a8789b6f299`. New semantic edits correctly change identities; fresh runtime reports with timing/engine context are not claimed universally byte-identical.

No Python production code, backend route, solver, schema, dependency lock, accepted fixture, prior evidence, workflow, release trust/checker or main rules were changed. Source/path inventories and the unchanged protected-path diff are retained. [Final results index](../ux/visual-v2-a/focus-fix/README.md) binds raw reports and checksums. Final evidence commit has only additive docs after the implementation SHA above.

Unsupported/deferred: interactive wiring/reconnect/drag edits; new REF authoring; LATCH/stateful authoring; decoded REF expansion; visual Canary overlays; persistent visual positions or a new portable visual envelope; cross-project/configuration undo; persistent undo stacks; screen-reader speech and physical touch-device acceptance. V2-B/V2-C need separate authorization and frozen interface decisions. Existing Advanced REF controls and existing Canary/agent workflows remain available under their original contracts; no new such feature was implemented here.

**SEC-01 remains OPEN/HIGH** under the approved solo-maintainer development policy. Passing functional tests does not resolve the repository trust-root risk or supersede the independent conditional security review. No wallet/signing/transaction, public solver hosting, deployment, production release or own merge. Stop with the draft PR open for independent review of the full combined delta.
