# Flip exact transaction approval protocol

**Status PROPOSED. Contract family version 0.1. Date 2026-11-19.**
No schema, signer, grant or transaction system is implemented here. Founder decisions are listed in [the register](../milestones/M45_0_DECISION_REGISTER.md).

## Types, canonicalization and digest rules

All contracts below reject unknown fields, duplicate JSON keys, unsafe numeric encodings and unsupported versions. Object keys are ASCII. Binary data is even-length lower-case 0x hex. Addresses are normalized 20-byte hex, digests 32 bytes. All quantities, timestamps and nonces are unsigned canonical decimal strings, with no leading zeros except zero and a maximum uint256 bound for monetary/chain quantities. Timestamp seconds are uint64 decimal strings. ChainId alone is the literal JSON integer 196 for consistency with the frozen identity convention. Negative values and floats are forbidden.

Use existing flip-json-v1 canonical UTF-8 rules for documents. For an intent body I, intentHash = SHA-256(UTF8("flip-tapeout-intent-0.1\n") concatenated with canonicalBytes(I)). The actual separator is one newline byte. The hash envelope contains only body and intentHash; body has no self-hash. Equivalent domain-separated rules apply to quote, policy, grant, dispatch and receipt bodies using their kind/version. Hex-byte digests are SHA-256 of decoded bytes. The network transaction hash is Ethereum's Keccak-256 of its signed encoded transaction, carried in the distinct field transactionHash. SHA-256 is never substituted for that network hash.

Schema exports, golden canonical vectors and generated frontend types are required before implementation. Tables define exact required fields for the proposed contracts. Labels/descriptions live outside these authenticated bodies and cannot affect the payload or authority. Optional variant fields are represented only by the defined tagged union. Unknown account/transaction variants fail closed.

## Immutable intent — flip-tapeout-intent-0.1

| Required body field | Type and meaning |
|---|---|
| schemaVersion, kind | Literals flip-tapeout-intent-0.1 and TAPEOUT_INTENT |
| requestId | Broker-issued cryptographically random 32-byte ID, unique in its journal |
| brokerId, brokerEpoch, deploymentProfileHash | Enrolled broker identity, recovery epoch decimal string, and approved local deployment profile |
| createdAt, expiresAt | Broker-clock timestamp seconds; expiresAt greater than createdAt; proposed 300-second maximum lifetime |
| action | Tagged union TAPEOUT, REPLACE_TAPEOUT or CANCEL; initial release enables only TAPEOUT |
| projectBinding | Object with projectHash, revisionHash, candidateNetlistHash, verificationEvidenceHash and requiredVerificationPolicyHash |
| circuit | Object with netlist hex bytes, nIn and nOut decimal strings, semanticsHash, sourceManifestHashes sorted unique digest array |
| executionContext | Object with factory, processor, beacon, resourceContract addresses; factoryImplementationHash, processorCodeHash, beaconImplementationHash, resourceCodeHash and dependencyContextHash digests; abiHash and executionGuardProfileHash digests |
| observation | Object with blockNumber decimal, blockHash digest, observedAt timestamp, chainTrustProfileHash and maximumObservationAgeSeconds decimal |
| quoteHash, policyHash | Exact validated quote and policy snapshot digests |
| transaction | Exact tagged transaction object below |
| limits | Object with maxNativeDebitWei decimal, maxGasLimit decimal, maxFeePerGasWei decimal, otherFeeCapWei decimal, tokenResources array and aggregateReservationPolicyHash digest |
| replacesRequestId | Null for TAPEOUT, predecessor request ID for a separately authorized replacement/cancellation |

The transaction object contains chainId=196, accountModel=EOA, sender address, target address, nonce decimal, calldata hex bytes, calldataHash digest, valueWei decimal and a fee union. LEGACY has type=LEGACY, gasLimit and gasPriceWei decimals. EIP1559 has type=EIP1559, gasLimit, maxFeePerGasWei, maxPriorityFeePerGasWei decimals and accessList fixed to an empty array for the first profile. No creation target, authorization list, blob fields or opaque wallet extension fields are accepted. The actual supported fee variant requires a capability-certified network/signer profile. Both variants are described to avoid assuming current device support.

TokenResources contains exactly the resources the reviewed tape-out ABI may consume. Each entry has contract address, tokenId decimal, maxQuantity decimal and resourceRuleHash digest, with unique contract/tokenId pairs sorted lexicographically. Initial policy allows the verified transistor burn only. A wrapper execution guard is not an implicit exception to target=processor or the tapeout ABI; it requires a separately versioned/profiled target and reviewed payload semantics. The execution guard/immutability profile must demonstrate enforcement of the approved maximum under actual execution.

Cross-field validation requires nonzero gas limit, gas limit at or below maxGasLimit, every signed fee field within its cap, and maxPriorityFeePerGasWei at or below maxFeePerGasWei. For TAPEOUT, valueWei equals the freshly verified quote feeWei. Quote sender/target/circuit/calldata/context must match the intent exactly, and each required resource quantity must fit its corresponding approved cap. The intent expiry must be no later than the policy and quote expiries. The quote must remain valid throughout approval/signing/first-dispatch checks.

Recompute calldata from netlist and widths using the reviewed tapeout ABI. Verify exact byte equality and hashes. TAPEOUT's target must equal executionContext.processor; the processor must be in the human-approved target policy and registered under the bound factory. Values and fee fields are exact, even when less than the caps. A wallet reducing or increasing a field still creates a different transaction and requires a new intent and human approval. Replacements/cancellations use distinct request IDs and approvals tied to the same nonce family.

## Read-only quote — flip-tapeout-quote-0.1

Required fields are schemaVersion, kind=RESOURCE_QUOTE, requestId, chainId=196, sender, target, candidateNetlistHash, calldataHash, observation, environmentHash, abiHash, feeWei, requiredResources, accountBalances, gasEstimate, feeModel, expiresAt and status.

Observation contains blockNumber, blockHash, observedAt and chainTrustProfileHash. RequiredResources is the exact contract/tokenId/quantity array from verified protocol rules. AccountBalances carries nativeWei and resource contract/tokenId/availableQuantity entries at the observation context. GasEstimate is a tagged result KNOWN with gasUnits and methodEvidenceHash, or UNKNOWN with reasonCode. FeeModel carries feeVariant, chosen exact gas price fields, otherFeeBoundWei and feeModelEvidenceHash. Any unbounded field makes status=UNKNOWN. status=SUFFICIENT requires fresh funds/resources and an enforceable full-debit bound. Record synthetic override pre-flight evidence separately; it cannot establish actual sender sufficiency.

The quote digest binds its complete body. It grants no authority. Recheck chain, account, code context, fee and resource sufficiency before signing and before first dispatch, without mutating the intent. A new observation can confirm the same approved values/context within policy. Any semantic change requires a new intent. No proof flag or user assertion bypasses the quote gate.

## Policy, grant and dispatch contracts

Policy body flip-tapeout-policy-0.1 requires policyId, policyVersion, deploymentProfileHash, enabled flag, chainId=196, enrolledSender, allowedTargets, allowedActions, perIntentNativeCapWei, rollingWindowSeconds, rollingNativeCapWei, perResourceCaps, maxPendingJobsPerSender, requiredVerificationPolicyHash, maximumIntentLifetimeSeconds, maximumObservationAgeSeconds, finalityPolicyHash, executionGuardProfileHash and policyOwner. Include schemaVersion and kind=TRANSACTION_POLICY. Initial live defaults are disabled, zero native/resource caps and maximum one active nonce family per sender. Founder-approved positive caps are required to make any live action admissible. A policy change invalidates unconsumed grants; it cannot undo a signed payload.

Grant body flip-tapeout-grant-0.1 requires schemaVersion, kind=HUMAN_GRANT, approvalId random 32 bytes, requestId, intentHash, policyHash, brokerId, brokerEpoch, approverId, humanChallengeHash, issuedAt, expiresAt and grantState=ISSUED. The challenge binds the exact intent and approval UI session. The signature envelope contains body, algorithm=Ed25519, keyId and signature hex. The broker authenticates protected human presence before producing this application signature with its own protected approval key. This key is separate from the wallet key. The signer adapter verifies against an enrolled broker public key and fixed algorithm, then checks live broker state. A copied signature does not bypass journal revocation or one-use consumption. No key is created by this design milestone.

Sign each grant/dispatch body as Ed25519 over UTF-8(kind + "/" + schemaVersion + one newline byte) concatenated with canonicalBytes(body). The algorithm is fixed by this protocol, with no algorithm negotiation or unsigned variant. keyId selects an enrolled key for the brokerId/epoch and is rejected if unknown or revoked. It cannot supply an arbitrary verification key. Signature malleability and invalid-key cases require library-level golden tests.

The agent can request preparation and read redacted outcome states. The authenticated approve/revoke operations are absent from agent APIs, tools, filesystem rights and desktop surface. Initial enrollment and policy changes require the human-controlled identity/device. An agent-supplied boolean, model response or forged browser event is rejected. OS-profile separation with unrestricted agent administrative control is insufficient. Broker availability alone never substitutes for human approval.

The proposed application signing algorithm follows the standardized Ed25519 construction through a reviewed library. It does not introduce a chain signature scheme. Implementation must supply cross-language vectors, key enrollment/revocation and anti-rollback checks. [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032)

Dispatch permit flip-tapeout-dispatch-0.1 requires schemaVersion, kind=DISPATCH_PERMIT, permitId, requestId, intentHash, approvalId, transactionHash, signedPayloadHash (SHA-256), brokerId, brokerEpoch, journalSequence, action=FIRST_SEND or IDENTICAL_RETRY, expiresAt and destinationProfileHash. The same fixed broker signature envelope applies. Submission validates the permit online against journal state, atomically claims its dispatch sequence and reads the matching raw payload from protected storage. A worker retry creates a separately journaled dispatch event for the identical hash. It cannot substitute fields, choose a new nonce or increase spend.

## Approval algorithm and invariants

1. Agent proposes a circuit artifact. Builder validates versions, bytes and trusted reference/test evidence. Broker assigns requestId and the pending nonce candidate under its account lock. It never trusts a caller-picked nonce or grant ID.
2. Estimator produces a fresh quote and exact transaction proposal. Broker checks policy, actual account identity and full execution guard/fee model. Missing compatibility or UNKNOWN estimates block approval.
3. Broker writes immutable intent and AWAITING_APPROVAL. Human UI independently decodes calldata, displays chain/sender/target, project and netlist fingerprints, exact native value, gas and total ceilings, resource burn, confirmation policy and expiry. It renders hostile labels as inert text. Raw bytes are inspectable. The human can refuse with equal accessibility.
4. A protected human challenge confirms the exact intentHash. In one serializable transaction, broker rechecks expiry/policy, validates nonce and aggregate available budget, creates one-use approvalId, reserves balances and nonce and moves to APPROVED. Another active family for that sender is blocked under the initial profile.
5. Before SIGNING, independently re-read signer/network context and required chain state. Atomically consume the grant and create a single signing attempt plus fencing token. The signer verifies grant authenticity/live state, exact payload and recovered account profile, then requires human device confirmation. It must not auto-broadcast.
6. Verify the returned raw transaction using an independent parser and sender recovery. Compare every signed field against the intent, not only a reported hash. Reject unprotected legacy signing, incorrect chain, wallet edits and unsupported types. Atomically persist signed bytes and both hashes, state SIGNED and the signing result before any dispatch is possible.
7. Revalidate policy and authorization dispatch deadline, fresh context and resource/nonce checks. Issue a hash-bound dispatch permit and record SUBMISSION_UNKNOWN before the external network call. Resolve the result according to the state machine. A late signer response after revocation is quarantined, not dispatched.
8. Verify inclusion, finality and circuit content before issuing the receipt. New authority for a replacement/cancellation requires another immutable intent, fresh human grant and recalculated family reservation.

Recommended total native reservation for a certified fee model is valueWei + gasLimit multiplied by the signed maximum fee per gas + otherFeeCapWei. Bound intermediate multiplication/addition to uint256. If additional network fees are not actually bounded under the signed transaction model, reject live activation; a numerical allowance in a JSON file alone cannot enforce them. Resource caps are enforced against the verified execution profile. Reserve worst-case pending exposure and consumed rolling-window spend, not only current displayed balance. See the state machine for family accounting and reorgs.

Legacy chain-bound signing and typed fee transactions have distinct encodings. EIP-155 and EIP-1559 ground those formats; compatibility with the selected X Layer signer remains a required test. [EIP-155](https://eips.ethereum.org/EIPS/eip-155), [EIP-1559](https://eips.ethereum.org/EIPS/eip-1559)

## Expiration, invalidation and revocation

Before signing, expiry, revocation, policy/identity/chain change, fee or nonce mismatch, stale dependencies, implementation/ABI/guard mismatch, clock rollback, broker epoch change or unknown estimates blocks progress. Record reason and require a new immutable intent/grant rather than silently revising one.

expiresAt controls broker signing/dispatch authorization. A standard signed EOA transaction remains cryptographically valid after that timestamp. Revocation after SIGNED suppresses future broker dispatch, retains quarantined signed bytes and keeps reservations until reconciliation proves the nonce family cannot execute. It cannot retract a payload already submitted or leaked. No UI may promise otherwise. Uncertainty during signing is treated as potential signed-payload existence.

A chain nonce, requestId and approvalId address different replay domains. Signed typed application data would also require expiry and one-use journal checks; EIP-712 itself does not supply replay protection. The first profile does not require an extra wallet-signed EIP-712 grant. [EIP-712](https://eips.ethereum.org/EIPS/eip-712)

## Proposed circuit receipt — flip-circuit-receipt-0.1

Required body fields are schemaVersion, kind=CIRCUIT_RECEIPT, requestId, intentHash, approvalIdReference, chainId=196, sender, processor, transactionHash, transactionNonce, inclusionBlockNumber, inclusionBlockHash, receiptEvidenceHash, publicationEventEvidenceHash, circuitIdentity, candidateNetlistHash, importedNetlistHash, importedManifestHash, dependencyContextHash, feeAndResourceSettlementHash, finalityPolicyHash, finalityEvidenceHash, verifiedAt, verifierIdentityHash and dispatchAuthorizationStatus. The latter is BROKER_AUTHORIZED or EXTERNAL_OR_UNKNOWN, established from the durable dispatch record rather than inferred from chain success.

circuitIdentity uses the existing normalized identity representation as a nested value. Confirmed receipt semantics require success status, matching sender/target/nonce/payload, canonical inclusion at the approved finality level, authoritative circuit ID extraction through the reviewed ABI, exact netlist/width match and valid dependency context. A status-1 receipt alone is insufficient. Failed checks produce a diagnostic journal event and no CIRCUIT_RECEIPT. A confirmed external/late submission is reported with its actual authorization status and cannot be described as a compliant broker dispatch. A later reorg invalidates the current receipt and retains its historical bytes.

## Migration, secrets and exports

These proposed contracts use separate names and version dispatch. They do not add accepted fields to frozen v1 schemas. Future portable projects may carry passive intent/receipt references and immutable public transaction evidence under their own approved version. Active grants, dispatch permits, raw unbroadcast signed bytes, wallet keys, broker keys and signer credentials are excluded. Records needed for reconciliation remain protected local journal data. A project import always requires a fresh approval sequence.
