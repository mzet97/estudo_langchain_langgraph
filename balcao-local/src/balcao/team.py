"""Supervisor team: specialist subgraphs dispatched via Send + Command."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, Send

from balcao.gateway import Ledger
from balcao.kb import Retriever
from balcao.models import Category, TicketState
from balcao.nodes import make_draft, make_fetch, make_retrieve

SPECIALISTS: tuple[str, ...] = (
    Category.FATURA.value,
    Category.TECNICO.value,
    Category.AGENDAMENTO.value,
)


def make_specialist(
    retriever: Retriever,
    backend: Ledger,
    fetch_failures: int = 0,
) -> object:
    """Specialist subgraph: kb + status fan out in parallel, then draft."""
    sub: StateGraph = StateGraph(TicketState)
    sub.add_node("kb", make_retrieve(retriever))
    sub.add_node(
        "status",
        make_fetch(backend, fetch_failures),
        retry_policy=RetryPolicy(max_attempts=3),
    )
    sub.add_node("draft", make_draft())
    sub.add_edge(START, "kb")
    sub.add_edge(START, "status")
    sub.add_edge("kb", "draft")
    sub.add_edge("status", "draft")
    sub.add_edge("draft", END)
    return sub.compile()


def route_specialist(state: TicketState) -> str:
    """After a specialist: proposals go to `propose`, answers to `finalize`."""
    if state.get("needs_action", False):
        return "propose"
    return "finalize"


def dispatch(state: TicketState) -> Command:
    """Supervisor handoff: Command carrying a Send to the specialist."""
    category = state.get("category", Category.DESCONHECIDO.value)
    if category in SPECIALISTS:
        return Command(goto=Send(category, dict(state)))
    return Command(goto="abstain")
