"""P18 tests: map-reduce, vazio e unitário."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p18_dag.graph import build_graph


def fresh_state(goal: str) -> dict:
    """Estado inicial para um pedido."""
    return {
        "goal": goal,
        "steps": [],
        "scheduled": False,
        "summed": False,
        "partials": [],
        "total": 0,
    }


def test_map_reduce_sums_doubled_values():
    # Given: 3 números no pedido
    graph = build_graph()
    # When: planeja, espalha, reduz
    result = graph.invoke(fresh_state("double 1 2 3 e some"))
    # Then: (1+2+3)*2
    assert result["total"] == 12


def test_empty_goal_finishes_at_zero():
    # Given: pedido sem números
    graph = build_graph()
    # When: invocação
    result = graph.invoke(fresh_state("nada aqui"))
    # Then: zero, sem travar na barreira
    assert result["total"] == 0


def test_single_item():
    # Given: 1 número
    graph = build_graph()
    # When: invocação
    result = graph.invoke(fresh_state("double 7"))
    # Then: dobro único
    assert result["total"] == 14
