"""P10 tests: fan-out dinâmico, vazio e unitário."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p10_send.graph import build_graph


def test_three_jobs_fan_out_and_merge():
    # Given: 3 jobs
    graph = build_graph()
    # When: invocação
    result = graph.invoke({"jobs": [1, 2, 3], "results": []})
    # Then: um resultado por job, fundidos
    assert sorted(result["results"]) == [10, 20, 30]


def test_empty_jobs_finishes_without_work():
    # Given: nenhum job
    graph = build_graph()
    # When: invocação
    result = graph.invoke({"jobs": [], "results": []})
    # Then: termina vazio, sem erro
    assert result["results"] == []


def test_single_job():
    # Given: 1 job
    graph = build_graph()
    # When: invocação
    result = graph.invoke({"jobs": [7], "results": []})
    # Then: resultado único
    assert result["results"] == [70]
