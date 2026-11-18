"""M0.5 benchmark family, freshly checked through the production proof path."""

import pytest
from flip_core.verification import compare
from test_m3_engine import benchmark_request


@pytest.mark.parametrize("target", [50, 100, 250, 500, 1000, 2500, 5000])
@pytest.mark.parametrize(
    "mode,expected",
    [
        ("self", "EQUIVALENT"),
        ("equivalent", "EQUIVALENT"),
        ("different", "DIFFERENT"),
        ("fault_reverse_one", "EQUIVALENT"),
    ],
)
def test_bounded_benchmark(target, mode, expected):
    result = compare(benchmark_request(target, mode))
    assert result["report"]["verification"]["verdict"] == expected, result["resources"]
    assert result["resources"]["peakBytes"] < 64 * 1024**2
    assert result["resources"]["peakMetric"] in ("PRIVATE_COMMIT", "VIRTUAL_ADDRESS_SPACE")
    if expected == "DIFFERENT":
        assert result["report"]["verification"]["witness"]["replay"] == "REF_BEAT_REPRODUCED"
