# Final merge recommendation — P7-V1 security re-review

## Exact identifiers

- PR: https://github.com/Technique-S/Flip/pull/12 — **kept open, not merged**
- Exact head reviewed: `53a7f1cdd729188c7bfd593d37049836b6ed6a12`
- Previously failed head: `006050d7b8349dca3c263da2e3f1112617706541` (ancestor of corrected head)
- Original independent FAIL: `1bfc6f677d6f4bd84ced14b078a96f6460f379a3` on `opencode/flip-visual-v1-independent-review` (verified unchanged)
- Review branch: `opencode/flip-visual-v1-security-rereview`; final review SHA reported in the accompanying chat handoff.

## Findings disposition

| ID | Disposition |
|---|---|
| RG-01 checker/provenance bypass | **RESOLVED** at code level; residual coordination risk requires branch protection |
| RG-02 unauthenticated static checksums | **RESOLVED** |
| RG-03 missing guard regressions | **RESOLVED** |
| UX-01 hidden Advanced navigation | **RESOLVED** |
| PROJ-01 alias syntax | **RESOLVED** |
| PROJ-02 late budget check | **RESOLVED** |
| SEC-01 (new, HIGH, repository-level) | **OPEN** — `main` is unprotected; PR-controlled workflow digest is not an independent trust root |

## Independent results

- Four previously accepted attacks: all now REJECT at intended boundaries (19/19 harness cases, 6/6 implementer replay).
- Workbench browser 44/44; showcase 28/28; Python 702/702; 9 schema + 3 canonical checks; lint/build/Ruff/custody pass.
- Projection 54/54 + boundary 13/13; read-only browser attack 1/1.
- Exact-head CI: all Ubuntu and Windows jobs and all steps `success` at `53a7f1c…` (runs `45739629122`, `45739623252`). Per-platform counts could not be read from the blocked log endpoint; local counts match the implementer's reported 702/44/28.

## Verdicts

| Area | Verdict |
|---|---|
| 1. Local integrity-check correctness | **PASS** |
| 2. PR #12 merge readiness | **CONDITIONAL PASS** (code-level PASS; owner action mandatory) |
| 3. Protected-repository security posture | **FAIL** |
| 4. V1 functional acceptance | **PASS** |
| 5. Overall P7 completion | **FAIL** (V1 is one increment; P7 incomplete) |
| 6. Public release readiness | **FAIL** |

## Mandatory owner action before merge

Branch protection is **mandatory for acceptance**, not optional hardening:

1. Protect `main` and require the `contracts` status check for both `ubuntu-latest` and `windows-latest`.
2. Require review for `.github/workflows/m1-contracts.yml`, `docs/release/V1_RELEASE_TRUST.json`, `scripts/check_m45_release_package.mjs` and `apps/showcase/lib.mjs`.
3. Dismiss stale approvals on new pushes; disallow bypass of required checks.

Until these are enabled, a PR can authorise its own trust root (demonstrated by case D8) even though every local integrity check passes. No code change in PR #12 can substitute for this repository-level control.

## Recommendation

Do not merge on the current unprotected repository. After the owner enables and verifies the controls above, the corrected exact head `53a7f1c…` is acceptable as P7-V1: the read-only projection, canonical parity, read-only enforcement, accessibility and release-guard integrity checks all pass independently.

V1 acceptance is not P7 completion and not P8 or public-release readiness. Continue to keep PR #12 open; no deploy, transaction, wallet, hosting, V2 implementation or rewrite of accepted evidence/results occurred in this review.
