# Human trial and manual screen-reader protocol

**Status: PROTOCOL ONLY — NOT EXECUTED. Date 2026-11-22.**
No first-time developer study and no human auditory screen-reader session was run by this review or by Codex R2.
Automated axe/keyboard/layout tests are engineering evidence and do not substitute for listening or for an
unassisted novice trial. A completed protocol with real observations is required before either gate can be PASS.

## Part A — First-time developer trial

### A1. Tester and environment record

Record before starting: tester ID (self-chosen alias), date, OS/version/architecture, supported Windows x64 or
Linux distribution, CPU/RAM, browser/version if UI used, shell, network/proxy constraints, prior Flip/TapeOut
experience (none / some / experienced), and whether the tester received any coaching. Use a clean account and
a directory outside the developer worktree. Do not use personal browser sessions or real wallet material.

### A2. Setup tasks (measure each independently)

| ID | Task | Start trigger | Stop trigger | Measurable result |
|---|---|---|---|---|
| U-01 | Install/verify prerequisites | "Begin" | `uv --version`, `node --version` show required majors/minors | CPython 3.14.6 and uv 0.9.11 available; Node 24.18.0/npm 11.16.0 available; record exact output and time |
| U-02 | Obtain pinned source | Given repository URL and pinned SHA `b537eb6` | Checkout complete | Exact HEAD SHA observed; time; any clone error verbatim |
| U-03 | Locked install | Command given | Process exits | `uv sync --locked` exit code/time; no manual dependency edits |
| U-04 | Frontend install/build | Command given | Process exits | `npm ci --prefix apps/web`, `npm run build --prefix apps/web` exit codes/time; artifact sizes |
| U-05 | Native solver opt-in | Explain that native HTTP operations are disabled by default | Launcher ready | Tester sets `FLIP_LOCAL_SOLVER=1` before launch; record whether they needed a hint |
| U-06 | Launch and open | Launch command given | Page loads at `127.0.0.1:8000` | Loopback URL only; no tunnel/proxy; time; any error |
| U-07 | Offline CLI smoke | Commands from reviewed quickstart | Final verify-bundle completes | Exit codes: sample 0, compose 0, compare (DIFFERENT) 1, export 0, verify 0; time; no coaching |

A setup failure is recorded with the exact command, output and time. Timeout/resource limit ⇒ UNKNOWN, not PASS.
Do not fix the tester's environment mid-trial; record what happened, then optionally run a separate coached session.

### A3. Unassisted task results

Give only the reviewed quickstart and the task statement; do not point to specific buttons beyond the task goal.

| ID | Task | Expected observable result | Measure |
|---|---|---|---|
| U-08 | Open archived sample and compose | 81-byte netlist, expanded truth table with four input rows | completed unaided yes/no; time; wrong clicks; whether HISTORICAL label was noticed |
| U-09 | Introduce output swap and run Wiring Canary | DIFFERENT plus a witness replayed by the independent evaluator | exit/status observed; tester can state what DIFFERENT proves and does not prove |
| U-10 | Inspect connection paths | Relevant paths shown with ambiguous-cause wording | tester does not claim a unique defective wire |
| U-11 | Verify a declared-prior correction | Separate proposal → verified → explicit local apply → second comparison | tester explains why apply is separate; no claim of autonomous repair |
| U-12 | Save complete portable project and replay | Project, receipt and evidence are separate files; CLI/browser replay reruns proof | files retained; engine identity/HISTORICAL understood; time |
| U-13 | Agent-portable bounded workflow on saved revision | Exact pins; mismatch stop unless explicitly continued; no revision until explicit open | tester identifies terminal STOP_AUTHORIZATION and exit 9 as a stop, not success |
| U-14 | Publication request | STOP_AUTHORIZATION with one stop log and no later operation | tester states that no wallet/sign/transaction/spend occurred |

### A4. Scoring and acceptance

- Target: at least 4/5 testers complete U-08–U-12 unaided with correct result interpretation; **target, not a measured claim**.
- Record absolute counts and times; do not convert a target into a result.
- A task is PASS only if the observable result and the tester's explanation both match the expected semantics.
- A correct output with a false claim (e.g., "EQUIVALENT means the circuit is correct") is FAIL for interpretation.
- Any wallet/signing/publication request during the trial is an immediate STOP and is recorded as a finding.

### A5. Recording template (one row per task)

```text
tester_alias, date, task_id, unaided (yes/no), time_seconds, exit_code/status,
observed_output, tester_explanation, assistance_given, failure_or_confusion, workaround, evidence_path
```

Retain only consented, non-sensitive artifacts. Do not store secrets, personal aliases or unrelated browser data.

## Part B — Manual screen-reader checklist

### B1. Environment record

Record OS/version, browser/version, screen reader and version (NVDA or Narrator on the supported OS), speech
rate/verbosity, keyboard layout, zoom level, and tester familiarity. Use the supported local launcher; do not
bypass the Computer Use/browser protection or substitute an automated accessibility tree for spoken output.

### B2. Required spoken-output cases

| ID | Case | Expected spoken/announced content | Record |
|---|---|---|---|
| SR-01 | Landmarks and headings | Page name, main navigation, current step, heading levels announced in logical order | expected vs actual speech; order; misses |
| SR-02 | Keyboard-only navigation to sample | Focus starts at a meaningful control; tab order follows the workflow; visible and spoken focus agree | focus trail; skips; traps |
| SR-03 | Sample load failure / wrong chain | Error announced immediately with actionable text; not color-only | speech; focus recovery |
| SR-04 | Import error | Structured error class and reason announced; invalid input not treated as proof verdict | speech; focus |
| SR-05 | EQUIVALENT result | Status, oracle/reference mode, scope (pairwise/stateless) and HISTORICAL freshness announced together | speech; tester interpretation |
| SR-06 | DIFFERENT witness table | Table caption, column headers, input bits and both mapped outputs announced per row; replay confirmation stated | table navigation path; speech; duplicates/missing headers |
| SR-07 | UNKNOWN / timeout / resource limit | Reason code and "inconclusive, not EQUIVALENT" announced; retry guidance if any | speech; no false success |
| SR-08 | Connection diagnostics | Relevant-path table read with numeric pins; ambiguous-cause wording spoken | speech; no unique-cause claim |
| SR-09 | Correction proposal and verify | Proposed revision clearly distinguished from current; verify result and trust declaration announced | speech; tester can explain separation |
| SR-10 | Apply and revert | Explicit local apply announced; original comparison retained; revert outcome spoken | speech; focus after action |
| SR-11 | New revision selection | Original stays active until explicit "Open verified revision"; selection confirmed | speech; tester understands no auto-switch |
| SR-12 | Provenance labels | HISTORICAL/STALE/RECORDED and engine identity announced near results; CURRENT not inferred from checksum | speech; tester explanation |
| SR-13 | Live regions and timing | Status changes announced once, not repeated endlessly; focus lands on new heading/error | timing; repetition count |
| SR-14 | Cancellation | Cancelled state and partial-log guidance announced; late results not accepted | speech; tester interpretation |
| SR-15 | STOP_AUTHORIZATION | Terminal stop, no permission granted, exit 9 meaning spoken; no "published/deployed" wording | speech; tester explanation |
| SR-16 | Portable downloads | Separate project/evidence/receipt files and names announced; storage-quota error spoken if triggered | speech; file list |

### B3. Acceptance rule

Each case records `expected_speech`, `actual_speech`, `result` (PASS / FAIL / UNKNOWN), `workaround`,
`tool_versions`, `tester_alias`, `date`. A case is PASS only when the information is actually conveyed and the
tester can restate the correct meaning. Missing or garbled speech is FAIL, not a note. Timeout or unavailable
assistive technology is UNKNOWN. No full WCAG conformity claim follows from these cases; they are targeted
release evidence for the listed workflows.

### B4. Safety and privacy

No personal browser session, wallet, credentials or live submission form is used. Keep recordings consented
and local; scrub aliases and personal data before sharing. R2's automated axe, focus and narrow-layout tests
remain separate PASS evidence and do not satisfy this protocol.

## Part C — Gate disposition

| Gate | Status | Evidence required to flip |
|---|---|---|
| First-time developer trial | NOT TESTED | Completed A1–A5 records for at least five testers against the reviewed quickstart |
| Manual screen-reader speech | NOT TESTED | Completed B1–B4 records for all 16 cases on supported OS/browser |
| Judge-access rehearsal | NOT TESTED | Organizer-confirmed method plus neutral-network tester run |
