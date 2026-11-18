# M1-A handoff — 2026-11-17

Stop point: foundations and frozen contracts. No M2+ feature implementation,
external RPC session, evaluator, solver, signer, broadcast or deployment was added.

## Git and scope

Remote: `https://github.com/Technique-S/Flip.git`. Existing seed commit
`37c39b3` was preserved and pushed as `main` after user authorization to set up
Git. Codex's sibling `flip-codex` worktree and `codex/flip-m1-core` branch start
at that same seed as the existing OpenCode worktree. No implementation is merged
to main. M1-A commit SHA is recorded by Git history (the commit containing this
file); the final chat handoff links that exact commit.

Changed files are limited to root build/install configuration and README,
`.github/workflows/m1-contracts.yml`, the three assigned Python packages and
`docs/schema/`. Audit files, evidence, fixtures, historical PRD, architecture
documents and OpenCode artifacts were not edited. `source-provenance.json`
records SHA-256 of immutable seed Git blob bytes, independent of checkout line
endings, plus directly fetched immutable upstream TAP-02 source bytes.

## Decisions frozen

- Six independently versioned content contracts initially use explicit `1.0.0`;
  all unsupported versions and unknown fields reject. Pydantic provides the full
  semantic validation; published Draft 2020-12 schemas provide portable shape checks.
- Chain 196 only; decimal-string uint256 EVM quantities; normalized lowercase
  addresses. REF recipe IDs additionally fit uint64. Explicit numeric pins and
  mappings; ordered arrays preserve identity. No inferred semantic port labels.
- `flip-json-v1` hashes all normalized content, sorts ASCII keys, emits exact
  UTF-8, preserves array order/Unicode and rejects floats, unsafe integers,
  duplicate keys and lone surrogates. Runtime metadata is outside content models.
- TAP-02 LSB-first packing provenance pins exact upstream spec/reference/vector
  hashes and revision. Seven packing vectors and two lenient unpack checks were
  verified against the inspected upstream functions, isolated from other code.
- Proof, intent and freshness remain independent. UNKNOWN is never equivalence.
  SAT differences require declared replayed witnesses; conclusive proof requires
  stateless validated sources/mappings. Validation does not prove assertions true.
- Preflight is structural only, read-only, with observed fee and same-block
  revalidation prerequisites. No fixed current fee or real-publication claim.
- Gate/depth/time/memory ceilings remain 5,000/64/5s/64MiB; default 2,500 gates.
  No solver binary or fallback is installed, and no containment claim is made.
- Argparse CLI exits 0–8 are documented, with exit 6 / HTTP 501 for every reserved
  feature. Implemented validate/canonical/hash operations prove contract consistency
  only. API body validation is bounded at 1 MiB.

## Commands actually executed and results

Run from the Codex worktree on Windows x64, CPython 3.14.6, Node 24.18.0.

```powershell
python -m venv .bootstrap
.\.bootstrap\Scripts\python.exe -m pip install uv==0.9.11
.\.bootstrap\Scripts\uv.exe lock
.\.bootstrap\Scripts\uv.exe sync --frozen
.\.venv\Scripts\python.exe docs/schema/build_examples.py
.\.venv\Scripts\flip-schemas.exe --out docs/schema/1.0.0
.\.venv\Scripts\ruff.exe check . --fix
.\.venv\Scripts\ruff.exe format .
.\.venv\Scripts\python.exe -m pytest -q
node docs/schema/check-canonical.mjs
```

Initial run: 141 passed / 10 setup errors because machine-shared pytest temp
directory access was denied. Fixed by placing disposable pytest scratch inside
`packages/flip-core/.test-tmp`. Initial Ruff formatting/lint findings were corrected.
Initial AnyIO 4.16.0 resolution caused a Starlette TestClient deprecation warning;
constrained to tested 4.11.0 and relocked. uv was initially absent from PATH and
from system Python; project-local bootstrap installed it without global changes.
uv emitted harmless skips of obsolete setuptools/Pygments distribution formats.

Final verification used a **new non-editable install with cache disabled**:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-clean'
.\.bootstrap\Scripts\uv.exe sync --locked --no-cache --no-editable
Remove-Item Env:UV_PROJECT_ENVIRONMENT
.\.venv-clean\Scripts\python.exe -m pytest -q --tb=short
.\.venv-clean\Scripts\ruff.exe check .
.\.venv-clean\Scripts\ruff.exe format --check .
.\.venv-clean\Scripts\flip-schemas.exe --out docs/schema/1.0.0 --check
node docs/schema/check-canonical.mjs
.\.venv-clean\Scripts\flip.exe hash project docs/schema/examples/project.json
git diff --check
```

Results: **155 passed**, no warnings; Ruff check/format passed; no schema drift;
all six Node canonical vectors passed. Import inspection confirmed flip-core was
loaded from `.venv-clean/Lib/site-packages`, not the editable source tree.
Project example hash:
`0x7f6744e0b20aa92eef4fdf8fed93fe86695969e92788be0a95157f0889830be9`.
A real subprocess running `python -m uvicorn flip_api.app:app --host 127.0.0.1
--port 18761` was probed with urllib: liveness and POST compare HTTP 501 /
NOT_IMPLEMENTED passed, then the process was terminated and reaped.
Pinned upstream files were read with urllib, SHA-256 verified, and only inspected
pack/unpack AST functions were executed for the separate packing checks.

CI is configured for Linux/Windows with pinned action commits and runtime/tool
versions. Local acceptance does not claim remote CI or Linux execution has passed.

## Unresolved dependencies

- M1-B raw audit fixture provenance/review and integration remain separate; no
  18-vector, 28-case SAT, real half-adder or nine-negative integrity replay is claimed.
- TAP-02 parser/evaluator, bounded REF resolver, exact decoder/RPC budgets,
  hash/ABI/storage validation, chain-session checking and live freshness are M2+.
- Actual native solver distribution/license, worker containment at 5s/64MiB,
  independent witness replay and parity must be proven before solver release.
- Vector/trace schemas, TypeScript type generation, portable archive details,
  complete workflow CLI/API and web UI are deferred. Stateful P1 remains <=8 beats
  from zero state, never unbounded equivalence.
- Maintainer must choose Flip's source license; dependency inventory does not
  grant a license to project/audit content. External hackathon rules and any
  separately authorized publication remain later release gates.

No remaining local test failures. No product feature is represented as completed.
