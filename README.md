# Flip

Flip is a local-first, read-only circuit workbench for TapeOut on X Layer. Humans and
coding agents can compose explicit TAP-02 wiring, reproduce behavioral differences,
inspect relevant connections, verify corrections and exchange Portable Project 1.1
revisions with content-addressed evidence. **Flip does not publish circuits.**

The accepted runtime is `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`.
This release branch adds documentation and a separate recorded static showcase;
production runtime, schemas and dependency locks retain that accepted revision.

## What works

- Browse processor/circuit metadata through bounded read-only X Layer RPC, or start
  offline with the archived half-adder and its pinned dependencies.
- Compose REF circuits, evaluate vectors and compare a stateless candidate with its
  declared reference using a bounded native SAT worker and trusted evaluator replay.
- Wiring Canary returns DIFFERENT witnesses, relevant connection paths and explicit
  correction proposals. Verification precedes applying a new local revision.
- Export/replay evidence and Portable Project 1.1 packages with named tests, parent-linked
  revisions and evidence references. Keep original packages and receipts separately.
- Run bounded declarative agent workflows through the CLI/API or browser adapter.
  Publication intent ends at STOP_AUTHORIZATION; metadata never grants spending rights.

These are reference-relative checks, not arbitrary HDL synthesis, formal verification of
smart contracts, a circuit marketplace or an onchain publication service.

## Install the local workbench

Supported source-checkout targets: Windows x64 (PowerShell) and Linux with compatible
native wheels. You need Git, Python **3.14.6**, uv **0.9.11**, Node **24.18.0** and npm
(11.16.0 used in acceptance). Installation needs network access. No installer, bundled
native binary, macOS support or wheel-only application distribution is promised.

Provision uv 0.9.11 using your approved Python environment, for example
`python -m pip install uv==0.9.11` (Linux may require a virtual environment).
Then, from a fresh terminal:

```sh
git clone https://github.com/Technique-S/Flip.git
cd Flip
git checkout b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b
uv python install 3.14.6
uv sync --locked
npm ci --prefix apps/web
npm run build --prefix apps/web
```

That pin installs the accepted native product. To include this branch's showcase and
release guides, check out the exact R3 delivery SHA given in its handoff instead; never
substitute a moving branch for an integrity pin. Run commands from the repository root.
The launcher resolves its frontend and sample files relative to this checkout.

Native HTTP computation is an explicit local opt-in. Set it **before** starting:

```powershell
# Windows PowerShell
$env:FLIP_LOCAL_SOLVER = '1'
uv run --frozen python -m flip_api.local
```

```sh
# Linux
FLIP_LOCAL_SOLVER=1 uv run --frozen python -m flip_api.local
```

Open `http://127.0.0.1:8000`. The supported launcher binds loopback, checks host/origin
and serves frontend/API together. Stop with Ctrl+C. Do not tunnel or expose this native
worker. The opt-in is not wallet authorization. CLI verification also runs native local
code; use only the bounded, trusted supported operations.

## First half-adder walkthrough

1. Select **Open sample**, then **Build netlist**. The archived reference expands to
   8 gates / 81 TAP-02 bytes. Evaluate the four inputs; numeric pin 0 is carry and pin 1
   is sum. Bit strings list pin 0 first.
2. Use **Swap outputs**, open Wiring Canary and run comparison. Inspect the DIFFERENT
   witness and reproduced reference/candidate outputs. DIFFERENT is a completed result;
   UNKNOWN means the comparison was inconclusive.
3. For a correction with a declared prior, open
   `docs/schema/m45-debugging/examples/swapped-prior.execution.json`. Inspect the relevant
   connection paths, select **Test the declared reference mappings**, verify, apply the
   verified correction locally and compare again. Relevant paths can be ambiguous;
   they do not establish a unique root cause.
4. In Evidence, **Save complete portable project**. Save evidence separately. Reopen the
   Portable 1.1 JSON and inspect tests, provenance and revision. Use a new filename for
   a new revision; preserve the original. A hash proves byte integrity, not authority.

No RPC is needed for the archived sample. Live library browsing needs a reachable
read-only provider and is distinct from historical sample evidence.

## CLI and agent integration

From the checkout, use new output filenames:

```sh
uv run --frozen flip sample half-adder --out sample.json
uv run --frozen flip compose --project sample.json --out composition.json
uv run --frozen flip compare --project sample.json --out comparison.json
uv run --frozen flip export --project sample.json --out evidence.json
uv run --frozen flip verify-bundle --project sample.json --bundle evidence.json
```

On the R3 checkout, the bounded offline agent example is:

```sh
uv run --frozen flip workflow --request docs/release/examples/m45-local-agent.request.json --out receipt.json
```

Inspect typed results, not just process success. Exit 1 is DIFFERENT, 2 UNKNOWN,
3 invalid input, 7 stale bindings and 9 STOP_AUTHORIZATION. A publication stop is final;
it does not resume. No agent-supplied assertions grant signing/spending permission.
The [schema contracts](docs/schema/m45-agent-workflow/1.0.0/request.schema.json)
and [integration acceptance](docs/milestones/M45_AGENT_PORTABLE_POST_MERGE_ACCEPTANCE.md)
describe the existing interfaces. Portable adapter plans must be reviewed before
execution; the CLI executes the inner `request` returned by `--prepare`.

## Portable 1.1 round-trip

On R3, after creating `sample.json`, Node's standard library can create the declarative
wrap request (it does not evaluate project content):

```sh
node -e "const f=require('node:fs');f.writeFileSync('wrap.request.json',JSON.stringify({schemaVersion:'flip-portable-project-1.1.0',kind:'PORTABLE_REQUEST',operation:'wrap',executionRequest:JSON.parse(f.readFileSync('sample.json','utf8'))}))"
uv run --frozen flip portable --request wrap.request.json --out portable.json
node -e "const f=require('node:fs');const p=JSON.parse(f.readFileSync('portable.json','utf8'));for(const op of ['validate','open','downgrade'])f.writeFileSync(op+'.request.json',JSON.stringify({schemaVersion:'flip-portable-project-1.1.0',kind:'PORTABLE_REQUEST',operation:op,package:p,...(op==='downgrade'?{allowLossy:true}:{})}))"
uv run --frozen flip portable --request validate.request.json --out validated.json
uv run --frozen flip portable --request open.request.json --out opened.json
uv run --frozen flip portable --request downgrade.request.json --out downgraded.json
```

The minimal wrapper declares no tests and no evidence; it makes no new proof claim.
Open `portable.json` in the browser, save a separate revision and compare its parent
and execution hashes. Every downgrade requires explicit lossy consent, including this minimal wrapper;
never discard tests/history silently. A compatible engine can independently replay a
separately saved evidence bundle with `verify-bundle`.

## Recorded static showcase

On the R3 checkout, Node alone builds the inert presentation:

```sh
node apps/showcase/build.mjs
node apps/showcase/build.mjs --check
node scripts/check_m45_release_package.mjs
```

Open `apps/showcase/dist/index.html` directly, offline. Seven linked pages show curated
sample → composition → DIFFERENT → connections → verified correction → revision →
evidence snapshots. Every page is marked **RECORDED · HISTORICAL**. The curated candidate
has 12 gates, not merely swapped outputs. This showcase has no JavaScript, backend,
native solver, uploads, RPC or wallet. See its [guide](apps/showcase/README.md).

## Evidence and operational limits

Historical evidence binds a recorded environment, dependency snapshots, reference and
native engine. It is not a current-chain proof, authorship certificate, security audit or
permission to act. Different platform binaries may correctly reject historical engine
pins; retain the old evidence and generate fresh evidence locally. Do not override checks.
Portable provenance claims cannot promote historical evidence to CURRENT.

The browser keeps project/session state in sessionStorage and library/recovery state in
localStorage. Export files before clearing browser data; do not store secrets in projects,
RPC URLs or screenshots. There is no account vault or credential-management promise.

Supported: local source checkout, bounded read-only discovery/import, local verification,
agent workflows and file export/replay. Prepared separately: inert static presentation.
Unsupported: public native solver/API hosting, tunnels, deployment, wallet connection,
signing, transaction construction, spending, broadcasting and circuit publication.
No deployment or hackathon submission has been performed. A repository/static URL has
not been confirmed to satisfy the organizer's application-access requirement.

Own-source licensing remains an owner decision. Third-party notices are inventoried,
not a grant to redistribute every bundled solver. No native binary or installer is supplied.
See [packaging and troubleshooting](docs/release/M45_R3_PACKAGING.md),
[asset checklist](docs/release/M45_R3_DEMO_AND_CHECKLIST.md),
[R3 handoff](docs/release/M45_R3_HANDOFF.md) and
[the preserved R2 audit](docs/release/M45_R2_READINESS_AUDIT.md).
