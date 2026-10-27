"""P17: supervisor despacha, especialistas devolvem (handoff), supervisor fecha."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command


class P17State(TypedDict):
    task: str
    assignment: str
    partial: str
    answer: str


def supervisor(state: P17State) -> Command:
    """Classifica por prefixo e despacha, ou fecha quando há parcial."""
    if state["partial"]:
        return Command(goto="respond")
    if state["task"].startswith("calc:"):
        return Command(update={"assignment": "math"}, goto="math_agent")
    if state["task"].startswith("text:"):
        return Command(update={"assignment": "text"}, goto="text_agent")
    raise ValueError(f"no specialist for task: {state['task']!r}")


def math_agent(state: P17State) -> Command:
    """Especialista em soma: resolve e devolve ao supervisor."""
    body = state["task"].split("calc:", 1)[1].strip()
    left, right = (part.strip() for part in body.split("+", 1))
    total = float(left) + float(right)
    return Command(
        update={"partial": str(int(total) if total.is_integer() else total)},
        goto="supervisor",
    )


def text_agent(state: P17State) -> Command:
    """Especialista em texto: devolve em maiúsculas ao supervisor."""
    body = state["task"].split("text:", 1)[1].strip()
    return Command(update={"partial": body.upper()}, goto="supervisor")


def respond(state: P17State) -> dict:
    """Monta a resposta final com o carimbo do especialista."""
    return {"answer": f"[{state['assignment']}] {state['partial']}"}


def build_graph() -> object:
    """Monta START→supervisor⇄especialistas→respond→END (só gotos dinâmicos)."""
    builder: StateGraph = StateGraph(P17State)
    builder.add_node("supervisor", supervisor)
    builder.add_node("math_agent", math_agent)
    builder.add_node("text_agent", text_agent)
    builder.add_node("respond", respond)
    builder.add_edge(START, "supervisor")
    builder.add_edge("respond", END)
    return builder.compile()
