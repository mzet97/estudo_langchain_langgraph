"""P23 tests: eventos ordenados, segredo sanitizado e erro registrado."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p23_trace.tracer import Tracer, build_graph, sanitize


def test_trace_captures_nodes_in_order():
    # Given: tracer sobre grafo de 2 nós
    tracer = Tracer(build_graph())
    # When: execução
    result = tracer.run({"n": 21, "doubled": 0, "secret": ""})
    # Then: eventos em ordem, latências válidas, resultado correto
    assert [e["node"] for e in tracer.events] == ["double", "finish"]
    assert all(e["latency_ms"] >= 0 for e in tracer.events)
    assert result["doubled"] == 42
    summary = tracer.summary()
    assert summary["calls"] == {"double": 1, "finish": 1}
    assert summary["total_ms"] >= 0
    assert summary["errors"] == {}


def test_sanitize_removes_denied_keys_without_mutating():
    # Given: payload com segredo
    payload = {"doubled": 42, "api_key": "SUPER-SECRETA"}
    # When: sanitiza para log
    logged = sanitize(payload)
    # Then: sem chave nem valor, original intacto
    assert "api_key" not in logged
    assert "SUPER-SECRETA" not in str(logged.values())
    assert payload["api_key"] == "SUPER-SECRETA"


def test_error_is_recorded_and_reraised():
    # Given: tracer sobre grafo cujo nó quebra
    from langgraph.graph import END, START, StateGraph

    def boom(state: dict) -> dict:
        raise ValueError("pane")

    builder = StateGraph(dict)
    builder.add_node("boom", boom)
    builder.add_edge(START, "boom")
    builder.add_edge("boom", END)
    tracer = Tracer(builder.compile())
    # When/Then: erro relançado e registrado
    with pytest.raises(ValueError, match="pane"):
        tracer.run({})
    assert tracer.summary()["errors"] == {"ValueError": 1}
