# M4.5-2D-V — Independent connection debugger review

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).

| Role | Exact SHA |
|---|---|
| Accepted main baseline | `1136b187bd68328cea4975caea50904ccece08fd` |
| Initially reviewed debugger SHA | `b9d3fc3f87d34cc6bd46e2a716504fe113f44f48` |
| **Final PR #7 head tested** | **`130dd341b622cc0ad68bffe7f6f37bb847de45c8`** |

The newer acceptance delta (`518bace`, `130dd34`) added only
`apps/web/tests/debugging-acceptance.spec.ts` and
`packages/flip-core/tests/test_m45_debugging_adversarial.py` (408 insertions). **No
production source, schema or frontend implementation changed after `b9d3fc3`.** All
checks below were re-run on the final PR head. CI runs `44555079596` (`b9d3fc3`) and
`44566684643` / `44566667973` (`130dd34`) are recorded as `success`; PR #7 remains open
and unmerged.

**Recommendation: PASS.** No blocking finding. No forged correction or fabricated causal
certainty was produced, and every adversarial path failed closed.

## 1. Commands executed

From `C:\Users\Kazi\Documents\Flip\repo` (CPython 3.14.6, Node 24.18.0):

```powershell
# shipped historical example through the real CLI
$env:FLIP_LOCAL_SOLVER=1
.venv\Scripts\flip.exe debug --request docs/schema/m45-debugging/examples/swapped-prior.request.json --out ...

# independent harnesses (OpenCode-owned; real production CLI/API)
.venv\Scripts\python.exe fixtures/m45-debugging-independent-review/harness/independent_debug_checks.py
.venv\Scripts\python.exe fixtures/m45-debugging-independent-review/harness/production_case_matrix.py
.venv\Scripts\python.exe fixtures/m45-debugging-independent-review/harness/trust_attacks.py
.venv\Scripts\python.exe fixtures/m45-debugging-independent-review/harness/debug_parity.py
cd apps/web; npm run build; npm test -- --reporter=list
cd ..; .venv\Scripts\python.exe -m pytest -q --junitxml=... -o junit_family=legacy
.venv\Scripts\python.exe scripts/check_m1_repository.py
```

All raw outputs, request/result JSON, logs and the manifest are in
`docs/evidence/m45-debugging-independent-review/results/` and registered in
`MANIFEST.json`.

## 2. Task A — production execution

The shipped `swapped-prior` example (historical, pinned at block 76206482) produced:

| Field | Observed |
|---|---|
| CLI exit | 1 (DIFFERENT) |
| classification / attribution | `VERIFIED_DIFFERENCE` / `AMBIGUOUS_MULTIPLE_CAUSES` |
| `uniqueFaultClaim` | `false` |
| witness | input `01`; reference `01`; candidate `10`; `REF_BEAT_REPRODUCED` |
| differing output bits | `[0, 1]` |
| connections | 56, all `RELEVANT_CONNECTION`; nested paths `top/ref[0]`, `top/ref[2]` |
| candidate action | 1 `CANDIDATE_ACTION` restoring the declared prior output maps |

**Independent, non-production oracle.** `independent_debug_checks.py` re-derived both
truth tables from the exact pinned netlist bytes using the OpenCode M4.5-2D stdlib
evaluator (`debug_core.CORE_VERSION`), which does not import any production module. At
witness `01` it independently computed reference `01` / candidate `10` and differing bits
`[0,1]` — matching the production result. It also validated each production
`connectionRef` against the independently compiled 81-byte netlist and confirmed nested
connections carry bound source identities. **Result: 8/8 checks passed** (independent
witness replay, path membership, relevance-not-fault labels, zero attribution for an
equivalent rewiring, and a genuine verified-correction replay).

The genuine correction replay returned `VERIFIED_CORRECTION` with
`scope = EXACT_STATELESS_SELECTED_REFERENCE_HISTORICAL`,
`revalidation = PINNED_IDENTITIES_HASHES_AND_CLOSURE_REPLAYED`, and an actionId binding
the original and revised request hashes. This is a *newly verified correction relative to
the declared synthetic reference over pinned historical snapshots* — not a claim about
current chain state or absolute intent.

The original 10-case debugging corpus and eight guidance examples were mapped onto real
production debug requests: `production_case_matrix.py` **16/16 passed**, covering all ten
categories (swapped outputs, REF input order, duplicate fan-out, unbound pin, output
ordering, multiple edits, nested/substituted dependency, equivalent rewiring, several
contributing connections, indistinguishable causes) plus changed project hash, stale
manifest, forged correction field, fabricated paths, reused action from another project,
resource exhaustion and depth cap. Structural rewrites that violated the frozen contract
were rejected at parse time (exit 3, no result file) rather than producing a diagnosis.

## 3. Task B — diagnostic trust attacks

`trust_attacks.py` (**3/3 passed**) additionally attempted: a forged witness injected into
the request, a changed candidate circuit identity, and a duplicated/substituted dependency
closure. All failed closed (exit 2/3, no `VERIFIED_DIFFERENCE`, no connections, no
correction). The `DebugRequest` schema has no witness field at all, so a caller cannot
supply one; the engine recomputes the witness from the trusted comparator every time.

Key trust properties confirmed in source and behavior:

- `uniqueFaultClaim` is a literal `False` in the result contract.
- `ConeTracer` emits only `RELEVANT_CONNECTION`; relevance is never causation.
- `verify-correction` requires the server-derived `actionId`, recompiles both original
  and revision through the M2 resolver, and re-runs the full comparison; a false
  classification flag in the request is rejected by `extra="forbid"` validation.
- Reused action IDs from another project hash return `UNKNOWN / INVALID_INPUT`.
- Reorg/stale/manifest substitution cannot produce trusted output; `revalidation` is
  explicitly `PINNED_SNAPSHOT_ONLY_NOT_LIVE`.

## 4. Task C — browser and CLI

`npm run build` then `npm test`: **21/21 Chromium tests passed**, including three debugger
journeys that execute the required ten interaction beats: load sample → wiring mutation →
compare → inspect relevant connections → select candidate correction → preview/verify the
separate revision → apply locally → confirm no-fault attribution on the applied version →
revert → return to DIFFERENT. The tests also assert keyboard-only inspection (focus +
Enter), axe WCAG 2.1 AA on the debugger region, a non-color `.different` marker with text
"differs at output N", 390px viewport with no horizontal overflow, `reducedMotion: reduce`,
a forced `maxNodes=1` producing `UNKNOWN / RESOURCE_LIMIT` with zero connections and no
apply button, and discarding an in-flight result when the project mapping changes during
async verification.

CLI/API parity (`debug_parity.py`): **passed** for diagnose (DIFFERENT), no-fault
(EQUIVALENT) and UNKNOWN cases — identical `classification`, `attribution`,
`differingOutputBits`, `semanticHash` and all binding hashes across the real CLI
subprocess and `POST /api/v1/debug`; solver-disabled API returned 501. The browser test
also byte-compared the downloaded diagnostic JSON with CLI stdout.

## 5. Claim integrity and freshness

- A **verified behavioral difference** is the replayed witness under the trusted evaluator.
- **Structural cone membership** is relevance only; the result says so explicitly.
- A **candidate correction** is the declared prior numeric mapping revision, never a proof.
- A **newly verified correction** required a fresh full EQUIVALENT comparison on a separate
  request over pinned snapshots and is scoped to that exact reference.
- All imported circuits retain `HISTORICAL` freshness; no diagnostic promotes anything to
  CURRENT. No RPC, wallet, signing, transaction or publication exists in the debugger.

## 6. Findings

| Severity | Finding |
|---|---|
| CRITICAL | none |
| HIGH | none |
| MEDIUM | none |
| LOW | none |
| INFORMATIONAL | An initial full-suite run failed one custody test because Windows `core.autocrlf=true` converted previously merged library-review evidence to CRLF against pinned LF blobs — a checkout artifact, not a debugger defect. After restoring pinned LF bytes, the custody guard returned `PASS` and the full suite passed **601 tests, zero failures**. CI on Linux/Windows recorded success. |
| INFORMATIONAL | The 10-case corpus categories are synthetic variants mapped onto the shipped historical execution; they do not represent additional onchain circuits. |

## 7. Skipped / environment-limited

- Linux execution was not performed locally; CI success for both platforms is recorded
  from the GitHub API, not independently re-executed here.
- Human screen-reader and first-time-developer usability sessions were not performed;
  automated axe checks are not a substitute.
- Live revalidation, publication and any chain write are out of scope and were not run.

## 8. Acceptance recommendation

**PASS** for PR #7 at `130dd341b622cc0ad68bffe7f6f37bb847de45c8`. The production debugger
correctly separates verified behavioral difference, structural relevance, candidate action
and newly verified correction; all adversarial trust attempts failed closed; CLI/API and
browser behavior are semantically equivalent; and no production change occurred after the
initially reviewed SHA beyond tests. Do not merge from this review branch.
