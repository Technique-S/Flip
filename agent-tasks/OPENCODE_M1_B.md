# Copy-ready prompt — OpenCode (HY4 Flash), Flip M1-B

You are the supporting research-fixture engineer for Flip. Operate **only** in the `opencode/flip-m1-fixtures` Git worktree created from the same initial commit as Codex. Your task is independent provenance-preserving fixtures and evidence; do not implement product code.

Read: `README.md`, `AGENTS.md`, `docs/audits/M0/` and `docs/audits/M05/` reports, `docs/architecture/FLIP_AGENT_OWNERSHIP_MATRIX.md`, `docs/architecture/FLIP_IMPLEMENTATION_DEPENDENCIES.md`. Locate the raw original experiments on the local Windows machine if accessible: `C:\research\circuitforge-feasibility\experiments` and `C:\research\circuitforge-feasibility\m05-final-verification\experiments`. These paths are **candidates**, verify they exist. They are read-only sources; never modify them.

**Write scope strictly:** `fixtures/` and `docs/evidence/`. Do not edit root configs, lockfiles, schemas, package code, PRD, architecture docs, or audit reports.

**Deliverables:** provenance index for XOR#1, NAND#2, composed 81-byte half-adder, mutation cases, nine integrity negatives, 28 scale verdicts, stateful k-beat fixture and structural pre-flight revert. Copy only actual raw fixture bytes/results that are present and safe to commit; preserve original content hashes; label each `RAW_REPLAYED`, `READ_ONLY_REGENERATED` or `REPORT_ONLY`. For missing artifacts create `docs/evidence/MISSING_ARTIFACTS.md` identifying source path, missing material and affected tests; never reconstruct truncated hashes or outputs from narrative. Prepare compact reproducibility instructions and fixture mapping to future schema; do not import Codex-unfrozen schema or invent one. Check secrets and large files before copying; never commit credentials.

**Acceptance:** complete source inventory with SHA-256 of each copied artifact, clear chain/block provenance when supported, bounded reproducibility commands that were actually run, explicit gaps, and no writes outside assigned scope. Commit work and report SHA, file list, provenance levels and blockers. Stop at M1-B. Do not merge into `main`.
