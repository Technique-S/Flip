# M4.5-1A agent workflow fixtures

Supporting generator and runner scripts for the independent agent-workflow corpus.
All JSON evidence is written to `docs/evidence/m45-agent-workflow/` because the
repository custody guard rejects unregistered JSON under `fixtures/`.

| Script | Purpose |
|---|---|
| `generators/build_corpus.py` | Writes 15 workflow cases, 5 negative cases, protocol contract, request fixtures and hash manifest |
| `generators/run_cli_cases.py` | Runs real `flip` CLI commands against a loopback synthetic RPC and records outcomes |
| `generators/verify_corpus.py` | Verifies manifest, case coverage, protocol bounds, execution record and fixture hygiene |

Reproduce from the repo root:

```powershell
python fixtures/m45-agent-workflow/generators/build_corpus.py
.venv\Scripts\python.exe fixtures/m45-agent-workflow/generators/run_cli_cases.py
.venv\Scripts\python.exe fixtures/m45-agent-workflow/generators/verify_corpus.py
```

The runner uses only read-only RPC methods and never signs, broadcasts or publishes.
Library and import cases use a synthetic chain-196 double; comparison and evidence cases
use archived pinned inputs. An agent-native interface does not exist on the baseline, so
those cases are explicitly `SPEC_ONLY_NOT_IMPLEMENTED`.
