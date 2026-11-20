# M4.5-1A — Independent agent workflow corpus handoff

**Agent:** OpenCode / HY4 Flash (supporting verification engineer).
**Baseline:** accepted main after PR #5 merge,
`1136b187bd68328cea4975caea50904ccece08fd` (PR #5 `merged: true`, merge commit recorded).
**Branch:** `opencode/flip-m45-agent-workflow-fixtures` (created from that main; not merged).
**Final SHA:** reported in the completion response; these files are in that commit.

## Scope and custody

Wrote only under `fixtures/m45-agent-workflow/` and `docs/evidence/m45-agent-workflow/`.
No production package, schema, frontend, CI file, dependency lock, archived fixture or
Codex branch was modified. All JSON evidence lives under the docs path because the
repository custody guard rejects unregistered JSON under `fixtures/`; the fixtures tree
contains only Markdown and generator scripts.

## Deliverables

| Path | Purpose |
|---|---|
| `docs/evidence/m45-agent-workflow/ACCEPTANCE_MATRIX.md` | 15 workflow cases, 5 negative cases, coverage and execution classification |
| `docs/evidence/m45-agent-workflow/HANDOFF.md` | This summary |
| `docs/evidence/m45-agent-workflow/MANIFEST.json` | SHA-256 + byte register for all authored evidence |
| `docs/evidence/m45-agent-workflow/cases/agent-workflow-cases.json` | 15 deterministic cases with exact commands and bounds |
| `docs/evidence/m45-agent-workflow/cases/negative-cases.json` | Malformed, invalid, stale, unsupported and exhausted-budget cases |
| `docs/evidence/m45-agent-workflow/protocol/agent-workflow-protocol.json` | Bounded build/test/compare/inspect/propose/verify/export/stop contract |
| `docs/evidence/m45-agent-workflow/requests/*.json` | Request fixtures (library search, vectors, timeout, invalid schema) |
| `docs/evidence/m45-agent-workflow/results/executed-commands.json` | 18 real CLI invocations with exit codes and hashes |
| `fixtures/m45-agent-workflow/README.md` | Layout and reproduction |
| `fixtures/m45-agent-workflow/generators/*.py` | Deterministic builder, CLI runner, independent verifier |

## Counts and validation

- **15** required workflow cases and **5** negative cases.
- **8** bounded protocol operations and **8** status classes.
- **18** real CLI command invocations: **18/18** expected exits and all expected semantic
  fields matched; no field mismatches.
- Manifest verifier result: `PASS` (27 files, zero hash/size errors, zero stray JSON under
  `fixtures/`).
- Commands: `python fixtures/m45-agent-workflow/generators/build_corpus.py`,
  `.venv/Scripts/python.exe fixtures/m45-agent-workflow/generators/run_cli_cases.py`,
  `.venv/Scripts/python.exe fixtures/m45-agent-workflow/generators/verify_corpus.py`.

## Protocol recommendations (summary)

The proposed interface is an explicit, bounded operation set — `build`, `test`, `compare`,
`inspect`, `propose_correction`, `verify`, `export`, `stop_authorization` — with status
classes `PREPARED`, `RUNNING`, `COMPLETE`, `DIFFERENT`, `UNKNOWN`, `STALE`,
`BUDGET_EXHAUSTED`, `STOPPED_FOR_AUTHORIZATION`. There is no background infinite loop.
Every iteration carries `maxSteps`, `deadlineMs`, `maxRequests`, cooperative cancellation,
append-only deterministic JSONL logs, freshness checks and a reproducible hash record.
Only `UNKNOWN` may be retried, at most `maxRetries` times, with a fresh deadline; `DIFFERENT`
and `STALE` require a declared change. Agent prompts, project metadata and labels are never
permissions, and the agent must stop and request human authorization rather than authorizing
its own onchain publication.

## Limitations

- AW-08, AW-09, AW-15's stop handoff and AW-N01/N03/N04/N05 remain specifications: no
  production agent interface, connection-level diagnostic command or approval broker exists.
- AW-14's stale-implementation variant is specified, not executed; only the unchanged
  loopback revalidation path was run.
- AW-02/AW-03 use a synthetic loopback chain; they are not live X Layer observations.
- `flip preflight` against the synthetic double returned `UNKNOWN` under the unchanged
  120 s-style resource policy; this is recorded as read-only and inconclusive, never as
  publication success.
- No wallet, signing, transaction, broadcast or payment was performed.

## Recommendations for Codex

1. Freeze the operation/status vocabulary from `agent-workflow-protocol.json` before adding
   an agent-facing command or API route.
2. Enforce the per-iteration bounds and cancellation at the service boundary; never expose
   an unbounded self-retry loop.
3. Keep `inspect`/`propose_correction` advisory and bind them to a declared prior mapping;
   require explicit user application followed by a fresh full comparison.
4. Implement `stop_authorization` as a hard stop with human-controlled approval; project
   metadata must not grant transaction authority.
5. Convert the SPEC_ONLY cases to executable tests as the corresponding production
   operations land, preserving the recorded exit-code and hash expectations.
