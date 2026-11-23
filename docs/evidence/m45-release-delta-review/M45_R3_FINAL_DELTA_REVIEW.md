# M4.5-R3-D — Final release package delta review (PR #11)

**Reviewer:** independent verification engineer (OpenCode / HY4 Flash).
**Scope:** delta review only. The complete static-showcase research was **not** repeated because the delta contains no generator, recording, pin, production, schema, lock or CI change (verified below).

## 1. Exact targets and ancestry (verified before testing)

| Item | Value / verification |
|---|---|
| PR | `https://github.com/Technique-S/Flip/pull/11` — OPEN, **draft**, `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`, base `main` @ `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b` |
| Reported / actual PR head | **`22e781d454336cb2067aca1ce7f8cf66809f0f4d`** — `git ls-remote origin refs/pull/11/head` and `refs/heads/codex/flip-m45-release-package` both returned this exact SHA; re-checked at end of review, unchanged |
| Originally reviewed delivery | `1783b61fefc41007b745753b09c4e0e70a8af7f7` — `merge-base --is-ancestor 1783b61 22e781d` exit 0; exactly **3 commits** in the delta |
| Previous independent review | `opencode/flip-m45-release-final-review` @ full SHA **`10fb6ca5798142d7d6a372e491aebd47d3bfb79f`** (commit `10fb6ca`), still present in the object store |
| Accepted main | `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b` |
| Delta commits | `8bcb1f2` (test: preserve R3 research and exercise twelve misleading claims), `a5c9a73` (fix: archive release specifications outside runtime fixture namespace), `22e781d` (docs: record R3 acceptance evidence reproduction and release gates) |

Worktree: `flip-m45-release-delta-review`, branch `opencode/flip-m45-release-delta-review`, created at `22e781d`, clean at start. A gitignored `apps/web/node_modules` junction was created solely to run the Playwright suite; no tracked file outside the two allowed evidence directories was changed by this review.

---

## 2. A — Exact delta review

`git diff --name-status 1783b61..22e781d`: **12 files, +1031 lines, no deletions in the net delta.**

| Area | Delta effect | Assessment |
|---|---|---|
| Static showcase generation | **none** — `build.mjs`, `lib.mjs`, `style.css`, `playwright.config.mjs`, `dist/` untouched | No regeneration research needed; I still rebuilt and byte-compared (below) |
| Recorded evidence / manifest pins | **none** — all 7 recording JSONs and `manifest.json` untouched | Pins remain `0d4161ac…6029` / accepted runtime `b537eb6…` / R2 `39df7af…` |
| CLI / API / native verification | **none** — `packages/`, `apps/web/`, `uv.lock`, `pyproject.toml` unchanged from both `1783b61` and accepted main | No native or production semantics changed |
| Release documentation | **additive** — new `docs/release/M45_R3_ACCEPTANCE.md` (199 lines) and 6 archived OpenCode research docs | Honestly marked "Independent acceptance: PENDING. Stop before merge or release" |
| Acceptance tests | **additive** — new `apps/showcase/tests/acceptance.spec.mjs` (143 lines): 1 custody test + 12 negative-claim cases | Existing 6 showcase tests untouched |
| CI configuration | **none** — zero diff in `.github/workflows/` vs `1783b61`; no gate removed, no timeout/exemption added | Verified independently |
| Custody / fixture preservation | `.gitattributes` gains one additive `-text` rule for `docs/evidence/m45-release-acceptance/**`; three research files were added then relocated with `R100` (100% byte-identical renames) out of the runtime fixture namespace | No corpus allowlist, exemption or original evidence weakened |

**Confirmation of unchanged production/pins:** `git diff` for `apps/showcase/build.mjs`, `lib.mjs`, `style.css`, `recordings/`, `dist/`, `docs/schema/`, `packages/`, `apps/web/`, `uv.lock`, `apps/web/package-lock.json`, `.github/workflows/` produced **no modifications**. Independently rebuilt output at the PR head: **19/19 files byte-identical** to the reviewed delivery's `dist`, same `CHECKSUMS.json`, same `BUILD.json`, all capability flags `false`, manifest SHA `0d4161ac…6029`, inventory match, zero independent checksum mismatches.

**Documented initial failure, independently confirmed:** CI run `45127865959` at `8bcb1f2` failed exactly `test_report_only_gaps_are_not_executable_golden_fixtures` because synthetic research JSON was placed under `fixtures/` (701 passed / 1 failed). Correction `a5c9a73` changed only 5 files (7 insertions, 3 deletions): 3 `R100` relocations, path updates in the new acceptance spec, and removal of the old `.gitattributes` line. No production test, gate or allowlist was modified.

---

## 3. B — Reconciliation of prior findings

| ID | Prior severity | Final disposition | Evidence |
|---|---|---|---|
| **F-01** missing delivery SHA | MEDIUM | **STILL OPEN** | `M45_R3_ACCEPTANCE.md:12` now states `1783b61…`, so the hash does exist in a release document. **But** `README.md:42` still directs a first-time reader to `git checkout b537eb6…`, and `README.md:50` still says to "check out the exact R3 delivery SHA given in its handoff" — while `M45_R3_HANDOFF.md:6-8` still deliberately omits it. The README does not link or mention `M45_R3_ACCEPTANCE.md`. Following the install section still yields the accepted runtime **without** `apps/showcase` or the R3-only commands, with no explanation of the difference. Per the task criterion, appearance in an internal/secondary document does **not** resolve F-01. |
| **F-02** checklist accuracy | LOW | **STILL OPEN / INFORMATIONAL** | `docs/release/M45_R3_DEMO_AND_CHECKLIST.md:28` is unchanged: `- [x] Corrected current README and source-pinned Windows/Linux instructions.` It remains overstated because of F-01. No false capability claim; informational severity retained. |
| **F-03** recording provenance | INFO | **LIMITATION PRESERVED** | Independent re-scan of the entire PR-head tree (1,044 files) found **no** original R2 source receipt/replay/project file outside `recordings/`. The acceptance record restates the pinned SHA-256 values (`b651a994…`, `2b77b5c5…`) and calls them "preserved R2 journey outputs", but supplies no independent originals. The manifest pins still match the curated bytes; no substitution evidence. I did not invent or rewrite historical source files or claims. |

**New findings:** none at HIGH or MEDIUM. One INFO observation: the new 12-case tests deliberately exercise a *custody boundary*, not a semantic claim classifier — a forged claim is rejected because recording bytes and the manifest pin fail, not because the text was understood (the acceptance record states this explicitly at `M45_R3_ACCEPTANCE.md:127-130`). This is honest and does not weaken the result, but it should not be read as a general-purpose hostile-text filter.

---

## 4. C — New acceptance tests (independently checked)

All 12 cases from the archived fixture (`c50aa301…988f`, `SPECIFICATION_ONLY / INVENTED_TEST_INPUT`) were executed by the new spec and corroborated with my own harness:

- **19/19 Playwright tests passed locally** in 40.2s (6 original showcase tests + 1 research-custody test + 12 claim cases); JSON report `expected: 19, skipped: 0, unexpected: 0, flaky: 0`. CI artifact for the exact head independently shows the same 19/19.
- Each case: modified recording bytes are rejected (`Wrong byte length: receipt.json`) → attacker rewrites manifest `bytes`/`sha256` → still rejected (`Recording manifest differs from the reviewed build input`) → **no `dist/index.html` is generated** in the tampered builder directory. Verified independently with a separate Python/node harness that does not import Codex's spec.
- All seven original offline pages independently verified to contain `RECORDED · HISTORICAL` and none of the 12 synthetic claim strings.
- **OpenCode research custody:** all **9** original Git blobs at `82e25de…` byte-identical to the archived files (independent `git show` comparison); fixture SHA-256 matches; 12 cases; net diff in the runtime `fixtures/` namespace is **empty**.
- No production corpus namespace or custody exemption was weakened (§2).

---

## 5. D — Exact-head acceptance

| Check | Result |
|---|---|
| Static build / deterministic `--check` / integrity checker | PASS (exit 0): 19 files; `--check` byte-identical; `PASS: 19 checksummed inert files, 122 local links` |
| Independent hash recomputation | PASS: 19/19 checksums, inventory match, all capabilities false |
| Full 19-test showcase suite | PASS locally and in exact-head CI artifact (19 expected, 0 skipped/unexpected/flaky) |
| Offline navigation / zero sensitive calls / accessibility | PASS — covered by the unchanged 6 suite tests (offline `file://` walkthrough, injected `fetch`/XHR/WebSocket/EventSource/beacon/wallet probes at zero, CSP, axe WCAG 2 A/AA + 2.1 AA at desktop/390px, reduced motion, keyboard/JS-disabled, 320px overflow) |
| Custody & credential scan | PASS (exit 0): 894 tracked files, 0 credential-pattern findings; `result: PASS` |
| Windows/Linux CI for exact head | PASS — runs `45130355038` and `45130326912`, both `head_sha = 22e781d…`; every step on both `ubuntu-latest` and `windows-latest` concluded `success`, including `npm test`, all four static-showcase steps, full pytest, Ruff, all schema `--check` gates, fixture verification, custody `--require-clean`, smoke and benchmark steps. Earlier delivery CI (`45082540732`) was **not** substituted for the final head. |
| Frozen schemas / previous evidence | PASS — byte-identical to accepted main and reviewed delivery |

**Honestly unexecuted locally:** fresh `uv sync --locked` / clean-novice install, native CLI comparison and replay (uv absent on this terminal; the release record reports them at the earlier source revision), full production pytest and 27 production Chromium tests (verified remotely via exact-head CI step conclusions and uploaded artifacts, not re-run locally here), human screen-reader/novice/physical-device testing, Safari/Firefox. No pass claim is made for those from local observation. A source scan is not treated as browser-runtime proof.

---

## 6. Merge readiness vs public readiness

**Merge readiness (development / release-package change): SAFE, with conditions.** The PR is a draft, mergeable/clean, has green CI on the exact head, changes only additive documentation and tests, leaves every production/pin/schema/CI path untouched, reproduces byte-identical static output, and preserves all original OpenCode research bytes. Nothing in the delta introduces a security, claim-integrity or custody regression.

**Public deployment / hackathon submission readiness: NOT READY.** The following remain owner/human/organizer gates, explicitly recorded as blocked in `M45_R3_ACCEPTANCE.md:177-193` and not resolved by this review: own-source license and third-party/content rights; organizer-confirmed judge-access method and rehearsal; human novice install and auditory screen-reader trials; final captioned video, submission copy, eligibility/contact and rights declarations; hosted public execution and any submission action. F-01 and F-02 are documentation-accuracy defects that should be fixed before the package is presented as a release to first-time users.

---

## 7. Recommendation

**CONDITIONAL PASS.**

PR #11 **is safe to merge as a development/release-package change**, conditional on:
1. Fixing **F-01** so the R3 showcase-bearing pin (`1783b61…` or the exact final delivery SHA) is stated in the README/install path or the handoff it points to, with a clear explanation of why it differs from the accepted-runtime pin `b537eb6…`; then correcting **F-02**.
2. Preserving **F-03** as an explicit provenance limitation in any public-facing material; do not fabricate originals or relabel recorded evidence as CURRENT.
3. Keeping owner/legal/human/organizer gates (§6) as separate pre-deployment and pre-submission approvals.

No HIGH-severity finding, no new production or custody defect, and no evidence of weakened gates. **No merge, deploy, publish, license choice, signing, wallet action or submission was performed by this review.** Stop after independent delta verification.
