# M4.5-0 authorized tape-out — independent security review

**Status: INDEPENDENT REVIEW (informational). Version 1.0. Date 2026-11-22.**
**Reviewer: OpenCode / HY4 Flash (supporting engineer). No founder authority is exercised here.**
This review does not approve a design, a founder decision, a wallet, a key, a signer, a transaction or a release.

## 0. Reviewed material and provenance

| Item | Value |
|---|---|
| Accepted read-only main | `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b` |
| Proposed authority architecture | `codex/flip-m45-authority-design` @ `8ea1b26c2667b2db86c34087e25c976f121c147e` |
| Proposal's own declared baseline | `09f2482beae84be6d919ecd6957c4153d1924cca` (accepted M4 **before** the agent-controller/portable-project merge) |
| Review branch | `opencode/flip-m45-authorization-security-review` (created from accepted main) |
| Allowed write scope | `docs/evidence/m45-authorization-security-review/`, `fixtures/m45-authorization-security-review/` only |
| Runtime code / schemas / acceptance checks / original evidence | Unchanged by this review |
| Keys, wallets, signing, broadcast, spend | None created, connected, signed, broadcast or spent |

Primary documents read at the proposed commit:
`docs/architecture/FLIP_ADR_AUTHORIZED_TAPEOUT.md`,
`FLIP_APPROVAL_PROTOCOL.md`, `FLIP_TRANSACTION_STATE_MACHINE.md`,
`FLIP_TRANSACTION_THREAT_MODEL.md`, `docs/milestones/M45_0_DECISION_REGISTER.md`,
`docs/milestones/M45_0_HANDOFF.md`.

Accepted interfaces read at the accepted main commit:
`README.md`, `AGENTS.md`, `MVP_CONSTRAINTS.md`, the PRD,
`FLIP_TECHNICAL_DESIGN.md`, `FLIP_AGENT_OWNERSHIP_MATRIX.md`,
`FLIP_IMPLEMENTATION_DEPENDENCIES.md`, `docs/agents/WORKFLOW_INTEGRATION.md`,
`docs/schema/m45-agent-workflow/README.md`, `docs/schema/m45-agent-portable/README.md`,
`docs/schema/m45-portable-project/README.md`,
`docs/milestones/M45_AGENT_PORTABLE_POST_MERGE_ACCEPTANCE.md`, and the
`STOP_AUTHORIZATION` implementation in `packages/flip-core/src/flip_core/agent_operations.py`
and `agent_portable_adapter.py`.

**Evidence labels used below:** `[OBSERVED]` direct repository/RPC observation in this review;
`[DOCUMENTED]` primary source documentation read in this review; `[INFERENCE]` reviewer reasoning
from observed/documented facts; `[UNKNOWN]` not established; `[SPECULATION]` explicitly not evidence.

## 1. Executive summary

| Readiness question | Verdict |
|---|---|
| Design-only readiness | **CONDITIONAL** — the package is a coherent, carefully fail-closed *specification*, but it is written against a stale baseline and contains unenforceable live claims. Safe to study; not safe to treat as accepted architecture. |
| Mock-only implementation readiness | **CONDITIONAL GO** — possible with synthetic brokers, signers, chain doubles and no keys/wallet/RPC writes, provided the interface boundary to the accepted controller is designed first and all 12 decisions stay pending. |
| Live signer integration readiness | **NO** — no device/profile is certified, no raw-sign capability is demonstrated, and the required OS/device separation has no platform evidence. |
| Mainnet execution readiness | **NO** — critical D03/D05/D10/fee-model gates are unresolved and current chain state contradicts the proposal's immutability assumptions. |

The strongest parts of the proposal are its honesty about signed-EOA capability after expiry, the nonce-family/reservation model, and its refusal to relabel ambiguous network outcomes as success. The weakest parts are platform assumptions, the stale integration baseline, the fee/finality model, and the execution-time immutability claim.

No decision was approved. All D01–D12 remain **PENDING**.

## 2. Part A — architecture findings

### A-01 — Stale baseline and missing controller adapter boundary — HIGH

`[OBSERVED]` The proposal declares baseline `09f2482` and states "Remote main matched that baseline at preparation". Accepted main is `b537eb6`, whose post-merge acceptance explicitly states the authority design commit `8ea1b26` **is not an ancestor** and that no signing capability exists. `[OBSERVED]` Accepted main ships a bounded agent controller (`/api/agent/v1/execute`, `flip workflow`) and an agent-portable adapter whose publication purpose prepends a **terminal** `STOP_AUTHORIZATION` step; `agent_operations.py` returns `signingCapability=False` and `retryable=False`. `[INFERENCE]` The proposal introduces a "Proposal builder" and a broker-facing agent API but never defines how an agent request crosses from the accepted terminal handoff into the proposed authority plane. Without a version-dispatched, explicitly reviewed adapter there are two competing authority stories: a terminal handoff that grants nothing, and a proposal plane whose inputs might be mistaken for approval inputs. Required fix: a separate additive contract that consumes the *output* of `STOP_AUTHORIZATION` as inert proposal evidence, never as a grant, with version dispatch and no changes to frozen controller bytes.

### A-02 — Portable-project authority invariant is not preserved explicitly — HIGH

`[OBSERVED]` The portable-project contract says revision chains and metadata "authenticate neither the author nor a global project namespace", that CURRENT cannot be declared by metadata, and that no signature/author permission is inferred. `[OBSERVED]` The ADR says future portable projects "may carry passive intent/receipt references and immutable public transaction evidence under their own approved version". `[INFERENCE]` This is compatible only if those references are explicitly inert, schema-tagged and never consulted by the broker as authorization. The proposal does not define that tagging or a fresh-approval trigger for imported references. Required fix: state that every import requires a new immutable intent and grant, and define the reference fields as non-executable metadata with a negative fixture.

### A-03 — Unrealistic/unenforceable platform separation — HIGH

`[OBSERVED]` The ADR requires a "separate broker OS identity or human-controlled device, protected approval UI, hardware user presence and ACLs that exclude the agent", and says a broadly privileged agent controlling the broker host cannot be granted transaction access. `[OBSERVED]` Accepted Flip is a local loopback service driven from the same user account by coding agents and browser sessions; no separate broker identity, device or OS-ACL model exists. `[INFERENCE]` This is an external deployment precondition, not a code feature. No supported-platform matrix, enrollment procedure, ACL verification method or manual test result is supplied. `M05` is explicitly unexecuted. Required fix: before any live discussion, produce a platform-specific deployment evidence pack (identity boundaries, process/ACL layout, device/firmware, human-presence path) reviewed by Codex and a human operator.

### A-04 — Human-presence proof is circular at the application layer — HIGH

`[OBSERVED]` The grant is an Ed25519 application signature produced by the broker after "protected human presence"; the signer adapter verifies it against an enrolled broker public key. `[OBSERVED]` The same document concedes that an agent with administrator access to the broker host, key storage and human UI defeats the assurance. `[INFERENCE]` The broker key therefore authenticates *the broker*, not *a human*, unless the human-presence path is independently attested outside the agent-controlled host. A copied grant is correctly blocked by journal state, but a coerced grant produced by a compromised broker is not. Required fix: independent presence attestation and a documented adversary model for broker compromise; otherwise live activation stays blocked.

### A-05 — Execution-time immutability claim is false for the current deployment — CRITICAL (live only)

`[OBSERVED]` The ADR requires "verified effective immutability of the relevant execution context or an independently reviewed atomic onchain guard" and notes that a boolean factory seal is insufficient. `[OBSERVED]` Bounded read-only RPC on 2026-11-22 returned factory `isSealed() = 0`, factory owner `0xb3d85b42…d3138`, and ERC-1967 implementation `0x336e9f0f4c3fee7c8c803377e4dea00293f4ae2a`. `[DOCUMENTED]` The open TAP-10 v1.2 PR lists the current X Layer factory implementation as `0xb41C1E7602EB5734BE2430b72178cCb814A5293d` and states that, while processors are frozen, an unsealed factory can still change the processor table and deregister a processor. `[OBSERVED]` Circuit beacon `owner() = 0` and `implementation() = 0x977f2178…9b2`, consistent with frozen processor code. `[INFERENCE]` Processor code may now be frozen, but the factory is unsealed with an owner and an implementation not listed in either TAP-10 v1.1 or the open v1.2 draft. A pre-sign read cannot enforce processor registration or implementation at inclusion. Required fix: D10 must stay blocked until the exact current implementation is identified, the factory-registration risk is accepted/reviewed, and either an atomic guard or enforceable immutability is demonstrated at the reviewed chain state. No guard is implemented by this proposal.

### A-06 — Total-debit bound cannot be enforced from JSON alone — HIGH

`[OBSERVED]` The approval protocol defines `maxNativeDebitWei`, `maxGasLimit`, fee caps and `otherFeeCapWei`, and warns that unknown additional fees block live use. `[DOCUMENTED]` Current official X Layer documentation describes an OP Stack rollup with a `GasPriceOracle` predeploy and an intrinsic L1 data fee charged from serialized transaction size and Ethereum gas price at inclusion, independently of the L2 `gasLimit × maxFeePerGas` bound; OP Stack guidance says the L1 fee may differ from the estimate and cannot be custom-set. `[OBSERVED]` `eth_estimateGas` and a synthetic `getL1Fee(bytes)` read-only call were accepted by the public RPC; the sampled historical receipt did not expose `l1Fee` fields. `[INFERENCE]` A JSON `otherFeeCapWei` is a policy number, not an onchain enforcement mechanism. Required fix: derive and verify a complete bounded fee formula (L2 + L1 components) at the signed transaction size, with a worst-case assumption reviewed against current chain semantics; otherwise D03/D06 stay blocked.

### A-07 — Finality model is unresolved and operator independence is unavailable — HIGH

`[OBSERVED]` The public RPC returned distinct `latest`, `safe` and `finalized` blocks (heights 76,571,210 / 76,571,101 / 76,569,783 in this session; `latest` and `pending` were equal). `[DOCUMENTED]` The open TAP-10 v1.2 PR states that on X Layer latest blocks can still be rewritten until posted to Ethereum and that its own protocol uses `safe` on L2. `[OBSERVED]` Official RPC documentation lists `https://rpc.xlayer.tech` and `https://xlayerrpc.okx.com`; the second endpoint did not respond in this session. `[DOCUMENTED]` TAP-10 v1.2 notes that default X Layer nodes belong to OKX, which also runs the sequencer. `[INFERENCE]` The proposal's "independent operator observations" cannot be satisfied from the official endpoints alone, and the meaning of the `finalized` tag is not established as a verified-rollup proof. Required fix: D05 stays pending until a chain-specific finality evidence policy and genuinely independent observations are documented; no invented block count.

### A-08 — Signer capability is assumed, not demonstrated — HIGH

`[OBSERVED]` The ADR recommends a hardware-backed EOA with an external raw signer that returns signed bytes before submission, while acknowledging that OKX's documented send path uses `eth_sendTransaction` with editable gas fields and that raw-sign support is unverified. `[DOCUMENTED]` OKX provider documentation describes `eth_requestAccounts`, `eth_sendTransaction`-style flows and EIP-5792 `wallet_sendCalls`; no raw-sign-only capability was established in the sources read. `[INFERENCE]` The whole exact-field verification chain depends on receiving raw bytes *before* broadcast. A combined sign-and-send provider cannot satisfy it. Required fix: device/app/firmware matrix, cross-language raw-signing vectors and a fail-closed adapter test before D01/D04 activation.

### A-09 — Unspecified and underspecified states — MEDIUM

`[OBSERVED]` The state machine defines 14 labels and a transition table. `[INFERENCE]` The following conditions have no explicit durable state or are only implied: (a) raw signed bytes leaked/exfiltrated outside the broker's protected store; (b) wallet chain/account change between APPROVED and SIGNING; (c) L1 fee or base fee spike after SIGNED but before dispatch; (d) receipt present at one provider and absent/disagreeing at another; (e) protected payload-store write error after signature return; (f) broker key rotation while signed bytes are still executable; (g) clock uncertainty above threshold during an existing grant; (h) `nextId` changed by an unrelated concurrent publication at receipt time (only A29 describes the test, not the state). Required fix: add explicit states/dispositions and negative fixtures; do not silently fold them into `SUBMISSION_UNKNOWN` or `PENDING`.

### A-10 — Recovery procedures are specified as properties, not runbooks — MEDIUM

`[OBSERVED]` The state machine has a crash table and says journal rollback freezes writes and increments a recovery epoch under human control; A22/A21 specify assertions. `[INFERENCE]` No step-by-step reconciliation runbook is given for: lost signed payload, used grant found in a stale backup, revocation racing an in-flight dispatch, replacement losing to the original, or restoring reservations after a reorg that exceeds policy. Required fix: human-readable recovery runbooks with exact authority checks and evidence capture, tested with fault injection.

### A-11 — Trust-boundary wording conflicts with accepted process topology — HIGH

`[OBSERVED]` The ADR says "No agent or verification process can write a grant … the agent-facing API and human authority must remain separate security principals" but also allows distinct services to share one trusted broker process. `[OBSERVED]` The accepted controller, CLI and API all run in one local service/process topology. `[INFERENCE]` Unless the broker is a separately deployed identity/process with enforced IPC rights, this boundary is only a naming convention. Required fix: explicit process/UID/IPC model and an OS-level denial test where the agent tries to call grant/signer/submit verbs (A25).

### A-12 — Test specification coverage gaps for the requested adversarial set — MEDIUM

`[OBSERVED]` The threat model has 33 automated cases (A01–A33), five manual and four live cases. `[INFERENCE]` Several requested categories are only partially represented: broker key theft (A25 is about agent read attempts), gas/fee underestimation (no explicit case), concurrent rolling-ceiling spending (A11/A12 approximate it), expired-but-signed (A28/A06), wallet semantics divergence (A24), and execution-time change (A15/A16). Required fix: an explicit mapping matrix and added cases; see the mapping in `SECURITY_REVIEW.md` §4 and `fixtures/m45-authorization-security-review/threat-cases.json`.

### A-13 — Repository guard change weakens directory-level protection — MEDIUM (governance)

`[OBSERVED]` The proposal's ancillary commit changes `scripts/check_m1_repository.py` from protecting the directory tuple `("AGENTS.md", "docs/product", "docs/architecture", "docs/audits")` to protecting only files present in the fixed `SEED` tree. `[OBSERVED]` Accepted main has a substantially expanded version of that guard. `[INFERENCE]` The intent (allow additive successor ADRs) is reasonable, but the mechanism would stop protecting any future non-seed file under those directories. This is a Codex-owned shared file and outside this review's write scope. Required fix: enumerate accepted protected paths explicitly, or add an additive-only allowlist with inventory checks, and review against the current accepted guard.

### A-14 — Key lifecycle is asserted but not specified — MEDIUM

`[OBSERVED]` The proposal requires an enrolled broker Ed25519 key, keyId, revocation and anti-rollback checkpoint, while stating "No key is created by this design milestone". `[INFERENCE]` Enrollment, rotation, compromise response and recovery-epoch custody are needed before any live use and are absent. Required fix: D11 evidence pack, including golden signature vectors and an independent reviewer.

## 3. Trust boundaries — reviewer assessment

| Boundary in proposal | Reviewer verdict | Basis |
|---|---|---|
| Agent/project → builder | Plausible with strict typed input; lacks mapping to the accepted controller's `stop_authorization` output | A-01, A-02 |
| Builder/estimator → broker | Sound in principle; depends on complete fee model | A-06 |
| Human surface → broker | **Not established** on accepted platform topology | A-03, A-04, A-11 |
| Broker → signer | Sound only with a certified raw-sign adapter | A-08 |
| Signer → journal | Sound with independent parsing and sender recovery; needs golden negatives | A-08, A-12 |
| Journal → submission | Sound with hash-bound permit and protected payload store; leak case unspecified | A-09 |
| RPC → reconciler | Sound fail-closed intent; independent operators unavailable and finality semantics unresolved | A-07 |
| Contract → receipt verifier | Claim unenforceable at inclusion under current factory state | A-05 |
| Journal → restart worker | Sound properties; no runbook | A-10 |
| Exports/logs → user | Aligned with accepted portable-project contract; needs explicit inert-reference schema | A-02 |

## 4. Part C — adversarial threat model (16 required scenarios)

Severity: **C** critical (live loss/authority breach), **H** high, **M** medium. "Control required" is a *specification*, not an implemented capability. Fixture case IDs are in
`fixtures/m45-authorization-security-review/threat-cases.json`.

| # | Scenario | Severity | Control required | Proposal coverage | Gap |
|---|---|---|---|---|---|
| 1 | Agent impersonating human approval | C | Separate identity/device, authenticated challenge bound to intentHash, no approve verb on agent API, OS denial test | A01, M01/M05 | Platform evidence missing; circular broker-key trust (A-03/A-04/A-11) |
| 2 | Malicious project metadata | H | Strict typed input; inert labels; validated digests; no authority from imports | A03, A33, portable README | Reference fields not schema-tagged inert (A-02) |
| 3 | Changed calldata after approval | C | Recompute calldata from netlist+ABI; exact byte/hash equality; re-review after any change | A04 | Adequate as specification; must bind accepted controller output hash (A-01) |
| 4 | Signer or network substitution | C | Enrolled key/chain/account; independent raw parse + sender recovery; reject unknown variants; EIP-1193 invalidation | A05, A24 | Device/chain matrix unverified (A-08) |
| 5 | Malicious/compromised RPC | H | Hash/nonce tracking, canonical block/finality checks, provider disagreement fail-closed | A14, A18, A23 | Independent operators unavailable; second official endpoint unreachable (A-07) |
| 6 | Changed factory/beacon/processor | C | Immutability or atomic guard at inclusion; pinned implementation + registration evidence | A15, A16 | Current factory unsealed with unlisted impl; processor-only freeze insufficient (A-05) |
| 7 | Gas/fee underestimation | H | Full L2 + L1 fee bound, worst-case serialization size and L1 gas price, bounded uint256 math | A23, protocol §73 | `otherFeeCapWei` not enforceable; no explicit A-case (A-06, A-12) |
| 8 | Pending nonce replacement | H | One active nonce family per sender; DB uniqueness + fencing; new intent/grant for same-nonce change | A07, A09, A20 | Adequate as specification; external wallet activity must freeze (state machine §101) |
| 9 | Duplicate submission after ambiguous RPC | C | Persist dispatch event before send; precomputed hash; identical-byte retry only after reconciliation | A08, A21 | Adequate; needs leak/partial-store state (A-09) |
| 10 | Expired but already signed | C | Treat signed bytes as live capability; hold reservation until nonce family unexecutable; no UI revocation promise | A06, A28 | Adequate; grant expiry/clock-uncertainty edge state missing (A-09) |
| 11 | Broker key theft | C | Protected key custody, keyId enrollment/revocation, anti-rollback checkpoint, independent review | A25 (partial), D11 | No explicit key-theft case or lifecycle (A-14) |
| 12 | Broker rollback / lost journal | C | Recovery epoch/checkpoint under human identity; freeze writes; reconcile every account | A22, crash table | No reconciliation runbook (A-10) |
| 13 | Reorg after apparent confirmation | H | REORGED state, invalidate receipt, restore worst-case exposure, finality policy | A17, A18 | Finality evidence/operator policy unresolved (A-07) |
| 14 | Concurrent spending against rolling ceilings | H | Serializable reservation; worst-case family exposure; nonnegative available budget property | A11, A12 | Adequate as specification; needs property-test evidence |
| 15 | Wallet differs from raw-signature assumptions | H | Certified adapter; reject combined sign-and-send; exact-field decode and compare | A24, M04 | No certified device/profile (A-08) |
| 16 | Execution-time contract change between verify and inclusion | C | Atomic onchain guard or demonstrated effective immutability at inclusion | A16, D10 | Explicitly unresolved; no guard implemented (A-05) |

## 5. Recovery scenarios — additional reviewer findings

The proposal covers crash points, reorgs, replacement races and journal rollback at a property level. The following recovery scenarios are not specified with an executable procedure: (a) protected payload store fails after signature return; (b) signed bytes found outside protected storage; (c) broker key rotation with unresolved signed exposure; (d) revocation committed after dispatch claim but before RPC response; (e) finalization evidence disagrees between providers at CONFIRMED; (f) factory registration changes after a reviewed verification but before signing; (g) L1 fee bound is breached by an inclusion-time price move. Each must produce a durable diagnostic and a fail-closed state, not a silent retry or cap increase.

## 6. Recommendation summary

See `FOUNDER_DECISIONS.md` for D01–D12, `COMPATIBILITY_GAPS.md` for X Layer evidence, `MINIMUM_SAFE_PLAN.md` for gated implementation and `HANDOFF.md` for provenance and handoff constraints.

**Reviewer position:** keep the entire authority architecture PROPOSED, keep all live paths disabled, and permit only mock-only engineering after the founder records decisions and Codex approves the controller/broker boundary. No founder decision is approved by this review.
