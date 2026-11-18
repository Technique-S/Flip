# M4.5-R — moderated five-developer trial (materials only)

**Status: TEST MATERIALS. No participants were recruited, no session was run,
and no completion rate, timing or quote is reported.** This document is a
ready-to-use protocol for a future moderator. Test at the accepted baseline
`09f2482beae84be6d919ecd6957c4153d1924cca`.

## 1. Recruitment criteria

Target **five** participants; record the actual number recruited and completed.

Primary persona (at least three of five):
- Developer familiar with EVM tooling and basic digital logic.
- Has used or evaluated TapeOut circuits, or can be shown a short primer.
- Has a TapeOut processor address/circuit ID or is willing to use the archived
  sample.

Secondary persona (remaining participants):
- Circuit author/maintainer who has refactored a circuit and needed evidence.

Exclusions to record, not silently filter:
- No prior exposure to Flip (ask before the session).
- Screen-reader or motor-impaired participants are **welcome**; this trial's
  accessibility observations are supplementary to, not a replacement for,
  dedicated assistive-technology testing.
- Participation is voluntary; no payment or wallet connection is requested.

## 2. Environment and setup

```sh
uv sync --locked
npm ci --prefix apps/web
npm run build --prefix apps/web
FLIP_LOCAL_SOLVER=1 uv run --frozen python -m flip_api.local --port 8000
```

Use a clean browser profile. Provide the project file
`fixtures/m5-demo/cli-run/mutation.json` only at the stage where it is needed.
Do not mention expected verdicts before the task.

## 3. Moderator script and tasks

**T0 — Orientation (3 min).** "This is a local circuit workbench. Please think
aloud. I will not help unless you are blocked for more than two minutes. There
is no wallet and no transaction."

**T1 — Sample walkthrough (6 min).** From Sources, open the historical sample;
build the netlist; expand the truth table; evaluate four inputs.
Record: did the participant find **Open sample** unaided? Did they identify the
historical label and block?

**T2 — Understand the pin map (6 min).** Explain what `nand0 [0]` means, map an
external input to a REF input, and say what the output order is before changing
anything. Record the exact words used.

**T3 — Mutation and DIFFERENT (8 min).** Apply **Swap outputs**, run Wiring
Canary, then explain the witness: which input, what reference output, what
candidate output. Ask: "Which circuit is wrong?"
Record: correct answer is "neither can be judged without a trusted oracle; the
behaviours differ".

**T4 — Restore and EQUIVALENT (5 min).** **Restore original**, rerun. Ask: "What
does EQUIVALENT prove, and what does it not prove?"
Record: must mention pinned stateless semantics, mapping, and that it is not a
correctness/security claim.

**T5 — UNKNOWN (4 min).** Set Timeout to 1 ms, run, then read the result. Ask:
"Is this a pass, a failure, or inconclusive?" Correct: inconclusive/UNKNOWN;
retry with a higher timeout.

**T6 — Evidence (8 min).** Save the project, export evidence (JSON), then replay
the bundle against an independently chosen project via CLI (moderator may run
the CLI while the participant reads the output). Ask: "Does this file prove the
result is current onchain?" Correct: no, it is recomputable historical evidence.

**T7 — Optional import (5 min).** With a controlled loopback RPC double only,
import a processor/circuit ID, inspect metadata and revalidate. Record whether
the participant distinguishes CURRENT from HISTORICAL.

## 4. Measurements (fill in during the session; leave blank now)

| Metric | How to record | Target / threshold |
| --- | --- | --- |
| Task completion T1–T6 | binary per task, unassisted vs assisted | target 4/5 complete flagship tasks unaided |
| Time to completion | minutes per task, start at instruction end | report median; do not claim a 10× improvement |
| Error count | wrong clicks, wrong pin, wrong interpretation | count per task |
| Pin-mapping comprehension | T2 explanation scored: correct / partial / wrong | report distribution |
| EQUIVALENT comprehension | T4: scope stated / correctness overclaimed | flag any correctness overclaim |
| DIFFERENT comprehension | T3: difference vs fault | flag "user circuit is wrong" answers |
| UNKNOWN comprehension | T5: inconclusive vs equivalent/failed | must not say equivalent |
| Evidence export/replay | T6: export found and replay explained | flag "file is a certificate/current" answers |
| Historical/current distinction | T1/T6/T7 labels | flag any "live verified now" statement |

## 5. Open-ended questions

1. What did you think the tool was for after the first screen?
2. Where did you feel unsure about which pin connected to which?
3. What did "DIFFERENT" mean to you before you read the explanation?
4. Did the counterexample table let you reproduce the finding? What was missing?
5. Did you understand why a historical result cannot be called current?
6. Was the JSON export easy to find? What would you expect to do with it?
7. Would you use this in your next circuit refactor? Why or why not?
8. What would you change first?

## 6. Data handling and honesty rules

- Store notes locally with participant IDs only (P1–P5); no wallet addresses,
  private keys, employer secrets or session recordings without written consent.
- Report **observed** behaviour only. If fewer than five sessions are completed,
  state the actual number and do not extrapolate.
- Do not convert task targets into achieved results. A "4/5 target" in the PRD
  remains a target until sessions actually occur.
- Separate objective usability defects (cannot complete a task) from
  preferences (would prefer a different layout).

## 7. Required evidence to attach after the trial

- Signed consent record or explicit opt-in note per participant.
- Per-task timing/completion sheet.
- Verbatim answers to comprehension checks and open questions.
- Screenshots of any blocking state, with personal data redacted.
- A summary that distinguishes observed results from targets.

No such evidence exists in this deliverable.
