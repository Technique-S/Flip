# Semantic blocker dispositions (SB-1 … SB-10)

| ID | Original decision needed | Disposition | Implementation evidence | Test evidence |
|---|---|---|---|---|
| SB-1 | Command envelope and validation authority | **RESOLVED** | `commands.ts:4-127` closed command types, own-key check, copied request; `useCandidateEditor.ts:141-212` compose validation; Python `POST /api/v1/compose` remains sole authority (`HANDOFF:23`) | `visual-edit.spec.ts:63,148` |
| SB-2 | Undo/redo boundaries | **RESOLVED** | `commands.ts:128-183` full-request snapshots, 100-transaction/4 MiB eviction, divergent `future=[]`; session-only history (`HANDOFF:39`) | `visual-edit.spec.ts:174,278` |
| SB-3 | Visual edit limits vs canonical graph limits | **PARTIALLY RESOLVED** | `commands.ts:11-27` inherits baseline `App.tsx` `pins * width > 65000` and `nIn/outputs > 255`; canonical `Candidate` still allows 5000 components. Effective ceiling ~178 NANDs; handoff records the boundary but not the formula (`HANDOFF:70`) | `visual-edit.spec.ts:155`, probes 178 ACCEPT / 179 REJECT |
| SB-4 | referenceCandidate, inputMap, outputMap preservation | **RESOLVED** within authorized scope | `commands.ts:63-126` mutates only candidate components; `useCandidateEditor.ts:346-363` configuration path refuses candidate changes; output remap intentionally excluded (`HANDOFF:20,37`) | `visual-edit.spec.ts:63,215,474` |
| SB-5 | Result invalidation and draft/commit binding | **RESOLVED** | `App.tsx` `invalidate()` archives proof to `pastEvidence`, clears table/built/proof/obs; `useCandidateEditor.ts:160-210` generation token and abort; commit only after successful compose | `visual-edit.spec.ts:362,424` |
| SB-6 | Draft persistence | **RESOLVED** | `flip-edit-draft` / `flip-edit-checkpoint` session keys; reload revalidates draft against exact base with real compose (`useCandidateEditor.ts:316-345`); reset clears keys (`App.tsx` reset handler) | `visual-edit.spec.ts:332,566,641` |
| SB-7 | Keyboard and focus behavior | **RESOLVED** | Native buttons/labels/selects (`NandControls.tsx`), focus refs and status region (`useCandidateEditor.ts:54-65`, `NandControls.tsx:13-34`); no global Ctrl/Cmd-Z interception | `visual-edit.spec.ts:498,673,708`; axe in `visual-readonly.spec.ts:259` |
| SB-8 | Network and compiler authorization | **RESOLVED** | Only `api("compose", next, abort.signal)` at `useCandidateEditor.ts:181`; no fetch/wallet/URL in new source; no backend or dependency change | `visual-edit.spec.ts:215` network recorder; `visual-edit.spec.ts:362` |
| SB-9 | Read-only enforcement on unsupported structures | **RESOLVED** | Only AddNand/RemoveNand commands; `removalProblem` rejects REF by actual kind; React Flow still non-draggable/non-connectable; no LATCH authoring, REF rebinding or decoded expansion | `visual-edit.spec.ts:113,148`, `visual-readonly.spec.ts:156` |
| SB-10 | Historical-evidence overlay binding | **RESOLVED** | `App.tsx` `pastEvidence` stores request + proof + revision, rendered under "Historical comparisons — not current verification"; no current verdict after edit/undo; export disabled without fresh proof | `visual-edit.spec.ts:424` (real EQUIVALENT → edit → undo → historical, no current heading, export disabled) |

## Unresolved / partial

- **SB-3** remains PARTIALLY RESOLVED: the inherited rule is real and enforced, but the handoff does not state the formula or its ~178-component ceiling. This is finding V2A-F1 (MEDIUM), not a merge blocker for an inherited budget; document it and surface the exact reason.
- No merge-decisive semantic blocker remains OPEN. Therefore the "do not approve with unresolved merge-decisive blockers" rule is satisfied.
