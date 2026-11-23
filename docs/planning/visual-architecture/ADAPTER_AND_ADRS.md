# Proposed ADRs and canonical adapter v1

Status: **PROPOSED_FOR_IMPLEMENTATION_REVIEW**, not executable schema or accepted production change. Applies to P7/P8. Prior frozen contracts and proof semantics remain intact.

## ADR-V01 — Renderer, not circuit runtime

Choose controlled React Flow behind pure projection/edit adapters. App owns the accepted execution request, last valid package, incomplete draft, layout and operation generation. Graph callbacks propose domain commands. Existing Python parsing/compile is authoritative for visual, numeric table and CLI; compare/vectors/debug/replay use existing entry points. Client checks reduce error latency but cannot approve execution. Consequence: no JS NAND evaluator, REF resolver, SAT solver or temporal simulation, even for a tutorial.

## ADR-V02 — Keep the existing editor and shell

Place Visual/Advanced inside Composition; Advanced is today's numeric table, not an invented HDL/raw-netlist editor. Retain Sources/Library/Canary/Evidence navigation and all existing controls. Shared edits and invalidation sit above both views. Consequence: changes to App/Composer integration require focused regression and independent review; a full shell replacement is unnecessary.

## ADR-V03 — Separate presentation and semantic identities

Version projection as `flip-visual-adapter-1.0.0` and layout as `flip-visual-layout-1.0.0`. Read-only stage uses local view state only. Later introduce single-file `flip-visual-project-1.0.0` wrapping exact Portable 1.1 plus layout and an outer digest. Do not add fields to accepted 1.1 or change its hash preimages. Explicit legacy extraction reports discarded layout; version-aware CLI/API transport is a reviewed later PR. No hidden backend change in V1.

## ADR-V04 — Unsupported state is visible, never erased

Candidate editing initially permits only canonical NAND/stateless REF. Decoded import inspection may show actual LATCH d/q/state index and unresolved/unsupported placeholders as read-only scope. Preserve original import bytes/manifests even when visualization is incomplete. Disable unsupported editing with reason. Lower-level `execution.beat` support does not establish public trace API or sequential equivalence. Full latch authoring requires a new recipe version; bounded simulation/trace reporting requires its own reviewed interface. Mandatory P7 LATCH representation is retained; authoring scope remains an explicit open decision.

## ADR-V05 — Transactional edits and identity-bound results

Each accepted semantic command is one history transaction, resets executable results and increments generation. Undo/redo/restoration revalidate and invalidate; do not revive old proof. Layout-only commands preserve semantic hashes and current result meaning. All responses require matching request hash, generation and project session. Keep proof history separately labeled historical. Never accept cached metadata as execution, correction or chain authority.

## Adapter interface contract

Proposed interfaces (specification only):

```text
projectExecution(validatedExecution, optionalLayout) -> Projection
projectDecodedScope(validatedImport, scopePath, budget) -> ReadonlyProjection
proposeEdit(currentExecutionHash, Command, draft) -> EditProposal | DraftIssue[]
validateAndCommit(proposal, generation) -> existing compose response | existing error
projectDiagnostic(validatedDebugResult, executionBinding, projection) -> Overlay
```

`Projection` contains adapterVersion, executionRequestHash, ordered semantic nodes, ordered edges, an ID→canonical locator map, read-only issues and layout. It contains no executable graph-library store or authoritative verdict. Decoder input must come from accepted bounded Python decoding/import, not unchecked client TAP-02 interpretation. If existing compose output lacks a record-to-project map, V1 uses canonical recipe projection only; decoded REF internals need a separately reviewed read-only adapter API in V2. Do not silently add an API or reconstruct nested behavior from labels.

### Stable IDs and widths

| Object | Stable renderer ID / canonical locator |
|---|---|
| Candidate component | `candidate/component/<instanceId>`; locator stable instanceId, array ordinal stored separately |
| External input bank | `candidate/external`; pin `out:<decimal i>` ↔ `{component:null,pin:i}` |
| NAND/REF output | `out:<decimal i>` ↔ `{component:instanceId,pin:i}` |
| Component destination | `in:<decimal j>` ↔ component.inputs[j] |
| Final output destination | `candidate/outputs`, `in:<decimal j>` ↔ candidate.outputs[j] |
| Canonical edge | `candidate/edge/<destination instanceId or reserved outputs>/<input index>`; source is payload, so reconnect preserves destination identity |
| Reference / decoded scope | Separate namespace includes side, ordered REF instance path, netlist hash and record ordinal; never alias-only/circuit-ID-only keys |

Use reserved namespaces outside valid canonical Name syntax, not colliding user names. IDs are renderer-neutral strings with strict length/encoding and unique-target validation. No random ID regeneration on render. Circuit IDs remain decimal strings; no Number conversion. Names/aliases are escaped plain text, not HTML. Input/output label includes index, direction and **width 1**; REF nIn/nOut are counts of one-bit ports. A future bus is an explicitly ordered UI grouping, not an implicit multi-bit edge or new width interpretation.

Example: source `candidate/component/xor`, handle `out:0`, target `candidate/component/inv`, handle `in:1` proposes setting `inv.inputs[1]={component:"xor",pin:0}`. No guessed signal number is serialized. Candidate array order remains unchanged on open, selection or drag. Existing compiler alone inserts any final-output copy NANDs.

### Validation and commit algorithm

1. Resolve exact current project/generation and unique IDs. Reject stale session/hash commands.
2. Check source output→destination input, integer in-range pins, scalar widths, one driver per target, legal fan-out, source/import/manifest bindings, supported kind/state. Wire crossing is no junction. NAND may use the same source on both inputs.
3. New/unbound nodes and disconnected ports stay in a separate non-executable draft; never insert default pin zero. Show missing/invalid target and block compile/verify/export-as-executable until complete. Preserve last saved valid package.
4. Canonical DAG order: opening existing requests preserves exact component/source/import array order. Rewiring to a later component uses stable topological ordering with existing ordinal as tie-breaker and explicit semantic-diff preview. Reject combinational cycles. New order may change bytes/hashes; no claim of canonical equivalence merely from graph isomorphism.
5. Submit through existing compose path using the unmodified request schema. Keep previous accepted state while validating. Commit only matching latest successful response; failure retains draft and original. All semantic views and guide events update atomically. Imported/untrusted JSON cannot skip Python validation.
6. Compare/vectors/debug are separate explicit actions on that accepted revision. Preserve reference choice, relation, pin-map bijections, trust assertion and limits. A build response is not a proof.

Delete/multidelete previews incident edges and output/map effects; one atomic command, cancel leaves bytes unchanged. Width shrink that strands pins remains an invalid draft until explicitly repaired. General history has proposed 100 commands/4 MiB bound and visible eviction; drag coalesces at pointer-up. Reconnect, remove and restore are semantic transactions. Project replacement clears history after unsaved-work protection. A pending validation never commits after cancellation, undo or project switch.

### Layout transport (V5, not V1)

Layout contains version, projectId, executionRequestHash, revisionHash, integer x/y (±1,000,000), viewport integer x/y and zoom thousandths, collapsed IDs and optional manual bend points (bounded 16 per edge). Reject floats/NaN, excessive labels, unknown versions, URLs/scripts and over-budget structures. Max proposed 5,002 positioned nodes, 256 KiB layout; entire envelope remains ≤1 MiB. Stable IDs must refer to actual project elements. On stale layout show notice and deterministic fallback; never modify wiring to fit a picture. Preserve unknown/unsupported original file separately and refuse lossy save rather than dropping data.

Outer digest binds exact package and layout under existing canonical JSON rules. It is a checksum, not proof/author identity. Layout-only edits change outer visual checksum/dirty state, never embedded execution/revision hashes, proof scope or replay result. Reopen new envelope via explicit version-aware CLI/API/web dispatch; old consumers reject it. Explicit extraction/downgrade produces unchanged 1.1 with discardedFields warning. Learning progress stays outside proof/package by default.

### Diagnostic adapter

Validate exact `projectHash`, `executionHash`, diagnostic engine and operation generation before overlaying. Use existing `Connection.side/path/connectionRef/instanceId/projectPin/inputPin/outputPin` and netlist hash. Match project edges only when canonical locator agrees; repeated/nested REF paths get distinct read-only scope. Compiler-generated output-copy NANDs appear as compiler-derived detail, not a fabricated editable edge. Unmapped/truncated findings remain in the table. Preserve 50-row paging and backend trace budgets.

Overlay states are orthogonal: selected; draft-valid/invalid; reference-only/candidate-only changed; witness-relevant; unobserved/unsupported. A geometry highlight is never a proof claim. Expected/actual bit values come from real mapped witness/vector output; current backend does not expose arbitrary internal per-wire values, so show “not observed” there until a reviewed API exists. No client computation or guessed signal propagation.

Corrections require current bound candidate action, explicit trusted local prior and fresh verification/apply checks. A deliberate mutation captures exact original request, displays before/after mappings and changes no reference silently. Restore original is one semantic command; later unrelated edits require explicit replacement/conflict review. Reverification must run afterward. UNKNOWN never yields success; relevant paths never mean uniquely proven root cause.
