# Flip M4 — independent web, CLI and accessibility review

**Role:** independent supporting verification engineer (OpenCode / HY4 Flash).
**Branch:** `opencode/flip-m4-independent-review`. **No production change, no merge.**

## 0. Reviewed commits and scope

| Role | Commit | Notes |
| --- | --- | --- |
| Fallback target (available first) | `f4d5b3a981d4cd5906c3ab11942c106f5becc7a9` | `codex/flip-m4-product-workflow` |
| Integration target (appeared during review) | `d6a00352edac93f930184d58605a646f021e1023` | `codex/flip-m4-integration`; final delta review below |
| M3 merge on `main` | `0bd006336d9ab710706e1e11aa0533636d7fae1e` | PR #3 merged; PR #3 state now `closed/merged` |
| M3 reviewed baseline | `af8ba1f109a2a1c59fe36be044bc025a127ea025` | inherited corpus origin |

`codex/flip-m4-integration` did not exist when the review began; the fallback
target was used first, then the exact integrated commit was rebuilt in a
temporary worktree and re-tested. All tested SHAs are recorded above and in
`case-parity.json`.

Write scope was limited to `fixtures/m4-independent-review/` and
`docs/evidence/m4-independent-review/`. No production package, frontend source,
frozen schema, dependency lock, CI file, existing fixture byte or Codex branch
was modified.

## 1. Commands actually executed

```sh
# fallback target (f4d5b3a), repository root
uv sync --locked
npm ci --prefix apps/web
npm run build --prefix apps/web
FLIP_LOCAL_SOLVER=1 uv run --frozen python -m flip_api.local --port 8000
uv run --frozen python -m flip_api.local --port 8001          # no solver opt-in
uv run --frozen python fixtures/m4-independent-review/generators/run_review_cases.py
uv run --frozen python fixtures/m4-independent-review/generators/run_trust_probes.py
uv run --frozen pytest -q packages/flip-core/tests/test_m4_workflow.py -k "preflight or burn"

# integration target (d6a0035), temporary detached worktree
uv sync --locked
npm ci --prefix apps/web
npm run build --prefix apps/web
FLIP_LOCAL_SOLVER=1 uv run --frozen python -m flip_api.local --port 8002
M4C_FLIP=<integration-worktree>/.venv/Scripts/flip.exe \
M4C_EXEC_DIR=docs/evidence/m4-independent-review/executed-integration \
uv run --frozen python fixtures/m4-independent-review/generators/run_review_cases.py
```

Runtime: CPython 3.14.6, uv 0.9.11, Node 24.18.0, Chromium driven through the
harness browser session. Browser interactions used the real built React app on
loopback, not a mock.

## 2. Task A — real browser acceptance

Executed against the running application at `127.0.0.1:8000` (f4d5b3a) and
`127.0.0.1:8002` (d6a0035):

- **Historical sample journey:** opened the sample from Sources; live Sources,
  Composition, Wiring Canary and Evidence pages rendered; identity, block
  76206482, 2 in/1 out, 4/3 gates and numbered pins were visible.
- **Composition mapping:** numbered source selects with `aria-label="Source for
  <target>"`, component tables with captions, external inputs, NAND glue and
  final outputs were inspected and focused.
- **Wiring mutation:** **Swap outputs** then **Run comparison** produced
  `DIFFERENT`, UNSAT/SAT text `SAT`, `HISTORICAL` freshness, and a replayed
  witness table: input `01`, reference `01`, candidate `10`, both mapped pins
  marked `≠ Different`.
- **Equivalent result:** **Restore original** then compare produced
  `EQUIVALENT`, solver `UNSAT`, `HISTORICAL`.
- **Solver timeout / UNKNOWN:** setting Timeout to 1 ms produced `UNKNOWN`,
  reason `SOLVER_TIMEOUT`, outcome `INTERRUPTED`, no EQUIVALENT badge.
- **Evidence download:** **Run and export evidence** downloaded `evidence.json`;
  **Save project** downloaded `project.json`. Captured under
  `fixtures/m4-independent-review/downloads/`.
- **CLI verification of downloaded evidence:** `flip inspect-evidence --bundle
  …/evidence.json` exit 0; `flip verify-bundle --project …/project.json --bundle
  …/evidence.json` exit 0 with recomputed EQUIVALENT/HISTORICAL; `flip compare
  --project …/project.json` exit 0.
- **Keyboard / focus:** Tab order reached the skip link, workflow nav and all
  primary controls; every checked focusable element showed a solid 2.4 px
  outline; Enter activated **Open sample**.
- **Responsive:** 390 px and 320 px viewports showed no document-level horizontal
  overflow and all workflow controls remained reachable.
- **Reduced motion:** see finding F-01/F-02 and the integration delta section.

The sample and all composition/compare flows use archived bytes and local
solver execution. They are **not** live-network verification. One CLI corpus
case (C18) did reach the default live RPC; see F-07.

## 3. Task B — independent CLI/API parity

The frozen 30-case M4-B corpus was re-executed on both targets (37 recorded
cases including product commands). `case-parity.json` records every command,
exit code and provenance. **No exit-code difference was observed between
`f4d5b3a` and `d6a0035`.**

| Area | Observation |
| --- | --- |
| EQUIVALENT | C04/C22 exit 0; report EQUIVALENT, `UNSAT`, HISTORICAL |
| DIFFERENT | C05/C26 exit 1; replayed witness present |
| UNKNOWN | C06 exit 2, `SOLVER_TIMEOUT`, no witness |
| Malformed / wrong version / bad map | C09/C10/C12 exit 3 `INVALID_INPUT` |
| Wrong chain | C11/C13/C21 exit 3 `WRONG_CHAIN` before state reads |
| RPC failure | C14 exit 4 `RPC_UNAVAILABLE` |
| Import | C27 exit 0 via local double (`CURRENT` only in that simulation); C28 `MISSING_REFERENCE` |
| STALE | C30 exit 7, freshness STALE, `BEACON_IMPLEMENTATION_CHANGED` |
| Determinism | C29: 10 builds, one digest `0x3dbb65a6…` |
| Product commands | `sample half-adder`, `sample swapped`, `export`, `inspect-evidence`, `verify-bundle` all exit 0; legacy `sample` with no subcommand exit 6 as documented |

API parity was probed over loopback: EQUIVALENT/DIFFERENT/UNKNOWN classes matched
the CLI output; caller `CURRENT` flags produced HTTP 200 with `HISTORICAL`
freshness; volatile `totalMs`, `verifiedAt` and native hashes were excluded from
semantic comparison.

## 4. Task C — trust-boundary review

All probes are captured in `executed/T-*.http.txt` and `executed/trust-probes.json`.

| Probe | Result | Assessment |
| --- | --- | --- |
| Forged EQUIVALENT→DIFFERENT claim | 422 `INVALID_INPUT` | safe |
| False CURRENT freshness relabel | 422 `INVALID_INPUT` | safe |
| Changed reference pin / stale dependency | 422 `INVALID_INPUT` | safe |
| Wrong-chain execution request | 422 `INVALID_INPUT` | safe |
| Malformed project upload | 422 `INVALID_INPUT` | safe |
| 1.1 MiB body | 413 `RESOURCE_LIMIT` | safe |
| Spoofed `Host` | 400 | safe (TrustedHostMiddleware) |
| Cross-origin `Origin` | 403 | safe |
| `Sec-Fetch-Site: cross-site` | 403 | safe |
| Cross-project bundle reuse | 422 `INVALID_INPUT` | safe |
| Manipulated witness input | 200 DIFFERENT, **recomputed** witness `01` | not a defect — alternate input `10` was also a valid counterexample (F-08) |
| Six parallel compares | `[200,200,429,429,429,429]` | two-slot limit enforced |
| Solver without opt-in (port 8001) | 501 `NOT_IMPLEMENTED` | safe |
| Listener addresses | `127.0.0.1` only on 8000/8001/8002 | no non-loopback exposure observed |

No forged-proof acceptance was possible in any attempted path. No public solver
access was observed. Therefore **M4 FAIL is not recommended** on these grounds
and there is no release blocker from public solver exposure on the supported
local deployment.

## 5. Task D — pre-flight classification

- 16 targeted pre-flight tests passed on `f4d5b3a`
  (`test_m4_workflow.py -k "preflight or burn"`), covering the exact burn revert,
  empty/short/ambiguous reverts, wrong caller/balance/needed/token, structural
  rejection, RPC failure, stale/reorg/implementation change and wrong chain.
- CLI pre-flight with unreachable RPC returned `status UNKNOWN`,
  `reasonCode RPC_UNAVAILABLE`, `freshness UNVERIFIED`, `checkedBlock null`.
- `export --observe-chain` with unreachable RPC still produced a bundle whose
  `chainObservation.status` is `UNKNOWN` while the comparison stayed
  `HISTORICAL`; no false freshness was attached.
- The acceptance rule in `flip_core/preflight.py` requires the exact four-word
  `03dee4c5` revert, fixed caller, `balance < needed == local_gates` and token 0.
  The single balance override is confined to that synthetic `eth_call`.
- Two genuine read-only live pre-flight observations succeeded via the CLI
  default RPC: block `76243401` (f4d5b3a) and `76244659` (d6a0035), fee
  `1300000000000000` wei, both `STRUCTURALLY_ACCEPTED` / `KNOWN_BURN_STAGE`.
  These are live observations, not local-double results (F-07). No transaction,
  burn payment, mint or publication occurred.
- The integrated UI states "No transaction broadcast." next to the pre-flight
  control. No wallet, signing or broadcast control exists in the interface.

## 6. Task E — UX and accessibility

Objective findings are separated from preferences:

- **Understandable sample:** the sample labels itself Historical, shows the
  block, truth table and wiring fault guide. First-time flow is followable.
- **Pin mappings:** numbered pins, explicit sources, captions and per-row
  `aria-label`s; disconnected pins are labelled in text. Selected state uses a
  leading marker as well as weight/colour — but on the integrated build the
  marker is mojibake (F-02).
- **Counterexample legibility:** input bits, mapped pin indices, reference and
  candidate columns and `≠ Different` text are present; differing cells also
  carry a double underline, so colour is not the only cue.
- **EQUIVALENT / UNKNOWN explanations:** the result panel states scope; the
  integrated live region announces verdict, freshness, intent and witness
  availability. UNKNOWN shows the reason and a retry path. The EQUIVALENT copy
  does not mention intent in the panel itself, though the setup page and live
  region do (preference, not a defect).
- **Historical/STALE visibility:** HISTORICAL is text beside the verdict; CLI C30
  produced freshness STALE with a named change.
- **Evidence export:** labelled "Run and export evidence (JSON)" on the
  integrated build; replay requires an independently chosen project and is
  described as recomputation, not certificate validation.
- **Errors:** role=alert region, focus moved to it on the integrated build;
  messages include machine codes in text.
- **Keyboard/focus:** verified as described in Task A; no keyboard trap found.
- **Reduced motion:** fixed in integration (F-01).

No subjective design preference is reported as a defect.

## 7. Findings and severities

| ID | Severity | Status | Summary |
| --- | --- | --- | --- |
| F-01 | LOW | Resolved in integration | `prefers-reduced-motion` specificity bug |
| F-02 | LOW | **Open in integration** | Mojibake `â†’`, `â–¸`, `â–¾` in CSS content |
| F-03 | LOW | **Open in integration** | Duplicated `SOLVER_TIMEOUT` ternary |
| F-04 | MEDIUM | Resolved in integration | Refresh lost project; confirmed reset added |
| F-05 | LOW | Resolved in integration | Missing "No transaction broadcast" copy |
| F-06 | INFORMATIONAL | Accepted design | HTTP 200 for completed UNKNOWN |
| F-07 | INFORMATIONAL | Disclosed | C18 used the CLI default live RPC |
| F-08 | INFORMATIONAL | No defect | Manipulated witness was still a valid counterexample |
| F-09 | INFORMATIONAL | Observed | Local-only controls verified; public hosting out of scope |

Full machine-readable detail is in `findings.json`. **No CRITICAL or HIGH
finding was identified.**

## 8. Reproducible defects

**F-02 (integrated `d6a0035`)**

1. Serve the integrated build on `127.0.0.1:8002`; open **Open sample** →
   **Composition**.
2. Focus the first pin source select.
3. Evaluate:
   `getComputedStyle(document.querySelector('.selected th'),'::before').content`
4. Observed: `"â†’ "`. Expected: `"→ "`. The same corruption exists for
   `.source summary:before` (`â–¸`, `â–¾`) in
   `apps/web/src/style.css`.

**F-03 (integrated `d6a0035`)**

Read `apps/web/src/Comparison.tsx`, the `Verdict` function's UNKNOWN branch: the
`reasonCode === "SOLVER_TIMEOUT"` condition is duplicated with identical copy.

## 9. Unexecuted and blocked cases

- True external-network access to the loopback service could not be originated
  from another interface; binding was verified from `Get-NetTCPConnection`.
- Live X Layer import/revalidation was not performed; C27/C28/C30 used the
  repository's committed offline loopback double. The only live calls were the
  two read-only C18 pre-flights disclosed in F-07.
- Playwright `npm test` from the repository was not run; equivalent scenarios
  were exercised manually through the browser session instead.
- Public deployment behaviour (authentication, rate limiting, aggregate
  quotas, TLS termination) cannot be assessed from a local launcher.
- Windows Job-object and Linux RLIMIT_AS resource containment were not
  re-measured here; inherited M3 evidence covers those platforms.

## 10. Integration delta review

The integrated branch added four commits over the fallback target. Production
deltas were confined to `apps/web/src/App.tsx`, `Comparison.tsx`, `style.css`,
web package metadata, a new Playwright acceptance spec and tests. Re-running
all 37 CLI cases on `d6a0035` produced **identical exit codes** and semantic
classes to `f4d5b3a`. Browser re-testing on `d6a0035` confirmed:

- reduced-motion now yields `transitionDuration: 0s` (F-01 resolved);
- session restore notice, confirmed reset and error focus added (F-04 resolved);
- live region announces verdict/freshness/intent;
- pre-flight copy includes "No transaction broadcast" (F-05 resolved);
- export label names the JSON format;
- F-02 and F-03 remain open.

The integration commit therefore improves, and does not regress, the acceptance
surface tested here.

## 11. Recommendation for M4 acceptance

**CONDITIONAL ACCEPT for the supported bounded local/offline deployment.**
Fix F-02 and F-03 before final release; F-04/F-05/F-01 require no further work.
Do not treat forged-proof or public-solver failures as blockers here: neither
was observed. **Public hosting remains BLOCKED** pending deployment-specific
authentication, rate/concurrency controls, aggregate resource limits and a
formal hosting decision. The local deployment is suitable for the documented
single-developer workflow only.

## 12. Public deployment limitations

- Native HTTP execution is opt-in via `FLIP_LOCAL_SOLVER=1` and additionally
  checks a loopback peer; it is not authentication.
- The launcher binds IPv4 loopback, disables proxy headers, checks Host, Origin
  and `Sec-Fetch-Site`, sets CSP and nosniff, and disables framing.
- Requests are capped at 1 MiB with two execution slots; parallel excess
  returns 429. This is a local guard, not a public rate-limit policy.
- Only single-RPC observations are claimed; malicious-RPC resistance and
  multi-operator agreement are not established.
- Structural pre-flight proves a read-only burn-stage classification only; it
  does not prove publication, ownership, minting or transaction success.
- No wallet, key, signing, broadcast, payment or deployment capability exists.

## 13. Evidence inventory

Captured raw output, transcripts, probe captures and the copied neutral corpus
are under `docs/evidence/m4-independent-review/` and
`fixtures/m4-independent-review/`. Reproducible drivers are in
`fixtures/m4-independent-review/generators/`. No files outside those two paths
were changed. No merge was performed. **Stop after the independent review.**
