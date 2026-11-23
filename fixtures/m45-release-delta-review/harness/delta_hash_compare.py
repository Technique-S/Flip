import hashlib, json, os
A = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-final-review\apps\showcase\dist"   # reviewed delivery 1783b61
B = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-delta-review\apps\showcase\dist"    # PR head 22e781d
WT = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-delta-review"

def sha(b): return hashlib.sha256(b).hexdigest()
def files(root):
    out = {}
    for dp,dn,fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp,f)
            out[os.path.relpath(p,root).replace("\\","/")] = open(p,"rb").read()
    return out

a, b = files(A), files(B)
print("FILE_COUNTS", len(a), len(b))
print("SAME_FILE_SET", set(a)==set(b))
diff = [k for k in a if k in b and a[k]!=b[k]]
print("BYTE_DIFFERENCES", diff)

sums = json.loads(b["CHECKSUMS.json"])
bad = []
for name, raw in b.items():
    if name == "CHECKSUMS.json": continue
    if sums[name]["sha256"] != sha(raw) or sums[name]["bytes"] != len(raw):
        bad.append(name)
print("INDEPENDENT_CHECKSUM_MISMATCHES", bad)
inv = json.load(open(os.path.join(WT,"docs/release/M45_R3_ASSET_INVENTORY.json"), encoding="utf-8"))
print("INVENTORY_STATIC_MATCH", inv["staticChecksums"] == sums)
print("MANIFEST_SHA", sha(b["artifacts/manifest.json"]))
build = json.loads(b["BUILD.json"])
print("CAPABILITIES", json.dumps(build["capabilities"], sort_keys=True))
assert set(a)==set(b) and not diff and not bad and inv["staticChecksums"]==sums
print("DELTA_STATIC_OUTPUT_IDENTICAL_OK")
