# Bounded agent workflow protocol 1.0.0

`m45-agent-workflow-1.0.0` is additive. All M1/M2/M3/library/debugging schemas stay
unchanged. [Request](1.0.0/request.schema.json) and [result](1.0.0/result.schema.json)
are exported from `flip_core.agent_models`, with drift checks in Windows/Linux CI.
Read the [integration guide](../../agents/WORKFLOW_INTEGRATION.md) for invocation.

A request contains an optional existing M3 `executionRequest`, a finite ordered
`steps` list, `budget`, and `stopOn`. IDs are unique; `source` selects a preceding
operation's actual output. Input cannot contain saved result statuses, permissions,
approval tokens, shell commands, Python code, arbitrary import paths or RPC methods.
The controller is deterministic orchestration, not natural-language synthesis.

| Operation | Input beyond current execution | Output / meaning |
|---|---|---|
| sample | historical variant | Existing pinned M3 execution; selects current project |
| discover | typed libraryRequest (discover/circuits/search only) | Bounded catalog; incomplete pages remain UNKNOWN/incomplete |
| import | typed circuit identity, optional blockNumber | Fresh M2 read; no saved catalog grants execution |
| build | optional source pointing to an import | Existing compiler output; a selected import is wrapped as a project |
| test | explicit vectors | Existing VECTORS_MATCH/MISMATCH, with declared coverage |
| compare | current execution | Existing replayed DIFFERENT, EQUIVALENT or UNKNOWN |
| inspect | current execution | Existing bounded diagnostics; structural relevance is not fault attribution |
| propose_correction | expectedExecutionHash; optional candidate / actionId | Separate CANDIDATE_ACTION; never edits current project |
| verify | proposal source, exact expectedExecutionHash and actionId | New comparison; VERIFIED_CORRECTION only after EQUIVALENT |
| apply | verification source, exact expectedExecutionHash and actionId | Reverify again, then explicitly select the separate local revision |
| revalidate | optional import source, otherwise current imports | Fresh M2 observations; changed implementation returns STALE and stops |
| export | current execution | Existing FLIP_EVIDENCE from a new comparison; no live observation |
| verify_bundle | one prior export source or external bundle | Existing consumer recomputes against independently selected execution |
| stop_authorization | current execution | Terminal STOP_AUTHORIZATION identifying exact artifacts and proposed action |

Correction proposals require TRUSTED_REFERENCE and a declared trust assertion.
Without a supplied candidate, the existing debugger can restore a declared local
prior with matching topology. An external agent can instead supply a structured
candidate under the existing compiler schema. Only candidate wiring may change;
oracle, imports, source bindings, identity, intent and limits must match exactly.
Action IDs hash the original and proposed execution requests. No persisted
VERIFIED_CORRECTION is consumed as authority: source outputs are process-local,
verification recomputes, and apply recomputes once more. A later workflow must
declare its project again. The receipt preserves the original and revised execution
requests, subject to its explicit byte budget; hashes always identify both.

The eight proposed corpus operations are retained. The proposed eight status classes
map directly except `STOPPED_FOR_AUTHORIZATION` is named `STOP_AUTHORIZATION`, as
required by the production mission. Two explicit terminal outcomes, CANCELLED and
INVALID_INPUT, avoid mislabeling these as proof verdicts. PREPARED and RUNNING are
internal lifecycle states; the synchronous endpoint returns only final outcomes.

| Status | Controller behavior / CLI exit |
|---|---|
| COMPLETE | Declared operation completed, not a claim of correctness / 0 |
| DIFFERENT | Verified difference or vector mismatch; stops unless continueOn explicitly permits the next step / 1 |
| UNKNOWN | Inconclusive, unsupported, service failure or incomplete catalog; explicit continuation required / 2 |
| STALE | Exact bindings or implementation changed; reimport/new request / 7 |
| BUDGET_EXHAUSTED | Deadline, iteration, tool, RPC or receipt ceiling reached / 2 |
| STOP_AUTHORIZATION | Terminal publication handoff; no retry or resumption / 9 |
| CANCELLED | Stop active work, discard late results; new request required / 2 |
| INVALID_INPUT | Invalid operation arguments or selected artifact / 3 |

Malformed protocol/schema/JSON input is rejected with the existing INVALID_INPUT
error envelope (CLI 3 / HTTP 422), not an invented verification verdict. An oversized
request is CLI 2 / HTTP 413. Operational outcomes use HTTP 200 and their typed status;
opt-in/loopback failures retain the existing HTTP 501 gate. Concurrency is HTTP 429.

Each log entry includes step, operation, attempt, status, error class, retryability,
inputHash, semantic outputHash, projectHash, executionHash, cumulative usage, previousHash
and entryHash. Errors include recovery guidance. `usage.iterations` and `toolRequests`
charge every attempted operation, including retries. `rpcRequests` counts wire attempts
(including transport retries), not only successful reads. If a worker is interrupted,
its full reserved RPC allowance is charged and labeled RESERVED_ON_INTERRUPTION.
No charged budget is refunded or reset between steps. All counters have hard maxima.

Default workflow limits: 24 iterations, 32 tool requests, 256 RPC attempts, 300 seconds,
8 MiB receipt. Hard maxima: 64 iterations/tools, 8192 RPC attempts, 300 seconds,
16 MiB receipt. A step defaults to 15 seconds and 1 MiB output; maxima are 30 seconds
and 4 MiB. M2 import budgets and debug trace budgets are explicit per-step fields;
the selected project's frozen M3 proof budgets govern all comparisons. The wrapper
enforces a 512 MiB per-process operation ceiling; the nested solver retains its
unchanged 64 MiB/five-second and gate/depth limits. Windows allows only the venv
launcher, operation and solver processes in its kill-on-close Job. Linux uses
RLIMIT_AS/CPU and parent-death signals; cancelling kills/reaps the operation and its
parent-bound solver. Unsupported containment platforms fail closed.

Cancellation is polled every 50 ms while a worker runs. CLI SIGINT or `--cancel-file`
stops the invocation; API disconnect cancels the local invocation. No persistent
server job, background retry loop, resumable authorization grant or cancellation
token is created. Process startup/OS scheduling and cleanup add bounded overhead;
the overall deadline never resets on retry. Only explicitly retryable UNKNOWN
(RPC_UNAVAILABLE, SOLVER_TIMEOUT, WORKER_FAILURE) may retry, when both policy and
remaining budgets permit it; at most two retries per step. Limits, STALE,
DIFFERENT and STOP_AUTHORIZATION never auto-retry. Retrying does not modify project
limits; a changed budget or mapping requires a separate declared request.

`stopOn` can stop after EQUIVALENT or EXPORTED. It is optional so a declared export
can follow a successful correction. `continueOn` is not permission to submit anything;
it only allows the next declared local step after DIFFERENT/UNKNOWN. Terminal
states cannot be overridden. Prior diagnostic relevance is not unique causation.

`receiptHash` covers the full serialized receipt except itself, including raw service
observations. It is a checksum, not a certificate. `reproductionHash` and chained
entry hashes cover request, implementation bytes, stable semantic outputs, status
and accounting. Runtime measurements, verification timestamps and their dependent
bundle/diagnostic hashes are excluded from semantic outputHash, but remain in raw
outputs and the full receipt checksum. Same-version, same-platform successful local
replays have identical semantic traces. Timeout outcomes, live observations and
platform-specific native solver hashes need not match. Portable proof consumption
always uses the existing `verify-bundle` re-execution, never a receipt's COMPLETE flag.

Regenerate/check: `python -m flip_core.agent_schema_export --out
docs/schema/m45-agent-workflow/1.0.0 [--check]`.
