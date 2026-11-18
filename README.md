# Flip — M3-A deterministic composition and Wiring Canary

Flip now evaluates TAP-02 snapshots locally, compiles explicit REF recipes and
checks stateless pairwise equivalence with isolated Minisat22 workers. Every
DIFFERENT witness is replayed by the independent local evaluator. These are
historical, reference-relative results; they do not establish current chain state
or intended correctness.

```powershell
uv sync --locked
uv run --frozen flip compose --project docs/schema/m3/examples/half-adder.request.json
uv run --frozen flip compare --project docs/schema/m3/examples/half-adder.request.json
```

See [M3 interfaces and trust boundaries](docs/schema/m3/README.md),
[solver containment/licensing](docs/milestones/M3_A_SOLVER.md), and
[M3-A handoff](docs/milestones/M3_A_HANDOFF.md). Native solver HTTP operations are
disabled by default; local-only opt-in is documented. Publication, wallets,
preflight and web UI remain outside M3-A.

## M2 importer

M2 adds bounded X Layer imports, strict TAP-02 structural decoding, REF dependency
inspection and canonical environment manifests. Proof, composition and preflight
execution remain unimplemented. See [M2 interfaces](docs/schema/m2/README.md) and
[M2-A handoff](docs/milestones/M2_A_HANDOFF.md) for limits and reproduction.

```powershell
.\.venv\Scripts\flip.exe inspect --processor 0x839bdd6fa7a66416a609a735e11de5411b98574e --id 1
.\.venv\Scripts\python.exe -m flip_core.import_schema_export --out docs/schema/m2/1.0.0 --check
```

Live smoke is opt-in: `python scripts/smoke_m2_live.py --out capture.json`.
Mandatory CI uses offline transport fixtures and never contacts an RPC endpoint.

## M1-A foundation notes

**M1-A status (historical): contracts only.** Three Python packages provide versioned models,
JSON Schemas, deterministic JSON/SHA-256, CLI and API scaffolds. No RPC, evaluator,
composer or solver is implemented. Product operations return `NOT_IMPLEMENTED`.

Tested locally: Windows x64, CPython **3.14.6**, uv **0.9.11**, Node **24.18.0**.
The lockfile pins Python distributions and hashes. From the Codex worktree:

```powershell
python -m venv .bootstrap
.\.bootstrap\Scripts\python.exe -m pip install uv==0.9.11
.\.bootstrap\Scripts\uv.exe sync --locked
.\.bootstrap\Scripts\uv.exe run --frozen pytest -q
.\.bootstrap\Scripts\uv.exe run --frozen ruff check .
.\.bootstrap\Scripts\uv.exe run --frozen ruff format --check .
.\.bootstrap\Scripts\uv.exe run --frozen flip-schemas --out docs/schema/1.0.0 --check
node docs/schema/check-canonical.mjs
```

On Linux use `.bootstrap/bin/python` and `.bootstrap/bin/uv`. With uv installed,
use `uv` directly; `uv python install 3.14.6` can provision the exact runtime.
CI targets Linux and Windows; local tests do not establish remote CI success.
`--locked` checks config/lock consistency; `--frozen` consumes the existing lock.
Pytest clears `packages/flip-core/.test-tmp` as disposable in-worktree scratch space.

Second empty-environment installation on PowerShell:

```powershell
$env:UV_PROJECT_ENVIRONMENT = '.venv-clean'
.\.bootstrap\Scripts\uv.exe sync --locked --no-cache --no-editable
.\.venv-clean\Scripts\python.exe -m pytest -q
Remove-Item Env:UV_PROJECT_ENVIRONMENT
```

Implemented usage:

```powershell
.\.venv\Scripts\flip.exe validate project docs/schema/examples/project.json
.\.venv\Scripts\flip.exe canonical circuit-identity docs/schema/examples/circuit-identity.json
.\.venv\Scripts\flip.exe hash manifest docs/schema/examples/manifest.json
.\.venv\Scripts\uvicorn.exe flip_api.app:app --host 127.0.0.1 --port 8000
```

`validate`/`canonical` emit a normalized contract; success means schema consistency
only. Examples are synthetic. API validation is
`POST /api/v1/contracts/{kind}/validate`; `/healthz` reports only liveness and `/docs`
exposes scaffold OpenAPI. Reserved product routes return HTTP 501 / CLI exit 6.

See [frozen contracts](docs/schema/README.md), [CLI exits](docs/schema/CLI_EXIT_CODES.md),
[licenses](docs/schema/DEPENDENCIES.md), and [handoff](docs/schema/M1_A_HANDOFF.md).
Codex and OpenCode worktrees share seed commit `37c39b3`. Implementation remains
on `codex/flip-m1-core`, separate from OpenCode-owned fixtures and from `main`.

---

## Historical starter instructions (retained for provenance)

**Product:** Flip (formerly CircuitForge). **Status:** Planning approved, implementation not yet started.

This folder is a documentation-first seed for a *new Git repository*. It contains **no production implementation**. Codex is the lead engineer; OpenCode (HY4 Flash) supports independent tasks.

## Begin on your Windows PC

1. Extract this ZIP to a new folder, for example `C:\dev\flip`. Avoid placing the project inside `C:\research\circuitforge-feasibility`.
2. Copy the **raw** M0 and M0.5 experiment folders from your local audit to `docs/evidence/raw/M0/` and `docs/evidence/raw/M05/`, respectively, **only if they exist and contain no secrets**. Prefer leaving full experiments in their audited original location and copying selected fixtures with hashes; do not invent absent files. Check sizes before committing large files. Do not commit credentials or private data.
3. Ensure Git is installed. Open a terminal here and run `git init -b main`, `git add .`, `git commit -m "docs: seed Flip engineering workspace"`. Record the resulting commit SHA.
4. Create two separate Git worktrees and branches from the same `main` commit (commands in `agent-tasks/WORKTREE_SETUP.md`).
5. Launch Codex with `agent-tasks/CODEX_M1_A.md` in its worktree; launch OpenCode with `agent-tasks/OPENCODE_M1_B.md` in its own worktree. Start both only after worktrees exist.
6. Bring OpenCode's completed fixture branch to Codex for provenance review; merge only after the M1 gates pass.

## Source-of-truth order

- Current official external rules (must be verified before submission).
- `docs/audits/M05/MVP_CONSTRAINTS.md` for verified hard technical limits.
- `docs/product/CircuitForge_PRD_v1.md` for product requirements (historical title, product now **Flip**).
- `docs/architecture/FLIP_TECHNICAL_DESIGN.md` and related files for proposed implementation architecture.
- `docs/audits/` for cited research and test findings.

Rename historical PRD content in a **versioned revision**, not silently; preserve original M0/M0.5 research terminology and provenance.

## What is missing

The **raw** experiment code, recorded JSON RPC results, and fixture bytes are **not included** in these uploaded markdown reports. The reports may reference paths such as `C:\research\circuitforge-feasibility\experiments`. These should be copied/pulled from the original Windows machine after integrity and secret review. Report-only claims must not become executable golden fixtures.

## Important guardrails

- No wallet signing, token spending, transaction broadcast or onchain deployment without separate explicit authorization.
- X Layer mainnet `chainId=196` only for MVP; no generic NAND canvas.
- Solver resource ceilings and result semantics are governed by `MVP_CONSTRAINTS.md`.
- Neither agent writes directly to `main`; Codex reviews and integrates.
