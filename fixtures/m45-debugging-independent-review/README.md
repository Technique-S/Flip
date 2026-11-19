# M4.5-2D-V debugging review harness

OpenCode-owned harnesses used to independently assess the production connection debugger
at PR #7 head `130dd341b622cc0ad68bffe7f6f37bb847de45c8`. No production code was edited.

| Script | Purpose |
|---|---|
| `harness/independent_debug_checks.py` | Re-derives witness/outputs/differing bits from pinned bytes with the OpenCode stdlib evaluator; drives real CLI for diagnose, equivalent and genuine correction replay plus forgery/stale/action attacks |
| `harness/production_case_matrix.py` | Maps the original 10-case corpus and trust attacks onto real production debug requests |
| `harness/trust_attacks.py` | Forged witness input, changed identity and substituted dependency closure attempts |
| `harness/debug_parity.py` | Real CLI vs FastAPI semantic parity and solver-disabled boundary |

All JSON outputs are written to `docs/evidence/m45-debugging-independent-review/results/`
(the repository custody guard rejects unregistered JSON under `fixtures/`).

Reproduce from the repo root with `FLIP_LOCAL_SOLVER=1` and the pinned `.venv`:

```powershell
.venv\Scripts\python.exe fixtures/m45-debugging-independent-review/harness/independent_debug_checks.py
.venv\Scripts\python.exe fixtures/m45-debugging-independent-review/harness/production_case_matrix.py
.venv\Scripts\python.exe fixtures/m45-debugging-independent-review/harness/trust_attacks.py
.venv\Scripts\python.exe fixtures/m45-debugging-independent-review/harness/debug_parity.py
```
