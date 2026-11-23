# Final handoff — P7-V1 independent acceptance review

## Ownership boundary

Review branch: `opencode/flip-visual-v1-independent-review`, created from exact PR head `006050d7b8349dca3c263da2e3f1112617706541` and pushed to `Technique-S/Flip`.
All review artifacts live only under `docs/evidence/visual-v1-independent-review/**`:

- `VISUAL_V1_INDEPENDENT_REVIEW.md` — main report, findings and verdict
- `PROJECTION_ATTACK_MATRIX.md` — 54 independent projection cases
- `RELEASE_GUARD_SECURITY_REVIEW.md` — adversarial release-guard analysis and blocking finding
- `ACCESSIBILITY_AND_USABILITY.md` — independent browser/a11y observations and untested scope
- `projection-attack-harness.mjs`, `projection.bundle.mjs`, `projection-attack-results.json`
- `release-guard-attack-harness.mjs`, `release-guard-attack-results.json`, `old-guard-self-tamper-check.mjs`
- `readonly-attack.spec.mjs`, `readonly-attack.config.mjs`

No production implementation, CI configuration, schema, fixture, existing test or accepted evidence was modified. The PR was not merged; no deploy, transaction, wallet, hosting, redesign or V2 work was performed.

## Exact revisions

- PR head verified (remote and local): `006050d7b8349dca3c263da2e3f1112617706541`
- Accepted main baseline: `7ecfb9b74933eacb03f1b6ebf7c18a13fd02230f`
- Approved architecture: `39322e49f9fb1aa83a726fe3bbe81921c7e0f21e`
- Review branch parent: the PR head above
- Final review commit SHA: reported in the chat handoff that accompanies this document (avoiding a self-referential hash inside the file).

Hosted exact-head CI independently verified through the GitHub API: workflow runs `45182811594` and `45182820732`; `contracts (ubuntu-latest)` and `contracts (windows-latest)` all `success` at `006050d7…`. Earlier failures `45181066145` / `45181184502` were at `cfb68b4…` and remain recorded as history, not as final-head results.

## Independent results summary

- Projection: 54/54 adversarial cases behaved as expected; request bytes unchanged in every case.
- Read-only enforcement: independent browser attack 1/1 pass; zero requests, zero page errors, stored request byte-identical.
- Workbench browser suite: 42/42 passed. Showcase/release-guard suite: 26/26 passed. Python: 702/702 passed.
- Frozen schema exporters 9/9, canonical parity checks 3/3, Ruff check/format clean, agent acceptance 10/10, portable review 26/26, smoke M1/M3 pass, frontend lint/build pass.
- Production bundle measured 567,908 B raw / 177,465 B gzip vs accepted-main baseline 278,735 B / 84,711 B built from a clean temporary worktree.
- Release guard: pristine checker passes (19 files / 130 links), but four independent adversarial tampers were **accepted** when they should have been rejected, including a newly introduced self-tamper/provenance-retarget bypass.

## Findings and verdict

Blocking: **RG-01** (`scripts/check_m45_release_package.mjs:98-113`) — checker self-tamper, pinned-commit retarget and historical-exception expansion are not detected; the pre-PR checker did detect its own tamper. High: **RG-02** (`:83-94,106`) — static artifact + inventory checksums are not pinned to the historical commit, so coordinated tamper passes. Medium: **RG-03** (new tests omit those failure modes), **UX-01** (`Composer.tsx:111,274,285` — build/navigation hidden in Visual mode). Low: **PROJ-01** (alias syntax unvalidated), **PROJ-02** (budget checked after materialisation). Informational: bundle growth and untested human/performance gates.

**Verdict: FAIL** for V1 merge at this head.

## Separate status assessments

1. **V1 merge readiness — NOT READY.** The projection and read-only behaviour are acceptable, but the release-guard bypass is a blocking finding. Merge only after RG-01/RG-02 are corrected, RG-03 cases added, and exact-head CI re-run on the corrected head.
2. **P7 milestone completeness — NOT COMPLETE.** V1 is the first increment. Editing/history, REF internals, visual Canary, versioned visual portability, guide integration and V7 measurement/human trials remain outstanding per the approved architecture.
3. **P8 readiness — NOT READY.** No dedicated guide, two-path curriculum, term catalog, stable anchors, progress/recovery lessons or capstone exist in this PR.
4. **Public release readiness — NOT READY.** P3/P4 gaps, rights/credential/human-accessibility dependencies and the release-guard finding remain. Nothing in this review authorises publication, deployment or solver hosting.

V1 acceptance, if achieved after corrections, must not be represented as P7 or P8 completion.

## Required next action

Keep PR #12 open and unmerged. Return the branch to the implementation owner for the four corrections in `RELEASE_GUARD_SECURITY_REVIEW.md`, then perform a fresh independent review of the corrected exact head. No other work should start from this review.
