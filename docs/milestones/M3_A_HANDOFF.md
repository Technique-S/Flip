# M3-A handoff — deterministic composition and Wiring Canary

Base: merged PR #2, `02463b1f370d39f6abab897d54d3438cd6056458`.
Branch: `codex/flip-m3-composition-canary`. M3 changes are not merged into main.

## Delivered behavior

- Stateless NAND/recursive REF evaluator reusing the M2 structural decoder and
  dependency resolver; separately isolated one-beat LATCH primitive for parity.
- Deterministic restricted REF compiler with explicit numbered pins/instances,
  output ordering and NAND glue/buffering, actual width checks and resource caps.
- Bounded Minisat22 CDCL equivalence with shared mapped inputs, independent
  variable allocation, full Tseitin output-difference miter and witness replay.
- Up to 64 deterministic greedy witness-reduction attempts within the same worker
  deadline; no assertion of globally minimal witnesses.
- Trusted construction/consumption binding actual source identities, exact bytes,
  dependency/implementation hashes, project, maps and engine/native identities.
  Consumers repeat solving; caller-provided EQUIVALENT/PASSED flags are not trust.
- Imported reference, prior-version and behavioral comparisons; bounded explicit
  user-vector evaluation with stated partial/exhaustive coverage.
- Shared CLI/API compose/compare/vectors/consume; reproducible JSON inputs/results,
  structured errors, unchanged exit categories. Native HTTP execution defaults
  off and is restricted to trusted loopback opt-in.

Frozen v1/M2 wire contracts and all accepted baseline tests remain byte-identical.
The additive `m3-1.0.0` project permits a local reference composition without
inventing an onchain identity. No migration or rewrite of historical evidence was
required. See [interfaces](../schema/m3/README.md) for precise map direction and
[solver policy](M3_A_SOLVER.md) for packaging, licenses and containment.

## Evidence and acceptance

Baseline established before edits: 279 passed, lint/format/schema checks and six
Node canonical vectors passed. PR #2's Linux and Windows checks were green before
the explicitly user-authorized merge.

Final local validation: **365 passed**, zero skipped/xfail; Ruff lint and format,
all three schema namespaces, original six Node canonical vectors plus the new
full M3 request hash-parity test, real ASGI/CLI smoke, repository/provenance and
tracked-text secret checks passed. The 86 added tests include the 28 benchmark
cases. Native timeout/crash/memory probes were actually executed on Windows.

The official vector corpus comprises five valid circuits, eight malformed cases
and five packing-edge cases: **18/18** categories are parameterized and exercised.
The five valid cases include 278 truth-table/beat observations, including all
256 popcount rows. LATCH/REF state placement is tested only as one-beat evaluation,
never stateless or unbounded equivalence.

The real M2 block-76206482 XOR #1/NAND #2 imports drive the committed half-adder
request. The compiler matches the archived 81 bytes without changing expected
evidence: SHA-256 `3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`,
four truth-table rows and 100 byte-identical builds. The actual captured REF wrapper
#4 -> core #102 replays locally with its two state bits and rejects stateless proof.

The 28-case benchmark matrix freshly passes through production binding, SAT and
replay up to 5,000 gates per design. Detailed Windows observations are committed
in [benchmark results](M3_A_BENCHMARK_WINDOWS.json); Linux/Windows CI emits its own
new measurements. This is not a reuse of archived timing/verdict claims.

Adversarial checks cover symmetric rewiring, duplicated fan-out, output order,
nontrivial input/output maps, actual width fraud, vacuous zero-input mappings,
zero outputs, reference substitution, missing dependencies, altered closure/edges,
bytes, gates and implementations, fabricated UNSAT reports, bad witnesses, source
alias deception, limits, timeout/crash/allocation containment, CLI/API parity and
native HTTP default/public-peer gates. Existing 279 tests are retained unedited.

## Reproduction and provenance

```text
uv sync --locked
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen flip-schemas --out docs/schema/1.0.0 --check
uv run --frozen python -m flip_core.import_schema_export --out docs/schema/m2/1.0.0 --check
uv run --frozen python -m flip_core.verification_schema_export --out docs/schema/m3/1.0.0 --check
node docs/schema/check-canonical.mjs
uv run --frozen python scripts/smoke_m1.py
uv run --frozen python scripts/check_m1_repository.py --require-clean
uv run --frozen python scripts/benchmark_m3.py --out bench.json
uv run --frozen flip compare --project docs/schema/m3/examples/half-adder.request.json
```

All offline tests are deterministic and do not query RPC. Captures retain their
historical single-RPC provenance; synthetic transports/benchmark identities are
explicitly synthetic. No raw bytes, protected architecture/audit files, existing
test assertions or expected historical results were changed. The repository
checker verifies immutable evidence, baseline test bytes, schemas, tracked-text
secret patterns and absence of unexpected binaries.

## Safety boundaries and remaining limits

EQUIVALENT requires completed supported UNSAT; DIFFERENT requires independently
replayed SAT witness; interrupted/failed execution is UNKNOWN. Findings remain
relative to selected source snapshots, implementation and mapping. User intent is
separate and user-declared. No probabilities, current chain observations, signed
certificates or independently checkable UNSAT proof traces are invented.

All M3 results remain HISTORICAL or known STALE. M2 live revalidation is separate;
no cached CURRENT flag is promoted to current proof freshness. No new M3 live
smoke was run. Offline source registration is the imported historical assertion,
not a new factory check or protection against a dishonest RPC provider.

OS containment enforces Windows private commit and Linux virtual address space,
not a uniform cross-platform 64 MiB RSS ceiling or whole-service aggregate budget.
The worker deadline kills noncooperative work, with normal spawn/scheduling/reap
overhead. Public hosting remains blocked until deployment-specific controls are
verified. Other OSes fail closed. Source/native hashes differ across platforms;
portable evidence must be recomputed under the consumer's implementation.

No M4 UI, publication preflight, ZIP export, signing, wallet operations, broadcasting
or general circuit canvas is implemented. The sequential primitive exists solely
to establish semantics parity; no P1 trace product is exposed.

M3 integration is suitable for local core/CLI and trusted loopback API use. Public
service release readiness is explicitly not established. Stop at M3-A.
