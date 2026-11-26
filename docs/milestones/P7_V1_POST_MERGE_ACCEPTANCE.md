# P7-V1 post-merge acceptance

Date: 2026-11-26. Scope: merged PR [#12](https://github.com/Technique-S/Flip/pull/12), read-only visual composer only. This document records fresh post-merge execution and establishes the source baseline for a separately authorized V2. No V2 implementation, production change, deployment, wallet, signing, broadcasting or public solver hosting occurred.

## Disposition and exact baseline

**V1 functional verification passes on both required hosted operating systems.** Local browser/showcase and invariant checks pass. The local full Python run has a retained timing failure: **701 passed, 1 failed**; its unchanged isolated retry passed. This is not labeled a clean local 702-test run. **SEC-01 remains OPEN / HIGH**, accepted only as a repository-level development risk under the owner's approved solo-maintainer policy. Full P7, P8 and public-release readiness are not established.

- Fetched accepted `origin/main`: **`d96bdad6755d8a0c7434850ec6db227868abab65`**.
- PR #12 is MERGED, at `2026-11-26T03:52:30Z`, with exactly that merge SHA. Its reviewed head is **`53a7f1cdd729188c7bfd593d37049836b6ed6a12`**.
- Both revisions have complete Git tree **`89c50f47c345c1b02cd0a8d7441d739cae6490f8`**; `git diff 53a7f1cdd729188c7bfd593d37049836b6ed6a12 d96bdad6755d8a0c7434850ec6db227868abab65` is empty. PR #12 was squash-merged, so reviewed-head ancestry is not the correspondence test.
- Independent security re-review: **[`77520e4fa9915a7668677bf6b831b02a0d01fcee`](https://github.com/Technique-S/Flip/commit/77520e4fa9915a7668677bf6b831b02a0d01fcee)**. It reviews the exact head above; its delta is 14 evidence/document files, not additional runtime implementation. Their original hashes are indexed in the evidence. Those review files are not incorporated into main by PR #12.
- Previous accepted R3 main: `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`. All **707** historical files selected under `fixtures`, `docs/evidence`, `docs/schema`, `docs/release`, and `apps/showcase/recordings` have identical Git blobs at accepted main. Per-file Git blob IDs and SHA-256 values are preserved in the evidence.

The original independent FAIL `1bfc6f677d6f4bd84ced14b078a96f6460f379a3` and the re-review's CONDITIONAL PASS remain historical conclusions as issued. Earlier handoff text describing pending review/unprotected main is retained unchanged; the later API snapshot below records current protection, without rewriting earlier observations.

## Fresh execution

Hosted run **[45751652532](https://github.com/Technique-S/Flip/actions/runs/45751652532)** is a push run at the accepted merge SHA, completed SUCCESS. This is post-merge evidence, not PR-head CI substituted for main.

| Check | Windows hosted | Ubuntu hosted | Fresh local Windows |
|---|---|---|---|
| Full Python | 702 passed, 230.20 s | 702 passed, 123.41 s | 701 passed / 1 timeout, 708.62 s; isolated retry 1 passed, 62.49 s |
| Browser | 44 passed, 58.4 s | 44 passed, 44.6 s | 44 passed, 142.283 s; no skips/flakes/unexpected results |
| Showcase | 28 passed, 18.0 s | 28 passed, 13.0 s | 28 passed, 46.0 s |
| Web lint / TypeScript + production build | PASS | PASS | PASS; 25 files linted |
| Showcase build and deterministic `--check` | PASS | PASS | PASS, 19 deterministic static files |
| Release-integrity checker / CI bootstrap | PASS | PASS | PASS; 19 inert checksummed files, 130 local links |
| Nine schema exports with `--check` | PASS | PASS | PASS |
| Three Node canonical-parity commands | PASS | PASS | PASS: six core vectors, three portable packages, adapter pins |
| Ruff check / format check | PASS | PASS | PASS; 88 files already formatted |
| Library fixture manifest verification | PASS | PASS | PASS, 12 cases / 19 manifest files |
| Agent acceptance / authorization | PASS | PASS | PASS: 27/27 agent, 10/10 authorization |
| Agent-portable independent review / portability | PASS | PASS | PASS: 26/26 adapter, 12/12 portability |
| Repository custody `--require-clean` | PASS | PASS | PASS (clean source tree before adding this evidence) |
| M1/M3 transport smoke | PASS | PASS | PASS |
| M3/M4 report aggregators | PASS | PASS | Expected FAIL from retained local full-suite timeout; no report synthesized from mixed runs |
| Benchmark command | PASS | PASS | Not separately rerun locally |

Local toolchain: Python 3.14.6, uv 0.9.11, Node 24.18.0, npm 11.16.0. A fresh worktree and `uv sync --locked` / `npm ci --prefix apps/web` were used. npm reported zero vulnerabilities and its existing pending-esbuild-install-script warning; no approval-script or configuration override was applied, and builds succeeded.

Reproduction: run the commands in `.github/workflows/m1-contracts.yml` at the accepted SHA. Local principal commands were `npm run lint --prefix apps/web`, `npm run build --prefix apps/web`, `uv run --frozen pytest -q --junitxml=.test-tmp/postmerge-python.xml -o junit_family=legacy`, `npm test --prefix apps/web`, `node apps/showcase/build.mjs`, `node apps/showcase/build.mjs --check`, `node scripts/check_m45_release_package.mjs`, and `node apps/showcase/test.mjs`. Exact additional commands, exit codes and output are retained in `supplemental-commands.json`. Hosted job/step outcomes and selected original log lines are retained separately.

### Retained local failure

`packages/flip-core/tests/test_m3_acceptance.py::test_custody_and_scratch_regeneration` exceeded its existing `subprocess.run(... timeout=120)` limit at line 404 while executing the historical generator in scratch. The preceding original-byte/manifest assertions passed; the timeout itself establishes no completed regeneration result. No fixtures were regenerated in place. The initial full-suite failure XML and traceback are preserved, including all 702 cases.

The unchanged test was rerun alone after browser/showcase completion with the same 120-second limit: **1 passed in 62.49 seconds**. Both hosted full suites also passed this test. Timing contention is a plausible explanation, not proven root cause; the local reproduction timing risk remains documented. No code, test, timeout or custody guard was modified. M3/M4 aggregators correctly reject the initial failed JUnit and their nonzero results are retained as derived failures, not additional product failures.

## Circuit, evidence and read-only invariants

Fresh `visual-readonly.spec.ts:156` executes the genuine production sample/compose API, checks each rendered node/edge and exact numeric mapping, attempts Delete/Backspace, verifies disabled handles/non-draggable nodes, switches Advanced/Visual repeatedly, asserts unchanged session request, zero additional requests/page errors, and exact full compiled-response equality. `:339` verifies the visible Return to Advanced actions path. Projection rejection tests include malformed aliases and pre-allocation connection bounds; keyboard/axe tests include narrow layout and reduced motion. These are executed checks, not inference from component presence.

The fresh `canonical-before-after` attachment is **byte-identical** to the accepted capture `docs/ux/visual-v1/results/canonical-parity.json`, SHA-256 **`b4c5aa157ef966f7022c880bb637c7ea0d121c4710f5610c2614c0759158b933`**. Every request/projection/compiled-response field also equals the accepted capture.

| Identity | Before = after = accepted |
|---|---|
| Execution request canonical content hash | `0x18f3b6ec5fa4922c100e30010de8f8a45bfaced042f945299125a90ca46e3961` |
| Compiled response canonical content hash | `0xa784de2684e5397c2d4076e1ddfe8d8500a1c2df64b01cd9498f0a1b16bf471f` |
| Circuit netlist hash | `0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce` |
| Manifest hash | `0x10a2616767a30352158c32aae8cdb85b44cd7f5f04b168c462f41a8789b6f299` |
| Project hash | `0xff70814e174ae2dc841eef4a9e6367bb5318bccd069307c3afdce1adaa329959` |

Hashes were calculated through existing `flip_core.canonical.content_hash`, not a second circuit engine. Retained accepted evidence bytes are unchanged. Fresh export/replay and tamper/engine-binding cases pass in both hosted full suites and local browser journeys. Arbitrary new solver reports are not claimed byte-identical across independent runs/platforms: timing and engine context belong to their hash preimages. No new verification authority or schema meaning is introduced.

## Active main protection and SEC-01

Fresh GitHub API snapshots: `repos/Technique-S/Flip/rulesets/28133104` and `repos/Technique-S/Flip/rules/branches/main`. [Flip - Protected Main](https://github.com/Technique-S/Flip/rules/28133104) is **active**, targets the default branch and `refs/heads/main`, blocks deletion and non-fast-forward updates, has **no bypass actors**, and reports `current_user_can_bypass: never`.

Required checks are exactly **`contracts (ubuntu-latest)`** and **`contracts (windows-latest)`**, GitHub Actions integration ID 15368. Strict up-to-date checks are required; checks are enforced on branch creation. PRs require resolved review threads, dismiss stale approvals on push and require extra approval for unattributed changes. The approved solo-maintainer policy has **0 required approving reviews**, **no code-owner review requirement**, and no last-push approval requirement. Both active required checks passed at the accepted merge SHA. No repository settings were changed in this acceptance task.

**SEC-01 â€” OPEN / HIGH, repository-level trust-root risk.** A contributor able to coordinate changes to checker, trust metadata and workflow-pinned digest can redefine the PR-controlled bootstrap. The independent D8 coordinated attack remains the trust-boundary demonstration; this task does not reinterpret that expected acceptance as a fixed vulnerability. Individual checker/static/history tamper regressions and coordinated checker+metadata tamper under an unchanged workflow do fail closed, as exercised by the passing showcase cases. That narrower guarantee remains intact.

Owner: repository maintainer. Policy authority: the owner's current post-merge request explicitly directs recording SEC-01 OPEN under the approved solo-maintainer development policy. Active rules provide required dual-OS CI, PR gates, stale-approval dismissal and no bypass, but do not supply independent approval for trust-root/workflow changes. This is a consciously retained development risk, not an independent-review guarantee, security completion, authorization to weaken controls, or public-release clearance. Reassess the policy/trust-root boundary before contributor expansion or public release. Independent reviewer conclusions remain unchanged.

## Remaining limitations and V2 handoff

V1 remains a read-only candidate projection for NAND/stateless REF and external/output banks. Advanced is the execution/editing authority; Python is the canonical compiler/evaluator/verifier. No semantic graph edits, history/undo/redo, decoded nested REF/LATCH structure, stateful authoring, visual Canary overlays or persistent Portable Project layout are accepted here. Real screen-reader speech, physical touch-device behavior and large-graph performance acceptance remain untested. Full P7/P8 and public-release work require separate authorization and evidence.

Use accepted main `d96bdad6755d8a0c7434850ec6db227868abab65` / tree `89c50f47c345c1b02cd0a8d7441d739cae6490f8` as the V2 source baseline. This evidence branch adds only the present document and its new evidence directory; historical acceptance/review files, fixtures, schemas, CI/security policy and runtime are untouched. Do not infer V2 authorization from this handoff.

Evidence directory: [visual-v1-postmerge](../evidence/visual-v1-postmerge/README.md). Its manifest binds the retained raw reports, exact reassembled Python XML, source/custody identities, live-rule snapshots, canonical capture and command results. The evidence commit is the documentation-only commit containing this document; its exact SHA is reported on the PR and in the task handoff rather than embedded self-referentially.
