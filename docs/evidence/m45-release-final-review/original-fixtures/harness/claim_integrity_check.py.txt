import json, os, re, sys

BASE = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-final-review"
DIST = os.path.join(BASE, "apps", "showcase", "dist")
ART = os.path.join(DIST, "artifacts")
CASES = json.load(open(r"C:\Users\Kazi\Documents\Flip\flip-m45-release-acceptance\fixtures\m45-release-acceptance\claim-negative-cases.json", encoding="utf-8"))
RENDERED = json.load(open(r"C:\Users\Kazi\AppData\Local\Temp\opencode\showcase_rendered_text.json", encoding="utf-8"))

alltext = "\n".join(RENDERED.values())

def has(pattern, text=alltext, flags=re.I):
    return bool(re.search(pattern, text, flags))

# For each case: forbidden claim fragments that must NOT be asserted, and safe assertions that MUST be present.
def affirmative_current_claim(text):
    # A CURRENT claim is affirmative only if not used inside an explicit negation
    neg = re.compile(r"(no|not|never|without)\b[\w\s,\-]{0,45}$", re.I)
    for m in re.finditer(r"\bCURRENT\b", text, re.I):
        prefix = text[max(0, m.start()-45):m.start()]
        if neg.search(prefix) or re.search(r"no\s+current-chain\s+or\s+authorship", prefix, re.I):
            continue
        print("   AFFIRMATIVE_CURRENT_DEBUG prefix=", repr(prefix[-45:]))
        return True
    return False

CASES_CFG = {
 "N-01": {
   "forbidden": [],  # handled by affirmative_current_claim below
   "required": [r"RECORDED\s*·\s*HISTORICAL", r"HISTORICAL"],
 },
 "N-02": {
   "forbidden": [r"all declared test vectors passed", r"EQUIVALENT\s*:\s*all declared"],
   "required": [r"not a universal equivalence proof", r"illustrate the interface"],
 },
 "N-03": {
   "forbidden": [r"Bundle checksum validated, therefore", r"checksum.{0,40}therefore.{0,20}EQUIVALENT"],
   "required": [r"File checksums detect byte changes", r"not authorship or truth", r"Integrity is not proof authority"],
 },
 "N-04": {
   "forbidden": [r"deployment succeeded", r"deployed onchain", r"publication succeeded", r"STOP_AUTHORIZATION means deployment"],
   "required": [r"Publication is outside this showcase", r"There is no publication control here", r"STOP_AUTHORIZATION"],
 },
 "N-05": {
   "forbidden": [r"Preparation created a verified correction", r"preparation.{0,30}(verified|approved)"],
   "required": [r"verified it against the declared local reference", r"separate verify and apply operations", r"VERIFY_CORRECTION|VERIFIED_CORRECTION"],
 },
 "N-06": {
   "forbidden": [r"STALE report is still current", r"still current verified"],
   "required": [r"A different native engine can reject old evidence", r"preserve it and create new local evidence instead of overriding identity checks", r"HISTORICAL"],
 },
 "N-07": {
   "forbidden": [r"Solver timeout returned EQUIVALENT", r"timeout.{0,30}returned EQUIVALENT"],
   "required": [r"A live timeout would be UNKNOWN", r"DIFFERENT is a result, not an instruction to retry"],
 },
 "N-08": {
   "forbidden": [r"single defective wire", r"the highlighted connection is the single", r"uniquely defective wire"],
   "required": [r"does not prove which wire is uniquely defective", r"Unique fault claim:\s*false", r"AMBIGUOUS_MULTIPLE_CAUSES"],
 },
 "N-09": {
   "forbidden": [r"Old native-engine evidence proves this platform", r"proves this platform's result"],
   "required": [r"Native runtime", r"different native engine can reject old evidence", r"instead of overriding identity checks"],
 },
 "N-10": {
   "forbidden": [r"complete registry", r"two discovered processors are the complete"],
   "required": [r"not a universal equivalence proof", r"Archived X Layer"],
 },
 "N-11": {
   "forbidden": [r"Wallet connected and circuit published", r"wallet connected", r"published onchain", r"transaction succeeded"],
   "required": [r"No backend, native solver, wallet or RPC connection", r"There is no publication control here", r"no wallet, signer, RPC client, transaction path or permission grant"],
 },
 "N-12": {
   "forbidden": [r"grant permission to publish", r"checksum grant.{0,20}permission", r"alias.{0,30}permission to publish"],
   "required": [r"not authorship, current chain state or signing permission", r"not authorship or truth", r"does not select or modify a project"],
 },
}

problems = []
print("=== 12 MISLEADING-CLAIM NEGATIVE CASES ===")
for c in CASES["cases"]:
    cid = c["id"]
    cfg = CASES_CFG[cid]
    forb_hits = [p for p in cfg["forbidden"] if has(p)]
    if cid == "N-01" and affirmative_current_claim(alltext):
        forb_hits.append("affirmative CURRENT claim")
    req_missing = [p for p in cfg["required"] if not has(p)]
    ok = not forb_hits and not req_missing
    print(f"{cid} {c['category']}: {'PASS' if ok else 'FAIL'}")
    if forb_hits: print("   FORBIDDEN PRESENT:", forb_hits); problems.append(f"{cid} forbidden claim present")
    if req_missing: print("   REQUIRED MISSING:", req_missing); problems.append(f"{cid} required safe assertion missing")
    print("   expected:", c["expectedClassification"])

# Independent value comparison: displayed values vs accepted source artifacts
receipt = json.load(open(os.path.join(ART,"receipt.json"), encoding="utf-8"))
project = json.load(open(os.path.join(ART,"project.json"), encoding="utf-8"))
evidence = json.load(open(os.path.join(ART,"evidence.json"), encoding="utf-8"))
compare_log = next(l for l in receipt["logs"] if l["step"]=="compare")["output"]
inspect_log = next(l for l in receipt["logs"] if l["step"]=="inspect")["output"]
verify_log = next(l for l in receipt["logs"] if l["step"]=="verify")["output"]
witness = compare_log["report"]["verification"]["witness"]

checks = []
def chk(label, value, page, present=None):
    text = RENDERED[page]
    ok = (str(value) in text) if present is None else present
    checks.append((ok, label, str(value)[:80], page))

chk("witness replay", witness["replay"], "difference.html")
chk("witness input bits", witness["inputs"]["bits"], "difference.html")
chk("witness reference bits", witness["referenceOutputs"]["bits"], "difference.html")
chk("witness candidate bits", witness["candidateOutputs"]["bits"], "difference.html")
chk("compare coverage", compare_log["coverage"], "difference.html")
chk("engineHash", compare_log["engineHash"], "difference.html")
chk("requestHash", compare_log["requestHash"], "difference.html")
chk("solverBackend", compare_log["report"]["verification"]["solverBackend"], "difference.html")
chk("solverOutcome", compare_log["report"]["verification"]["solverOutcome"], "difference.html")
chk("diagnostic attribution", inspect_log["attribution"], "connections.html")
chk("uniqueFaultClaim=false", "Unique fault claim: false", "connections.html", present=("Unique fault claim: false" in RENDERED["connections.html"]))
chk("correction classification", verify_log["classification"], "correction.html")
chk("correction verdict", verify_log["comparison"]["report"]["verification"]["verdict"], "correction.html")
chk("correction solverOutcome", verify_log["comparison"]["report"]["verification"]["solverOutcome"], "correction.html")
chk("project schemaVersion", project["schemaVersion"], "revision.html")
chk("project revisionSequence", project["revision"]["sequence"], "revision.html")
chk("project parentHash", project["revision"]["parentHash"], "revision.html")
chk("project revisionHash", project["revision"]["revisionHash"], "revision.html")
chk("evidence verdict", evidence["comparison"]["report"]["verification"]["verdict"], "evidence.html")
chk("evidence coverage", evidence["comparison"]["coverage"], "evidence.html")
chk("evidence verifiedAt", evidence["comparison"]["verifiedAt"], "evidence.html")
chk("evidence contentHash", evidence["contentHash"], "evidence.html")
chk("evidence limitations", evidence["limitations"][:60], "evidence.html")

print()
print("=== DISPLAYED-VS-ARTIFACT VALUE COMPARISON ===")
for ok,label,val,page in checks:
    print(("OK  " if ok else "FAIL"), f"{label:28s}", page, "=", val)
    if not ok: problems.append("value mismatch: "+label)

# Manifest values
manifest = json.load(open(os.path.join(ART,"manifest.json"), encoding="utf-8"))
for label,val,page in [("acceptedRuntimeSha",manifest["acceptedRuntimeSha"],"index.html"),
                       ("r2AuditSha",manifest["r2AuditSha"],"index.html"),
                       ("recordedDifferenceAt",manifest["recordedDifferenceAt"],"evidence.html"),
                       ("recordedEquivalentAt",manifest["recordedEquivalentAt"],"evidence.html")]:
    ok = str(val) in RENDERED[page]
    print(("OK  " if ok else "FAIL"), f"{label:28s}", page, "=", str(val)[:80])
    if not ok: problems.append("value mismatch: "+label)

print()
print("=== FACTS FROM ARTIFACTS ===")
print("freshness=", evidence["comparison"]["report"]["integrity"]["freshness"])
print("compare verdict=", compare_log["report"]["verification"]["verdict"])
print("uniqueFaultClaim=", inspect_log["uniqueFaultClaim"])
print("diagnostic classification=", inspect_log.get("classification"))
print("stop/signingCapability present in receipt:", "signingCapability" in json.dumps(receipt))
print("candidate expandedGates=", json.loads(open(os.path.join(ART,"composition.json"),encoding="utf-8").read())["candidate"]["manifest"]["expandedGates"])

if problems:
    print("PROBLEMS:", problems); sys.exit(1)
print("ALL_CLAIM_INTEGRITY_CHECKS_OK")
