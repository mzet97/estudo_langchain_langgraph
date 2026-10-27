"""P19 tests: citação, abstenção e limiar do retriever."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p19_rag.graph import build_graph, retrieve


def fresh_state(query: str) -> dict:
    """Estado inicial para uma pergunta."""
    return {"query": query, "sources": [], "answer": "", "grounded": False}


def test_covered_question_cites_source():
    # Given: pergunta coberta pelo corpus
    graph = build_graph()
    # When: invocação
    result = graph.invoke(fresh_state("o que faz o RetryPolicy?"))
    # Then: cita a fonte e marca grounded
    assert result["grounded"] is True
    assert result["sources"][0] == "retry"
    assert "[retry]" in result["answer"]


def test_uncovered_question_abstains():
    # Given: pergunta sem cobertura
    graph = build_graph()
    # When: invocação
    result = graph.invoke(fresh_state("receita de bolo de cenoura"))
    # Then: abstenção explícita, sem fontes
    assert result["grounded"] is False
    assert result["sources"] == []
    assert "abstenho" in result["answer"]


def test_retriever_honors_minimum_overlap():
    # Given: corpus padrão
    # When: consulta sem tokens em comum
    found = retrieve("xyzq wjvk")
    # Then: nenhuma fonte fraca
    assert found == []
