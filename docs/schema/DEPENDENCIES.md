# Pinned tooling and license inventory

CPython 3.14.6 is PSF-licensed; uv 0.9.11 is MIT OR Apache-2.0; Node 24.18.0
is MIT with bundled third-party notices. GitHub actions checkout v4.2.2,
setup-python v5.6.0 and setup-node v4.4.0 are MIT and pinned by verified commit SHA.
All Python runtime and test transitive versions/distribution hashes are locked in
`uv.lock`. Build backend setuptools is independently pinned in each package.

The following inventory records installed distribution metadata after the tested
Windows install. Preserve upstream distribution license files/notices when
redistributing; this inventory is not a replacement for those files.

| Distribution | Tested version | Declared license |
| --- | --- | --- |
| annotated-doc | 0.0.6 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.11.0 | MIT |
| attrs | 26.1.0 | MIT |
| certifi | 2026.10.23 | MPL-2.0 |
| click | 8.5.1 | BSD-3-Clause |
| colorama | 0.4.6 | BSD |
| fastapi | 0.121.1 | MIT |
| h11 | 0.16.0 | MIT |
| httpcore | 1.0.9 | BSD-3-Clause |
| httpx | 0.28.1 | BSD |
| idna | 3.20 | BSD-3-Clause |
| iniconfig | 2.3.1 | MIT |
| jsonschema | 4.25.1 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.7.0 | MIT |
| pydantic | 2.12.4 | MIT |
| pydantic-core | 2.41.5 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| pytest | 9.0.1 | MIT |
| referencing | 0.37.0 | MIT |
| rpds-py | 2026.9.1 | MIT |
| ruff | 0.14.5 | MIT |
| setuptools | 80.9.0 | MIT |
| sniffio | 1.3.1 | MIT / Apache |
| starlette | 0.49.3 | BSD-3-Clause |
| typing-inspection | 0.4.5 | MIT |
| typing-extensions | 4.16.0 | PSF-2.0 |
| uvicorn | 0.38.0 | BSD-3-Clause |

AnyIO is constrained to 4.11.0 because the initially resolved 4.16.0 emitted a
Starlette TestClient deprecation warning. The complete suite passes with the
constrained version. CLI uses standard-library argparse; no Typer is needed.

TAP-02 specification is CC0-1.0, upstream reference is MIT. Source hashes and
immutable links are in the contract documentation; the upstream evaluator is not
vendored or installed. Python-sat/Minisat22 is **not installed**: binary packaging,
license review of the selected exact distribution and per-platform containment
remain M3 prerequisites. No additional solver license is implied by M1.

No license has been selected for Flip's own source. Maintainer must choose one
before third-party distribution; this change does not grant an unsolicited license
to the historical PRD or audit artifacts.
