import os, re
DIST = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-final-review\apps\showcase\dist"
pat = re.compile(r"pysat|solver_worker|FLIP_LOCAL_SOLVER|minisat|subprocess|spawn\s*\(|Worker\s*\(|\bwasm\b|\bimport\s*\(", re.I)
for dp,dn,fn in os.walk(DIST):
    for f in fn:
        p = os.path.join(dp,f)
        s = open(p, encoding="utf-8", errors="replace").read()
        hits = sorted(set(m.group(0) for m in pat.finditer(s)))
        if hits:
            print(os.path.relpath(p,DIST), "->", hits)
