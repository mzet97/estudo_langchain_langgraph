"""P03: roteamento condicional — função pura decide o próximo nó."""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class P03State(TypedDict):
    value: int
    route: str


def decide(state: P03State) -> Literal["even", "odd"]:
    """Roteia pelo valor: par ou ímpar. Domínio fechado em dois destinos."""
    if state["value"] % 2 == 0:
        return "even"
    return "odd"


def handle_even(state: P03State) -> dict:
    """Marca a rota par."""
    return {"route": "even"}


def handle_odd(state: P03State) -> dict:
    """Marca a rota ímpar."""
    return {"route": "odd"}


def build_graph() -> object:
    """Monta START→decide→{handle_even|handle_odd}→END."""
    builder: StateGraph = StateGraph(P03State)
    builder.add_node("handle_even", handle_even)
    builder.add_node("handle_odd", handle_odd)
    builder.add_conditional_edges(
        START,
        decide,
        {"even": "handle_even", "odd": "handle_odd"},
    )
    builder.add_edge("handle_even", END)
    builder.add_edge("handle_odd", END)
    return builder.compile()
