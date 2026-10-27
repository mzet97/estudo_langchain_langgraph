"""P01: primeiro StateGraph — START, END, nós e arestas (sem LLM)."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class P01State(TypedDict):
    count: int
    message: str


def start_node(state: P01State) -> dict:
    """Inicializa a mensagem preservando a contagem de entrada."""
    return {"message": "started"}


def increment_node(state: P01State) -> dict:
    """Soma 1 à contagem."""
    return {"count": state["count"] + 1}


def finish_node(state: P01State) -> dict:
    """Registra a mensagem final com o valor alcançado."""
    return {"message": f"done:{state['count']}"}


def build_graph() -> object:
    """Monta START→start→increment→finish→END e retorna o grafo compilado."""
    builder: StateGraph = StateGraph(P01State)
    builder.add_node("start", start_node)
    builder.add_node("increment", increment_node)
    builder.add_node("finish", finish_node)
    builder.add_edge(START, "start")
    builder.add_edge("start", "increment")
    builder.add_edge("increment", "finish")
    builder.add_edge("finish", END)
    return builder.compile()
