"""P13 tests: memória cross-thread, namespaces e chave ausente."""

import sys
from pathlib import Path

import pytest
from langgraph.store.memory import InMemoryStore

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p13_store.graph import build_graph


def base_state(mode: str, ns: str, key: str, value: str = "") -> dict:
    """Estado inicial para um pedido de store/recall."""
    return {"mode": mode, "ns": ns, "key": key, "value": value, "answer": ""}


def test_memory_survives_across_threads():
    # Given: store compartilhado, gravação na thread A
    store = InMemoryStore()
    writer = build_graph(store=store)
    writer.invoke(base_state("store", "user", "nome", "Ada"))
    # When: leitura na thread B (store é o elo, não a thread)
    reader = build_graph(store=store)
    result = reader.invoke(base_state("recall", "user", "nome"))
    # Then: valor atravessou as threads
    assert result["answer"] == "Ada"


def test_namespaces_do_not_leak():
    # Given: mesma key em dois namespaces
    store = InMemoryStore()
    graph = build_graph(store=store)
    graph.invoke(base_state("store", "ns1", "k", "um"))
    graph.invoke(base_state("store", "ns2", "k", "dois"))
    # When: leitura de cada um
    first = graph.invoke(base_state("recall", "ns1", "k"))
    second = graph.invoke(base_state("recall", "ns2", "k"))
    # Then: sem vazamento
    assert first["answer"] == "um"
    assert second["answer"] == "dois"


def test_missing_key_raises():
    # Given: store vazio
    graph = build_graph(store=InMemoryStore())
    # When/Then: chave ausente é erro explícito
    with pytest.raises(ValueError, match="no memory"):
        graph.invoke(base_state("recall", "user", "fantasma"))
