# M4.5-2L — Acceptance matrix for a future implementation

**Status:** specification for Codex. These integration tests are **not implemented or
executed in this research task**. The mocked cases they reference are deterministic and
manifest-verified; passing them will not by itself establish current chain truth.

## Classification legend

| Label | Meaning |
|---|---|
| **SOURCE_OBSERVED** | Established by source code, verified evidence or the bounded live read in `PROTOCOL_DISCOVERY.md` |
| **DOCUMENTED_EXPECTED** | Required by TAP-10/TAP-02 or by the engineering plan; not executed end to end here |
| **UNEXECUTED_SPEC** | Proposed test for Codex to implement and run against doubles |
| **FIXTURE_VERIFIED** | The referenced fixture file passed `verify_fixtures.py` in this task |

Every row below is `UNEXECUTED_SPEC` for the *implementation* unless noted; the fixture
column records which synthetic case supplies the inputs.

## A. Protocol preconditions (observed or documented, not implementation tests)

| ID | Behavior | Basis | Classification |
|---|---|---|---|
| AC-P01 | Factory exposes `cpuCount`, `cpuAt`, `isCPU`; Flip implements only `isCPU` | TAP-10 Appendix A; `abi.py`; live read | SOURCE_OBSERVED |
| AC-P02 | Processor numbers are append-only and never reused; no reverse table | TAP-10 §1, §4.3 | DOCUMENTED_EXPECTED |
| AC-P03 | `nextId` is an exclusive upper bound; `ownerOf` reverts for a missing token | `importer.py`; TAP-10 §4.2; live `ownerOf(1)` | SOURCE_OBSERVED |
| AC-P04 | No authoritative factory registration event is specified; `eth_getLogs` may be unavailable | TAP-10 §11; live availability probe | SOURCE_OBSERVED + UNKNOWN |
| AC-P05 | Factory/beacon/processor implementations are mutable; proxy bytecode is insufficient | live impl/beacon hashes; `isSealed=0` | SOURCE_OBSERVED |
| AC-P06 | `name()` is display-only and must not be used for identity | TAP-10 §4.2 | DOCUMENTED_EXPECTED |

## B. Integration tests for Codex (unexecuted specifications)

| ID | Behavior | Given / When / Then | Fixture | Fixture status |
|---|---|---|---|---|
| AC-01 | Successful processor discovery | Given cpuCount=3 and three `cpuAt` responses; when discovery runs at a pinned block; then three `ProcessorRecord`s with indices 0,1,2 and `discoveryStatus=COMPLETE` | C01 | FIXTURE_VERIFIED |
| AC-02 | Processor search | Given a three-processor catalog; when the user searches one processor address; then exactly one record is returned with its provenance label | C01 | FIXTURE_VERIFIED |
| AC-03 | Successful circuit enumeration and search | Given nextId=5 and four valid circuits; when search filters by `(processor, circuitId)`; then the matching interface metadata is returned and ID 0 is absent | C02 | FIXTURE_VERIFIED |
| AC-04 | Interface metadata honesty | Given a stateful circuit (`nState=1`); when it is displayed; then it is labeled stateful and never offered for stateless-equivalence composition | C02 | FIXTURE_VERIFIED |
| AC-05 | Missing / noncontiguous IDs | Given reverts at IDs 3 and 6 below nextId; when a bounded scan completes; then existing IDs are 1,2,4,5,7 and status is `COMPLETE_WITH_GAPS`, not an error | C03 | FIXTURE_VERIFIED |
| AC-06 | Bounded pagination | Given cpuCount=7 and nextId=200; when page size and caps apply; then three pages are emitted, status is `PARTIAL_BOUNDED`, and no uncapped scan occurs | C04 | FIXTURE_VERIFIED |
| AC-07 | Outage | Given an `eth_call` timeout mid-scan; when discovery runs; then status is `UNKNOWN`, the prior snapshot is retained, and favorites/recents are unchanged | C05 | FIXTURE_VERIFIED |
| AC-08 | Rate limit | Given two HTTP 429 responses; when bounded backoff applies; then the scan completes, throttle events are counted, and calls stay within budget | C06 | FIXTURE_VERIFIED |
| AC-09 | Changed factory implementation | Given a new factory implementation/code hash at the next block; when refresh runs; then existing records become `STALE`, favorites remain user data, and composition is blocked | C07 | FIXTURE_VERIFIED |
| AC-10 | Changed processor implementation | Given identical proxy bytecode but a changed beacon implementation code hash; when refresh runs; then cached netlists are not accepted as current and composition is blocked | C08 | FIXTURE_VERIFIED |
| AC-11 | Chain reorganization | Given a different canonical block hash at the same height; when refresh checks block identity; then the snapshot is invalidated, records are `REORGED`, and a rescan starts from the canonical block | C09 | FIXTURE_VERIFIED |
| AC-12 | Duplicate records | Given the same identity from enumeration, seed and user import (mixed address case); when the catalog merges; then one canonical record exists with provenance sources ordered by authority | C10 | FIXTURE_VERIFIED |
| AC-13 | Favorite survives stale snapshot | Given a favorite whose environment hash changed; when the user opens it; then `USER_FAVORITE_ONLY` and `STALE` are shown, composition is blocked, and revalidation is required | C11 | FIXTURE_VERIFIED |
| AC-14 | Favorite is not authority | Given a favorite with an injected `transactionAuthority` field; when the overlay is loaded; then the field is dropped and no permission is granted | C11, C12 | FIXTURE_VERIFIED |
| AC-15 | Recents | Given a successful import; when it is recorded; then a bounded recent entry stores identity and snapshot digest; exceeding the cap evicts the oldest recent, never a favorite | design §5.4/§9 | UNEXECUTED_SPEC |
| AC-16 | Import then revalidate | Given a discovered entry; when the trusted importer revalidates it at a fresh pinned block and the environment matches; then it becomes executable and its netlist hash/closure are bound to the manifest | design §7 | UNEXECUTED_SPEC |
| AC-17 | Revalidation failure | Given a changed netlist hash or beacon hash; when revalidation runs; then status is `VERIFICATION_FAILED` or `STALE` and no EQUIVALENT claim is produced | C07, C08 | FIXTURE_VERIFIED |
| AC-18 | Untrusted metadata rendering | Given HTML, a bidi control and authority-looking text in labels; when the UI renders and indexes them; then output is escaped plain text, controls are visible/removed, and identity is unchanged | C12 | FIXTURE_VERIFIED |
| AC-19 | Wrong chain | Given a response with chainId 8453 while 196 is required; when discovery starts; then it stops with `WRONG_CHAIN` before any catalog write | design §6 | UNEXECUTED_SPEC |
| AC-20 | Freshness labeling | Given an offline session; when the user searches; then results are shown with a clear non-current freshness label and no claim of live verification | design §7 | UNEXECUTED_SPEC |
| AC-21 | Known-address fallback | Given enumeration unavailable; when the catalog loads; then it shows verified seeds + user imports with `INCOMPLETE`/`UNKNOWN` freshness and never presents them as fresh chain truth | seeds file | FIXTURE_VERIFIED |
| AC-22 | Selector provenance | Given the 11 signatures in the selector proof; when a build checks selectors; then all recomputed selectors match the registered values | keccak self-test | FIXTURE_VERIFIED |
| AC-23 | Credential hygiene | Given any catalog export; when it is scanned; then no API keys, wallet secrets, active approvals or unbroadcast signed payloads are present | design §8/§9 | UNEXECUTED_SPEC |
| AC-24 | Live read-only acceptance | Given a real endpoint; when a bounded snapshot is captured; then chainId, block number/hash, provider trust, ABI provenance and code identities are recorded; no signing or broadcast occurs | live observation format | SOURCE_OBSERVED (capture method only) |

## C. Coverage of required acceptance topics

| Required topic | Covered by |
|---|---|
| Successful search | AC-02, AC-03, AC-20 |
| Import | AC-16, AC-21 |
| Revalidation | AC-16, AC-17, AC-10 |
| Favorites | AC-13, AC-14, AC-15 |
| Recents | AC-15 |
| Stale records | AC-09, AC-10, AC-13, AC-17 |
| Bounded discovery failures | AC-05, AC-06, AC-07, AC-08, AC-11, AC-19 |
| Metadata safety | AC-14, AC-18, AC-23 |
| Verified identities / provenance | AC-01, AC-12, AC-22, AC-24 |

## D. Execution limits of this research task

- No production interface existed to exercise, so rows AC-01–AC-23 remain unexecuted specifications.
- The 12 synthetic cases were generated deterministically and passed the manifest verifier;
  they are inputs for future tests, not evidence that the tests pass.
- The live capture (AC-24 method) is a single-provider, single-block observation. A passing
  fixture or a successful capture must not be relabeled as current chain truth or publication.
- Timeout, resource-limit or unavailable-provider outcomes must remain `UNKNOWN`; this
  research does not weaken that rule to force a pass.
