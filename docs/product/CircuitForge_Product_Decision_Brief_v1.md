# CircuitForge — Product Decision Brief

**Version:** 1.0 (planning baseline)  
**Date:** 16 November 2026  
**Decision:** Conditional GO for a narrow MVP  
**Owners:** Product founder (approval); engineering lead (implementation acceptance) — names TBD  
**Authoritative technical boundary:** `MVP_CONSTRAINTS.md` (M0.5 audit)

## 1. Decision in one paragraph

Build **CircuitForge**, an X Layer–specific, verification-first workbench for developers who reuse or refactor TapeOut circuits. The product imports deployed circuits and their chain-bound REF dependencies, supports **a narrow deterministic composition workflow**, compares the resulting stateless circuit to an explicit reference or specification, and returns **EQUIVALENT**, **DIFFERENT** with a reproducible counterexample, or **UNKNOWN**, backed by a portable integrity manifest. Deliver both **a web application and a CLI** in the first release, powered by one shared core. Add read-only publication *structural* pre-flight; do **not** add wallet signing, broadcast, a full NAND canvas, BLIF/Verilog tools, or unbounded stateful proofs. Stateful bounded trace comparison is **P1**, after the stateless vertical slice works.

## 2. Who and what job

- **Primary:** TapeOut application developers integrating deployed circuits into a new workflow, who need to prove that a change in REF wiring has not altered expected behavior.
- **Secondary:** Circuit-library authors and maintainers comparing a new revision with a known reference.
- **Primary job:** “When I connect or refactor existing TapeOut circuits, help me test and establish whether the resulting logic preserves my intended behavior, and give me a reproducible diagnostic if it does not.”
- **Moment of use:** Before committing a refactor, handing a circuit to another developer, or preparing it for publication.
- **User-provided intent anchor:** Known reference circuit, declared expected input/output vectors, or an explicit behavioral specification. CircuitForge cannot infer correct intent from an unlabeled pin order.

## 3. Evidence and problem size

**Observed engineering evidence:** The M0/M0.5 audits reproduced X Layer circuit reads and simulations, composed an 81-byte half-adder from deployed XOR/NAND REFs, and demonstrated SAT equivalence and verified counterexamples. M0.5 reported 28/28 correct solver verdicts across up to 5,000 equivalent gates under its tested benchmark family. Its integrity prototype detected 9/9 negative fixtures. These are **audit-reported experiments, not an independently rerun production test suite**.

**Competitive evidence:** `tapeout.net` already supports onchain REF loading, simulation, BLIF, pre-send checks and cross-chain warnings. `tapeout.pro` verifies against fixed task references. A general editor is redundant; the credible gap is **arbitrary user-supplied refactor equivalence plus portable dependency/evaluation evidence**. Competitive advantage is plausible and easy for competitors to imitate, not proven by customers.

**Missing evidence:** No measured user pain frequency, retention, willingness to pay, or 10× time saving. Obtain these through pilot use; do not claim them in launch copy.

## 4. Product promise and explicit boundaries

**Promise:** “Compose existing TapeOut circuits. Know exactly whether your changes altered their behavior.”

**What it can prove:** For two compatible stateless circuits under the explicitly pinned semantics and trusted reference, SAT UNSAT establishes equivalence within that modeled domain. SAT DIFFERENT is only reported after re-executing the witness in the trusted evaluator; the product shows the input and both outputs.

**What it cannot prove:** Without trusted intent it cannot identify which circuit is *correct*; bounded traces do not establish unbounded stateful equivalence; read-only structural pre-flight does not prove publication success; a single RPC is not guaranteed honest.

## 5. User-facing experience to ship

1. **Start:** Open a sample immediately, or import one/two real X Layer circuits using processor address and ID. No account or wallet required.
2. **Compose:** Connect imported REF components using explicit numbered pins and restricted glue NAND logic. Show validity and source identities; avoid a general circuit-design canvas.
3. **Compare:** Select a trusted reference (e.g., earlier version) or supply expected vectors. Make the intent mode prominent.
4. **Verify:** Return EQUIVALENT, DIFFERENT + minimized reproduced witness, or UNKNOWN + exact reason; show checked scope/assumptions.
5. **Export:** Download netlist, wiring specification, canonical chain/dependency manifest, verification summary, test witness and reproduction instructions.
6. **Pre-flight:** Perform read-only, fresh-fee structural validation and label only STRUCTURALLY ACCEPTED / REJECTED / UNKNOWN.
7. **CLI parity:** The same journey can be run with command-line inputs and machine-readable JSON output using the same verification engine.

## 6. P0 / P1 / excluded

**P0 (launch-critical):** Real X Layer importer + REF closure, canonical manifest and integrity revalidation, deterministic limited composer, local evaluator parity, stateless SAT comparison, independently checked counterexamples, sample workspace, minimal web UI, CLI, artifact export, read-only structural pre-flight, documented failure/UNKNOWN behavior, automated regression tests.

**P1 (only after P0 stable):** Up to eight beats of stateful trace *difference* (zero initial state and explicit input sequence), optional local project persistence and better visual diagnosis. If schedule slips, P1 is cut first.

**Excluded:** Full NAND editor, BLIF/Verilog toolchain, challenge task solver, marketplace, wallet connection, token purchase, transaction broadcast, new circuit publication, arbitrary cross-chain execution, unlimited solver/runtime, unbounded stateful equivalence, malicious-RPC resistance, mobile-native app, promises of 10× productivity.

## 7. Decision-quality release gates

- **G1: Live import parity.** Known X Layer circuits import with correct byte hashes, dependency closure and reproducible local outputs.
- **G2: Deterministic composition.** The audited XOR+NAND half-adder fixture generates byte-identical netlists across repeated builds and the expected 4/4 truth table.
- **G3: Verification integrity.** Every SAT witness is replayed; unknown/timeout/missing oracle never becomes a proof; 9/9 integrity negative fixtures stay green.
- **G4: Interface parity.** Web and CLI generate equivalent results and canonical artifacts from the same input fixture.
- **G5: Honest pre-flight.** The documented burn failure is displayed as STRUCTURALLY ACCEPTED, not transaction success.
- **G6: External usefulness.** Aim for ≥4/5 pilot developers independently completing the flagship journey; this is a **proposed success target**, not existing evidence.
- **G7: Submission compliance.** Confirm current event rules and determine whether a separately authorized onchain circuit publication is necessary for the final submission; obtain approval outside this product's transaction flows.

## 8. Hard technical constraints from M0.5

X Layer mainnet chain ID **196** only; verify `eth_chainId` per session. Stateless circuits are the exact-equivalence domain. Default limit **2,500 equivalent gates**, user-adjustable to **5,000**; conservative REF nesting cap **64**, solver budget **5 s / 64 MiB**. Native Minisat22/CDCL used in audit; browser WASM or local service deployment requires separate performance validation. Cache by content **and** environment hashes, revalidate before report/export/pre-flight. Processor beacon and factory implementation hashes matter: proxy bytecode alone is insufficient. Re-read fee; audit observed **0.0013 OKB**, not a permanent price. Avoid claiming full read-only publication simulation where the RPC cannot supply ERC-1155 storage overrides.

## 9. Delivery strategy and open product decisions

**Approved product decision:** Both web and CLI ship in v1. They share a headless core and common report schema; no duplicated parsing, solver, or proof logic.

**Implementation decision to resolve in architecture:** M0.5's handoff suggests a backend-first verification service, while its constraints document allows local-first/browser WASM. Select hosting only after testing packaging, solver isolation, browser resource enforcement, and web/CLI artifact parity. The PRD requires behavior, not a prematurely chosen deployment topology.

**Other decisions needing implementation-level definition:** exact UI wiring affordance (table vs lightweight graph), oracle file schema, stable CLI command names, export archive structure, authoritative release artifact signatures, and completion of hackathon submission verification.

## 10. Sources and provenance

Primary project references, supplied 16 November 2026: `MVP_CONSTRAINTS.md` §§1–10; `FINAL_HANDOFF.md` top five findings; `FINAL_VERDICT.md` four gates; `DIFFERENTIATION_REPORT.md` D1–D4; `INTEGRITY_VERIFICATION.md` B1–B5; `WIRING_CANARY_SCALE.md` C1–C6; `PUBLICATION_READINESS.md` A1–A4; original M0 `EVIDENCE_REGISTER.md`, `WIRING_CANARY_EXPERIMENT.md`, `XLAYER_COMPATIBILITY.md`.

**Evidence language:** “Audit-reported” means experiment outcomes documented by OpenCode; “Product decision” means scope chosen here; “Proposed target” means a future acceptance or validation goal. Do not blend these statuses in external claims.
