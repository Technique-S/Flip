"""Build a declarative, explicit correction example using accepted pinned inputs."""

import argparse
from pathlib import Path

from flip_core.agent_models import WorkflowRequest
from flip_core.canonical import canonical_bytes, content_hash, load_json
from flip_core.debugging import prior_action
from flip_core.verification import parse_request

ROOT = Path(__file__).resolve().parents[1]


def example():
    original = load_json(
        (ROOT / "docs/schema/m45-debugging/examples/swapped-prior.execution.json").read_bytes()
    )
    action = prior_action(parse_request(original))
    bound = dict(expectedExecutionHash=content_hash(original), actionId=action.actionId)
    steps = [
        dict(id="compare", op="compare", continueOn=["DIFFERENT"]),
        dict(id="diagnose", op="inspect", continueOn=["DIFFERENT"]),
        dict(id="proposal", op="propose_correction", expectedExecutionHash=content_hash(original)),
        dict(id="verify", op="verify", source="proposal", **bound),
        dict(id="apply", op="apply", source="verify", **bound),
        dict(id="export", op="export"),
    ]
    return WorkflowRequest.model_validate(dict(executionRequest=original, steps=steps)).model_dump(
        mode="json"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(canonical_bytes(example()) + b"\n")


if __name__ == "__main__":
    main()
