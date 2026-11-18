# Flip transaction state machine and recovery

**Status PROPOSED. Version 0.1. Date 2026-11-19.**
This is a durable design contract, with no transaction implementation. It depends on the [approval protocol](FLIP_APPROVAL_PROTOCOL.md) and proposed founder defaults.

## State model and persistent records

Maintain one immutable intent per requestId and a separate nonce-family record keyed by (chainId, sender, nonce). Each attempt has a monotonic sequence, state, reason, approval disposition, signing attempt, exposure flag, inclusion/finality observations, receipt-verification result and settlement status. The required state label is a workflow summary. Authorization, possible transaction execution and budget settlement are independent axes.

Persist exact intent/quote/policy/grant bytes and hashes, approver audit reference, nonce/budget reservations, consumed approval IDs, raw signed payload in protected storage, network and payload hashes, dispatch events, replacement-family links, RPC observations, block evidence, circuit-verification evidence and an append-only event sequence. Use transactional storage with enforced uniqueness and compare-and-swap state versions. A hash chain can expose accidental journal changes; it cannot prevent rollback if the attacker controls the database and its checkpoint. Store recovery epoch/checkpoint under the human-controlled broker identity and fail closed on mismatch.

Recommended initial policy permits one unresolved nonce family per enrolled sender, across all broker workers. A software mutex alone is insufficient. The database enforces this rule and unique active signing attempt. Cross-process workers acquire leases with fencing tokens. A late worker cannot commit a result or dispatch after a newer lease/revocation has superseded it.

## Meaning of required states

| State | Durable meaning | Reservation disposition |
|---|---|---|
| PREPARED | Complete immutable intent; required quote/context validation recorded | No committed live authorization reservation; provisional nonce claim may expire |
| AWAITING_APPROVAL | Human-readable exact intent is offered to protected human UI | Provisional claim only; no signer call |
| APPROVED | Fresh one-use grant and live policy checks atomically committed | Native/resource budget and nonce reserved |
| SIGNING | Grant atomically consumed; one signing attempt/fencing token recorded before signer I/O | Held; uncertain signer outcome means possible signed exposure |
| SIGNED | Independently decoded matching raw transaction and hashes durably stored | Held; raw signature is executable beyond application expiry |
| SUBMISSION_UNKNOWN | A dispatch attempt is persisted; network outcome is not yet reliably known | Held; never allocate a fresh nonce as an implicit retry |
| PENDING | Matching transaction observed in mempool or inclusion awaits finality/content checks | Held, with observed provisional costs tracked separately |
| CONFIRMED | Successful transaction, required finality and circuit receipt all verified | Settle actual costs/resources; retain reorg contingency until policy allows closure |
| REVERTED | Canonical failed transaction reached required finality | Settle actual gas/other fees; resource changes verified from reviewed semantics |
| REPLACED | Another known same-sender/nonce transaction is the canonical final winner | Transfer settlement to the family winner; preserve original attempt evidence |
| DROPPED | No active transaction is observed and the policy's bounded queries support a dropped observation | A missing mempool observation alone releases nothing |
| REORGED | Prior inclusion/finality observation no longer matches canonical chain | Invalidate current receipt, restore worst-case family reservation, quarantine overspend risk |
| EXPIRED | Broker authorization window elapsed | Release only if signed exposure is excluded; otherwise hold and reconcile |
| REVOKED | Human/policy stopped this attempt, or a definite pre-sign refusal was recorded | Same signed-exposure rule; revocation cannot unsign a transaction |

PREPARED means mechanically complete. If estimator/compatibility requirements are UNKNOWN, store a rejected proposal diagnostic outside the executable intent workflow and do not enter AWAITING_APPROVAL. A coding agent cannot force a proposal into APPROVED by choosing a state field.

## Complete permitted transition relation

All transitions require the broker/journal authority and an expected prior state version. Self-loops are event updates with no duplicate external side effect. Any edge absent from this table is forbidden.

| From | To | Guard and atomic effect |
|---|---|---|
| PREPARED | AWAITING_APPROVAL | Intent/quote/policy/profile valid; persist preview hash |
| PREPARED, AWAITING_APPROVAL | EXPIRED or REVOKED | Record expiry/refusal/policy reason; release unsigned provisional claim |
| AWAITING_APPROVAL | APPROVED | Protected human challenge, unexpired exact hash and policy; create grant and reserve nonce/budget in one transaction |
| APPROVED | SIGNING | Revalidate sender/chain/context; consume grant, issue one signing attempt/fence and commit before I/O |
| APPROVED | EXPIRED or REVOKED | No signing attempt exists; release reservations atomically |
| SIGNING | SIGNED | Valid matching signed bytes returned; persist protected payload and hashes atomically |
| SIGNING | REVOKED | Definite user rejection, definite pre-sign failure or human revocation; unknown/late signing outcome sets possible exposure and retains reservation |
| SIGNING | EXPIRED | Signing deadline/approval expiry; preserve possible exposure and fence late worker |
| SIGNED | SUBMISSION_UNKNOWN | Valid dispatch permit, exact hash, fresh final checks; commit dispatch event before send |
| SIGNED | EXPIRED or REVOKED | Suppress first broker dispatch; retain signed exposure and reconciliation watch |
| SUBMISSION_UNKNOWN | PENDING | Matching hash observed/acknowledged with valid transaction fields |
| SUBMISSION_UNKNOWN | DROPPED | Exhausted bounded observation window; retain reservations and distinguish observation from unexecutability |
| SUBMISSION_UNKNOWN, PENDING, DROPPED | EXPIRED or REVOKED | Stop broker retransmission; preserve watch and reservations for potentially executable bytes |
| PENDING | CONFIRMED | Required finality plus status success, authoritative circuit identity and exact content verification |
| PENDING | REVERTED | Required finality plus status failure and verified canonical transaction binding |
| PENDING | DROPPED | Observation window exceeded without canonical result; no resource release merely from absence |
| DROPPED | SUBMISSION_UNKNOWN | Only while original authority/policy/dispatch validity still permits identical-byte retry; new hash requires a new intent/grant |
| DROPPED | PENDING | Same hash or family candidate reappears; no new authority is created |
| SUBMISSION_UNKNOWN, PENDING, DROPPED, EXPIRED, REVOKED | REPLACED | A different same-sender/nonce canonical winner reaches required finality; verify sender/nonce and family settlement |
| EXPIRED, REVOKED | PENDING | Matching payload was externally submitted or late signer exposure is discovered; observation only, dispatch remains prohibited |
| CONFIRMED, REVERTED, REPLACED | REORGED | Canonicality/finality contradiction; revoke current receipt validity and restore family exposure |
| PENDING | REORGED | Provisional included block is displaced; preserve payload and restore pending context |
| REORGED | PENDING, SUBMISSION_UNKNOWN or DROPPED | Reconciler classifies same family using new observations; no automatic signing or fresh authority |

If a SUBMISSION_UNKNOWN query immediately finds a finalized receipt, first record PENDING with inclusion evidence, then evaluate its final outcome. This keeps receipt-verification guards on a single transition. A successful chain receipt with mismatched circuit identity/content stays PENDING with receiptVerification=FAILED and a quarantine reason; it cannot produce CONFIRMED. Known finalized financial effects may be settled separately while the application success claim remains blocked.

EXPIRED and REVOKED are authorization-terminal, but observations can reopen transaction tracking. They never restore the grant or permit a new send. CONFIRMED and REVERTED are subject to canonicality monitoring per the approved chain profile. A stronger finality signal reduces risk; the model still records any observed contradiction.

## Atomicity and external effects

No database transaction can atomically include the external signer or RPC. Use write-ahead intent, idempotency and reconciliation rather than an exactly-once-network claim.

1. Approval transaction validates human/policy, consumes the human challenge, inserts approvalId and reserves spend/nonce. All commit together or none commit.
2. Signing transaction consumes approvalId once, persists attempt ID and fencing token, sets SIGNING, then invokes the external signer. The signer must use that attempt ID idempotently or expose authoritative status. Otherwise an uncertain signer outcome cannot be automatically retried.
3. Signed-result transaction stores decoded fields, hashes and protected raw bytes, then marks SIGNED. A crash before commit requires recovering the signer's attempt status and returned payload. Unknown results quarantine the family.
4. Dispatch transaction persists exact transactionHash, endpoint profile, permit ID and attempt sequence, then marks SUBMISSION_UNKNOWN before network I/O. The network may accept the transaction even if the call times out. Reconciliation queries the precomputed hash and sender/nonce.
5. Observation transaction appends receipt/block evidence and changes state with the same family settlement update. Publishing a verified circuit receipt occurs only after these committed checks.

Revocation and dispatch contend on the same state/version lock. Revocation committed before dispatch claim prevents send. Once a dispatch claim commits, the call may race with a later revocation and may already be in flight. The UI must report this boundary accurately; it cannot promise cancellation of an external side effect.

## Crash recovery matrix

| Crash point | Restart behavior |
|---|---|
| Before approval commit | No grant; re-offer only a still-valid preview |
| After approval commit, before signing claim | Recheck expiry/policy; retain reservation and require valid grant |
| After signing claim, before/after signer response | Query same signing attempt; never initiate another signing attempt blindly |
| After raw payload persistence | Recover same signed bytes and hashes; check revocation/expiry/context before permitted first dispatch |
| Before dispatch-event commit | No dispatch by this service is allowed; confirm lease ownership before proceeding |
| After dispatch commit, before send or before response persistence | Assume possible submission; query hash and nonce, then only a permitted identical-byte retry |
| After inclusion, before receipt verification | Re-read canonical receipt/block and verify content before success |
| During replacement, settlement or reorg | Recover nonce family atomically; never release original exposure because a new attempt merely exists |
| Journal loss, rollback or stale backup | Freeze signing/dispatch; increment recovery epoch only through human-controlled recovery and reconcile every enrolled account before re-enabling |

Broker clock rollback or excessive clock uncertainty blocks new signing/dispatch and records a diagnostic. Recovery may continue reading chain data. It must not lengthen previously issued grants. Grants should survive ordinary trusted restart only if journal and protected epoch/checkpoint agree.

## Concurrent jobs and spend accounting

Use a rolling policy window with its definition and clock included in policyHash. Available native budget is the approved rolling cap minus finalized debits in the window minus worst-case unresolved family exposure. Do not double-count provisional inclusion as both settled and reserved. Pending reservations remain after window rollover until settlement. Resources use analogous per-contract/tokenId quantities. Reverted transactions can consume native fees, even when resource burn is reverted.

For mutually exclusive same-nonce attempts, reserve the maximum possible native debit across the family and the per-resource maximum of possible consumption, not the sum of mutually exclusive outcomes. A family may temporarily retain a higher prior reservation until a definitive winner is established. Any independent nonce requires its own full reservation. External wallet activity or unexplained nonce changes freeze new jobs and require reconciliation.

DROPPED is an observation state. Providers can omit pending transactions, and signed bytes can be resubmitted. A family reservation can be released only when unsigned exposure is proven absent, a required-finality nonce-consuming winner is verified, or the underlying signed payload is provably invalid under a reviewed chain rule. Application expiry, provider absence and human revocation alone are insufficient. After a reorg restores exposure, stop new jobs if restored reservations exceed limits. Never hide the deficit by raising the cap.

## Replacement, cancellation and receipt verification

Fee replacement requires a new immutable intent at the same nonce, a new grant and cap validation. Exact payload changes, including fee decreases, are reapproved. Once a replacement is merely broadcast, the original remains executable. Mark the losing attempt REPLACED only after a canonical winner meets the finality policy. Cancellation is also a new spend transaction with separate approval and gas budget; no automatic cancellation signer is enabled in the initial profile. A rejected cancellation leaves the original family live.

Receipt verification uses transaction hash and full transaction fields, receipt status, canonical block hash, log address and reviewed ABI, sender/nonce, event-derived circuit ID and fresh imported netlist/interface/dependency evidence at the inclusion context. Never derive the ID solely from nextId-1. Network acknowledgment, pending inclusion and success status do not alone satisfy CONFIRMED. Policy must define the required finality evidence and RPC disagreement handling before live use. All receipt failures remain inspectable without assigning authority to the imported report.

Detailed adversarial cases are in the [threat model](FLIP_TRANSACTION_THREAT_MODEL.md). No transition above is tested as implemented by this design milestone.
