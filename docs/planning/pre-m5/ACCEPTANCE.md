# P7/P8 acceptance matrix

All proposed tests below are **NOT TESTED**, unless an existing prerequisite is explicitly identified. No audit production code or new product tests were added. Existing evidence IDs resolve in EVIDENCE.md. Codex owns integration assertions; OpenCode supplies independent expectations in disjoint new files after contracts freeze. Every final gate requires exact combined-head SHA, platform, command, full outcome and original artifact hashes. Never rewrite accepted fixtures or archived reports.

## P7 functional traceability

IDs F01–F14 follow the source update's numbered functional requirements, not invented completion claims.

| Requirement | Current status | Required acceptance / evidence |
|---|---|---|
| F01 node canvas | MISSING | Real canonical sample/import projection; node/edge identities map back to exact numeric recipe. |
| F02 drag/drop | MISSING | Add supported NAND/REF by drag and by keyboard/tap equivalent; no silent default connections; validate real compiled result. |
| F03 NAND/LATCH/REF representation | PARTIAL | Existing NAND/REF table; new actual decoded structure displays all three with numeric ports and state badge. Unsupported state authoring fails explicitly. Any executable LATCH support requires new schema/evaluator-bound tests, no stateless proof. |
| F04 clear I/O pins | PARTIAL | Current numeric table; canvas labels direction/index/width and reference identity; test >53-bit circuit IDs without JS truncation, zero-input source, multioutput REF and collapsed high-width banks. |
| F05 compatible connections | MISSING | Drag/tap/keyboard connect/reconnect; single driver per input, legal fan-out, invalid direction/width/cycle/missing import refused. |
| F06 signal-flow inspection | PARTIAL | Current canonical bytes/diagnostic table; visual path selection resolves exact side/path/hash, not invented runtime values. |
| F07 properties inspector | PARTIAL | Existing table controls; new selected component inspector edits same request, validates identity/arity, preserves oracle and import bindings. |
| F08 zoom/pan/layout | MISSING | Fit/reset and keyboard controls; layout-only interaction changes no semantic hash; narrow-screen fallback and touch cancellation. |
| F09 precompile connection validation | PARTIAL | Existing Python validators; visual invalid draft and targeted messages; tampered API request still rejected by same core. |
| F10 undo/redo/restore | PARTIAL | Existing bound correction revert only; test multi-edit history, drag coalescing, deletion/reconnect undo, redo truncation, byte budget and project switch. Restored wiring requires reverification. |
| F11 structural feedback | PARTIAL | Build errors exist; visual feedback before compile for feasible local constraints, no network/solver call per pointer move; stale errors clear only for matching draft. |
| F12 simulation/verification | PARTIAL | Existing trusted backend; visual request produces same vectors/verdict/witness as table/CLI. Timeouts stay UNKNOWN; stateful proof denied. |
| F13 same canonical export | PARTIAL | Existing compiler/table; opening/switching view produces identical request/netlist for accepted fixture. New topological order is explicit semantic revision, never hidden by hash normalization. |
| F14 visual metadata in portable files | MISSING | New versioned single-file envelope preserves entire 1.1 package plus layout; web→CLI→web lossless roundtrip, old consumers reject new version, explicit downgrade reports visual loss. Unknown/tampered/stale layout cannot alter execution or authority. |

## P7 named acceptance journeys and Visual Wiring Canary

| Gate | Required operation and observable outcome | Existing prerequisite |
|---|---|---|
| P7-A1 real circuit | Import recorded genuine circuit bytes with identities/manifests and label HISTORICAL; graph reflects decoded supported structure. Separate opt-in fresh import records actual block if performed. A synthetic editor demo does not pass. | M2 genuine captures; E01/E04. New visualization NOT TESTED. |
| P7-A2 create/wire | Actual drag/connect composition and keyboard equivalent build through Python; compare to advanced table and CLI exact canonical bytes. | E01/E09. Canvas NOT TESTED. |
| P7-A3 deliberate reversible fault | Protect original; reverse output mapping/change selected edge; real compare yields DIFFERENT with independently replayed witness. Show expected/actual **for that witness** and linked affected/relevant paths. | E08/E10 underlying debugger. Visual overlay NOT TESTED. |
| P7-A4 counterexample/implicated pins | Correct mapped output roots, repeated nested REF paths, nonidentity maps, ambiguous causes; selection synchronizes diagram/table. Truncated/unmapped/compiler-added paths disclose limitations. | E08. No unique faulty-wire promotion. |
| P7-A5 restore/reverify | One-click original wiring restore on learner copy, undo compatible with subsequent edits, actual new EQUIVALENT selected-reference comparison. Correctness is not inferred from restoring array order or a green node. | Sample Restore original and debugger revert exist. New history NOT TESTED. |
| P7-A6 portable reopen | Single-file visual project reopens with same semantics, imports, tests, ancestry, evidence references and positions; replay verifies separately. | E07; layout/envelope NOT TESTED. |
| P7-A7 preserve functionality | Full unchanged accepted Python/browser suites, nine frozen schema exports, canonical and custody/credential gates on Windows/Linux, plus new schema tests; original fixture Git blobs unchanged. | Accepted E02/E03. New combined-head regression NOT TESTED. |
| P7-A8 resource/accessibility | Measure proposed P7 budgets, large-input bounded fallback; keyboard complete flow, reduced motion, axe, 320px/200% zoom, touch gesture/cancel; real auditory screen-reader session. | E10 old UI accessibility subset only. New canvas NOT TESTED. |
| P7-A9 state boundary | Decode/render actual latch netlist without EQUIVALENT; if versioned latch authoring enabled, verify state ordering/feedback/initialization with existing official sequential vectors and bounded trace semantics. | Existing latch vector evaluation/rejection E01; new behavior NOT TESTED. |

## P8 and UX acceptance

| Gate | Current status | Required acceptance evidence |
|---|---|---|
| P8-A1 dedicated two-track guide | MISSING | Accessible User Guide entry; choose/switch experienced or beginner path without workspace mutation; concise task cards versus progressive modules. |
| P8-A2 experienced topics 1–12 | MISSING | All source topics mapped to actual controls, screenshots pinned to release/viewport, deep navigation preserves project; optional deployment accurately says unavailable/STOP_AUTHORIZATION. |
| P8-A3 beginner modules 1–7 | MISSING | Every topic in P8_CURRICULUM taught; module predicates use real operations; unmet P7 dependency is shown honestly and does not complete lesson. |
| UX-01 contextual explanations | MISSING | All ten named example terms plus core width/order/reference/freshness terms available in workflow, keyboard/touch/screen-reader usable, no hover-only essential explanation, glossary links return focus. |
| UX-02 anchored real actions | MISSING | Steps target stable visible controls; Next/Back/Exit; missing/unmounted/renamed target safe pause; no guessed clicks. Changed project cancels stale predicates. Failed/UNKNOWN response cannot advance success. |
| UX-02 progress | MISSING | Resume across reload after validating actual workspace, independent track/version state; storage unavailable/quota/corrupt/migration tests; no proof rehydration from progress. |
| UX-03 recovery lessons | MISSING | Nine required categories; each explains failure, cause, protection, recovery, prevention; disposable copies preserve originals. Controlled outage/timeout and actual malformed files; no production settings silently changed. |
| P8-A4 full module 7 | MISSING | Real Create/import→Compose→Wire→Simulate→Debug→Verify→Export→Replay, final portable visual project plus evidence and independent CLI replay; original and fault retained; no fake completion. |
| P8-A5 human usability | NOT TESTED | At least one complete novice and one experienced developer perform their full paths without author impersonation; record assistance, failures and actual saved artifacts. This is minimum proposed evidence, not statistical validation. |
| P8-A6 assistive technology | NOT TESTED | Actual screen-reader spoken-output session and keyboard path, including coachmark/target changes and errors; retain tester/platform/version findings. Automated axe is separate evidence. |
| P8-A7 regressions/safety | NOT TESTED | No auto trust/consent/apply/publication; tutorial exit/back cannot erase unsaved project; public/native guard unchanged; exact-head full regression and custody check. |

## Remaining P1–P6 completion gates

| Outstanding requirement | Acceptance gate / owner |
|---|---|
| P3 real quote and payload preview | Separately scoped Codex authority project: current sender/resource/fee assumptions, exact immutable payload/cost bounds, independent protocol review; no implementation here. |
| P3/P4 approval, limits, no repeat spend | Separate broker design and negative tests for expired/revoked/changed/replayed grants, chain/account/nonce/payload mismatch, concurrent reservations and ambiguous broadcast; owner transaction authorization. |
| P3 submission/status/receipt/recovery | Separately authorized capped live lifecycle with real transaction/circuit ID, confirmations and reproducible receipts; timeout/reorg/replacement recovery. Mocks alone do not complete P3. |
| P4 credential and execution boundaries | Preserve current no-key/no-write allowlist and solver gates; future signer boundary independently reviewed, no credential in agent/project/guide data. |
| P5 visual extension under P7 | Versioned compatible transport and explicit downgrade; preserve existing 1.1 consumers/goldens. |
| P6 visualization under P7 | Preserve existing reliable correction contract and ambiguity semantics while rendering bound connections. |

P3/P4 remain mandatory pre-M5 gaps even if deferred from the constrained first implementation slice. Neither hackathon prioritization nor a visual guide may relabel them complete.
