# M4.5-1P-V portable project independent review harness

OpenCode-owned harnesses used to verify Portable 1.1 at delivery SHA
136b1115ee0f5ffe0a5583d68c474641fdce1ca1. No production code was modified.

| Script | Purpose |
|---|---|
| harness/portable_acceptance.py | 30 independent checks for legacy compatibility, named vectors, evidence trust, revision chains and resource limits |
| harness/evidence_trust.py | Evidence attacks with recomputed package checksums to isolate semantic trust rules |
| harness/portable_api.py | Core/CLI/API parity and replay gating |

All outputs are written to docs/evidence/m45-portable-independent-review/results/.
