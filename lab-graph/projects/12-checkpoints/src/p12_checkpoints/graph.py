"""P12: checkpointers — retomada por thread_id e fork por checkpoint_id."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class P12State(TypedDict):
    count: Annotated[int, operator.add]


def bump(state: P12State) -> dict:
    """Soma 1 à contagem acumulada no checkpoint da thread."""
    return {"count": 1}


def build_graph(checkpointer: object | None = None) -> object:
    """Monta START→bump→END com o backend de checkpoint dado (ou memória)."""
    builder: StateGraph = StateGraph(P12State)
    builder.add_node("bump", bump)
    builder.add_edge(START, "bump")
    builder.add_edge("bump", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


def thread_config(thread_id: str, checkpoint_id: str | None = None) -> dict:
    """Config de execução: thread obrigatória, checkpoint só para fork."""
    configurable: dict[str, str] = {"thread_id": thread_id}
    if checkpoint_id is not None:
        configurable["checkpoint_id"] = checkpoint_id
    return {"configurable": configurable}
