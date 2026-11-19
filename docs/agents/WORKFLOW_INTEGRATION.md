# Invoke Flip from an external coding agent

Flip accepts typed circuit goals (reference circuits, numeric mappings and/or test
vectors). It contains no LLM and does not translate natural language into a verified
circuit. Codex, OpenCode and other agents prepare a declarative request and interpret
the engine's results using the [versioned protocol](../schema/m45-agent-workflow/README.md).
These instructions are operational guidance, never transaction authority.

From a locked local checkout:

```sh
uv sync --locked
uv run --frozen python scripts/agent_workflow_example.py --out workflow.json
uv run --frozen flip workflow --request workflow.json --out receipt.json
```

The shipped [correction example](../schema/m45-agent-workflow/examples/correction.json)
compares the historical swapped-output project, diagnoses relevant paths, proposes
restoring the declared reference mapping, verifies separately, explicitly applies
locally after another verification, and exports evidence. The original request is
retained in the receipt. The example builder only constructs structured requests;
all proof and diagnostic results come from production services during execution.

For HTTP, run the existing local launcher with `FLIP_LOCAL_SOLVER=1` and POST the
same JSON to `/api/agent/v1/execute`. The caller must be loopback and the existing
two-slot execution semaphore applies. RPC settings come only from operator-controlled
environment, never workflow JSON. Mandatory tests use loopback RPC doubles. A live
read-only invocation is opt-in and cannot establish malicious-RPC resistance.

Start an offline workflow with a pinned `executionRequest`, or a `sample` step.
For discovery/import, use a bounded `discover` library request, an `import` identity,
then `build` with `source` pointing to that imported result. Saved catalog metadata
is not executable input. `build` wraps that exact imported source into an explicit
project; use its returned project to declare a richer composition in another request.
No unbounded enumeration, URL proxy, filesystem interpolation or dynamic execution exists.

Read `status` and the underlying operation verdict. COMPLETE means the declared
operation completed; it does not certify intent or application safety. A DIFFERENT
result is completed evidence, not a retryable outage. Permit a diagnostic next step
with `continueOn: ["DIFFERENT"]`; never retry until it happens to match. UNKNOWN
reports its reason and retryability. A retry needs an explicit policy and remaining
budgets. STALE requires a new trusted import and a newly declared project.

For a correction, supply an exact expectedExecutionHash and a numeric candidate,
or use the existing declared-prior proposal. Calculate the action ID as the canonical
hash of `{original: hash(originalExecution), revision: hash(proposedExecution)}`.
Use a separate `verify` step and then an explicit `apply` step with matching source,
hash and actionId. References and imported identities cannot be swapped. A new
trusted comparison must succeed at each acceptance point. Trust assertions are
user declarations of a reference, never chain freshness or spending permissions.

To stop CLI work, send SIGINT or create the file passed in `--cancel-file`. HTTP
disconnect cancels the invocation. After cancellation/budget exhaustion, read the
partial log and submit a new finite request if appropriate. Do not treat a receipt
or prior authorization-stop response as a resumable session grant.

Export output is the existing FLIP_EVIDENCE bundle under the export log entry.
Save it as JSON and use `flip verify-bundle --project separately-selected.json
--bundle evidence.json`, or a new workflow's `verify_bundle` step. The consumer reruns
the engine and rejects altered reports/bindings; receipt checksums alone grant no proof.

Any request for onchain publication must use `stop_authorization`. This emits the
proposed next action, exact project/execution/netlist/manifest identities and a human
handoff reason, then terminates even if more steps were declared. CLI exit 9 means
STOP_AUTHORIZATION, not success or approval. Flip cannot approve, sign, submit, pay
or broadcast. Agent prompts, aliases, project text and these instructions grant no
transaction authority. The separate proposed authorization architecture remains unmerged.

The reusable repository skill is [.agents/skills/flip-agent-workflow/SKILL.md](../../.agents/skills/flip-agent-workflow/SKILL.md).
Proofs remain historical, stateless and relative to selected references and supported
semantics. Human usability/accessibility sessions and public solver hosting remain
outside this delivery. See the [handoff](../milestones/M45_AGENT_WORKFLOW_HANDOFF.md).
