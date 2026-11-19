# M4.5-2L-C Circuit Library acceptance

Assessment date: 2026-11-19. **Integration verdict: FAIL — independent OpenCode
evidence is still pending.** The corrected production interfaces pass platform CI
and focused acceptance. This report does not substitute those results for the
required independent review.

## Exact starting state and provenance

- Accepted remote main: `09f2482beae84be6d919ecd6957c4153d1924cca`.
- Original library head: `dec9420bb76e9245c6740bf3d92031d175e408ec`, locally clean
  and equal to its origin ref before acceptance work.
- Research: `5c7bcfbc8babb58d5f040fe869e2017f4a8c46fd`, preserved as the second
  parent of library merge `9867dcb`; its first parent is accepted M4.
- Acceptance branch: `codex/flip-m45-library-acceptance`.
- First corrections commit: `72278a15e2cd7c6aefc4bf00c57253cf094d01f9`.
- Fully checked acceptance head before this handoff update:
  `9b5df5ebd69f1e696881e09a53d1aafed2bc87b8`. The following handoff update adds
  only evidence/reporting; production code remains the corrections commit's state.
- Remote main remains unchanged. Local `main` points to the older historical
  `02463b1`; it is not the acceptance base and was not changed.
- The proposed authority-design branch is not merged. No debugging fixtures,
  diagnostic production code, wallet, signer or transaction functionality is added.

All 24 research files and their 19-file byte manifest remain unchanged. Historical
audit, M1/M2/M3 schemas, evidence and original tests are preserved. New reproductions
are in separate Codex acceptance test files, not the reviewer's directories.

## Independent review coordination

The user identified OpenCode M4.5-2L-V as assigned to
`opencode/flip-m45-library-independent-review`, with expected report
`docs/evidence/m45-library-independent-review/M45_LIBRARY_INDEPENDENT_REVIEW.md`
and supporting `fixtures/m45-library-independent-review/`.

The local review branch exists at the original library head and the reviewer is
assembling its own artifact directories. No completed review commit has been
supplied or fetched yet. **Independent review is pending.**
No OpenCode finding, approval or reproduction is claimed. Fetch and inventory that
branch when pushed; inspect and reproduce actual findings, preserve its report,
then update this section with exact commit, findings and dispositions. Do not merge
this PR before that evidence is available and required checks are green.

## Codex acceptance findings and corrections

These findings were reproduced against the actual production core/API or browser
at the original library head; they are not attributed to OpenCode.

| ID | Reproduction before correction | Correction and focused evidence |
|---|---|---|
| C-L01 | Save an alias, then favorite the same circuit: core search for the alias returns zero results. Favorite text overwrites alias text in the index. | Accumulate both independent metadata sources. New core/API test searches alias, alias tag, favorite label and description. |
| C-L02 | Discover circuits, change processor bytecode only, refresh factory discovery: response says COMPLETE and cached circuits remain HISTORICAL. | Compare each observed processor environment with its cached records; mark affected circuits STALE and emit ENVIRONMENT_CHANGED. Favorite remains, and no import payload is returned. |
| C-L03 | Restore an unsupported JSON catalog in browser storage: validation rejects it and the library is empty despite known-address fallback. | Retry only the offline search with a seed catalog; retain original saved bytes. On a later explicit edit, preserve a recovery copy before saving the new catalog. New browser test checks initial bytes and recovery copy. |
| C-L04 | Import #1 then #2 and restore the browser: Recent imports displays #1 first. | Sort the recent collection by the persisted recent-import order. New browser test imports through the production API and checks #2 first after restoration. |

Before corrections, the core reproductions produced **2 failures and 1 security
test pass**; the browser reproductions produced **2 failures**. After corrections,
the existing 21 library tests plus three new core tests passed (**24/24**) and both
new browser tests passed (**2/2**). No historical assertion or corpus expectation
was weakened to suppress a failure.

The additional security test rejects persisted CURRENT claims and confirms a
previously imported circuit cannot be re-imported after isCPU becomes false.
Library import into composition consumes only a fresh complete M2 import, never a saved
catalog record, favorite, alias or recent pointer.

## Required acceptance coverage

| Requirement | Executable evidence |
|---|---|
| cpuCount/cpuAt/isCPU, processor pagination, duplicate addresses | Existing C01/C04/C10 core tests and pinned cursor tests |
| Exclusive nextId, sparse/nonexistent IDs, large ranges | C02/C03/C04, known/unknown revert classification, L03 browser journey |
| Known-address fallback, invalid stored catalog recovery | C05/C11, L02 and new LC01 browser tests |
| Search, display metadata, aliases, authority rejection | C01/C02/C12 and new C-L01 core/API test |
| Favorites, recents, browser persistence and order | C11, bounded-recents test, L01, new LC01/LC02 |
| Factory/beacon/processor execution changes | C07/C08 and new C-L02 processor-code test |
| Revalidation before composition/import transition | Complete M2 import/revalidation tests, L01/L03, unregistered-import acceptance test |
| Reorg, wrong chain, RPC outage/throttling | C05/C06/C09, retry/error tests, canonical pinned-header checks |
| CLI/API parity, safe CURRENT boundary | Existing byte-parity tests and new saved-CURRENT/unregistered-import test |
| Resource bounds, deadlines and abort | 50-ID limit, request/retry budgets, callback abort/deadline tests and overlay quota test |

The research scripts are synthetic scenario descriptions, not complete raw wire
recordings. The existing test adapter's documented in-memory tuple normalization
and synthetic environment supplementation remain unchanged. Fixtures are never
rewritten to repair their malformed delimiters.

## Validation outcomes

Original-head CI was inspected: [run 44430900962](https://github.com/Technique-S/Flip/actions/runs/44430900962)
at `dec9420bb76e9245c6740bf3d92031d175e408ec` passed both Ubuntu and Windows jobs.
That does not substitute for CI on the corrected acceptance head.

| Check | Current outcome |
|---|---|
| Focused library tests at first corrections state | PASS — 24 tests |
| New browser reproductions after corrections | PASS — 2 tests |
| Complete inherited production suite and additional tests | CI PASS — 538 tests on each OS; see local timeout/rerun detail below |
| Complete browser regression suite | PASS — 16 tests locally and on both CI platforms |
| Ubuntu/Windows CI on acceptance code | PASS — PR run 44484376094 at fbef352 and latest run 44486873838 at 9b5df5e; both OS jobs succeeded |
| Independent Keccak selectors | PASS — 11 research signatures |
| Fixture hashes | PASS — 19 registered files / 12 synthetic scenarios |
| M1/M2/M3/library schema drift | PASS |
| Python/Node canonical hash parity | PASS — six vectors |
| Frontend lint/build; Python lint/format | PASS |
| Custody/credential scan | PASS in both platform CI jobs and local standalone require-clean scan at 9b5df5e; zero findings |
| Separate live read-only smoke | PASS — bounded processor and circuit pages; 21/64 requests each |

The complete starting head contains 535 tests: the earlier 531-test run plus four
later M4.5 guards. The three Codex acceptance core tests bring this to 538. No
starting test was removed, excluded or rewritten. Downloaded CI JUnit artifacts
show **538 passed, zero failed/skipped on Ubuntu and Windows**, with M3/M4 reports
PASS. Their actual job metadata and counts are in
[ci-results.json](m45-library-acceptance/ci-results.json).
The later [9b5df5e PR matrix](https://github.com/Technique-S/Flip/actions/runs/44486873838)
also passed both platforms. The [standalone custody result](m45-library-acceptance/custody-results.json)
records its exact checked commit and credential/registered-evidence results.

The first local full run produced 537 passes and one inherited M3 scratch-generator
timeout under a custom temporary-directory override. A focused custom-layout rerun
also exceeded its unchanged 120-second timeout. The same unmodified test then passed
in the prescribed default layout in 85.56 seconds. Both failures and the successful
rerun are preserved in [local-test-results.json](m45-library-acceptance/local-test-results.json).
No timeout was increased, test expectation changed or archive rewritten. The cause
of the two custom-layout timeouts has not been established; the results are reported
separately from the clean full-platform CI passes.

The [browser result summary](m45-library-acceptance/browser-results.json) records all
16 completed local journeys. The [separate live capture](m45-library-acceptance/live-readonly.json)
records processor count 430 at block 76306412 / hash
`0xcabd495802f540c45043dfe57102002e9f21b4a3c3ba6e4d6a03c1420b01ea1f`
and two circuit candidates below exclusive nextId 104 at block 76306422 / hash
`0xd59720f75402e4e6b9117409dfbd5c0b7f6681452a6cb1163ef46fa65590b298`.
Both observations came from `rpc.xlayer.tech`, verified chain 196, used 21 of 64
requests and were PARTIAL_BOUNDED. They are single-provider read observations,
not proof of a complete catalog, current execution or publication.

Mandatory tests prohibit external networking. Live observations will be run and
recorded separately; timeouts remain UNKNOWN. The public RPC is a single untrusted
provider and cannot establish independent consensus truth.

## Security and remaining limits

Only inherited read-allowlisted RPC methods and fixed read selectors are used.
Saved catalog freshness cannot express CURRENT. Metadata is escaped React text,
stripped of controls, bounded and structurally forbidden from adding authority
fields. Cursors bind block number/hash and environment and have bounded offsets;
all scans have page/request/deadline limits. Unknown failures do not establish
absence. Every selected executable import rereads registration and the full REF
closure via M2.

The original known limitations remain: bounded explicit discovery, historical
saved observations, single-provider trust, no complete global index, and no human
screen-reader/developer usability session claimed by automated tests.

**Readiness for debugging integration: NOT YET ACCEPTED.** The library must pass
the independent review and final platform checks first. Preparing this acceptance
PR does not authorize merging it or starting the separate debugging implementation.

## Handoff and outstanding gate

[PR #5](https://github.com/Technique-S/Flip/pull/5) targets remote main and remains
draft and unmerged. Original library branch `codex/flip-m45-circuit-library` remains
at `dec9420`; only the dedicated acceptance branch was updated. Acceptance changes
touch `library.py`, `Library.tsx`, two new acceptance test files and this report's
evidence directory. No dependencies, frozen schemas, historical tests, research
fixtures or reviewer report were changed during this milestone.

The sole missing integration evidence is the completed, published OpenCode review.
When supplied, fetch its exact SHA, verify ancestry and file inventory, inspect its
actual reproductions, address any remaining verified defect with regression tests,
rerun affected checks and update the verdict. Do not mark independent review complete
from the presence of a local branch or uncommitted artifact directories. No main
merge or approval to begin debugging integration is granted by this report.
