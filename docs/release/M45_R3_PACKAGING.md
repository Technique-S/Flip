# M4.5-R3 — Source and static package instructions

Prepared 2026-11-23. No deployment, installer or native binary redistribution is included.
The accepted runtime is `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`; reviewed R2 is
`39df7af4c2784502d243e6cc00be43fa84b5799b`. R3 descends from R2 and retains both
histories and all original independent reports. The final delivery commit is the immutable
Git SHA accompanying this handoff; a document cannot contain its own commit hash.

## Source checkout and inventory

Use the [root README](../../README.md) for pinned runtime setup and a complete first-use
walkthrough. For R3, replace the checkout pin with the exact delivery SHA; verify
`git rev-parse HEAD` against that SHA. Do not download a branch ZIP and call it immutable.
Use `git status --short`, `uv sync --locked` and `npm ci --prefix apps/web`; never update
locks to repair an installation without a separate review.

| Component | Pinned or observed version | Distribution scope |
|---|---|---|
| Flip workspace/core/CLI/API | 0.1.0; accepted runtime SHA above | Source checkout only |
| CPython / uv | 3.14.6 / 0.9.11 | Locally provisioned prerequisites |
| Node / npm | 24.18.0 / 11.16.0 observed | Node required for both builds; npm only for runtime/test deps |
| React / React DOM | 19.3.1 | Existing local workbench, absent from static output |
| esbuild / TypeScript | 0.28.2 / 7.0.2 | Existing frontend build tooling |
| Playwright / axe-core Playwright | 1.65.1 / 4.14.0 | Existing QA tooling, absent from static output |
| Python and transitive JS dependencies | Exact versions/integrities in uv.lock and apps/web/package-lock.json | Unchanged locks; metadata inventory linked below |

The machine-readable [asset inventory](M45_R3_ASSET_INVENTORY.json) binds the locks,
static sources, recording inputs and generated output checksums. The preserved
[R2 metadata inventory](M45_R2_EVIDENCE.json) contains installed Python/Node versions
and license declarations. Metadata is a discovery aid, not a complete legal opinion.

## Build and inspect the static bundle

```sh
node apps/showcase/build.mjs
node apps/showcase/build.mjs --check
node scripts/check_m45_release_package.mjs
```

Open `apps/showcase/dist/index.html` by file URL. No server, npm install or network is
required to build/view it with Node installed. Seven HTML pages, one CSS, eight JSON
artifacts, BUILD.json, README.txt and CHECKSUMS.json: **19 files**, no client JavaScript.
The recordings are immutable build inputs; do not replace them with arbitrary imports.
All displayed artifact fields are text-escaped, and manifest/file bytes are pinned.
No dynamic evaluation, executable uploads or browser project import exist here.

`CHECKSUMS.json` covers every other output file; the inventory also hashes that manifest.
`BUILD.json` hashes the builder, library and CSS, with all sensitive capability flags false.
Two builds on the same sources must match `--check`; Windows/Linux CI rebuilds and
checks its own copy. This establishes deterministic static bytes, not reproducible native
wheel binaries, upstream dependency availability or trust in an unsigned Git checkout.
Compare checksums through a trusted delivery channel before sharing copies.

`dist` is ignored, not committed. Preserve the whole directory structure if preparing an
owner-reviewed archive. Do not add native workers, dependencies, local storage, telemetry,
remote assets or a fallback server. No archive, installer or hosted access is published by
this assignment. Rights clearance and explicit owner authorization are still required.

## Third-party notice inventory and rights decisions

| Material | Source/notice location | Release consequence |
|---|---|---|
| Flip own source and original presentation | No root source LICENSE selected; owner decision outstanding | Do not label this an approved open-source release or choose a license |
| python-sat / PySAT wrapper | Locked distribution metadata; wrapper MIT; bundled solver notices differ | Wheel installation by user is distinct from redistributing its native binaries |
| MiniSat and other solvers included in python-sat | Installed wheel license/solver notices; MiniSat MIT-style, others individually applicable | Review all shipped solvers and retain notices before any binary packaging; wrapper MIT is insufficient |
| React/React DOM and JS transitive packages | npm lock and installed node_modules package LICENSE/metadata | Inventory exists; review/copy exact notices if bundling the production frontend |
| Python API/validation/HTTP/test packages | uv lock and installed .dist-info licenses/metadata | Review the full selected distribution's notices before redistribution |
| Archived TapeOut/X Layer snapshots, source metadata and historical evidence | Original preserved fixture/evidence records and processor identities | Evidence provenance is not ownership or a sublicense; owner must clear content use |
| Static CSS/HTML generator | Repository source; system fonts, source-drawn Flip F, no external images/fonts/code | Static output has no bundled React/PySAT/native binary; own-source/content rights still unresolved |
| QA tools (axe/Playwright/browser) | Existing dev dependencies and their upstream notices | Not copied into the static output |

This inventory is not a license text bundle or completed rights clearance. Do not publish
native binaries, an installer, an open-source license announcement or a commercial grant
until the owner decides the license and clears relevant third-party rights. No new
external dependency or dependency version was introduced by R3.

## Troubleshooting

| Symptom | Action |
|---|---|
| uv command unavailable | Provision pinned uv in an approved environment; reopen terminal/check PATH. A previous developer's bootstrap path is not portable. |
| Python version rejected | Install 3.14.6 with uv; run from the source root; keep required-version constraints. |
| Native wheel unavailable on this platform | Use a supported Windows x64/Linux environment and inspect the locked wheel availability. Do not substitute an unreviewed solver. |
| npm/build failure | Verify Node 24.18.0; use npm ci and preserve package-lock. Corporate proxies/download failures are environment limits. |
| Launcher says build frontend first | Run npm ci/build from this source checkout. A wheel-only install omits source-relative web/sample assets. |
| Solver HTTP operation disabled | Set FLIP_LOCAL_SOLVER=1 before starting the loopback launcher; restart it. It is intentionally opt-in. |
| Port 8000 in use | Stop the old local instance or use `python -m flip_api.local --port 8001`; open the exact loopback URL. Do not expose/tunnel it. |
| Archive evidence rejected on another OS | Engine identities can differ. Preserve historical evidence and regenerate/replay new local evidence. Never bypass engine/dependency pins. |
| DIFFERENT causes shell failure | Exit 1 is a result. Inspect JSON; UNKNOWN (2) is not success. Publication intent terminates with STOP_AUTHORIZATION (9). |
| Portable output already exists | Choose a new output filename. Preserve the original package and its parent relationship. |
| Library RPC unavailable | Use offline sample first; archived snapshots do not establish current chain state. Keep credentials out of URLs/files. |
| Static JSON link opens in browser | Expected for file URLs. Use Save as; do not claim a tested universal forced-download behavior. |
| Static output drift/unexpected file | Inspect it, then build into a separately reviewed clean directory; do not disable checksum or executable-file checks. |
| Browser data disappeared | Local/session storage is not a backup; reopen separately exported files. Do not store secrets in project metadata. |

A clean novice installation, manual auditory screen-reader trial, Safari/Firefox and
physical assistive-device testing have **NOT BEEN PERFORMED**. Existing isolated
Chromium checks do not bypass the previously blocked personal-browser action.
