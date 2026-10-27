"""P14 tests: pausa auditável, resume aprovado e efeito contido."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from langgraph.types import Command
from p14_hitl.graph import build_graph, thread_config


def test_pause_exposes_draft_and_pending_node():
    # Given: pedido novo
    graph = build_graph()
    # When: invoke congela antes do efeito
    paused = graph.invoke(
        {"draft": "", "approved": False}, thread_config("t1")
    )
    # Then: rascunho pronto, efeito pendente e nada aprovado
    assert paused["draft"] == "order:42"
    assert paused["approved"] is False
    assert graph.get_state(thread_config("t1")).next == ("place_order",)


def test_resume_with_approval_runs_effect():
    # Given: pausa ativa
    graph = build_graph()
    graph.invoke({"draft": "", "approved": False}, thread_config("t1"))
    # When: humano aprova
    resumed = graph.invoke(Command(resume=True), thread_config("t1"))
    # Then: efeito executado
    assert resumed["approved"] is True
    assert resumed["draft"] == "order:42"


def test_no_resume_no_effect():
    # Given: pausa ativa e nenhum resume
    graph = build_graph()
    paused = graph.invoke(
        {"draft": "", "approved": False}, thread_config("t1")
    )
    # When/Then: estado segue não aprovado; efeito jamais rodou
    assert paused["approved"] is False
    assert graph.get_state(thread_config("t1")).next == ("place_order",)
