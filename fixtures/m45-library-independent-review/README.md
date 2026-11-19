# Independent M4.5-2L library review harness

OpenCode-owned harnesses used to exercise Codex's production library at tested commit
`dec9420bb76e9245c6740bf3d92031d175e408ec`. No production file was edited.

- `harness/independent_core_checks.py` — invokes real `LibraryService` with an
  OpenCode-owned RPC double; 24 production checks including the 12 research scenarios
  and adversarial discovery cases.
- `harness/independent_cli_api_checks.py` — real `flip library` CLI subprocess and real
  FastAPI app against a loopback RPC double; parity and error-code checks.
- `harness/browser_observations.mjs` — real API + loopback RPC double driven by
  Playwright Chromium; captures freshness language, keyboard, narrow viewport and
  corrupted-storage behavior.

All outputs are written to `docs/evidence/m45-library-independent-review/results/`
(the production custody scan forbids unregistered JSON under `fixtures/`).

Reproduce from the repo root:

```powershell
.venv\Scripts\python.exe fixtures/m45-library-independent-review/harness/independent_core_checks.py
.venv\Scripts\python.exe fixtures/m45-library-independent-review/harness/independent_cli_api_checks.py
node fixtures/m45-library-independent-review/harness/browser_observations.mjs
```

For browser regression tests, build the frontend first (`npm ci`, `npm run build` in
`apps/web`) before `npm test`; otherwise the served bundle is stale.
