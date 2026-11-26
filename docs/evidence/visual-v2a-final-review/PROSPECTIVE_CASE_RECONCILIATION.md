# Prospective 56-case reconciliation

Source: `opencode/flip-visual-v2a-test-design` / `b671893b58d11011bacefafddcd356fc1224dc56` (unmodified).
Machine-readable: `case-reconciliation.json` (raw harness output), `case-reconciliation-final.json` (reconciled with governing sources).

**Final distribution: PASS 30 · CONTRACT_MISMATCH 22 · NOT_EXECUTED 4 · FAIL 0.**

## Method

1. Each case's genuine half-adder input was reconstructed from `input.base` + `input.patch`.
2. Its `editSequence` was adapted to the published private command layer (`AddNand`, `RemoveNand`, history moves). Only the *execution adapter* changed; original case files remain byte-identical on their branch.
3. The real bundled `proposeNand`, `openHistory`, `commitHistory`, `moveHistory` and `checkInteractiveBudget` from PR head were executed in Node for command-layer cases.
4. Browser-only behaviors (mode switch, proof creation, keyboard, focus, network, draft cancel) were reconciled against the executed 72-case workbench suite, not guessed.
5. Where the original premise conflicts with the approved contract, the case was classified `CONTRACT_MISMATCH` with an explicit governing source. No original case was rewritten to make it pass.

## Outcome by focus area

| Focus | Cases | Final classes |
|---|---|---|
| 1 Invalid/incomplete NAND | 01A–D | 4 PASS |
| 2 Removal of referenced components | 02A–C | 2 PASS, 1 CONTRACT_MISMATCH (output remap out of scope) |
| 3 Index shifts/reference corruption | 03A–C | 3 CONTRACT_MISMATCH (insert/output-remap commands not authorized) |
| 4 Undo/redo divergence | 04A–D | 3 PASS, 1 NOT_EXECUTED (BUILD is a browser action) |
| 5 Rapid/repeated commands | 05A–C | 2 PASS, 1 NOT_EXECUTED (generation binding is hook-owned, browser-tested) |
| 6 Canonical mutation/aliasing | 06A–D | 4 CONTRACT_MISMATCH (no such commands; read-only by absence; JSON extras reject) |
| 7 REF identity corruption | 07A–E | 4 PASS, 1 CONTRACT_MISMATCH (malformed patched input outside edit authority) |
| 8 Visual/Advanced differences | 08A–C | 3 PASS via real browser tests |
| 9 Stale evidence as current | 09A–C | 2 PASS, 1 NOT_EXECUTED (direct proof injection not browser-tested) |
| 10 Invalid command parameters | 10A–E | 5 CONTRACT_MISMATCH (enforced by hook/validator; equivalent malformed cases executed) |
| 11 Maximum component limits | 11A–D | 2 PASS, 2 CONTRACT_MISMATCH (interactive nIn=255; ~178-NAND inherited budget) |
| 12 Dirty/draft/commit confusion | 12A–D | 1 PASS, 1 NOT_EXECUTED, 2 CONTRACT_MISMATCH |
| 13 Keyboard-only interaction | 13A–C | 3 PASS via browser suite |
| 14 Unexpected network requests | 14A–D | 3 PASS, 1 CONTRACT_MISMATCH (URL field outside command contract; validator probe rejects) |
| 15 Read-only bypass on unsupported | 15A–D | 2 PASS, 2 CONTRACT_MISMATCH (UI events, not commands; read-only by absence) |

## Key reinterpretations (governing sources)

- **Output remap/insert/REF-authoring cases (02C, 03A/B/C, 06D, 07E, 12D):** `P7_V2_A_HANDOFF.md:20,93` and `P7_V2_A_DESIGN_CHECKPOINT.md:26,111` explicitly exclude output remapping, cascade repair, REF authoring and LATCH. Their original ACCEPT assumptions are superseded by the approved scope, not by a product defect.
- **Generation/requestHash cases (05C, 10A/B, 12C):** `HANDOFF:31` places generation, abort and stale-response rejection in the hook. Executed by `visual-edit.spec.ts:362,566`. The private command has no such fields.
- **Budget cases (11A/C):** `HANDOFF:70` records the unchanged interactive table budget; baseline `App.tsx` uses `pins * width > 65000` and `nIn > 255`. Effective ceiling is ~178 NANDs, not the 500 display components of the V1 projection. CONTRACT_MISMATCH, not a canonical regression.
- **Malformed patched input cases (07D, 11C):** V2-A starts from an accepted composed request. Identity/width validation belongs to Python/canonical validation; the editor never accepts arbitrary input as a command premise.
- **`__proto__` case (06A):** the `proposeNand` closed-key check inspects own keys; a JS object-literal `__proto__` sets a prototype rather than an own key, so the pure probe accepted it. Direct probe with a JSON-parsed `__proto__` own key is REJECTED (`Unexpected edit command fields`) and no canonical object was mutated. Classified CONTRACT_MISMATCH with a LOW finding rather than a security bypass.

## Executed evidence pointers

- `canonical-attack-results.json` — 26 direct command-layer probes.
- `.test-tmp/m4-browser.json` (from the fresh local run) and `docs/ux/visual-v2-a/focus-fix/browser-final-72.json` — 72 browser cases.
- `visual-edit.spec.ts:63,113,148,155,174,215,278,304,332,362,424,474,498,546,566,641,673,708` — mapping of executed cases to each reinterpretation.

Generated fixtures are **not** counted as passing production tests; they remain prospective design artifacts.
