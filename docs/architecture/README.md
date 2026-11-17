# Flip architecture package — 2026-11-16

This package describes the proposed architecture and implementation contracts for **Flip**, formerly CircuitForge, grounded in the existing PRD and M0/M0.5 technical audits.

1. `FLIP_SYSTEM_ARCHITECTURE.md` — complete system boundary, topology, trust model, data flows and release gates.
2. `FLIP_TECHNICAL_DESIGN.md` — stack, module interfaces, schemas, solver isolation, API/CLI, data, security and test strategy.
3. `FLIP_ARCHITECTURE_DECISIONS.md` — 15 ADRs with choices, alternatives, risks, and engineering proofs.
4. `FLIP_AGENT_OWNERSHIP_MATRIX.md` — Codex/OpenCode write ownership, handoff contract, first independent M1 task prompts.
5. `FLIP_IMPLEMENTATION_DEPENDENCIES.md` — dependency graph, milestone gates, cut-lines, approximate schedule, release prerequisites.

**Important evidence boundary:** Uploaded audit reports contain claims about tests and chain checks; the full local `experiments/` directory from OpenCode was not supplied with the conversation. The source PRD was inspected at `/mnt/data/circuitforge_prd/`, and the M0/M0.5 markdown reports were inspected at `/mnt/data/`. Architecture choices such as Python/FastAPI server-side verification are design proposals, not already benchmarked deployment facts.

**Do not begin live onchain publication or token spending without separate approval.** All planned Flip product operations are read-only.
