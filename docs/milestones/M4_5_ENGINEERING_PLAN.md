# M4.5 engineering plan for the six-capability pre-M5 gate

Planning date 2026-11-19. Baseline **09f2482beae84be6d919ecd6957c4153d1924cca**. Companion [gap audit](PRE_M5_CAPABILITY_GAP_AUDIT.md). These are proposed implementation assignments. This audit delivers documentation only.

## Priority and dependency order

| Order | Milestone | Capabilities | Dependencies | Exit artifact |
|---|---|---|---|---|
| P0 / 1 | M4.5-0 authority and architecture decision | 1, 3, 4 | Product owner and security review | Approved versioned scope, threat model, signer custody and approval protocol |
| P0 / 2 | M4.5-1 portable project and agent loop | 1, 5 | Schema/version decisions from M4.5-0 | Versioned project package, CLI/web round-trip and agent workflow guide |
| P1 / 3a | M4.5-2L circuit library | 2 | Read-only ABI verification and M4.5-1 identities | Discovery/import index, search, metadata and local user collections |
| P1 / 3b | M4.5-2D witness diagnostics | 6 | M4.5-1 test and diagnostic contracts | Signal-to-connection trace and explicitly applied repair workflow |
| P0 / 4 | M4.5-3 sender-bound quote and preview | 3, 4 | M4.5-0, M4.5-1, current contract verification | Read-only exact-byte transaction preview with capped cost/resource quote |
| P0 / 5 | M4.5-4A authorization broker and recovery journal | 1, 3, 4 | M4.5-3 | Enforced human approval, durable nonce/spend reservations, mock submission/recovery |
| P0 / 6 | M4.5-4B external signer and submission adapter | 3, 4 | Independent review of M4.5-4A | Explicitly authorized local adapter, tested with controlled chain/signing doubles |
| P0 / 7 | M4.5-5 live lifecycle acceptance and six-capability decision | All six | Every earlier exit gate | Separately approved live receipt and final six-capability acceptance record |

Codex owns core/interfaces and integration. An independent reviewer must inspect new authority, signing and receipt paths before activation. M4.5-2L and M4.5-2D can be reviewed as separate changes after the portable format is stable. Transaction orchestration must not borrow unreviewed catalog metadata as authority.

## M4.5-0 — Approve the architectural scope

Deliver a successor ADR and versioned requirements amendment that explicitly changes the original read-only boundary for the authorized lifecycle. Retain the historical MVP constraints and architecture. Adopt or revise the audit's threat model, approval sequence, capability separation and durable state transitions.

Resolve the supported signer/account model, human identity/approval surface, sender and target policy, exact spend caps, allowed operation, nonce management, cancellation/replacement semantics, finality criteria and limits on RPC trust. Define who may approve a public software deployment separately from a transaction. Record an explicit decision for remaining UNKNOWN verification/estimate cases.

Acceptance is documentary and manual security review. The human-controlled broker must own the final authority decision. A model's proposal, CLI flag or imported project cannot grant that authority. Exit requires approval of the specific architecture rather than a generic instruction to make tape-out work.

## M4.5-1 — Portable specification and agent build/test/verify loop

Add a new package version with full source identities, netlist bytes, manifests, candidate/reference definitions, explicit maps, named user tests, expected behavior/intent declarations, tool/semantics requirements, revision references and evidence digests. Export formal schemas for the new envelopes and generate frontend types from them. Keep old readers and original hash semantics.

Add a documented agent task contract binding input package hash, allowed operations, resource budgets, validation/test commands and stop conditions. The loop should validate, compose, run declared tests, compare, inspect the witness, propose edits and rerun. New revision and evidence hashes must be emitted for each accepted edit. Approval remains external. The existing repo's lint/build/CI commands remain usable by coding agents.

Automated acceptance must show web save -> CLI validate/build/test/verify/export -> web re-import with all supported fields preserved, including user tests and metadata. Check unsupported versions, stale source closures, malformed input, intentional migration, canonical parity and both native engine identities. Define the common web/CLI interchange profile and the larger CLI profile. Legacy import must report absent fields, and downgrade must fail or explicitly report loss. Cross-platform fresh reproduction must retain its own engine identity.

Manual acceptance must let a developer and a coding agent independently complete the same workflow from documented inputs. No live transaction is needed for this milestone.

## M4.5-2L — Discoverable circuit and processor library

First establish the current deployed factory enumeration/event ABI, processor registration semantics, circuit ID gaps and upgrade/reorg behavior with a read-only protocol investigation. Record verified source/ABI/code provenance. Avoid inventing enumeration selectors from historical mentions.

Then implement bounded discovery and a block-aware local catalog. Include address/ID and interface search, provenance-labeled names/descriptions/tags, favorites and recent imports. Use chain/processor/circuit identity plus block/environment digests as appropriate keys. Favorites can survive a code upgrade while the executable snapshot is marked stale. Untrusted labels must be escaped and cannot affect permissions.

Automated acceptance uses a paginated factory/RPC double, missing IDs, multiple processors, reorgs, upgrades, unavailable endpoints, bounded indexing, storage quotas and schema migration. Every selected discovered entry must pass the existing trusted importer before composition. Search/favorite/recent behavior must run in the real UI and CLI where specified.

A live read-only acceptance separately verifies current factory discovery and a sample of selected entries. It must record endpoint trust assumptions, chain ID, block/hash and code identities. A verified address is not permanent proof of an unchanged implementation.

## M4.5-2D — Connection-level diagnostics

Extend the evaluator/composer with bounded optional trace data and a stable map from emitted signals to project components and numbered pins. For each differing output, expose the replayed input, baseline/expected and actual values, mismatched bit indices and the implicated signal cone. Distinguish a declared vector expectation from an undeclared behavioral reference.

Offer actionable connection inspections and explicit candidate edits. Any suggested repair must be applied deliberately and evaluated against the full declared suite and comparator. Keep the existing verdict logic authoritative and show uncertain/ambiguous causes clearly. Preserve manual pin editing and the current sample walkthrough.

Automated acceptance covers REF nesting, glue gates, constants, output permutations, repeated fanout, ambiguous causes, zero-input circuits and trace resource ceilings. Assert that tracing cannot change verdicts or consume authority. A repaired sample must progress from reproduced DIFFERENT to a completed comparison. Manual usability acceptance must use an unfamiliar mutation and include keyboard and auditory screen-reader review.

## M4.5-3 — Read-only quote and transaction preview

Implement preparation against an explicitly chosen real sender, target processor and candidate digest. Revalidate the current network, target, implementation/dependency context, fee, native balance and resource requirements. Investigate real gas accounting and token burn behavior with the current ABI. Introduce only the specific additional read calls required, through a dedicated bounded adapter.

Expose fee, gas estimate and maximum gas-price/gas-quantity/native-value caps, token contract/ID/burn quantity, resource sufficiency, observation block/hash, estimate confidence and expiry. Total-spend arithmetic must use bounded integers/decimal strings. Unknown/full-simulation failures must have explicit policy outcomes. Retain structural pre-flight as a separate observation.

Build an immutable exact calldata preview and independently decode it for display, including sender, chain 196, target, function, netlist digest, widths and resources. The future approval broker consumes this artifact. This milestone can be completed without a signer or broadcast path.

Automated acceptance covers malformed ABI, wrong chain/account, provider disagreement, fee changes, insufficient resources, unsupported estimate calls, gas overflow, stale dependencies and preview tampering. A live read-only session must separately establish that the quote describes the chosen current deployment and real account. The old synthetic insufficient-balance revert cannot substitute for that evidence.

## M4.5-4A — Enforced permission, budget and recovery protocol

Implement the reviewed broker and durable journal with transaction/signing doubles only. A human approves one immutable preview with an unpredictable request ID, expiry and exact caps. The agent can request an approval and inspect its outcome, but cannot create a human grant. Revalidate before authority is consumed.

Atomically reserve sender/chain/nonce and native/token budgets across concurrent jobs. Persist consumed/revoked approvals, signed-transaction identity, pending spend and state transitions. Prevent duplicate authorization after crash or application restart. Replacement/cancellation rules must be explicit and separately approved where payloads change. Reconcile ambiguous submission before attempting another transaction.

Automated adversarial tests must cover forged/cross-session approvals, double-clicks, metadata prompt injection, mutated target/data/value, expired grants, nonce races, aggregate pending spend, same-nonce replacements, RPC timeout after accepted submission, reorg and crash at every persistence boundary. No failed authorization may reach the signer double. Budget policy must account for gas on reverted transactions.

Manual acceptance must demonstrate a refusal, an expiry, a revocation and a changed-preview reapproval using the trusted approval surface. Independent security review is the exit gate before M4.5-4B.

## M4.5-4B — Local external signing and transaction reconciliation

Only after the reviewed approval boundary exists, add the chosen human-controlled external signer adapter and an allowlisted tape-out submission adapter. Keep keys and wallet secrets outside agent/core/API storage. Independently compare signed transaction fields with the approved preview and chain-bound payload. Never export active grants or unbroadcast signed payloads inside a portable circuit project.

Implement receipt-status tracking, replaced/dropped/reorged transaction states, confirmation policy and circuit receipt verification. Use verified contract events or another reviewed authoritative result to identify the published circuit, then re-import and compare its complete netlist/interface/dependency context with the approved artifact. A global nextId increment alone is insufficient under concurrency.

Automated acceptance must use a controlled EVM/RPC/signing environment and exercise success, revert, replacement, ambiguous submission, restart, reorg, mismatched receipt/event, wrong processor, wrong circuit bytes and signer rejection. Retain all baseline solver, proof, origin/Host and input-limit checks. Key handling and any infrastructure secrets require an explicit review. Public untrusted signer or solver hosting is outside this local milestone.

No live funds are spent by passing the automated gate. A live write acceptance remains an explicit separate human decision.

## M4.5-5 — Separate live acceptance and M5 readiness

Prepare a concrete immutable proposal for one X Layer mainnet tape-out containing account, chain 196, target, exact circuit bytes/calldata, project/evidence digests, maximum native and token spend, fee/gas caps, request expiry and confirmation policy. Identify any resource acquisition as a separately authorized action. Obtain the human approval through the reviewed mechanism.

Execute only the approved operation. Preserve the actual transaction hash, inclusion/confirmation block, fee/resource expenditure, receipt/event data and re-imported circuit identity/content. A rejected wallet request, revert, unknown submission or mismatched receipt must be reported accurately. Do not fabricate a successful lifecycle from a fixture.

M5 admission requires all six capability rows to reach COMPLETE for their explicitly accepted profiles, evidence of the human and agent journeys, migration and diagnostics acceptance, manual accessibility results and independent review of authority/recovery. Remaining limitations must be listed individually. The existing public-solver deployment restriction continues until its separate deployment-specific isolation/authentication/aggregate-resource tests pass.

## Implementation review and regression rules

Each milestone should be a bounded PR with exact code/test/artifact provenance and a reviewable completion checklist. Keep the frozen schemas, independent review files and historical evidence immutable. New schemas require additive versioning and migration fixtures. No corpus expectation may be relabeled to turn an unexecuted live action into a pass.

Use the merged M4 suite as the regression baseline of 514 Python and 11 Chromium tests. New regression tests should target the behavior introduced by each milestone. Require Windows/Linux CI, schema drift, Python/Node canonical parity, frontend lint/build, credential scans and existing worker lifecycle/containment checks. Do not relax proof replay, native solver timeouts or resource controls to enable the broader workflow.

## Scope of this audit delivery

Only this plan and PRE_M5_CAPABILITY_GAP_AUDIT.md are intended tracked changes. All implementation milestones are future work. The user has authorized assessment and planning, with no signer or broadcasting implementation in this branch.
