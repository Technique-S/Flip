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
                in (M3C_REPORT_ONLY_TEST_SHA, M4C_REPORT_ONLY_TEST_SHA, M45_REPORT_ONLY_TEST_SHA)
            )
            require(
                blob("HEAD", path) == blob(M3_A, path) or corrected, f"M3-A test altered: {path}"
            )
    for path in git("diff", "--name-only", M3_B + "^", M3_B).decode().splitlines():
        require(blob("HEAD", path) == blob(M3_B, path), f"M3-B evidence altered: {path}")
        require((ROOT / path).read_bytes() == blob(M3_B, path), f"M3-B checkout altered: {path}")
    require(not git("diff", M3_A, "HEAD", "--", "docs/schema/m3/1.0.0"), "M3 wire schemas changed")
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
        require(len(raw) <= 200_000 or large_registered, f"unexpected large tracked file: {path}")
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
