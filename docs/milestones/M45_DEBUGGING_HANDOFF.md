# M4.5-2D — Production connection debugger handoff

Date: 2026-11-19. **Implementation verdict: PASS for handoff and independent review.**
This branch is unmerged; this report does not authorize a main merge or claim independent
approval of the new production code.

## Exact state and provenance

| Role | Revision |
|---|---|
| Accepted library main / baseline | `1136b187bd68328cea4975caea50904ccece08fd` |
| Independent debugging corpus | `8fc4efb71cb750cced98b4e88540796d665b616a` |
| History-preserving fixture integration | `3edfa2349df05621e7fa352b59de6f2a1d91b62f` |
| Initial implementation | `5973a30459e9e88d5720591127445ad58b38b322` |
| Final tested production code | `ad5d0fdf5e574a736d019f9bd6a4e5402746e886` |
| Delivery branch | `codex/flip-m45-debugging` |

Origin refs, clean baseline and the library merge were verified before creating the
branch. The corpus branch was based on M4 `09f2482`; it was merged into the accepted
library baseline without losing the M4.5 library. Its original 15 files remain exact
Git blobs, including the original diagnostic model, matrix, handoff and transcript.
All nine manifest entries match their original byte counts and SHA-256 hashes.
The original reports retain their original scope; they do not claim production testing.

The independent verifier runs only on a scratch copy. It regenerates the corpus and
checks byte identity without rewriting OpenCode's transcript or fixtures. A separate
production adapter reconstructs the declared dependency bytes using the trusted encoder;
an isolated check confirms exact identity with the frozen dependency bank. Production
expectations are then regenerated with the production evaluator and solver, rather than
using the fixture evaluator as a proof oracle.

[Machine-readable validation and complete original-file hash inventory](m45-debugging/validation-results.json).
The final handoff commit adds only documentation/results after the tested code above;
the exact final branch SHA is recorded in the delivery response. Main remains unchanged.

## Production behavior

`flip_core.debugging.execute` is the shared deterministic engine behind `flip debug
--request request.json` and `POST /api/v1/debug`. The additive contract is
`m45-debugging-1.0.0`; [schemas, bounds, examples and compatibility notes](../schema/m45-debugging/README.md)
are separate from every frozen M1/M2/M3/library profile.

The engine revalidates pinned identities, bytes, manifest hashes and REF closure through
the existing importer/compiler, runs Wiring Canary, and independently replays any witness
again before tracing. It follows differing output bits through explicit comparison maps,
NAND pins, individual REF outputs and parent input boundaries. Nested and repeated
instances retain distinct numeric paths. REF output edges explicitly identify the child
source scope/hash/identity and the parent destination pin. Generated compiler records
are not mislabeled as user components. Ordering and semantic hashes are deterministic;
comparison timestamps and runtime measurements are excluded from diagnostic semantics.

VERIFIED_DIFFERENCE describes the replayed mismatch. Each RELEVANT_CONNECTION describes
structural cone membership. Neither proves a defective wire, a uniquely identified cause,
or intended application behavior. Multiple causes remain ambiguous. EQUIVALENT designs
have no suspect paths/actions. Stale closure, missing data, unsupported state, failed
replay, resource limits or inconclusive comparison fail closed without attribution.

A declared trusted local reference with matching component/source topology permits a
CANDIDATE_ACTION: a separate, structurally validated revision and explicit numeric diff.
The original project/imports/reference are not overwritten. `verify-correction` accepts
only a hash-bound action reconstructed from the original request; it cannot replace the
oracle, source bindings or imports. A fresh exact comparison must return EQUIVALENT to
emit VERIFIED_CORRECTION. That status remains relative to the selected historical
reference and does not establish a unique faulty wire or current chain truth.

## Web flow

Open the [prior-mapping example](../schema/m45-debugging/examples/swapped-prior.execution.json),
run comparison, then select **Inspect connection paths**. The existing white, near-black
and cobalt interface now shows:

- Replayed witness inputs and aligned output bits, with text plus double underlines for differences.
- Numeric component pins and path-qualified relevant connections, paginated at 50 rows.
- A selectable proposed revision and its before/after mappings; verification does not apply it.
- Explicit local apply, rerun and revert. Original workspace state survives screen navigation;
  reverting cannot overwrite unrelated subsequent edits.
- Identity/manifest bindings and a downloadable diagnostic JSON artifact.

Requests are bound to the exact workspace state; delayed responses are discarded after
an edit or unmount. Keyboard entry, reduced motion, narrow viewport, no page overflow,
automated axe checks, resource UNKNOWN and browser/CLI artifact equality are tested.
Desktop and mobile captures were inspected. The mechanical detector reported only two
incumbent warnings (existing selected-row border and Inter font); the established visual
world was preserved. No human screen-reader or first-time usability session is claimed.

Undo is session memory rather than a persistent version store. Save the original project
or download diagnostic JSON before refreshing. The interface applies at most 50 visible
edits; larger proposals require the explicit JSON/separate-project workflow. Automatic
restoration of changed component/source topology is intentionally unsupported.

## Executed corpus and guidance

| Case | Production result / disposition |
|---|---|
| D01 swapped outputs | DIFFERENT; ambiguous relevant mappings; separate prior-output correction also verified in the browser flow. |
| D02 REF input order | DIFFERENT; ambiguous pins; restoring declared order verified by a new comparison. |
| D03 duplicate fan-out | DIFFERENT; single unverified prior candidate; separate correction verified. |
| D04 unbound pin | Production decoder rejects structurally; no behavioral or fault attribution. |
| D05 three-output ordering | DIFFERENT; multiple aligned output paths; ambiguous. |
| D06 simultaneous edits | DIFFERENT; multiple component/output changes; proposed revision remains a candidate until checked. |
| D07 nested REF | DIFFERENT; path crosses two REF boundaries and excludes the unrelated child output computation. |
| D08 commutative rewiring | EQUIVALENT; no suspect connections or corrections. |
| D09 multiple contributing connections | DIFFERENT; multiple relevant paths remain ambiguous. |
| D10 indistinguishable causes | Both distinct single-edge alternatives reproduce the same wrong truth table in production; no unique cause or automatic correction claim. |

All authored truth-table rows and first-difference witnesses replay in the production
evaluator. The solver's independently chosen witness is also replayed and its differing
bits are checked against the trace roots. All eight guidance examples are exercised:
G02/G05 require production VERIFIED_CORRECTION; G01/G04/G06 remain candidate diagnostic
actions; G03/G07/G08 remain explanation-only. Original fixture classifications are preserved.

Negative tests cover traversal/index/connection/depth/circuit/byte/gate/deadline bounds,
missing closure, stale snapshots, forged actions/authority fields, failed witness replay,
solver UNKNOWN, direct-engine input size, repeated shared children, API opt-in/loopback
gates and exact CLI/API output. No fixture result is consumed as an executable proof.

## Final validation

All final code results below are tied to `ad5d0fd`, not the older fixture baseline.

| Check | Actual outcome |
|---|---|
| Focused production diagnostics | **33 passed** |
| Local full Python | **576 passed, 0 failed/errors/skips**, 11,086.05 s; abnormal custody wall time discussed below |
| Local full Chromium | **21 passed**, no skips/failures/flakes; all 18 inherited browser cases retained |
| Linux CI full Python / browser | **576 / 21 passed**, Python 54.558 s |
| Windows CI full Python / browser | **576 / 21 passed**, Python 92.911 s |
| Ruff / frontend | Check and format PASS (70 Python files); Biome, TypeScript and frontend build PASS |
| Schema drift | M1, M2, M3, library 1.0/1.1 and debugging 1.0 PASS; frozen profiles unchanged |
| Canonical / interface parity | Six Node canonical vectors PASS; core/CLI/API and browser diagnostic equality PASS |
| Fixture custody | Original debugging 15 files / nine manifest entries, scratch regeneration, discovery 19 files / 12 cases PASS |
| Custody / credentials | Standalone clean-worktree guard PASS, zero credential findings; both platform CI guards PASS |
| Offline smoke | M1 CLI/ASGI smoke and M3 compose/EQUIVALENT/DIFFERENT parity smoke PASS |

[Final code CI run 44521242685](https://github.com/Technique-S/Flip/actions/runs/44521242685)
is SUCCESS on both supported platforms. Downloaded JUnit and M4 acceptance artifacts
confirm the exact tested commit, all 576 tests, zero skips/errors/failures and all 21 browser
outcomes. The 543 inherited Python tests remain present. One inherited assertion changes
only by registering `fixtures/m45-debugging`; its exact new hash is pinned by custody,
and all new archive bytes are independently pinned. No inherited test is removed or skipped.

Earlier development failures are not hidden: one initial unit mock used an unsupported
solver outcome and was corrected to the existing INTERRUPTED timeout contract. The first
full browser run had 17 passes, one failure and three unexecuted cases because the new
stale-response test ended before its route handler; it now awaits fulfillment. No inherited
library test or production verdict contract was changed to suppress these failures.

## Runtime follow-ups and limits

**F03-PERF-001 remains open** in [the library follow-up](M45_LIBRARY_FOLLOWUPS.md).
The inherited 120-second archival subprocess limit and custody assertions are unchanged.
Its local scratch-regeneration test passed in **68.685 s**. No archival source, generator
or expected result was rewritten.

**D-RUNNER-001 — local Git custody wall-time anomaly.** Owner: Flip lead engineering.
The local full run reported **10,879.267 s** in
`test_git_provenance_and_secret_patterns`; the same test took **2.412 s Linux CI** and
**36.951 s Windows CI**. The local process eventually progressed and all 576 tests passed;
the subsequent standalone custody scan also passed. The cause is unestablished. Preserve
these observations and investigate host scheduling, Git/process/I/O behavior if reproduced;
do not infer a diagnostic-engine performance regression or a resolved host issue from them.
No timeout was increased and no check was skipped. CI correctness passes do not establish
acceptable latency for every local layout/host.

Only bounded stateless NAND/REF tracing is supported. Operation deadlines are cooperative
between bounded validation phases; the existing isolated solver hard limits remain intact.
All diagnostics/corrections replay pinned historical snapshots, never cached CURRENT
authority. No live RPC smoke or current-chain assertion is claimed. Live read-only
revalidation remains separate from mandatory CI. Independent review of this production
delta, human assistive-technology testing and general usability research remain open.

## Changed areas and handoff

Production: new `debugging.py`, `debugging_models.py`, `debugging_schema_export.py`;
bounded CLI/API entry points; `Debugger.tsx` and its comparison/workspace integration.
Tests: new production corpus adapter/33 cases, three Chromium flows, and the exact fixture
namespace registration. Tooling: archived line-ending preservation, narrow immutable
generator Ruff exclusions, exact custody pins and the new schema CI check. Documentation:
contract/examples, README and this handoff/results. No dependency/lockfile update is needed.

Reproduction: `uv run --frozen pytest -q`, `npm test --prefix apps/web`, the six documented
schema check commands, and `uv run --frozen python scripts/check_m1_repository.py --require-clean`.
For a machine-readable example, run `uv run --frozen flip debug --request
docs/schema/m45-debugging/examples/swapped-prior.request.json` (exit 1 means a demonstrated
DIFFERENT result, not a proven defective wire). See the contract for correction replay.

No wallet, signing, broadcasting, payment, spending or agent authorization architecture
is included. Main is unchanged. Stop here for review; do not merge this implementation.
