# M4.5-R3 release acceptance fixtures

Synthetic, deterministic fixtures supporting
`docs/evidence/m45-release-acceptance/STATIC_SHOWCASE_SECURITY.md`.

`claim-negative-cases.json` contains **invented test inputs only** for future display/UI rejection checks.
They are not quotations from R2, not observed product behavior and not recorded submission text. Each case
states the expected safe classification and the assertion a reviewed implementation must make.

No fixture contains keys, wallet data, signed payloads, real personal data or live RPC responses.
`MANIFEST.json` is a checksum inventory, not proof or authority evidence.

Verify checksums after any edit:

```sh
python -c "import hashlib,json,pathlib; d=pathlib.Path('.'); m=json.loads((d/'MANIFEST.json').read_text()); [print(f['path'], hashlib.sha256((d/f['path']).read_bytes()).hexdigest()==f['sha256']) for f in m['files']]"
```
