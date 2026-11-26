# Explicit input-binding authorization

After the Phase 1 checkpoint in commit `73d70b971b64de899acd9f6d2f49301eda8d6217`, the owner was asked:

> A canonical NAND requires two input connections. Your request says to stop if creation requires adding wires. Do you authorize Add NAND to collect two explicit numeric source/pin selections, then validate and commit atomically, while keeping interactive wiring out of scope?

The owner's response on 2026-11-26 was:

> Authorize explicit input bindings

This authorizes the narrow complete NAND creation form. It does not authorize placeholders, interactive wiring, REF authoring, new canonical schemas, V2-B/C, wallet/signing/transactions, deployment, public solver hosting or weakening trust/custody controls. The original checkpoint and original authorization remain unchanged.
