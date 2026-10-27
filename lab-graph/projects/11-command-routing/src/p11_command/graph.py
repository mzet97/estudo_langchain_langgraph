"""P11: Command — atualização de estado e salto decididos num só retorno."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class P11State(TypedDict):
    kind: str
    visited: Annotated[list[str], operator.add]


def route(state: P11State) -> Command:
    """Decide o destino E registra a passagem num único Command."""
    if state["kind"] == "fast":
        return Command(update={"visited": ["route"]}, goto="fast")
    if state["kind"] == "slow":
        return Command(update={"visited": ["route"]}, goto="slow")
    raise ValueError(f"unknown kind: {state['kind']}")


def fast(state: P11State) -> dict:
    """Ramo rápido: registra visita."""
    return {"visited": ["fast"]}


def slow(state: P11State) -> dict:
    """Ramo lento: registra visita."""
    return {"visited": ["slow"]}


def build_graph() -> object:
    """Monta START→route⇢{fast|slow}→END e retorna compilado."""
    builder: StateGraph = StateGraph(P11State)
    builder.add_node("route", route)
    builder.add_node("fast", fast)
    builder.add_node("slow", slow)
    builder.add_edge(START, "route")
    builder.add_edge("fast", END)
    builder.add_edge("slow", END)
    return builder.compile()
