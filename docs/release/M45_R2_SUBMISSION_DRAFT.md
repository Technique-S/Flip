# M4.5-R2 — Submission material and quickstart draft

**DRAFT — NOT SUBMITTED.** Date: 2026-11-22. Product claims below describe accepted main
`b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`. Owner must approve final wording, rights,
contact details, eligibility and access arrangement. No customer interviews, current
revenue, adoption or successful onchain publication are claimed.

## Product description

Flip is a local-first circuit workbench for developers and coding agents building with
TapeOut on X Layer. Import or open pinned circuit snapshots, compose explicit TAP-02
netlists, compare a wiring revision with a declared reference, inspect a reproduced
counterexample and verify a separate correction. Portable Project 1.1 carries named tests,
revision history and content-addressed evidence references between the browser and CLI.
Bounded agent workflows use the same native verifier and stop at publication intent.

The demo shows an archived half-adder, an intentional output swap, a replayed difference,
connection diagnostics, a verified correction and an independently replayed revised project.
Results are historical and reference-relative. The workbench does not publish circuits,
connect a wallet, sign transactions or spend funds.

Suggested short tagline: **Change circuit wiring. Keep a reproducible account of what changed.**

## Problem and differentiation

A reusable circuit's identity does not establish that a new wiring arrangement behaves like
the intended design. A passing set of vectors also does not establish equivalence over all
inputs. Developers need explicit dependency/implementation context, understandable
counterexamples and results that survive handoff between human and agent workflows.

Flip's combination is a browser workbench, canonical Python CLI/API, bounded stateless SAT
comparison with evaluator replay, connection-level relevant paths, explicit verified local
corrections, and portable parent-linked revisions with separate receipts/evidence. Hashes
establish integrity, not authorship or permission. DIFFERENT is a completed result, UNKNOWN
is inconclusive, and a stopped publication request does not resume itself.

This is an explanation of the implemented combination, not a claim of worldwide novelty,
patentability, audited smart-contract security or superiority over every developer tool.

## Target developers and route to them

| Persona | Job / value | Proposed acquisition and validation |
|---|---|---|
| TapeOut application integrator with EVM and basic digital-logic knowledge | Reuse circuit snapshots and check that mappings preserve a known reference. | Share a reproducible half-adder example in appropriate developer communities only after owner approval; ask developers to perform a timed local walkthrough. |
| Circuit maintainer | Produce a reviewable account of a revision and its reference/dependency assumptions. | Offer a maintainer-led example review; ask whether evidence/diagnostics reduce review effort. |
| Coding-agent/tool integrator | Load exact packages, run bounded steps and receive typed failures without granting spending rights. | Publish the existing CLI/schema integration examples after rights are settled; test one external agent integration. |

These are intended users and future validation channels. No reach, conversion, retention,
completion-time improvement or willingness-to-pay result has been measured. General logic
novices, HDL/EDA fabrication workflows and wallet end-users are not first-release targets.

## Why TapeOut and X Layer are central

The sample uses recorded TapeOut XOR/NAND circuit snapshots and explicit REF composition,
TAP-02 semantics and pin order. X Layer identity binds chain 196, processor and decimal
circuit ID; snapshots also bind dependencies, block/environment hashes and native engine
context. Library operations inspect processor registration and circuit metadata with bounded
read-only RPC. The integration is the circuit/data model and reproducible behavior check,
not a decorative chain label. Most UI and proof work runs locally.

Relevant identities (not Flip-owned contracts):

| Item | Exact identity | Provenance / wording for submission |
|---|---|---|
| X Layer mainnet | chainId `196` | Network identifier; [official network information](https://web3.okx.com/onchainos/dev-docs/xlayer/developer/build-on-xlayer/network-information). |
| TapeOut factory used by importer | `0x1f09daefa827f02cbb40967cc91b259763760761` | Constant in [strict ABI adapter](../../packages/flip-core/src/flip_core/abi.py); not deployed by Flip. |
| Sample processor | `0x839bdd6fa7a66416a609a735e11de5411b98574e` | Archived sample and live bounded catalog registration observed in this audit; provider observation is not author identity. |
| XOR dependency | sample processor, circuit ID `1` | Archived netlist hash `0xd3f8f3a8316a49023a82436e92607f77a51e7f1b96b614b3d71417372f3f6a9f`. |
| NAND dependency | sample processor, circuit ID `2` | Archived netlist hash `0x91c81eb018919169c97a8b7e10f4ab9bb2792960f53c0f4de3e3d2681939fd8e`. |
| Local composed half-adder | 81 bytes, 8 expanded gates | Local netlist hash `0x3dbb65a615e1f12be2325bdcad12b4a970a7ef721311452b5e09ac255ffc23ce`; no new published address/ID exists in this demo. |
| Additional catalog processor | `0x0565ea48ca41ae559d8d491dbb0a9ec945db551b` | Bounded live discovery at block 76571242; not a sample dependency or a claim of Flip ownership. |

Archived dependency hashes above come from preserved source/sample evidence, not from the
November 22 metadata-only page. That page did not provide netlist hashes. Use the package's
actual embedded block/hash labels on screen; do not relabel the sample CURRENT.

## Commercial use cases and proposed revenue

Possible use cases are circuit revision review, application-integration regression checks,
agent-generated wiring review and repeatable teaching/review exercises. Demand is a
hypothesis: the audit has no verified commercial adoption or current revenue data.

A plausible future model is team subscriptions or support for private CI workflows,
artifact retention, policy/review integration and supported local runners. Developers might
pay for repeatability and coordination rather than a claim that every circuit is safe.
Pricing and willingness to pay need interviews and pilot evidence. Paid hosted execution
would first need separate security, operational and owner approval. An open-core or dual
license model is only a future option contingent on the owner's rights/licensing decision;
Flip must not be described as already open-source simply because its repository is public.

## Substantial event-window work to describe

Git history records these additions within the displayed event window. Dates are commit
metadata, not independent authorship/time attestation. Owner must confirm actual creation,
prior work and borrowed-material attribution before submitting H4 declarations.

| Addition | Recorded implementation commit | Date recorded, Africa/Lagos |
|---|---|---|
| Canonical models and frozen schemas | `6dc21e0b97ffe03273a62ea1e9499e6346244d32` | Nov 17 |
| Pinned read-only importer and integrity checks | `0c26ab7aebba0269b41a05de657578bdb2ba6075` | Nov 18 |
| Deterministic composition and bounded Wiring Canary | `52d5475a7603587f408471554369cb1fbc2f6efc` | Nov 18 |
| Browser workbench and reproducible CLI workflow | `0b5762dfcdcfb0b71a8d0992b10747d7ee26eb96` | Nov 18 |
| Processor/circuit library | `7fabe524c9c97acd479fbe83d040cc813607d809` | Nov 19 |
| Connection diagnostics and verified corrections | `5973a30459e9e88d5720591127445ad58b38b322` | Nov 19 |
| Bounded agent controller | `5fb91579cbe6f79fefef2ff7059ff80f1af27d0f` | Nov 20 |
| Portable 1.1 packages | `475540cac3759b87df0605bb62f63135da1e30ab` | Nov 20 |
| Explicit portable-agent adapter | `303203a5909c0c5cee446f91c6170793d073beee` | Nov 20 |

R2 adds release assessment/materials only; it does not add new runtime features. Distinguish
original development from reused TAP-02 specification/reference concepts, PySAT/MiniSat,
React and other dependencies. Prior independent reports remain immutable.

## Suggested README quickstart replacement, for review

This is a **draft**, not a change to the root README. Supported distribution today is the
repository checkout, with assets/sample files at their repository paths. Prerequisites:
Git, supported Windows x64 or Linux, CPython **3.14.6**, uv **0.9.11**, Node **24.18.0** and
npm (11.16.0 observed here). Internet is needed to install dependencies. Native wheels are
platform-specific. No standalone installer, macOS support or general wheel-only app install
is promised. If uv is absent, install the pinned tool through an approved local process;
the existing README includes a venv/bootstrap method. Do not use the historical starter's
`git init`/private-audit-copy instructions for a clone of the current repository.

```sh
git clone https://github.com/Technique-S/Flip.git
cd Flip
git checkout b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b
uv --version
node --version
uv python install 3.14.6
uv sync --locked
npm ci --prefix apps/web
npm run build --prefix apps/web
```

The clone/uv provisioning lines are proposed onboarding commands, not a fresh clean-machine
trial performed by this audit. R2 did execute locked sync, npm ci, lint and build against
its existing worktree and already installed runtime. Never interpret that as validating
all prerequisite installers, corporate proxy environments or Linux desktop screen readers.

Enable the native local solver **before** launching (otherwise native HTTP operations are
intentionally disabled):

```powershell
# Windows PowerShell, from repository root
$env:FLIP_LOCAL_SOLVER = '1'
uv run --frozen python -m flip_api.local
```

```sh
# Linux shell, from repository root
FLIP_LOCAL_SOLVER=1 uv run --frozen python -m flip_api.local
```

Open `http://127.0.0.1:8000`. Do not bind to a public interface or tunnel this port.
For an offline first run: Open sample → Build netlist → evaluate four inputs → Swap outputs
→ Wiring Canary → Run comparison. Inspect the reproduced witness. To demonstrate verified
correction using a declared prior, open
`docs/schema/m45-debugging/examples/swapped-prior.execution.json`, inspect connection paths,
select Test the declared reference mappings, verify, apply locally and compare. A trust
assertion declares the chosen reference; it is not permission to sign or deploy.

In Evidence, Save complete portable project. Keep project, evidence and workflow receipt
as separate files. Bounded agent workflow works on the saved revision. A mismatch stops by
default; only enable Continue to correction when declared tests differ if that continuation
is intended. A prepared verified revision remains separate until Open verified revision.

Minimal offline CLI reproduction (use a new output directory; DIFFERENT exits 1):

```sh
uv run --frozen flip sample half-adder --out sample.json
uv run --frozen flip compose --project sample.json --out composition.json
uv run --frozen flip compare --project sample.json --out comparison.json
uv run --frozen flip sample swapped --out swapped.json
uv run --frozen flip compare --project swapped.json --out difference.json
uv run --frozen flip export --project swapped.json --out difference-evidence.json
uv run --frozen flip verify-bundle --project swapped.json --bundle difference-evidence.json
```

These existing operations were exercised by the workflow regression. Shells with automatic
stop-on-nonzero need to handle the documented DIFFERENT exit rather than calling it a crash.
`UNKNOWN` exits 2; invalid input 3; changed bindings 7; STOP_AUTHORIZATION 9. See
[CLI exit contracts](../schema/CLI_EXIT_CODES.md) and
[adapter semantics](../schema/m45-agent-portable/README.md).

Coding-agent use: construct preparation `{package, action:"correct", continueOnTestMismatch:true}`
only when the selected saved package has the intended trusted reference; run
`flip agent-portable --prepare --request preparation.json`, save its **inner request** to a
new file, then run `flip agent-portable --request request.json --out result.json`. Inspect
status and receipts before extracting `revisedPackage`. Preparation is not verification.
Do not pass the whole preparation-response wrapper back as the execution request. A
publication-purpose workflow must finish at STOP_AUTHORIZATION, not proceed to signing.

## Common troubleshooting

| Symptom | Meaning / supported response |
|---|---|
| uv not recognized / wrong Python | Install/select pinned prerequisites through approved local tooling. Use the README bootstrap path if appropriate; a Python App Execution Alias is not proof of the required minor version. |
| Local launcher reports missing assets | Run npm ci and npm run build from the checkout. `flip_api.local` resolves `apps/web/dist` relative to workspace source. A bare installed wheel is not the supported product distribution. |
| HTTP 501 for comparison/replay | Restart the local launcher with FLIP_LOCAL_SOLVER=1 in its environment; do not disable peer/origin guards. |
| Port already in use | Use `python -m flip_api.local --port 8001` and open the matching loopback URL. Do not replace another process or expose 0.0.0.0. |
| UNKNOWN / timeout / budget exhausted | Inconclusive, never EQUIVALENT. Inspect code/budget; reduce scope or choose a supported bounded setting. Do not silently raise deadlines or auto-retry a DIFFERENT result. |
| Live discovery PARTIAL_BOUNDED | A finite page; use supported cursor continuation. UNKNOWN/RESOURCE_LIMIT may retain partial hints; do not label them a full verified registry. |
| Native evidence engine mismatch | Preserve the old artifact and generate fresh local evidence with the selected engine. Canonical package parity is not native-binary equivalence. |
| Correction button disabled / no candidate | Need a compatible explicitly trusted local reference and an actual verified candidate; relevant connections do not identify a unique defective wire. |
| New revision not shown as active | Expected: the original remains open until explicit selection. Save/download all artifacts before changing the selected revision. |
| Storage quota/recovery error | Export files. Project session state and persistent library metadata are different stores; clearing one is not a complete browser-data wipe. |

Remaining owner fields: entrant/team/contact details; rights and license decision; actual
application/video URLs; permitted artifact-download location; final form fields and all
eligibility declarations. Do not fill these with invented placeholders in a real submission.
