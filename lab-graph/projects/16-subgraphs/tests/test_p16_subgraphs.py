"""P16 tests: dobra, fronteira estanque e erro do filho."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p16_subgraphs.graph import build_parent


def test_parent_doubles_through_child():
    # Given: pai com filho real
    graph = build_parent()
    # When: invocação
    result = graph.invoke({"n": 21, "doubled": 0})
    # Then: valor dobrado pelo filho
    assert result["doubled"] == 42


def test_state_boundary_is_watertight():
    # Given: pai com filho real
    graph = build_parent()
    # When: invocação
    result = graph.invoke({"n": 5, "doubled": 0})
    # Then: chaves do filho não vazam para o pai
    assert set(result) == {"n", "doubled"}
    assert result["n"] == 5


def test_child_error_propagates_to_parent():
    # Given: filho que sempre falha
    class BrokenChild:
        def invoke(self, *_args: object, **_kwargs: object) -> dict:
            raise RuntimeError("child blew up")

    graph = build_parent(child=BrokenChild())
    # When/Then: erro sobe sem ser engolido na fronteira
    with pytest.raises(RuntimeError, match="child blew up"):
        graph.invoke({"n": 1, "doubled": 0})
