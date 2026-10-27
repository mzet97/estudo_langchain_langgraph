"""M2: supervisor despacha via Send; especialista entrega via Command."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from balcao.gateway import Backend
from balcao.graph import build_graph
from balcao.kb import Retriever, load_kb
from balcao.models import ABSTAIN


def _graph(auto_approve: bool = True) -> object:
    kb = Retriever.build(load_kb(Path("kb")))
    backend = Backend(invoices={"cli1": "vencida R$ 89,90"})
    return build_graph(kb, backend, auto_approve=auto_approve)


def test_send_entrega_ao_especialista_com_status() -> None:
    # Given: pedido de visita à tarde
    # When: grafo roda
    out = _graph(auto_approve=True).invoke(
        {"ticket": "t", "customer": "cli1", "message": "agendar visita a tarde"}
    )
    # Then: especialista agendamento respondeu, status veio junto, plano pronto
    assert out["category"] == "agendamento"
    assert "[fonte:agendamento-visita]" in out["answer"]
    assert out["status"] == "vencida R$ 89,90"
    assert out["plan"].tool == "schedule_visit"
    assert out["done"] is True


def test_command_sem_acao_finaliza_direto() -> None:
    # Given: dúvida técnica sem pedir ação
    # When: grafo roda
    out = _graph(auto_approve=True).invoke(
        {"ticket": "t", "customer": "cli1", "message": "wifi fraco no quarto"}
    )
    # Then: handoff foi para finalize, sem plano
    assert out["category"] == "tecnico"
    assert out.get("plan") is None
    assert out["done"] is True


def test_desconhecido_abstem_fora_dos_especialistas() -> None:
    # Given: pergunta sem overlap
    # When: grafo roda
    out = _graph(auto_approve=True).invoke(
        {"ticket": "t", "customer": "cli1", "message": "qual meu horoscopo de hoje"}
    )
    # Then: abstenção, sem plano, finalizado
    assert out["answer"] == ABSTAIN
    assert out.get("plan") is None
    assert out["done"] is True
