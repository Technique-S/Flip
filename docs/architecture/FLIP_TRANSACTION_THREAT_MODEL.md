# Flip transaction threat model and acceptance specification

**Status PROPOSED. Version 0.1. Date 2026-11-19.**
The security requirements and test cases below are specifications for later implementation. None is presented as an executed transaction-system test.

## Assets and trust assumptions

Protect human signing authority, native currency and transistor resources, sender nonce, exact circuit bytes and intent, grants/policy, journal integrity, circuit receipt identity and confidential signing material. The existing verification core remains subject to M4's trusted engine and bounded native worker assumptions.

Untrusted inputs include projects, netlists, aliases/descriptions, agent instructions, proof files, browser storage, provider responses and stale receipts. A successful equivalence check proves a bounded behavior relation; it does not authenticate a human or authorize spending. The agent-facing verifier/CLI has no route to the authority plane.

Potential adversaries include a mistaken/malicious coding agent, injected project metadata, compromised browser page/dependency, malicious local client, dishonest RPC, faulty signer, competing transaction user and a crash/rollback/concurrency failure. Assume the protected broker identity, enrolled public keys and signer boundary remain trustworthy. If an agent has administrator access to that boundary, key storage and human UI, application checks cannot establish independent human consent. A verified external human-presence path is therefore an activation gate.

## Trust boundaries and required controls

| Boundary | Failure scenario | Proposed control |
|---|---|---|
| Agent/project -> builder | Prompt injection changes target or instructs an approve operation | Strict typed input, inert metadata, validated artifact digests, no authority verbs on agent API |
| Builder/estimator -> broker | Proposal lies about chain, fees or burn quantity | Broker independently revalidates quote, account, ABI and guard profile; rejects unknowns |
| Human surface -> broker | Automated browser event masquerades as a person | Protected separate identity/device, authenticated challenge bound to intent and trusted display |
| Broker -> signer | Replayed grant or wrong payload is signed | Fixed algorithm and enrolled broker key, live one-use state, attempt fencing, independent exact-field validation and device confirmation |
| Signer -> journal | Wallet edits fields or signs on the wrong chain | Independent raw parser, sender recovery, chain/payload comparison before persistence and dispatch |
| Journal -> submission | Arbitrary byte or endpoint substitution | Hash-bound dispatch permit, protected payload store, destination policy and atomic dispatch event |
| RPC -> reconciler | Ambiguous result, false receipt or missing mempool entry | Hash/nonce tracking, reviewed chain-trust profile, canonical block/finality verification and fail-closed disagreement |
| Contract -> receipt verifier | Upgraded code burns excess resources or emits substituted circuit identity | Immutability/atomic guard live gate, reviewed ABI, exact context and content verification; no retrospective safety claim |
| Journal -> restart worker | Stale backup resurrects approvals or releases funds | Protected epoch/checkpoint, uniqueness and atomic records, freeze and reconcile on rollback |
| Exports/logs -> agent/user | Keys, grants or signed bytes leak | Redacted metadata, passive evidence exports only, least-privilege file access and canary leak tests |

Two RPC URLs operated by the same organization are not evidence of independent operators. Provider agreement does not eliminate collusion or prove chain finality by itself. The chain-trust profile must name the provider trust assumptions and required evidence. The first recommended live policy requires independent observations and a verified finalized-block rule; unavailable evidence blocks completion.

## Critical residual risks

A signed standard EOA transaction can remain executable after application expiry or revocation. Treat a possibly exposed raw payload as a live capability until its nonce family is safely settled. This is handled by reservation/reconciliation, not by deleting a file.

An upgrade between pre-sign checks and execution can change effects while preserving target and calldata. The default profile requires demonstrated effective immutability or a reviewed onchain guard. The historical factory seal and old implementation hashes alone do not prove that condition. No onchain guard is created by this design.

Unknown additional chain fees may defeat an application-only total-debit ceiling. Verify the fee model and enforceability before enabling live signing. Unknown or unbounded exposure blocks approval under the proposed defaults.

Human approval can still be mistaken. The surface must make sender, chain, target, circuit fingerprint, native fee/cap and resource burn understandable, accessible and independently inspectable. A hardware confirmation showing opaque hex alone is insufficient for the chosen threat model.

## Automated adversarial acceptance matrix

Each test must assert resulting journal events, state version, signer/submission invocation counts, approval consumption, nonce ownership, reservation amounts and absence/presence of a verified circuit receipt. Use deterministic fake human authentication, signer and chain fixtures. They must not use real keys, connect a wallet or call mainnet.

| ID | Scenario and fault injection | Required observable result |
|---|---|---|
| A01 | Agent posts approve=true, forges approver identity or submits an unsigned grant | No APPROVED transition; zero signer/dispatch calls; structured denial |
| A02 | Reuse a valid grant in another request, broker epoch, account or UI session | Signature/context or journal check rejects it; no new consumption |
| A03 | Inject HTML/instructions in project labels, ABI descriptions and provider messages | Text remains inert; cannot change target/data/policy or invoke protected UI operations |
| A04 | Change one calldata/netlist/width byte or digest after preview | Intent/independent ABI validation fails before signing |
| A05 | Signer returns valid signature for wrong chain, sender, nonce or transaction type | Raw parser/recovery rejects; payload quarantined and no dispatch |
| A06 | Expire or revoke before APPROVED/SIGNING/dispatch; return late signer response | Transition respects linearization guard; no newly authorized send; possible exposure remains reserved |
| A07 | Replay one approval concurrently from multiple workers or after restart | One signing attempt and one approval consumption; database constraints/fencing reject other workers |
| A08 | Double-click dispatch, timeout after node acceptance, resend worker message | One logical transaction identity; reconciliation precedes any permitted identical-byte retry; no fresh nonce |
| A09 | Nonce conflict from another broker job or external wallet action | Freeze sender/family, reconcile winner and require new approval for changed nonce |
| A10 | Overflow, negative amount, float, duplicate resource entry, zero/unknown cap or mutated policy | Parser/policy rejects; no budget is manufactured |
| A11 | Two jobs individually fit but exceed aggregate native/token cap | Serializable reservation admits only permitted exposure; no second signer call |
| A12 | Pending job crosses rolling-window boundary or provider forgets transaction | Reservation remains held; budget window cannot release potential exposure |
| A13 | Signer definitively refuses or disconnects before signature; then returns ambiguous error | Definite refusal consumes/revokes attempt without retry; ambiguity retains possible signed exposure |
| A14 | RPC returns wrong transaction hash, malformed response, 429 or disconnect after send | SUBMISSION_UNKNOWN persists with precomputed hash; bounded polling and recoverable diagnostic |
| A15 | Factory/beacon/processor/resource implementation changes before signing or dispatch | Context/guard check blocks; fresh preview and human approval required |
| A16 | Upgrade occurs between last read and execution in a mutable test contract | Unsafe profile is rejected at admission; guard profile must revert atomically before excess effects |
| A17 | Chain reorg removes a previously verified inclusion or final receipt | REORGED, current receipt invalidated, family exposure restored, no automatic re-sign |
| A18 | Substitute another hash, sender, target, log address, event ID, netlist or dependency in receipt | Receipt validation fails; no CONFIRMED/circuit receipt; financial observation tracked separately |
| A19 | Receipt status is failure or success with wrong/missing circuit event | REVERTED only after finality for actual failure; mismatched success quarantined with no success claim |
| A20 | Replace/cancel at same nonce with changed fees/value; original wins race | Each payload has new approval; family maximum reservation held; only canonical final winner settles |
| A21 | Kill process before/after every database commit, signer call and RPC call | Recover per state-machine crash table without duplicate authority or dropped exposure |
| A22 | Roll back journal/clock or restore stale backup with a used grant | Protected checkpoint/epoch mismatch freezes writes; no approval resurrection |
| A23 | Unsupported finalized tag, disagreeing providers, incomplete fee model or unavailable gas estimate | UNKNOWN/blocked gates remain visible; no false confirmed state or approval bypass |
| A24 | Wallet silently changes gas/access list or uses a combined signing-and-send interface | Unsupported adapter rejected; no certification of the separate-signing profile |
| A25 | Agent attempts to read broker key, raw signed bytes or invoke wallet transport directly | OS/IPC policy denies; audit log records denial without leaking secret material |
| A26 | Export project/report and inspect logs during signing, revocation and recovery | No key, active grant, dispatch capability or unbroadcast signed payload present |
| A27 | Fuzz extra fields, duplicate JSON keys, canonical quantities and hashes | Fail closed; Python/frontend canonical vectors agree; no unsafe conversion |
| A28 | Reuse a DROPPED/EXPIRED signed transaction after approval expiry | Tracking resumes, authorization stays dead, reservation held until family unexecutable/final settlement |
| A29 | Receipt verifier sees nextId changed by unrelated concurrent publication | Uses authoritative reviewed event/result and exact content; never assigns global nextId-1 blindly |
| A30 | Journal disk full/fsync failure or protected payload-store error | Fail before external side effect when possible; uncertainty is quarantined; no grant reuse |
| A31 | Audit-only mode, default zero spend or public/untrusted client | All signer/submission routes absent or denied; existing local verification still works |
| A32 | Signer attempt returns the same signature after worker timeout or lease handoff | Same-attempt recovery is idempotent; stale fence cannot dispatch |
| A33 | Required verification is UNKNOWN, STALE, mismatched to candidate, or lacks intent anchor | Default publication policy rejects; no implicit exception from successful schema validation |

Implementation acceptance must inject crashes at each state-machine persistence boundary and exercise all forbidden transitions. Use model-based/property tests for one-use authority, at-most-one active nonce family, nonnegative available budget, no success without verified receipt and no send without a persisted dispatch event. A transaction may be retransmitted as the same bytes when allowed; tests must distinguish duplicate RPC calls from unauthorized duplicate publication.

## Manual approval acceptance

| ID | Exercise | Evidence required |
|---|---|---|
| M01 | Human accepts one exact preview using protected UI and external signer | Independent observer traces intentHash, human challenge, grant and signer fields; no agent can trigger the same sequence |
| M02 | Human refuses, revokes or waits for expiry; agent tries to continue | Visible denial and correct journal/reservation state; honest explanation after possible signed exposure |
| M03 | Keyboard and auditory screen-reader preview/refusal flow | Native/token caps, network, sender, target, expiry, risks and outcomes are announced; no color-only meaning |
| M04 | Selected device/app/firmware profile, account/chain switch and wallet field edit | Compatibility matrix with exact versions, raw-sign behavior, trusted semantic display and fail-closed mutations |
| M05 | Broker enrollment/recovery on a separate identity/device | Agent cannot access approval secrets/UI; backup/rollback and revocation drill recorded |

All M01-M05 are unexecuted in this design milestone. The M4 auditory screen-reader limitation remains open. A code test's fake human fixture cannot complete these manual gates.

## Live read-only and mainnet acceptance

L01 verifies selected RPC/client behavior, chain 196, pending nonce, target registration/code and resource ABI, real sender balances, total fee model and estimate semantics. L02 verifies current signer capability using safe non-spending tests only after separate consent to connect the wallet. L03 establishes finality semantics and authoritative receipt/event interpretation for the current chain/contracts. Record exact versions, endpoint/operator trust, block/time and uncertainty. Documentation discovery alone cannot complete these checks.

L04 is one separately approved mainnet publication after design, policy, compatibility and security review. Human authorization must name account, target, exact circuit/calldata digest, native/resource ceilings, expiry and finality policy. A funding/acquisition/allowance/cancellation action needs its own approval. Capture transaction, canonical receipt, actual costs and re-imported circuit content. Unknown submission, rejection, revert and mismatched receipts are legitimate outcomes; none may be relabeled success.

No L gate was executed here. Public hosting, arbitrary call support and autonomous signing remain outside this profile. Future release acceptance must record each A/M/L case with PASS, FAIL or BLOCKED, exact tested revision and evidence location.

## Approval gates

The release profile stays disabled until founder decisions D01-D12 are explicitly recorded, all applicable A cases pass on supported platforms, M cases pass on the selected protected setup, L01-L03 establish protocol compatibility, and an independent reviewer approves the authority/journal code. L04 still requires its own human grant. See [handoff](../milestones/M45_0_HANDOFF.md).
