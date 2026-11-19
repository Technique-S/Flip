# M4.5-2D-C — Debugging acceptance and integration readiness

Assessment date: 2026-11-19. **Recommendation: PASS for independent review.**
**Merge approval: PENDING. Do not merge until OpenCode's independent production review
passes and required checks remain green.** This is Codex's implementation audit and
acceptance record; the independent fixture corpus is not approval of the production delta.

## Exact implementation and tested state

| Role | Revision |
|---|---|
| Accepted library main | `1136b187bd68328cea4975caea50904ccece08fd` |
| Delivered debugger implementation | `b9d3fc3f87d34cc6bd46e2a716504fe113f44f48` |
| Acceptance tests and tested state | `518bacecec824ebbc90ab465ca0d3c464fd1314c` |
| Original independent corpus | `8fc4efb71cb750cced98b4e88540796d665b616a` |
| History-preserving corpus integration | `3edfa2349df05621e7fa352b59de6f2a1d91b62f` |
| Delivery / PR head branch | `codex/flip-m45-debugging` |

Fetch and actual remote refs matched the requested main, implementation and fixture
revisions. The worktree was clean. Both main and the original corpus are ancestors of
the delivery head. No debugger production-review ref was available on origin during
this acceptance. The corpus's original reports retain their original fixture-only scope.

**No production defect was reproduced and no production fix was required.** Production
core/API/CLI/web source, all schema profiles, scripts, configuration, dependencies and
lockfiles remain byte-identical to the delivered implementation. Acceptance adds only
one Python regression file, one Chromium regression file, this report and its results.
No inherited test was changed, removed or skipped. No original evidence was rewritten.
The report/results commit after `518bace` contains documentation only; the final PR head
is separately recorded in the PR and delivery response.

[Machine-readable outcomes and original-file inventory](m45-debugging-acceptance/validation-results.json).

## Final implementation audit

| Area | Finding and evidence |
|---|---|
| Trusted identities and complete closure | M2 `ImportResult.content_bound` checks the manifest digest and every declared netlist byte hash. `validated_import` redecodes/resolves native REFs and compares actual snapshots/edges with the complete manifest. The compiler binds each source's manifest hash, identity, widths, block and execution environment; conflicting snapshots fail closed. New tests reject substituted hashes even after recomputing outer bindings, a valid but different import, and a self-consistent manifest that omits a native REF target. |
| NAND and nested REF paths | The production decoder/compiler/evaluator remain the trusted boundaries. The tracer walks actual compiled producers, individual REF output cones and input boundaries. Edges bind owner and source paths/hashes/identities, with numeric pins; generated compiler records are distinguished from recipe components. D07 and actual depth-limit tests exercise nested descent. |
| Repeated instances and maps | Repeated immutable children retain distinct instance paths. Both trace/index budgets count instance expansion. A 64-instance, 192-gate-per-design case hits the indexing bound independently of the gate cap. A nonidentity input/output-map test checks different physical candidate/reference trace roots against aligned differing bits. |
| Ambiguous causes | Cone membership is RELEVANT_CONNECTION, not a defective-wire proof. `uniqueFaultClaim` remains false. D10's distinct single-edge alternatives reproduce the same wrong truth table and stay ambiguous; multiple contributing connections are retained. A single declared prior candidate remains unverified until checked. |
| EQUIVALENT | No fault attribution, connection highlighting or correction actions. A previously successful action cannot be reused to claim a correction on an already applied/equivalent project. |
| UNKNOWN / incomplete / stale | Stale or unverified inputs, missing closure, failed witness replay, limits, timeout and worker failure produce no diagnostic attribution. Original-comparison UNKNOWN clears comparison/paths/actions. If only the proposed revision's worker fails, the original replayed mismatch may remain valid but the correction is explicitly UNKNOWN, never VERIFIED_CORRECTION. |
| Correction binding | Action IDs hash the exact original and proposed execution requests, including project, source/import, reference, intent, environment and mapping bindings. Proposals are regenerated from the original request; caller-provided witnesses, claimed results and replacement revisions are rejected. Changing the project ID, candidate, reference or a consistently rebound environment invalidates an old action ID. |
| Fresh correction verification | Every verification recompiles validated pinned data and runs a new trusted comparison. Two repeated checks execute the expected five real comparisons (one proposal comparison plus original/revision for each check). Actual crash/timeout injection during the correction phase cannot promote the action. Only a new EQUIVALENT revision receives VERIFIED_CORRECTION. |
| Apply / revert / stale responses | Local application is an explicit candidate edit and clears the workspace proof. Undo is bound to the applied execution and survives screen navigation. Existing tests discard in-flight results after edits; new tests invalidate an already selected proposal before apply and verify repeated apply/revert checks. Reload restores project data but not undo, diagnostics or proof status; comparison is required again. Original project-file bytes remain unchanged. |
| Interface semantic parity | Shared core execution supplies CLI and API results. Stable diagnostic semantics omit comparison timestamps/resource timings and bind engine/project/manifest identities. New tests compare complete core/CLI/API JSON for successful and forged correction actions, including exit codes. Existing production browser tests compare downloaded diagnostic JSON with CLI output on the same engine/runtime. |

## Corpus and adversarial regression

All ten cases run against production, including exhaustive table-row regeneration and
replay of the corpus's witness and the solver's independently selected witness:

| Case | Result |
|---|---|
| D01 swapped outputs | DIFFERENT; ambiguous mapped paths; browser checks a separate verified correction, local apply and revert. |
| D02 incorrect REF inputs | DIFFERENT; ambiguous input connections; declared prior-order correction independently re-compared. |
| D03 duplicate fan-out | DIFFERENT; one unverified prior candidate; correction requires a fresh EQUIVALENT result. |
| D04 unbound signal | Structural rejection by the production decoder; no behavioral/fault attribution. |
| D05 output rotation | DIFFERENT; multiple output paths. Nonidentity input/output-map regression also verifies aligned physical roots. |
| D06 simultaneous edits | DIFFERENT; multiple relevant mappings, ambiguous causes. |
| D07 nested references | DIFFERENT; path-qualified nested cone, unrelated child output excluded, depth budget enforced. |
| D08 equivalent rewiring | EQUIVALENT; no suspect connections or correction actions. |
| D09 contributing connections | DIFFERENT; multiple relevant paths remain ambiguous. |
| D10 indistinguishable causes | Both distinct alternatives reproduce the same wrong behavior; no unique cause or automatic correction claim. |

All eight guidance examples retain their intended classifications: G02/G05 require a new
production VERIFIED_CORRECTION; G01/G04/G06 remain candidate diagnostic actions;
G03/G07/G08 are explanation-only. OpenCode's 15 original files and all nine manifest
entries remain exact. Independent regeneration/verifier execution occurs in scratch;
its archived transcript is never overwritten or recredited as a production review.

Acceptance introduces **25 focused Python adversarial cases** and **two browser flows**:
altered witness bits; a false native SAT witness; untrusted report/revision inputs;
dependency-hash substitution; valid import substitution; incomplete closure; forged/stale
action identifiers; project/reference/environment changes; nested and repeated expansion
limits; actual contained worker timeout/crash; correction-phase worker failure;
repeated verification; mapped root ordering; success/rejection CLI/API parity;
selected-proposal invalidation; refresh/undo/proof-authority limits.

The new files are `packages/flip-core/tests/test_m45_debugging_adversarial.py` and
`apps/web/tests/debugging-acceptance.spec.ts`. They exercise production entry points and
the existing internal worker probes, without exposing probes in the public API or CLI.

## Executed checks

All results below are tied to acceptance test state `518bace`, whose production code
matches implementation `b9d3fc3` exactly.

| Check | Actual outcome |
|---|---|
| Focused debugger + adversarial Python | **58 passed**, no failures/errors/skips |
| Full local Python, including all 576 delivery tests | **601 passed**, no failures/errors/skips; terminal duration 355.41 s |
| Full local Chromium, including all 21 delivery cases | **23 passed**, no failures/skips/flakes; about 128.8 s |
| Linux CI Python / Chromium | **601 / 23 passed**, Python 72.648 s |
| Windows CI Python / Chromium | **601 / 23 passed**, Python 151.743 s |
| Ruff / format | PASS, **71** Python files formatted |
| Frontend | Biome lint, TypeScript and build PASS |
| Schema drift | M1, M2, M3, library 1.0/1.1, debugging 1.0 PASS; no contract changes |
| Canonical / interface parity | Six Node canonical vectors PASS; diagnosis and verified/rejected-correction core/CLI/API parity and browser/CLI parity PASS |
| Fixture custody | Original debugger 15 Git files / nine manifest entries and scratch regeneration PASS; discovery 19 manifest files / 12 cases PASS |
| Clean custody / credentials | Standalone guard PASS; zero credential findings; both CI platform guards PASS |
| Offline smoke | M1 real CLI/ASGI smoke and M3 compose/EQUIVALENT/DIFFERENT parity smoke PASS |

[Acceptance CI run 44563236625](https://github.com/Technique-S/Flip/actions/runs/44563236625)
is SUCCESS on Windows and Linux. Downloaded JUnit/M4 acceptance artifacts confirm the
exact commit, 601 Python tests with zero skips/errors/failures, and all 23 browser cases.
No production regression failed during this acceptance. Live network tests were not
made mandatory or used to establish these results; corpus identities remain synthetic.

The local full run used pytest's temporary `faulthandler_timeout=120` observation option
to aid investigation of the known local Git-custody delay. It does not terminate tests,
extend timeouts or change assertions; no repository pytest/CI configuration was changed.
The current Git custody test passed in **119.952 s**. Its earlier 10,879 s anomaly remains
tracked as D-RUNNER-001, not declared fixed. The inherited scratch-regeneration test
passed in **81.370 s**, with its original **120-second** inner limit unchanged.
F03-PERF-001 remains open in [the library follow-ups](M45_LIBRARY_FOLLOWUPS.md).

## Security, trust limits and known UI limitations

- Results are exact stateless, selected-reference comparisons over validated **pinned
  historical snapshots**. Cached CURRENT flags, aliases and metadata grant no proof or
  execution authority. No live/current-chain implementation assertion or malicious-RPC
  resistance is established; fresh read-only revalidation remains separate.
- Relevant cones are structural influence sets, not proof of causation, a minimal faulty
  set or a uniquely defective wire. Reference trust is explicitly user-declared.
- Automatic proposals require a declared trusted local prior design with matching
  component/source topology. Missing prior mappings or changed topology require manual
  inspection; no semantic pin names or intended behavior are inferred.
- Undo survives workspace navigation but **not page refresh**. Project data is restored
  after reload, while proof, diagnostics and undo are absent. Save the original project
  or diagnostic before refreshing. Revert cannot overwrite unrelated later edits.
- UI trace pages show 50 connections; local apply is limited to 50 visible edits. Larger
  proposals use the explicit diagnostic JSON/separate-project workflow.
- Overall diagnostic deadlines are cooperative between bounded phases. Existing isolated
  solver hard time/memory limits, aggregate/source/trace bounds, 1 MiB input limit,
  loopback-only opt-in and two execution slots remain unchanged.
- Human screen-reader and first-time usability sessions remain unperformed. Automated
  keyboard, narrow viewport, reduced-motion and axe coverage remain green.

No agent workflow orchestrator, wallet, signer, publication, broadcasting, payment,
spending capability or authorization-architecture merge is included. No new dependencies
are introduced. Original audit/fixture/report evidence and frozen contracts are preserved.

## Independent review and handoff gate

**OpenCode independent production review: PENDING.** OpenCode's corpus at `8fc4efb`
provides independent synthetic expectations, not approval of this implementation.
Codex's audit and passing CI do not replace that review. Reviewers should inspect the
implementation delta from main together with the historical-snapshot, ambiguity,
correction-binding, resource and UI limitations above.

The PR is ready for independent review after its final-head checks are green. Keep it
unmerged, with auto-merge disabled, until OpenCode's independent review passes. Any
subsequent production change requires focused reproduction and appropriate renewed
validation. Stop after preparing the acceptance PR; no main merge is authorized here.
