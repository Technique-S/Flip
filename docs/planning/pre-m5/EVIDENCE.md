# Baseline, sources and execution evidence

## Exact baseline and provenance

Audit date: 2026-11-23, Africa/Lagos. Repository remote verified as `https://github.com/Technique-S/Flip.git`. Original checkout `C:\Users\Kazi\Documents\Flip\repo` was clean at admission on an older review branch; it was not reset or edited. A separate worktree was created at `C:\Users\Kazi\Documents\Flip\flip-pre-m5-expansion-audit`, branch `codex/flip-pre-m5-expansion-audit`.

1. `git fetch origin main` resolved admission main to **`b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`** (PR #10 accepted integration).
2. `gh pr view 11 --json state,headRefOid,mergedAt,mergeCommit,statusCheckRollup` initially observed OPEN, head `5adf0c9edfc65526741848eaffba673947176853`; Windows jobs were running. No PR action was taken by this audit.
3. PR #11 merged externally at **2026-11-23 12:07:20 UTC / 13:07:20 Africa/Lagos**. Re-fetch confirmed exact merge/main **`7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`**. Audit branch advanced to this main before committing documentation.
4. `git diff --exit-code b537eb6 origin/main -- packages apps/web docs/schema uv.lock pyproject.toml` returned exit 0. Runtime, frontend and all frozen contracts tested before that merge are identical in final accepted main. Showcase/release additions are audited separately, not credited as interactive product work.
5. User-supplied update source: `C:\Users\Kazi\Documents\Flip\repo\docs\milestones\FLIP_PRE_M5_MILESTONE_UPDATE.txt`. [Exact-byte snapshot](requirements/FLIP_PRE_M5_MILESTONE_UPDATE.txt), SHA-256 **`f1f5629cf3323be909e067eda34a1108d4f5e35d7aa26fb975b2ee3715085c95`**. The initial absence in accepted main was resolved by user location, not reconstructed from the old audit. Source remains untouched.

All production citations below resolve at final accepted SHA above; files identical at admission retain the same line references. GitHub source links are immutable commit links. Local exact symbols and tests provide additional lookup precision. Proposed architecture is explicitly separated from observed behavior.

## Sources read

- Root `AGENTS.md`, README, `docs/audits/M05/MVP_CONSTRAINTS.md`, product PRD, `docs/architecture/FLIP_SYSTEM_ARCHITECTURE.md`, `FLIP_TECHNICAL_DESIGN.md`, `FLIP_ARCHITECTURE_DECISIONS.md`, `FLIP_AGENT_OWNERSHIP_MATRIX.md`, `FLIP_IMPLEMENTATION_DEPENDENCIES.md`.
- Current Python contracts/models and their exported schemas: M1 1.0, M2/M3 1.0, library 1.0/1.1, debugger 1.0, agent workflow 1.0, Portable Project 1.1 and agent-portable 1.0. Strict models are authority; schema shape validity is not execution/proof validity.
- `docs/milestones/M1_ACCEPTANCE.md`, `M2_ACCEPTANCE.md`, `M3_ACCEPTANCE.md`, `M4_ACCEPTANCE.md`, `M45_LIBRARY_ACCEPTANCE.md`, `M45_LIBRARY_FOLLOWUPS.md`, `M45_DEBUGGING_ACCEPTANCE.md`, `M45_AGENT_WORKFLOW_ACCEPTANCE.md`, `M45_PORTABLE_PROJECT_HANDOFF.md`, `M45_AGENT_PORTABLE_POST_MERGE_ACCEPTANCE.md`, associated acceptance/case evidence indexes.
- Latest release `docs/release/M45_R2_RELEASE_BLOCKERS.md`, `M45_R3_ACCEPTANCE.md`, `M45_R3_MERGE.md`, independent review dispositions and PR #11 live merge/check record. Earlier pending-review text remains historical, not an unresolved override of the later merge record.
- All web source files and browser test names/critical journeys; CLI/API route/operation sets; composition, TAP-02 execution, comparison, library, portable, agent and debugging implementation and relevant tests.
- Historical local six-capability audit at `Flip_M1_Engineering_Starter/flip-pre-m5-audit/docs/milestones/PRE_M5_CAPABILITY_GAP_AUDIT.md` was consulted as historical context, not accepted current production evidence.
- Primary library documentation linked in P7_ARCHITECTURE. No assumptions about newest npm versions or event deadlines were used as acceptance evidence.

## Evidence index

### E01 — canonical engine and stateless boundary

Code: [models.py:186](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/models.py#L186) (`PinSource`, NAND/REF union, Candidate, ordered mapping validators); [composition.py:42](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/composition.py#L42) `compile_project`; [verification.py:135](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/verification.py#L135) `compare`; `execution.py::evaluate/beat`, `tap02.py::decode`.

Tests: `test_m3_engine.py::test_audited_81_bytes_100_builds_and_truth_table`, `test_canary_and_every_witness_replays`, `test_real_xor_nand_wrapper_and_stateful_rejection`, `test_official_valid_vectors`, `test_genuine_captured_wrapper_replays_sequential_primitive`, `test_full_request_python_node_hash_parity`. Executed in E10 focused Python rerun. Decoder/evaluator latch support is not composer/stateful proof support.

### E02 — accepted cross-interface baseline

Code: `packages/flip-cli/src/flip_cli/main.py:109::main`, `packages/flip-api/src/flip_api/app.py:161::m3_request`, `flip_core.workflow.product`, React `model.ts::api` and App orchestration.

Records: [M4 acceptance](../../milestones/M4_ACCEPTANCE.md), [post-merge integration](../../milestones/M45_AGENT_PORTABLE_POST_MERGE_ACCEPTANCE.md). The latter records **702 Python / 27 Chromium per platform** for accepted integrated scope. These are prior exact-head records, not this audit's fresh full-suite counts. Admission main CI [44773778968](https://github.com/Technique-S/Flip/actions/runs/44773778968) had both contracts jobs SUCCESS when queried. Final release head pre-merge matrices are described below.

### E03 — agent workflow and portable integration

Code: [agent_workflow.py:150](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/agent_workflow.py#L150) `execute`; [agent_portable_adapter.py:242](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/agent_portable_adapter.py#L242) `execute`; `agent_models.py`, `agent_operations.py`, `AgentPortable.tsx`, `.agents/skills/flip-agent-workflow/SKILL.md`, `docs/agents/WORKFLOW_INTEGRATION.md`.

Tests: `test_m45_agent_portable.py::test_combined_15_stage_journey_preserves_original_and_prior_evidence`, `test_publication_stop_is_terminal_no_revision_or_later_operation`, `test_exact_pins_required`, `test_cancellation_before_and_immediately_before_commit`, `test_rehashed_fake_engine_cannot_turn_integrity_into_proof`, CLI/API parity and immutable-original cases. Entire file rerun E10. `agent-portable.spec.ts:58` actual combined flow rerun E10. Accepted independent adapter review **26/26 including 10 attacks**, preserved in post-merge record; not a new independent review by this audit.

### E04 — library

Code: [library.py:130](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/library.py#L130) `LibraryService`, `search` at :79, `library_protocol.py`, `Library.tsx`. Tests: `test_m45_library.py` enumeration/pagination/reorg/provenance/recents/allowlist; focused `test_m45_library_acceptance.py` all three tests rerun E10. Browser library tests and accepted two-platform reconciliation are historical [library acceptance](../../milestones/M45_LIBRARY_ACCEPTANCE.md). No new live discovery call in this audit; saved observed snapshots remain historical. User-only metadata is not on-chain evidence.

### E05 — preparation is not authorized publication

Code: [preflight.py:39](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/preflight.py#L39) `StructuralReader`, `preflight` at :60; [rpc.py:16](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/rpc.py#L16) read allowlist. CLI/API complete dispatch lists have no signing/submission/transaction status/receipt operation. Synthetic caller and override are eth_call only. `test_m4_workflow.py::test_preflight_transport`, `test_unrecognized_burn_is_inconclusive`, M4 historical fixture are accepted earlier execution evidence, not rerun in this focused audit. P3 publication acceptance is absent.

### E06 — execution safety

Code: `app.py:21–22` body/slot limits, :191 native opt-in, :344 debug and :475 adapter local guards; `local.py::application`, `rpc.py::RpcClient.call/_read`, `isolation.py::run_worker` and worker modules. Tests: accepted `test_m4_workflow.py::test_public_or_disabled_native_rejected`, `test_local_service_transport_boundary`; E10 reran `test_m3_engine.py::test_timeout_crash_and_memory_containment`, `test_api_never_publicly_enables_native_solver` and all integrated adapter boundary tests. No signer or public-service safety claim.

### E07 — Portable 1.1

Code: [portable.py:77](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/portable.py#L77) `metadata_hash`, :94 `PortableProject`, :171 `create_package`, :252 `portable_operation`; [strict Contract](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/models.py#L59); [portable schema guide](../../schema/m45-portable-project/README.md). No layout/progress field. Entire `test_m45_portable.py` rerun E10, including named exact roundtrip, attacks, explicit downgrade, missing/tampered/forged/stale evidence and CLI/API legacy preservation. E10 integrated browser independently replays a new revision via CLI.

### E08 — diagnostics and safe correction

Code: [debugging.py:35](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/packages/flip-core/src/flip_core/debugging.py#L35) `ConeTracer`, :203 `prior_action`, :247 `execute`; `debugging_models.py::Connection/DebugResult/Correction`; `Debugger.tsx` renders table, bounded proposal and explicit verify/apply/revert. Entire `test_m45_debugging_adversarial.py` rerun E10. Browser `debugging.spec.ts:19` rerun E10 (real witness, correction, revert, CLI parity). Historical [debugger acceptance](../../milestones/M45_DEBUGGING_ACCEPTANCE.md) contains corpus/ambiguity and worker limitations; do not read its earlier pending-review footer as the latest integration state.

### E09 — UI prerequisites and absent expansion controls

Code: [Composer.tsx:92](https://github.com/Technique-S/Flip/blob/7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f/apps/web/src/Composer.tsx#L92) numeric wiring/add/remove/build, `App.tsx:21` five pages, :631 sample fault guide; `Comparison.tsx`, `Portable.tsx`, `AgentPortable.tsx`. `apps/web/package.json` has React/react-dom only as runtime dependencies. Full source/entry-point search and route/operation trace found no graph editor, general history controller, guide track/module model, glossary, anchor registry or learning progress. Sample SVG and static showcase cannot establish those capabilities. Actual controls are enumerated in P8_CURRICULUM.

## E10 — Fresh audit execution

Windows 11 build 26200, CPython **3.14.6**, Node **24.18.0**; reused existing repository `.venv` dependencies (pytest 9.0.1, Pydantic 2.12.4, python-sat 1.9.dev23, FastAPI 0.121.1). `uv` was unavailable on PATH and not installed into the existing environment. No clean native installation claim.

Each Python/browser command inherited explicit `PYTHONPATH` containing this audit worktree's `packages/flip-core/src`, `packages/flip-cli/src`, `packages/flip-api/src`. Imported module `__file__` paths were checked and resolve here. Ignored `.venv` is a directory junction to `C:\Users\Kazi\Documents\Flip\repo\.venv` so unchanged Playwright configuration can launch the native environment. No dependency installation/update was made in that shared environment. Browser subprocess CLI inherited the same source paths. Worktree had immutable b537eb6 runtime during tests; runtime paths are identical to final 7ecfb9b baseline.

| Command / observation | Actual result |
|---|---|
| `npm ci --prefix apps/web` | Exit 0, 17 packages added, zero reported vulnerabilities. Local locked frontend dependency install, not native/novice install acceptance. npm noted esbuild pending install-script approval; subsequent TypeScript/esbuild build succeeded without changing approval/config. |
| `npm run build --prefix apps/web` | Exit 0, TypeScript and esbuild build PASS. |
| `npm run lint --prefix apps/web` | Exit 0, 20 files checked, no fixes. |
| Python focused command below | **140 passed**, 255.11 s, zero failures/errors/skips. |
| Browser selected command below | **4 passed**, 1.6 minutes, zero skips/retries/flakes. Real loopback API/native engine and controlled RPC fixture, not live X Layer. |
| `node apps/showcase/build.mjs` / `--check` after baseline advance | Exit 0, 19 deterministic inert files. |
| `node scripts/check_m45_release_package.mjs` | Exit 0, 19 checksummed inert files, 130 links; no script/server/import/native/RPC/wallet/publication surface. |

```powershell
# From audit worktree; same PYTHONPATH also supplied to npm test.
$env:PYTHONPATH = "$PWD/packages/flip-core/src;$PWD/packages/flip-cli/src;$PWD/packages/flip-api/src"
& C:/Users/Kazi/Documents/Flip/repo/.venv/Scripts/python.exe -m pytest packages/flip-core/tests/test_m45_agent_portable.py packages/flip-core/tests/test_m45_library_acceptance.py packages/flip-core/tests/test_m45_debugging_adversarial.py packages/flip-core/tests/test_m45_portable.py packages/flip-core/tests/test_m3_engine.py -q --junitxml=.test-tmp/pre-m5-python.xml -o junit_family=legacy
npm test --prefix apps/web -- --grep 'B01|B03|debugger replays paths|combined named tests'
```

Original run outputs copied without editing to [Python JUnit](execution/python-junit.xml) and [browser JSON](execution/browser-results.json). They contain actual test IDs/durations and local paths. Browser screenshots remain ignored scratch attachments, not a new permanent curriculum screenshot set. Python and selected browser execution overlapped; all passed at unchanged resource limits. This is focused regression evidence, not a full new Windows/Linux audit suite.

Archived file SHA-256: JUnit `b9e9c4da3d59cc82c44946e5598b7db2477c20681a70c6ceb61870e17bb18c59` (29,976 bytes); browser JSON `9b217ce113c35a9fff79e4278d5a636274ef9637475177988c600177c6636f17` (7,585 bytes). Terminal pytest duration includes overhead; JUnit suite time is 253.384 s. Original report timestamps remain unchanged.

Browser test identities/outcomes:

- `acceptance.spec.ts:19` B01 keyboard-only complete export journey: passed, 9.0 s.
- `acceptance.spec.ts:67` B03 accessible labels/B05 responsive axe: passed, 19.6 s.
- `agent-portable.spec.ts:58` named tests/correction/new revision/CLI replay/authorization stop: passed, 41.9 s.
- `debugging.spec.ts:19` replay paths/verify/apply/revert/CLI parity: passed, 14.2 s.

No audit assertion failed. Earlier accepted host-sensitive failures and PR #11's initial fixture-placement failure remain documented in their original records; this audit did not rerun, rewrite or erase them. Visual/P8 performance, full curriculum, human novice/experienced and auditory screen-reader trials, current mainnet state and transaction lifecycle were **NOT TESTED**.

## PR #11 and remaining release work

Live [PR #11](https://github.com/Technique-S/Flip/pull/11) final head **`5adf0c9edfc65526741848eaffba673947176853`** merged as **`7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`**. Both Windows/Ubuntu jobs succeeded in exact-head [push 45169094258](https://github.com/Technique-S/Flip/actions/runs/45169094258) and [PR 45169101331](https://github.com/Technique-S/Flip/actions/runs/45169101331). Original independent reviews remain **CONDITIONAL PASS**, not rewritten as unconditional approval.

Release record: [M45_R3_MERGE.md](../../release/M45_R3_MERGE.md). F-01 checkout guidance resolved; F-02 documentation resolved by retaining an **unchecked** independent first-time setup gate; F-03 original R2 receipt/replay/project versus curated-copy provenance remains unavailable. Checksums establish retained bytes, not missing original provenance or CURRENT freshness. F03-PERF-001 and historical runner runtime limitations remain tracked, no relaxed limits.

Owner license/content rights, organizer-confirmed access and rehearsal, independent Windows/Linux novice setup, auditory trials, final captioned video/copy and entrant/eligibility/contact/rights declarations, distribution/hosting/submission authorization remain outstanding. This audit independently reran static package checks but did not execute those human/external steps. Post-merge PR record reports clean custody and M1/M3 smoke; those are separately attributed observations.

The final machine-readable [remote snapshot](execution/remote-status.json) records observation time, PR state, merge SHA and automatic main CI run 45171298993 state at audit close. Running checks are not described as passed. No additional release fix, PR merge, hosting or submission is performed by this branch.

At that final snapshot, [main CI 45171298993](https://github.com/Technique-S/Flip/actions/runs/45171298993) is **COMPLETED / SUCCESS**, both Windows and Ubuntu jobs successful for exact main `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`. This updates the earlier in-progress observation without rewriting PR #11's historical handoff. Snapshot SHA-256 `29dbbbd8d5eb505775ccff2b0e7b71e804844485ec87062ca6adcf44a01b78b8`, 31,733 bytes.

## Preservation and scope checks

Final audit delta must contain only `docs/planning/pre-m5/**`. `git diff --check`, internal file-link checks, exact requirement snapshot hash, archived execution parsing and protected-path equality are required before push. Original fixtures, schemas and all accepted code/test blobs stay byte-identical. Full repository custody/credential check is run against the committed audit tree and reported in the final handoff; it is not a waiver for newly archived data. No .gitattributes, fixture namespace exception, test assertion, timeout or credential rule is changed.
