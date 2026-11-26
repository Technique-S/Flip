# Proof freshness, evidence integrity and security boundaries

## Proof freshness

Real browser execution (`visual-edit.spec.ts:424`) established the critical chain:

1. Open genuine sample, run an actual comparison → real `EQUIVALENT` heading visible.
2. Switch to Visual, add a NAND through explicit inputs → prior proof archived and cleared.
3. Undo edit → Evidence page shows `Historical comparisons (1) — not current verification`; **no current `EQUIVALENT` heading**; `Run and export evidence` disabled.
4. Redo → status shows unsaved changes relative to export checkpoint.
5. Save project (download request) clears dirty state; undo makes dirty again; redo clears again.

Returning to previously verified bytes does **not** reinstate proof authority. `App.invalidate()` stores `{request, proof, revision}` snapshots and clears `table/built/proof/obs/replayed/chainNote`. Historical records are bounded to 10 runs / 4 MiB with an eviction notice. No exported or previously accepted evidence file was rewritten; the "export" button requires a fresh current `proof` and is disabled while a draft/pending edit exists.

Stale asynchronous responses: `useCandidateEditor.ts:160-210` increments a generation token, aborts the previous `AbortController`, and ignores any response whose token no longer matches. Executed by `visual-edit.spec.ts:362` (late real compiler response ignored, duplicate rapid submit becomes one transaction) and `:566` (interrupted edit recovered only after real revalidation).

## Network and authority boundaries

- Only new network call: `api("compose", next, abort.signal)` (`useCandidateEditor.ts:181`). `api()` uses the existing loopback `/api/v1/…` path.
- No `fetch` to arbitrary URLs, WebSocket, RPC, wallet, signing, transaction or broadcast code in any changed source (`grep` over `apps/web/src/visual/**`, `App.tsx`, `Composer.tsx`).
- No new dependency; `apps/web/package.json` and lockfile byte-identical to accepted main.
- No React Flow mutation callback added; nodes/edges/handles remain non-draggable/non-connectable/non-reconnectable, Delete/Backspace do not edit (`visual-readonly.spec.ts:156`).
- Publication handoff test still reaches `STOP_AUTHORIZATION`; no transaction path.
- No new backend endpoint, schema version or canonical hash implementation.

## Release integrity and SEC-01

`docs/release`, `.github/workflows`, `scripts`, `apps/showcase`, frozen schemas and release trust metadata are byte-identical Git trees to accepted main. Pristine release guard PASS (19 checksummed inert files, 130 local links) and the seven original release-guard attacks still reject at their intended boundaries (showcase 28/28). CI bootstrap digest and protected-main ruleset (`28133104`, no bypass actors, required Ubuntu/Windows checks, stale-approval dismissal) remain active as recorded.

**SEC-01 remains OPEN / HIGH** under the owner's approved solo-maintainer development policy. V2-A does not close it; passing functional tests are not a trust-root guarantee. Reassessment is required before contributor expansion or public release.

## Credential and malicious-string audit

Changed source contains no credentials, private keys, mnemonic phrases or API tokens. Untrusted display strings are React-escaped text; the showcase build-integrity test (`showcase.spec.ts:217`) covers escaping of artifact strings. The only new persistent strings are bounded session-storage checkpoint/draft JSON (≤1 MiB request, ≤3 MiB recovery draft) and status messages.

## Findings

- **V2A-F2 (LOW):** `proposeNand`'s closed-key check uses `Object.keys`, so an object-literal `__proto__` (prototype setter, not an own key) is not counted as an extra field. Direct probe ACCEPTs the pure proposal, but the request is unaffected, and a JSON-parsed `__proto__` own key is REJECTED. Recommendation: build the command with normalized own keys (`Object.keys({...c})`) before the closed-key assertion. Regression: add the object-literal case to `visual-edit.spec.ts:148`.
