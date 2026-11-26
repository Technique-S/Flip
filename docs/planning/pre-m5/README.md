# Pre-M5 expansion audit: P1–P8

Assessment: 2026-11-23, Africa/Lagos. **Audit and planning only; the expanded pre-M5 gate is not satisfied.**

Accepted main after PR #11 merged during the audit: **`7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`**. Admission main was `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`; runtime, web and schema paths are identical between them. This branch was advanced to the new accepted main and adds documentation only. Production, contracts, tests, locks, accepted fixtures and custody policy are unchanged.

Read in order:

1. [Baseline, sources and execution evidence](EVIDENCE.md).
2. [P1–P8 capability gap matrix](CAPABILITY_MATRIX.md).
3. [P7 architecture and staged plan](P7_ARCHITECTURE.md).
4. [P8 curriculum and UX architecture](P8_CURRICULUM.md).
5. [P7/P8 acceptance matrix](ACCEPTANCE.md).
6. [Dependencies, risk, scope and separate assignments](HANDOFF.md).

## Decision

P1, P2, P5 and P6 are VERIFIED within the update's bounded local requirements, supported by accepted execution records and targeted audit reruns. P4 is PARTIAL: execution and denial boundaries work, while spending/transaction approval controls do not exist. P3 is BLOCKED: preparation and read-only structural pre-flight exist; authorized publication does not. P7 is PARTIAL: a numeric table composer and trusted debugger exist, but visual composition, visual diagnosis, general history and LATCH composition do not. P8 is PARTIAL: the sample and recovery controls exist; two interactive tracks, seven beginner modules, anchored help and durable learning progress do not. UX-01, UX-02 and UX-03 are each MISSING as dedicated contextual-help, walkthrough and recovery-lesson systems.

**Requirements authority:** the user supplied `C:\Users\Kazi\Documents\Flip\repo\docs\milestones\FLIP_PRE_M5_MILESTONE_UPDATE.txt` during the audit. An exact-byte [snapshot](requirements/FLIP_PRE_M5_MILESTONE_UPDATE.txt) is included, SHA-256 `f1f5629cf3323be909e067eda34a1108d4f5e35d7aa26fb975b2ee3715085c95`. It supplies all P1–P8, fourteen P7 functions, both tracks, seven module names and UX-01/02/03 wording. The initial missing-source uncertainty is resolved. The older local six-capability audit is historical context only.

Recommended first implementation milestone: **M4.6-A, stateless visual mapping contract and parity slice**. Freeze graph-to-canonical mapping, a new single-file visual package version preserving embedded Portable 1.1, invalidation/history semantics and stable guide anchors; then implement the smallest real NAND/REF sample → compare → diagnose → save/reopen vertical slice. LATCH representation remains a mandatory P7 dependency; its executable authoring/trace scope needs an explicit decision and a stateless slice does not complete P7. No second circuit engine, wallet, signing, broadcast or public native solver.

PR #11 was OPEN at admission and merged externally at `2026-11-23T12:07:20Z`, merge/main SHA above, final head `5adf0c9edfc65526741848eaffba673947176853`. Its recorded static showcase is now accepted-main behavior but cannot count as an interactive guide or visual editor. See EVIDENCE.md for exact checks and outstanding release gates. This audit performed no merge or release.
