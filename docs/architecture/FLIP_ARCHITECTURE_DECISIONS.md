# FLIP — Architecture Decision Records (ADRs)

**Baseline date:** 2026-11-16  
**Authority:** M0/M0.5 verified technical boundaries and existing CircuitForge PRD, with Flip branding.  
**Status language:** `ACCEPTED_FOR_PLANNING` means architecture choice, not implemented/validated; `CONDITIONAL` needs an engineering proof gate; `DEFERRED` is excluded from P0; `REJECTED` is excluded by design.

## ADR-001: Build Flip as a verifier, not a general circuit canvas

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Context:** Official `tapeout.net` supports REF import, simulation, BLIF, network warnings and pre-send checks. `tapeout.pro` has exhaustive task-reference verification. M0.5 judged Flip *partially differentiated*.
- **Choice:** Narrow pipeline: chain-bound import → deterministic restricted REF composition → arbitrary baseline-vs-candidate stateless equivalence/counterexample → integrity manifest → read-only pre-flight.
- **Rejected:** NAND drawing editor, task-challenge solver, BLIF/Verilog compiler, circuit marketplace.
- **Consequence:** Smaller differentiated MVP; no promise of a full circuit authoring environment.
- **Reopen when:** User evidence strongly supports another workflow and deadline allows a separately approved scope revision.

## ADR-002: Python shared engine, Python CLI, thin web API

- **Decision:** `CONDITIONAL` pending clean packaging, sandbox and parity proof.
- **Alternatives:** (A) TypeScript/WebAssembly browser-local solver shared with Node CLI; (B) Python core, browser via FastAPI and CLI via same Python package; (C) duplicated languages with independent solvers.
- **Choice:** B. The audit's independently tested Python TAP-02 semantics and PySAT Minisat22 are a more direct path to MVP; CLI fully local, web calls server worker.
- **Advantages:** One core, reuse audit fixtures, no uncertain WASM solver build in critical path.
- **Costs:** Web projects are sent to API when submitted; uptime/hosting, resource abuse and worker isolation require design. Web is **not offline-first SAT**. Disclose this rather than claiming user computation stays on-device.
- **Proof gate:** Repeat audited benchmark and canonical artifact comparison across CLI and web, verify worker hard limits; if blocked, use a documented alternate shared runtime through a revised ADR, not duplicated proof logic.

## ADR-003: X Layer mainnet only and read-only RPC

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Context:** M0 verified chainId 196; testnet chainId 1952 has no factory at shared address; native REF chain-blind. Factory address `0x1f09DAeFA827f02CBb40967cc91b259763760761` observed on mainnet.
- **Choice:** Allowlist chainId=196; read-only `eth_chainId`, `eth_call`, `eth_getBlockByNumber`, `eth_getCode`, `eth_getStorageAt` and applicable read-only gas estimation if used. No wallet, signer or broadcast.
- **Consequence:** No product-controlled live publishing. External hackathon circuit publication (if required) is a separate owner-approved milestone.
- **Verification:** static denial of write methods and integration tests, no imported signing libraries in runtime.

## ADR-004: Canonical manifests are mandatory and freshness is separate from proof

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Context:** Unsealed factory and upgradeable beacons; same addresses on Base and X Layer; proxy bytecode alone doesn't capture behavior.
- **Choice:** Pin chain ID, processor/id, netlist and closure hashes, block, factory implementation, beacon implementation and hashes, semantics/test-suite versions. Revalidate environment before fresh export/pre-flight.
- **Consequence:** Can retain historical evidence while reporting `STALE`, `HISTORICAL` or `UNVERIFIED` freshness independently. Single-RPC data is *observed*, not Byzantine-proof.
- **Evidence gate:** all 9 prior negative fixtures, plus cross-language canonical serialization test.

## ADR-005: Exact stateless SAT with independent witness replay

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Context:** Audit 28/28 Minisat22 verdicts within bounded XOR-chain family; pure Python DPLL timed out on larger UNSAT cases.
- **Choice:** Native CDCL Minisat22 with stateless TAP-02 miter; UNSAT → `EQUIVALENT`, SAT with reproduced witness → `DIFFERENT`, all resource/solver/replay uncertainty → `UNKNOWN`.
- **Consequence:** In-scope exact pairwise equivalence is not automatically a correctness claim about user intent. User-supplied truth-table vectors have separately typed results.
- **Limits:** default 2,500 expanded gates, manual max 5,000, 5s solve, 64MiB solver worker, REF nesting <=64. Confirm limits on actual deployment.

## ADR-006: Worker isolation is a security release gate

- **Decision:** `CONDITIONAL`.
- **Choice:** Separate bounded worker OS processes, parent kill/reap, hard per-job memory and deadline, global concurrency limits, no persistence of untrusted user inputs in logs.
- **Why:** A timeout inside the API process or Python-only memory sampling cannot guarantee isolation of a native solver.
- **Fallback:** No public untrusted solver endpoint until hard containment is demonstrated; CLI/local trusted use and isolated demo can continue with accurate caveat. Do not silently change the approved 64MiB worker memory budget.
- **Test:** Hostile SAT/REF fixtures and actual resource-kill log on deployment target.

## ADR-007: Explicit pin mapping via compact table

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Choice:** Numbered input/output pins and restricted connection table with validation. Semantic names are user-asserted labels, never protocol-authenticated meaning. Optional graph is post-MVP.
- **Why:** Fastest credible workflow and avoids redundant editor; maps to FR-020–023.
- **Test:** half-adder composed without developer inspecting raw bytecode; usable keyboard-only.

## ADR-008: One versioned project/report/artifact schema

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Choice:** Pydantic models + generated JSON Schema/OpenAPI types; canonical SHA-256 JSON; decimal strings for uint256; network addresses validated; versioned project, manifest, report and proof bundle. Web and CLI call identical core.
- **Rejected:** separate web-only and CLI-only pipelines, floating-point circuit IDs and implicit JS bit packing.
- **Test:** 100-run determinism, cross-interface canonical hash and witness parity.

## ADR-009: Public web is stateless; local project retention is browser-owned

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Choice:** No signup, no database for user projects; local browser drafts, ephemeral API job content, bounded public chain snapshot cache. Transparent server-processing notice and CLI offline alternative for pinned fixtures.
- **Tradeoff:** No cross-device syncing, server receives submitted project while processing; requires abuse controls.
- **Test:** restart/reload project behavior; server temp cleanup; no body logging.

## ADR-010: Pre-flight reports only observed structural progress

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Evidence:** Previous 81-byte half-adder reached ERC-1155 burn-stage insufficient-balance revert at audited 0.0013 OKB; storage overrides unsupported in audited RPC.
- **Choice:** Re-read fee fresh, perform read-only call and classify `STRUCTURALLY_ACCEPTED`, `REJECTED`, `UNKNOWN`, record actual revert and execution context.
- **Rejected:** `SIMULATION_SUCCESS`, “publish-ready guaranteed”, onchain transaction submission. No assumed fixed fee.
- **Test:** burn-stage known revert / invalid-control / unknown selector / RPC failure cases.

## ADR-011: Stateful work is optional P1 and only trace-bounded

- **Decision:** `DEFERRED` from P0.
- **Choice:** At most eight input beats, explicitly defined zero initial state, first trace divergence; no unbounded sequential equivalence.
- **Gate:** All P0 completed before implementing P1. If schedule slips, omit.

## ADR-012: Assign clear Codex/OpenCode write boundaries

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Choice:** Codex owns architecture, shared core, API, CLI integration, final merges. OpenCode HY4 Flash handles isolated fixtures, negative test cases, independent benchmark reports, docs and safe UI presentation components under explicit subpath ownership.
- **Rules:** Separate Git worktrees/branches; shared schemas frozen before concurrent work; OpenCode may propose core changes in report but not edit core without delegation and Codex approval.
- **Consequence:** Higher parallelism when tasks are independently testable; no artificial split of tightly coupled compiler/SAT work.

## ADR-013: No unearned productivity or security claims

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Choice:** Public copy states measured benchmarks by fixture/hardware; report intent unknown without oracle; no “10x faster” absent independent time-on-task study; single-provider observation not resistant to malicious RPC.
- **Gate:** Content/UX language review, user study with target >=4/5 completing flagship workflow, transparent actual sample size.

## ADR-014: Submission verification is a separate release dependency

- **Decision:** `CONDITIONAL`.
- **Choice:** Before release, re-check current hackathon rules, deadline and artifact requirements. If judges require a newly published onchain circuit, owner separately authorizes a limited one-time publication using outside tooling, with budget/transaction review; Flip app remains read-only.
- **Known uncertainty:** transistor acquisition path and real gas remain unverified from audit.
- **No implicit authorization** to acquire tokens, connect wallet, or broadcast transactions.

## ADR-015: Acceptance gates outweigh feature count

- **Decision:** `ACCEPTED_FOR_PLANNING`.
- **Choice:** Deliver tested vertical slice, golden parity, single RPC integrity guard, auditable artifacts, web+CLI parity and honest result language. Cut visual embellishment and P1 before relaxing any proof, safety or traceability guarantee.
- **Escalation:** Any proposed change conflicting with PRD or `MVP_CONSTRAINTS.md` becomes a written change request requiring owner approval.

## Open risks to revisit at milestones

1. Host enforcement of solver 64MiB / 5s, binary packaging and license (M1/M3).
2. Exact canonical bit-order and archive serializations verified against reference (M1).
3. Availability and latency of X Layer RPC, unreliable alternative providers (M2/M4).
4. Limited differentiation from incumbent canvas and verifier (M4 user tests).
5. Real circuit publication and final judging eligibility (M5, explicit human action).
