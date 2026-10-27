"""M1: retry tolera provider instável; reflexão corrige resposta sem citação."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from langgraph.graph import END, START, StateGraph

from balcao.gateway import Backend
from balcao.graph import (
    TicketState,
    build_graph,
    make_draft,
    make_fetch,
    make_propose,
    make_retrieve,
    make_triage,
)
from balcao.kb import DocHit, Retriever, load_kb
from balcao.models import Category


def _retriever() -> Retriever:
    return Retriever.build(load_kb(Path("kb")))


def test_fetch_retry_recupera_provider_instavel() -> None:
    # Given: fetch que falha 2 vezes antes de responder
    builder: StateGraph = StateGraph(TicketState)
    backend = Backend(invoices={"cli1": "vencida R$ 89,90"})
    builder.add_node("triage", make_triage())
    builder.add_node("retrieve", make_retrieve(_retriever()))
    from langgraph.types import RetryPolicy

    builder.add_node(
        "fetch",
        make_fetch(backend, failures=2),
        retry_policy=RetryPolicy(max_attempts=3),
    )
    builder.add_node("draft", make_draft())
    builder.add_node("propose", make_propose())
    builder.add_edge(START, "triage")
    builder.add_edge("triage", "retrieve")
    builder.add_edge("retrieve", "fetch")
    builder.add_edge("fetch", "draft")
    builder.add_edge("draft", END)
    graph = builder.compile()
    # When: grafo roda
    out = graph.invoke({"ticket": "t", "customer": "cli1", "message": "fatura pix"})
    # Then: retry recuperou e o status chegou
    assert out["status"] == "vencida R$ 89,90"
    assert "[fonte:fatura-pix]" in out["answer"]


def test_reflexao_corrige_resposta_sem_citacao() -> None:
    # Given: render que erra na 1ª tentativa e cita na 2ª
    calls = {"n": 0}

    def flaky_render(sources: list[DocHit]) -> str:
        calls["n"] += 1
        if calls["n"] == 1:
            return "resposta sem citar nada"
        return f"ok [fonte:{sources[0].doc_id}]"

    builder: StateGraph = StateGraph(TicketState)
    builder.add_node("draft", make_draft(flaky_render))
    builder.add_edge(START, "draft")

    def check(state: TicketState) -> str:
        if "[fonte:" not in state.get("answer", "") and state.get("attempts", 0) < 2:
            return "draft"
        return "end"

    builder.add_conditional_edges("draft", check, {"draft": "draft", "end": END})
    graph = builder.compile()
    # When: grafo roda
    out = graph.invoke({"sources": [DocHit("fatura-pix", "texto", 0.5)]})
    # Then: 2 tentativas e resposta final com citação
    assert out["attempts"] == 2
    assert "[fonte:fatura-pix]" in out["answer"]


def test_keyword_plan_mapeia_chamado_e_visita() -> None:
    # Given: backend e grafo padrão
    graph = build_graph(_retriever(), Backend(), auto_approve=True)
    # When: pedido de chamado
    out = graph.invoke(
        {"ticket": "t", "customer": "c", "message": "abram um chamado, los vermelha"}
    )
    # Then: plano open_ticket com motivo
    assert out["plan"].tool == "open_ticket"
    assert out["plan"].args["motivo"] != ""
    # When: pedido de visita à tarde
    out2 = graph.invoke(
        {"ticket": "t", "customer": "c", "message": "agendar visita a tarde"}
    )
    # Then: plano schedule_visit com janela tarde
    assert out2["category"] == Category.AGENDAMENTO.value
    assert out2["plan"].tool == "schedule_visit"
    assert out2["plan"].args["janela"] == "tarde"
