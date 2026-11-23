# Capability gap matrix

Baseline and evidence IDs: [EVIDENCE.md](EVIDENCE.md). VERIFIED means the stated bounded requirement has callable code, tests and observed execution; PARTIAL means only a subset; MISSING means no implementation found after tracing routes, commands and UI; BLOCKED means a named prerequisite prevents completion/assessment; NOT TESTED means execution evidence is unavailable. Overall status does not replace subrequirement status. P1 here is the new capability ID, not the old architecture's optional stateful priority tier.

| Capability | Overall | Evidence-backed gap / dependency |
|---|---|---|
| P1 dual workflows | VERIFIED | Bounded local human/agent parity; authorized lifecycle remains separate P3/P4. |
| P2 library | VERIFIED | Bounded factory-backed discovery/catalog/import; no global completeness or new live observation claim. |
| P3 authorized tape-out | BLOCKED | Preview/approval/submit/status/receipt/recovery absent; separate authority project. |
| P4 safe agent execution | PARTIAL | Local execution/denial guards verified; transaction approval/spend/payload controls absent. |
| P5 portable format | VERIFIED | Accepted semantic interchange; visual transport extension is outstanding P7 work. |
| P6 debugging | VERIFIED | Bounded stateless witness/path/correction; canvas and stateful expansion are outstanding P7 work. |
| P7 visual composer/canary | PARTIAL | Numeric editor/backend prerequisites exist; fourteen functions and seven named journeys assessed below/ACCEPTANCE. |
| P8 two-track guide | PARTIAL | Sample and recovery primitives exist; dedicated guide/modules/progress absent. |
| UX-01 contextual explanations | MISSING | Systematic contextual term help/glossary. |
| UX-02 anchored walkthroughs | MISSING | Real-action step controller, anchors and progress. |
| UX-03 recovery lessons | MISSING | Nine safe failure lessons with all five explanatory parts. |

## P1 — Dual human/agent workflows: VERIFIED within accepted local scope

| Requirement | Status | Exact evidence / remaining gap |
|---|---|---|
| Human web and structured CLI/API call one core | VERIFIED | E01, E02; `workflow.product`, `verification.execute`, `App.tsx`, `flip_cli.main.main`; browser/CLI replay and adapter parity tests. No TS proof engine. |
| Bounded declarative discovery/build/test/compare/debug/correct/export loop | VERIFIED | E03; `agent_workflow.execute`, `agent_portable_adapter.execute`; combined 15-stage journey and exact-pin rejection tests. Current audit Python/browser outcomes are separately recorded. |
| Explicit selection of separate revision, cancel and ignore late results | VERIFIED | E03; `AgentPortable.tsx`, hosted by `Portable.tsx`; `agent-portable.spec.ts` both named tests; adapter cancellation tests. |
| Agent-accessible documentation/skill and sensitive-operation gate | VERIFIED | `docs/agents/WORKFLOW_INTEGRATION.md`, `.agents/skills/flip-agent-workflow/SKILL.md`, versioned agent schemas; STOP_AUTHORIZATION tested terminally. No granted transaction authority is claimed. |
| Agent-driven authorized deployment / arbitrary repository build sandbox | MISSING | Outside P1's accepted local scope; P3/P4 remain incomplete. Complete operation sets in `agent_models.py` and `agent_operations.py`; publication stops terminally. Solver containment is not an arbitrary-code build sandbox. |

## P2 — Circuit and processor library: VERIFIED (bounded local catalog scope)

| Requirement | Status | Exact evidence / remaining gap |
|---|---|---|
| Factory-backed bounded discovery and circuit pages | VERIFIED | E04; `library.LibraryService`, `library_protocol.py`; `test_research_enumeration`, `test_C04_pages_large_ranges_and_dedup`; historical accepted live-smoke record is separately dated. |
| Search metadata, aliases, favorites, recents, persistence/recovery | VERIFIED | E04; `library.search`, `Library.tsx`; `test_alias_and_favorite_metadata_are_both_searchable`, library acceptance browser cases LC01/LC02. |
| Imported bytes/closure re-read before executable use; user metadata grants no authority | VERIFIED | E04; `test_saved_current_claim_rejected_and_unregistered_import_always_fresh`, `test_C12_metadata_rejects_authority_and_removes_controls`; UI import excludes stateful sources. |
| Complete global index or guaranteed current RPC contents | NOT TESTED | Not claimed by bounded discovery. This audit made no new live-chain observation. No uptime/index completeness claim. |

## P3 — Authorized tape-out lifecycle: BLOCKED

| Requirement | Status | Exact evidence / remaining gap |
|---|---|---|
| Processor selection | VERIFIED | E04/E09; library selection/import and Sources processor input exist; selection is not transaction authority. |
| Deterministic netlist and read-only structural pre-flight | VERIFIED | E01, E05; `composition.compile_project`, `preflight.preflight`, `StructuralReader.probe`; M4 pre-flight transport and historical burn-stage cases. |
| Real-sender resources and reliable total quote | MISSING | `preflight.py` uses a synthetic caller/fee override in `eth_call`; gate count/current fee are not total cost, gas or owned-resource validation. |
| Exact transaction preview, expiring human authorization, signer/custody broker | MISSING | No reachable implementation in CLI/API operation lists or RPC allowlist. Proposed authority branch is not accepted main. |
| Broadcast, pending/replacement journal, confirmation/reorg recovery and minted-ID receipt | MISSING | No write RPC method; STOP_AUTHORIZATION is terminal. No real publication trial exists. |
| Authority/scope change and live acceptance | BLOCKED | Requires separate architecture, protocol and owner decisions; implementation expressly excluded from this audit. Hashes and proof do not authorize spending. |

## P4 — Safe agent execution: PARTIAL

| Requirement | Status | Exact evidence / remaining gap |
|---|---|---|
| Strict bounded operations, pin/closure verification, cancellation, no prompt/code execution | VERIFIED | E03, E06; `agent_workflow.py`, `agent_portable_adapter.py`; injection, forged-engine, late-result and budget tests. |
| Loopback opt-in, origin/Host guard, 1 MiB and two-slot admission; isolated native worker | VERIFIED | E06; API `MAX_BODY_BYTES`, `_slots`, `local.application`, `isolation.run_worker`; accepted worker timeout/crash/memory tests. Windows private commit and Linux virtual address space differ. |
| Human authority cannot be self-issued by agent metadata | VERIFIED | E03; `test_publication_stop_is_terminal_no_revision_or_later_operation`; false signer/permission fields rejected. This is a denial boundary, not transaction authorization. |
| Network/chain verification and current credential safeguards | VERIFIED | E04/E06; integer chain 196, source/environment identity validation, trusted local RPC settings reject URL credentials, no signing keys accepted by operation contracts; repository credential scan is additional limited hygiene, not runtime custody. |
| Transaction payload inspection, human transaction approval and spending limits | MISSING | No transaction payload/approval/spend-reservation implementation; existing read-call inspection and STOP_AUTHORIZATION do not supply these controls. |
| Safe signing/spend reservations/nonce/custody recovery | MISSING | Depends on P3 authority architecture, not solved by current solver sandbox. |
| Public multi-tenant process-tree/aggregate containment and arbitrary code sandbox | NOT TESTED | Public hosting prohibited here. Local bounded process tests do not establish this property. |

## P5 — Portable project format: VERIFIED for stated semantic interchange

| Requirement | Status | Exact evidence / remaining gap |
|---|---|---|
| Exact execution request, named vectors, ancestry, evidence references and explicit downgrade | VERIFIED | E07; `portable.PortableProject`, `metadata_hash`, `create_package`, `portable_operation`; roundtrip, hash/ancestry attacks, downgrade and CLI/API tests. |
| Identities/manifests/wiring and simulation/verification settings | VERIFIED | E01/E07; exact embedded M3 request preserves sources/imports, candidate mappings, comparison relation/maps, limits and declared tests; no engine duplication. |
| Real replay, no evidence/freshness authority from checksums | VERIFIED | E07; `test_digest_valid_forged_equivalence_is_recomputed`, missing-evidence and stale tests; integrated browser-to-CLI replay. Native engine compatibility remains exact and platform-bound. |
| Layout and guide-progress fields in accepted Portable 1.1 | MISSING | `PortableProject` has no such fields; inherited `Contract` forbids extras. P7 requires a successor single-file envelope, preserving embedded 1.1 hashes. Progress remains separate learning data. |
| Cross-platform transport | VERIFIED | Accepted two-platform schema/canonical and integration records E02/E03/E07. Transport portability does not promise old native evidence will replay on a different engine build. |

## P6 — Circuit debugging: VERIFIED for bounded stateless requirements

| Requirement | Status | Exact evidence / remaining gap |
|---|---|---|
| Replayed witness → mapped output roots → nested relevant connections | VERIFIED | E08; `debugging.ConeTracer`, `execute`; nonidentity map, incomplete closure, altered witness and repeated REF-budget tests. |
| Explicit trusted prior-design proposal, new verification, separate apply/revert | VERIFIED | E08; `prior_action`, `Debugger.tsx`; selected-project invalidation and repeated correction browser tests. No unique faulty-wire claim. |
| Connection overlay on a circuit canvas and selection linkage | MISSING | `Debugger.tsx` renders a paged table (50 connections); no canvas library or graph adapter in accepted web sources/dependencies. |
| Stateful diagnostic/proof scope | MISSING | Diagnostic kinds are NAND/REF_INPUT/REF_OUTPUT/OUTPUT_MAP; current correction scope is exact stateless historical. Lower-level latch evaluation does not complete stateful debugging. |

## P7 — Visual composer and Visual Wiring Canary: PARTIAL

| Requirement | Status | Exact evidence / remaining gap |
|---|---|---|
| Numeric pin table editing, NAND and imported stateless REF | VERIFIED | E01/E09; `Composer.tsx` source selects/add/remove/output controls; `models.PinSource`, `Candidate`; 81-byte deterministic sample tests. |
| Visual nodes/edges, port connection editing, visual canary result | MISSING | No graph dependency or reachable canvas/editor implementation; sample SVG is an illustration. Existing canary is trusted backend functionality, not visual composer acceptance. |
| LATCH placement/wiring and stateful composition | MISSING | `models.Component` only NAND/REF; `compile_project` rejects `state_width`. `tap02.decode` and official-vector evaluation support latch bytes at a lower level only. |
| General undo/redo, persistence and advanced-editor synchronization | MISSING | Debugger has a single correction revert bound to unchanged execution, lost on refresh; no general command history or raw JSON editor. Numeric table is the current advanced editing surface. |
| Visual performance, keyboard/touch and manual screen-reader acceptance | NOT TESTED | No visual implementation to execute; budgets and checks in P7/ACCEPTANCE are proposed. |

## P8 — Two-track interactive guide: PARTIAL

| Requirement | Status | Exact evidence / remaining gap |
|---|---|---|
| Real sample, table, swap/restore, compare, recovery and evidence actions | VERIFIED | E09; App/Composer/Comparison/Debugger/Portable real controls; existing automated sample journey is observed application behavior. |
| Experienced track and seven beginner modules | MISSING | No curriculum model, track selection or module completion controller in source/routes. README, static recorded showcase and sample hint are not an interactive curriculum. |
| Contextual glossary/help and stable anchored walkthrough | MISSING | No glossary/tour/anchor registry. Existing accessible names are a basis, not stable tutorial anchors. |
| Durable learning progress and completed guided-project evidence | MISSING | Session storage retains executable drafts/packages, not learning checkpoints. Existing test projects are machine journey evidence, not completed learner sessions. |
| UX-01 contextual explanations | MISSING | Inline scope notes exist, but no systematic contextual explanations/glossary for the required processor/REF/NAND/LATCH/SAT/netlist/pin/dependency/counterexample/evidence terms. |
| UX-02 interactive application walkthroughs | MISSING | No step controller, stable anchor registry, next/back/exit or durable walkthrough progress; real sample controls are only prerequisites. |
| UX-03 error and recovery lessons | MISSING | Error handling exists, but no nine-category educational exercises explaining failure, cause, work protection, recovery and prevention. |
| Novice usability, auditory screen-reader and curriculum completion outcomes | NOT TESTED | Human trials remain absent in accepted/release records. Future acceptance must retain actual session outcomes and projects. |
