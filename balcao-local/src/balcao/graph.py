"""Graph assembly: triage → router (Send) → specialist → propose/gate/act."""

from __future__ import annotations

from langchain_core.runnables import Runnable
from langgraph.graph import END, START, StateGraph

from balcao.gateway import Ledger, ToolGateway
from balcao.kb import Retriever
from balcao.models import TicketState
from balcao.nodes import (
    make_abstain,
    make_act,
    make_draft,
    make_fetch,
    make_finalize,
    make_gate,
    make_propose,
    make_retrieve,
    make_triage,
)
from balcao.team import SPECIALISTS, dispatch, make_specialist, route_specialist

__all__ = [
    "TicketState",
    "build_graph",
    "make_abstain",
    "make_act",
    "make_draft",
    "make_fetch",
    "make_finalize",
    "make_gate",
    "make_propose",
    "make_retrieve",
    "make_triage",
]


def build_graph(
    retriever: Retriever,
    backend: Ledger,
    classifier: Runnable | None = None,
    fetch_failures: int = 0,
    checkpointer: object = None,
    auto_approve: bool = False,
    gateway: ToolGateway | None = None,
    planner: Runnable | None = None,
) -> object:
    """Assemble triage → Send specialist → propose → gate → act.

    Specialists run kb + status in parallel; the human gate stands
    between proposal and any write effect.
    """
    builder: StateGraph = StateGraph(TicketState)
    builder.add_node("triage", make_triage(classifier))
    for name in SPECIALISTS:
        builder.add_node(name, make_specialist(retriever, backend, fetch_failures))
    builder.add_node("abstain", make_abstain())
    builder.add_node("propose", make_propose(planner))
    gateway = gateway or ToolGateway(backend=backend)
    builder.add_node("gate", make_gate(gateway, auto_approve))
    builder.add_node("act", make_act(gateway))
    builder.add_node("finalize", make_finalize())
    builder.add_node("router", dispatch)
    builder.add_edge(START, "triage")
    builder.add_edge("triage", "router")
    for specialist in SPECIALISTS:
        builder.add_conditional_edges(
            specialist,
            route_specialist,
            {"propose": "propose", "finalize": "finalize"},
        )
    builder.add_edge("propose", "gate")
    builder.add_edge("act", "finalize")
    builder.add_edge("abstain", END)
    builder.add_edge("finalize", END)
    return builder.compile(checkpointer=checkpointer)
