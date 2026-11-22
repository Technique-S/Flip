# Flip recorded static showcase

This separate HTML/CSS/JSON package presents selected, verified historical snapshots.
It does not execute a project or produce a proof. The existing Flip blue/white workbench,
F mark, typography and evidence vocabulary are retained. It is not part of apps/web.

From the repository root, with Node 24.18.0:

```sh
node apps/showcase/build.mjs
node apps/showcase/build.mjs --check
node scripts/check_m45_release_package.mjs
```

Open `apps/showcase/dist/index.html` directly in a browser, with networking disabled if
preferred. No npm packages or server are needed for this build or viewing. JSON links
open exact local artifacts; use browser Save as to retain a copy. The HTML has no
JavaScript. There is no upload, wallet, RPC endpoint, proof API or publication control.
A strict meta CSP denies scripts and connections in supporting browsers.

For development checks, install the existing frontend test dependencies and Chromium:

```sh
npm ci --prefix apps/web
npm exec --prefix apps/web -- playwright install chromium
node apps/showcase/test.mjs
```

Seven pages cover sample, composition, difference, connections, correction, portable
revision and evidence. Each retains RECORDED/HISTORICAL labels. The original candidate
has 12 expanded gates against an 8-gate reference; do not call it merely an output swap.
The receipt and revised package were copied byte for byte from R2's passing browser
journey; supporting extraction/compilation and compatible-engine replay were rechecked
before curation. Original independent evidence is untouched. The builder verifies pinned
hashes, not native proofs, authorship or current-chain state.

`recordings/manifest.json` identifies every input, source revision and curation method.
The builder pins its SHA-256, escapes all displayed data and never evaluates artifact
strings. It rejects unexpected output files and symlinks. `dist/CHECKSUMS.json` covers
every other distribution file; `BUILD.json` binds builder/CSS sources. Output is ignored
by Git and reproducible byte for byte. Do not add scripts, analytics, remote fonts,
backend calls or a production-worker dependency.

Automated accessibility is not a manual screen-reader or novice usability result.
The [packaging guide](../../docs/release/M45_R3_PACKAGING.md) documents supported native
setup, packaging limits, rights decisions and troubleshooting. This prepared package
has not been deployed; hosting and judge-access compliance need separate approval.
