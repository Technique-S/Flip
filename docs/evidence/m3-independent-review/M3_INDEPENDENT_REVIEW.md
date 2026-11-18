# Flip M3-C — independent proof soundness review

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).
**Branch:** `opencode/flip-m3-independent-review`.
**Allowed write paths only:** `docs/evidence/m3-independent-review/`,
`fixtures/m3-independent-review/`. No production module, frozen schema, existing
fixture, lockfile, CI config or agent branch was modified. No merge, no wallet,
no RPC write, no onchain publication.

## 1. Exact target reviewed

- **Primary reviewed commit:** `59751e20590117f0cbc4ef41b9b30d836e533f84`
  (`codex/flip-m3-integration`, "merge: preserve independent M3-B verification
  corpus"). Worktree was clean at review time.
- **Fallback commit recorded in the task:** `d4adf809f2576a1e14e64adce0b04c914049a50f`
  (`codex/flip-m3-composition-canary`) was inspected first and is an ancestor of
  the primary commit.
- **Availability note:** at initial check `codex/flip-m3-integration` had no
  remote ref on `origin`; it became available as a local, clean, recorded commit
  in the shared workspace. Per the task, the integration branch was then
  reviewed instead of relying on the earlier fallback findings.
- **Final diff inspected:** `git diff d4adf809..59751e2 --stat` adds exactly the
  18 M3-B fixture/evidence files and changes no production source.

## 2. Commands executed

Environment: CPython 3.14.6, uv 0.9.11, locked dependencies installed to a
venv **outside the repository** (`C:\Users\Kazi\AppData\Local\Temp\opencode\m3c-venv`),
`PYTHONPATH` pinned to the reviewed worktree's three `src` directories. Windows
`win32`, native Minisat22 via `python-sat 1.9.dev23`.

```powershell
# baseline (from the review worktree)
python -m pytest packages/flip-core/tests/test_m3_engine.py `
  packages/flip-core/tests/test_m3_benchmarks.py -q --tb=short

python fixtures/m3-independent-review/review_sat.py
python fixtures/m3-independent-review/review_make_requests.py
python fixtures/m3-independent-review/review_consumer.py
python fixtures/m3-independent-review/review_identity.py
python fixtures/m3-independent-review/review_solver.py
python fixtures/m3-independent-review/review_parity.py
python fixtures/m3-independent-review/review_api_extras.py
python fixtures/m3-independent-review/review_corpus.py
powershell fixtures/m3-independent-review/termination_check.ps1

# real CLI surface (examples)
python -m flip_cli compare --project fixtures/m3-independent-review/requests/valid_different.json
python -m flip_cli consume --project fixtures/m3-independent-review/requests/forged_equivalent_consume.json
```

## 3. Fixtures tested

- Accepted offline half-adder request from `scripts/make_m3_sample.py`, built
  from M2 live-import captures for `0x839BDD6f…#1` (XOR) and `…#2` (NAND).
- Generated request files under `fixtures/m3-independent-review/requests/`
  (valid equivalent, valid different, valid consume, forged-equivalent consume,
  frozen v1 report, invalid proof shape).
- Mutant designs: self-equivalence, output permutation, commutative REF inputs,
  wrong glue wiring, triple output, output-map permutation, input-map reversal.
- OpenCode M3-B corpus as integrated: 10 golden compositions, 17 SAT cases,
  8 witnesses, 12 proof-integrity attacks, 7 benchmark sizes.
- Independent oracles: `independent_core.py` (OpenCode M3-B, own reimplementation)
  and `tap02_reference_official.py` (archived TAP-02 reference, MIT), both run
  against the exact production netlist bytes and resolved REF children.

## 4. Results

### Baseline
`86 passed in 40.43s` for the two M3 core test modules.

### Task A — trusted proof consumer
- Genuine EQUIVALENT and DIFFERENT reports were accepted by `execute("consume")`.
- **11/11 hostile report attacks were safely rejected**: forged EQUIVALENT from
  a DIFFERENT run, empty self-declared maps, false CURRENT freshness, swapped
  reference hash, project-hash mismatch, replaced candidate identity (`IMPLEMENTATION_CHANGED`),
  altered netlist hash (`IMPLEMENTATION_CHANGED`), non-differing witness
  (schema rejection), wrong-input witness (`WITNESS_REPLAY_FAILED`),
  unverified source flags, and a proof transplanted from another project.
- **4/4 identity attacks against `compare` were rejected**: substituted netlist
  bytes under a pinned identity, altered manifest `netlistHash`, altered source
  processor, altered source `manifestHash`.
- Evidence: `consumer-attacks.json`, `identity-attacks.json`.

### Task B — SAT soundness
- **7/7 production verdicts matched the independent exhaustive oracle** and the
  official evaluator agreed bit-for-bit on every enumerated input.
- Both DIFFERENT cases had their witnesses replayed by both independent
  evaluators (`differs: true`, outputs matching production).
- EQUIVALENT cases returned production `UNSAT`; an independent miter confirmed
  UNSAT for the positionally comparable cases (self, commutative inputs, triple
  output, input-map reversal). For the mapped output-permutation case the
  positional independent miter is not applicable; the full-domain oracle with
  the declared `outputMap` is the authority and agreed with production.
- Evidence: `sat-soundness.json`.

### Task C — solver failure behavior
- Forced 1 ms timeout → `UNKNOWN` (`SOLVER_TIMEOUT`); 1 MiB memory cap →
  `UNKNOWN`; incomplete imports, gate-cap overflow, wrong REF arity → contract
  rejection; worker `timeout-probe` and `crash-probe` → `INTERRUPTED`;
  `memory-probe` → `MEMORY_BLOCKED`; malformed worker payload → `INTERRUPTED`.
- **No unresolved execution produced an EQUIVALENT verdict.**
- Worker termination: 0 workers before, 0 immediately after, 0 after 2 s,
  0 persisting (Windows Job containment).
- Evidence: `solver-failures.json`, `worker-termination.json`,
  `termination_check.ps1`.

### Task D — CLI / API trust parity
- CLI exit codes: EQUIVALENT → 0, DIFFERENT → 1, invalid/forged consume → 3.
- API statuses: valid compare/consume → 200; forged consume and invalid shape →
  422; frozen v1 report → 501; compare without `FLIP_LOCAL_SOLVER=1` → 501.
- After removing volatile telemetry (`verifiedAt`, `totalMs`, `wallMs`,
  `peakBytes`), CLI and API canonical results matched for both EQUIVALENT and
  DIFFERENT.
- Caller-injected top-level verdict fields were rejected (422). Freshness was
  `HISTORICAL` in all conclusive reports, never `CURRENT`.
- Vectors endpoint returned `VECTORS_MATCH` with `solver.outcome = NOT_RUN` and
  never an equivalence verdict.
- Evidence: `cli-api-parity.json`, `api-gate-and-vectors.json`.

### Task E — integrated corpus
- All **18 M3-B files are byte-identical** (Git blob IDs) between
  `4822a051…` and `59751e2…`: `all_blobs_identical: true`, no differing files.
- Counts unchanged: 10 golden compositions, 17 SAT cases, 8 witnesses,
  12 proof-integrity attacks (all still `SPEC_ONLY`), 7 benchmark sizes.
- Expected-result fields retained; explicit "No synthetic circuit was deployed
  on X Layer" denial retained; no affirmative live/production claim phrases.
- Evidence: `corpus-integration.json`.

## 5. Reproduced defects and severity classification

| Severity | Defects reproduced |
|---|---|
| CRITICAL | **None.** No false EQUIVALENT and no forged-proof acceptance was found. |
| HIGH | None. |
| MEDIUM | None. |
| LOW | None in reviewed production code. |
| INFORMATIONAL | See limitations below. |

The following were initially flagged during harness development and were proven
to be **harness expectation errors, not product defects**: (a) a no-op netlist
swap (each import holds one circuit), corrected to a real substitution which was
rejected; (b) a "forged" consume built from an already-EQUIVALENT result,
corrected to a DIFFERENT-derived forgery which was rejected; (c) a canonical
comparison that included volatile timing/peak-memory telemetry, corrected by
normalising those fields; (d) `refDepthCap=1` returning EQUIVALENT — legal,
because the minimum cap still permits one REF level and the imported sources
are flat NAND.

## 6. Trust-boundary analysis

- **Untrusted input → conclusive verdict:** the engine recompiles from the
  pinned request, re-derives both manifests, re-runs the native solver, applies
  the maps itself, and replays any DIFFERENT witness with the local evaluator.
  Serialized verdict/status fields are never promoted. `consume()` additionally
  recomputes UNSAT cases and compares all frozen report fields plus source,
  implementation and engine hashes.
- **Identity:** source identity, widths, manifest hash, closure/edges,
  netlist bytes vs declared hash, processor environment and factory/beacon
  context are checked against imported M2 evidence before composition.
- **Solver:** a separate `-I` process with a strict output schema (outcome,
  peak memory and metric, minimization bound, witness shape) runs under a
  Windows Job object; invalid output, crash, timeout or over-budget input fails
  closed to `INTERRUPTED`/`UNKNOWN`.
- **Freshness:** reports are explicitly `HISTORICAL` or `STALE`, with context
  `LOCAL_OFFLINE_REPLAY_SINGLE_RPC_ASSERTIONS_NOT_REVALIDATED`. No chain-current
  claim is reachable through M3.
- **Interface parity:** both surfaces call the same core operation; the API
  additionally requires loopback plus an explicit local-solver opt-in for
  compare/consume.

## 7. Remaining uncertainties

1. **Custody:** `codex/flip-m3-integration` was not present on `origin` at review
   time; this review is against the local recorded commit `59751e2…`. Re-review
   is required if the pushed integration commit differs.
2. **Linux containment not executed:** Windows `WINDOWS_JOB_COMMIT` was
   exercised; Linux `RLIMIT_AS`/`PR_SET_PDEATHSIG`/`killpg` was static review
   only. RLIMIT_AS is per-process and inherited by children; no cgroup-level
   memory ceiling was observed in code. This is a **deployment risk**, distinct
   from local CLI safety on Windows.
3. **Deep/nested REF overflow not exercised:** available accepted imports are
   flat 3–4 NAND circuits with one REF level. A nested-REF fixture is needed to
   test depth-cap rejection end to end.
4. **Zero-input circuits not expressible:** `PinSource` requires `pin < nIn` and
   no `nIn=0` source exists in the accepted imports, so M3-B's zero-input cases
   cannot be driven through the production project schema.
5. **Multi-output REF inlining** was exercised only via locally composed
   multiple outputs, not via an imported source with `nOut > 1`.
6. EQUIVALENT confirmation is exact only for the enumerated small domains and
   completed UNSAT miters tested here; large benchmark sizes were not
   re-proved by this review.

## 8. M3 acceptance recommendation

**Recommendation: M3 PASS (bounded), with the uncertainties above retained as
explicit gates.** No critical false-equivalence or forged-proof acceptance was
reproduced, so the task's FAIL trigger does not apply. The proof consumer,
identity/manifest binding, miter construction, witness replay, fail-closed
solver behavior, CLI/API parity and M3-B corpus preservation all held under the
executed adversarial checks. Recommendation is limited to this reviewed commit
and to local/offline operation; public deployment still requires separate
Linux containment measurement and freshness revalidation gates.

**End of M3-C independent review. No merge into `main`.**
