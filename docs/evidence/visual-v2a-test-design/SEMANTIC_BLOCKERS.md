# Semantic blockers — decisions V2-A must settle before cases become executable

These are unresolved specifications, not defects in the test package. Each case lists the blockers that prevent it from being turned into a passing production regression test.

| ID | Unresolved decision | Cases affected | Why it blocks acceptance |
|---|---|---|---|
| SB-1 | Command envelope: operation names, payload fields, `generation`, `requestHash`, draft identifier, and commit response shape. | 01A–D, 02A–C, 03A–C, 04A–B, 05A–C, 06A–B, 10A–E, 12A/C, 14A–D | Without a published contract, test command names are provisional adapters. A test could pass against a different API than the one shipped. |
| SB-2 | Undo/redo depth, branch truncation, session scope and whether history survives reload. | 03A, 04A–C | Exact byte-parity and stale-redo expectations depend on defined history semantics. |
| SB-3 | Visual edit limits: whether 500 components / 1,000 connections / 4,096 pins are editing limits or display-only budgets; how positions are bounded. | 11A–D, 15B | Canonical `Candidate` allows 5,000 components and 65,536 pins; silently applying either limit changes meaning. |
| SB-4 | Update rules for `referenceCandidate`, `comparison.inputMap` and `outputMap` after a candidate edit. | 02C, 03B, 06D, 07E, 11D | Local reference designs require equal `nIn` and output count plus complete bijections; without a rule, edits can produce an invalid project or silently alter reference identity. |
| SB-5 | Result invalidation and draft/commit binding: which hashes bind a build or proof to a revision, and when a result becomes historical. | 01D, 04C, 05C, 09A–C, 12A–C | Stale evidence as current is a release-integrity failure; the binding contract must be explicit. |
| SB-6 | Draft persistence across Visual↔Advanced switching, reload and cancellation; presentation-only position handling. | 06B, 08A–C, 12B, 13B, 15B | Without a persistence rule, the same edit can appear committed in one view and draft in another. |
| SB-7 | Keyboard equivalents, focus return, Escape ordering, text-field exemptions and status announcements. | 13A–C | Library keyboard support alone does not establish Flip's editing workflow; exact equivalents must be specified. |
| SB-8 | Network boundary: which client-side validation is allowed and the exact point at which compile/verify may be called. | 05A, 08C, 14A–D | An unintended compile or arbitrary URL would create a second execution path or data exfiltration surface. |
| SB-9 | Read-only enforcement for unsupported structures: REF internals, decoded LATCH, stateful sources and HTML/event strings. | 04D, 06C, 07A–E, 12D, 15A/C/D | V2-A is NAND-only; without explicit denial semantics, unsupported edits may silently mutate trusted data. |
| SB-10 | Evidence-overlay binding fields and whether a historical proof may be displayed after undo/restore. | 03B, 04C, 09A–C | A proof shown as current for the wrong revision is a false verification claim. |

## Resolving a blocker

A blocker is resolved only when an approved V2-A design document states the rule precisely, the corresponding fixture expectations are updated, and Codex publishes the implementation head that realizes it. Independent review must then re-check the case against that exact head. Verbal assurances, UI labels, or passing smoke tests do not resolve a blocker.

## Consequence if left unresolved

- SB-1/SB-5/SB-10 can produce false current evidence or silent state overwrite — **semantic blockers for merge**.
- SB-3/SB-4 can change canonical meaning or produce invalid projects — **semantic blockers for merge**.
- SB-2/SB-6/SB-7/SB-8/SB-9 affect correctness, accessibility and security of the editing workflow; each must be resolved before V2-A functional acceptance.
