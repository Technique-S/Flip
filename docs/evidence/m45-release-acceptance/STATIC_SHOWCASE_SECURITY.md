# Static showcase — no-solver, no-signing, no-write-RPC acceptance checks

**Status: CHECK SPECIFICATION + EXECUTED BASELINE SOURCE INSPECTION. Date 2026-11-22.**
A static showcase/viewer does **not** exist in accepted main. These checks apply to a future, separately
authorized artifact. Current `apps/web/dist` is a frontend for same-origin Python API routes and must not
be presented as a static showcase (Codex R2 access ledger).

## 1. Scope and hard rules

The proposed viewer may only display curated, precomputed evidence. It must not:

- invoke the native SAT solver, a Python worker, WASM solver or any child process;
- call `/api/...` routes, a tunnel, a reverse proxy or loopback services;
- connect to a wallet, inject a provider, request accounts, sign, broadcast or construct transactions;
- make any JSON-RPC call, especially write methods;
- generate a fresh `EQUIVALENT`, `VERIFIED_CORRECTION`, publication or deployment result from user input.

Any viewer that fails one of these rules is not a static showcase. It inherits the full public-hosting
security review that is currently BLOCKED (R2 G23).

## 2. Executed baseline evidence (accepted main `b537eb6`)

These commands were run read-only in this review. They describe the **current source**, not a viewer artifact.

| Check | Command / method | Observed result |
|---|---|---|
| Frontend wallet/signing references | Case-insensitive `grep` over `apps/web` for `eth_sendTransaction|eth_sign|personal_sign|wallet_|signTransaction|private key|seed phrase|mnemonic|broadcast|window.ethereum|okxwallet` | 3 textual matches only: two "No transaction broadcast" disclosure strings and a single-provider note in `Library.tsx`. No wallet SDK, provider object or signing call found. |
| Frontend network calls | `grep` for `fetch(` / `/api/` in `apps/web/src` | `model.ts` uses `/api/v1/${path}`; `Library.tsx` uses `/api/library/v1/execute`; `AgentPortable.tsx` uses `/api/agent/v1/portable`. Current frontend depends on the API. |
| No JS SAT engine | R2 source/build observation | `apps/web/dist` contains no JavaScript SAT engine; core actions require the API. Not re-built in this review. |
| Core RPC allowlist | Read `packages/flip-core/src/flip_core/rpc.py` | `READ_METHODS = {eth_chainId, eth_getBlockByNumber, eth_call, eth_getCode, eth_getStorageAt}`; `call()` raises `INVALID_INPUT` for non-allowlisted methods. `eth_call` is further restricted to exact selector/calldata shapes. |
| Design-script gap | Directory listing of `scripts/` | No `scripts/check_write_rpc_absence.py` exists. The technical design names it as a proposal; absence of an implemented checker is recorded. |
| Local launcher guards | Read `packages/flip-api/src/flip_api/local.py` | Binds `127.0.0.1`, uses `TrustedHostMiddleware` for `127.0.0.1`/`localhost`, rejects non-loopback clients and cross-origin requests, sets `proxy_headers=False`. |
| Terminal publication handoff | `agent_operations.py` read; R2 browser/Python assertions | `STOP_AUTHORIZATION` carries `signingCapability=False`, `retryable=False`; R2 reports one stop log and no later queued operation. |

## 3. Viewer checks — specification (must be executed on the built artifact)

| ID | Check | Method | Required result |
|---|---|---|---|
| S-01 | Artifact is static | Build manifest; serve from a plain static file server | Only HTML/CSS/JS/images/data JSON; no server runtime, no API routes, no environment secrets |
| S-02 | No native solver invocation | Static scan for `pysat`, `solver_worker`, `FLIP_LOCAL_SOLVER`, `minisat`, `subprocess`, `spawn`, `Worker`, `wasm`, `import(` | Zero executable references; any mention is inert documentation text only |
| S-03 | No child processes | Runtime process snapshot before/after all viewer interactions | No Python, uvicorn, solver or shell process attributable to the viewer |
| S-04 | No API calls | Browser network capture on all viewer paths | Zero requests to `/api/`, `127.0.0.1`, localhost, tunneled hosts or any same-origin API route |
| S-05 | No wallet/signing | Static scan plus network/permission observation | No provider injection, wallet SDK, `eth_sign*`, `personal_sign`, `eth_send*`, key/seed inputs or wallet popups |
| S-06 | No RPC writes | Static scan and network capture | No JSON-RPC POST and no `eth_sendRawTransaction`, `eth_sendTransaction`, `eth_sign*`, `wallet_*`, `eth_accounts`, `eth_requestAccounts` |
| S-07 | No fresh proof generation | UI interaction trace | No control starts SAT, comparison, witness replay or correction verification; all displayed verdicts come from curated recorded files |
| S-08 | Truthful labels | Visual/DOM assertion on every verdict and evidence card | `HISTORICAL` or `RECORDED` visible; `CURRENT` never claimed from a recording; provenance and native engine identity shown |
| S-09 | Negative claims | Execute `claim-negative-cases.json` | All 12 cases rejected or relabeled; no misleading CURRENT/EQUIVALENT/deployment/verified-correction claim survives |
| S-10 | STOP boundary | Search curated records and UI copy | `STOP_AUTHORIZATION` shown as terminal; no "deployed", "published", "transaction succeeded" or wallet scene |
| S-11 | Escaped content | Hostile-text fixture with HTML/instructions in aliases and labels | Rendered inert as text; no script execution, no layout injection, no authority effect |
| S-12 | No hidden downloads/executables | Artifact inventory | No executable payloads; any downloadable project/evidence/receipt is a data file with rights clearance and notices |
| S-13 | Storage hygiene | Application data inspection | No credentials or personal data; no silent writes to library favorites/recovery for viewer visitors |
| S-14 | Transport policy | Headers and runtime capture | Restrictive CSP, no inline evaluation; no WebSocket to an API or RPC; static assets only |
| S-15 | Judge rehearsal | Neutral browser/network | A tester unfamiliar with Flip can navigate and explain what is recorded vs live; no privileged developer knowledge needed |

## 4. Required evidence package for a viewer PASS

1. Exact built artifact hash and its source commit.
2. Static scan output for S-02/S-05/S-06 with file paths and match counts (expected zero executable matches).
3. Browser network HAR/log covering every navigation path in the storyboard.
4. Process snapshot or OS tracing covering the same session.
5. Screenshots/DOM assertions for S-08/S-09/S-10.
6. Owner authorization for hosting and organizer confirmation that a static viewer is acceptable access.
7. Rights-cleared asset inventory and notices (see `RIGHTS_AND_NOTICES.md`).

## 5. Failure handling

Timeout, blocked request, missing artifact or ambiguous network evidence is **UNKNOWN**, not PASS. Do not
infer absence of a call from a single successful render. Repeat the capture on a neutral network and record
tool/browser versions. Any discovery of a live API/native/wallet path converts the viewer into a hosted
service requiring the full R2 G23 security review before it may be used for judging.

## 6. Relation to negative claim fixtures

`fixtures/m45-release-acceptance/claim-negative-cases.json` encodes the misleading-claim cases that S-08/S-09
must reject. The fixture is a specification, not an executed test result; a viewer implementation must run
each case and retain per-case observed DOM/state output before claiming PASS.
