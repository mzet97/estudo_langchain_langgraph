"""P17 tests: despacho, handoff de volta e rota desconhecida."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p17_team.graph import build_graph


def fresh_state(task: str) -> dict:
    """Estado inicial vazio para um pedido."""
    return {"task": task, "assignment": "", "partial": "", "answer": ""}


def test_calc_task_dispatched_to_math():
    # Given: pedido com prefixo calc
    graph = build_graph()
    # When: pipeline com handoff de volta ao supervisor
    result = graph.invoke(fresh_state("calc: 2+3"))
    # Then: especialista carimbado e resultado certo
    assert result["answer"] == "[math] 5"
    assert result["assignment"] == "math"


def test_text_task_dispatched_to_text():
    # Given: pedido com prefixo text
    graph = build_graph()
    # When: pipeline com handoff de volta ao supervisor
    result = graph.invoke(fresh_state("text: olá"))
    # Then: especialista carimbado e texto transformado
    assert result["answer"] == "[text] OLÁ"


def test_unknown_prefix_has_no_default_worker():
    # Given: prefixo sem especialista
    graph = build_graph()
    # When/Then: falha explícita, sem rota padrão silenciosa
    with pytest.raises(ValueError, match="no specialist"):
        graph.invoke(fresh_state("x: faça algo"))
