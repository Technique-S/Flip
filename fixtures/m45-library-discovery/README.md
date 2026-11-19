# M4.5-2L library discovery fixtures

Read-only feasibility evidence for the circuit/processor library discovery investigation.
Nothing in this directory is a production implementation and nothing grants transaction
authority.

## Layout

| Path | Provenance | Contents |
|---|---|---|
| `generators/keccak_selectors.py` | derived, deterministic | Dependency-free Keccak-256; self-checks and recomputes all 11 relied-on ABI selectors |
| `generators/capture_live_readonly.py` | tooling | Bounded pinned-block RPC capture (read methods only, 40-call budget) |
| `generators/build_fixtures.py` | tooling | Deterministic emission of synthetic cases, seeds and SHA-256 manifest |
| `generators/verify_fixtures.py` | tooling | Manifest, schema, provenance-label and authority assertions |
| `cases/` | **SYNTHETIC** | 12 mocked discovery cases (C01–C12) |
| `seeds/verified_known_addresses.json` | OBSERVED_READ_ONLY_DERIVED | Truthful fallback seed list from audit evidence and live observation |
| `observations/live_xlayer_observation_*.json` | OBSERVED_READ_ONLY | One bounded live capture with block, hash, chain ID and provider trust |
| `SHA256SUMS.manifest.json` | derived | SHA-256 and byte count for every file in this directory |

## Reproduction

```powershell
python fixtures/m45-library-discovery/generators/keccak_selectors.py
python fixtures/m45-library-discovery/generators/build_fixtures.py
python fixtures/m45-library-discovery/generators/verify_fixtures.py
```

Optional live refresh (network required, read-only, ~33 RPC calls):

```powershell
python fixtures/m45-library-discovery/generators/capture_live_readonly.py
python fixtures/m45-library-discovery/generators/build_fixtures.py
python fixtures/m45-library-discovery/generators/verify_fixtures.py
```

## Rules

- Synthetic cases must carry `provenance: "SYNTHETIC"`; live observations carry
  `artifactType: "OBSERVED_READ_ONLY"`.
- No signing, wallet connection, broadcast, state override or payment appears in any case.
- `eth_getLogs` output is recorded as an availability observation only. No factory
  registration event signature is asserted or interpreted as authoritative.
- Re-run `build_fixtures.py` after editing any fixture file, then verify.
