# Flip M4-C — independent review fixtures

Supporting engineer deliverable for the M4 web/CLI/accessibility review.
Only this directory and `docs/evidence/m4-independent-review/` are written.
No production code, frontend source, schema, lock, CI file or existing fixture
byte was changed. No merge.

| Path | Purpose |
| --- | --- |
| `corpus/` | Byte-copies of the frozen M4-B neutral request fixtures, read from `opencode/flip-m4-ux-acceptance` and replayed against both M4 targets |
| `downloads/` | `evidence.json` and `project.json` downloaded from the real browser |
| `generators/run_review_cases.py` | Replays 37 CLI cases; honours `M4C_FLIP` and `M4C_EXEC_DIR` for delta runs |
| `generators/run_trust_probes.py` | Loopback HTTP trust-boundary probes |

Captured raw output, transcripts, semantic comparisons and the final report are
in `docs/evidence/m4-independent-review/`. The local RPC double used in the
corpus is the repository's committed offline transport; it is never a live
chain observation. The two C18 pre-flight captures did use the CLI's default
live RPC and are disclosed as such in the report.

Regeneration from the repository root:

```sh
uv sync --locked
uv run --frozen python fixtures/m4-independent-review/generators/run_review_cases.py
uv run --frozen python fixtures/m4-independent-review/generators/run_trust_probes.py
```
