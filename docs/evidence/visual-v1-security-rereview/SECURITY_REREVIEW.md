# P7-V1 security remediation — independent re-review

Reviewer: OpenCode (independent security and correctness reviewer). Date: 2026-11-26.
PR: https://github.com/Technique-S/Flip/pull/12 · **corrected head under review: `53a7f1cdd729188c7bfd593d37049836b6ed6a12`**

## Overall result

The four previously accepted adversarial attacks now fail at the intended integrity boundaries, the two low-severity projection findings and the UX navigation finding are corrected, and no accepted circuit semantics changed. **Local integrity-check correctness: PASS.** **V1 functional acceptance: PASS.**

The remaining condition is external to the code: the CI bootstrap trusts a digest embedded in `.github/workflows/m1-contracts.yml`, and that workflow is itself PR-controlled. I independently confirmed via the GitHub API that `main` is **not protected** (`HTTP 404 Branch not protected`). A coordinated modification of checker + trust metadata + workflow digest passes the bootstrap (case D8). Therefore **PR #12 merge readiness is CONDITIONAL PASS** — the code is mergeable only after the owner enables mandatory branch protection and required-workflow/review controls. The original FAIL remains the historical disposition; this is a new, independent review of a different exact head.

## Phase A — exact target and scope

- Current `refs/pull/12/head` = `53a7f1cdd729188c7bfd593d37049836b6ed6a12` (remote and checked out). No mismatch.
- Failed head `006050d7b8349dca3c263da2e3f1112617706541` is an ancestor of the corrected head; accepted main `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f` is also an ancestor.
- Remediation delta: 12 files — `.gitattributes`, `.github/workflows/m1-contracts.yml`, `apps/showcase/tests/release-guard.spec.mjs`, `apps/web/src/Composer.tsx`, `apps/web/src/visual/projection.ts`, `apps/web/tests/visual-readonly.spec.ts`, `docs/release/V1_RELEASE_TRUST.json`, `docs/ux/visual-v1/SECURITY_REMEDIATION.md`, two retained harness files, `results/security-before.json`, and `scripts/check_m45_release_package.mjs`. No change outside the security/non-security correction scope.
- Byte equality against the failed head verified for `packages`, `fixtures`, `docs/schema`, `apps/web/src/model.ts`, `apps/web/src/App.tsx`, `apps/web/package.json`, `apps/web/package-lock.json`, `docs/release/M45_R3_ASSET_INVENTORY.json`, `apps/showcase/recordings` and all original review evidence. The independent FAIL commit `1bfc6f677d6f4bd84ced14b078a96f6460f379a3` is unchanged on its branch.
- The implementer's retained `original-attack-harness.mjs.txt` is byte-identical (CRLF-normalized) to my committed original attack harness.

## Phase B/C/D — security results

Independent harness `security-rereview-harness.mjs` executes the **actual modified scratch checker** and the **exact inline CI bootstrap code extracted from the workflow**. 19/19 cases matched expectations and triggered the intended diagnostics. Full detail in `ORIGINAL_ATTACK_RETEST.md` and `TRUST_ROOT_ASSESSMENT.md`.

Key results:
- Pristine checker PASS (19 files / 130 links); pristine bootstrap PASS.
- All four previously accepted attacks REJECT: checker self-tamper (`Current checker integrity mismatch`), exemption/retarget (`Current checker scope changed`, `Authorized historical commit mismatch`), coordinated static+inventory tamper (`Historical static integrity mismatch: staticChecksums`).
- Bootstrap challenges all REJECT: changed checker, changed metadata with old workflow digest, changed imported `lib.mjs`, missing metadata, malformed checksum formatting, mismatched source hash, wrong historical tree, CRLF metadata. CRLF checker is normalized and passes, consistent with cross-platform intent.
- D8: a self-consistent checker + metadata + workflow-digest change **PASSES** the bootstrap. This is the documented residual trust assumption, not a detected code bypass.

## Phase E/F — non-security corrections and V1 correctness

- UX-01 RESOLVED: Visual shows an explicit explanation and a "Return to Advanced actions" button; browser test confirms Build is hidden in Visual and restored on return. Independent read-only attack still passes with zero requests/state changes.
- PROJ-01 RESOLVED: canonical `Name` guard on all source aliases and used REF aliases; 9 alias boundary cases plus a REF-used-alias case pass.
- PROJ-02 RESOLVED: cumulative pre-allocation counters. Exactly 1,000 edges accepted; 1,001 rejected early; 4,337 pins rejected early. No truncation or partial graph.
- Original 54 projection cases re-run against the corrected adapter with only the two alias expectations updated (now correctly REJECT): 54/54 as expected, zero input mutation.

## Phase G — test execution

| Check | Independent local result |
|---|---|
| `npm test` (workbench) | **44 passed**, 0 skipped/failed/retries, 3.7 min |
| `node apps/showcase/test.mjs` | **28 passed**, 0 skipped/failed/retries, 1.7 min |
| `uv run --frozen pytest -q` | **702 passed**, 0 failures, 13.5 min |
| `npm run lint` / `npm run build` | exit 0 |
| 9 frozen schema exporters, 3 canonical checks | 12/12 exit 0 |
| Ruff check / format | 88 files clean (initial failure was my removed one-shot helper, not production) |
| Custody/credential `--require-clean` | PASS on a clean temporary worktree at the exact corrected head |
| Release guard pristine | PASS, 19 files / 130 links |
| Implementer replay harness | 6/6 original attacks rejected |
| Independent security harness | 19/19 expected |
| Independent projection harness | 54/54; boundary harness 13/13; read-only attack 1/1 |

Exact-head hosted CI verified via GitHub API: runs `45739629122` and `45739623252`; `contracts (ubuntu-latest)` and `contracts (windows-latest)` all `success`, with every step including "Check release guard before execution" successful. The public log-receiver endpoint was unreachable from this environment, so per-platform test *counts* could not be read from CI logs; the implementer's reported 702/44/28 match my independently executed local counts, and the job conclusions are verified. No failed run was relabeled and no unexecuted check was called PASS. No retries were used locally.

## Phase H — original finding disposition

| Finding | Disposition | Evidence |
|---|---|---|
| RG-01 (checker bypass / provenance retarget) | **RESOLVED** (code level) | Checker removed from historical exemption; current bytes hashed via `V1_RELEASE_TRUST.json`; commit/tree/4 blobs pinned; exact set assertions; B1/B1b/B2/B2b/D1/D2 all rejected. Residual: D8 requires branch protection. |
| RG-02 (static checksums not pinned) | **RESOLVED** | `staticChecksums`, `staticChecksumManifest`, `recordingHashes`, `acceptedRuntimeSha`, `r2AuditSha` compared to historical inventory; B4 rejected at intended boundary. |
| RG-03 (missing regression cases) | **RESOLVED** | 7 original cases retained; 6 independent attacks replayed with boundary-specific assertions; coordinated bootstrap case added; 28 showcase tests pass. |
| UX-01 (Advanced navigation hidden) | **RESOLVED** | Explicit notice + return button; focused browser test passes. |
| PROJ-01 (alias syntax) | **RESOLVED** | `Name` guards; 10 boundary cases pass. |
| PROJ-02 (late budget check) | **RESOLVED** | Pre-allocation counters; 13 boundary cases pass. |

New finding: **SEC-01 (HIGH, repository-level)** — main branch is unprotected and the workflow digest is mutable in the same PR, so the trust root is not independently protected. Not remediated by this patch; requires owner action, not a code change in PR #12.

## Phase I — verdicts

1. Local integrity-check correctness: **PASS**
2. PR #12 merge readiness: **CONDITIONAL PASS** (code-level PASS; mandatory owner action below)
3. Protected-repository security posture: **FAIL**
4. V1 functional acceptance: **PASS**
5. Overall P7 completion: **FAIL** (V1 is one increment; editing, REF internals, Canary, portability, guide and V7 trials remain)
6. Public release readiness: **FAIL**

**Merge recommendation:** do not merge until the owner enables protection on `main` with `contracts` as a required status check for both OS matrix legs, requires review for `.github/workflows/m1-contracts.yml`, `docs/release/V1_RELEASE_TRUST.json`, `scripts/check_m45_release_package.mjs` and `apps/showcase/lib.mjs`, and dismisses stale approvals on new pushes. With those controls, the corrected head is acceptable for V1; without them, a PR can authorise its own trust root.
