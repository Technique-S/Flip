# M4.5-0 authorization security review — handoff

**Status: REVIEW EVIDENCE ONLY. Date 2026-11-22.**
This handoff records what was reviewed, what was written, what was actually executed, and what remains
blocked. It grants no approval and authorizes no implementation, wallet, key, transaction or release.

## 1. Identity and scope

| Item | Value |
|---|---|
| Reviewer | OpenCode / HY4 Flash (supporting engineer) |
| Branch | `opencode/flip-m45-authorization-security-review` |
| Base | accepted main `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b` |
| Proposed architecture | `codex/flip-m45-authority-design` @ `8ea1b26c2667b2db86c34087e25c976f121c147e` |
| Proposal's declared baseline | `09f2482beae84be6d919ecd6957c4153d1924cca` (stale relative to accepted main) |
| Write scope used | `docs/evidence/m45-authorization-security-review/`, `fixtures/m45-authorization-security-review/` only |
| Runtime code / schemas / acceptance checks / original evidence | Unchanged |
| Keys, wallets, signing, broadcast, spend | None created, connected, signed, broadcast or spent |

## 2. Files written

Documentation:

- `docs/evidence/m45-authorization-security-review/SECURITY_REVIEW.md`
- `docs/evidence/m45-authorization-security-review/FOUNDER_DECISIONS.md`
- `docs/evidence/m45-authorization-security-review/COMPATIBILITY_GAPS.md`
- `docs/evidence/m45-authorization-security-review/MINIMUM_SAFE_PLAN.md`
- `docs/evidence/m45-authorization-security-review/HANDOFF.md` (this file)

Fixtures:

- `fixtures/m45-authorization-security-review/README.md`
- `fixtures/m45-authorization-security-review/threat-cases.json`
- `fixtures/m45-authorization-security-review/rpc-observations.json`
- `fixtures/m45-authorization-security-review/MANIFEST.json` (checksums only)

No file outside these two directories was created or edited on the review branch.

## 3. Commands actually executed (read-only unless noted)

Repository analysis:
- `git fetch origin`; `git cat-file -t` on both specified commits; `git ls-tree`, `git diff`, `git log` for inventory and guard comparison.
- `git worktree add` for the review branch (from accepted main) and a detached read-only worktree at the proposed commit.
- File reads of the six proposed documents and the accepted baseline documents listed in `SECURITY_REVIEW.md` §0.
- `grep` of `STOP_AUTHORIZATION` in `packages/` and direct read of `agent_operations.py` around the terminal handoff.
- `python` local Keccak selector recomputation using the accepted dependency-free helper; results matched known selectors.

Web/research:
- `agent-reach doctor --json` → command not installed (failure recorded).
- `mcporter call exa.web_search_exa ...` for OKX X Layer network, RPC, finality/OP Stack, fee model, provider API and TAP-10 evidence.
- `webfetch` of the OKX RPC endpoints page → transport error; search-result highlights used instead.
- `gh api repos/TapeOutProtocol/TAPs/pulls/88/files` → confirmed TAP-10 v1.2 PR is open and read its patch.
- `webfetch` of the GitHub PR page confirmed open status.

Bounded onchain reads (all read-only JSON-RPC over `https://rpc.xlayer.tech`):
- 1 × `eth_chainId`; batches of 10, 9, 4 and 2 calls; 1 × single `eth_call`.
- Methods: `eth_chainId`, `eth_blockNumber`, `eth_getBlockByNumber`, `eth_getCode`, `eth_getStorageAt`, `eth_call`, `eth_getTransactionByHash`, `eth_getTransactionReceipt`, `eth_estimateGas`.
- Exact observed values are in `fixtures/m45-authorization-security-review/rpc-observations.json`.
- `xlayerrpc.okx.com` `eth_chainId` produced no response in this session.

Verification of own artifacts:
- `git status --porcelain` before writing (clean at accepted main).
- SHA-256 recomputation of the two JSON fixtures for `MANIFEST.json`.

## 4. Findings summary

- Design-only: **CONDITIONAL** — coherent fail-closed specification, stale baseline and unresolved live claims.
- Mock-only: **CONDITIONAL GO** — with fake broker/signer/chain and zero caps, after Decision Phase 0.
- Live signer integration: **NO**.
- Mainnet execution: **NO**.
- All D01–D12: **PENDING**; no founder decision was made by this review.
- Critical gates: D05 finality/operator independence, D10 execution-time immutability/guard, D03/D06 complete fee model, D01/D02/D11 signer/platform/key evidence.
- Hackathon: **do not include** transaction authorization in the hackathon build.

Full findings are in `SECURITY_REVIEW.md` §2–§6 and `COMPATIBILITY_GAPS.md`.

## 5. Limitations, failures and blockers

- The OKX docs host could not be fetched directly; evidence relies on primary-source search highlights and the TAP-10 GitHub PR patch. Re-read the live pages before any live decision.
- `agent-reach` CLI is not installed; its `mcporter` exa backend was used instead.
- The sampled receipt did not expose L1 fee fields; OP Stack documentation says such fields may exist. Receipt/event semantics remain UNKNOWN.
- One untrusted RPC endpoint was used. This is not independent-operator evidence and not finality evidence.
- No signer, wallet, device or key was available; signer compatibility is UNVERIFIED.
- No transaction-system implementation exists; all A/M/L cases remain unexecuted specifications.
- The proposal's repository-guard change is Codex-owned and was not applied here.

## 6. Source provenance

- Proposed documents: commit `8ea1b26c2667b2db86c34087e25c976f121c147e` on `codex/flip-m45-authority-design`.
- Accepted baseline: commit `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`.
- Accepted read-only fixtures: `fixtures/m45-library-discovery/observations/live_xlayer_observation_0x48be576.json` and `seeds/verified_known_addresses.json` at accepted main; their values are referenced, not copied as new claims.
- External primary sources are enumerated in `COMPATIBILITY_GAPS.md` §4.
- Onchain observations are single-provider, read-only and dated 2026-11-22.

## 7. Next steps for the founder / Codex

1. Founder records D01–D12 with the required evidence; no default is auto-approved.
2. Codex re-bases the additive authority documents onto accepted main and defines the inert `STOP_AUTHORIZATION` → proposal boundary.
3. Codex reviews the repository-guard change against the accepted guard.
4. Only then start Phase 1/2 mock work under the gates in `MINIMUM_SAFE_PLAN.md`.
5. Keep all live paths disabled until G0–G4 pass and a separate exact live grant is issued (G5).

**Review commit SHA:** the single commit on this branch; reported in the final handoff message and
available from `git log -1` on `opencode/flip-m45-authorization-security-review`.
