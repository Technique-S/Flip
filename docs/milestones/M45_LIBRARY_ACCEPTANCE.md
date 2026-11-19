# M4.5-2L-C Circuit Library acceptance

Assessment date: 2026-11-19. **Integration verdict: FAIL — pending independent
OpenCode evidence and final acceptance checks.** This is a gate status, not a claim
that the focused tests failed. This report is updated as checks finish.

## Exact starting state and provenance

- Accepted remote main: `09f2482beae84be6d919ecd6957c4153d1924cca`.
- Original library head: `dec9420bb76e9245c6740bf3d92031d175e408ec`, locally clean
  and equal to its origin ref before acceptance work.
- Research: `5c7bcfbc8babb58d5f040fe869e2017f4a8c46fd`, preserved as the second
  parent of library merge `9867dcb`; its first parent is accepted M4.
- Acceptance branch: `codex/flip-m45-library-acceptance`.
- First corrections commit: `72278a15e2cd7c6aefc4bf00c57253cf094d01f9`.
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

No review commit has been supplied or fetched yet. **Independent review is pending.**
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
Composition continues to consume only a fresh complete M2 import, never a saved
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
| Complete inherited production suite and additional tests | RUNNING |
| Complete browser regression suite | RUNNING |
| Ubuntu/Windows CI on acceptance head | PENDING |
| Independent Keccak selectors | PASS — 11 research signatures |
| Fixture hashes | PASS — 19 registered files / 12 synthetic scenarios |
| M1/M2/M3/library schema drift | PASS |
| Python/Node canonical hash parity | PASS — six vectors |
| Frontend lint/build; Python lint/format | PASS |
| Final custody/credential scan | PENDING |
| Separate live read-only smoke | PENDING |

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
