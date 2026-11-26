# Recommended V2-A acceptance criteria

These are gates for a future independent review of a published V2-A head. They are not claims about the current baseline.

## G0 — Scope and authority

- V2-A edits only candidate NAND components through the existing compose path. Python remains the sole compiler, evaluator and verifier. No JS NAND evaluator, REF resolver, SAT, new endpoint, new schema version, transaction/signing or hosting path.
- `packages/**`, `fixtures/**` except the new V2-A namespace, `docs/schema/**`, `docs/release/**`, accepted evidence and CI security policy remain byte-identical to baseline `fc9c0c1…`.
- Every command is bound to exact `generation` and `requestHash`; stale, unbound or unknown commands fail closed with zero state and zero network change.

## G1 — Canonical parity

- For each ACCEPT case, the stored request equals the expected candidate object in its fixture, with all non-candidate fields byte-identical to the case input.
- Trusted compose output for the edited request is computed fresh; project/manifest/netlist hashes are recorded, never asserted from this package.
- For each REJECT case, request bytes are unchanged and no partial graph is rendered.
- Component order is deterministic; no silent index renumber, truncation or normalization.

## G2 — Result freshness and dirty state

- A build or proof is current only when its binding hashes equal the exact post-edit request/project hash.
- Any semantic edit, undo/redo branch change or removal invalidates current result status; stale results may be shown only with explicit historical labeling and never with EQUIVALENT/DIFFERENT as a current claim.
- Drafts are visibly non-executable; cancel restores exact prior bytes; commit applies only a response matching the latest generation and request hash.
- Unsupported edits are unavailable with a stated reason and preserve original data.

## G3 — Read-only boundaries and security

- REF internals, LATCH/stateful structures, sources, imports, manifests, processor/circuit identities and referenceCandidate remain read-only for NAND-only V2-A.
- Untrusted display strings are React-escaped text; no HTML/event handlers, arbitrary URLs or non-loopback requests.
- Positions/layout never alter wiring, request bytes or semantic hashes.
- Keyboard Delete/Backspace and clipboard shortcuts outside an explicit editing scope do not mutate; unsupported event combinations fail closed.

## G4 — Interaction and accessibility

- Keyboard-only add/connect/reconnect/delete produces exactly the same canonical bytes as pointer interaction.
- Focus order, visible focus, status announcements and focus return are verified; Delete is ignored in text fields; Escape cancels the active gesture.
- axe zero violations at desktop, 390px and 320px; reduced motion honored; no duplicate initialization or solver call across StrictMode remounts.

## G5 — Network and performance

- Zero HTTP requests during local draft/edit operations; exactly one compose request on explicit build; no request on rejection.
- Display budgets (500 components, 1,000 connections, 4,096 pins, 512 nIn/outputs) are enforced before allocation; oversized commands rejected explicitly with no partial graph.
- 100/200 and 500/1,000 node benchmarks are V7 work; V2-A acceptance does not claim measured large-graph performance.

## G6 — Regression and custody

- Full workbench browser suite, release guard/showcase suite, full Python suite, frozen schema/canonical checks, lint/build, custody and credential scan at the exact V2-A head on Windows and Ubuntu.
- All 56 cases promoted to executable tests only after SB-1…SB-10 resolution; until then they remain prospective and are not counted.
- Original V1 evidence and this test-design package remain unchanged.

## Decision rule

Merge V2-A only with **PASS on G0–G6**, no BLOCKER/HIGH findings, exact dual-OS CI success at the reviewed head, and explicit owner resolution of SB-1, SB-3, SB-4, SB-5 and SB-9. Full P7 and public-release readiness require separate evidence; V2-A alone does not establish either.
