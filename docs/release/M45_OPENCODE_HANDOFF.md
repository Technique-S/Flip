# M4.5-R — OpenCode evidence handoff

**Branch:** `opencode/flip-m45-release-evidence`
**Baseline:** `09f2482beae84be6d919ecd6957c4153d1924cca` (accepted main, merge
commit #4; confirmed by `git rev-parse origin/main` and ancestry check for the
required merge commit).
**Commit:** `fc23517a8d0ed58eddb82a650a6fc0d34e590798`
**No merge into main. No production, schema, lock, CI or existing evidence file
was modified.**

## Created documents

| File | Purpose |
| --- | --- |
| `docs/release/M45_INDEPENDENT_READINESS.md` | Six-capability evidence matrix with classifications and exact sources |
| `docs/release/M45_HACKATHON_COMPLIANCE.md` | Official-rule verification with URLs, retrieval date and classifications |
| `docs/release/M45_DEMO_SCRIPT.md` | 12-step reproducible demo, narration, capture points and fallback |
| `docs/release/M45_DEVELOPER_TRIAL.md` | Five-developer moderated usability protocol (materials only) |
| `docs/release/M45_SECURITY_LICENSING_RISKS.md` | 12-item outstanding risk register, local vs write-lifecycle scope |
| `docs/release/M45_RELEASE_DOCUMENTATION_DRAFT.md` | Draft release-facing documentation |
| `docs/release/M45_OPENCODE_HANDOFF.md` | This file |
| `fixtures/m5-demo/cli-run/` | CLI demo inputs/outputs captured on the exact baseline |
| `fixtures/m5-demo/MANIFEST.json` | Byte/size and SHA-256 register of demo captures |

## Work actually executed on the baseline

```sh
git fetch --all
git rev-parse origin/main                 # 09f2482...
git merge-base --is-ancestor 09f2482... origin/main   # exit 0
uv sync --locked
uv run flip sample half-adder --out project.json
uv run flip compose --project project.json --out composition.json
uv run flip compare --project project.json --out comparison.json
uv run flip sample swapped --out mutation.json
uv run flip compare --project mutation.json --out difference.json
uv run flip export --project mutation.json --out evidence.json
uv run flip inspect-evidence --bundle evidence.json
uv run flip verify-bundle --project mutation.json --bundle evidence.json
npm ci --prefix apps/web && npm run build --prefix apps/web
```

Observed CLI exits in order: `0, 0, 0, 0, 1, 1, 0, 1`. Observed semantic
results: 81-byte netlist with digest `0x3dbb65a6…`; baseline EQUIVALENT /
UNSAT / HISTORICAL; swapped witness `01 → reference 01 / candidate 10`;
evidence bundle `FLIP_EVIDENCE` with `contentHash`; `inspect-evidence` exit 0;
`verify-bundle` recomputed DIFFERENT (exit 1). Raw output is in
`fixtures/m5-demo/cli-run/`.

Research used agent-reach (Exa search backend) plus direct retrieval of the
official OKX page on 2026-11-19. No submission was made.

## Six-capability evidence summary

| # | Capability | Independent classification |
| --- | --- | --- |
| 1 | Human and coding-agent workflows | **PARTIAL** — UI/CLI/schemas/shared engine verified; agent loop tooling only; deployment approval missing |
| 2 | Circuit and processor library | **MISSING as a library** — pinned labels/factory inspection only; no discovery, search, favorites or history |
| 3 | Authorized X Layer tape-out lifecycle | **MISSING** — preparation, structural validation and fee read exist; no preview, approval, submission, confirmation or receipt; no write path |
| 4 | Agent execution safety | **PARTIAL** — boundaries, chain checks, replay protection, credential scanning and recovery verified; approval/tx preview/spending limits missing |
| 5 | Portable circuit project format | **VERIFIED** — web↔CLI exchange, versioned schemas, identities, manifests, export/replay and deterministic reproduction |
| 6 | Circuit debugging diagnostics | **PARTIAL** — witnesses, actual/expected and bit-level labels verified; connection-level diagnostics and automated correction guidance missing |

Details, file paths and test names are in `M45_INDEPENDENT_READINESS.md`.
Codex's audit remains authoritative; this matrix is independent corroboration.

## Hackathon compliance findings

OFFICIALLY VERIFIED from <https://web3.okx.com/xlayer/build-x-series> on
2026-11-19: deadline 2026-12-07 23:59 UTC (explicitly provisional); 18+/entity
eligibility; form submission with description, users, revenue model and
addresses/links; developer tools and circuit design are eligible; demo video
recommended ≤3 minutes; shortlisted teams attend offline Demo Day; must use
TapeOut circuits/contracts/onchain data on X Layer and provide addresses;
FAQ explicitly says no need to deploy a new processor. UNCONFIRMED: any public
repository requirement and whether a loopback-only app satisfies "access
link". No submission performed. See `M45_HACKATHON_COMPLIANCE.md`.

## Risks and blockers

- Public hosting BLOCKED pending authentication, process isolation, aggregate
  budgets and request controls.
- Manual auditory screen-reader session BLOCKED/NOT TESTED.
- Write-enabled tape-out lifecycle not implemented; spending limits, approval
  and transaction preview are not applicable locally.
- Solver and dependency license notices, plus Flip's own source license,
  remain administrative open items.
- Hackathon "access link" for a loopback-only app is unresolved.

## Recommended next steps

1. Codex should reconcile the six-capability matrix with its authoritative gap
   audit and decide explicitly which capabilities are M5 scope versus out of
   scope.
2. Resolve the access-link question before submission; do not add a public
   deployment solely because local CI passes.
3. Schedule the screen-reader session and record the actual outcome.
4. Choose a Flip source license and preserve upstream solver notices before
   redistribution.
5. Re-check the official deadline on the submission date.

## Explicitly unexecuted / not claimed

- No live X Layer import, revalidation or pre-flight was run in this task.
- No write transaction, signing, wallet connection, payment or publication.
- No browser UI walkthrough was re-run on `09f2482`; UI steps in the demo script
  were observed on reviewed commit `d6a0035` and are labelled as rehearsed.
- No five-developer sessions, interviews, completion rates or timings were
  collected; `M45_DEVELOPER_TRIAL.md` contains materials only.
- No public deployment or public solver access test.
- No full production test suite re-run; the accepted M4 CI evidence is cited
  rather than duplicated.

## Final verification performed

- All modified files are under `docs/release/` and `fixtures/m5-demo/`.
- All authored JSON parses; demo fixtures registered in `MANIFEST.json`.
- Markdown local links resolve; no broken file references.
- Credential-pattern scan over both owned directories found no hits (64-hex
  content hashes are not credentials).
- Working tree clean after commit; remote branch matches local HEAD.

Stop after delivering the evidence package.
