"""P14: human-in-the-loop — pausa antes do efeito, resume com aprovação."""

from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class P14State(TypedDict):
    draft: str
    approved: bool


def draft_order(state: P14State) -> dict:
    """Prepara o pedido sem nenhum efeito colateral."""
    return {"draft": "order:42", "approved": False}


def place_order(state: P14State) -> dict:
    """Efeito sensível: só roda após resume explícito."""
    if not state["draft"]:
        raise ValueError("nothing to approve")
    return {"approved": True}


def build_graph(checkpointer: object | None = None) -> object:
    """Monta START→draft→[pausa]→place→END com o checkpointer dado."""
    builder: StateGraph = StateGraph(P14State)
    builder.add_node("draft_order", draft_order)
    builder.add_node("place_order", place_order)
    builder.add_edge(START, "draft_order")
    builder.add_edge("draft_order", "place_order")
    builder.add_edge("place_order", END)
    return builder.compile(
        checkpointer=checkpointer or InMemorySaver(),
        interrupt_before=["place_order"],
    )


def thread_config(thread_id: str) -> dict:
    """Config de execução com a thread obrigatória."""
    return {"configurable": {"thread_id": thread_id}}
