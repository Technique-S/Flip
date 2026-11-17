# FLIP — Codex / OpenCode Agent Ownership Matrix

**Version:** 1.0  
**Operating principle:** Codex is the primary engineering owner. OpenCode (HY4 Flash) is a bounded, independent supporting engineer. Split tasks only if it reduces total time without shared-file or interface conflicts. **No coding assignment is executed merely by writing this document.**

## 1. Agent strengths and escalation rules

| Agent | Best tasks | Do not assign by default |
|---|---|---|
| **Codex (lead)** | Architecture, security-sensitive parsing, REF compiler, manifest and onchain semantics, SAT integration, API/CLI shared contracts, system integration, release decisions, PR reviews | None of these delegated for speed without clean interfaces and required review |
| **OpenCode / HY4 Flash (support)** | Documentation, reproducible tests, offline fixture normalization, negative test generators, sample walkthrough, isolated presentation components, exploratory performance measurements, independent QA | Unreviewed protocol rules, Solidity/onchain assumptions, solver correctness rewrites, shared schema edits, broad refactors, final merge/deploy |

**Escalate to Codex alone** when a task changes core TAP-02 semantics, alters canonical serialization, modifies trust/result verdict, requires live contract interaction logic, or touches shared modules. **Parallelize** when OpenCode can finish with read-only inputs or frozen interfaces and write only a disjoint directory.

## 2. Branch and worktree discipline

- `main` protected; no direct commits by either agent; Codex integrates PRs after checks.
- Codex: `codex/flip-mN-<module>` worktree. OpenCode: `opencode/flip-mN-<tests-or-docs>` worktree.
- Both work against the same pinned base commit and approved schema/fixture versions.
- Each task prompt must include: objective, allowed paths, read-only paths, forbidden paths, acceptance commands, evidence required, commit/PR convention, escalation conditions.
- OpenCode may read any public source and relevant test, but may **write only designated owned paths**. No editing lockfiles or package config without explicit task scope.
- No parallel edits to `packages/flip-core/src`, `packages/flip-api/src`, `packages/flip-cli/src`, top-level schema and workspace configuration. Codex owns these unless a specifically reviewed handoff occurs.
- File changes outside assigned paths are a failed task, not an integration convenience.
- Codex handles conflict resolution, schema migration, canonical artifact compatibility and final test run.

## 3. Milestone-level ownership and independent tasks

| Milestone / workstream | Codex (primary) | OpenCode (parallel support) | Conflict avoidance |
|---|---|---|---|
| M1 contracts/fixtures | Define `flip-core` public types, schemas, versioning, canonical hash and CLI exit codes; setup workspace | Convert prior M0/M0.5 evidence into **read-only** golden test fixtures and provenance README | OpenCode writes `fixtures/` + `docs/evidence/` only |
| M2 import/manifest | Chain reader, TAP-02 validator, REF resolver, manifest generation/revalidation, caches | Add malformed netlist, wrong-chain and 9 integrity negative fixtures with explicit expected results | OpenCode writes `packages/flip-core/tests/fixtures/` or top-level `fixtures/` only; no production code |
| M3 composer | REF composition, deterministic netlist, simulator tests | Additional known-good truth-table inputs, 100-run deterministic script and benchmark harness | OpenCode writes tests/scripts separate from core |
| M3 Wiring Canary | CNF/miter, SAT isolation, witness replay, UNKNOWN semantics | Independent synthetic mutation corpus; timeouts/memory stress harness; report templates | No editing SAT engine by OpenCode |
| M4 API/CLI | Python CLI and API wrappers, stable JSON and error contracts | CLI help/examples, clean-machine reproducibility checklist, schema-driven parity tests in owned test files | Codex owns commands, OpenCode only docs/tests |
| M4 Web | Web flow and API adapters, import/compose/compare/results orchestration | Stateless UI components (example `src/components/evidence/`, `src/components/status/`) using Codex-frozen prop types | Disjoint components, avoid shared routes/state |
| M4 Export | Export format, archive safety and verification | Sample proof bundle walkthrough and verifier fixture | OpenCode documents and tests, not exporter code |
| M5 hardening | Integration, security review, production release, CI wiring | Exploratory accessibility checklist, adversarial fixture tests, independent manual QA, docs | Separate PRs; Codex final gates |
| M5 hackathon | Technical integration and final demonstration | Submission checklist and demo script drafts | User owns any external financial authorization |
| M6 P1 traces | Only after P0 green: bounded stateful comparator | Toggle sequence fixtures | Separate branch; optional |

## 4. Dependency-based concurrency rule

| Situation | Recommendation |
|---|---|
| Interface/schema not yet frozen | Codex only implements schema; OpenCode may collect source fixtures without assuming new format |
| Interface frozen; new core module begins | Parallel: Codex implements module, OpenCode builds independent tests to frozen contract |
| Core bug detected | Codex fixes; OpenCode reproduces and shrinks fixture, never silently edits core |
| UI contract unstable | Codex builds workflow; OpenCode can work on docs or standalone presentational components |
| Release merge or security regression | Codex lead, OpenCode audit-only |

## 5. Agent handoff contract

Every delegated task contains:

1. **Input baseline:** branch SHA and approved docs (`MVP_CONSTRAINTS.md`, architecture ADRs, contracts).
2. **Goal:** one bounded technical outcome, not vague “improve project”.
3. **Write scope:** exact permitted directories, with no overlapping ownership.
4. **Evidence:** commands, outputs, fixture hashes and what was *actually* executed.
5. **Prohibitions:** no signing/broadcast, no changed global dependencies, no secrets, no false proofs, no source `main` edits.
6. **Completion:** commit SHA, files changed, test report and explicit unresolved issues.
7. **Merge gate:** Codex reviews changes, runs relevant tests on combined tree, resolves schema conflicts.

## 6. First parallel assignment: M1

### Prompt for Codex (primary)

> **Task: Flip M1-A — architecture bootstrap and frozen shared contracts.** Read `FLIP_SYSTEM_ARCHITECTURE.md`, `FLIP_TECHNICAL_DESIGN.md`, `FLIP_ARCHITECTURE_DECISIONS.md`, original PRD and `MVP_CONSTRAINTS.md`. Work in `codex/flip-m1-core`, separate worktree from OpenCode. Own root workspace configuration, `packages/flip-core/`, `packages/flip-cli/` and `packages/flip-api/` initial scaffolds, `docs/schema/`. Implement *only* versioned Pydantic/JSON Schemas for project, circuit identity, manifest, comparison result, preflight status, error codes, canonical serialization/hash and baseline core package tests; wire skeleton CLI/API entrypoints without fabricating blockchain/solver functionality. Freeze decimal-string IDs, address normalization, bit-order annotation and oracle/verdict semantics; create cross-language golden fixtures. Define stable CLI exit codes and export schema, with tests rejecting unknown versions and wrong chains. No chain writes, no wallet, no product feature implementation. Produce contract spec, passing tests, source hashes, and list of unresolved integration choices. **Do not touch** `fixtures/` or `docs/evidence/`, assigned to OpenCode. Commit changes and return SHA. Stop at M1 contract acceptance.

### Prompt for OpenCode / HY4 Flash (parallel)

> **Task: Flip M1-B — independent, provenance-preserving audit fixtures.** Read M0 and M0.5 reports and the original `experiments/` sources if present. Work in `opencode/flip-m1-fixtures`, separate worktree. You may **write only** `fixtures/` and `docs/evidence/`. Assemble the audited XOR#1, NAND#2, 81-byte half-adder, mutation, nine integrity negative fixtures, 28 SAT scale expectations and preflight revert evidence **only when the raw fixture/result bytes are available**. For missing raw artifacts, create an explicit `MISSING_ARTIFACTS.md` and a non-executable metadata index; never reconstruct hashes, calldata or results from abbreviated text or invent fixtures. Record source path, original SHA-256, observed chain ID/block, test provenance and whether each artifact is `RAW_VERIFIED` or `REPORT_ONLY`. Write a reproducibility README and proposal for tests using the frozen schema once available, but **do not edit schemas, core, CLI, API, workspace configs or locks**. No mainnet transaction, spending or credentials. Commit and report files, missing evidence, and SHA; do not modify Codex files.

These prompts are **ready for delegation after a repository is initialized**. Run them in independent worktrees. If raw experiments aren't shared to OpenCode, fixture completion will be partial by design. The user can send the respective prompts; this document does not start either agent.

## 7. Integration acceptance and review

- Two PRs may merge only after Codex verifies no overlapping writes or API contract drift.
- M1: schema golden samples + reject invalid/cross-chain/ambiguous bit representations; M2: 9/9 manifest negative; M3: 28/28 SAT tests + replay, 81-byte fixture; M4: canonical CLI/web parity; M5: release security and demo.
- If OpenCode output diverges from evidence, preserve the negative finding, quarantine fixture and request correction; never weaken tests to pass.
- Keep `CircuitForge` in legacy file names only for traceability. Product UI, commands, package names and docs say **Flip**.
