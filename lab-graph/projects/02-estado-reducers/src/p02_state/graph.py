"""P02: estado com reducer — fusão de atualizações parciais em fan-in."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class P02State(TypedDict):
    items: Annotated[list[str], operator.add]
    total: Annotated[int, operator.add]


def add_a(state: P02State) -> dict:
    """Contribui o item 'a' e uma unidade ao total."""
    return {"items": ["a"], "total": 1}


def add_b(state: P02State) -> dict:
    """Contribui o item 'b' e uma unidade ao total."""
    return {"items": ["b"], "total": 1}


def collect(state: P02State) -> dict:
    """Ponto de convergência; não altera o estado."""
    return {}


def build_graph() -> object:
    """Monta START→{add_a, add_b}→collect→END e retorna compilado."""
    builder: StateGraph = StateGraph(P02State)
    builder.add_node("add_a", add_a)
    builder.add_node("add_b", add_b)
    builder.add_node("collect", collect)
    builder.add_edge(START, "add_a")
    builder.add_edge(START, "add_b")
    builder.add_edge("add_a", "collect")
    builder.add_edge("add_b", "collect")
    builder.add_edge("collect", END)
    return builder.compile()
