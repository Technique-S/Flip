import os, re, json, sys

DIST = r"C:\Users\Kazi\Documents\Flip\flip-m45-release-final-review\apps\showcase\dist"
findings = []
html_files = []
ext_count = {}
for dirpath, dirnames, filenames in os.walk(DIST):
    for fn in filenames:
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, DIST).replace("\\", "/")
        ext = os.path.splitext(fn)[1].lower()
        ext_count[ext] = ext_count.get(ext, 0) + 1
        if os.path.islink(full):
            findings.append(f"SYMLINK: {rel}")
        with open(full, "rb") as f:
            b = f.read()
        if b[:4] in (b"MZ\x90\x00", b"\x7fELF", b"\xca\xfe\xba\xbe", b"PK\x03\x04"):
            findings.append(f"EXECUTABLE_OR_ARCHIVE_MAGIC: {rel}")
        if rel.endswith(".html"):
            html_files.append((rel, b.decode("utf-8", "replace")))

print("EXTENSION_COUNTS", json.dumps(ext_count, sort_keys=True))
print("HTML_FILES", len(html_files))

# CSP and script/active-content checks per HTML page
CSP_REQUIRED = ["default-src 'none'", "script-src 'none'", "connect-src 'none'",
                "object-src 'none'", "frame-src 'none'", "worker-src 'none'",
                "base-uri 'none'", "form-action 'none'"]
active_pat = re.compile(r"<\s*(script|form|input|button|iframe|object|embed|video|audio|img|svg|base)\b|<\s*link(?![^>]*rel\s*=\s*['\"]stylesheet['\"])[^>]*\bhref\s*=<\s*meta[^>]*http-equiv\s*=\s*['\"]refresh['\"]|\son[a-z]+\s*=|javascript\s*:", re.I)
href_pat = re.compile(r'\bhref\s*=\s*"([^"]*)"', re.I)
src_pat = re.compile(r'\bsrc\s*=\s*"([^"]*)"', re.I)
for rel, s in html_files:
    for tok in CSP_REQUIRED:
        if tok not in s:
            findings.append(f"CSP_MISSING[{rel}]: {tok}")
    m = active_pat.search(s)
    if m:
        findings.append(f"ACTIVE_CONTENT[{rel}]: {m.group(0)[:80]}")
    for h in href_pat.findall(s):
        if re.match(r"^[a-z][\w+.-]*:", h, re.I):
            findings.append(f"NONLOCAL_HREF[{rel}]: {h}")
        if "\\" in h or "%" in h:
            findings.append(f"SUSPICIOUS_HREF[{rel}]: {h}")
    for x in src_pat.findall(s):
        findings.append(f"SRC_ATTRIBUTE[{rel}]: {x}")
    if "RECORDED · HISTORICAL" not in s:
        findings.append(f"MISSING_HISTORICAL_LABEL[{rel}]")

# CSS external resources
for dirpath, dirnames, filenames in os.walk(DIST):
    for fn in filenames:
        if fn.endswith(".css"):
            s = open(os.path.join(dirpath, fn), encoding="utf-8").read()
            if re.search(r"url\s*\(|@import", s, re.I):
                findings.append(f"CSS_EXTERNAL_RESOURCE: {fn}")

# Network / control keywords across generated text (informational; JSON is historical evidence)
pat = re.compile(r"https?://|wss?://|fetch\s*\(|XMLHttpRequest|WebSocket|EventSource|sendBeacon|eth_send|wallet|signMessage|personal_sign|broadcast|tapeout\s*\(", re.I)
hits = {}
for dirpath, dirnames, filenames in os.walk(DIST):
    for fn in filenames:
        rel = os.path.relpath(os.path.join(dirpath, fn), DIST).replace("\\", "/")
        s = open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace").read()
        found = sorted(set(m.group(0).lower() for m in pat.finditer(s)))
        if found:
            hits[rel] = found
print("NETWORK_CONTROL_KEYWORD_HITS", json.dumps(hits, indent=2, sort_keys=True))

if findings:
    print("FINDINGS:")
    for f in findings:
        print(" -", f)
    sys.exit(1)
print("STATIC_SECURITY_SCAN_OK")
