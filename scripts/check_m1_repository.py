"""Offline M1 Git/evidence review. No historical artifact is rewritten."""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = "37c39b3cf06edad908a6c579b7b0a78f1b42c202"
CORE = "6dc21e0b97ffe03273a62ea1e9499e6346244d32"
FIXTURES = "e4de86ef8870fb9b85adf94ace400791a479f985"
M1 = "8e9b6b928b5d08b7383ae2413dec26d6068ea44e"
M2_A = "e5c47e55ff1600a62ef2cb96c19abb51b33d32f5"
M2_B = "3cdbf14f59eb842f395da368e2e08d1f5708aa28"
M3_A = "d4adf809f2576a1e14e64adce0b04c914049a50f"
M3_B = "4822a05163166ec67b791328e2d1de490fa1c35f"
# M2-C narrows the historical REPORT_ONLY assertion to permit registered synthetic
# adversarial JSON. Pin that exact reviewed correction; all other baseline tests
# remain byte-identical. No test is removed/skipped and historical gaps stay gaps.
M2C_REPORT_ONLY_TEST_SHA = "5f6cb596e5e669c4efe64fc270391768645bde6207a8fef4812e2040f4f9eaf2"
M2C_TEST_CORRECTION = {"packages/flip-core/tests/test_m1_integration.py": M2C_REPORT_ONLY_TEST_SHA}
M4C_REPORT_ONLY_TEST_SHA = "81ffaa464609a66d2356104a1c4db6a0c5f1b81e3cd326f8f114063f46125680"
M3C_REPORT_ONLY_TEST_SHA = "f29d3b9983ee9df7472d9a7ac306ab1032d4a1182c75391048acf029dc853f49"
# Only registers the independently hash-verified M45 synthetic fixture namespace.
M45_REPORT_ONLY_TEST_SHA = "246cc510a2cd9c0c2e1c037dbfde887e8fea0683efd1fbcdca8ebeb96695919a"
# Registers only the immutable, independently hash-verified debugging corpus namespace.
M45_DEBUG_REPORT_ONLY_TEST_SHA = "ec77774346875877ab7e6c5b887bacc62e788285d15bcac3e2b8658cfc0cea02"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def blob(revision: str, path: str) -> bytes:
    return git("show", f"{revision}:{path}")


def registered_files() -> list[tuple[str, int, str]]:
    text = (ROOT / "docs/evidence/SOURCE_INVENTORY.md").read_text(encoding="utf-8")
    rows = re.findall(
        r"\| `(docs/evidence/(?:raw|derived)/[^`]+)` \| ([\d,]+) \| `([0-9a-f]{64})`",
        text,
    )
    return [(path, int(size.replace(",", "")), digest) for path, size, digest in rows]


def library_review_evidence() -> tuple[dict, list[dict]]:
    """Pin both independent reviews, including manifests, to their original Git blobs."""
    captures = {}
    reviews = []
    for revision, target, scopes in (
        (
            "9741e66ae385979dc0d18c89aec4ec6ed93ff285",
            "dec9420bb76e9245c6740bf3d92031d175e408ec",
            (
                "docs/evidence/m45-library-independent-review/",
                "fixtures/m45-library-independent-review/",
            ),
        ),
        (
            "96187da8718bcf7d14a452685f7de84231895920",
            "786cbca056c6cd61ca0e7a5b61ddbc772a55a800",
            ("docs/evidence/m45-library-final-review/",),
        ),
    ):
        require(
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", revision, "HEAD"], cwd=ROOT
            ).returncode
            == 0,
            f"library review history missing: {revision}",
        )
        paths = git("diff", "--name-only", target, revision).decode().splitlines()
        require(len(paths) == 16, f"unexpected review inventory: {revision}")
        require(all(p.startswith(scopes) for p in paths), "review ownership breach")
        archived = git("ls-tree", "-r", "--name-only", "HEAD", "--", *scopes)
        require(set(archived.decode().splitlines()) == set(paths), "review inventory changed")
        for path in paths:
            original = blob(revision, path)
            require(blob("HEAD", path) == original, f"library review altered: {path}")
            require((ROOT / path).read_bytes() == original, f"review checkout altered: {path}")
            if path.endswith(".png"):
                require(original.startswith(b"\x89PNG\r\n\x1a\n"), "invalid review capture")
                captures[path] = (len(original), hashlib.sha256(original).hexdigest())
        manifest_path = scopes[0] + "RESULTS_MANIFEST.json"
        entries = json.loads(blob(revision, manifest_path))["files"]
        require(len(entries) == 15, "unexpected review manifest size")
        require(
            {entry["path"] for entry in entries} == set(paths) - {manifest_path},
            "review manifest coverage mismatch",
        )
        for entry in entries:
            raw = blob(revision, entry["path"])
            require(
                len(raw) == entry["bytes"] and hashlib.sha256(raw).hexdigest() == entry["sha256"],
                f"review manifest mismatch: {entry['path']}",
            )
        reviews.append({"revision": revision, "target": target, "files": len(paths)})
    return captures, reviews


def debugging_fixture_evidence() -> dict:
    revision = "8fc4efb71cb750cced98b4e88540796d665b616a"
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"], cwd=ROOT
        ).returncode
        == 0,
        "debugging fixture history missing",
    )
    paths = git("diff", "--name-only", revision + "^", revision).decode().splitlines()
    require(len(paths) == 15, "debugging fixture inventory changed")
    require(
        all(
            p.startswith(("fixtures/m45-debugging/", "docs/evidence/m45-debugging/")) for p in paths
        ),
        "debugging fixture ownership breach",
    )
    for path in paths:
        require(blob("HEAD", path) == blob(revision, path), f"debugging evidence altered: {path}")
        require(
            (ROOT / path).read_bytes() == blob(revision, path),
            f"debugging checkout altered: {path}",
        )
    manifest = json.loads(blob(revision, "fixtures/m45-debugging/MANIFEST.json"))
    require(len(manifest["files"]) == 9, "debugging manifest inventory mismatch")
    for entry in manifest["files"]:
        path = "fixtures/m45-debugging/" + entry["path"]
        require(path in paths, "unregistered debugging manifest path")
        raw = blob(revision, path)
        require(
            len(raw) == entry["bytes"] and hashlib.sha256(raw).hexdigest() == entry["sha256"],
            f"debugging manifest mismatch: {path}",
        )
    return {"revision": revision, "files": len(paths), "manifestEntries": 9}


def debugging_review_evidence() -> dict:
    """Preserve the final independent review without rewriting its findings or fixtures."""
    revision = "fe807d3eb2bf7752973468c8ec9441c1691b1209"
    target = "130dd341b622cc0ad68bffe7f6f37bb847de45c8"
    scopes = (
        "docs/evidence/m45-debugging-independent-review/",
        "fixtures/m45-debugging-independent-review/",
    )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"], cwd=ROOT
        ).returncode
        == 0,
        "independent debugger review history missing",
    )
    paths = git("diff", "--name-only", target, revision).decode().splitlines()
    require(
        len(paths) == 67 and all(p.startswith(scopes) for p in paths),
        "debugger review inventory/ownership changed",
    )
    require(
        set(git("ls-tree", "-r", "--name-only", "HEAD", "--", *scopes).decode().splitlines())
        == set(paths),
        "debugger review archive inventory changed",
    )
    # Read all pinned/current blobs with one Git process. Avoid adding hundreds of
    # process startups to the tracked Windows Git-custody runtime-margin issue.
    queries = [(ref, path) for path in paths for ref in (revision, "HEAD")]
    raw = subprocess.check_output(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input="".join(f"{ref}:{path}\n" for ref, path in queries).encode(),
    )
    cursor, blobs = 0, {}
    for ref, path in queries:
        end = raw.index(b"\n", cursor)
        header = raw[cursor:end].split()
        require(len(header) == 3 and header[1] == b"blob", f"missing review blob: {path}")
        size = int(header[2])
        cursor = end + 1
        blobs[ref, path] = raw[cursor : cursor + size]
        require(
            len(blobs[ref, path]) == size and raw[cursor + size : cursor + size + 1] == b"\n",
            "invalid review blob frame",
        )
        cursor += size + 1
    require(cursor == len(raw), "unexpected review blob output")
    for path in paths:
        original = blobs[revision, path]
        require(blobs["HEAD", path] == original, f"independent debugger review altered: {path}")
        require(
            (ROOT / path).read_bytes() == original, f"independent debugger checkout altered: {path}"
        )
    manifest_path = scopes[0] + "MANIFEST.json"
    manifest = json.loads(blobs[revision, manifest_path])
    require(manifest["testedSha"] == target, "independent debugger review target changed")
    entries = manifest["files"]
    require(
        len(entries) == 66 and {e["path"] for e in entries} == set(paths) - {manifest_path},
        "independent debugger manifest coverage changed",
    )
    for entry in entries:
        data = blobs[revision, entry["path"]]
        require(
            len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"],
            f"independent debugger manifest mismatch: {entry['path']}",
        )
    return {"revision": revision, "target": target, "files": 67, "manifestEntries": 66}


def agent_workflow_evidence() -> dict:
    revision = "996a300324877d0017cbe0cdb23d8da76692862c"
    scopes = ("fixtures/m45-agent-workflow/", "docs/evidence/m45-agent-workflow/")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"], cwd=ROOT
        ).returncode
        == 0,
        "workflow corpus history missing",
    )
    paths = git("diff", "--name-only", revision + "^", revision).decode().splitlines()
    require(
        len(paths) == 31 and all(p.startswith(scopes) for p in paths),
        "workflow corpus inventory/ownership changed",
    )
    require(
        set(git("ls-tree", "-r", "--name-only", "HEAD", "--", *scopes).decode().splitlines())
        == set(paths),
        "workflow archive inventory changed",
    )
    queries = [(ref, path) for path in paths for ref in (revision, "HEAD")]
    raw = subprocess.check_output(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input="".join(f"{ref}:{path}\n" for ref, path in queries).encode(),
    )
    cursor, blobs = 0, {}
    for ref, path in queries:
        end = raw.index(b"\n", cursor)
        header = raw[cursor:end].split()
        require(len(header) == 3 and header[1] == b"blob", "workflow blob missing")
        size, cursor = int(header[2]), end + 1
        blobs[ref, path] = raw[cursor : cursor + size]
        require(
            len(blobs[ref, path]) == size and raw[cursor + size : cursor + size + 1] == b"\n",
            "invalid workflow blob frame",
        )
        cursor += size + 1
    require(cursor == len(raw), "unexpected workflow blob output")
    for path in paths:
        original = blobs[revision, path]
        require(
            blobs["HEAD", path] == original and (ROOT / path).read_bytes() == original,
            f"workflow evidence changed: {path}",
        )
    manifest = json.loads(blobs[revision, scopes[1] + "MANIFEST.json"])
    require(len(manifest["files"]) == 30, "workflow manifest count changed")
    require(
        {e["path"] for e in manifest["files"]} == set(paths) - {scopes[1] + "MANIFEST.json"},
        "workflow manifest coverage changed",
    )
    for entry in manifest["files"]:
        data = blobs[revision, entry["path"]]
        require(
            len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"],
            f"workflow manifest mismatch: {entry['path']}",
        )
    return dict(revision=revision, files=31, manifestEntries=30)


def agent_workflow_review_evidence():
    """Pin every independent review byte, including logs omitted by its manifest."""
    revision = "7b4b1f711ddc9676141becfae2fc77a3d5941374"
    target = "d2638d057b6236286480891d6fdd7dfb0402bc5a"
    scopes = (
        "docs/evidence/m45-agent-workflow-independent-review/",
        "fixtures/m45-agent-workflow-independent-review/",
    )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"], cwd=ROOT
        ).returncode
        == 0,
        "independent agent review history missing",
    )
    paths = git("diff", "--name-only", target, revision).decode().splitlines()
    require(
        len(paths) == 14 and all(p.startswith(scopes) for p in paths), "agent review scope changed"
    )
    require(
        set(git("ls-tree", "-r", "--name-only", "HEAD", "--", *scopes).decode().splitlines())
        == set(paths),
        "agent review archive inventory changed",
    )
    queries = [(ref, path) for path in paths for ref in (revision, "HEAD")]
    raw = subprocess.check_output(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input="".join(f"{ref}:{path}\n" for ref, path in queries).encode(),
    )
    cursor, blobs = 0, {}
    for ref, path in queries:
        end = raw.index(b"\n", cursor)
        header = raw[cursor:end].split()
        require(len(header) == 3 and header[1] == b"blob", "missing agent review blob")
        size, cursor = int(header[2]), end + 1
        blobs[ref, path] = raw[cursor : cursor + size]
        require(raw[cursor + size : cursor + size + 1] == b"\n", "invalid agent review blob frame")
        cursor += size + 1
    require(cursor == len(raw), "unexpected review blob output")
    original = {}
    for path in paths:
        data = blobs[revision, path]
        require(
            blobs["HEAD", path] == data and (ROOT / path).read_bytes() == data,
            f"independent agent review bytes changed: {path}",
        )
        original[path] = data
    manifest = json.loads(original[scopes[0] + "MANIFEST.json"])
    require(
        manifest["testedSha"] == target and len(manifest["files"]) == 10,
        "agent review manifest changed",
    )
    for entry in manifest["files"]:
        data = original[entry["path"]]
        require(
            len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"],
            f"agent review manifest mismatch: {entry['path']}",
        )
    return original, {"revision": revision, "target": target, "files": 14, "manifestEntries": 10}


def portable_review_evidence():
    """Pin every independent review byte, including logs omitted by its manifest."""
    revision = "8daacf7af2a1cfc17d83a33f7841d1088807ec82"
    target = "136b1115ee0f5ffe0a5583d68c474641fdce1ca1"
    scopes = (
        "docs/evidence/m45-portable-independent-review/",
        "fixtures/m45-portable-independent-review/",
    )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"], cwd=ROOT
        ).returncode
        == 0,
        "independent portable review history missing",
    )
    paths = git("diff", "--name-only", target, revision).decode().splitlines()
    require(
        len(paths) == 18 and all(p.startswith(scopes) for p in paths),
        "portable review scope changed",
    )
    require(
        set(git("ls-tree", "-r", "--name-only", "HEAD", "--", *scopes).decode().splitlines())
        == set(paths),
        "portable review archive inventory changed",
    )
    queries = [(ref, path) for path in paths for ref in (revision, "HEAD")]
    raw = subprocess.check_output(
        ["git", "cat-file", "--batch"],
        cwd=ROOT,
        input="".join(f"{ref}:{path}\n" for ref, path in queries).encode(),
    )
    cursor, blobs = 0, {}
    for ref, path in queries:
        end = raw.index(b"\n", cursor)
        header = raw[cursor:end].split()
        require(len(header) == 3 and header[1] == b"blob", "missing portable review blob")
        size, cursor = int(header[2]), end + 1
        blobs[ref, path] = raw[cursor : cursor + size]
        require(
            raw[cursor + size : cursor + size + 1] == b"\n", "invalid portable review blob frame"
        )
        cursor += size + 1
    require(cursor == len(raw), "unexpected review blob output")
    original = {}
    for path in paths:
        data = blobs[revision, path]
        require(
            blobs["HEAD", path] == data and (ROOT / path).read_bytes() == data,
            f"independent portable review bytes changed: {path}",
        )
        original[path] = data
    manifest = json.loads(original[scopes[0] + "MANIFEST.json"])
    require(
        manifest["testedSha"] == target and len(manifest["files"]) == 11,
        "portable review manifest changed",
    )
    for entry in manifest["files"]:
        data = original[entry["path"]]
        require(
            len(data) == entry["bytes"] and hashlib.sha256(data).hexdigest() == entry["sha256"],
            f"portable review manifest mismatch: {entry['path']}",
        )
    return original, {"revision": revision, "target": target, "files": 18, "manifestEntries": 11}


def portable_research_evidence():
    import io
    import tarfile

    revision = "2f3d6263edf4e62ad4e94718c99f6c1a79e350a1"
    scopes = ("docs/evidence/m45-portable-project", "fixtures/m45-portable-project")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"], cwd=ROOT
        ).returncode
        == 0,
        "portable research history missing",
    )
    paths = git("ls-tree", "-r", "--name-only", revision, "--", *scopes).decode().splitlines()
    extra = "docs/evidence/m45-portable-project/harness/run_portability_cases.py.txt"
    current = git("ls-tree", "-r", "--name-only", "HEAD", "--", *scopes).decode().splitlines()
    require(set(current) == set(paths) | {extra}, "portable research inventory changed")
    require(not git("diff", revision, "HEAD", "--", *paths), "portable research Git blobs changed")
    # Historical trees predate -text attributes; compare original blobs on Windows too.
    archive = git("-c", "core.autocrlf=false", "archive", revision, "--", *scopes)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as bundle:
        for member in bundle.getmembers():
            if member.isdir():
                continue
            require(member.isfile() and member.name in paths, "unexpected research archive member")
            require(
                (ROOT / member.name).read_bytes() == bundle.extractfile(member).read(),
                f"portable research checkout changed: {member.name}",
            )
    require(
        (ROOT / extra).read_bytes()
        == blob(revision, "fixtures/m45-portable-project/generators/run_portability_cases.py"),
        "portable research harness snapshot changed",
    )
    return dict(revision=revision, files=len(paths), additionalPinnedHarness=extra)


def agent_portable_final_review_evidence():
    revision = "4ad32846a995255105aa027e9809599e2cb9562f"
    scopes = (
        "docs/evidence/m45-agent-portable-final-review",
        "fixtures/m45-agent-portable-final-review",
    )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", revision, "HEAD"], cwd=ROOT
        ).returncode
        == 0,
        "final adapter review history missing",
    )
    paths = git("ls-tree", "-r", "--name-only", revision, "--", *scopes).decode().splitlines()
    current = git("ls-tree", "-r", "--name-only", "HEAD", "--", *scopes).decode().splitlines()
    require(len(paths) == 3 and paths == current, "final adapter review inventory changed")
    for path in paths:
        data = blob(revision, path)
        require(
            blob("HEAD", path) == data and (ROOT / path).read_bytes() == data,
            f"final adapter review bytes changed: {path}",
        )
    return dict(revision=revision, target="9c0c23698dfd1c7045de348da851c28d68f5e22b", files=3)


def review() -> dict:
    # CI must fetch full history, since M1-B need not exist as a remote branch.
    for commit in (CORE, FIXTURES):
        require(git("merge-base", SEED, commit).decode().strip() == SEED, "wrong ancestry")
        require(
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT
            ).returncode
            == 0,
            f"agent commit absent from integration history: {commit}",
        )
    m4b = "52814f5cef02716f4a9e49842ae520cdf7937a31"
    for path in git("diff", "--name-only", m4b + "^", m4b).decode().splitlines():
        require(blob("HEAD", path) == blob(m4b, path), f"M4-B archival file changed: {path}")
        require((ROOT / path).read_bytes() == blob(m4b, path), f"M4-B checkout changed: {path}")
    review_commit = "7a4d85e9d7b280b6a2d11fa4420889f555d499f0"
    for path in (
        git("diff", "--name-only", review_commit + "^", review_commit).decode().splitlines()
    ):
        require(
            blob("HEAD", path) == blob(review_commit, path), f"Independent review altered: {path}"
        )
        require(
            (ROOT / path).read_bytes() == blob(review_commit, path),
            f"Review checkout altered: {path}",
        )
    protected = ("AGENTS.md", "docs/product", "docs/architecture", "docs/audits")
    require(not git("diff", SEED, "HEAD", "--", *protected), "protected seed content changed")
    evidence_paths = git("diff", "--name-only", SEED, FIXTURES).decode().splitlines()
    require(
        all(p.startswith(("docs/evidence/", "fixtures/")) for p in evidence_paths),
        "M1-B ownership breach",
    )
    root_core_paths = {
        ".gitattributes",
        ".gitignore",
        ".python-version",
        "README.md",
        "pyproject.toml",
        "uv.lock",
    }
    require(
        all(
            p in root_core_paths
            or p.startswith(
                (
                    "docs/schema/",
                    "packages/flip-core/",
                    "packages/flip-cli/",
                    "packages/flip-api/",
                    ".github/workflows/",
                )
            )
            for p in git("diff", "--name-only", SEED, CORE).decode().splitlines()
        ),
        "M1-A ownership breach",
    )
    for path in evidence_paths:
        require(blob("HEAD", path) == blob(FIXTURES, path), f"archival evidence altered: {path}")
    # M2 adds runtime modules and promotes the already pinned httpx dependency.
    # Freeze existing wire schemas/examples and canonical rules, not future code.
    frozen = git("ls-tree", "-r", "--name-only", CORE, "--", "docs/schema").decode().splitlines()
    frozen += [
        f"packages/flip-core/src/flip_core/{name}.py"
        for name in ("models", "canonical", "schema_export")
    ]
    require(not git("diff", CORE, "HEAD", "--", *frozen), "frozen M1-A contracts changed")
    for path in git("ls-tree", "-r", "--name-only", M2_A, "--", "packages").decode().splitlines():
        if "/tests/" in path:
            current = blob("HEAD", path)
            baseline = blob(M2_A, path)
            corrected = hashlib.sha256(current).hexdigest() in {
                M2C_TEST_CORRECTION.get(path),
                M45_REPORT_ONLY_TEST_SHA
                if path == "packages/flip-core/tests/test_m1_integration.py"
                else None,
                M45_DEBUG_REPORT_ONLY_TEST_SHA
                if path == "packages/flip-core/tests/test_m1_integration.py"
                else None,
                M4C_REPORT_ONLY_TEST_SHA
                if path == "packages/flip-core/tests/test_m1_integration.py"
                else None,
                M3C_REPORT_ONLY_TEST_SHA
                if path == "packages/flip-core/tests/test_m1_integration.py"
                else None,
            }
            require(current == baseline or corrected, f"baseline tests changed: {path}")
    require(
        not git(
            "diff",
            M2_A,
            "HEAD",
            "--",
            "docs/schema/m2/1.0.0",
            "packages/flip-core/src/flip_core/import_models.py",
        ),
        "M2 wire contract changed",
    )
    for path in git("diff", "--name-only", M2_B + "^", M2_B).decode().splitlines():
        require(
            path.startswith(("fixtures/m2-adversarial/", "docs/evidence/m2-adversarial/")),
            "M2-B ownership breach",
        )
        require(blob("HEAD", path) == blob(M2_B, path), f"M2-B evidence changed: {path}")
        require(
            (ROOT / path).read_bytes() == blob(M2_B, path), f"M2-B checkout bytes changed: {path}"
        )
    require(blob("HEAD", ".gitignore") == blob(CORE, ".gitignore"), ".gitignore changed")
    # Preserve every M3-A test node/file except the exact historical namespace
    # correction above, and retain M3-B's entire independent custody unchanged.
    for path in git("ls-tree", "-r", "--name-only", M3_A, "--", "packages").decode().splitlines():
        if "/tests/" in path:
            corrected = (
                path == "packages/flip-core/tests/test_m1_integration.py"
                and hashlib.sha256(blob("HEAD", path)).hexdigest()
                in (
                    M3C_REPORT_ONLY_TEST_SHA,
                    M4C_REPORT_ONLY_TEST_SHA,
                    M45_REPORT_ONLY_TEST_SHA,
                    M45_DEBUG_REPORT_ONLY_TEST_SHA,
                )
            )
            require(
                blob("HEAD", path) == blob(M3_A, path) or corrected, f"M3-A test altered: {path}"
            )
    for path in git("diff", "--name-only", M3_B + "^", M3_B).decode().splitlines():
        require(blob("HEAD", path) == blob(M3_B, path), f"M3-B evidence altered: {path}")
        require((ROOT / path).read_bytes() == blob(M3_B, path), f"M3-B checkout altered: {path}")
    require(not git("diff", M3_A, "HEAD", "--", "docs/schema/m3/1.0.0"), "M3 wire schemas changed")
    library_v1 = "60d9e94c4cfec9306492cb4016c4c6b60444a73f"
    require(
        not git("diff", library_v1, "HEAD", "--", "docs/schema/m45-library/1.0.0"),
        "frozen library 1.0 schemas changed",
    )
    require(
        blob("HEAD", "packages/flip-core/src/flip_core/library_models_v1.py")
        == blob(library_v1, "packages/flip-core/src/flip_core/library_models.py"),
        "frozen library 1.0 model implementation changed",
    )
    research = "5c7bcfbc8babb58d5f040fe869e2017f4a8c46fd"
    for path in git("diff", "--name-only", research + "^", research).decode().splitlines():
        require(blob("HEAD", path) == blob(research, path), f"M45 research altered: {path}")
        require((ROOT / path).read_bytes() == blob(research, path), f"M45 checkout altered: {path}")
    require(b"/docs/evidence/raw/\n" in blob("HEAD", ".gitignore"), "raw ignore rule removed")
    tracked = git("ls-files", "-z").decode().strip("\0").split("\0")
    rows = registered_files()
    require(len(rows) == 14, "expected 12 raw and 2 derived registrations")
    results = []
    for path, size, expected in rows:
        data = blob("HEAD", path)
        require(path in tracked, f"registered artifact is not tracked: {path}")
        require(len(data) == size, f"size mismatch: {path}")
        require(hashlib.sha256(data).hexdigest() == expected, f"Git blob hash mismatch: {path}")
        require((ROOT / path).read_bytes() == data, f"checkout altered evidence bytes: {path}")
        if path.endswith("gate_a_compose_rerun.json"):
            require(data.startswith(b"\xff\xfe"), "UTF-16 LE BOM missing")
            json.loads(data.decode("utf-16"))
        results.append({"path": path, "bytes": size, "sha256": expected})
    raw_tracked = [p for p in tracked if p.startswith("docs/evidence/raw/")]
    require(len(raw_tracked) == 12, "unexpected tracked raw file")
    ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", "docs/evidence/raw/unregistered.json"],
        cwd=ROOT,
    )
    require(ignored.returncode == 0, "unregistered raw data is no longer ignored")

    patterns = [
        re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,})\b"),
        re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
        re.compile(
            r"(?:private[_-]?key|mnemonic|seed[_-]?phrase|password|api[_-]?key|access[_-]?token)"
            r"[\"']?\s*[:=]\s*[\"']([A-Za-z0-9+/_=-]{12,})",
            re.IGNORECASE,
        ),
    ]
    # Only these visually inspected synthetic browser captures are admitted as binary.
    # Pin exact bytes rather than allowing an arbitrary image/binary namespace.
    captures = {
        "docs/milestones/m45-library-browser/desktop.png": (
            106119,
            "5c5b21fe87e4031fdcf1b05671763479a49a1dbf0eef5a63ec8463f1b9f82c98",
        ),
        "docs/milestones/m45-library-browser/mobile.png": (
            78765,
            "a760c451e91f9f766d29c29a5726756aa199f634fe8dc7bdf59a371fee55a8ba",
        ),
    }
    review_captures, library_reviews = library_review_evidence()
    captures.update(review_captures)
    debugging_fixtures = debugging_fixture_evidence()
    debugging_review = debugging_review_evidence()
    workflow_fixtures = agent_workflow_evidence()
    workflow_review_blobs, workflow_review = agent_workflow_review_evidence()
    portable_review_blobs, portable_review = portable_review_evidence()
    portable_research = portable_research_evidence()
    final_adapter_review = agent_portable_final_review_evidence()
    for path in tracked:
        raw = (ROOT / path).read_bytes()
        if path in captures:
            size, digest = captures[path]
            require(
                len(raw) == size and hashlib.sha256(raw).hexdigest() == digest,
                f"registered browser capture changed: {path}",
            )
            require(raw == blob("HEAD", path), f"browser capture checkout changed: {path}")
            require(raw.startswith(b"\x89PNG\r\n\x1a\n"), f"invalid PNG capture: {path}")
            continue
        large_registered = (
            path == "fixtures/m3-verification/benchmarks/benchmark-corpus.json"
            and len(raw) == 534927
            and hashlib.sha256(raw).hexdigest()
            == "795a3b2cccc429dbc9ee3efd1f4eeb5d019974eeb64b34249954135d8b4e76f8"
        )
        require(
            len(raw) <= 200_000
            or large_registered
            or path in workflow_review_blobs
            or path in portable_review_blobs,
            f"unexpected large tracked file: {path}",
        )
        text = raw.decode("utf-16" if raw.startswith(b"\xff\xfe") else "utf-8")
        require("\0" not in text, f"unexpected binary: {path}")
        require(
            not path.endswith((".dll", ".pyd", ".exe", ".pyc", ".zip", ".pem", ".key")),
            f"unexpected binary/key filename: {path}",
        )
        require(not any(p.search(text) for p in patterns), f"potential credential in {path}")
    return {
        "scope": "M1 offline repository consistency; not chain verification or solver replay",
        "seed": SEED,
        "core": CORE,
        "fixtures": FIXTURES,
        "raw_files": 12,
        "registered_blob_checks": results,
        "tracked_files_scanned": len(tracked),
        "credential_pattern_findings": 0,
        "registered_browser_captures": sorted(captures),
        "library_independent_reviews": library_reviews,
        "debugging_fixture_evidence": debugging_fixtures,
        "debugging_independent_review": debugging_review,
        "agent_workflow_fixtures": workflow_fixtures,
        "agent_workflow_independent_review": workflow_review,
        "portable_independent_review": portable_review,
        "portable_research": portable_research,
        "agent_portable_final_review": final_adapter_review,
        "provenance_limit": "Audited originals unavailable; imported observations are historical.",
        "result": "PASS",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-clean", action="store_true")
    if parser.parse_args().require_clean:
        require(
            not git("status", "--porcelain"), "repository contains staged/unstaged/untracked files"
        )
    print(json.dumps(review(), indent=2))
