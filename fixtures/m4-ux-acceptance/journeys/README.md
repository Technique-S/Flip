# Golden user journeys — M4-B

Machine source: [`JOURNEYS.json`](JOURNEYS.json). Each entry defines initial state,
user action, expected response, trust/freshness classification, failure handling,
accessibility considerations and reproducible test input. This README is the
human-readable index; the JSON is authoritative.

The journeys follow the PRD's linear flow **Start → Import → Compose → Compare →
Evidence / Pre-flight** and deliberately keep the two trust axes separate:
verdict (`EQUIVALENT` / `DIFFERENT` / `UNKNOWN`) and freshness (`CURRENT` /
`HISTORICAL` / `STALE` / `UNVERIFIED`).

| ID | Scenario | Expected headline result | Trust / freshness | Execution status |
| --- | --- | --- | --- | --- |
| J01 | First-time sample walkthrough | DIFFERENT (witness) → EQUIVALENT after fix | HISTORICAL / pinned fixture | PARTIAL (web spec only) |
| J02 | Live X Layer import | Snapshot, REF closure, numbered pins, manifest | CURRENT only for fresh RPC; SINGLE_RPC | PARTIAL (local double) |
| J03 | Offline/historical selection | Normal verdict, HISTORICAL badge | HISTORICAL, never promoted | EXECUTED_CLI |
| J04 | Two-circuit composition | Deterministic 81-byte netlist, explicit map | Inherits source freshness | EXECUTED_CLI |
| J05 | Deterministic half-adder | 100/100 identical, audited digest | Determinism ≠ correctness | EXECUTED_CLI |
| J06 | Equivalent refactor | EQUIVALENT, UNSAT, scope qualified | EQUIVALENT under model; HISTORICAL | EXECUTED_CLI |
| J07 | Differing wiring | DIFFERENT + replayed witness | Not "user is wrong" | EXECUTED_CLI |
| J08 | Timeout | UNKNOWN / SOLVER_TIMEOUT | Inconclusive, never EQUIVALENT | EXECUTED_CLI |
| J09 | Changed dependency | STALE; old report retained | STALE, not CURRENT | PARTIAL (local double) |
| J10 | Failed RPC import | RPC_UNAVAILABLE, retry offered | Infrastructure, no verdict | EXECUTED_CLI |
| J11 | Invalid pin mapping | INVALID_INPUT before SAT | Invalid input, no verdict | EXECUTED_CLI |
| J12 | Evidence export/re-import | Recompute valid claim; reject forged ones | HISTORICAL; recomputation ≠ certificate | PARTIAL (export reserved) |
| J13 | Read-only pre-flight | ACCEPTED / REJECTED / UNKNOWN only | Separate trust axis; no publication | SPEC_ONLY |

## Cross-cutting rules for every journey

1. **Never equate a timeout or resource ceiling with a verdict.** J08 is the
   canonical example; the failure handling section of each journey repeats it.
2. **A difference is not a judgement.** J07 states that a detected difference
   does not imply the user's circuit is wrong without a trusted oracle.
3. **Freshness is orthogonal.** J03, J09 and J12 show that a historically
   reproducible report can remain reviewable while being explicitly not current.
4. **No privileged operations.** No journey contains wallet connection, key
   access, signing, fee payment, broadcast or publication. J13 is read-only.
5. **Accessibility is part of acceptance.** Every journey names text-based
   statuses, labelled controls, focus behaviour and error announcements.

## Provenance of execution claims

- `EXECUTED_CLI`: reproduced on the accepted M3 integration commit
  `af8ba1f109a2a1c59fe36be044bc025a127ea025` with the pinned uv lockfile; see
  `../cli-cases/CLI_ACCEPTANCE.md` and the executed transcript.
- `PARTIAL`: the CLI portion was executed; the web or planned-M4 portion is a
  specification because no M4 web application, export ZIP or live RPC is part
  of this branch.
- `SPEC_ONLY`: no execution is claimed. J13's command demonstrably returns
  `NOT_IMPLEMENTED` (exit 6) on the baseline.
