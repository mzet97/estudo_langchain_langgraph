"""P22: grafo determinístico de demonstração para a API."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class P22State(TypedDict):
    n: int
    doubled: int


def double(state: P22State) -> dict:
    """Dobra a entrada."""
    return {"doubled": state["n"] * 2}


def finish(state: P22State) -> dict:
    """Nó final; marca o fim do pipeline HTTP."""
    return {}


def build_graph() -> object:
    """Monta START→double→finish→END e retorna compilado."""
    builder: StateGraph = StateGraph(P22State)
    builder.add_node("double", double)
    builder.add_node("finish", finish)
    builder.add_edge(START, "double")
    builder.add_edge("double", "finish")
    builder.add_edge("finish", END)
    return builder.compile()
