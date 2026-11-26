# Coverage matrix — 15 focus areas / 56 prospective cases

All cases are `PROSPECTIVE_ACCEPTANCE`. `expectedCanonicalState` is either `UNCHANGED` (byte-identical to case input) or an exact candidate object; edited hashes must come from trusted compose.

| # | Focus area | Case IDs | Expected outcome(s) | Canonical invariant pinned | Evidence freshness rule | Regression pointer |
|---|---|---|---|---|---|---|
| 1 | Invalid or incomplete NAND creation | V2A-01A/B/C/D | REJECT/REJECT/REJECT/ACCEPT | NAND exactly 2 pins; Name syntax; valid append order | D accepted edit invalidates prior result; no current verdict | `tests/visual-edit.spec.ts::V2A-01*` |
| 2 | Removal of referenced components | V2A-02A/B/C | REJECT/REJECT/ACCEPT | No undefined/forward pin; one driver per output; atomic rewire | No partial deletion; preserved last valid package | `::V2A-02*` |
| 3 | Index shifts and reference corruption | V2A-03A/B/C | REJECT/ACCEPT/REJECT | Deterministic component order; no silent renumber; explicit rewire only | New request hash; old proof historical | `::V2A-03*` |
| 4 | Undo/redo state divergence | V2A-04A/B/C/D | ACCEPT/REJECT/ACCEPT/REJECT | Exact byte parity after redo; branch truncation; no stale resurrection; unsupported REF read-only | Restored proof historical only; never current without fresh verify | `::V2A-04*` |
| 5 | Rapid and repeated edit commands | V2A-05A/B/C | ACCEPT/REJECT/REJECT | Deterministic final state; duplicate ID rejection; generation binding | No hidden compile during burst; late response cannot overwrite newer revision | `::V2A-05*` |
| 6 | Canonical data mutation and hidden aliasing | V2A-06A/B/C/D | REJECT×4 | Extra fields forbidden; detached display copies; sources/imports/reference not editable | Request byte-identical; no hash change | `::V2A-06*` |
| 7 | REF identity corruption | V2A-07A–E | REJECT×5 | Alias existence, nState=0, exact arity, uint64 ID, manifest identity | No partial graph for malformed input; unsupported edits unavailable | `::V2A-07*` |
| 8 | Visual/Advanced state differences | V2A-08A/B/C | ACCEPT×3 | Stored request identical across modes; projection mirrors canonical exactly; stable-identity selection | No hidden compile or request on mode switch | `::V2A-08*` |
| 9 | Stale evidence shown as current | V2A-09A/B/C | ACCEPT/REJECT/REJECT | Proof binding to exact post-edit request/project hash | EQUIVALENT/DIFFERENT heading forbidden for stale binding | `::V2A-09*` |
| 10 | Invalid command parameters | V2A-10A–E | REJECT×5 | generation/requestHash binding; integer in-range pins; backward refs; known command kind | Zero network and zero state change on rejection | `::V2A-10*` |
| 11 | Maximum component limits | V2A-11A/B/C/D | ACCEPT/REJECT/REJECT/ACCEPT | 500 display components; nIn ≤512; outputMap bijection | Fail before partial materialization; no truncation | `::V2A-11*` |
| 12 | Dirty state and draft/commit confusion | V2A-12A/B/C/D | REJECT/ACCEPT/REJECT/REJECT | Incomplete draft non-executable; cancel restores bytes; commit only on matching response | Build/export disabled for drafts; last valid retained | `::V2A-12*` |
| 13 | Keyboard-only interaction | V2A-13A/B/C | ACCEPT×3 | Keyboard add/connect produces same canonical bytes as mouse; Delete ignored in text fields; status announcements | Focus return; no mouse-only step | `::V2A-13*` |
| 14 | Unexpected network requests | V2A-14A–D | ACCEPT/ACCEPT/REJECT/REJECT | Zero calls during edits; exactly one compose on explicit build; no arbitrary URL | Compile/verify only via existing loopback API | `::V2A-14*` |
| 15 | Bypass read-only protections on unsupported structures | V2A-15A–D | REJECT/ACCEPT/REJECT/REJECT | LATCH authoring denied; positions presentation-only; REF delete denied; HTML escaped | No new request, no execution, no semantic hash change | `::V2A-15*` |

## Cross-cutting assertions (every case)

1. Input request bytes before and after the case are exactly as specified (`UNCHANGED`) or exactly equal to the expected candidate with all non-candidate fields untouched.
2. `project.sources`, `imports`, manifest hashes, processor/circuit identities, comparison inputMap/outputMap (except V2A-11D), limits and projectId remain byte-identical unless the case explicitly says otherwise.
3. No accepted case introduces a semantic proof claim; verification is always a separate explicit action.
4. A rejected case never leaves a partial graph, new request, new hash, or network request.
5. Expected hashes for edited candidates are computed through the existing Python compose path, never asserted from this package.

## Genuine-vector grounding

Every case derives from `docs/schema/m3/examples/half-adder.request.json` (SHA-256 `04f95a33102af…`), a genuine accepted-main M3 request whose unedited parity capture and hashes are recorded in `baseline-vectors.json`. No synthetic circuit engine, fabricated netlist, or invented proof verdict is used.
