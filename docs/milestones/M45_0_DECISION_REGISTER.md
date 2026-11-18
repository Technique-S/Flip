# M4.5-0 founder decision register

**Status PROPOSED. Version 0.1. Date 2026-11-19. All decisions PENDING.**
Recommended defaults below are proposals for review. The publication objective and permission to produce this design do not approve custody, deployment or spending.

Baseline is merged M4 `09f2482beae84be6d919ecd6957c4153d1924cca`. Starting audit/planning evidence is commit `962f5beeea9a485e8d4088ab1e67e0f8d69e6a27`. No architectural or financial approval has been inferred from either commit.

## Required decisions

| ID | Decision and recommended default | Trade-off and alternative | Required founder action/evidence | Status |
|---|---|---|---|---|
| D01 | Dedicated locally controlled hardware-backed EOA and reviewed external raw signer; wallet keys remain with the human | More setup and device compatibility work. A browser/software/hosted wallet is easier but broadens custody and auto-submit risks | Approve custody model and exact device/app/firmware/adapter profile after compatibility testing | PENDING |
| D02 | Protected approval interface under separate human OS identity/device, with authenticated human presence and independent semantic display | Adds operational friction. Same unrestricted desktop/local HTTP control cannot reliably distinguish agent from human | Approve trust boundary and demonstrate agent exclusion plus keyboard/auditory accessibility | PENDING |
| D03 | Live disabled and all spend/resource caps zero until explicitly configured. Every action binds exact quoted value and gas fields; per-action and rolling 24-hour native/resource ceilings must be supplied as decimal quantities | Conservative policy may block work. Blanket approval or automatic cap increase expands loss exposure | Enter positive per-action and aggregate caps, permitted token contracts/IDs and approver identity; no monetary amount is selected by this design | PENDING |
| D04 | One enrolled ordinary EOA, no code/delegation, one active nonce family per sender; only chain 196 and an existing registered reviewed processor | Serial operation limits throughput. Smart accounts/multisig/delegated accounts need separate signature/nonce/gas profiles | Approve supported account profile and enrolled sender/target policy | PENDING |
| D05 | CONFIRMED requires matching canonical receipt/content and a verified finalized-block policy with independent operator observations | Slower than a fixed count or sequencer acknowledgment. Finalized support/meaning on current X Layer is unverified here | Approve chain-specific finality evidence and operator independence. If unsupported, hold PENDING until a separately reviewed policy is approved; no invented block count | PENDING |
| D06 | UNKNOWN gas, other-fee bounds, sender-resource sufficiency or execution context blocks signing | May delay publication where full simulation is unsupported. Manual estimate override would weaken default protections | Approve rejection policy; any alternative requires a bounded enforceable fee model and documented independent evidence | PENDING |
| D07 | One stateless tape-out to an existing processor per human grant; no acquisition, transfers, allowances, new processors, batches or autonomous publication | Narrow first release. Broader operations require their own exact payloads and authority profiles | Approve first publication scope and verification policy. Recommended requirement is an explicit trusted intent anchor, EQUIVALENT comparison and passing declared tests; UNKNOWN/STALE/mismatched evidence is rejected | PENDING |
| D08 | Development approval permits mocks/local simulation only. Code review, release enablement and each live transaction are separate authorizations | More gates, with clearer authority. A generic release/task instruction cannot authorize an account spend | Name owner/reviewer for each gate and approve live acceptance only with an immutable preview | PENDING |
| D09 | Intent maximum lifetime 300 seconds, fresh observation maximum age 30 seconds, fail closed on clock rollback; grant expiry no later than intent expiry | Short windows may require repeated previews. Longer windows increase stale context risk | Approve time limits and recovery clock policy. Expiry after signing never promises cryptographic revocation | PENDING |
| D10 | Live requires verified effective immutability or a separately reviewed atomic execution guard for context/resource caps | Can block a mutable deployment. Rechecks alone leave an execution race; a guard may require new contract architecture and review | Select and prove guard/immutability profile. Any changed risk acceptance requires a successor ADR and honest cap claims | PENDING |
| D11 | Protected broker application key, fixed Ed25519 grant/dispatch authentication, pinned public-key enrollment and anti-rollback checkpoint; independent raw transaction parsing and sender recovery | Adds key lifecycle and parser review. Agent-readable keys or bearer flags cannot enforce grants | Approve broker enrollment/rotation/recovery procedure and independent security reviewer | PENDING |
| D12 | No automatic fee replacement/cancellation in initial profile. Future variants require a new intent/grant, same-nonce family accounting and exact caps | Stuck pending transactions may require manual recovery. Automatic replacement can spend beyond the approved action | Approve operational response and replacement/cancellation enablement as a separate future profile | PENDING |

The 30-second observation age is a proposed local freshness threshold, not a claim about chain finality or RPC correctness. The 300-second lifetime governs application authority only. The 24-hour window is rolling, with pending exposure retained across window boundaries. Final account, target, gas model and resource rules remain unset.

## Decision capture format

For each ID, record decisionId, status APPROVED/REJECTED/DEFERRED, exact selected value/profile hash, rationale, constraints, founder identity, decision time, reviewed document revision/commit and evidence reference. This is a proposed record format in documentation, not a new runtime schema. An omitted value or unrecorded decision stays PENDING. Approval of one ID does not resolve other rows.

A founder design approval permits the next stated engineering milestone only. It does not produce a HUMAN_GRANT, authorize wallet connection or approve a transaction. A live grant must bind the actual sender, target, calldata, fees/resources, nonce, expiry, policy and one-use identifier specified in the approval protocol.

## Current compatibility evidence and open checks

Current official documentation lists X Layer mainnet chain ID 196 and OKB. It documents an OKX send interface and Ethereum provider events, but does not demonstrate the selected protected raw-signing deployment. No wallet or device has been connected, no key created and no transaction issued in M4.5-0. See the ADR's dated sources and alternative assessment.

Before D01/D04/D05/D10 can activate a live profile, verify exact raw transaction behavior, account/code state, fee variants and all fee components, pending nonce behavior, finality semantics, authoritative publication event ABI and execution-time cap enforcement. These are external compatibility gates, not assumed M4 functionality.

## Review sequence

1. Founder chooses the scope/trust/custody defaults or records alternatives with explicit risk changes.
2. Security reviewer checks broker isolation, immutable contracts and the state machine against the threat model.
3. Implementation receives a scoped assignment with mocks and versioned schemas, preserving M4 regression tests.
4. Compatibility/manual acceptance is performed under separate consent and recorded with exact versions.
5. Release enablement and one live acceptance receive distinct explicit authorization.

This register is ready for review with all decisions pending. No approval question needs to be answered to complete this design-only milestone.
