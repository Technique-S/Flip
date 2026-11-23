import hashlib, json, os, sys

ROOT = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-final-review"
DIST = os.path.join(ROOT, "apps", "showcase", "dist")

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def read(p):
    with open(p, "rb") as f:
        return f.read()

sums = json.loads(read(os.path.join(DIST, "CHECKSUMS.json")).decode("utf-8"))
problems = []
seen = []
for dirpath, dirnames, filenames in os.walk(DIST):
    for fn in filenames:
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, DIST).replace("\\", "/")
        if rel == "CHECKSUMS.json":
            seen.append(rel)
            continue
        seen.append(rel)
        b = read(full)
        h = sha256_bytes(b)
        if rel not in sums:
            problems.append(f"NOT_IN_CHECKSUMS: {rel}")
            continue
        if sums[rel]["sha256"] != h:
            problems.append(f"HASH_MISMATCH: {rel} expected={sums[rel]['sha256']} got={h}")
        if sums[rel]["bytes"] != len(b):
            problems.append(f"LENGTH_MISMATCH: {rel} expected={sums[rel]['bytes']} got={len(b)}")
for name in sums:
    if name not in seen:
        problems.append(f"CHECKSUMS_ENTRIES_MISSING_FILE: {name}")

# Independent manifest hash (the pinned build input)
manifest_bytes = read(os.path.join(DIST, "artifacts", "manifest.json"))
manifest_sha = sha256_bytes(manifest_bytes)

# Read source manifest from recordings (original input)
rec_manifest = read(os.path.join(ROOT, "apps", "showcase", "recordings", "manifest.json"))
rec_manifest_sha = sha256_bytes(rec_manifest)

# BUILD.json source hashes independently recomputed
build = json.loads(read(os.path.join(DIST, "BUILD.json")).decode("utf-8"))
for name, rec in build.get("sourceHashes", {}).items():
    src = read(os.path.join(ROOT, "apps", "showcase", name))
    h = sha256_bytes(src)
    if h != rec:
        problems.append(f"BUILD_SOURCE_HASH_MISMATCH: {name} expected={rec} got={h}")
if build.get("recordingManifestSha256") != manifest_sha:
    problems.append("BUILD_MANIFEST_SHA_MISMATCH")
if build.get("recordingManifestSha256") != rec_manifest_sha:
    problems.append("BUILD_VS_RECORDING_MANIFEST_SHA_MISMATCH")

# Release asset inventory cross-check
inv = json.loads(read(os.path.join(ROOT, "docs", "release", "M45_R3_ASSET_INVENTORY.json")).decode("utf-8"))
if inv.get("staticChecksums") != sums:
    problems.append("INVENTORY_STATIC_CHECKSUMS_MISMATCH")
cm_sha = sha256_bytes(read(os.path.join(DIST, "CHECKSUMS.json")))
if inv.get("staticChecksumManifest", {}).get("sha256") != cm_sha:
    problems.append("INVENTORY_CHECKSUMS_MANIFEST_SHA_MISMATCH")
for name, rec in inv.get("sourceHashes", {}).items():
    p = os.path.join(ROOT, name)
    if not os.path.exists(p):
        problems.append(f"INVENTORY_SOURCE_MISSING: {name}")
        continue
    b = read(p).replace(b"\r\n", b"\n")
    h = sha256_bytes(b)
    if h != rec.get("sha256") or len(b) != rec.get("bytes"):
        problems.append(f"INVENTORY_SOURCE_DRIFT: {name}")

print("FILE_COUNT", len(seen))
print("CHECKSUMS_ENTRIES", len(sums))
print("MANIFEST_SHA256", manifest_sha)
print("RECORDING_MANIFEST_SHA256", rec_manifest_sha)
print("BUILD_CAPABILITIES", json.dumps(build.get("capabilities"), sort_keys=True))
print("INVENTORY_KEYS", sorted(inv.keys()))
if problems:
    print("PROBLEMS:")
    for p in problems:
        print(" -", p)
    sys.exit(1)
print("ALL_INDEPENDENT_HASH_CHECKS_OK")
