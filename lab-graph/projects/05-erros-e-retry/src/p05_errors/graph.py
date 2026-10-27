"""P05: erros esperados — RetryPolicy, esgotamento e cache por entrada."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy


class P05State(TypedDict):
    attempts: int
    value: str
    cached: bool


def make_counter() -> dict:
    """Contador compartilhado para observar quantas vezes um nó rodou."""
    return {"runs": 0}


def build_retry_graph(fail_times: int, max_attempts: int) -> tuple:
    """Grafo de um nó com RetryPolicy; retorna (grafo, contador)."""
    counter = make_counter()

    def flaky(state: P05State) -> dict:
        counter["runs"] += 1
        if counter["runs"] <= fail_times:
            raise ConnectionError(f"transient failure #{counter['runs']}")
        return {"attempts": counter["runs"], "value": "ok", "cached": False}

    builder: StateGraph = StateGraph(P05State)
    builder.add_node(
        "flaky", flaky, retry_policy=RetryPolicy(max_attempts=max_attempts)
    )
    builder.add_edge(START, "flaky")
    builder.add_edge("flaky", END)
    return builder.compile(), counter


def build_cache_graph() -> tuple:
    """Grafo com memo por entrada; retorna (grafo, contador)."""
    memo: dict[str, str] = {}
    counter = make_counter()

    def cached_lookup(state: P05State) -> dict:
        key = state["value"]
        if key in memo:
            return {"value": memo[key], "cached": True}
        counter["runs"] += 1
        computed = f"computed:{key}"
        memo[key] = computed
        return {"attempts": 1, "value": computed, "cached": False}

    builder: StateGraph = StateGraph(P05State)
    builder.add_node("lookup", cached_lookup)
    builder.add_edge(START, "lookup")
    builder.add_edge("lookup", END)
    return builder.compile(), counter
