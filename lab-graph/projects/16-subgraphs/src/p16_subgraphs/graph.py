"""P16: subgrafo com fronteira de estado — mapeamento explícito pai/filho."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class P16Child(TypedDict):
    x: int
    y: int


class P16Parent(TypedDict):
    n: int
    doubled: int


def double(state: P16Child) -> dict:
    """Dobra x dentro do schema do filho."""
    return {"y": state["x"] * 2}


def build_child() -> object:
    """Filho compilado: schema próprio, sem conhecer o pai."""
    builder: StateGraph = StateGraph(P16Child)
    builder.add_node("double", double)
    builder.add_edge(START, "double")
    builder.add_edge("double", END)
    return builder.compile()


def make_call_child(child: object) -> object:
    """Nó do pai: traduz n→x na ida e y→doubled na volta."""

    def call_child(state: P16Parent) -> dict:
        result = child.invoke({"x": state["n"], "y": 0})
        return {"doubled": result["y"]}

    return call_child


def build_parent(child: object | None = None) -> object:
    """Pai compilado; sem `child`, usa o filho real."""
    chosen = child if child is not None else build_child()
    builder: StateGraph = StateGraph(P16Parent)
    builder.add_node("call_child", make_call_child(chosen))
    builder.add_edge(START, "call_child")
    builder.add_edge("call_child", END)
    return builder.compile()
