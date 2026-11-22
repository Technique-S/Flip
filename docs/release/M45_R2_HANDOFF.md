# M4.5-R2 — Release-readiness handoff

Date: **2026-11-22**. Branch: `codex/flip-m45-release-readiness`.
Accepted and freshly fetched main: `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`.
Production code, schemas, acceptance checks, lockfiles and previous independent evidence
are unchanged. This branch is to be committed/pushed **without merging**. No deployment,
public solver, tunnel, submission, wallet, signing, transaction or spending is authorized.

## Disposition

| Readiness layer | Result |
|---|---|
| Supported technical local demonstration | PASS with documented prerequisite/reference/engine bounds |
| Judge access | BLOCKED pending organizer-confirmed usable access arrangement |
| Submission completeness | PARTIAL: drafts ready; actual video/access/owner declarations not finished |
| Public interactive deployment | BLOCKED; current native service must remain loopback-only |
| Write-enabled publication | BLOCKED and intentionally outside hackathon minimum path |
| Manual auditory accessibility / independent novice trial | NOT TESTED; no invented success |

Recommended minimum: owner resolves rights and access interpretation, reviews the short
quickstart, obtains a real human accessibility/first-use check, records an honestly labeled
local walkthrough, and offers the pinned supported checkout plus artifacts/video. Consider
an inert static viewer only if access clarification makes it useful and the owner explicitly
authorizes hosting. Do not add a public native solver or transaction lifecycle for this release.

## Deliverables

| File | Purpose |
|---|---|
| [Readiness audit](M45_R2_READINESS_AUDIT.md) | Journey-by-journey results, fresh test/source observations and interface/accessibility gaps |
| [Access options](M45_R2_ACCESS_OPTIONS.md) | Current official-rule/source ledger; live versus recorded options and unresolved access compliance |
| [Submission draft](M45_R2_SUBMISSION_DRAFT.md) | Product/personas/model/addresses/new work, draft quickstart and troubleshooting |
| [Demo script](M45_R2_DEMO_SCRIPT.md) | Timed storyboard, actual capture plan and manual test matrix; not a produced video |
| [Release blockers](M45_R2_RELEASE_BLOCKERS.md) | PASS/PARTIAL/FAIL/BLOCKED/NOT TESTED gates, rights/security review and ordered worklist |
| [Evidence manifest](M45_R2_EVIDENCE.json) | Exact baseline, source retrieval limitations, command outcomes, observed live page identities, artifact hashes and dependency metadata |

R2 is an engineering audit, not a fresh independent security review. Earlier OpenCode
findings remain unchanged. The pre-library unmerged release evidence at
`ddbd72e655c0afe4085e5c949f5e1741c7a6f552` is historical context only. Current accepted
[post-merge record](../milestones/M45_AGENT_PORTABLE_POST_MERGE_ACCEPTANCE.md) and its
preserved final review supersede no original conclusions by editing them.

## Reproduction and observed results

Executed from the release-readiness worktree on Windows 11 x64, CPython 3.14.6,
uv 0.9.11, Node 24.18.0 / npm 11.16.0. The existing uv executable used for setup was outside
PATH; judge-facing instructions must provision it rather than depend on this machine's path.

```sh
uv sync --locked
npm ci --prefix apps/web
npm run lint --prefix apps/web
npm run build --prefix apps/web
uv run --frozen pytest -q --junitxml=.test-tmp/r2/python.xml -o junit_family=legacy
npm test --prefix apps/web
uv run --frozen ruff check .
uv run --frozen ruff format --check .
```

For isolated browser ports, this audit used PowerShell
`$env:FLIP_TEST_APP_PORT='19271'` and `$env:FLIP_TEST_RPC_PORT='19272'` before npm test.
The accepted test configuration launches its own loopback API and synthetic RPC. It does
not use the protected personal-browser session. No browser safety mechanism was bypassed.

| Check | Observation |
|---|---|
| Locked sync, npm ci, lint/build | Exit 0; two same-host frontend builds have matching hashes |
| Full Python | 702 passed in 763.42s, no skips |
| Full Chromium | 27 passed in 156.907s, no retries/flakes/skips |
| Ruff lint / format | PASS, 88 files |
| Nine schema drift checks / three Node parity gates | PASS |
| Independent agent/authorization, portability, final adapter review | PASS: 27 agent + 10 authorization, 12 portability, 26 final adapter checks (including 10 attacks) |
| Documentation links / new-doc coverage / credentials / archive custody | PASS: 23 local links, 862 tracked files scanned, zero credential findings; original archive/review bytes intact |
| Accepted-main CI | Windows/Linux SUCCESS, [44773778968](https://github.com/Technique-S/Flip/actions/runs/44773778968), checked via GitHub API in R2 |

The Python suite includes all 32 adapter tests and the existing archival timeout assertions.
The 120-second archival deadline was not increased. The inherited debugger test's response
synchronization remains unchanged and passed in the full browser suite. C10 uses the accepted
loopback changed-dependency wrapper; its prior provider-sensitive failure and original
independent observation remain documented, not overwritten.

Nine schema commands and exact parity commands are captured in the evidence manifest and
unchanged [CI workflow](../../.github/workflows/m1-contracts.yml). Existing replay helpers:

```sh
uv run --frozen python scripts/check_m45_agent_acceptance.py
uv run --frozen python scripts/check_m45_portability.py
uv run --frozen python scripts/check_m45_agent_portable_review.py
uv run --frozen python scripts/check_m1_repository.py --require-clean
```

The last command requires a clean committed worktree. New logs go to ignored scratch, not
original independent-result paths. Documentation link checking covers local paths/anchors
in these new files; external pages have individually recorded retrieval status. Inaccessible
submission fields remain NOT VERIFIED even though the local link structure passes.

## Source verification and interruption handling

Official rules were retrieved with the web retrieval tool during 2026-11-22
09:51:58–09:52:01 UTC. Event requirements, deadlines and access uncertainty are recorded
centrally in [the access ledger](M45_R2_ACCESS_OPTIONS.md); no blanket compliance claim is made.
Submission-form access was unsuccessful and not retried through a protected UI. A direct
HTTPS request for the event page also failed on this host, while independent web text
retrieval succeeded. Metadata does not invent an origin HTTP 200 or uncached response.

The earlier Computer Use stop could not verify the personal browser URL. It was not a
Flip failure. This resumed task made **no further Computer Use calls or equivalent personal
browser actions**. Existing isolated regression tests and local screenshot-file inspection
are separately authorized engineering checks; they are not a manual browsing/auditory test.

Separate live read-only source/library probes are timestamped in the evidence manifest.
A low-budget discovery returned UNKNOWN/RESOURCE_LIMIT; the standard-budget CLI returned
a bounded two-processor page successfully. No initial probe was hidden and no complete
registry or current proof was inferred from partial metadata. No transaction/write method
was used. Public repository visibility is confirmed; own-source license remains undecided.

## Remaining decisions and acceptance gates

- Owner: rights/license/permitted distribution, actual entrant/contact/eligibility fields,
  access clarification, final material approval and any future hosting/submission authority.
- Human tester: actual screen-reader speech, novice installation and judge-access rehearsal.
- Maintainer: small reviewed onboarding documentation correction; curate rights-cleared
  downloadable artifacts with complete notices if that access path is approved.
- Separate security review before any interactive hosting. Separate transaction/authorization
  scope before any write-enabled capability. Do not merge the proposed architecture or begin
  tape-out implementation as part of this handoff.

## Commit, push and follow-up status

The exact delivered documentation SHA is returned with the completed handoff; putting its
own hash in this file would be self-referential. Production evidence is pinned above.
Use `git log -1 --format=%H`, `git diff b537eb6 --name-only`, and the branch's GitHub Actions
status to audit the delivery. Only new R2 documents/evidence under docs/release may differ.

Push triggers the unchanged Windows/Linux workflow. Record its actual post-push result in
the final delivery response; do not label a queued run successful in these documents.
Nothing is merged, released, hosted or submitted by this task. Stop after the handoff.
