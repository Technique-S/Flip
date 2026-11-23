# P8 curriculum and UX architecture

Normative source: [exact milestone update](requirements/FLIP_PRE_M5_MILESTONE_UPDATE.txt), sections 4–5. This plan preserves its two tracks and seven named modules. Dedicated User Guide, contextual help, anchored walkthroughs and recovery lessons are **not implemented**. Existing executable sample journeys provide integration evidence, not proof of learner completion.

## Actual control inventory

All paths below are in accepted main `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`. Symbols/labels are inspected source; four production browser journeys were rerun (E10 in EVIDENCE). Controls are conditional on an open project, page, trust choice and prior response. Tutorial authors must check these conditions.

| Workflow | Actual controls and source | Availability / guide implication |
|---|---|---|
| Navigate | `App.tsx:21` pages: Sources, Composition, Wiring Canary, Evidence, Circuit Library; workflow nav at :440 | These are the current page names. No dedicated User Guide route yet. |
| Start/open/recover | `App.tsx:538` Open sample; :591 Open project file; :465 reset/confirm; session restoration :161–205 | Start from sample or a real saved project. There is no UI “New blank circuit” wizard; use the update's permitted known-sample route. Never reset unsaved work from a tutorial. |
| Discover/import | `Library.tsx:294` Discover processors; :307 Browse saved processors; search/filter :327–353; :502 Browse circuits; :537 Revalidate; :546 Import into composition | Imports re-read and validate. Stateful imports cannot be composed here; discovery data is not proof. App Sources also has processor/circuit inputs and actual inspection/import controls. |
| Edit/build | `Composer.tsx:92–227` External inputs, numeric Source-for-target selects, Component, Add component, Remove last component, Final outputs, Add output, Remove last output, Build netlist | Current advanced surface is the numeric table. No embedded raw-netlist editor or drag canvas. Visual steps must wait for P7. |
| Inspect composition | `Composer.tsx:251` Netlist built; expandable TAP-02 bytes and manifest | Compiler result is real; no signal animation or simulation state inferred from node color. |
| Sample simulation/fault | `App.tsx:631–671` Swap outputs, Restore original, Half-adder truth table, Evaluate four inputs | Swap/restore only appear for the sample; restore replaces current candidate with original, so teach project-copy protection first. Four-input evaluator is fixed sample behavior. |
| Other test inputs | `Portable.tsx:104` Import named test sets; :178 Run named tests | Named vector JSON import exists. There is no general interactive bit-toggle simulation console. Beginner test-input UI is a gap if JSON files prove unsuitable; implement it before teaching it. |
| Verify | `Comparison.tsx:132–247` reference selection, relation, trust assertion, mapping disclosure, limits, Run comparison | Trust is explicit. Test vectors are not formal equivalence. Changes invalidate proof. |
| Debug/correct | `Debugger.tsx:144` Inspect connection paths; :238 Relevant connection paths; :314 proposal radio; :355 Verify proposed revision; :369 Apply candidate locally; :170 revert control | Proposal requires compatible declared trusted prior design. Not guaranteed for arbitrary circuits. Do not instruct every user to click a button that may not exist. |
| Export/replay | `App.tsx:736–804` evidence consent/export, Save project, Replay evidence file; `Portable.tsx:90` Save complete portable project and explicit legacy downgrade | A saved project is not proof; replay must use selected project/engine. Teach separate evidence artifacts and missing-evidence recovery. |
| Agent loop | `AgentPortable.tsx`; `agent-portable.spec.ts:58–175` actual labels: Propose and verify correction, Continue to correction when declared tests differ, Download verified revision, Download workflow receipt, Open verified revision | Optional experienced lesson; action/response assertions already exist. Opening returned revision is explicit. |
| Sensitive operations | `AgentPortable.tsx` Request publication handoff; structural pre-flight in App :810 | Handoff stops at STOP_AUTHORIZATION. Pre-flight is structural only. No deployment/confirmation walkthrough exists. |

Screenshot policy: capture from actual accepted implementation with page state, source SHA, viewport, input project hash and freshness caption. Use annotations that point to actual controls. Screenshots/recorded showcase are supporting explanation only; do not count them as an executed learner action. Re-capture after relevant control changes. No fabricated product screen, fake wallet or simulated success toast.

## Path A — Experienced Circuit/TapeOut Developers

Concise task cards with annotated screenshots and direct navigation; skip circuit theory. Suggested 15–25 minute target is an estimate, not measured completion time.

| Required topic | Short task and actual success signal |
|---|---|
| 1 Navigation | Visit five existing pages; return to original workspace without altering request. |
| 2 Starting/opening | Open sample or uploaded project; await trusted compose/open validation. Save original before edits. |
| 3 Discovery | Discover processors, search/filter, inspect metadata and its block/trust label. Handle outage with saved historical view. |
| 4 Importing | Select registered circuit, revalidate/import; only advance after import accepted into project sources. |
| 5 Visual/advanced composition | Numeric table now; visual adapter after P7. Switch views with identical semantic hash; no duplicate recipe. |
| 6 Pin mapping | Change explicit numeric input/output mapping, inspect width and source identity, build. |
| 7 Simulation | Run sample four vectors or import/run named tests. Inspect real expected/observed rows and declared coverage. |
| 8 Verification | Select reference/relation/trust, run comparison; read verdict, historical scope and limits from response. |
| 9 Debugging | Introduce reversible sample fault, replay witness, inspect relevant connections; verify correction then explicitly apply/recompare. |
| 10 Evidence | Export actual artifact and complete project; retain original revision and content identities. |
| 11 Replay | Reopen independently selected saved project, replay artifact through trusted core/CLI; show actual engine-bound outcome. |
| 12 Optional deployment | Explain current STOP_AUTHORIZATION/structural-only boundary. No actionable deployment lesson unless a future separately authorized implementation is accepted. |

## Path B — Complete Beginners

Each module offers a short explanation, actual visual aid, safe action, confirmation and resumable checkpoint. Conceptual visuals explain real semantics but never pretend to execute a circuit. Terms include all topics from the source, not just the half-adder vocabulary.

| Module (normative title) | Curriculum and practical exercise | Completion evidence / dependency |
|---|---|---|
| 1 — Understanding the ecosystem | X Layer, TapeOut, processor versus circuit, transistor tokens, why developers use circuits, Flip's role. Show chain 196 identity and historical-vs-current observation. Explain tokens as protocol resources without offering acquisition or spending. | Learner correctly identifies processor/circuit/chain on real source card. Chain/token explanations need primary protocol-source review; no current fee or economics claim copied from old reports. |
| 2 — Understanding components | Binary logic, gates/NAND, LATCH state, REF reuse, circuit I/O, pins/connections, bit ordering/width, netlists, combinational versus stateful. Use actual decoded sample structure and numeric labels; latch conceptual/real imported read-only inspection until supported authoring. | Read sample input/output widths and interpret `tap02-lsb0-v1`. Explain why a stateless proof cannot cover stateful behavior. P7 required for interactive graph exercises; no fake latch simulation. |
| 3 — Creating the first project | Open sample (allowed route), save as learner copy, discover/import existing circuit, inspect real structure/I/O and provenance. Explain project versus reusable circuit identity. | Saved working request/package reopens through trusted validator with same semantic hash. Real-circuit visualization waits for P7; no invented blank-project button. |
| 4 — Visual composition and wiring | Add supported components, position them, connect pins, inspect flow, validate, modify and save reusable composition. Numeric table is available as equivalent access. | P7 dependency: actual drag/tap/keyboard connections compile to expected canonical result; portable export/reopen preserves positions and wiring. Module remains blocked until P7. |
| 5 — Simulation and debugging | Supply sample inputs/named vectors, run actual evaluator, interpret expected/observed bits, deliberately swap outputs on a protected copy, inspect replayed counterexample and implicated paths, restore/correct and rerun. | Four-row results plus real DIFFERENT witness, verified correction and rerun. Existing file import is real; a friendlier vector-entry UI, if needed, must be built/tested first. Visual diagnostics wait for P7. |
| 6 — Verification and evidence | Simulation versus formal proof, reference/trust, EQUIVALENT/DIFFERENT/UNKNOWN, state/time/memory limits, evidence bundles, identity/hashes, export and independent replay. | Actual response-bound proof scope and downloaded artifact; reject forged/missing/stale claims. Teach cross-engine compatibility failure as recovery, not successful replay. |
| 7 — Complete guided project | **Create/import → Compose → Wire → Simulate → Debug → Verify → Export Evidence → Replay Evidence** using known historical half-adder/prior-reference project. Every stage invokes real application/core operations. | Full artifact set and trace described below, including correction and independent replay. No completion badge based merely on Next/click/visible component. |

Do not require irreversible exercises. Concept checks can test understanding, but cannot replace actual project/evidence tasks. Module 7 may begin with a known sample as explicitly permitted in the source; a new blank-project workflow is not a prerequisite.

## UX-01 — Contextual explanations

Introduce a versioned glossary catalog with stable term IDs: processor, circuit, REF, NAND, LATCH, SAT, netlist, pin, bit/width/order, circuit dependency, counterexample, reference, evidence bundle, freshness and structural pre-flight. Place help next to current source metadata, pin inspector, comparison results and evidence controls. A short definition plus “why it matters here” and link to the relevant module stays available without leaving the workflow.

Use labeled Help buttons and expandable text/popovers; keyboard activation, Escape, focus return and screen-reader descriptions are required. Essential safety/scope text stays inline and is not hidden behind hover. Touch works without hover. Reuse term content between guide and contextual help, not execution logic. Do not interpret user aliases as verified semantics or define EQUIVALENT as intended correctness.

## UX-02 — Anchored walkthrough controller

Proposed step record: `guideVersion`, track, moduleId, stepId, existing route, anchorId, precondition, user instruction, expected application event predicate, recovery step, next/back edges. React controller observes the shared edit/operation state; its actions navigate or highlight only. Domain commands remain those used by the app.

Add stable semantic `data-guide-anchor` attributes to Codex-owned controls; do not anchor to translated text, array indexes, CSS coordinates or duplicate-label selectors. Resolve a single visible enabled target after real route/render, within a bounded wait (propose 3 s for render only; operation deadlines remain unchanged). Missing/changed target pauses with an explanation and safe skip/exit; it never clicks a guessed replacement. On unmounted targets, screen changes, zoom and resize, re-resolve or switch to a docked instruction panel.

Next, Back and Exit are always reachable. Exit returns focus to launch control and retains workspace. Back revisits instruction, not an automatic undo. A coachmark must not trap focus away from the required action; use a nonmodal panel for interactive steps. Screen-reader users receive concise instructions and a direct focus-target control. Reduced motion avoids moving spotlight animation. Do not overlay critical warnings.

Completion predicates use matching request/operation/revision identity and actual validated result: import committed, compose bytes returned, vectors observed, witness replayed, correction verified/applied explicitly, export artifact created, replay accepted. A click, successful HTTP transport, checksum validation, downloaded filename or cached badge is insufficient. UNKNOWN routes to recovery; no forced success. Cancelling or editing invalidates pending predicates. Walkthroughs cannot grant consent, select trust, execute correction, approve spending or bypass API/native opt-in on behalf of the user.

## Progress preservation

Store a small versioned local learning record separately from execution/proof: track, guide version, last module/step, observed checkpoint IDs, relevant project/request/revision hashes and timestamps; no raw witness/private project in learning storage. Proposed bound: 64 KiB. This is resume convenience, not proof authority. Offer reset/export of progress, handle storage denial/quota/corruption, preserve invalid bytes for explicit recovery, and explain when session-only fallback is used.

On reload, inspect the actual restored project/package before resuming. Changed project or guide versions require rechecking prerequisites; completed conceptual lessons may remain, but action checkpoints are invalidated if their identities differ. Saved progress never reinstates CURRENT/EQUIVALENT or correction permission. Cross-device completion requires explicit progress import and fresh artifact validation; cloud accounts/sync are deferred. Unsaved project data must be downloaded before closing; tutorial must not imply sessionStorage is durable backup.

## UX-03 — Error and recovery lessons

Each lesson includes the required five parts: **what failed; why; how Flip protected the work; recovery; prevention**. Exercises use a separate disposable project or validate-only request; user originals and accepted fixtures remain untouched. Network faults use a controlled loopback test environment for automation, not changing real user's RPC settings automatically.

| Required failure | Real safe exercise / cause | Protection, recovery and prevention |
|---|---|---|
| Invalid processor address | Enter malformed address in Sources; existing parser rejects it | Keep previous project; correct 20-byte address or use Library. Check chain and identity before import. |
| Nonexistent circuit ID | Bounded fixture processor with absent ID, or explanation from a real failed import | No successful import/project substitution; choose registered circuit via Browse circuits. Do not guess IDs or treat network error as nonexistence. |
| Incompatible pins | P7 invalid draft connects wrong direction/out-of-range target | Compilation blocked, last valid package retained; choose compatible numeric port. Inspect width/direction first. |
| Incorrect output mapping | Swap sample outputs on copy; actual DIFFERENT witness | Original saved; inspect mapped pins, restore/recompare. Check order/bijection rather than trusting semantic labels. |
| RPC connection failure | Controlled fixture refusal/outage | Saved historical catalog/project retained; retry configured connection or continue historical sample. Cached data is not CURRENT. |
| Solver timeout / UNKNOWN | Existing minimal-deadline comparison on a copy, or recorded real UNKNOWN with retry lesson | Never EQUIVALENT; retain project and reason code. Reduce supported problem size/retry unchanged valid operation within hard ceilings; no raising safeguards or hiding timeout. |
| Stale verification evidence | Controlled changed dependency / incompatible exact request replay | Reject/retain old historical artifact; revalidate, compare afresh and export a new artifact. Never relabel old proof current or bypass engine pin. |
| Malformed project file | Disposable invalid JSON/version/hash file via Open project file | Existing project retained on rejection; reopen last saved valid file or correct supported format. Keep backups; no silent partial sanitize/import. |
| Unsaved changes / recovery | Edit a learner copy, navigate, refresh with actual session restore; separately exercise denied storage | Data preservation is tested only where actually supported; proof/undo may be lost. Save complete project before closing; explain quota message, download and explicit reset confirmation. |

Avoid a “simulate successful failure recovery” overlay. Where an error cannot safely be induced on the production UI, show a clearly recorded explanation and mark the hands-on checkpoint unavailable until a real isolated lesson mode exists.

## Module 7 completed-project evidence contract

Retain a new learner project/revision, declared named test inputs/expected outputs, compiled canonical request/netlist hashes, original and faulty wiring, real DIFFERENT witness with independent replay status, diagnostic/correction identity, final comparison, evidence artifact, independently selected-project replay result and actual commands/engine/semantics/freshness. P7 visual package must preserve positions too. Keep original package immutable and final package separate. The guide completion record references these artifacts and matching observed events; it does not manufacture proof content.

Automated acceptance runs the entire chain in real browser plus independent CLI and saves artifacts under a **new** acceptance namespace. Human beginner acceptance records completion, assistance, errors and artifact outcomes; failed/abandoned sessions remain failures. Existing combined adapter browser test demonstrates underlying machinery, not this proposed curriculum. No beginner or auditory screen-reader completion was observed in this audit.

## Delivery sequence

1. Freeze term catalog, step/progress contracts and actual anchor inventory; contextual help can begin against accepted controls.
2. Deliver experienced path for existing flows and safe recovery lessons. Mark P7 lessons unavailable with accurate prerequisites.
3. After accepted P7, capture current screenshots and implement modules 2/4/5 graph actions and the complete module 7 walkthrough.
4. Run exact-head automated artifact-based acceptance and independent novice/screen-reader sessions. Refresh lesson mappings after any UI change.

Estimate: 1–2 focused days for contracts/help; 2–3 for controller/progress and existing-control track; 2–3 for seven-module content/actions; 1–2 for integration plus actual tester availability. These are planning estimates, not delivery guarantees. P3 optional-deployment content stays a boundary explanation until separately implemented and authorized.
