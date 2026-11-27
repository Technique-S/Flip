# V2-B0 command and transaction contract

Implementation scope: pure foundation only. Production base `2fa7281ba01557f484cef2878e484b6e16f3ffd2`; implementation/test head `35d997aa161fa7ce5fa1e156453bb69f33ef80c1`. Initial runtime implementation `7f67a53d1eca3f75be6d225d8570db7fafa14952`; test synchronization `b4ff854c1b4b5e2164f8dee1bebd5575cf98e227`; guard evaluation-order correction `35550556d29081a506ddff2e5d9899dd08e21889`; alias-preserving replacement correction at the final implementation head. Approved architecture planning `3ab3d4fdbf8748fbc88c2a0d091022b195a76ab6` and final evidence `b65140670f1207501d1db165c8bce353bdbbeb36` remain on their original branch. No architecture or historical evidence is rewritten or copied into this implementation PR.

## Implemented pure functions

`interactiveCapacity(Execution)` reports destinationPins P, sourcePins W, score P×W, externalInputs, outputs and full JSON UTF-8 requestBytes. W uses the original sourceAlias lookup and `?.nOut ?? 1` fallback, including its behavior on metric-only malformed metadata. `checkInteractiveBudget` retains P×W ≤65,000, nIn/output count ≤255 and requestBytes ≤1,048,576; it reports measured values and distinguishes UI from native/solver limits. Its pin-table/count guards execute before full serialization, preserving the original denial order. Git-blob-pinned before/after probes and a serialization sentinel regression verify that ordering; the sentinel is metric-only test instrumentation, not supported project-transport code. Existing display caps and 100-transaction/4 MiB history bounds are unchanged. The helper is not a canonical request validator.

Descriptor-based normalization checks exact own string keys, enumerable own data descriptors and dense two-pin NAND arrays. Accessors/inherited required values/unknown own or symbol keys fail closed; values are copied to explicit clean records. Array `length` is the standard required non-enumerable data property, not an exemption for arbitrary hidden keys. Reflection errors become bounded generic errors; executable Proxy traps are not sandboxed. Object-literal `__proto__` changes a prototype without adding an own field, so exact own data fields normalize normally; JSON/computed/defined own `__proto__` is an unknown field and is rejected. Canonical names such as constructor/prototype remain allowed.

`normalizeReplaceBinding(unknown)` accepts exactly:

```ts
type BindingTarget =
  | { kind: "component-input"; instanceId: string; pin: number }
  | { kind: "output"; pin: number };
type ReplaceBinding = {
  type: "ReplaceBinding";
  target: BindingTarget;
  source: { component: string | null; pin: number };
};
```

`proposeReplaceBinding(acceptedExecution, unknownCommand)` is synchronous and pure. It requires an **already native-accepted JSON Execution**; the TypeScript type alone is not evidence of acceptance. It reuses current bounded projection/REF-interface guards, resolves canonical component IDs and numeric slots, enforces source range/direction/order and replaces exactly one PinSource in a structured clone. Valid destinations are existing NAND/REF inputs or existing final-output slots. Sources are external bits or preceding component outputs; all existing component outputs can feed final-output slots. Fan-out/repeated sources remain legal. No sorting, new component/output/source, identity/dependency change, bus, constant or LATCH is introduced.

An identical normalized binding returns the **exact input request object**, without cloning or reordering fields. This identity is the no-op signal: the caller must not issue validation, history, revision, checkpoint or proof operations for it. A changed proposal returns a new complete Execution with every unrelated field unchanged. Since structuredClone preserves object aliases, replacement additionally detaches the candidate and changed component/array path. Shared referenceCandidate designs and shared input/output arrays therefore retain their previous values, as verified on native-accepted aliased inputs. This preserves JSON semantics without changing canonical encoding or rewriting unrelated fields. No history or proof object is passed to this function and it has no state, storage, network, wallet or graph-store access. React Flow is not imported or serialized.

These local checks do **not** validate imported netlist bytes, manifest hashes, dependency closure/environment or referenceCandidate semantics. Native compose remains mandatory both to establish the accepted base and to accept a changed full proposal. The native tests demonstrate corruption cannot establish an accepted base; no local metadata predicate is promoted to canonical authority. No new API/schema is introduced.

## Reusable transaction seam specified for B1 — not implemented

The authorization explicitly permits pure proposal plus native test harness without enabling UI commits. B0 chooses that boundary; there is no production session/token/commit adapter or new UI caller. A future implementation must follow this seam and test it before activation:

1. From the shared idle editor, require the request was accepted through the real local compose path. Capture an opaque session identity, accepted revision, `requestKey(fullAcceptedExecution)` and a clean copy of the previous target binding. The fingerprint is exact UI JSON, **not a canonical project hash**. Use normalized command records and a stable component ID, not a stale array index or rendered handle string.
2. Propose on that accepted request. If the result is the same object, stop before POST, proof invalidation, revision/history/dirty changes. Otherwise capture the exact proposed payload/fingerprint and one prospective history transition without publishing either. Keep mutable external references out of the transaction envelope; recompute/assert the one-slot proposal when checking its base.
3. Acquire the shared synchronous pending lock and generation token, then validate the complete proposed request through existing `POST /api/v1/compose` with AbortSignal. No alternate validator, route or optimistic graph-store mutation. Keep accepted request/history/checkpoint/proof intact during a rejected, aborted or malformed response. A proposal is not a proof.
4. After a successful response, validate the existing compose response contract before consumption; recheck session, revision, full base fingerprint, previous target binding, operation generation and immutable proposed payload. A changed base or cancelled generation rejects the result. An old response cannot commit to a new session even when projectId is reused. Native processing may outlive client abort; that is never commit authority.
5. Only a still-authorized explicit operation with a valid native response can atomically publish accepted request plus **one** bounded complete-request history entry, revision/dirty transition and current-proof invalidation. Retain prior evidence with its original request/revision as historical. A failed validation consumes no history and cannot clear Redo or alter saved checkpoints. Undo/Redo need native validation and never restore an old proof as freshly verified.

**Authorization refinement:** the approved architecture described invalidation on entering Review. The newer B0 authorization says only successful authorized commits may invalidate current proof authority. This seam therefore preserves current accepted-revision proof until successful wiring commit; pending proposals must block incompatible execution/export without presenting proposal proof. Existing V2-A NAND/Advanced invalidation behavior is deliberately unchanged. B1 must implement and independently verify the new wiring transaction behavior; B0 does not claim that work completed.

The proposed seam is a specification, not a second test-only implementation presented as production. Session races, response corruption, cancellation/recovery and new wiring-proof transitions remain B1 dependencies. Current V1/V2-A implementations/tests continue to cover their own original paths.

## Native harness and limits

New Playwright cases use the existing real local compose endpoint for base/proposal acceptance, native negative cases and a genuine comparison for no-op proof preservation. Multi-output REF input is generated in memory by the existing synthetic FakeChain fixture helper, then accepted by real compose. No accepted fixture or raw historical hash is rewritten. Metric-only synthetic envelopes isolate exact 65,000/65,001, scalar-interface, UTF-8 size and display-allocation boundaries; they are explicitly not native-accepted fixtures.

No-op identity, unchanged input bytes, whole-request equality against one-slot expected results, REF/source/reference/maps preservation, native gate-limit rejection and bounded history interoperability are observed. These tests do not establish B1 interaction, transaction races, accessibility, touch or gesture performance. The live canvas remains read-only, without an Edit connections mode or new wire editing controls.

SEC-01 remains OPEN/HIGH. F1/F2 fixes require independent OpenCode disposition after complete regressions; source changes alone do not constitute independent closure.
