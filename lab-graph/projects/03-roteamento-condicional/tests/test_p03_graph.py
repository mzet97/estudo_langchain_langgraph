"""P03 tests: cada ramo e domínio fechado da função de decisão."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p03_routing.graph import build_graph, decide


def test_even_value_takes_even_branch():
    # Given: valor par
    graph = build_graph()
    # When: invocação
    result = graph.invoke({"value": 4, "route": ""})
    # Then: ramo par
    assert result["route"] == "even"


def test_odd_value_takes_odd_branch():
    # Given: valor ímpar
    graph = build_graph()
    # When: invocação
    result = graph.invoke({"value": 7, "route": ""})
    # Then: ramo ímpar
    assert result["route"] == "odd"


@pytest.mark.parametrize("value,expected", [(0, "even"), (1, "odd"), (-2, "even")])
def test_decide_covers_closed_domain(value, expected):
    # Given: inteiros de borda
    # When: decisão pura
    # Then: só os dois destinos existem
    assert decide({"value": value, "route": ""}) == expected
