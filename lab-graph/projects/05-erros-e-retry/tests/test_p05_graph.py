"""P05 tests: retry com sucesso, esgotamento e cache hit."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p05_errors.graph import build_cache_graph, build_retry_graph


def test_retry_succeeds_on_third_attempt():
    # Given: nó que falha 2 vezes, com 3 tentativas
    graph, counter = build_retry_graph(fail_times=2, max_attempts=3)
    # When: invocação
    result = graph.invoke({"attempts": 0, "value": "", "cached": False})
    # Then: sucesso na 3ª tentativa
    assert result["value"] == "ok"
    assert result["attempts"] == 3
    assert counter["runs"] == 3


def test_exhausted_retries_raise():
    # Given: nó que sempre falha, com 2 tentativas
    graph, counter = build_retry_graph(fail_times=10, max_attempts=2)
    # When/Then: erro sobe após esgotar
    with pytest.raises(ConnectionError, match="transient failure"):
        graph.invoke({"attempts": 0, "value": "", "cached": False})
    assert counter["runs"] == 2


def test_cache_hit_skips_recompute():
    # Given: grafo com memo e mesma entrada duas vezes
    graph, counter = build_cache_graph()
    first = graph.invoke({"attempts": 0, "value": "k", "cached": False})
    # When: segunda invocação igual
    second = graph.invoke({"attempts": 0, "value": "k", "cached": False})
    # Then: 1 computação real, 2ª resposta do cache
    assert counter["runs"] == 1
    assert first["cached"] is False
    assert second["cached"] is True
    assert second["value"] == first["value"]
