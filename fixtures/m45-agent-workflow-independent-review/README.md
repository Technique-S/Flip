# M4.5-1A-V agent workflow independent review harness

OpenCode-owned harnesses used to independently verify the production agent workflow
controller at delivery SHA `d2638d057b6236286480891d6fdd7dfb0402bc5a`. No production
code was modified.

| Script | Purpose |
|---|---|
| `harness/independent_acceptance.py` | 27 independent checks over the real core/CLI covering the 15 corpus scenarios, negatives, adversarial authorization, cancellation and reproducibility |
| `harness/authorization_checks.py` | Deep authority-field injection, freshness-promotion, write-op rejection, API parity and loopback gating |

All outputs are written to `docs/evidence/m45-agent-workflow-independent-review/results/`.
No wallet, signing, transaction or live chain observation.

Reproduce with the pinned `.venv` and `FLIP_LOCAL_SOLVER=1` where required:

```powershell
.venv\Scripts\python.exe fixtures/m45-agent-workflow-independent-review/harness/independent_acceptance.py
.venv\Scripts\python.exe fixtures/m45-agent-workflow-independent-review/harness/authorization_checks.py
```
