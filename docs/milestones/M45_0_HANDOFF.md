# M4.5-0 authority architecture handoff

**Status PROPOSED. Version 0.1. Date 2026-11-19.**
Design package ready for founder and independent security review. It carries no signing, wallet connection, deployment or spend authorization.

## Baseline and inputs

The branch is created from accepted M4 main **09f2482beae84be6d919ecd6957c4153d1924cca**. Remote main matched that baseline at preparation. The committed gap audit and M4.5 plan were read from **962f5beeea9a485e8d4088ab1e67e0f8d69e6a27** on the separate audit branch. They remain identifiable evidence rather than silently copied/reclassified requirements.

Preparation included AGENTS.md, FLIP_SYSTEM_ARCHITECTURE.md, FLIP_TECHNICAL_DESIGN.md, MVP_CONSTRAINTS.md, M4_ACCEPTANCE.md and existing architectural decisions. The source audit reports five PARTIAL capabilities and a BLOCKED authorized lifecycle. Its live-chain and auditory screen-reader limitations remain applicable. M4's verification/evidence/worker acceptance does not validate transaction authority.

## Package map

| Deliverable | Purpose |
|---|---|
| [Successor ADR](../architecture/FLIP_ADR_AUTHORIZED_TAPEOUT.md) | Scope amendment, nine component boundaries, recommended signer/account model, alternatives and activation gates |
| [Transaction threat model](../architecture/FLIP_TRANSACTION_THREAT_MODEL.md) | Assets, adversaries, residual risks and 33 automated, five manual and four live/compatibility acceptance specifications |
| [Exact approval protocol](../architecture/FLIP_APPROVAL_PROTOCOL.md) | Proposed immutable intent/quote/policy/grant/dispatch/receipt contracts, digest rules and exact authority checks |
| [State machine](../architecture/FLIP_TRANSACTION_STATE_MACHINE.md) | All required states, permitted transitions, atomic commits, concurrent budgets, signing/submission uncertainty and recovery |
| [Decision register](M45_0_DECISION_REGISTER.md) | Twelve founder decisions with defaults, trade-offs, evidence and PENDING status |
| This handoff | Evidence, limits, review checks and next-milestone admission |

## Recommendation and unresolved gates

Recommend a dedicated human-controlled hardware-backed EOA, external raw signer, protected broker identity/device and separate dispatch. A coding agent may prepare and verify a proposal. It cannot authenticate as the human, issue grants, access keys or directly submit arbitrary bytes. Same-desktop controls with unrestricted agent access cannot meet that assurance.

A specific wallet/device/firmware/provider profile remains unverified. Official OKX documentation describes combined transaction sending with wallet-editable fee fields; that path needs a different reviewed adapter model if it cannot return raw signed bytes before submission. The first profile remains blocked rather than silently degrading the approval checks.

Signed EOA bytes remain a capability after application expiry or revocation. Reservations survive uncertain signing and submission. A durable nonce-family journal and protected anti-rollback checkpoint are mandatory. Unknown network outcomes are reconciled before any retry. Replacements and cancellations are separate approved payloads.

Execution-time upgrades and extra chain fees are explicit live gates. Fresh pre-sign reads cannot alone enforce an implementation/resource cap at inclusion. The chosen deployment must prove effective immutability or a reviewed atomic guard, and a complete bounded fee model. No guard contract, wallet integration or transaction code is provided in this package.

## Proposed contract migration

All new contracts are separate proposed version 0.1 families defined in Markdown. There are no edits to frozen v1/M2/M3 schemas, accepted models, canonical rules or production routes. Implementation must introduce version dispatch, formal schemas/generated types, golden hash/signature vectors and independent review. Legacy projects/evidence never acquire authority through import or conversion. Active grants and raw unbroadcast signed payloads are excluded from portable exports.

## Documentation verification

Review checks for this design package must verify all six documents carry PROPOSED status, internal links resolve, every required state has semantics and transition guards, all founder decisions remain pending and every requested adversarial category has a corresponding test specification. The deliverable contains six new documents and one ancillary repository-guard correction. The existing guard rejected all additions under docs/architecture. It now enumerates and protects every original seed file, permitting additive successor documents while continuing to reject modifications/deletions of historical planning files. Historical evidence, frozen contracts and production package/application source remain byte-identical to accepted main.

Documentation checks passed for six PROPOSED files, local links, 14 required states, 12 PENDING decisions, 33 automated test specifications and five manual test specifications. Git diff whitespace and original protected-file preservation are checked.

No runtime feature tests are claimed for proposed components. The existing baseline is already accepted M4 with 514 Python and 11 Chromium tests in its recorded platform matrix. This design does not rerun that matrix merely to imply transaction functionality exists. Proposed A/M/L acceptance cases are unexecuted and require actual implementation and separately authorized compatibility/manual/live sessions.

## Current external documentation checks

Official protocol/provider documentation was checked on 2026-11-19. These reads confirm standards/interface descriptions, not actual wallet/device behavior or deployed tape-out contract safety.

- X Layer network identity and native token. [Official network information](https://web3.okx.com/onchainos/dev-docs/xlayer/developer/build-on-xlayer/network-information)
- OKX's documented send path and editable fee parameters. [Official EVM send interface](https://web3.okx.com/onchainos/dev-docs/wallet/dapp-connect/chains/evm/web-send-transaction)
- Provider chain/account event contract. [EIP-1193](https://eips.ethereum.org/EIPS/eip-1193)
- Raw signing method description, with provider support still a compatibility gate. [Ethereum execution API](https://ethereum.github.io/execution-apis/api/methods/eth_signTransaction/)
- Chain-bound legacy and typed fee transaction formats. [EIP-155](https://eips.ethereum.org/EIPS/eip-155), [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559)
- Typed application signatures require their own replay controls. [EIP-712](https://eips.ethereum.org/EIPS/eip-712)
- Proposed broker grant signature primitive. [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032)

Only primary sources support these statements. No live JSON-RPC query, wallet connection, account enrollment, credential creation or publication was performed. No vendor compatibility is certified.

## Admission to the next milestone

Founder decisions and independent review must resolve the authority architecture before enabling it. The next scoped implementation can build versioned proposals/quotes and mocked policy/journal behavior under the approved design. Signing and submission require their later explicit assignments and gates. Any live mainnet acceptance must approve one exact reviewed intent through the human-controlled protocol.

M4.5-0 stops with this proposed package and pending register. It does not begin M5 or change public-hosting restrictions.
