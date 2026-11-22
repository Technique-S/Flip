# M4.5-0 authorization review fixtures

Deterministic, synthetic review fixtures supporting
`docs/evidence/m45-authorization-security-review/`.

These files contain **no keys, wallet data, signatures, signed payloads, broadcast payloads or
funds**. `threat-cases.json` is a case-index mapping the 16 requested adversarial categories to the
proposal's specification cases and review findings. `rpc-observations.json` records **read-only**
observations made on 2026-11-22 through one public RPC endpoint; it is single-provider evidence, not
consensus-verified truth and not independent-operator evidence.

`MANIFEST.json` lists SHA-256 checksums of the two data files. It is a checksum, not an authority or
proof artifact. No file here establishes that any transaction was prepared, signed, submitted or
settled.

Regenerate/verify checksums with:

```sh
python -c "import hashlib,json,pathlib; d=pathlib.Path('.'); m=json.loads((d/'MANIFEST.json').read_text()); [print(f['path'], hashlib.sha256((d/f['path']).read_bytes()).hexdigest()==f['sha256']) for f in m['files']]"
```
