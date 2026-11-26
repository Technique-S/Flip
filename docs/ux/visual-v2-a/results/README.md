# P7-V2-A implementation evidence

See [handoff and acceptance matrix](../../../milestones/P7_V2_A_HANDOFF.md). Source baseline `fc9c0c1bcb2557169dd89af0c3b2c5a7628c9adf`; final production implementation `2826e4a5778f32d6a6fc1a3ca965eb924b46f29e`. The following evidence commit is additive documentation only.

- `EXPLICIT_INPUT_AUTHORIZATION.md`: exact owner approval resolving the unchanged Phase 1 checkpoint.
- `browser-final-70.json` / `.txt`: complete successful local browser run, 70 expected, no failures/skips/flakes. Includes 44 unchanged inherited cases and 26 new cases.
- `browser-initial-failures.json` / `.txt`: original 67-pass/2-failure run. The inherited debugger overflow was corrected in scoped fieldset styling; the unchanged portable-agent test exceeded its existing 60-second limit. `inherited-retry.txt` records both passing afterwards, without test/timeout changes. Original trace paths in the report refer to local scratch; raw traces are not committed.
- `keyboard-retry.txt`: corrected new keyboard test sequence checks actual values/focus and passes; accepted tests are unchanged.
- `post-implementation-checks.json`: exact commands, durations, exit codes and output for showcase/build/release bootstrap/integrity, Ruff, nine schemas, three canonical parity checks and custody at the initial implementation commit. `implementation-custody.txt` is the clean scan at the final production implementation.
- `checkpoint-local-33-commands.json` / `checkpoint-python-summary.json`: prior complete local workflow, including 702 Python passes, with explicit source binding. These are not substituted for final-head CI. Final-head Windows/Ubuntu full workflow results and exact run links are recorded on draft PR #14 after completion.
- `canonical-parity.json`: original fresh browser attachment, byte-identical to the accepted V1 capture.
- `provenance.json`: source/blob digests, unchanged protected-path diff and accepted-test diff, canonical capture digest and browser stats. `execution-bindings.json` distinguishes every execution phase.
- `screenshots.json`: original real UI screenshot SHA-256, dimensions, source binding and retained absolute local paths. Raw PNGs remain in ignored `.test-tmp/v2a-screenshots/`; no binary exception or encoded-image workaround was introduced. Reproduce screenshots using `npm test --prefix apps/web -- --grep V2-A`. They are local artifacts, not claimed hosted by the unchanged CI upload configuration.
- `ui-detector.json`: initial scoped mechanical UI review produced no findings. Actual final desktop/narrow screenshots and automated axe/overflow/keyboard tests provide render evidence; real screen-reader/physical-device trials remain untested.
- `MANIFEST.json`: byte count/SHA-256 index, excluding itself. Hashes describe original Git blob bytes; use `git show`, `git archive` or `core.autocrlf=false` to avoid Windows checkout line-ending conversion when verifying raw bytes. This index is not an independent security trust root.

No historical fixture/evidence, canonical schema, dependency lock, Python/API/CLI runtime, workflow, release trust metadata/checker or repository protection was changed. SEC-01 remains OPEN/HIGH. No V2-B/C, public hosting, transaction, deployment or own merge.
