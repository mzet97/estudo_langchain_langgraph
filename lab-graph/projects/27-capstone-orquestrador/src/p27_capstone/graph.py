"""P27: capstone — analisa, planeja, delega, testa, aprova, revisa."""

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt

KNOWN_OPS = ("double", "add")


def merge_dict(left: dict, right: dict) -> dict:
    """Reducer: funde parciais sem perder chaves."""
    return {**left, **right}


class P27State(TypedDict):
    spec: dict
    plan: list
    staged: Annotated[dict, merge_dict]
    results: dict
    approved: bool
    report: str


def analyze(state: P27State) -> dict:
    """Valida a spec e monta o plano; op/deps inválidas falham aqui."""
    steps = state["spec"].get("steps", [])
    known = {step["id"] for step in steps}
    if len(known) != len(steps):
        raise ValueError("duplicate step id")
    for step in steps:
        if step["op"] not in KNOWN_OPS:
            raise ValueError(f"unknown op: {step['op']}")
        for dep in step.get("depends_on", []):
            if dep not in known:
                raise ValueError(f"unknown dependency: {dep}")
    return {"plan": steps}


def dispatch(state: P27State) -> Command:
    """Espalha um Send por step do plano (delegação)."""
    sends = [Send("worker", step) for step in state["plan"]]
    return Command(goto=sends)


def worker(step: dict) -> dict:
    """Executa o step isolado e encena o resultado (sem aplicar)."""
    if step["op"] == "double":
        value = step["args"]["n"] * 2
    else:
        value = step["args"]["a"] + step["args"]["b"]
    return {"staged": {step["id"]: value}}


def collect(state: P27State) -> dict:
    """Barreira da delegação; a fusão já ocorreu no reducer."""
    return {}


def approve(state: P27State) -> dict:
    """Pede aprovação humana com o encenado; resume decide."""
    decision = interrupt({"staged": state["staged"]})
    return {"approved": bool(decision)}


def route_approval(state: P27State) -> Literal["apply", "rejected"]:
    """Aplica só com aprovação explícita."""
    if state["approved"]:
        return "apply"
    return "rejected"


def apply(state: P27State) -> dict:
    """Promove o encenado a resultado (só após aprovação)."""
    return {"results": dict(state["staged"])}


def rejected(state: P27State) -> dict:
    """Registra a recusa sem aplicar nada."""
    return {"report": "rejected by human"}


def review(state: P27State) -> dict:
    """Revisa o aplicado: relatório com contagem e valores."""
    items = sorted(state["results"].items())
    body = ", ".join(f"{k}={v}" for k, v in items)
    return {"report": f"applied {len(items)} steps: {body}"}


def build_graph(checkpointer: object | None = None) -> object:
    """Monta analyze→dispatch⇢worker→collect→approve→{apply→review|rejected}→END."""
    builder: StateGraph = StateGraph(P27State)
    builder.add_node("analyze", analyze)
    builder.add_node("dispatch", dispatch)
    builder.add_node("worker", worker)
    builder.add_node("collect", collect)
    builder.add_node("approve", approve)
    builder.add_node("apply", apply)
    builder.add_node("rejected", rejected)
    builder.add_node("review", review)
    builder.add_edge(START, "analyze")
    builder.add_edge("analyze", "dispatch")
    builder.add_edge("worker", "collect")
    builder.add_edge("collect", "approve")
    builder.add_conditional_edges(
        "approve", route_approval, {"apply": "apply", "rejected": "rejected"}
    )
    builder.add_edge("apply", "review")
    builder.add_edge("review", END)
    builder.add_edge("rejected", END)
    if checkpointer is None:
        checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)


def thread_config(thread_id: str) -> dict:
    """Config de execução com a thread obrigatória."""
    return {"configurable": {"thread_id": thread_id}}
