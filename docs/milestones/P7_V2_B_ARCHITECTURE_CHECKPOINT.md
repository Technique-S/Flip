# P7-V2-B architecture checkpoint and merged V2-A baseline

Prepared 2026-11-26. This is a documentation-only architecture handoff, not V2-B implementation acceptance. **SEC-01 remains OPEN/HIGH. V2A-F1 remains OPEN/MEDIUM; V2A-F2 remains OPEN/LOW.** No production code, frozen schemas, accepted fixtures, prior evidence, CI or release/security guards are changed.

## Baseline and provenance

- Fetched `origin/main` and observed the exact accepted main **`2fa7281ba01557f484cef2878e484b6e16f3ffd2`**.
- [PR #14](https://github.com/Technique-S/Flip/pull/14) is MERGED, at that commit; GitHub reports merge time `2026-11-26T22:28:07Z` and original head **`036c7a99f26d87dd4366762c8c3c059ac8e3d65d`**. The independently reviewed head is identified by the owner's acceptance/merge-authorization comment on PR #14; GitHub's formal reviews endpoint returned no review objects. This checkpoint verifies byte correspondence, not independent authorship of the review or an additional signed review artifact.
- Reviewed head and merged main have the **same entire Git tree**: `3a579710889e4b456bf0ac93b9642475ba73b749`. `git diff --name-status 036c7a99f26d87dd4366762c8c3c059ac8e3d65d 2fa7281ba01557f484cef2878e484b6e16f3ffd2` is empty. This is stronger than checking only production paths. The earlier production implementation is `b23d3dcf8f98e9b95cd0bc8ca8fbf612045e1daa` with subsequent additive evidence at the reviewed head.
- Isolated branch: `codex/flip-visual-v2-b-architecture`, worktree `C:\Users\Kazi\Documents\Flip\flip-visual-v2-b-architecture`. Other worktrees and the original untracked milestone update are untouched.
- Read AGENTS.md, README, MVP constraints, PRD, technical architecture, ownership/dependency documents, V2-A checkpoint/handoff/evidence, compiler/model/projection/command/editor code and the current workflow. Historical illustrative architecture is not treated as the actual schema. No skill-generated product/theme files or dependency changes were introduced.

The planning commit is the commit first introducing this document and its four linked specifications; the additive final verification receipt records its exact SHA after creation. `git log --diff-filter=A --format=%H -- docs/architecture/P7_V2_B_WIRING_CONTRACT.md` independently identifies it without a self-referential checksum. The final evidence/branch SHA is reported separately; neither is substituted for the accepted production baseline.

## Deliverables and decisions

| Deliverable | Document |
|---|---|
| Canonical binding command, ordering/fan-out/REF/output semantics, atomic state/history/proof boundaries | [Wiring contract](../architecture/P7_V2_B_WIRING_CONTRACT.md) |
| Actual control inventory, drag preview/review/recovery, pin labels, wire inspection, keyboard/touch/AT, React Flow source research | [Interaction/accessibility specification](../ux/P7_V2_B_INTERACTION_SPEC.md) |
| Risk/dependency register, proposed stages, separate Codex/OpenCode ownership, capacity/own-property remediation | [Integration and remediation plan](../architecture/P7_V2_B_INTEGRATION_PLAN.md) |
| 29 adversarial cases, native/compiler/UI/manual evidence gates, preservation of V1/V2-A | [Acceptance architecture](../ux/P7_V2_B_ACCEPTANCE.md) |

Recommended first implementation milestone, **after separate authorization**: V2-B0 fixes F1/F2 and introduces the pure one-slot ReplaceBinding seam with real-compiler regressions, without enabling canvas wiring. Then implement native keyboard/tap picking and Review, followed by the drag adapter and target-class gates. React Flow remains a controlled presentation/interaction layer; accepted Execution plus native compose stays authoritative. No second circuit engine or schema version is needed for changing an existing binding.

## Post-merge execution observed at planning

The accepted-main [push CI run 45904976829](https://github.com/Technique-S/Flip/actions/runs/45904976829) completed **SUCCESS** on both Windows and Ubuntu at exactly `2fa7281ba01557f484cef2878e484b6e16f3ffd2`. Both jobs completed every workflow step successfully, including:

| Suite | Ubuntu | Windows |
|---|---|---|
| Browser | 72 passed, 49.1s | 72 passed, 1.2m |
| Showcase | 28 passed, 10.9s | 28 passed, 17.4s |
| Full Python | 702 passed, 95.03s | 702 passed, 190.77s |
| Nine schema exports, three Node canonical parity checks, release trust bootstrap/integrity, fixture validation, Ruff, agent/portable acceptance, clean custody, smoke and benchmark | Every step SUCCESS | Every step SUCCESS |

Fresh local Windows source checkout uses locked Python 3.14.6/uv 0.9.11 and the unchanged npm lock. `uv sync --locked` and `npm ci --prefix apps/web` succeeded; npm reported zero vulnerabilities and an advisory about an unapproved esbuild install script, but the production build passed without changing install policy. The sequential 33-command harness follows the existing workflow, preserving each command's arguments, timing, exit code and separate output. At the planning commit, lint/build, **72/72 browser** (202.212s, zero skips/unexpected/flaky), showcase **28/28**, release bootstrap/integrity, Ruff, all nine schema exports and frozen library fixtures have passed. Full Python and subsequent checks are in progress; the additive final receipt records actual completion and any failures/retries. Do not read this interim observation as a clean final local run.

Fresh canonical-before/after browser attachment SHA-256 is **`b4c5aa157ef966f7022c880bb637c7ea0d121c4710f5610c2614c0759158b933`**, byte-identical to `docs/ux/visual-v2-a/focus-fix/canonical-parity.json`. Stored request before/after and native compose responses before/after are equal. Project identity `0xff70814e174ae2dc841eef4a9e6367bb5318bccd069307c3afdce1adaa329959`, netlist `0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`, manifest `0x10a2616767a30352158c32aae8cdb85b44cd7f5f04b168c462f41a8789b6f299` remain unchanged. No arbitrary fresh solver report is claimed byte-identical across engine/timing environments.

The unchanged browser suite exercises Visual/Advanced mode switches, read-only graph guards, explicit NAND creation/removal, real compose validation, history/dirty/recovery/reset/stale evidence and the hosted focus regressions. Desktop V2-A and 390px baseline screenshots were visually inspected; current UI remains read-only for graph wiring. Screenshot metadata/hashes are retained; raw PNGs stay in ignored scratch under existing custody rules. No binary exception or encoded-image workaround is added. Future drag/keyboard/touch/screen-reader wiring behavior is **NOT IMPLEMENTED / NOT TESTED**.

## Probes, failures and limitations

Twenty corrected native parser/compiler probes cloned the archived half-adder and observed NAND replacement, fan-out, repeated input, existing REF input/output and output-bank binding acceptance, plus self/forward/missing/range/bool/identity/stateful/LATCH/extra-field rejection. They invoke existing native code, not a proposed UI command or second engine. All corrected expected/observed outcomes match.

The **initial probe harness failed its assertion**: it guessed a nonexistent `xor0` component and used component index 2 (`sum`, a REF) for a supposed self-reference to `carry` (an earlier NAND). The actual recipe is `[nand0 REF, carry NAND, sum REF]`. Thus a missing REF source was rejected and the supposed “self” binding was correctly accepted as a backward reference. The initial report/script are preserved separately; only the scratch probe's IDs/indexes were corrected. No compiler, production test or accepted fixture was changed. This is an investigator harness error, not a post-merge production defect.

Frontend probes reproduce the exact F1 178/179 boundary and F2 own/inherited/prototype behavior. A plain pin, exact own pin with object-literal custom/null prototype, and a malformed inherited-pin/decoy-own-key object are accepted by current V2-A; a JSON own `__proto__` extra is rejected. The remedy specifies normalization of exact own data keys, preserving canonical semantics. Both findings stay OPEN until real implementation/regressions and independent review.

Retained earlier V2-A evidence already records the fixed focus/overflow failures and prior timing timeout; it is not rewritten or relabeled as a new failure here. Local full-Python native worker performance is slower than hosted runners; no timeout/budget/assertion is changed. Historical source observations remain historical, single-RPC data is not malicious-RPC resistance, and green CI cannot close SEC-01.

## Evidence custody and stop boundary

New evidence only: `docs/ux/visual-v2-b/checkpoint/` holds baseline/tree/blob hashes, direct probe reports and reproduction-script text, exact-main hosted CI metadata/logs, browser report, canonical capture and screenshot metadata. A manifest hashes those new files. Raw binaries/traces and generated environments remain ignored scratch; tests can recreate baseline renders. The final additive receipt and local completion evidence are separate from the initial planning capture.

No production behavior, frozen schema, accepted fixture, historical evidence, dependency, workflow, trust metadata/checker or security setting is changed. No wallets, signing, transactions, unexpected live RPC, deployment, public solver hosting, Visual Wiring Canary or V2-C is authorized or performed. No V2-B implementation is started; assignments remain proposed. Stop after pushing the documentation-only design branch with exact planning and final evidence SHAs.
