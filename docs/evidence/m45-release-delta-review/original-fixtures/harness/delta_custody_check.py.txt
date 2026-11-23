import subprocess, hashlib, os, json
REPO = r"C:\Users\Kazi\Documents\Flip\repo"
WT = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-delta-review"
RESEARCH = "82e25deef9ae3498f837e188a7faed0ed61cd7ff"

def git(*a):
    return subprocess.check_output(["git","-C",REPO,*a])

names = git("ls-tree","-r","--name-only",RESEARCH,
            "docs/evidence/m45-release-acceptance","fixtures/m45-release-acceptance").decode().strip().split("\n")
print("RESEARCH_FILE_COUNT", len(names))
bad = []
for n in names:
    orig = git("show", f"{RESEARCH}:{n}")
    archived = n.replace("fixtures/m45-release-acceptance/","docs/evidence/m45-release-acceptance/original-fixtures/")
    p = os.path.join(WT, archived)
    if not os.path.exists(p):
        bad.append(f"MISSING {archived}"); continue
    cur = open(p,"rb").read()
    if cur != orig:
        bad.append(f"BYTE_DIFF {archived}")
    print(("OK " if cur==orig else "BAD"), archived, len(cur), hashlib.sha256(cur).hexdigest()[:16])

fp = os.path.join(WT,"docs/evidence/m45-release-acceptance/original-fixtures/claim-negative-cases.json")
fb = open(fp,"rb").read()
h = hashlib.sha256(fb).hexdigest()
print("FIXTURE_SHA256", h)
print("FIXTURE_SHA_MATCH", h=="c50aa3012f228ecbfc09c56f2415f38cb3adaa5b739adc3f4b799f21bbce988f")
cases = json.loads(fb)
print("CASE_COUNT", len(cases["cases"]))
print("FIXTURE_STATUS", cases.get("status"), cases.get("provenance"))

# net effect on runtime fixture namespace vs reviewed delivery
d = git("diff","--name-status","1783b61fefc41007b745753b09c4e0e70a8af7f7",
        "22e781d454336cb2067aca1ce7f8cf66809f0f4d","--","fixtures/").decode().strip()
print("RUNTIME_FIXTURE_NAMESPACE_DIFF", repr(d))

if bad:
    print("PROBLEMS", bad); raise SystemExit(1)
print("RESEARCH_CUSTODY_OK")
