import os, sys, json, shutil, subprocess, hashlib, tempfile

WT = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-delta-review"
SRC = os.path.join(WT, "apps", "showcase")
DIST = os.path.join(SRC, "dist")
tmp = tempfile.mkdtemp(prefix="flip-delta-tamper-", dir=r"C:\Users\Kazi\AppData\Local\Temp\opencode")
builder = os.path.join(tmp, "build.mjs")
for name in ["build.mjs", "lib.mjs", "style.css"]:
    shutil.copy2(os.path.join(SRC, name), os.path.join(tmp, name))
shutil.copytree(os.path.join(SRC, "recordings"), os.path.join(tmp, "recordings"))

def run():
    p = subprocess.run([subprocess.executable if False else "node", builder],
                       cwd=tmp, capture_output=True, text=True)
    return p.returncode, (p.stderr or "")

# baseline
rc, err = run()
print("BASELINE_RC", rc, err.strip()[:120])
assert rc == 0, "pristine builder must succeed"

# 1) mutate recording bytes
rp = os.path.join(tmp, "recordings", "receipt.json")
raw = open(rp, "rb").read()
data = json.loads(raw)
data["originalExecutionRequest"]["imports"][0]["alias"] = "CURRENT onchain now"
mutated = json.dumps(data).encode()
open(rp, "wb").write(mutated)
if os.path.exists(os.path.join(tmp, "dist")):
    shutil.rmtree(os.path.join(tmp, "dist"))
rc, err = run()
print("MUTATED_RC", rc, "MSG", [l for l in err.splitlines() if "Wrong" in l][:2])
assert rc != 0 and ("Wrong byte length" in err or "Wrong recording checksum" in err)
assert not os.path.exists(os.path.join(tmp, "dist", "index.html")), "no forged page may be generated"

# 2) repin manifest checksum for mutated bytes
mp = os.path.join(tmp, "recordings", "manifest.json")
man = json.loads(open(mp, "rb").read())
for f in man["files"]:
    if f["name"] == "receipt.json":
        f["bytes"] = len(mutated)
        f["sha256"] = hashlib.sha256(mutated).hexdigest()
open(mp, "wb").write(json.dumps(man).encode())
if os.path.exists(os.path.join(tmp, "dist")):
    shutil.rmtree(os.path.join(tmp, "dist"))
rc, err = run()
print("REPINNED_RC", rc, "MSG", [l for l in err.splitlines() if "manifest" in l.lower()][:2])
assert rc != 0 and "Recording manifest differs from the reviewed build input" in err
assert not os.path.exists(os.path.join(tmp, "dist", "index.html")), "no forged page after repin"

# 3) all seven original pages retain framing and contain none of the 12 synthetic claims
cases = json.load(open(os.path.join(WT,"docs/evidence/m45-release-acceptance/original-fixtures/claim-negative-cases.json"), encoding="utf-8"))["cases"]
pages = ["index","composition","difference","connections","correction","revision","evidence"]
for p in pages:
    s = open(os.path.join(DIST, p + ".html"), encoding="utf-8").read()
    assert "RECORDED · HISTORICAL" in s, p
    hits = [c["id"] for c in cases if c["syntheticClaim"] in s]
    assert not hits, (p, hits)
    print("PAGE_OK", p, "framed=True", "claims=0")

print("INDEPENDENT_TAMPER_BOUNDARY_OK")
shutil.rmtree(tmp, ignore_errors=True)
