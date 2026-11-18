# Flip M4-A product handoff

## Run Flip locally

From this branch's repository root, use CPython 3.14.6, uv 0.9.11, Node 24.18.0 and npm. The supported installation is the checked-out workspace. The sample and built UI are loaded from that checkout.

```sh
uv sync --locked
npm ci --prefix apps/web
npm run build --prefix apps/web
uv run --frozen python -m flip_api.local
```

Open **http://127.0.0.1:8000**. The same process serves the static React/TypeScript application and FastAPI. To enable native comparison, export and replay, set `$env:FLIP_LOCAL_SOLVER="1"` in PowerShell or `export FLIP_LOCAL_SOLVER=1` in a POSIX shell **before starting the server**. The launcher accepts an optional `--port`. Imports and the historical sample work with the solver disabled.

## First session

1. In **Sources**, open the historical half-adder. It uses the recorded chain-196 XOR #1 and NAND #2 at block 76206482. Credentials and external requests are unnecessary.
2. In **Composition**, build the original. Inspect the 81 TAP-02 bytes, manifest and two dependencies. Expand **Half-adder truth table** and evaluate all four input pairs. Pins start at zero. The output order is carry, sum.
3. Choose **Swap outputs**, open **Wiring Canary** and run the comparison. On a recorded run the evaluator reproduced input `01`, reference `01`, candidate `10`. Both mapped pins differ. **Behavior only** leaves intent undeclared. A trusted reference or previous version requires a user assertion.
4. Restore the original wiring and compare again. The exact stateless miter returns UNSAT and the verdict is EQUIVALENT. A 1 ms worker deadline on the test hosts yielded UNKNOWN with SOLVER_TIMEOUT.
5. In **Evidence**, save the project separately and select **Run and export evidence**. This starts a fresh run and downloads its result, including inconclusive outcomes. Replay evidence against an independently selected project. Replay returns a freshly computed comparison. An inconclusive file can be inspected and the project rerun.

For a new design, import a registered processor address and decimal circuit ID. The first import initializes a REF wrapper and a local reference. Additional imports use the project's pinned block. Inspect the processor, widths, state count, gate count, manifest, block and REF dependencies. **Revalidate on chain** queries the configured RPC. Stateful sources can be inspected. Composition requires stateless components with native REF-compatible widths.

The editor supports external pins, REF instances, NAND glue, explicit output selection, editable mappings and a local reference snapshot. Select a source for a numbered destination to highlight both endpoints. Clear a disconnected pin by selecting a valid source. Match reference/candidate interfaces before building. A new local reference can be captured after width changes. The interactive table supports up to 255 inputs/outputs and a 65,000 option rendering budget. Larger supported projects use the CLI.

## CLI journey

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

The mutation comparison, export and successful replay each exit **1** for DIFFERENT. Equivalent exits 0. UNKNOWN exits 2, invalid input 3, RPC infrastructure errors 4, legacy unavailable operations 6, changed bindings 7 and structural rejection 8. Scripts should read both the operation's JSON and exit code. Use `vectors --project` with the M3 vector request for declared input/output rows.

Live read-only commands, run separately from offline tests:

```sh
uv run flip inspect --processor 0x839bdd6fa7a66416a609a735e11de5411b98574e --id 1
uv run flip import --processor 0x839bdd6fa7a66416a609a735e11de5411b98574e --id 1 --out source.json
uv run flip new-project --source source.json --out imported-project.json
uv run flip compose --project imported-project.json
uv run flip preflight --project project.json
uv run flip export --project project.json --observe-chain --out observed.json
```

Set `FLIP_RPC_URL` on the server or CLI to configure the trusted operator. HTTP clients cannot choose arbitrary RPC targets. Only chain 196 is supported. A failed import surfaces the actual error. Explicit historical imports accept `--block-number`.

## Evidence and structural classification

The additive `m4-1.0.0` envelope uses a single canonical JSON document. It contains the M3 comparison, project and source snapshots, both execution identities and canonical manifest hashes, implementation and dependency context, mappings, solver limits and outcome, reproduced witness where applicable, tool/engine identities and reproduction command. `contentHash` covers the other fields using flip-json-v1. Each run records observed timings and time of verification. Separate runs can have different file hashes.

The UI and CLI reuse the existing M3 compose/compare/vectors/consume boundaries. The additional product HTTP POST operations are `new-project`, `export`, `verify-bundle` and `preflight` under `/api/v1/`. They use `kind=PRODUCT_REQUEST` and `schemaVersion=m4-1.0.0`. The first takes `source`; the others take the full M3 `executionRequest`. Export accepts `observeChain`. Replay accepts a bundle object or its JSON text and derives pins from the caller's independent request. GET `/api/v1/sample/half-adder` and `/api/v1/sample/swapped` load the archived sample and its mutation.

Offline comparisons carry HISTORICAL or known STALE integrity. Fresh structural observations have their own checked block and fee. Export with the chain option attaches that observation, including a failure or change. Offline replay never attests to the recorded RPC response or elapsed time. It recompiles and reruns the proof using the pinned engine and independently replays a claimed witness. Cross-platform builds may differ in native binary hashes. A changed engine requires a new comparison. A checksum alone grants no proof authority.

Pre-flight uses the first source processor and resolves all supplied closures at one newly pinned block under a shared RPC/time budget. It checks source block canonicality, snapshots and environment, the reviewed validator code identity, current fee, chain ID and final block hash. The sole probe is a fixed `eth_call` with the synthetic caller's fee balance overridden for that call. The acceptance rule requires the exact four-word insufficient-balance revert, matching caller, insufficient balance, expected local gate count and token ID zero. Three byte-exact known structural revert strings yield REJECTED. Empty data, ambiguous results, unsupported overrides, RPC failures or changed implementations yield UNKNOWN. A single RPC remains a trust assumption.

A separate read on 2026-11-18 observed STRUCTURALLY_ACCEPTED for the original 81-byte sample at block **76234348**, fee **1300000000000000 wei**. The recorded response is [M4_A_LIVE_PREFLIGHT.json](M4_A_LIVE_PREFLIGHT.json). This observation applies to that block. No transaction was signed or sent.

## Acceptance and provenance

PR #3's reviewed production baseline was unchanged between review target `59751e20590117f0cbc4ef41b9b30d836e533f84` and accepted head `af8ba1f109a2a1c59fe36be044bc025a127ea025`. Both CI platforms passed. The merge preserving both parents is **0bd006336d9ab710706e1e11aa0533636d7fae1e**. The product branch starts at that merge. All 440 inherited test cases, frozen schema bytes and historical evidence are retained.

The combined suite covers the historical workflow, CLI and API parity, evidence recomputation, untrusted claims, source validation, strict burn decoding, all three pre-flight outcomes, transport errors, stale/reorganized blocks, the read-method boundary and local deployment controls. Chromium exercises desktop and 390 px layouts, keyboard input, reduced motion, actual downloads and replay through a separate CLI process. The import journey uses a synthetic loopback RPC. The mandatory tests have no live-chain dependency.

```sh
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen ruff format --check .
npm run lint --prefix apps/web
npm run build --prefix apps/web
# In apps/web, install Chromium once, then run browser acceptance.
npx playwright install --with-deps chromium
npm test
```

CI also executes the v1/M2/M3 schema drift checks, Python/Node canonical parity, historical custody and credential checks, CLI/ASGI smoke tests and the M3 benchmark. The original sample reproduces SHA-256 `3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`.

## Hosting and integration limits

Only the local launcher is supported. It binds IPv4 loopback, disables proxy-header trust, checks peer/Host/origin, serves same-origin assets, and disables framing. Native HTTP operations require deliberate solver opt-in and a loopback peer. Requests are capped at 1 MiB and share two execution slots. The M3 worker retains its isolated process, timeout and cleanup controls. Windows measures private commit and Linux measures virtual address space. Neither metric covers whole-service RSS.

Project data stays in browser memory until saved. Each action sends the necessary project data to the local API. Live import, revalidation and pre-flight use the configured external RPC. No wallet, signing, transaction broadcast, token acquisition or payment path is present. Public verification hosting remains blocked pending deployment-specific isolation, authentication and aggregate resource controls.

Integration scope is the local developer workflow. M5 and remote hosting are outside this branch.
