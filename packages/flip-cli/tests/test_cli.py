import json
import subprocess
import sys
from pathlib import Path

import pytest
from flip_core.canonical import canonical_bytes, content_hash
from flip_core.contracts import validate_contract

ROOT = Path(__file__).resolve().parents[3]


def cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "flip_cli", *map(str, args)], capture_output=True, check=False
    )


@pytest.mark.parametrize(
    "command",
    [
        "sample",
        "import",
        "inspect",
        "compose",
        "compare",
        "preflight",
        "revalidate",
        "export",
        "verify-bundle",
    ],
)
def test_reserved_operations(command, tmp_path):
    target = tmp_path / "never-created.bin"
    result = cli(command, "--out", target)
    assert result.returncode == 6
    assert json.loads(result.stdout)["error"]["code"] == "NOT_IMPLEMENTED"
    assert not target.exists()


def test_contract_commands():
    path = ROOT / "docs/schema/examples/project.json"
    model = validate_contract("project", path.read_bytes())
    result = cli("canonical", "project", path)
    assert result.returncode == 0
    assert result.stdout == canonical_bytes(model) + b"\n"
    result = cli("hash", "project", path)
    assert result.returncode == 0
    assert json.loads(result.stdout)["hash"] == content_hash(model)


@pytest.mark.parametrize("args", [[], ["wat"], ["validate", "project", "absent.json"]])
def test_invalid_arguments_structured(args):
    result = cli(*args)
    assert result.returncode == 3
    assert json.loads(result.stdout)["error"]["code"] == "INVALID_INPUT"


def test_wrong_chain_cli(tmp_path):
    path = tmp_path / "wrong.json"
    path.write_text('{"schemaVersion":"1.0.0","chainId":8453}')
    result = cli("validate", "circuit-identity", path)
    assert result.returncode == 3
    assert json.loads(result.stdout)["error"]["code"] == "WRONG_CHAIN"
