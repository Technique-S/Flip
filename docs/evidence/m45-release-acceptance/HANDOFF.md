# M4.5-R3 — Release acceptance materials handoff

**Status: EVIDENCE AND SPECIFICATION ONLY. Date 2026-11-22.**
No release, public deployment, static hosting, wallet integration, transaction, submission, license choice or
founder approval occurred. This branch is to be committed and pushed **without merging**.

## 1. Scope and provenance

| Item | Value |
|---|---|
| Reviewer | OpenCode / HY4 Flash (support) |
| Branch | `opencode/flip-m45-release-acceptance` |
| Base | accepted main `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b` |
| Codex R2 audit | `codex/flip-m45-release-readiness` @ `39df7af`, based on accepted main, documentation only |
| Write scope | `docs/evidence/m45-release-acceptance/`, `fixtures/m45-release-acceptance/` only |
| Production, schemas, lockfiles, CI, Codex release branch | Unchanged |

## 2. Files written

- `docs/evidence/m45-release-acceptance/RELEASE_ACCEPTANCE_MATRIX.md`
- `docs/evidence/m45-release-acceptance/STATIC_SHOWCASE_SECURITY.md`
- `docs/evidence/m45-release-acceptance/RIGHTS_AND_NOTICES.md`
- `docs/evidence/m45-release-acceptance/HUMAN_TEST_PROTOCOL.md`
- `docs/evidence/m45-release-acceptance/SUBMISSION_CLAIM_AUDIT.md`
- `docs/evidence/m45-release-acceptance/HANDOFF.md` (this file)
- `fixtures/m45-release-acceptance/README.md`
- `fixtures/m45-release-acceptance/claim-negative-cases.json`
- `fixtures/m45-release-acceptance/MANIFEST.json`

## 3. Commands actually executed in this review (read-only)

Repository setup/source:
- `git fetch origin --no-tags`; `git for-each-ref` on remote refs; `git log` and `git diff --name-status origin/main..origin/codex/flip-m45-release-readiness` to locate and verify the R2 audit.
- `git worktree add -b opencode/flip-m45-release-acceptance ... b537eb6`; `git worktree add --detach ... 39df7af`.
- Full reads of the six R2 documents plus R2 evidence JSON metadata; reads of accepted `README.md`, `MVP_CONSTRAINTS.md`, PRD, technical design, ownership matrix, dependency plan, `docs/agents/WORKFLOW_INTEGRATION.md`, `docs/schema/DEPENDENCIES.md`, `docs/milestones/M3_A_SOLVER.md`, `apps/web/package.json`, `apps/web/package-lock.json`, `packages/flip-core/src/flip_core/rpc.py`, `packages/flip-api/src/flip_api/local.py` and the relevant frontend sources.

Static-showcase / security baseline:
- Case-insensitive `grep` over `apps/web` for wallet/signing/broadcast/provider terms → 3 textual matches: two "No transaction broadcast" disclosures and one single-provider note; no wallet SDK, provider object or signing call.
- `grep` for `fetch(` and `/api/` in `apps/web/src` → `/api/v1/${path}` in `model.ts`, `/api/library/v1/execute` in `Library.tsx`, `/api/agent/v1/portable` in `AgentPortable.tsx`.
- `grep` for `eth_[A-Za-z]+` in `flip_core/src` → read-only methods in `rpc.py` (`eth_chainId`, `eth_getBlockByNumber`, `eth_call`, `eth_getCode`, `eth_getStorageAt`) plus bounded call sites in `importer.py`/`preflight.py`; no send/sign method.
- Directory listing of `scripts/` → no `check_write_rpc_absence.py`; the design document's checker is not implemented.
- `local.py` inspection → loopback bind, `TrustedHostMiddleware`, cross-origin rejection, `proxy_headers=False`.

Licensing inventory:
- `python` parsed `M45_R2_EVIDENCE.json`: 35 Python and 17 Node dependency metadata entries; Python license counts MIT 19, BSD-3-Clause 6, MPL-2.0 1, Apache-2.0 OR BSD-2-Clause 1, BSD-2-Clause 1, MIT OR Apache-2.0 1, PSF-2.0 1, null 5; Node declaredLicense null 17.
- `python` parsed accepted `apps/web/package-lock.json`: 70 installed entries with MIT 33, Apache-2.0 24, MIT OR Apache-2.0 11, MPL-2.0 2. This resolves the R2 null-field gap without rewriting R2 evidence.

Self-verification:
- `python` JSON parse of `claim-negative-cases.json` and `MANIFEST.json`; 12 cases; SHA-256 match true.
- `git status --short`, `git diff --check`, `git diff --name-only b537eb6..HEAD` → only the two allowed directories are staged/untracked; no whitespace errors.

## 4. Not executed here

- No full Python/Chromium suite re-run. The 702 Python / 27 Chromium results are **R2_EXECUTED** historical evidence, not this reviewer's fresh result.
- No static viewer was built or scanned; no viewer exists in accepted main.
- No browser or screen-reader session, no first-time developer trial, no judge-access rehearsal.
- No wallet, key, signing, RPC write, broadcast, transaction, hosting, tunnel, deployment or submission.
- No web retrieval of organizer form; R2 recorded it as inaccessible and NOT VERIFIED, and this review did not bypass that protection.

## 5. Blockers and unresolved gates

1. Judge access method unconfirmed by organizer (H3/G13).
2. No own-source license or redistribution rights decision (G17/G18).
3. No human screen-reader speech or novice trial results (G12/G03).
4. No finished captioned video or approved final submission copy (G16/O-05/O-06).
5. No static viewer or downloadable supported distribution; both require separate authorization (RA-01/RA-11, G22).
6. Public interactive hosting remains BLOCKED pending independent target-host review (G23).
7. No organizer-confirmed access URL or completed form fields/eligibility declarations (G14).

## 6. Disposition

- Supported local technical demo: PASS with R2's prerequisite/reference/native-engine bounds.
- Judge access: BLOCKED. Submission completeness: PARTIAL. Public deployment and write-enabled publication: BLOCKED.
- Manual accessibility and novice trial: NOT TESTED. Rights/licensing: BLOCKED.
- All nine deliverables are specifications or evidence inventories; passing static-source checks do not flip any blocked gate.

## 7. Next steps

Owner resolves O-01–O-12 in `SUBMISSION_CLAIM_AUDIT.md`; maintainer adopts the reviewed quickstart corrections;
human tester completes Part A/B of `HUMAN_TEST_PROTOCOL.md`; then, and only then, the conditional judge-access
checks in `RELEASE_ACCEPTANCE_MATRIX.md` §4 may be run against the organizer-confirmed method.

**Commit SHA:** the single commit on this branch; reported in the final handoff message and available from
`git log -1` on `opencode/flip-m45-release-acceptance`.
