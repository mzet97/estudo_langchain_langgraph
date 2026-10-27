"""P01 tests: happy path, determinismo e entrada incompleta."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p01_graph.graph import build_graph


def test_happy_path_increments_once():
    # Given: grafo compilado e entrada válida
    graph = build_graph()
    # When: invocação única
    result = graph.invoke({"count": 0, "message": ""})
    # Then: contagem somada e mensagem final
    assert result["count"] == 1
    assert result["message"] == "done:1"


def test_repeated_invokes_are_identical():
    # Given: mesma entrada duas vezes
    graph = build_graph()
    first = graph.invoke({"count": 5, "message": ""})
    # When: segunda invocação
    second = graph.invoke({"count": 5, "message": ""})
    # Then: resultados idênticos
    assert first == second


def test_missing_count_fails_loudly():
    # Given: entrada sem a chave obrigatória
    graph = build_graph()
    # When/Then: falha explícita em vez de valor silencioso
    with pytest.raises(KeyError, match="count"):
        graph.invoke({"message": ""})
