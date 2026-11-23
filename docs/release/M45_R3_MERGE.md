# M4.5-R3-E — Documentation resolution and integration record

Prepared 2026-11-23 for [PR #11](https://github.com/Technique-S/Flip/pull/11).
Development/release-package merge is authorized after exact-head verification and green
Windows/Linux CI. Deployment, hosting, submission and public release remain outside scope.
The final head, CI outcomes, merge SHA and post-merge main SHA are recorded on the PR;
this document does not attempt to contain its own commit SHA.

## Independent decision and remaining findings

The final independent delta review is OpenCode commit
`2b403ea86b8b2941aaa9adfd0d25a97c78d36ec6`, reviewing PR head
`22e781d454336cb2067aca1ce7f8cf66809f0f4d` against original showcase delivery
`1783b61fefc41007b745753b09c4e0e70a8af7f7`. It gives **CONDITIONAL PASS**, safe to
merge as a development/release-package change after the documentation conditions.
The previous independent review is `10fb6ca5798142d7d6a372e491aebd47d3bfb79f`.
Neither review is rewritten or upgraded to an unconditional PASS by this integration.

| Finding | Disposition |
|---|---|
| F-01 | README distinguishes runtime-only baseline `b537eb6ca9de63f24a69fd5d837ccbc8e02f3a3b`, original showcase delivery `1783b61fefc41007b745753b09c4e0e70a8af7f7`, reproducible reviewed package `22e781d454336cb2067aca1ce7f8cf66809f0f4d`, and PR #11's final integration. Both setup paths use the showcase-bearing package pin and link its installation guide and acceptance record. |
| F-02 | The source-pinned setup checklist is unchecked and narrowed to independent first-time validation on Windows/Linux. Documentation fixes and automated checks do not establish a clean novice install. |
| F-03 | Preserved explicitly in README: independent reviewers could not locate original R2 receipt/replay/project files outside the curated recordings. Pinned recording bytes are intact; independent original-versus-copy verification remains unavailable. No missing original is fabricated and no recording is relabeled CURRENT. |

The [earlier acceptance record](M45_R3_ACCEPTANCE.md) remains a preparation snapshot.
Its pending-review wording describes that earlier stage. This record and the unchanged
independent reports document the later conditional acceptance and documentation fixes.

## History and byte custody

Both original review commits are retained as parents of ordinary merge commits on the
release branch. PR #11 uses the repository's merge-commit strategy, retaining those
ancestors on main. No squash or rewritten reviewer history is used.

Original reports remain at
[previous review](../evidence/m45-release-final-review/M45_R3_INDEPENDENT_REVIEW.md) and
[final delta review](../evidence/m45-release-delta-review/M45_R3_FINAL_DELTA_REVIEW.md).
Their findings, conclusions and historical source-path references are unchanged.

Directly importing their synthetic JSON under `fixtures/` would violate the existing
runtime corpus restriction; importing Python harnesses as runnable `.py` would expose
archival code to repository lint/discovery. This conflict is resolved by archiving those
files under each report's `original-fixtures/` directory, with `.txt` appended to Python
and JavaScript harness names. Contents are byte-identical. The original paths remain
available in the original Git commits. No production fixture allowlist, test, lint
exemption, schema, dependency or existing custody registration changes.

[Review custody manifest](M45_R3_REVIEW_CUSTODY.json) maps all fourteen files to their
original revision/path, current archive path, byte length and SHA-256. Reproduce custody
with Python from the source root; full Git history is required:

```python
import hashlib, json, pathlib, subprocess
for f in json.loads(pathlib.Path("docs/release/M45_R3_REVIEW_CUSTODY.json").read_text())["files"]:
    raw = subprocess.check_output(["git", "show", f["revision"] + ":" + f["sourcePath"]])
    assert pathlib.Path(f["archivePath"]).read_bytes() == raw
    assert len(raw) == f["bytes"]
    assert hashlib.sha256(raw).hexdigest() == f["sha256"]
print("PASS: all 14 original review files retained unchanged")
```

## Verification and merge gates

Run README/release link checks, reproduce the README's exact checkout in a fresh clone,
regenerate static output with `--check`, run all nineteen showcase tests and the existing
no-script/no-network integrity checks, and run repository custody/credential scans.
The fresh showcase checkout checks Node build/view instructions; it does not claim
independent first-time native setup on both OSes. Required full Windows/Linux CI must
pass for the exact final head before PR #11 is marked ready and merged.

Against reviewed head `22e781d454336cb2067aca1ce7f8cf66809f0f4d`, the final change
is documentation/evidence plus explicit evidence line-ending rules. `apps/showcase`,
production packages, `apps/web`, schemas, dependencies, recordings, checks and CI remain
unchanged. Substantive showcase/production changes would require independent delta
review before merging; none is planned in this integration.

After merge, synchronize main, verify the reviewed ancestry and protected-path equality,
rebuild/check the static output, run smoke and custody checks, and record exact merge
and main SHAs on PR #11. Do not deploy, publish, submit, select a license, redistribute
native binaries or add wallet/signing/broadcast/public-native-hosting functionality.

## Public and hackathon release blockers

Still unresolved: own-source license and third-party/content rights; organizer-confirmed
judge-access method and rehearsal; human novice installation and auditory screen-reader
trials; final captioned video, final copy and eligibility/contact/rights declarations;
owner approval for any distribution, hosting or submission. Engineering merge acceptance
does not clear those gates. The static showcase remains recorded and historical, with
no interactive proof engine, API/RPC/wallet calls or publication capability.
