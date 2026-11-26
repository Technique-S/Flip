# P7-V2-A — semantic design checkpoint

**Disposition: stop after Phase 1, as explicitly required by the authorization. No V2 editing implementation or acceptance is claimed.**

Exact accepted/fetched main and branch parent: **`fc9c0c1bcb2557169dd89af0c3b2c5a7628c9adf`**. Dedicated branch: `codex/flip-visual-v2-a`. Implementation SHA: **none**; this branch contains documentation and read-only research evidence only. The exact checkpoint commit is identified on its draft PR and delivery handoff. No main merge, deployment, schema/dependency change, fixture rewrite, second engine or security-control change.

Authority: the owner's [complete V2-A request](../ux/visual-v2-a/checkpoint/authorization.txt), including: “If atomic component creation cannot be supported safely under the existing model without adding wires or changing semantics, stop at a design checkpoint. Do not invent placeholder wires, inputs or outputs.” This checkpoint is triggered by that instruction, not by a skill or an inferred approval requirement.

## Finding and scope decision

A wire-free, disconnected NAND **cannot be committed** under the accepted canonical contracts. Every NAND requires exactly two explicit, valid input bindings. A UI-only draft can describe an unconnected NAND, but that is not a canonical component and cannot satisfy the requested canonical AddNand acceptance case. The existing Advanced editor automatically selects the first available input twice when adding a NAND. Copying that behavior would invent input intent, which this request forbids.

A schema-compatible route exists **if the owner permits explicit input-source selection as part of creation**: collect an instance ID and two numeric source/pin selections, preview those two new bindings, then validate/commit the complete request through the existing compose API. This requires no pin dragging, new backend or schema. It does, however, add two input connections. The authorization also says “without adding wires”; this checkpoint does not silently interpret that phrase as permission for a new source-selection workflow.

**Concrete decision needed before Phase 2:** permit the narrow Add NAND form to collect both explicit input bindings and atomically compile/commit them, while keeping interactive wiring, REF authoring and output remapping out of scope; or retain the no-new-bindings restriction and accept draft-only creation, with canonical AddNand still unavailable. Recommended: the explicit-input form, subject to that scope decision. No placeholder pin 0, inferred first source, constant, output or REF binding is a fallback.

## Six established semantic constraints

All citations below refer to the exact accepted base; [source provenance](../ux/visual-v2-a/checkpoint/source-provenance.json) records blob identities and SHA-256 values.

| Question | Observed answer and exact source |
|---|---|
| Can a NAND temporarily have unconnected inputs? | Not inside a canonical request. `packages/flip-core/src/flip_core/models.py:198` defines NAND inputs with min=max=2, each a strict `PinSource` (`:186`). Missing, empty, one-element, null, excessive, undefined/self/negative/out-of-range input probes reject. Temporary empty fields must stay outside this schema. |
| Does adding/deleting require index renumbering? | Recipe references use stable instance IDs, not component array indices. Unreferenced removal requires no recipe-pin renumbering; other entries stay in exact order. Binary signal offsets are assigned sequentially by the compiler (`composition.py:115`, `:139`) and may change. Array order and emitted netlist bytes are semantic inputs, not layout metadata. |
| How are preceding references represented? | `{component: <instanceId>, pin: <numeric output index>}`; external input is `{component: null, pin: i}`. Validation builds a width map in array order and rejects undefined/forward/cyclic or out-of-range sources (`models.py:239`, `composition_models.py:34`). Append-only creation avoids reorder policy. |
| How do REF dependencies and output mappings behave? | REF components bind source aliases and exact imported identities/manifests. Neither their aliases nor import/source records should change for NAND edits. Final outputs explicitly refer to external pins or component IDs. Removing any NAND referenced by another input or final output is invalid unless references are explicitly repaired; repair/remapping is outside this stage. Preserve referenceCandidate and comparison maps exactly. Compiler source-binding validation remains authoritative (`composition.py:42` onward). |
| Does serialization preserve stable IDs? | Yes, `instanceId` and PinSource component names remain request fields. Existing canonical JSON sorts object keys, not array order (`canonical.py:35`); it neither regenerates IDs nor renumbers references. Duplicate/invalid IDs reject. A component named `nand0` in the actual half-adder is **REF**, not NAND: authorize removal by kind, never name. |
| How does Advanced handle invalid intermediate configurations? | `apps/web/src/Composer.tsx:75` fills inputs from the first available choice; `:207` pops the last component without dependency repair. `App.tsx:286` clones/mutates/replaces state; `:259` checks UI budgets and clears live results but does not call canonical validation. State is written to session storage at `:194`; actual compile is a later explicit action at `:379`. Thus invalid intermediate requests can exist in current Advanced state. It is not a ready-made validate-before-commit transaction layer. |

The compiler preserves final output intent using derived NAND copies if requested outputs are no longer the final emitted signals (`composition.py:145`). In the synthetic feasibility probe, appending an unused NAND with explicitly supplied external inputs changes expanded gates from **8 to 13**, not merely 8 to 9. Its recipe output mappings, source/import identities and REF dependency digest remain unchanged, but project/netlist/manifest hashes change. A seemingly irrelevant graph edit cannot retain a current proof.

Observed original sample identities remain:

- Project: `0xff70814e174ae2dc841eef4a9e6367bb5318bccd069307c3afdce1adaa329959`.
- Netlist: `0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`.
- Manifest: `0x10a2616767a30352158c32aae8cdb85b44cd7f5f04b168c462f41a8789b6f299`.

Removing the synthetic unreferenced NAND restores the exact original request and all three original hashes. Middle insertion/removal likewise preserves all existing recipe IDs, inputs, output order and bindings. These are compiler observations on copied requests, not implemented editor commands or equivalence proofs.

## Proposed private command contract — not implemented

These are local command descriptions, not a public API/schema addition. The complete unchanged M3 execution request remains the only backend input. No backend or network authorization is added.

| Command | Parameters and preconditions | Proposed result |
|---|---|---|
| AddNand | Explicit `instanceId` using canonical Name syntax; **exactly two** existing schema-compatible PinSource values, both explicitly chosen; unique ID; sources must be external or preceding component outputs. Append only. Scope decision above required. | Clone the complete accepted request and append one NAND; preserve sources/imports, reference, limits, comparison, input/output mappings and all preceding components. Existing compose validation must succeed before commit. |
| RemoveNand | Exact candidate `instanceId`, whose kind is NAND; enumerate inbound references from all other candidate inputs and final outputs. | Reject referenced removal with explicit dependants/locators. Otherwise remove only that element from a cloned candidate, keep remaining order/IDs/bindings, validate through compose before commit. No cascading delete, automatic remap or REF removal. |
| Undo | A prior full-request snapshot in the same project session; no unresolved pending operation; sufficient bounded history. | Revalidate the target complete snapshot, then atomically select it and advance generation. Historical proof is never restored as a fresh result. |
| Redo | An unconsumed future snapshot from the same session and history branch. | Same validation/invalidation as Undo. A successful divergent edit clears future history; a rejected proposal does not change canonical history. |

The pure deterministic layer may propose a copied request or an explanatory rejection. It cannot declare a request canonical/verified on its own; `parse_request`/`compile_project` through existing compose must decide. No compiler/resolver/evaluator/hash semantics are duplicated in TypeScript. Malformed command payloads fail closed even if TypeScript types were bypassed.

## Staged versus accepted state

Proposed state is held above Visual and Advanced, never in React Flow node state:

1. **Accepted request:** the last complete request that passed authoritative compose, with its returned project/manifest/netlist identity and local operation generation. Existing saved package/evidence remain separately preserved.
2. **Local draft:** an incomplete form/proposal separate from accepted JSON. An empty input choice is represented only in this local form; never null/zero/undefined inside a committed NAND input. Show an explicit draft/invalid reason and missing-field markers. No executable export, proof attachment, comparison or compile-as-current of an incomplete draft. Cancel restores the accepted view without changing bytes.
3. **Pending validation:** clone the full accepted request with the explicit proposed edit. Freeze duplicate submission; retain accepted state, saved package, proof history and proposal. The UI announces validation and provides cancellation. Validate with the existing compose call, subject to existing loopback/opt-in/custody controls. No new endpoint or automatic live-chain operation.
4. **Commit or reject:** only a successful response matching the exact request snapshot, project-session token and generation can commit. A stale/cancelled/interrupted response is ignored. A resource/validation failure leaves accepted state untouched and explains the invalid draft. Commit is one update of request, history, dirty identity and result invalidation; “built” is not “verified.”

Advanced edits must use the same staging/commit/invalidation boundary; a Visual-only transaction layer would leave unsafe intermediate state and divergent semantics. Valid existing Advanced operations must remain available; invalid intermediate controls must be staged and visibly blocked from execution rather than silently normalized or discarded. Opening/restoring/replacing a project, including a different file with the same projectId, starts a new session and clears incompatible history after explicit unsaved-work handling. Page/view switches preserve that session and draft.

## Atomic history, evidence and saved state

The proposed history entry captures the complete semantic request: component kind/order/IDs/inputs, external count and final outputs, source/import manifests and identities, local reference, comparison/input/output maps, relation, trust assertion and limits. Presentation selection can be stored separately; it grants no execution authority.

- Every accepted edit/undo/redo increments a monotonically increasing operation generation in the current session. Capture exact request bytes for stale-response comparison; returned canonical hashes use the existing Python implementation. Rapid repeats cannot create duplicate IDs, overwrite later commits or replay an old response.
- Undo/redo restores semantic state atomically, then **clears current verification/build/debug/observation authority**. Prior results stay available only as historical evidence bound to their original request/revision. Restoring the same old bytes does not count as a fresh verification. Recompare explicitly.
- Rejected proposals do not mutate accepted state or consume history. A successful edit after Undo invalidates Redo. Cancellation invalidates pending tokens; no late commit. Disable actions with clear explanations while pending; do not silently queue stale commands.
- Track dirty state against an explicit saved/export checkpoint of the full request, not against component count or graph geometry. Session-storage persistence is not a saved file. Browser download initiation does not prove a successful disk write; UI wording must identify that limitation. Undo to the saved snapshot can clear semantic dirty state; incomplete drafts remain separately dirty and non-executable.
- Keep Portable 1.1 package/history/evidence bytes intact until a separate explicit save operation creates a validated revision. No visual fields inside the accepted schema. Clearing results is not deletion or rewriting of historical evidence.
- Retain the architecture's proposed bounded history (100 transactions / 4 MiB) with a visible eviction notice, subject to implementation measurement. Enforce serialized bytes and command count before allocation; do not reinterpret this as a new canonical limit.

## Proposed controls and focus behavior — not shipped

Keep Flip's current restrained workbench controls and existing Visual/Advanced switch. A discoverable **Add NAND** action opens the explicit-input form only if authorized; every source control begins unselected. A selection in the existing inspector identifies the exact candidate instance and kind; only NAND exposes removal. Before a referenced removal, show the dependants and explanatory block; do not offer an ineffective confirmation that would still leave invalid references. Unreferenced removal displays the exact target and an explicit confirmation/cancel path. No wire creation, draggable handles, reconnect, pan-to-edit semantics or graph-store mutation.

All actions have normal keyboard buttons and labeled native inputs/selects. Undo/redo have disabled reasons and do not intercept text-field undo. After create, focus the new component inspector; after removal, focus the component list; after cancellation, return focus to the initiating control; after invalid submission, focus the first invalid field with a text error. Use a stable status region for successful commits, history movement, dirty state and interrupted/failed validation. Keep focus stable during unrelated renders. Mouse and keyboard must call the same command path. Selection/view-only actions make no request, dirty change or proof change.

No V2 screenshots or keyboard-success claims exist because these controls were not implemented. Existing V1 selection/keyboard/zoom and readonly protection remain unchanged (`VisualComposer.tsx:168`, `:181`, `:184`, `:188`). New interface acceptance must exercise rendered controls rather than infer completion from these existing components.

## Measurements and acceptance gap

The [archived read-only harness and results](../ux/visual-v2-a/checkpoint/README.md) executed **24/24 expected semantic observations**, using the actual existing canonical parser/compiler and historical imports. Synthetic copied requests are explicitly labeled; no accepted fixture or user's project was altered. It confirms incomplete NAND rejection, explicit-binding feasibility, unsafe deletion rejection, middle insertion/removal identity stability, REF/source/import/comparison preservation, malformed IDs/pins, and limits. With the retained source closure, 4990 constructed NANDs compile; 5000 parse but exceed the aggregate composition-plus-import record budget (`RESOURCE_LIMIT`), and 5001 violate the component-count schema (`INVALID_INPUT`). This is not a general performance budget or graph rendering acceptance.

Fresh local dependency install used the locked existing versions, reporting zero npm vulnerabilities and the existing pending-esbuild-install-script warning without a policy override. Web lint checked 25 files; the existing TypeScript/production build passed. No frontend was edited, so no new UI detector/screenshots are applicable. Required full baseline execution at the exact accepted main is [run 45757589943](https://github.com/Technique-S/Flip/actions/runs/45757589943): both Windows and Ubuntu succeeded, each **702 Python / 44 browser / 28 showcase**, with schema, release-integrity, custody and remaining workflow checks. These are baseline results, not V2-A acceptance. Fresh checkpoint-branch execution and exact CI links are reported on its draft PR after completion; a pending job never counts as PASS.

| Requested V2-A acceptance case | What this checkpoint establishes | V2-A editor acceptance |
|---|---|---|
| 1 Add NAND | Canonical add requires two explicit bindings; scope decision pending. | BLOCKED at Phase 1 |
| 2 Remove unreferenced NAND | Native compiler confirms safe copied-request removal/restoration. | NOT TESTED; command/UI absent |
| 3 Reject referenced removal | Native compiler rejects stranded input/output references. | NOT TESTED; command/UI absent |
| 4 Order/reference stability | Copied native recipe IDs/order verified. | NOT TESTED; command/UI absent |
| 5 Multiple undo/redo | Contract specified only. | NOT TESTED |
| 6 Divergent history | Contract specified only. | NOT TESTED |
| 7 Rapid commands/interruption | Session/generation design specified only. | NOT TESTED |
| 8 Visual/Advanced parity | Existing V1 unchanged; common staging integration specified. | NOT TESTED for editing |
| 9 Malformed commands | Native malformed recipe probes reject; new command parser absent. | NOT TESTED |
| 10 Boundary graphs | Native schema/compiler boundary measured; visual display bounds unchanged. | NOT TESTED for editing |
| 11 Stale evidence | Native identities change; invalidation/history design specified. | NOT TESTED for editing |
| 12 REF dependencies | Exact unchanged native source/import/dependency digests observed. | NOT TESTED through editor |
| 13 Keyboard actions | Existing V1 only; new focus/control contract specified. | NOT TESTED for editing |
| 14 Saved/dirty/invalid draft | State design specified only. | NOT TESTED |
| 15 No unapproved operations | No runtime/network/transaction code added; source/trust blobs unchanged. | NOT TESTED for new controls |

## Handoff and remaining dependencies

Resolve the explicit-input creation scope first. If approved, implement the small shared staging/command/history layer plus the NAND form/removal controls and all 15 acceptance cases on a refreshed accepted baseline; each commit must retain exact code/evidence identities. Full Python/browser/showcase/schema/release/custody checks and both OS CI remain implementation gates; native probes are not a substitute. Leave any implementation PR unmerged for independent review.

V2-B/V2-C remain separate: interactive wiring/reconnect, REF authoring, decoded REF/LATCH expansion, visual Canary, layout transport and broader authoring workflows are not added by this design. Preserving correct output maps and REF identities is a V2-A constraint, not permission to implement their editors. No schema mutation is proposed here.

**SEC-01 remains OPEN/HIGH** under the approved solo-maintainer development policy. This checkpoint does not alter CI, main rules, trust metadata, custody checks, solver policy or the prior independent CONDITIONAL PASS. No signing/transaction, public solver hosting, production deployment or historical-evidence rewrite.
