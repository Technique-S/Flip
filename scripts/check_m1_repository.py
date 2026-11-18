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
    for path in git("ls-tree", "-r", "--name-only", M1, "--", "packages").decode().splitlines():
        if "/tests/" in path:
            require(blob("HEAD", path) == blob(M1, path), f"baseline tests changed: {path}")
    require(blob("HEAD", ".gitignore") == blob(CORE, ".gitignore"), ".gitignore changed")
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
    for path in tracked:
        raw = (ROOT / path).read_bytes()
        require(len(raw) <= 200_000, f"unexpected large tracked file: {path}")
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
