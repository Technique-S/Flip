# Flip M4-B — independent UX acceptance fixtures

OpenCode / HY4 Flash supporting-engineer deliverable for the M4 product
experience. **Fixtures and documentation only.** No production package, shared
schema, dependency lock, CI configuration, frontend application or audit
evidence was modified. No merge into `main`. Stop at M4-B.

Baseline: accepted M3 integration head
`af8ba1f109a2a1c59fe36be044bc025a127ea025` (PR #3 head; see the handoff for the
recorded setup deviation). All hashes are SHA-256 and registered in
[`MANIFEST.json`](MANIFEST.json).

## Contents

| Path | Purpose |
| --- | --- |
| `journeys/JOURNEYS.json`, `journeys/README.md` | 13 golden user journeys with initial state, action, response, trust/freshness, failure handling, accessibility and reproducible input |
| `cli-cases/CLI_ACCEPTANCE.md`, `cli-cases/CASES.json` | 30 executed CLI cases plus 6 planned-but-unexecuted specifications |
| `cli-cases/requests/` | Neutral request fixtures derived from the frozen half-adder sample; no fabricated claims |
| `cli-cases/requests/SOURCES.json`, `CONSUMPTION_SOURCES.json` | Exact derivation provenance for each request fixture |
| `error-messages/error-catalog.json`, `ERROR_MESSAGE_REVIEW.md` | 12 plain-language explanations with technical codes in expandable details |
| `browser/accessibility-matrix.json`, `ACCESSIBILITY_ACCEPTANCE_PLAN.md`, `playwright-spec.md` | 11 browser/a11y scenarios and an unexecuted Playwright scaffold |
| `docs/USER_GUIDE.md` | Bounded user documentation for the nine required topics |
| `generators/` | Deterministic fixture builder, CLI runners, local RPC double and verification |

Executed evidence lives in `docs/evidence/m4-ux-acceptance/`, including the
[M4-B handoff](../../docs/evidence/m4-ux-acceptance/M4_B_HANDOFF.md),
`executed/transcript.json`, `executed/summary.json` and raw per-case captures.

## Provenance legend

| Class | Meaning |
| --- | --- |
| `PINNED_M3_BASELINE` | executed with the pinned uv lockfile on the accepted M3 head; no live RPC |
| `LOCAL_DOUBLE_OFFLINE_ARCHIVED_BYTES` | executed against a loopback double reusing the committed M2 offline transport and archived M0/M0.5 bytes; never a live chain observation |
| `NEUTRAL_DERIVED_FROM_FROZEN_M3_SAMPLE` | request fixture derived mechanically from `docs/schema/m3/examples/half-adder.request.json` |
| `CLAIMS_CAPTURED_CLI_OUTPUT` | consumption claim taken from actual `flip compare` stdout, not authored |
| `SPEC_ONLY_NOT_EXECUTED` | web/M4 capability absent on the baseline; no passing result claimed |

## Regeneration and verification

From the repository root with Python 3.14.6 and uv 0.9.11:

```powershell
uv sync --locked
uv run --frozen python fixtures/m4-ux-acceptance/generators/build_fixtures.py build
uv run --frozen python fixtures/m4-ux-acceptance/generators/verify_fixtures.py
```

`verify_fixtures.py` rebuilds the 10 neutral request fixtures in a scratch
directory, requires byte equality, verifies every registered hash, and rewrites
the semantic transcript summary and `cli-cases/CASES.json`. Use `--write` to
refresh `MANIFEST.json` after intentionally changing authored files. Captured
stdout files are registered as `EXECUTED_CAPTURE`: they contain noncanonical
timings and are not expected to regenerate byte-identically.

## Important boundaries

- `LOCAL_DOUBLE_OFFLINE_ARCHIVED_BYTES` results include `CURRENT`/`STALE`
  labels that describe the **simulated** environment only. They are never live
  X Layer evidence.
- `flip preflight`, `export`, `sample` and `verify-bundle` are reserved on this
  baseline. Their cases are specifications with observed `NOT_IMPLEMENTED`
  behaviour, not fabricated passes.
- No browser test was executed; the web application does not exist on this
  branch.
