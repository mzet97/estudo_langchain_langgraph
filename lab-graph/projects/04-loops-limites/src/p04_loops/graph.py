"""P04: ciclo com limite — reflexão que sempre termina."""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class P04State(TypedDict):
    attempt: int
    done: bool


def make_reflect() -> object:
    """Nó que registra uma passagem de reflexão."""

    def reflect(state: P04State) -> dict:
        return {"attempt": state["attempt"] + 1}

    return reflect


def make_should_continue(limit: int) -> object:
    """Condição de parada: volta ao reflect abaixo do limite."""

    def should_continue(state: P04State) -> Literal["reflect", "finish"]:
        if state["attempt"] < limit:
            return "reflect"
        return "finish"

    return should_continue


def finish(state: P04State) -> dict:
    """Marca a conclusão após o limite de passagens."""
    return {"done": True}


def build_graph(limit: int = 3) -> object:
    """Monta START→reflect⇄(limite)→finish→END e retorna compilado."""
    if limit < 1:
        raise ValueError(f"limit must be >= 1, got {limit}")
    builder: StateGraph = StateGraph(P04State)
    builder.add_node("reflect", make_reflect())
    builder.add_node("finish", finish)
    builder.add_edge(START, "reflect")
    builder.add_conditional_edges(
        "reflect",
        make_should_continue(limit),
        {"reflect": "reflect", "finish": "finish"},
    )
    builder.add_edge("finish", END)
    return builder.compile()
