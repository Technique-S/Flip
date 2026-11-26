# P7-V2-A final independent acceptance review

Reviewer: OpenCode (independent adversarial reviewer). Date: 2026-11-26.
PR #14: https://github.com/Technique-S/Flip/pull/14 — **draft, not merged**. Exact reviewed head: `036c7a99f26d87dd4366762c8c3c059ac8e3d65d`.

## Verdict summary

| Area | Verdict |
|---|---|
| V2-A functional acceptance | **PASS** |
| Canonical semantic correctness | **PASS** |
| Historical proof/evidence integrity | **PASS** |
| PR #14 merge readiness | **PASS (code level)** — owner retains SEC-01 policy decision |
| SEC-01 repository risk | **OPEN / HIGH** (unchanged, accepted solo-maintainer policy) |
| Overall P7 completion | **FAIL** (V2-A is one increment) |
| P8 readiness | **FAIL** |
| Public deployment readiness | **FAIL** |

No BLOCKER or HIGH product finding was found. Two non-blocking findings: MEDIUM SB-3 limit documentation, LOW `__proto__` own-key handling in the private validator.

## A. Baseline and scope

- PR head verified against `refs/pull/14/head`: exact match `036c7a99…`.
- Accepted main `fc9c0c1bcb2557169dd89af0c3b2c5a7628c9adf` is an ancestor; production implementation `b23d3dcf8f98e9b95cd0bc8ca8fbf612045e1daa` is an ancestor.
- `git diff b23d3dc… 036c7a9…` contains only evidence/documentation additions (handoff edit + `docs/ux/visual-v2-a/focus-fix/**`). The production tree is unchanged between implementation and final head.
- Production delta vs accepted main: 11 frontend source files and one new browser test file. `packages`, `fixtures`, `docs/schema`, `docs/release`, `.github/workflows`, `scripts`, `apps/showcase` and `apps/web/package*.json` are byte-identical Git trees. No Python, schema, CI, release-guard, dependency or accepted-evidence change.
- Original review packages preserved unchanged on their branches: `1bfc6f67…` (V1 FAIL), `77520e4f…` (V1 security re-review), `b671893b…` (V2-A prospective design).

## B. Prospective case reconciliation

All 56 cases from the test-design package were read and executed where feasible. **Final classification: 30 PASS, 22 CONTRACT_MISMATCH, 4 NOT_EXECUTED, 0 FAIL.** No case was silently relabeled; every reinterpretation records its governing source and browser evidence in `case-reconciliation-final.json`. The original 19/37 expected distribution was not treated as authoritative: V2-A's approved contract (explicit input bindings, NAND-only, no output remap, inherited interactive budget) changes the premise of several cases.

Full matrix in `PROSPECTIVE_CASE_RECONCILIATION.md`.

## C. Semantic blockers

SB-1, SB-2, SB-4, SB-5, SB-6, SB-7, SB-8, SB-9, SB-10 **RESOLVED** with implementation and test references. SB-3 **PARTIALLY RESOLVED** — the interactive budget is inherited from baseline `App.tsx` (`pins * width > 65000`), but its effective ceiling (~178 NANDs) is not stated in the handoff. See `SEMANTIC_BLOCKER_DISPOSITIONS.md`.

## D–F. Attacks, history, proof freshness

26 independent adversarial probes of the actual command layer all produced the expected accept/reject outcomes: duplicate IDs, malformed/boolean/negative/fractional/out-of-range pins, true forward references, unknown source components, unsupported kinds, referenced removals (exact locators), unreferenced removal restoring exact original bytes, two-add/two-undo and divergent-redo snapshots, 178/179/499 budget boundaries, 1 MiB size guard. Real compose/history/proof behavior was re-executed by the 72-case browser suite, including a real EQUIVALENT comparison invalidated by an edit and retained only as historical. See `CANONICAL_AND_HISTORY_ATTACKS.md` and `PROOF_FRESHNESS_AND_SECURITY.md`.

## G. UX and accessibility

72/72 workbench browser tests pass locally and on both hosted OSes, including new keyboard/focus regressions. No manual screen-reader, physical touch or high-zoom trial occurred; those remain untested. See `UX_ACCESSIBILITY_REVIEW.md`.

## H. Security

Only `api("compose", …)` is called by the editor; no wallet, signing, transaction, arbitrary URL, external network or React Flow mutation authority. Release guard, CI bootstrap and protected-main rules unchanged and re-verified. SEC-01 remains OPEN/HIGH under the owner's accepted policy; this review does not close it. See `PROOF_FRESHNESS_AND_SECURITY.md`.

## I. Regression evidence

| Check | Independent local result | Hosted exact-head |
|---|---|---|
| Workbench browser | 72/72 passed, zero skips/flakes | 72/72 Ubuntu and Windows (read from run logs) |
| Showcase | 28/28 passed | 28/28 both OS |
| Python | 702/702 passed, 0 failures, 12.1 min | 702/702 both OS |
| Lint / production build | PASS (29 files) | PASS |
| Frozen schema exports / canonical parity | 7/7 + 3/3 PASS | PASS |
| Release guard + CI bootstrap | PASS (19 files / 130 links) | PASS |
| Custody `--require-clean` | PASS on clean worktree at exact head | PASS |

Hosted runs `45898397718` and `45898393524` all `success`; earlier failed run `45896495418` was at `e92ae1e…` and is retained as history, not relabeled. No assertion was weakened or timeout increased in this review.

## J. Findings

| ID | Severity | Location | Correction |
|---|---|---|---|
| V2A-F1 | MEDIUM | `apps/web/src/visual/commands.ts:22`, `P7_V2_A_HANDOFF.md:70` | Document the inherited interactive-budget formula and its ~178-NAND effective ceiling; surface the exact reason in the UI. |
| V2A-F2 | LOW | `apps/web/src/visual/commands.ts:73-81` | Normalize own keys after command construction so an object-literal `__proto__` cannot bypass the closed-key check; JSON-parsed extras already reject and no canonical mutation was observed. |
| V2A-I1 | INFORMATIONAL | SEC-01 | Remains OPEN/HIGH under approved solo-maintainer policy; reassess before contributor expansion or public release. |

## K. Ownership

Review branch `opencode/flip-visual-v2a-final-review`; evidence only under `docs/evidence/visual-v2a-final-review/**` and optional fixtures under `fixtures/visual-v2a-final-review/**`. No production code, PR #14, accepted fixture, earlier review package or security guard was modified. No merge, deployment, V2-B/V2-C, wallet, transaction or public solver work was performed.
