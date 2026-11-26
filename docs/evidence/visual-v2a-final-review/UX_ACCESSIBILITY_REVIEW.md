# UX and accessibility review — independent

Evidence: 72/72 workbench browser tests executed locally and on both hosted OSes; screenshots from the final results bundle (`docs/ux/visual-v2-a/focus-fix/screenshots.json` and `docs/ux/visual-v2-a/results/screenshots.json`) were not independently inspected as raw images in this review, so visual claims below are limited to executed assertions and hashes.

## Executed behaviors

| Behavior | Evidence |
|---|---|
| Add NAND with explicit source selects; controls start empty; exact compile/commit | `visual-edit.spec.ts:215`, `:498` |
| Remove unreferenced NAND after confirmation; restore exact original request | `:304` |
| Block referenced removal with exact locators | `:113`, `:304` |
| Visual/Advanced share one candidate and stored request | `:215`, `:474` |
| Accessible labels and status region (`role="status"`, `role="alert"`, `aria-describedby`) | `NandControls.tsx:45-208`, `App.tsx` edit-status, axe in `visual-readonly.spec.ts:259` |
| Keyboard-only add, source selection, selection and confirmed removal | `:498` |
| Focus after add (inspector/selector), after removal, after cancel, invalid submit focuses first incomplete field | `:498`, `:673`, `:708` |
| No global Ctrl/Cmd-Z interception in text fields | `NandControls`/`useCandidateEditor` code inspection; `:498` |
| Escape/cancel and invalid-draft visibility | `:332`, `:362` |
| Narrow 390px / 320px, reduced motion, no document overflow | V1 `visual-readonly.spec.ts:259`; focus-fix regression for disabled fieldsets |
| No drag-connect/reconnect; Delete/Backspace do not edit | `visual-readonly.spec.ts:156` |
| Native form semantics (form/select/button/label, no custom role soup) | `NandControls.tsx` |
| StrictMode / repeated mode transitions stable | V1 tests `:156`, `:259`; V2-A tests `:215`, `:474` |

## Focus-race correction

The first final-head CI run (`45896495418` at `e92ae1e…`) failed on Ubuntu at `workflow.spec.ts:92` due to an inherited Advanced focus race; Windows was cancelled by fail-fast. Final head keeps Advanced rows non-focusable until validation commits, avoids stealing focus on ordinary Advanced commits, and adds two deterministic regressions (`:673`, `:708`). The original inherited assertion is unchanged. Final-head CI is green on both OSes at `036c7a9…`.

## Not tested

- Real screen-reader speech/verbosity (NVDA, JAWS, VoiceOver).
- Physical touch-device gestures and pinch/scroll interactions.
- 200% / 400% browser zoom and forced-colors/high-contrast mode.
- Manual visual inspection of the captured PNGs in this review session (hashes and source paths are recorded in the evidence bundle).

These are V7/human-acceptance items and are explicitly **NOT TESTED**, not passes.

## Usability note

The interactive budget rejects the 179th NAND with "Use the CLI for larger designs" while the native compiler accepts 4990; the discrepancy is documented but not explained in the error. Finding V2A-F1 (MEDIUM) requests exact documentation of the inherited limit and reason.
