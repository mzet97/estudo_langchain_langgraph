"""P10: fan-out dinâmico — Send distribui N tarefas decididas em runtime."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send


class P10State(TypedDict):
    jobs: list[int]
    results: Annotated[list[int], operator.add]


def split(state: P10State) -> dict:
    """Ponto de partida do fan-out; a distribuição mora na aresta."""
    return {}


def fanout(state: P10State) -> list[Send]:
    """Roteia um Send por job; N só existe em runtime."""
    return [Send("worker", n) for n in state["jobs"]]


def worker(n: int) -> dict:
    """Processa um item isolado (executa em paralelo com os demais)."""
    return {"results": [n * 10]}


def collect(state: P10State) -> dict:
    """Ponto de convergência; a fusão já ocorreu no reducer."""
    return {}


def build_graph() -> object:
    """Monta START→fanout→worker⇉collect→END e retorna compilado."""
    builder: StateGraph = StateGraph(P10State)
    builder.add_node("split", split)
    builder.add_node("worker", worker)
    builder.add_node("collect", collect)
    builder.add_edge(START, "split")
    builder.add_conditional_edges("split", fanout)
    builder.add_edge("worker", "collect")
    builder.add_edge("collect", END)
    return builder.compile()
