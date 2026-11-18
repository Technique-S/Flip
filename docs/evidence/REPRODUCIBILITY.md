# Bounded reproducibility — Flip M1-B fixtures

All commands below are read-only with respect to the source experiments and the network. Nothing here connects a wallet, signs, broadcasts, pays a fee, or calls an RPC. Observed environment: Python 3.14.6, Windows 11, Intel64; Git worktree `opencode/flip-m1-fixtures` at base commit `37c39b3cf06edad908a6c579b7b0a78f1b42c202`.

## 0. Paths

```
SRC0 = C:\Users\Kazi\Documents\Flip\experiments
SRC5 = C:\Users\Kazi\Documents\Flip\m05-final-verification\experiments
WT   = C:\Users\Kazi\Documents\Flip\Flip_M1_Engineering_Starter\flip-opencode
```

The canonical `C:\research\circuitforge-feasibility\...` paths do not exist here (see `MISSING_ARTIFACTS.md`); `SRC0`/`SRC5` are the only accessible raw sources.

## 1. Commands actually executed during this task

### 1.1 Source discovery and size inventory (executed)

```powershell
Test-Path 'C:\research\circuitforge-feasibility\experiments'                       # False
Test-Path 'C:\research\circuitforge-feasibility\m05-final-verification\experiments' # False
Get-ChildItem -Force -Recurse -File $SRC0,$SRC5 |
  Select-Object @{N='Bytes';E={$_.Length}},FullName | Sort-Object FullName
```

### 1.2 Secret scan before copying (executed)

```powershell
$pat = '(?i)(private[_-]?key|mnemonic|seed[_-]?phrase|api[_-]?key|secret|password|passwd|BEGIN .*PRIVATE KEY|0x[a-f0-9]{64}|Bearer |Authorization\s*:|keystore)'
$files = Get-ChildItem -File -Recurse $SRC0,$SRC5 |
         Where-Object { $_.Extension -in '.json','.txt','.md','.py' }
foreach($f in $files){ Select-String -Path $f.FullName -Pattern $pat }
```

128 text files scanned; no credentials found. All matches were public netlists, storage slots, hashes, calldata, and bytecode.

### 1.3 Byte-preserving copy with hash equality check (executed)

```powershell
Copy-Item -LiteralPath <source> -Destination <destination> -Force
(Get-FileHash -Algorithm SHA256 <source>).Hash -eq (Get-FileHash -Algorithm SHA256 <destination>).Hash
```

This was run for each of the 12 mappings in `SOURCE_INVENTORY.md` §3; every comparison returned `MATCH`. Source files were never opened for writing.

### 1.4 Read-only re-derivation (executed — the `READ_ONLY_REGENERATED` artifact)

```powershell
cd $WT
python docs\evidence\derived\recompute_checks.py
```

Observed output (abridged to the asserted values):

```
recompute matches: True True True
stateful trace matches embedded copy: True
{ "wiring_mutation_cases": 4, "integrity_negative_cases": 9,
  "all_negative_detected": true, "scale_target_counts": 7,
  "scale_mode_cases": 28, "correctness_safeguards": 7,
  "stateful_beats": 8, "stateful_first_difference_beat": 0,
  "stateful_reproducible": true }
```

The script reads only the committed raw fixtures under `docs/evidence/raw/`, recomputes the XOR#1 / NAND#2 / composed netlist digests with `hashlib.sha256`, counts the negative/mutation/scale/safeguard cases, compares the standalone stateful trace with the copy embedded in `gate_c_scale.json`, and writes `docs/evidence/derived/recomputed_checks.json`. No network access.

### 1.5 Raw-data inspection commands (executed)

```powershell
python -c "import json; v=json.load(open(r'$SRC0\fixtures\vectors.json',encoding='utf-8')); print([(k, len(x) if hasattr(x,'__len__') else x) for k,x in v.items()])"
python -c "import json; p=r'$SRC5\results'; cs=json.load(open(p+r'\gate_c_scale.json',encoding='utf-8')); print([(s['targetGates'],len(s['cases'])) for s in cs['scales']])"
```

These established that `vectors.json` holds 5 valid + 8 ill-formed + 5 packing-edge cases (18 total, matching the audit's "18 vectors" claim) and that the scale matrix is 7 × 4 = 28 cases.

## 2. How a reviewer reproduces the fixture set

1. Check out `opencode/flip-m1-fixtures` (or this commit) in a worktree; keep both `SRC0`/`SRC5` trees read-only.
2. Confirm the host paths with `Test-Path` (§1.1). If the canonical `C:\research` trees are now available, re-run the copy with those as sources and compare SHA-256 values to `SOURCE_INVENTORY.md` §3 — this closes the main provenance blocker.
3. Re-run the secret scan (§1.2) on any newly introduced source.
4. Re-run the byte-preserving copy (§1.3) and require `MATCH` for all 12 artifacts. `gate_a_compose_rerun.json` must remain UTF-16 LE with BOM (do not transcode).
5. Run `python docs\evidence\derived\recompute_checks.py` (§1.4) and require all booleans `True` and all counts as shown in `PROVENANCE_INDEX.md`.

## 3. Explicitly NOT run (out of scope)

- No `eth_call`, RPC endpoint access, chainId verification, or fee read against a live node. All chain values are historical and block-pinned.
- No re-execution of `gate_a_probe*.py`, `gate_b_*.py`, or `gate_c_*.py` experiment scripts and no solver run; their recorded JSON outputs are copied as `RAW_REPLAYED`, not regenerated.
- No `tapeout()` call, transaction, signing, token acquisition, or publication.
- No product build, test suite, schema import, or lockfile/package change. Codex owns those files.
