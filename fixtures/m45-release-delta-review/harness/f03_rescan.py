import os, hashlib
WT = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-delta-review"
TARGETS = {
 "b651a99486cbb6c7b053087b94ac9072f7dd9b0d4aae307b03e700441455c730": "R2 source receipt",
 "2b77b5c59b07c2e135a55b805112c364ce87bde7bf64370b728c881b423ea46c": "R2 source replay request",
 "112b7f261b3603dc18d95413fe206a492ec04828266fda4545bce83fdc9fd048": "recorded project revision",
}
found = {k: [] for k in TARGETS}
n=0
for dp,dn,fn in os.walk(WT):
    dn[:] = [d for d in dn if d not in (".git",".venv","node_modules","dist")]
    for f in fn:
        p=os.path.join(dp,f)
        try: b=open(p,"rb").read()
        except Exception: continue
        n+=1
        h=hashlib.sha256(b).hexdigest()
        if h in found: found[h].append(os.path.relpath(p,WT))
print("SCANNED",n)
for h,label in TARGETS.items():
    hits=[x for x in found[h] if "recordings/" not in x.replace("\\","/")]
    print(label, "->", hits if hits else "NO INDEPENDENT ORIGINAL OUTSIDE recordings/")
