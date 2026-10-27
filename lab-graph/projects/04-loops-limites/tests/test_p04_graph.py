"""P04 tests: término garantido e contagem exata de passagens."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p04_loops.graph import build_graph


def test_loop_stops_at_limit():
    # Given: limite 3
    graph = build_graph(limit=3)
    # When: invocação
    result = graph.invoke({"attempt": 0, "done": False})
    # Then: exatamente 3 passagens e conclusão
    assert result["attempt"] == 3
    assert result["done"] is True


def test_limit_one_finishes_in_single_pass():
    # Given: limite mínimo
    graph = build_graph(limit=1)
    # When: invocação
    result = graph.invoke({"attempt": 0, "done": False})
    # Then: uma passagem só
    assert result["attempt"] == 1
    assert result["done"] is True


def test_invalid_limit_rejected_upfront():
    # Given: limite zero
    # When/Then: rejeitado na construção, nunca em loop
    with pytest.raises(ValueError, match="limit"):
        build_graph(limit=0)
