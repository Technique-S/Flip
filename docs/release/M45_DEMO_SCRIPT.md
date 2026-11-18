# M4.5-R — reproducible technical demonstration

**Baseline:** `09f2482beae84be6d919ecd6957c4153d1924cca` (accepted main, merge
commit #4). **Duration target:** under three minutes, matching the
recommended demo-video length in the official hackathon guidance.

**Execution status legend used below:**
- `EXECUTED_ON_09f2482` — command was run in this task on the exact baseline;
  raw output is in `fixtures/m5-demo/cli-run/`.
- `REHEARSED_ON_d6a0035` — browser transition was observed on the earlier
  reviewed integration commit and is documented in
  `docs/evidence/m4-independent-review/M4_INDEPENDENT_REVIEW.md`; it was **not**
  re-run on `09f2482` by this task.
- `PLANNED` — capture point or narration only; no execution claimed.

## One-time setup

```sh
uv sync --locked
npm ci --prefix apps/web
npm run build --prefix apps/web
FLIP_LOCAL_SOLVER=1 uv run --frozen python -m flip_api.local --port 8000
```

Open <http://127.0.0.1:8000>. The sample and all comparisons are **historical
local replays** of archived X Layer bytes at block 76206482; they are not live
chain verification and are not deployed onchain.

## Shot list, commands, transitions and narration

| # | Step | Command / UI action | Expected transition and on-screen evidence | Status |
| --- | --- | --- | --- | --- |
| 1 | Launch | command above; open URL | "Flip · Circuit workbench"; Sources page; "Historical sample / Half-adder"; X Layer 196 badge; no wallet prompt | PLANNED capture point |
| 2 | Load sample | CLI: `flip sample half-adder --out project.json`; UI: **Open sample →** | UI moves to Composition, labelled "Historical sample"; project schema `m3-1.0.0`, `projectId=historicalHalfAdder` | CLI `EXECUTED_ON_09f2482`; UI `REHEARSED_ON_d6a0035` |
| 3 | Inspect components | UI: expand component cards; CLI: `cat composition.json` | Two REF sources (`xor` #1, `nand` #2), numbered pins, 2 in / 1 out, 4 and 3 expanded gates, block 76206482 | CLI executed; UI rehearsed |
| 4 | Compose | `flip compose --project project.json --out composition.json` | `COMPOSITION_RESULT`; 81 bytes; netlist hash `0x3dbb65a6…` | `EXECUTED_ON_09f2482` |
| 5 | Truth table | UI: **Half-adder truth table** → **Evaluate four inputs** | `VECTORS_MATCH`, 4 rows: `00→00`, `01→01`, `10→01`, `11→10` (inputs `[A,B]`, outputs `[carry,sum]`) | `REHEARSED_ON_d6a0035` |
| 6 | Introduce mutation | CLI: `flip sample swapped --out mutation.json`; UI: **Swap outputs** | Candidate output order becomes sum, carry; explicit map unchanged | CLI `EXECUTED_ON_09f2482`; UI rehearsed |
| 7 | Wiring Canary | CLI: `flip compare --project mutation.json --out difference.json`; UI: **Wiring Canary → Run comparison** | `DIFFERENT`, solver `SAT`, replayed witness; CLI exit **1** (a result, not a crash) | CLI `EXECUTED_ON_09f2482`; UI rehearsed |
| 8 | Inspect witness | UI: witness table; CLI: read `difference.json` | Input bits `01`; reference outputs `01`; candidate outputs `10`; both mapped pins `≠ Different`; replay `REF_BEAT_REPRODUCED`; minimization HEURISTIC | CLI `EXECUTED_ON_09f2482`; UI rehearsed |
| 9 | Restore | CLI: regenerate `project.json` from step 2; UI: **Restore original** | Candidate returns to carry, sum; outputMap `[0,1]` | CLI executed; UI rehearsed |
| 10 | Equivalent | `flip compare --project project.json --out comparison.json` | `EQUIVALENT`, `UNSAT`, freshness `HISTORICAL`; exit 0 | `EXECUTED_ON_09f2482` |
| 11 | Export | `flip export --project mutation.json --out evidence.json`; UI: **Run and export evidence (JSON)** | `FLIP_EVIDENCE` bundle with `contentHash`, comparison, project, chainObservation; CLI exit 1 for DIFFERENT | `EXECUTED_ON_09f2482`; UI rehearsed |
| 12 | CLI verify | `flip inspect-evidence --bundle evidence.json` then `flip verify-bundle --project mutation.json --bundle evidence.json` | `inspect` exit 0; `verify-bundle` exit 1 with recomputed DIFFERENT and replayed witness; no trust from the serialized flags | `EXECUTED_ON_09f2482` |

Recorded CLI bundle `contentHash` in this run:
`0x3897d1bc5dc9cad8784d0b2ad1efc71d7ffcb13035563f789c2000118cb611e8`.
It is run-dependent (timings and observation context are noncanonical) and must
not be used as a fixed expected value in a regression test.

## Exact CLI command block (copy/paste)

```sh
uv run flip sample half-adder --out project.json
uv run flip compose --project project.json --out composition.json
uv run flip compare --project project.json --out comparison.json
uv run flip sample swapped --out mutation.json
uv run flip compare --project mutation.json --out difference.json
uv run flip export --project mutation.json --out evidence.json
uv run flip inspect-evidence --bundle evidence.json
uv run flip verify-bundle --project mutation.json --bundle evidence.json
```

Raw outputs are preserved under `fixtures/m5-demo/cli-run/`. Expected exit
codes in order: `0, 0, 0, 0, 1, 1, 0, 1`.

## Narration (approx. 150 seconds)

1. "Flip is a local workbench for reusing X Layer circuit definitions and
   checking whether a wiring change preserves behaviour. No wallet is needed."
2. "We open the archived half-adder: XOR #1 and NAND #2 on X Layer mainnet at
   block 76206482. Everything shown is labelled historical; we are not making a
   fresh chain claim and nothing is deployed by this demo."
3. "The composer turns explicit numbered pins into an 81-byte TAP-02 netlist.
   The digest matches the audited fixture."
4. "The four-row truth table shows the declared semantics before we change
   anything."
5. "Now swap the two outputs. This is a syntactically valid netlist — structural
   validity alone cannot tell us behaviour changed."
6. "Wiring Canary returns DIFFERENT, and the evaluator replays input 01: the
   reference emits 01, the candidate 10. Both mapped pins differ. This tells us
   the behaviours differ, not that one circuit is wrong; no intent oracle was
   declared."
7. "Restore the wiring and rerun: UNSAT gives EQUIVALENT under the pinned
   stateless semantics and mapping, with freshness shown separately as
   HISTORICAL."
8. "Export one canonical JSON evidence bundle. The CLI recomputes the proof and
   independently replays the witness — a checksum alone conveys no proof
   authority."

## Capture points

- **S1** Sources page with the "Historical sample" badge and X Layer 196.
- **S2** Composition page showing 81 bytes, 2 REF + 1 NAND, and the truth table.
- **S3** Wiring Canary result with DIFFERENT and the two-column witness table.
- **S4** Repeated comparison showing EQUIVALENT / UNSAT / HISTORICAL.
- **S5** Evidence page with the JSON export control and replay result.
- **V1–V5** Short screen recordings while narrating each corresponding section.
  Mention in the video description that all verdicts are historical local
  replays and that no circuit was published or transaction broadcast.

Keep recordings and screenshots outside the repository unless explicitly
cleared for release; do not commit personal data or credentials.

## Fallback when live RPC is unavailable

The entire 12-step demo works offline. If import or pre-flight is attempted:

1. Skip import and pre-flight; use **Open sample** and the CLI `sample`
   command, which read archived bytes from the checkout.
2. A failed RPC surfaces `RPC_UNAVAILABLE` (CLI exit 4) or an `UNKNOWN`
   pre-flight with `freshness: UNVERIFIED`; say "no current chain observation
   was made" rather than presenting cached data as current.
3. Do not configure a live endpoint ad hoc during the recording. Never use a
   wallet, signing key or write method as a workaround.

## Honesty labels to keep on screen

- "Historical sample · block 76206482 · X Layer 196"
- "EQUIVALENT — pairwise stateless behaviour under the pinned mapping; not a
  correctness or security claim"
- "DIFFERENT — a replayed behavioural difference; which behaviour is intended
  is unknown without a trusted oracle"
- "UNKNOWN — inconclusive, never equivalent"
- "HISTORICAL — reproducible but not chain-current"
- "STRUCTURALLY ACCEPTED — read-only structural stage only; no transaction was
  broadcast and nothing was published"
