"""P11 tests: salto dinâmico, ambos os ramos e kind inválido."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p11_command.graph import build_graph


def test_fast_route_skips_slow():
    # Given: kind fast
    graph = build_graph()
    # When: invocação
    result = graph.invoke({"kind": "fast", "visited": []})
    # Then: só o ramo rápido foi visitado
    assert result["visited"] == ["route", "fast"]


def test_slow_route_skips_fast():
    # Given: kind slow
    graph = build_graph()
    # When: invocação
    result = graph.invoke({"kind": "slow", "visited": []})
    # Then: só o ramo lento foi visitado
    assert result["visited"] == ["route", "slow"]


def test_unknown_kind_fails_loudly():
    # Given: kind fora do domínio
    graph = build_graph()
    # When/Then: falha explícita, sem salto silencioso
    with pytest.raises(ValueError, match="unknown kind"):
        graph.invoke({"kind": "x", "visited": []})
