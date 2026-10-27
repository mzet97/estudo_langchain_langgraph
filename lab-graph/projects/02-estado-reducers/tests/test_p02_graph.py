"""P02 tests: fusão por reducer e isolamento entre invokes."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p02_state.graph import build_graph


def test_reducer_merges_both_branches():
    # Given: grafo com fan-out/fan-in
    graph = build_graph()
    # When: invocação única
    result = graph.invoke({"items": [], "total": 0})
    # Then: ambas as contribuições fundidas, total somado
    assert sorted(result["items"]) == ["a", "b"]
    assert result["total"] == 2


def test_invokes_do_not_leak_state():
    # Given: primeira execução concluída
    graph = build_graph()
    first = graph.invoke({"items": [], "total": 0})
    # When: segunda execução com entrada limpa
    second = graph.invoke({"items": [], "total": 0})
    # Then: nada vaza de uma execução para outra
    assert first["items"] == second["items"]
    assert len(second["items"]) == 2
