# CIRCUITFORGE — PRODUCT REQUIREMENTS DOCUMENT

**Version:** 1.0 | **Status:** Proposed implementation baseline, pending founder approval  
**Prepared:** 16 November 2026 | **Release:** OKX X Layer TapeOut Accelerate hackathon MVP  
**Product decision:** CONDITIONAL GO | **Primary constraint:** `MVP_CONSTRAINTS.md` (M0.5)  
**Companion:** `CircuitForge_Product_Decision_Brief_v1.md`

> **One-line definition:** CircuitForge is an X Layer circuit-composition and behavioral-diff workbench that helps developers reuse existing TapeOut circuits, prove whether stateless wiring changes preserve behavior, and export reproducible evidence.
>
> **Critical interpretation rule:** An `EQUIVALENT` verdict proves equivalence **between two explicitly defined stateless behaviors under the pinned semantics and dependencies**. It does not, by itself, prove either behavior matches a real-world intention, is secure, or is safe to publish.

## 0. Document governance and evidence rules

This PRD describes **desired behavior and acceptance standards**, not a declaration that the application exists. All implemented features are pending development. It is intentionally bounded by the uploaded M0/M0.5 audit reports.

- **[AUDIT]**: Finding reported from the audit's tests or direct inspection; original experiment package was not independently executed in this PRD exercise.
- **[DECISION]**: Product or priority choice approved in the user's instructions or proposed here for sign-off.
- **[TARGET]**: Future performance, quality, or usability threshold; not a verified outcome.
- **[OPEN]**: Unsettled product/architecture/eligibility issue, with an owner and resolution checkpoint.
- **Authority order when conflicts occur:** 1) current official protocol and hackathon requirements for external compliance, 2) signed-off `MVP_CONSTRAINTS.md` for technical bounds, 3) this PRD for user-visible behavior and scope, 4) architecture/design documents for implementation detail. Any conflict must be recorded and approved, not silently reconciled.
- **Change control:** Record PRD revision, decision owner, rationale, affected requirement IDs, test updates, and whether an M0.5 revalidation is needed. Reject changes that reintroduce an excluded generic editor without an explicit product pivot decision.

## 1. Executive summary

TapeOut allows onchain circuits to reference other circuits using `REF`. Application developers and circuit authors can create structurally valid compositions that behave differently from a prior version or intended specification. Existing ecosystem tooling already supports common editing, import and simulation tasks, but the M0.5 comparison did not establish an equivalent end-to-end workflow for **arbitrary user-defined refactor-equivalence checking with portable integrity evidence**. [AUDIT: `DIFFERENTIATION_REPORT.md`]

CircuitForge solves a narrow job: **import genuine X Layer circuit dependencies → define limited, deterministic connections → select a reference or expected behavior → compute trustworthy behavioral comparisons → explain differences with replayable witnesses → export proof context → optionally run read-only structural publication pre-flight.**

**Customers:** Primary: developers integrating existing onchain circuits into applications. Secondary: circuit creators maintaining or refactoring their libraries. [DECISION]

**Distribution:** Web application and CLI in v1, using the same logical engine and canonical report schema. [DECISION]

**Feature priority:** The complete stateless vertical slice is P0. Bounded stateful trace diff (at most eight beats) is P1 and cannot displace the complete P0 workflow. [DECISION]

**Status:** M0.5 assessed CONDITIONAL GO, high confidence within bounded technical tests; existing competition and real publication remain limitations. [AUDIT: `FINAL_VERDICT.md`]

## 2. Vision, market position, and value proposition

### 2.1 Vision

Make independently authored onchain computation easier to reuse without losing track of behavioral changes and execution assumptions.

### 2.2 Value proposition

**“Change the wiring. Verify the behavior. Share the evidence.”**

Users get a result more actionable than “netlist valid”: either the changed design computes the same result as their reference, or the app gives a concrete test input that proves it behaves differently, or it clearly explains why it cannot conclude.

### 2.3 Defensible differentiation

CircuitForge is **not** a generic NAND canvas, circuit compiler, BLIF importer or fixed-challenge verifier. `tapeout.net` covers multiple such functions; `tapeout.pro` has a task-oriented verifier. Its narrower differentiator is **arbitrary stateless circuit-vs-circuit comparison, verified witnesses, and dependency/implementation manifest binding**, integrated with composition and read-only X Layer pre-flight. [AUDIT: `DIFFERENTIATION_REPORT.md`, D1–D4]

This advantage is **partially differentiated**, not an uncopyable invention or demonstrated tenfold productivity increase.

### 2.4 Anti-goals

Do not compete with the official canvas on general-purpose design tooling. Do not become an asset marketplace, wallet, blockchain explorer, multi-chain runtime or universal formal-verification product during the hackathon.

## 3. Problem, evidence, and unresolved user demand

### 3.1 Core problem statement

When a developer integrates or refactors existing TapeOut circuits, structural validity alone cannot prove the new wiring preserves intended behavior. REF interfaces lack trusted semantic port labels, and processor/dependency upgradeability can make prior verification evidence stale. A developer needs a repeatable workflow that connects circuit identities, composition, equivalence checking, counterexamples and reproducible proof context.

### 3.2 Concrete failure modes

| ID | Failure | Observed or inferred foundation | Product response |
|---|---|---|---|
| P-01 | Swapped or duplicated pins produce valid but behavior-changing netlists | [AUDIT] Wiring Canary half-adder and parity mutation tests | Produce SAT counterexample; validate by reference simulation |
| P-02 | Equivalent rewiring is mistaken for an error | [AUDIT] Symmetric-gate mutations returned UNSAT | Return EQUIVALENT with declared domain |
| P-03 | Circuit from wrong network is silently reused | [AUDIT] X Layer/Base identical processor addresses, different state | Chain-bound tuple and rejection |
| P-04 | Processor implementation changes while proxy stays the same | [AUDIT] Upgradeable beacon/factory and mismatched documentation | Full environment hashes and stale-result invalidation |
| P-05 | Public RPC is slow/unreliable | [AUDIT] ~1.3 s median, some endpoints failed during audit | Local cache, clear failure/retry controls |
| P-06 | A structural acceptance result is mistaken for deploy success | [AUDIT] ERC-1155 transistor burn blocked complete simulation | Precise pre-flight result labels |

### 3.3 What remains unknown

User pain frequency, adoption, repeated use, willingness to pay, and comparative completion time have **not** been validated with independent developers. The product is feasible enough for a hackathon MVP, but commercial demand is a validation task rather than an established fact.

## 4. Target segments, personas and accessibility assumptions

### 4.1 Primary persona: application integrator

A developer familiar with EVM tooling and basic digital logic who wants to incorporate existing TapeOut circuits in an application. They have processor addresses/circuit IDs, perhaps a previous version or expected test vectors, and want pre-publication behavioral confidence. Their most important question is **“Did this change alter behavior?”**

**Needs:** No wallet to inspect; explicit pin indices; direct comparison; readable witnesses; clear UNKNOWN; machine-readable results for scripts. **Success:** Gets a valid composed netlist and a trustworthy, reproducible comparison outcome.

### 4.2 Secondary persona: circuit author/maintainer

A developer updating a circuit implementation or reusing a component library. Their most important job is **“Can I show my revision is behaviorally equivalent to the version others already rely on?”**

**Needs:** Import both versions; stable artifact and dependency identities; equivalence on supported stateless cases; shareable local report.

### 4.3 Deliberately unsupported first-release personas

General hardware-design novices requiring schematic tutoring, professional silicon designers requiring HDL/EDA flows, end users buying NFTs, and non-developer consumers. They may use the sample project, but their workflows are not requirements.

### 4.4 Accessibility baseline [TARGET]

Keyboard-accessible primary actions, labeled controls, clear focus states, text equivalents for circuit graphs, readable counterexamples without relying on color, and meaningful feedback for long-running or failed checks. Accessibility verification belongs in end-to-end QA.

## 5. Jobs to be done and top use cases

| Use case | Trigger | Input | Desired outcome | Priority |
|---|---|---|---|---|
| UC-01 First run | Developer opens tool | Built-in audited sample | Understand compose→compare→verify without wallet | P0 |
| UC-02 Import and inspect | Has processor and circuit ID | X Layer identity | Trusted netlist/REF closure and manifest | P0 |
| UC-03 Compose components | Wants new circuit | Two or more compatible REFs and glue | Deterministic netlist with explicit connections | P0 |
| UC-04 Verify a refactor | Changed wiring | Baseline and candidate, explicit mapping | EQUIVALENT/DIFFERENT/UNKNOWN | P0 |
| UC-05 Explain regression | Comparator finds difference | SAT witness | Replayable input and both observed outputs | P0 |
| UC-06 Share evidence | Needs review or CI | Completed verification | Self-contained reproducibility bundle | P0 |
| UC-07 Publication preparation | Wants structural readiness | Composed netlist | Read-only structural acceptance/rejection/unknown | P0 |
| UC-08 Sequential trace | Has LATCH circuit | Zero state and up to 8 input beats | Bounded observed divergence, never unbounded proof | P1 |

### 5.1 Priority tradeoff

UC-04 and UC-05 define the strongest market distinction. UC-02/03/06/07 support them. Product decisions, visual polish and technical investments should be evaluated against this priority.

## 6. End-to-end user journeys

### J-01: First-use sample (web)

**Entry:** Homepage → **Try a sample**.  
**Steps:** Load audited half-adder fixture and a miswired candidate; show both source identities; present connection summary; choose baseline as oracle; click **Compare behavior**; display DIFFERENT and witness with explicit inputs and both outputs; click **Fix mapping** using predefined sample action; rerun to EQUIVALENT; download report.  
**Exit:** Developer understands what changed, why, and how to reproduce the finding.  
**Failure handling:** If live RPC unavailable, sample must be clearly labeled **pinned fixture/demo**, not “live chain verified now”; integrity status remains separate.

### J-02: Real import and composition (web)

**Entry:** Import processor + circuit IDs; app verifies `eth_chainId=196`.  
**Steps:** Fetch metadata/netlists at consistent block; recursively resolve REFs; validate TAP-02; expose numbered pins, width, state count, processor and dependency hashes; choose pins and a restricted glue operation; generate and simulate netlist; save draft locally.  
**Exit:** Deterministic netlist and explicit composition definition.  
**Failure handling:** RPC timeout, wrong chain, nonexistent circuit, malformed bytes, REF cycle/depth cap, incompatible arity → informative rejection or UNKNOWN; never fabricate cached results as fresh.

### J-03: Behavioral refactor check (web and CLI)

**Entry:** Select baseline/reference and candidate composition; user supplies/approves external pin correspondence and declares trust basis.  
**Steps:** Validate compatible external interfaces; revalidate manifests; formulate SAT comparison; execute within resource limits; confirm any difference via reference evaluator; minimize counterexample; present status and evidence; export.  
**Exit:** EQUIVALENT, DIFFERENT, or UNKNOWN with transparent semantics.  
**Failure handling:** No oracle/reference → allow *behavioral diff* but never “intended behavior proven”; no defined correspondence → block verification or request mapping; solver timeout and excessive size → UNKNOWN.

### J-04: CLI/automation

**Entry:** Developer provides the same project/manifest definition from a terminal.  
**Steps:** `inspect`, `compose`, `compare`, `preflight`, or `export` commands (names provisional) operate on the shared schema; machine JSON result and clear process exit behavior; local cache and RPC configuration documented.  
**Exit:** Artifacts match web semantics; automation can distinguish equivalence, difference, unknown, invalid input and infrastructure error.  
**Failure handling:** Never equate successful process execution with behavioral equivalence; return explicit result fields and documented exit-code categories.

### J-05: Read-only pre-flight

**Entry:** Developer has valid candidate netlist.  
**Steps:** Refresh fee and dependency hashes; use read-only X Layer contract checks; classify structural acceptance or rejection; describe any resource burn limitation; export separate pre-flight receipt.  
**Exit:** Exact statement of what was and was not tested.  
**Failure handling:** RPC does not support storage override → UNKNOWN for full simulation; structural validation may still be classified if it reached the known transistor-burn stage.

### J-06: Stateful comparison (P1)

**Entry:** Both circuits contain LATCH.  
**Steps:** User supplies input sequence, chooses explicit zero-state convention and beat count ≤8; evaluate beat-by-beat; show first differing beat and trace.  
**Exit:** “Different on this bounded trace” or “No difference observed in this bounded trace”; **never** an unbounded EQUIVALENT verdict.  
**P1 gate:** Only after J-01 through J-05 are accepted.

## 7. Functional requirement conventions

Every requirement has an ID, priority, deterministic behavior and acceptance reference. **P0** must be done before release. **P1** is cut if any P0 acceptance is incomplete. Dependencies among requirements are noted by ID. An engineering design may choose implementation details without changing observable behavior.

### 7.1 Onboarding, application shell and shared project format

**FR-001 [P0] Sample-first entry.** Web UI offers a complete runnable sample without wallet or account. The sample clearly distinguishes pinned audit fixture from fresh onchain verification. **Accept:** E2E sample reaches both DIFFERENT (witness) and EQUIVALENT after selecting the corrected fixture. **Depends:** FR-020, FR-027.

**FR-002 [P0] Workspace state.** User can enter X Layer circuit identities, choose/import reference and candidate, define connections and retain the current unsaved work during navigation; no server account required. **Accept:** Navigation preserves inputs; explicit reset clears project and shows confirmation.

**FR-003 [P0] Portable project definition.** Web and CLI accept/export one versioned, deterministic project schema including chain IDs, source identities, pin mapping, netlist or source references, oracle mode and tool-version metadata. **Accept:** Import→export→import yields same canonical project fingerprint; invalid schema versions reject clearly.

**FR-004 [P0] Shared engine parity.** Web and CLI use the same parsers, compiler, simulator, manifest validator, solver meaning and report schema. **Accept:** Identical fixture in both interfaces produces semantically identical canonical result JSON and netlist bytes, ignoring explicitly nondeterministic metadata such as timestamps.

### 7.2 Chain import and dependency closure

**FR-010 [P0] X Layer only.** The user-facing import path permits X Layer mainnet `chainId=196`; verify current RPC chain ID every session, reject a mismatch before reading circuit data. **Accept:** Base `8453` negative fixture rejected even with same processor address.

**FR-011 [P0] Circuit read.** Read `nextId`, `circuitInfo`, `netlist` and required factory/beacon context using read-only ABI-validated calls. Reads forming a snapshot use a consistent block context where RPC supports it. **Accept:** Audited XOR#1 and NAND#2 fixture identities and decoded fields match recorded hashes.

**FR-012 [P0] REF closure.** Recursively traverse native `REF` dependencies, confirm registered processors and target circuits, detect cycles, and record parent/child identities and arity. **Accept:** Real reference wrapper imports full reachable closure; synthetic cycle/depth overrun is rejected before expensive expansion.

**FR-013 [P0] Decoder resource guard.** Validate TAP-02 structure before simulation, apply record/expanded gate/REF depth limits and explicit error codes. **Accept:** Malformed opcode, forward-reference, pin mismatch, oversized and recursive fixtures cannot exhaust processing.

**FR-014 [P0] Content-addressed cache.** Cache netlists only with chain, processor, circuit ID, netlist hash and execution-environment hashes; expose freshness and origin. Revalidate relevant context before report and pre-flight. **Accept:** Changed beacon implementation or dependency invalidates a cached verification result; offline sample remains labeled cached.

**FR-015 [P0] Provenance display.** Show source chain, processor, circuit ID, netlist hash, block identity, nIn/nOut/nState, gate count and manifest status. Do not invent semantic pin names. **Accept:** Generic numbered pin labels until user declares mapping; unverified user labels visibly marked user-supplied.

### 7.3 Limited composition

**FR-020 [P0] Explicit pin mapping.** Users can define source REF outputs to target REF inputs by numeric pin position and external input mapping, with visible widths; unsupported mappings rejected. **Accept:** Invalid arity/position rejected with actionable message; valid mapping survives export/reimport.

**FR-021 [P0] Restricted glue.** Support necessary TAP-02 NAND glue and output selection/buffering for the approved reference-composition cases; no freeform NAND canvas or full circuit design IDE. **Accept:** Official half-adder fixture can be composed; extra generic drawing UI is not required.

**FR-022 [P0] Deterministic compiler.** Emit well-formed TAP-02 netlist with backward signal ordering and permitted REF dependencies; topological ordering and output placement handled automatically. **Accept:** 100 repeat builds of audited half-adder generate identical 81-byte netlist and 4/4 truth-table outputs.

**FR-023 [P0] Composition preview.** Present netlist byte count, gate/REF counts, input/output mapping, dependency identities and any limitations. **Accept:** Preview matches exported artifact for fixture; unresolved sources block verification/export of a “verified” report.

### 7.4 Oracle and comparison setup

**FR-024 [P0] Explicit intent mode.** Offer (A) trusted baseline circuit or previous version, (B) user-supplied expected vectors/specification, (C) no declared intent: behavioral diff only. State visibly whether an oracle exists and what it establishes. **Accept:** Mode C cannot display “correct”/“bug fixed”.

**FR-025 [P0] Comparison compatibility.** Ensure compatible external widths and explicit pin/output correspondence before SAT or vector comparison; reject undefined correspondence. **Accept:** Misordered external outputs trigger mapping prompt or fail setup, not silently “EQUIVALENT”.

**FR-026 [P0] Truth-table/vector semantics.** When supplied, expected vectors have exact bit order, widths, declared coverage and a deterministic parser; vector success means “matches supplied tests,” never universal equivalence without an exhaustive argument. **Accept:** Contradictory or out-of-range vectors rejected; partial vectors not labeled full proof.

### 7.5 Wiring Canary and semantic verdicts

**FR-027 [P0] Exact stateless comparison.** Compare two valid stateless netlists using CDCL SAT over the declared, supported TAP-02 semantics and pin mapping. UNSAT may produce `EQUIVALENT` only within the verified model; if reference intent is untrusted, explicitly label this as pairwise behavioral equivalence, not correctness. **Accept:** 28/28 M0.5 scale fixtures expected verdicts reproduced in CI at supported sizes.

**FR-028 [P0] Counterexample verification.** For SAT differences, independently evaluate the witness against both candidate and reference; if confirmed, report `DIFFERENT` and show input plus both outputs. Minimize counterexample under a documented strategy; do not claim mathematically minimal unless proved. **Accept:** All reported witnesses replay successfully; deliberately broken solver fixture never produces a trusted difference.

**FR-029 [P0] UNKNOWN semantics.** Timeout, memory cap, unsupported circuit, unavailable reference/candidate needed for a requested comparison, stale environment, missing mapping or irrecoverable ambiguity result in `UNKNOWN` or an explicit invalid-input state, never a fabricated proof. A valid pair of circuits **without a trusted intent oracle** may still be compared as EQUIVALENT/DIFFERENT **in behavioral-diff mode**; the result must not claim which circuit is correct. **Accept:** Forced 5-second timeout and missing oracle cases cannot yield EQUIVALENT.

**FR-030 [P0] Verification resource controls.** Default 2,500 expanded equivalent gates; user may raise to 5,000; 5 s hard solver timeout, 64 MiB memory budget; conservative REF nesting 64. Reject or return UNKNOWN above limits. Apply conservative bounds to decoder input size, records, and expanded reference trees; exact auxiliary caps are architecture-level choices to be validated with hostile fixtures. **Accept:** Resource-exhaustion fixture produces bounded response and clear reason. **Note:** audit benchmarks used native Minisat22; browser/CLI deployments require parity measurements.

**FR-031 [P0] Result explanation.** Show `EQUIVALENT`, `DIFFERENT`, `UNKNOWN` with plain-language scope, confidence basis, source/version, oracle, solver timing, limit and dependency freshness. **Accept:** UX review confirms no use of “safe”, “formally correct application”, “published” or “guaranteed” without supporting evidence.

**FR-032 [P1] Bounded stateful trace diff.** For stateful netlists, accept explicit beat sequence up to eight and declared all-zero initial state, identify first observed divergence; report “no observed difference on supplied trace” if none. **Accept:** M0.5 toggle fixture identifies beat 0 divergence; no unbounded EQUIVALENT label. Only ship after all P0 gates.

### 7.6 Integrity and reproducibility

**FR-040 [P0] Canonical manifest.** Record chainId, processor/circuit ID, netlist hash, block number/hash, REF closure, factory impl slot/code hash, beacon address/impl/code hash, processor proxy code hash, TAP-02 semantics version, test-suite hash, tool/version and canonical manifest digest. **Accept:** Same pinned inputs produce byte-identical canonical manifest digest.

**FR-041 [P0] Integrity revalidation.** Before marking exported verification current, compare live environment and dependency closure with pinned manifest. **Accept:** All nine negative fixtures from M0.5 must be detected; synthetic wrong-chain, changed netlist, dependency and implementation changes invalidate reports.

**FR-042 [P0] Honest trust level.** Reports distinguish verified hash consistency and single-RPC observations from any stronger trust claim. **Accept:** Report warns that malicious-RPC resistance and multi-operator consensus are not established.

**FR-043 [P0] Evidence bundle export.** Export versioned portable bundle with project definition, netlist bytes, hashes, source/oracle specification, comparison result, witness if any, simulation reproduction inputs/outputs, environment manifest and instructions. **Accept:** A second clean CLI environment verifies bundle checksums and reproduces the benchmark outcome without relying on an in-memory browser session; live-current status requires fresh RPC check.

**FR-044 [P0] Evidence lifecycle.** A previously verified report can become `STALE` when dependency or environment hashes change; original past evidence must remain reviewable, but not labeled current. **Accept:** Mutated beacon fixture preserves historical report yet blocks “current verified” badge.

### 7.7 Read-only pre-flight

**FR-050 [P0] Fresh structural pre-flight.** Use live mainnet read-only calls and current `TAPEOUT_FEE()` to validate publication structure; revalidate manifest environment. **Accept:** Half-adder reaches known burn-stage revert and maps to `STRUCTURALLY ACCEPTED`, with exact scope.

**FR-051 [P0] Pre-flight status contract.** Only `STRUCTURALLY ACCEPTED`, `REJECTED` with precise reason, or `UNKNOWN` are valid pre-flight labels. No `SIMULATION SUCCESS` or `PUBLISHED`. **Accept:** ERC-1155 insufficient balance at documented burn stage is not mislabeled as full transaction success; unknown revert remains UNKNOWN.

**FR-052 [P0] No transaction capabilities.** No wallet connection, private-key access, fee payment, token mint/purchase, signature or broadcast paths. **Accept:** Production repository has no reachable signing/broadcast workflow; tests assert read-only RPC method allowlist for app-controlled calls.

### 7.8 CLI, error handling and operations

**FR-060 [P0] CLI workflow parity.** CLI supports import/inspect, compose, compare, export and preflight from versioned input files, with JSON results; exact command syntax defined in CLI specification. **Accept:** J-04 can be run on clean machine from README with one example fixture.

**FR-061 [P0] Stable result classes.** Provide stable machine fields for `EQUIVALENT`, `DIFFERENT`, `UNKNOWN`, `INVALID_INPUT`, `RPC_ERROR`, `STALE`, and pre-flight statuses. Exit-code mapping documented independently; do not conflate tool execution success with verification equivalence. **Accept:** CI example interprets all classes correctly.

**FR-062 [P0] User-facing errors.** For failed RPC, malformed netlist, wrong chain, mismatch, solver timeout and unsupported stateful proof, show distinct actionable messages. **Accept:** E2E fixtures cover each failure without blank output or unhandled exception.

**FR-063 [P0] Source attribution.** Web reports, CLI exports, and help link to provenance and limitation documentation, audit methodology where appropriate, and versioned schema specs. **Accept:** Every generated report names tool version and semantic assumptions.

## 8. Non-functional requirements

| ID | Requirement | Measurable acceptance |
|---|---|---|
| NFR-01 | Determinism | Same fixture/config/versions yield same netlist, normalized report and manifest hashes across 100 repeated tests; timestamps excluded from digest |
| NFR-02 | Solver correctness | All agreed SAT verdict regression fixtures pass; every DIFFERENT witness replayed; UNKNOWN on timeout |
| NFR-03 | Solver budget | Default 2,500 gates, optional 5,000; 5 s/64 MiB enforced on supported deployment, overrun terminates safely |
| NFR-04 | Runtime validation | Measure browser/WASM and CLI/native parity under specified CPU/browser conditions before signing off release; native audit latency cannot be assumed to equal browser latency |
| NFR-05 | Resource safety | Bound bytes, REF depth, expanded gates, recursion, RPC concurrency, solver work; reject abusive fixtures predictably |
| NFR-06 | RPC resilience | Wrong chain rejected; failed RPC gives explicit retry/offline state; cached historical results never shown as live-verified |
| NFR-07 | Integrity | All 9 negative fixtures detected in CI and revalidation applied before report/preflight |
| NFR-08 | Security posture | Read-only network methods only, no key custody, no broadcasting, sanitized user strings, no arbitrary code execution from imported artifacts |
| NFR-09 | Accessibility [TARGET] | Core web flow usable with keyboard; status text not conveyed only by color; critical errors announced/accessibly labeled |
| NFR-10 | Portability | One schema for web and CLI, portable report import; clean CLI reproduction for sample fixtures |
| NFR-11 | Observability & privacy | Local diagnostics and opt-in error export; do not collect private-key material or silently upload project contents |
| NFR-12 | Reliability [TARGET] | No data loss during ordinary page navigation; failure is explicit and recoverable; local storage quota errors handled |

**Performance evidence boundary:** M0.5 reports native Minisat22 at 5,000 gates up to ~1.4 s and under 8 MiB on its chosen XOR-chain benchmark. These are benchmark-family observations, **not** guarantees for arbitrary graphs, WASM packaging, deep nested REF trees or end-user hardware.

## 9. Result semantics and trust model

| Result | Exact meaning | Required evidence | Must never imply |
|---|---|---|---|
| `EQUIVALENT` | Under pinned supported stateless TAP-02 semantics and defined I/O mapping, no distinguishing input exists between two modeled circuits | Validated sources, manifest, SAT UNSAT within limits | Either circuit is intrinsically correct or secure |
| `DIFFERENT` | At least one input gives different outputs | SAT witness replayed by independent evaluator; both outputs preserved | Which circuit is correct without oracle |
| `UNKNOWN` | No trustworthy complete verdict | Reason code: limit, timeout, unsupported, stale, missing reference, RPC, etc. | Equality or inequality |
| `VECTORS_MATCH` | All declared test vectors passed | Parsed expected vectors, actual outputs, coverage | Full-input equivalence unless exhaustive domain proved |
| `BOUNDED_TRACE_DIFFERENCE` (P1) | A supplied state/input trace differs at an identified beat | Beat-by-beat reproducible trace | General sequential inequivalence from an unspecified initial state |
| `BOUNDED_TRACE_NO_DIFFERENCE` (P1) | No mismatch on that one checked trace | Trace and initial-state convention | Unbounded equivalence |
| `STRUCTURALLY ACCEPTED` | Read-only publication checks progressed through structural validation to known resource-burn stage | Call input, current fee, RPC/block, decoded revert reason | Success after paying burn, minting or deployment |
| `REJECTED` (pre-flight) | Structural validator rejected candidate with known reason | RPC revert class and input | Chain is unavailable for every possible candidate |
| `UNKNOWN` (pre-flight) | Could not establish structural result | RPC/override/unrecognized revert reason | Structural success |

**Two orthogonal dimensions:** Result may be *historically reproducible* but *not fresh relative to chain state*. Show verification verdict and integrity freshness separately. A stale report should not lose its historical evidence.

## 10. Data contracts and artifacts

### 10.1 Canonical project schema (requirements, not final JSON schema)

- `schemaVersion`, `projectId` (local), `chainId=196`, optional `snapshotBlock`.
- `sources[]`: processor, circuit ID, hash, nIn/nOut/nState, dependency manifest reference.
- `components[]`, `wires[]`: explicit source and target pin indices plus restricted glue operations.
- `candidate`: deterministic composed netlist bytes or reproducible recipe.
- `comparison`: baseline/reference circuit or declared vectors, pin/output mappings, oracle mode and trust assertion.
- `limits`: gate cap, REF depth, solver timeout and memory budget.

### 10.2 Verification report schema (requirements)

- `reportSchemaVersion`, `projectHash`, `toolVersion`, `semanticVersion`.
- `manifestHashes` for both compared sides and full embedded provenance or linked content-addressed records.
- `verdict`, `reasonCode`, `oracleMode`, `completeness`, `inputMapping`.
- `solverBackend`, `solverOutcome`, `elapsedMs`, `resourceUsage`, timeout/limit flags.
- `witness` (only after replay) with input values, both outputs, verification method, and minimization status.
- `freshnessStatus`, `lastCheckedBlock`, `warnings`.
- `preflight` object, separately typed from comparison verdict.

**Security note:** Canonical hash encoding, numeric representation (including circuit IDs larger than JS safe integers), address case/checksum, JSON/CBOR choice, deterministic archive container and schema versioning are architecture deliverables. The PRD prohibits ambiguous serialization, but does not predetermine exact encoding.

### 10.3 Export package

Provide a human-readable summary and machine-verifiable archive: project JSON, circuit binary, manifest JSON(s), comparison JSON, oracle/input specification, optional witness, reproduction README and relevant hashes. Avoid storing API secrets and do not include private credentials.

## 11. Web UX requirements and information architecture

**Web top-level flow:** Start/Sample → Import → Compose → Compare → Evidence & Pre-flight. This is a **linear workflow**, not five unrelated power-user dashboards.

**Start:** Show product promise and one-click audited sample. Display that no wallet is required.  
**Import:** Form for processor/circuit ID; chain fixed to X Layer; source cards with numbered inputs/outputs, expanded dependency summary, freshness and read-only origin.  
**Compose:** Compact pin-mapping table or restricted connection graph; immediate arity/index warnings; deterministic preview. Avoid introducing a blank universal canvas.  
**Compare:** Two named sides (“Reference” and “Candidate”), explicit oracle source, run control, visible resource budget; show SAT status separately from semantic interpretation.  
**Result:** Side-by-side outputs for witness, clear evidence that reproduces it, explanation of equivalence scope; action to modify wiring, rerun or export.  
**Pre-flight:** Separate trust labels and current fee, plus clear caveat about transistor burn and real publication.  
**Export:** Download machine-readable artifact and concise human summary; links to reproducibility instructions.

**Visual hierarchy rule:** Always show network/source identity, verdict, oracle assumption, counterexample (if any), and freshness in the primary report viewport. Full manifest detail may be expanded on demand.

**Empty/loading/error requirements:** Provide empty-state guidance; progress with cancellation for long imports and solver checks; retry with config for RPC failures; distinguish stale cached result from a live result; preserve project state after errors.

**Design decisions deferred to UX spec:** CSS framework, exact page layouts, animation, iconography, responsive breakpoints, and whether compose uses a table or minimal graph.

## 12. CLI product requirements

CLI is a first-release surface, not a later developer convenience. It should be scriptable and useful when graphical composition is not needed.

**Proposed command families (illustrative, not frozen syntax):**

```text
circuitforge inspect --processor <address> --id <integer> --format json
circuitforge compose --project project.json --out candidate.bin
circuitforge compare --project project.json --format json
circuitforge preflight --project project.json --format json
circuitforge export --project project.json --out report-bundle.zip
```

**CLI acceptance:** Document install and supported OS/runtime; one command can validate a bundled sample, one compares two imported circuits, one exports reproducible evidence. Machine output is stable and parseable. Diagnostic messages go to stderr (or structured error field), and output files are either complete and validated or not committed.

**Exit semantics:** Define stable codes for successful EQUIVALENT, demonstrated DIFFERENT, UNKNOWN, invalid input and infrastructure failures. A DIFFERENT result is not a tool crash; automation must be able to distinguish the classes. Final code numbers belong in the CLI specification.

**Architecture guardrail:** Web and CLI must call the same versioned engine and file/schema validators. A CLI-specific verification algorithm or web-only proof shortcut is not allowed.

## 13. Non-goals, dependencies, risks and assumptions

### 13.1 Explicitly out of scope for P0

- Generic NAND-from-scratch circuit editor or broad visual IDE; BLIF/Verilog toolchain; onchain challenge/task verifier.
- Wallets, key management, token acquisition, signature, broadcast, publication transactions.
- X Layer testnet support (no verified factory at shared testnet address during M0 audit), arbitrary cross-chain REF execution, multi-network support.
- Unlimited circuits, deep unbounded REF graphs, unbounded stateful equivalence, malicious-RPC consensus.
- Cloud collaboration/accounts/marketplace and unvalidated 10× productivity claims.

### 13.2 Risk register

| Risk | Impact | Mitigation / decision | Ownership |
|---|---|---|---|
| Official canvas closes differentiator | Product-market risk | Lead with arbitrary refactor equivalence + portable manifests; validate with users; revisit at release | Product |
| Mutable beacon or factory | Invalid/stale proofs | Pin and compare impl/code hash and dependency closure before export/preflight | Protocol engineering |
| Wrong chain/source | Incorrect artifact | Chain 196 per session, signed-off manifest and explicit reject | Protocol engineering |
| False SAT verdict | Critical trust damage | Independent witness replay; 28-case baseline; timeout→UNKNOWN; compare reference evaluator | Verification engineering |
| Solver scaling outside benchmark | Slow/frozen app | 2,500 default / 5,000 max; 5 s/64 MiB; measure real deployment | Verification engineering |
| RPC failure/latency | Interrupted flow | Cache with freshness status; configurable RPC; retry; no false green | Integration engineering |
| Bad oracle/incorrect pin intent | Misleading “correct” claim | Explicit oracle and mapping; no correctness guarantee without intent | Product/UX |
| No onchain publication | Submission eligibility/demo concern | Verify rules; separately authorized real publication if required; never add covert signer | Hackathon owner |
| Fee or transistor rules change | Pre-flight stale | Re-read fee and implementation; indicate unknown real gas/availability | Protocol engineering |

### 13.3 Open decision log

| ID | Decision required | When | Proposed resolution |
|---|---|---|---|
| O-01 | Browser WASM solver vs hosted native service | Architecture gate, before implementation | Benchmark parity, resource isolation and delivery reliability; share core semantics |
| O-02 | Minimal pin-mapping UI | UX wireframes | Start with explicit table; graph only if user test shows meaningful gain |
| O-03 | Oracle/vector schema and explicit trust affirmation | Schema design | Define versioned portable file and unambiguous bit order |
| O-04 | Current hackathon onchain requirement | Before submission and roadmap lock | Verify latest official rules; budget separately authorized publication if required |
| O-05 | Web/CLI package distribution | Architecture gate | Choose documented install/runtime, avoid two independent engines |
| O-06 | Launch user-study recruitment | During P0 integration | ≥5 qualified developers, measure task completion/errors; no fabricated demand claims |
| O-07 | Real transistor acquisition and deployment cost | Authorized publication milestone only | Research and perform only with explicit financial/signing approval |

## 14. Success metrics, instrumentation and validation

### 14.1 Engineering release gates (mandatory)

1. **Importer correctness:** Audited live X Layer fixture identities match; wrong-chain and malformed cases rejected.
2. **Composition correctness:** Half-adder yields 81-byte deterministic netlist, 100 repeated builds identical, complete 4-row truth table.
3. **Verification correctness:** M0.5's 28 scale cases reproduce expected results under chosen runtime; witness replay required; timeouts never EQUIVALENT.
4. **Integrity:** All nine negative mutation fixtures detected and stale results invalidated.
5. **Cross-interface:** Same input → consistent canonical hashes, netlist and result in web and CLI.
6. **Pre-flight:** `STRUCTURALLY ACCEPTED` / `REJECTED` / `UNKNOWN` faithfully reflect the actual read-only stage; no publication success claims.
7. **Security:** Runtime resource limits and hostile-input tests run; no wallet or write RPC path.
8. **Release:** Working public web app, reproducible CLI install, sample and report download; approved submission requirements satisfied.

### 14.2 User-value validation [TARGET]

- Recruit at least **five** qualified developers, with primary-persona participants prioritized; record prior circuit experience.
- Have participants independently complete J-01 and a real or realistic J-03 workflow.
- Target at least **4/5** completing the flagship task unaided. Measure median completion time, error count, point of confusion, and confidence calibration (whether they correctly understand EQUIVALENT vs correct-intent).
- Compare against a documented baseline workflow where possible. **Do not claim 10× time improvement** absent measured comparison on comparable tasks.
- Ask whether the developer would reuse it in their next project; record behavior (repeat use) separately from stated interest.

### 14.3 Hackathon validation [TARGET]

Demonstrate a full end-to-end story with genuine X Layer circuits and an independently replayable counterexample; provide public repo or required product links, technical integration identifiers, and short demonstration video per current official instructions. Treat final official rules check as a release gate, not an assumption embedded in the PRD.

## 15. Acceptance traceability matrix

| Test ID | Requirement IDs | Fixture / scenario | Required observed outcome |
|---|---|---|---|
| AT-01 | FR-001, FR-031 | Audited sample miswire and fix | DIFFERENT with witness → EQUIVALENT after fix; limitations visible |
| AT-02 | FR-010, FR-011, FR-015 | Real X Layer XOR#1/NAND#2 | Correct identities and netlist hashes; source metadata shown |
| AT-03 | FR-010, FR-040, FR-041 | X Layer 196 vs Base 8453 collision | Rejected; no cross-chain conflation |
| AT-04 | FR-012–014 | Recursive REF, oversized, invalid | Bounded failure and no uncontrolled recursion |
| AT-05 | FR-020–023 | Half-adder composition | 81 bytes, 2 REFs + 1 NAND, 100 identical builds, correct 4/4 outputs |
| AT-06 | FR-024–026 | Reference, vectors and missing intent | Scope and claim labels accurate; no false correctness |
| AT-07 | FR-027–030 | M0.5 28 SAT cases and 7 safeguards | Expected E/D; verified witnesses; timeout UNKNOWN; resource limit enforced |
| AT-08 | FR-040–044 | Nine integrity mutations | All detected; historical report retained and marked STALE |
| AT-09 | FR-043, FR-060–063 | Same project via web and CLI | Equivalent canonical artifacts; reproduction works from clean CLI |
| AT-10 | FR-050–052 | Valid netlist to resource burn and invalid controls | Honest pre-flight status with current fee; never called published |
| AT-11 | FR-032 | Eight-beat LATCH trace fixture | First mismatch shown; never universal equivalence (P1 only) |
| AT-12 | NFR-03–09 | Resource stress, malformed inputs, keyboard workflow | Bounded failure and usable accessible flow |
| AT-13 | UC-01, UC-04 | Five developer pilot sessions | Record ≥4/5 task-completion target or transparently report miss |
| AT-14 | Release gate | Public web + CLI + artifacts + official rule checklist | Working demonstrable product; no invented onchain publication status |

## 16. Release definition of done and milestone sequence

**Definition of Done for P0:** Every P0 FR and mandatory NFR has an automated or documented acceptance test; J-01 through J-05 work; web and CLI use the same core; all gate-critical tests pass; provenance is reproducible; UI never overclaims proof; released application and CLI can be installed/opened by someone outside the engineering environment; submission obligations checked against official terms.

**Milestones (sequence, not unverified effort estimates):**

- **M1 — Contracts and fixtures:** Freeze project/report/manifest schemas and interpretation of E/D/UNKNOWN; import official audit fixtures into CI.
- **M2 — Core and integrity:** Decoder, chain reader, bounded REF closure, canonical manifests, diff-aware cache, safe errors.
- **M3 — Composition and verification:** Deterministic composer, local evaluator, Minisat22/CDCL integration, witness replay, limit enforcement.
- **M4 — Web and CLI parity:** Web journey, scriptable commands, shared schema, sample, evidence bundles, read-only pre-flight.
- **M5 — Acceptance and submission:** Adversarial tests, pilot users, documentation, deployment, official rule check and demo.
- **M6 (P1 only) — Bounded trace:** Up to eight beats if M1–M5 are green.

**Release fallback:** If schedule compresses, cut P1, visual graph polish, persistent local projects and nonessential visualizations. Do **not** cut the shared CLI/web core, integrity, witness replay, UNKNOWN semantics or core sample. If web+CLI parity becomes impossible, escalate a product scope decision rather than quietly shipping a noncompliant version.

### 16.1 Separate onchain publication decision

The audits reported a real X Layer half-adder structurally accepted up to an ERC-1155 transistor-burn revert at 0.0013 OKB. They did not verify transistor acquisition, real gas or successful publication. Those are **external authorization-dependent tasks**. If the hackathon requires an onchain circuit ID representing our new work, plan and authorize that transaction as a dedicated submission operation, not as a hidden CircuitForge product feature. No financial actions are authorized by this PRD.

## 17. Product approvals and unresolved prerequisites

**Approved by user for PRD:** Both target personas with application developers prioritized; integrated compose→compare→verify; web+CLI in v1; stateful traces P1.  
**Pending founder sign-off:** Proposed P0 list, five-user pilot target, exact launch/no-account approach, and scope of restricted glue wiring.  
**Pending engineering:** Formal schema, concrete dependency graph, solver packaging, runtime cap enforcement, read-only preflight implementation, and CLI distribution.  
**Pending external verification:** Latest hackathon compliance requirements and whether separately authorized publication is needed.

No additional general feasibility research is required to start architecture and build planning. The remaining open items are explicit implementation or release decisions.

## Appendix A — Research crosswalk

| Claim/theme | Source supplied in this conversation | Status |
|---|---|---|
| CONDITIONAL GO, four gates | `FINAL_VERDICT.md`, `FINAL_HANDOFF.md` | [AUDIT] |
| Network 196 only, limits and exclusions | `MVP_CONSTRAINTS.md` §§1–10 | [AUDIT/CONSTRAINT] |
| 18 official TAP vectors and X Layer corpus | `FEASIBILITY_REPORT.md`, `EVIDENCE_REGISTER.md` | [AUDIT] |
| Composition 81-byte half-adder and read-only burn | `PUBLICATION_READINESS.md` | [AUDIT] |
| Manifest contents and nine negative fixtures | `INTEGRITY_VERIFICATION.md` | [AUDIT] |
| 28/28 Minisat22 benchmarks and trace P1 | `WIRING_CANARY_SCALE.md` | [AUDIT] |
| Existing-tool overlap and narrow differentiation | `DIFFERENTIATION_REPORT.md` | [AUDIT] |
| Resource/security issues | `SECURITY_REVIEW.md`, `TECHNICAL_RISKS.md` | [AUDIT] |
| Product persona, web+CLI, stateful P1 | User's explicit PRD decision message | [DECISION] |
| Pilot thresholds, information architecture | This PRD | [TARGET/PROPOSAL] |

## Appendix B — Product questions that should be asked during UX testing

1. Does the developer understand what evidence makes a result EQUIVALENT?
2. Can they specify pin order and choose a trusted reference without unintended assumptions?
3. Can they reproduce the counterexample after exporting the evidence bundle?
4. Do they understand a cached result may be historically valid but not chain-current?
5. Can they explain why STRUCTURALLY ACCEPTED does not mean PUBLISHED?
6. Does the CLI reduce repetitive testing effort or merely duplicate web actions?
7. Would they incorporate this workflow into their next actual integration or refactor?

**End of PRD v1.0.**
