"""P26 tests: percentis coerentes, isolamento e teto de deploy."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p26_perf.bench import (
    OverBudget,
    benchmark,
    budget_check,
    deployment_report,
    run_concurrent,
)


def doubling_graph_invoke(payload: dict, _config: dict) -> dict:
    """Grafo demo inline: dobra sem depender de outro projeto."""
    return {"doubled": payload["n"] * 2}


def test_benchmark_reports_coherent_percentiles():
    # Given: 20 repetições do demo
    # When: mede com warmup
    stats = benchmark(
        lambda: doubling_graph_invoke({"n": 1}, {}), repeats=20, warmup=3
    )
    # Then: n certo e ordem coerente
    assert stats["n"] == 20
    assert 0 <= stats["min_ms"] <= stats["p50_ms"] <= stats["max_ms"]
    assert stats["p50_ms"] <= stats["p95_ms"] <= stats["max_ms"]


def test_concurrent_runs_stay_isolated():
    # Given: 4 payloads distintos
    payloads = [{"n": i} for i in [1, 2, 3, 4]]
    # When: concorrência real com thread por payload
    results = run_concurrent(doubling_graph_invoke, payloads)
    # Then: cada resultado certo na sua posição
    assert [r["doubled"] for r in results] == [2, 4, 6, 8]


def test_budget_blocks_above_ceiling_and_passes_below():
    # Given: p50 conhecido
    # When/Then: teto folgado passa, teto apertado barra
    assert budget_check(10.0, 100.0) == 10.0
    with pytest.raises(OverBudget, match="over budget"):
        budget_check(10.0, 5.0)
    assert deployment_report(10.0, 100.0)["deploy"] is True
    assert deployment_report(10.0, 5.0)["deploy"] is False
