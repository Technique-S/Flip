# D01–D12 — independent review of founder decisions

**Status: REVIEW ONLY. All twelve decisions remain PENDING.**
The reviewer does **not** approve, reject or defer on the founder's behalf. "Safe to approve now" below
means *reviewer assessment of whether sufficient evidence exists for a founder to record a binding
decision*, not a decision itself. "Mock-only proceed" is a technical readiness statement, not authority.

Source: `docs/milestones/M45_0_DECISION_REGISTER.md` at `8ea1b26`. Register status at review: all PENDING.

## Summary matrix

| ID | Safe to approve now? | Mock-only implementation may proceed? | Live activation must remain blocked? |
|---|---|---|---|
| D01 | **No** — no device/profile certified | Yes, with fake raw signer only | **Yes** |
| D02 | **No** — no platform/ACL evidence | Yes, with fake human fixture only | **Yes** |
| D03 | **No** — no positive caps or approver identity supplied | Yes, zero-cap defaults only | **Yes** |
| D04 | **No** — sender/target policy not enrolled | Yes, synthetic account/target only | **Yes** |
| D05 | **No** — finality evidence and operator independence unresolved | Yes, fake finality provider only | **Yes** |
| D06 | **No** — full fee model not verified | Yes, UNKNOWN/blocked paths only | **Yes** |
| D07 | **No** — first publication scope and verification policy not fixed | Yes, synthetic artifact only | **Yes** |
| D08 | **No** — gate owners/reviewers not named | Yes, as staged mock work | **Yes** |
| D09 | **No** — time/recovery policy not calibrated | Yes, simulated clock only | **Yes** |
| D10 | **No** — current execution context fails immutability evidence | Yes, with adversarial mock doubles | **Yes** |
| D11 | **No** — enrollment/rotation/recovery not specified | Yes, synthetic signatures only | **Yes** |
| D12 | **No** — operational replacement response not defined | Yes, no replacement enabled | **Yes** |

No decision can be approved on the strength of this review. A founder may record a decision only with
the evidence column below, against an immutable document revision, using the register's own capture
format (decisionId, status, selected value/profile hash, rationale, constraints, founder identity,
time, reviewed commit, evidence reference).

---

## D01 — Signer / custody profile

- **Codex's proposed default.** Dedicated, locally controlled hardware-backed EOA; human-controlled external signer with a reviewed raw-signing adapter that returns signed bytes before submission. Reject smart accounts, multisig, session keys, delegated EOAs, hosted/agentic wallets and software keystores reachable by the agent.
- **What it protects.** Key custody stays with the human; a hardware confirmation step exists; the broker can independently decode exact fields before dispatch; no unattended signing path.
- **Main failure mode.** No specific device/app/firmware/provider is certified. OKX's documented path uses combined `eth_sendTransaction` with editable gas; a provider that cannot return raw signed bytes before broadcast breaks the exact-field guarantee entirely. A hardware button also does not certify calldata semantics.
- **Alternatives.** OKX extension/mobile provider (later, needs different adapter model), other EIP-1193/WalletConnect transport, smart account/multisig/onchain guard (separate profile), manual unsigned export (diagnostic only), software/hosted keystore (rejected).
- **Required evidence.** Exact device/app/firmware/adapter version matrix; raw-sign-only capability demonstration with no broadcast; cross-language vectors; rejection test for combined sign-and-send and silent field edits; account/chain-change invalidation test (M04).
- **Safe to approve now?** **No.** Compatibility unverified.
- **Mock-only proceed?** **Yes** — fake signer that emits synthetic raw bytes; no real key or wallet.
- **Live activation blocked?** **Yes**, until a certified profile and independent reviewer are recorded.

## D02 — Protected human approval boundary

- **Proposed default.** Protected UI under a separate human OS identity/device with authenticated human presence and independent semantic display; agent-supplied booleans/model output/forged browser events rejected.
- **What it protects.** Attempts to distinguish a human approver from an agent with computer-control tools; prevents a local HTTP/loopback request from being treated as consent.
- **Main failure mode.** The accepted application runs in the user's OS principal. The ADR itself says an agent with administrative control of the broker host and UI cannot be granted safe access. No supported-platform matrix, ACL proof, enrollment procedure or executed M01–M05 evidence exists; the auditory screen-reader gap from M4 remains open.
- **Alternatives.** Same-desktop approval (explicitly insufficient for this threat model), human-controlled second device (proposed), external trusted execution/attestation (future, not specified).
- **Required evidence.** Platform-specific identity/process/ACL layout; demonstration that agent tools cannot invoke approve/revoke, read key material or reach human UI; keyboard and screen-reader pass/refusal/expiry drill; independent observer trace (M01–M05).
- **Safe to approve now?** **No.**
- **Mock-only proceed?** **Yes** — deterministic fake human fixture, clearly labeled non-authoritative.
- **Live activation blocked?** **Yes**, until the boundary is demonstrated on the exact deployment platform.

## D03 — Policy, caps and approver identity

- **Proposed default.** Live disabled; all native/resource caps zero. Every action binds exact quoted value and gas fields; per-action and rolling 24-hour native/resource ceilings must be entered as decimal quantities.
- **What it protects.** Loss containment and explicit spend ceilings; zero-cap default prevents accidental live operation.
- **Main failure mode.** No positive caps, permitted token contracts/IDs or approver identity are supplied. On X Layer an intrinsic L1 data fee can move at inclusion and is not bounded by the signed L2 gas fields; a JSON `otherFeeCapWei` is a number, not enforcement.
- **Alternatives.** Blanket approval or automatic cap increases (unsafe), per-action-only caps without rolling window (weaker), dedicated low-balance account (containment, not enforcement).
- **Required evidence.** Founder-supplied decimal caps, rolling window definition and clock, approver identity, permitted token contracts/IDs, and a verified full-fee formula including L1 data fee.
- **Safe to approve now?** **No.**
- **Mock-only proceed?** **Yes** — zero caps and mock budgets only.
- **Live activation blocked?** **Yes.**

## D04 — Account / chain / target profile

- **Proposed default.** One enrolled ordinary EOA, no code/delegation, one active nonce family per sender, chain 196 only, one existing registered reviewed processor; no new processors, arbitrary calls, batches, transfers or allowances.
- **What it protects.** Narrow replay/nonce surface and a known target ABI; avoids smart-account/session-key complexity.
- **Main failure mode.** The exact sender and target are not enrolled, and registration on the current chain is not verified. `[OBSERVED]` Current factory `isCPU`/processor-table state can change while unsealed; `cpuCount` rose from 430 (fixture block 76,277,110) to 441 (review session), and processor-0 `nextId` from 104 to 105. Out-of-band wallet activity invalidates nonce assumptions.
- **Alternatives.** Smart account/multisig/delegated EOA (separate signature/nonce/gas profile), multiple senders/targets (later profile).
- **Required evidence.** Enrolled sender address and chain, target registration and code/delegation check at the reviewed block, account-isolation procedure, external-activity freeze rule.
- **Safe to approve now?** **No.**
- **Mock-only proceed?** **Yes** — synthetic addresses only.
- **Live activation blocked?** **Yes.**

## D05 — Finality policy

- **Proposed default.** `CONFIRMED` requires matching canonical receipt/content and a verified finalized-block policy with independent operator observations; if unsupported, stay PENDING and invent no block count.
- **What it protects.** Avoids treating a sequencer acknowledgement or single-provider success as durable settlement; supports reorg recovery.
- **Main failure mode.** `[OBSERVED]` `latest`, `safe` and `finalized` tags are exposed but differ (review session: 76,571,210 / 76,571,101 / 76,569,783). `[DOCUMENTED]` Open TAP-10 v1.2 says X Layer latest blocks may be rewritten until posted to Ethereum and uses `safe`; official endpoints are OKX-operated and the second endpoint did not respond. Independent operator observations are not established and `finalized` semantics are undocumented.
- **Alternatives.** Fixed confirmation count (weaker, rejected by default), sequencer preconfirmation (not finality), user-run node plus independent operator (future), L1-settlement evidence (needs new design).
- **Required evidence.** Chain-specific finality definition, provider operator identities and independence proof, block-hash/canonicality checks, disagreement handling, reorg drill (A17), and exact tag semantics at the reviewed RPC version.
- **Safe to approve now?** **No.**
- **Mock-only proceed?** **Yes** — fake finality provider and reorg injection.
- **Live activation blocked?** **Yes.**

## D06 — UNKNOWN / blocking policy

- **Proposed default.** UNKNOWN gas, other-fee bounds, resource sufficiency or execution context blocks signing; no manual estimate override or proof flag bypasses the quote gate.
- **What it protects.** Prevents fabricated sufficiency and false success claims; aligns with Flip's existing UNKNOWN semantics.
- **Main failure mode.** The complete fee model is not verified. `[DOCUMENTED]` X Layer/OP Stack has an intrinsic L1 data fee that varies with serialized transaction size and L1 gas price at inclusion; our `eth_call`/`eth_estimateGas` probes are read-only and prove nothing about a paid transaction's success.
- **Alternatives.** Manual override (unsafe), bounded worst-case formula with reviewed evidence (acceptable if proven), separate fee-reservation contract (future).
- **Required evidence.** L2 and L1 fee formula and evidence hash, `getL1Fee` behavior on the exact serialized signed transaction shape, receipt fee fields, worst-case bound and rejection of unbounded cases (A23).
- **Safe to approve now?** **No** as a complete decision; the *principle* that UNKNOWN blocks is already a safe design constraint for mock work.
- **Mock-only proceed?** **Yes** — UNKNOWN paths and fail-closed diagnostics.
- **Live activation blocked?** **Yes.**

## D07 — First publication scope / verification policy

- **Proposed default.** One stateless tape-out to an existing processor per human grant; no acquisition, transfers, allowances, new processors, batches or autonomous publication. Recommended verification requires explicit trusted intent anchor, EQUIVALENT comparison and passing declared tests; UNKNOWN/STALE/mismatched evidence rejected.
- **What it protects.** Keeps the first release inside the accepted MVP constraints and prevents a verification verdict from becoming spending authority.
- **Main failure mode.** The exact verification policy hash is not fixed, and the accepted controller already defines `EQUIVALENT` as relative to selected references, not intended correctness. A "successful verification" can be misread as publication readiness.
- **Alternatives.** Broader operations (separate profiles), no verification requirement (unsafe), manual human review of raw netlist (slower).
- **Required evidence.** Fixed policy hash, trusted-anchor definition, declared test set, mapping from the accepted controller's output to an inert proposal input (A-01/A-02), and negative fixture A33.
- **Safe to approve now?** **No.**
- **Mock-only proceed?** **Yes** — synthetic verified artifact.
- **Live activation blocked?** **Yes.**

## D08 — Staged authorization / gate ownership

- **Proposed default.** Development approval permits mocks/local simulation only; code review, release enablement and each live transaction are separate authorizations.
- **What it protects.** A generic task or release instruction cannot become permission to spend; matches AGENTS.md and the ownership matrix.
- **Main failure mode.** No owners/reviewers are named for each gate, and the proposal's ancillary guard change touches a Codex-owned acceptance script.
- **Alternatives.** Single broad approval (rejected), founder self-review (weaker separation).
- **Required evidence.** Named owner and independent reviewer per gate, immutable assignment record, and Codex review of the guard change against accepted main.
- **Safe to approve now?** **No** until owners are named; the *principle* is consistent with accepted governance and can guide mock work.
- **Mock-only proceed?** **Yes** — staged mock work only.
- **Live activation blocked?** **Yes.**

## D09 — Time limits / clock recovery

- **Proposed default.** Intent lifetime ≤300 s, observation age ≤30 s, fail closed on clock rollback, grant expiry no later than intent expiry.
- **What it protects.** Limits stale-context windows and application-level authority duration.
- **Main failure mode.** These are application limits only; a signed EOA transaction remains executable after expiry. Clock uncertainty handling during an existing signing attempt is underspecified.
- **Alternatives.** Longer windows (higher stale risk), shorter windows (operational friction), monotonic trusted clock service (future).
- **Required evidence.** Calibrated values, clock-rollback and clock-uncertainty drill, expiry-after-signing negative fixtures A06/A28, and wording confirmed in UI that expiry does not revoke a signed transaction.
- **Safe to approve now?** **No.**
- **Mock-only proceed?** **Yes** — simulated clock only.
- **Live activation blocked?** **Yes.**

## D10 — Execution-time guard / immutability — **critical gate**

- **Proposed default.** Live requires verified effective immutability of the relevant execution context or a separately reviewed atomic onchain guard; rechecks alone are not sufficient.
- **What it protects.** Closes the race where an implementation/resource-cap change occurs after the last read and before inclusion.
- **Main failure mode.** `[OBSERVED]` Current factory is unsealed (`isSealed() = 0`) with a nonzero owner and ERC-1967 implementation `0x336e9f0f…93f4ae2a`, which is not the implementation listed in TAP-10 v1.1 (`0x74956236…`) or the open v1.2 draft (`0xb41C1E76…`). `[DOCUMENTED]` v1.2 says factory control can still change processor registration while processor code is frozen. A boolean seal is explicitly insufficient in the proposal itself; no guard is implemented.
- **Alternatives.** Demonstrated effective immutability of *all* relevant context (needs verified current implementation and registration behavior), atomic wrapper guard (changes target/ABI; separate profile), accept risk via successor ADR (founder-only, not reviewer).
- **Required evidence.** Verified implementation identity, owner/seal state, processor-registration immutability proof or reviewed guard with atomic revert evidence (A16), and exact finality/receipt interpretation.
- **Safe to approve now?** **No — this is the strongest blocker.**
- **Mock-only proceed?** **Yes** — with adversarial mutable-contract doubles.
- **Live activation blocked?** **Yes.**

## D11 — Broker key / authentication model

- **Proposed default.** Protected broker application key, fixed Ed25519 grant/dispatch authentication, pinned public-key enrollment and anti-rollback checkpoint, independent raw parsing and sender recovery.
- **What it protects.** No bearer flag, agent-readable key or unsigned variant can forge a grant; copied signatures cannot bypass journal revocation.
- **Main failure mode.** Enrollment, rotation, compromise response and checkpoint custody are unspecified. Theft of the broker key plus host access could produce apparently valid grants; A25 only tests agent read attempts, not theft.
- **Alternatives.** Hardware-backed broker key/HSM (stronger, more setup), multi-party approval (separate profile), agent-readable bearer flag (rejected).
- **Required evidence.** Key lifecycle and revocation procedure, golden Ed25519 vectors, malleability/invalid-key golden tests, anti-rollback drill, independent security reviewer sign-off.
- **Safe to approve now?** **No.**
- **Mock-only proceed?** **Yes** — deterministic synthetic signatures only; no real key.
- **Live activation blocked?** **Yes.**

## D12 — Replacement / cancellation

- **Proposed default.** No automatic fee replacement or cancellation in the initial profile; future variants require a new intent/grant, same-nonce family accounting and exact caps.
- **What it protects.** Prevents an automatic retry from spending beyond the approved action; preserves one-use authority semantics.
- **Main failure mode.** A stuck pending transaction can require manual recovery; the operational response is undefined, and a cancellation is itself a new spend transaction needing its own approval.
- **Alternatives.** Automatic replacement (explicitly unsafe here), manual external recovery (needs runbook), separate future replacement profile.
- **Required evidence.** Operational response runbook, same-nonce family test A20, proof that a rejected cancellation leaves the original family live, and explicit founder enablement of any future profile.
- **Safe to approve now?** **No** as a complete decision; the *default of no automatic replacement* is a safe constraint for mock work.
- **Mock-only proceed?** **Yes** — replacement disabled in mocks.
- **Live activation blocked?** **Yes.**

## Reviewer conclusion

The register is correctly written as PROPOSED with all decisions PENDING. That property must be preserved.
The next milestone may prepare schemas, version dispatch, golden vectors, mocks and negative fixtures, but
no founder decision, code review or evidence in this review creates a HUMAN_GRANT, a wallet connection or
transaction authority. See `MINIMUM_SAFE_PLAN.md` for the gated sequence.
