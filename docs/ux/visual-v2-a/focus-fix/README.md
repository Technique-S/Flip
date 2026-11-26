# Final V2-A focus correction and acceptance

This additive evidence supersedes the earlier 70-case disposition in `../results` without changing those original reports/manifests. Final production source: `b23d3dcf8f98e9b95cd0bc8ca8fbf612045e1daa`. See [current handoff](../../../milestones/P7_V2_A_HANDOFF.md).

Initial final-head push CI run 45896495418 at `e92ae1e21c8c3ea0fd7e713c1a643ed642a906e7` failed the unchanged inherited Advanced keyboard journey: `Source for part2 [0]` did not retain row selection. Ubuntu recorded 69 passes / 1 failure; Windows was cancelled by the unchanged matrix fail-fast policy. The original job-log capture is retained as `ci-initial-ubuntu-failure.txt`; it is evidence data, never a script to execute.

The Advanced draft could expose a future row while disabled/pending, and the generic commit focus effect could redirect focus to NAND controls. The fix renders the accepted recipe during pending validation, leaves failed drafts visible after rejection, and does not redirect ordinary Advanced commits. An origin-focus ref restores an existing field only when focus otherwise fell to the document body, never over a user's valid new focus. Cancellation/project replacement clears that ref.

Two additional tests cover the held real compiler response/new-row focus sequence and existing-field focus after validation. The complete corrected run is 72/72 passed: 44 unchanged inherited cases plus 28 new cases, no skips/flakes/unexpected results. `browser-final-72.json` / `.txt` are original complete local results; `focus-regression-targeted.txt` retains the deterministic target run. Final-head hosted matrices are recorded on PR #14 only after completion; the earlier checkpoint/head greens are not substituted.

`canonical-parity.json` remains byte-identical to accepted V1. `provenance.json` binds source files, the original failure and final run. `screenshots.json` records real final-source captures retained in ignored `.test-tmp/v2a-focus-fix-screenshots/`; older source captures in `../results/screenshots.json` remain separately retained. PNGs/encoded images are not committed and no custody exception was added. `MANIFEST.json` binds original Git blob bytes except itself; use Git blob bytes or `core.autocrlf=false` to validate without checkout newline translation.

No accepted test, timeout, fixture, canonical schema, backend/solver, dependency, workflow, trust metadata or guard was changed. SEC-01 remains OPEN/HIGH. Keep the draft PR unmerged for independent review.
