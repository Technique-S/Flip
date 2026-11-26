# Visual composer architecture checkpoint

Date: 2026-11-23 (Africa/Lagos). **Research and proposed contracts only. Await explicit authorization for stage V1; no implementation is started.**

Accepted main: `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`. Parent research/audit: `6427b1b291f67151cc62ba413dc607e40be2af72`, retained unchanged. This branch adds only `docs/planning/visual-architecture/**`; production, existing audit, fixtures, schemas and locks remain identical. No open PRs were returned at admission. PR #11 is merged; accepted runtime remains unchanged from b537eb6. Its static historical showcase does not satisfy interactive P7/P8.

The requested `docs/milestones/FLIP_PRE_M5_MILESTONE_UPDATE.md` does not exist on main or at the supplied local location. The authoritative update supplied in the preceding task is the exact-byte [TXT snapshot](../pre-m5/requirements/FLIP_PRE_M5_MILESTONE_UPDATE.txt), SHA-256 `f1f5629cf3323be909e067eda34a1108d4f5e35d7aa26fb975b2ee3715085c95`. No alternative requirements were invented. The new directive is preserved in [source](source/directive.txt).

## Deliverables

- [Independent research, interaction comparison and technology decision matrix](RESEARCH.md).
- [Proposed ADRs and canonical adapter contract](ADAPTER_AND_ADRS.md).
- [Editor layout, interactions, Wiring Canary and learning integration](UX_SPEC.md).
- [Dependencies, threat assessment, stages, tests and exact ownership](DELIVERY.md).
- [Baseline code inspection, checksum manifest and actual checks](BASELINE.md).

## Recommendation

Use controlled React Flow rendering behind a versioned adapter, with Flip's existing Python contracts/compiler/evaluator/verifier as sole execution authority. Keep the existing numeric advanced editor. Begin with **V1: read-only sample projection**, with no semantic editing, new backend endpoint, project-schema change or new proof behavior. Subsequent small reviewed PRs add REF inspection, transactional edits/history, visual Canary, versioned visual portability, then the complete guide.

Reuse the existing white/ink/cobalt identity and surrounding workflow navigation. Add a composition-local toolbar, palette, canvas, inspector and diagnostics dock progressively. Use one-bit numeric handles rather than inventing bus semantics. Read-only decoded structures can represent LATCH; executable latch authoring and stateful verification remain separately versioned unresolved scope.

The new normal/stress benchmark targets are **100 nodes/200 edges** and **500 nodes/1,000 edges**. They supersede the earlier audit's provisional 200/400 planning profile for this checkpoint; neither is an approved production limit. Optional auto-layout is deferred. No Pro example source, competitor assets, second engine, wallet, signing, broadcasting, spending, deployment or public solver hosting.

P1/P2/P5/P6 remain verified within bounded accepted scope; P3 BLOCKED, P4 PARTIAL, P7/P8 PARTIAL, UX-01/02/03 MISSING. See the unchanged [capability matrix](../pre-m5/CAPABILITY_MATRIX.md) and [full curriculum](../pre-m5/P8_CURRICULUM.md). This checkpoint fills research/contract detail; it does not promote those statuses.
