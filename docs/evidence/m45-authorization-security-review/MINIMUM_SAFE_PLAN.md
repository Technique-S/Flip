# Minimum safe implementation plan (proposal only)

**Status: REVIEWER RECOMMENDATION, NOT APPROVAL. Date 2026-11-22.**
This plan contains no authorization to implement signing, wallet integration, broadcast or spending.
Codex owns interfaces and integration; OpenCode/HY4 Flash may own disjoint evidence and fixture work.
Nothing here changes runtime code, production schemas, acceptance checks or original evidence.
All twelve founder decisions remain PENDING until the founder records them.

## Guiding rule

No phase may start because a previous phase was *documented*. Each phase starts only after its named
owner records the required evidence against an immutable revision, and each live phase requires its own
explicit authorization. "Mocks" means synthetic data with no real keys, no wallet connection, no RPC
write methods and no mainnet submission.

## Phase 0 — founder decisions and document baseline (gate G0)

**Owner:** Founder, with Codex preparing the record.
**Actions**
1. Record D01–D12 in the register's decision-capture format, each with exact selected value/profile hash, rationale, constraints, founder identity, time, reviewed commit and evidence reference.
2. Rebase the authority documents onto accepted main `b537eb6` as **additive** version-dispatched artifacts; explicitly state that the accepted controller's `STOP_AUTHORIZATION` is terminal and produces inert proposal evidence only.
3. Put the portable-project inert-reference rule in writing: imported intent/receipt references authenticate no author, confer no authority and always require a fresh intent and grant.
4. Have Codex re-review the repository-guard change against the accepted guard (A-13).

**Exit evidence:** immutable decision records; baseline/adapter ADR; guard review sign-off.
**Exit test:** no authority document claims an approval; register still marks unrecorded items PENDING.
**Blocked if:** any decision is assumed approved by this review or by a prior generic task instruction.

## Phase 1 — versioned contracts, canonical vectors and fail-closed parsing (gate G1)

**Owner:** Codex for schemas and canonical rules; OpenCode may generate independent golden fixtures under its own paths.
**Actions**
1. Define version-0.1 JSON Schemas and generated types for intent, quote, policy, grant, dispatch permit and receipt, with the proposal's domain-separated SHA-256 digests and distinct Keccak transaction hash.
2. Produce cross-language golden vectors for canonical bytes, duplicate keys, unsafe numbers, unknown fields, tagged unions and Ed25519 signatures.
3. Implement a mock artifact builder that consumes accepted controller output as inert data and never emits an approval verb.

**Exit evidence:** schema drift checks, golden vectors, negative fixture corpus, `UNKNOWN`/`INVALID_INPUT` mapping.
**Exit test:** A27, A10, A03, A33 pass against mocks; no production schema or frozen contract bytes changed.
**Blocked if:** runtime authority is inferred from a schema-valid document.

## Phase 2 — mock broker, journal, signer and chain doubles (gate G2)

**Owner:** Codex for broker/journal; OpenCode may provide independent adversarial harness under `fixtures/m45-authorization-security-review/`.
**Actions**
1. Implement durable journal doubles with uniqueness, compare-and-swap versions, fencing tokens and the full 14-state machine using synthetic identities.
2. Implement fake human challenge, fake Ed25519 broker key and fake signer returning synthetic raw bytes; no real key material.
3. Inject all A01–A33 cases, crashes at every persistence boundary, one-use authority, at-most-one nonce family, nonnegative budget and no-success-without-receipt properties.
4. Add explicit states/negative tests for the gaps in SECURITY_REVIEW §2 A-09/A-10/A-12.

**Exit evidence:** journal event traces, state-version assertions, signer/submission invocation counts, reservation ledger snapshots.
**Exit test:** all 33 automated cases pass on mocks; all forbidden transitions rejected; 16 adversarial scenarios mapped and exercised.
**Blocked if:** any fake primitive touches a real wallet, key, endpoint or signed payload.

## Phase 3 — platform and adapter certification, still no live keys (gate G3)

**Owner:** Codex with a human operator; independent reviewer for security evidence.
**Actions**
1. Produce the D01/D02/D11 platform evidence pack: hardware/app/firmware matrix, separate identity/device topology, ACL denial test, human-presence path, keyboard and screen-reader drills.
2. Certify a raw-sign adapter using synthetic payloads and a device that never holds live funds; verify exact-field decode, sender recovery and rejection of combined sign-and-send, chain/account changes and silent fee edits.
3. Document broker key enrollment, rotation, revocation and anti-rollback checkpoint custody.

**Exit evidence:** compatibility matrix with exact versions, M01–M05 manual records, negative adapter results, reviewer sign-off.
**Exit test:** agent cannot invoke approve/revoke, read broker key or raw signed bytes, or reach signer transport; all fail closed.
**Blocked if:** the only available wallet cannot return raw signed bytes before broadcast.

## Phase 4 — read-only compatibility and policy completion (gate G4)

**Owner:** Codex; OpenCode may supply bounded read-only observation fixtures.
**Actions**
1. Complete L01–L03: chain/client behavior, exact fee variants and all fee components (L2 execution **and** L1 data fee), pending nonce behavior, target registration/code, real sender balances, resource ABI, finality evidence and authoritative receipt/event interpretation.
2. Establish genuinely independent operator observations or record that D05 cannot be satisfied.
3. Identify the current factory implementation and decide whether the full execution context is effectively immutable; otherwise design and independently review an atomic guard as a separate profile (D10).
4. Capture a real canonical receipt and event ABI before any receipt-verification claim.

**Exit evidence:** dated read-only observations with exact versions/blocks/hashes, operator identities, fee formula, finality policy hash, event ABI review.
**Exit test:** every UNKNOWN stays visible; no `eth_call` or estimate is relabeled as paid-transaction success.
**Blocked if:** fee bound, finality policy or immutability/guard evidence is missing — live activation remains blocked.

## Phase 5 — single separately authorized live acceptance (gate G5)

**Owner:** Founder for authorization; Codex for execution; independent observer for evidence.
**Actions**
1. Founder records one exact human grant naming account, target, netlist/calldata digest, native/resource ceilings, expiry, nonce family and finality policy. This is a **new** authorization, not an inheritance from D01–D12.
2. Execute one profile action through the reviewed protocol with the certified adapter and dispatch permit; record transaction hash, canonical receipt, actual costs and re-imported circuit content.
3. Treat UNKNOWN submission, rejection, revert and mismatched receipt as legitimate outcomes; never relabel them success.

**Exit evidence:** immutable intent/grant/permit bytes, dispatch record, canonical block/finality evidence, independent observation, recovery drill results.
**Blocked if:** any earlier gate is open, or the founder has not issued the exact live grant.

## Forbidden throughout

- No key creation, wallet connection, signing, broadcast, payment, spending or onchain deployment.
- No changes to frozen v1/M2/M3 schemas, accepted controller bytes, production schemas, acceptance checks or original evidence.
- No automatic cap increase, no manual estimate override, no "successful validation = publication" relabeling.
- No public solver/signer hosting or agent custody of broker/wallet authority.
- No merge of review work directly to `main`.

## Hackathon recommendation

**Do not include transaction authorization in the hackathon build.** The accepted MVP already delivers its
differentiator — refactor equivalence, witness replay, integrity manifests and read-only pre-flight —
with no wallet. Adding a signer/journal/guard stack would consume the remaining calendar on the exact
gates that are currently unresolved (D01, D02, D05, D06, D10, D11) and would put financial authority
inside a deadline-driven release. Keep the authority work as a **separate post-hackathon, separately
authorized** milestone. If a hackathon submission genuinely requires an onchain circuit ID, treat it as
an external, founder-authorized submission operation outside the product, as the PRD already specifies.

## Coverage crosswalk

| Requested adversarial category | Mock case | Live gate |
|---|---|---|
| Agent impersonation | A01, A02, A25 | G3 |
| Malicious metadata / changed calldata | A03, A04, A33 | G1/G2 |
| Signer/network substitution, wallet divergence | A05, A24 | G3 |
| Malicious RPC / reorg / receipt substitution | A14, A17, A18, A23 | G4 |
| Factory/beacon/processor change, execution-time change | A15, A16 | G4/G5 (D10) |
| Fee underestimation | new explicit case + A23 | G4 (D03/D06) |
| Nonce replacement / duplicate submission / expired signed | A07–A09, A20, A28 | G2/G5 |
| Broker key theft / journal rollback | new explicit key-theft case + A22 | G3 |
| Concurrent rolling ceilings | A11, A12 | G2 |
| Broker/application OS boundary | A25, M01–M05 | G3 |
