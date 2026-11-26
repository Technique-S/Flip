# Canonical and history attacks — independent

Harness: `canonical-attack-harness.mjs` with real bundled `commands.ts` from PR head. Results: `canonical-attack-results.json` (26 probes). All outcomes matched expectation; 0 unexpected accepts/rejections.

## Adversarial command probes

| Attack | Outcome | Boundary that fired |
|---|---|---|
| Duplicate NAND instance ID | REJECT | `Component ID already exists.` |
| Unsupported LATCH/REF kind via AddNand | REJECT | `Unsupported edit command` / `unsupported component kind` |
| Missing second input | REJECT | `Choose exactly two explicit NAND input sources.` |
| Boolean, negative, fractional, 65536 pin | REJECT | `Input must identify an existing external or preceding output pin.` |
| True forward reference (`future`) | REJECT | same available-pin check |
| Unknown source component | REJECT | same |
| JSON-parsed `__proto__` / URL extra field | REJECT | `Unexpected edit command fields.` |
| Bad Name (leading digit, 65 chars) | REJECT | canonical Name pattern |
| Insert/set-output/AddRef commands | REJECT | unsupported edit command (out of authorized scope) |
| Remove REF component | REJECT | `Select an existing NAND component. REF removal is unavailable here.` |
| Remove output-referenced NAND (`carry`) | REJECT | exact locator `project.candidate.outputs[0]` |
| Remove downstream-referenced NAND | REJECT | exact locator `project.candidate.components[4].inputs[0]` |
| Remove unreferenced NAND | ACCEPT | restored request byte-identical to original |
| 1 MiB request limit | REJECT | `Project exceeds the 1 MiB interactive request limit.` |

**Invariant:** no rejected command changed the last accepted candidate or any trusted identity. `proposeNand` clones the request and only returns a proposal; the hook commits only after a successful authoritative compose response.

## Budget probes

| Components | Outcome |
|---|---|
| 178 NANDs | ACCEPT (unchanged baseline interactive budget) |
| 179 NANDs | REJECT with explicit interactive-budget message |
| 499 NANDs | REJECT before materialising a partial graph |

The formula `pins * width > 65000` is byte-identical to accepted main `App.tsx`; the canonical schema still permits up to 5000 components. This is finding V2A-F1 (documentation, not regression).

## History probes

- Two adds → two undos → exact original request bytes; two redos → exact final bytes.
- Divergent edit after undo → redo raises `Nothing to redo`; stale future cannot resurrect an obsolete edit.
- Rejected edits do not consume history (pure `commitHistory` is only called after successful proposal).
- Bounded to 100 entries / 4 MiB with visible eviction (`commands.ts:142-155`).
- Project replacement calls `editor.open()` creating a new session; execution-setup changes reset history but preserve the saved checkpoint (`useCandidateEditor.ts:346-363`).

## No client-side authority substitution

Client checks (closed keys, Name, pin existence, removal dependencies, budgets, display guards) only prevent wasted work. Every commit calls `POST /api/v1/compose` and requires success before `App.replace()`. Compiler-generated output-copy NANDs, netlist bytes and hashes come from Python. No JS compiler, evaluator, SAT, REF resolver or canonical hashing was added; `requestKey` is explicitly `JSON.stringify`, labeled "not a canonical hash" (`commands.ts:9`).
