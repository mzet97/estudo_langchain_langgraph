"""P21: execução durável — crash no meio, resume sem refazer o completo."""

from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph


class P21State(TypedDict):
    a: int
    b: int
    c: int


def make_step(name: str, field: str, value: int, runs: dict) -> object:
    """Etapa que registra sua execução e escreve o campo."""

    def step(state: P21State) -> dict:
        runs[name] = runs.get(name, 0) + 1
        return {field: value}

    return step


def make_fragile(runs: dict, crash_budget: dict) -> object:
    """Etapa que quebra enquanto houver orçamento de crash."""

    def fragile(state: P21State) -> dict:
        runs["fragile"] = runs.get("fragile", 0) + 1
        if crash_budget.get("n", 0) > 0:
            crash_budget["n"] -= 1
            raise ConnectionError("crash simulado no fragile")
        return {"b": 2}

    return fragile


def build_graph(
    checkpointer: object | str | None = "memory",
    crash_budget: dict | None = None,
    runs: dict | None = None,
) -> object:
    """Monta step1→fragile→step3; checkpointer None = sem durabilidade."""
    budget = crash_budget if crash_budget is not None else {}
    counter = runs if runs is not None else {}
    builder: StateGraph = StateGraph(P21State)
    builder.add_node("step1", make_step("step1", "a", 1, counter))
    builder.add_node("fragile", make_fragile(counter, budget))
    builder.add_node("step3", make_step("step3", "c", 3, counter))
    builder.add_edge(START, "step1")
    builder.add_edge("step1", "fragile")
    builder.add_edge("fragile", "step3")
    builder.add_edge("step3", END)
    if checkpointer is None:
        return builder.compile()
    return builder.compile(checkpointer=InMemorySaver())
