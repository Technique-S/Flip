# Flip — M1 engineering workspace starter

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
