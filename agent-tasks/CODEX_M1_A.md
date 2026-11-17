# Copy-ready prompt — Codex (lead), Flip M1-A

You are the lead engineer for Flip (formerly CircuitForge). Operate **only** in the `codex/flip-m1-core` worktree created from the shared initial commit. This is milestone M1-A: foundations and frozen contracts, **not** feature implementation.

First read: `README.md`, `AGENTS.md`, `docs/product/CircuitForge_PRD_v1.md`, `docs/audits/M05/MVP_CONSTRAINTS.md`, `docs/architecture/FLIP_SYSTEM_ARCHITECTURE.md`, `FLIP_TECHNICAL_DESIGN.md`, `FLIP_ARCHITECTURE_DECISIONS.md`, `FLIP_AGENT_OWNERSHIP_MATRIX.md`, `FLIP_IMPLEMENTATION_DEPENDENCIES.md`.

**Write scope:** Root workspace/build configuration (except audit evidence), `packages/flip-core/`, `packages/flip-cli/`, `packages/flip-api/`, `docs/schema/`, and CI files directly required for M1. Do **not** modify `fixtures/`, `docs/evidence/`, `docs/audits/`, or OpenCode-owned artifacts. Preserve historical PRD unchanged.

**Implement only:** a maintainable Python monorepo skeleton; versioned Pydantic/JSON Schemas for project, circuit identity, manifest, comparison report, read-only pre-flight and error envelope; canonical deterministic JSON serialization and SHA-256 hashing with known golden cross-language-friendly examples; explicit chainId=196, decimal-string EVM quantities, lowercase normalized addresses, TAP-02 bitvector encoding provenance, proof/intent/freshness status axes; rejected unsupported schema versions; stable CLI exit-code spec; minimal CLI/API entrypoints that return NOT_IMPLEMENTED for non-existent features rather than simulating success. Pin tooling to tested versions and note licensing. Build tests for schema roundtrips, canonical hashes, malformed payload rejection, wrong-chain input and version rejection. Provide JSON schema documentation. No RPC integration or solver logic yet.

**Mandatory boundary:** no wallet/signing/broadcast, no speculative onchain success, no generic circuit canvas. `UNKNOWN` must never be rendered equivalent. Preserve all hard M0.5 limits.

**Acceptance:** reproducible clean install; documented test commands; passing schema and canonicalization tests; no writes outside assigned scope; code review ready; committed change with SHA. Final handoff: files changed, commands actually run, failures, key schema decisions, unresolved dependencies. Stop at M1-A.
