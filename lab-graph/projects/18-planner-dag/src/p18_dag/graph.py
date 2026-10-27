"""P18: planner DAG em 2 camadas — map por Send, reduce por fold."""

from __future__ import annotations

import operator
import re
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send


class P18State(TypedDict):
    goal: str
    steps: list[dict]
    scheduled: bool
    summed: bool
    partials: Annotated[list[int], operator.add]
    total: int


def plan(state: P18State) -> dict:
    """Extrai os números do pedido e monta os steps da camada map."""
    numbers = [int(m) for m in re.findall(r"-?\d+", state["goal"])]
    steps = [{"id": f"t{i}", "arg": n} for i, n in enumerate(numbers)]
    return {"steps": steps}


def schedule(state: P18State) -> Command:
    """Dispara a onda map (ou pula direto ao sum se não há steps)."""
    if not state["steps"]:
        return Command(goto="sum")
    sends = [Send("worker", step) for step in state["steps"]]
    return Command(update={"scheduled": True}, goto=sends)


def worker(step: dict) -> dict:
    """Map: dobra o argumento do step isolado."""
    return {"partials": [step["arg"] * 2]}


def collect(state: P18State) -> dict:
    """Barreira da camada map; a fusão já ocorreu no reducer."""
    return {}


def decide_sum(state: P18State) -> Literal["sum", "done"]:
    """Só reduz após a barreira; camada 2 depende da camada 1."""
    if state["summed"]:
        return "done"
    return "sum"


def sum_partials(state: P18State) -> dict:
    """Reduce (fold): soma os parciais uma única vez."""
    return {"total": sum(state["partials"]), "summed": True}


def build_graph() -> object:
    """Monta plan→schedule⇢worker→collect→{sum→END|END}."""
    builder: StateGraph = StateGraph(P18State)
    builder.add_node("plan", plan)
    builder.add_node("schedule", schedule)
    builder.add_node("worker", worker)
    builder.add_node("collect", collect)
    builder.add_node("sum", sum_partials)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "schedule")
    builder.add_edge("worker", "collect")
    builder.add_conditional_edges(
        "collect", decide_sum, {"sum": "sum", "done": END}
    )
    builder.add_edge("sum", END)
    return builder.compile()
