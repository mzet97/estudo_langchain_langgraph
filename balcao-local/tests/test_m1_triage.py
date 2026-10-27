"""M1: triage classifica e roteia; plano só quando há ação."""

import sys

sys.path.insert(0, "src")

from pathlib import Path

from balcao.gateway import Backend
from balcao.graph import build_graph
from balcao.kb import Retriever, load_kb
from balcao.models import ABSTAIN


def _graph(auto_approve: bool = True) -> object:
    kb = Retriever.build(load_kb(Path("kb")))
    return build_graph(
        kb, Backend(invoices={"cli1": "vencida R$ 89,90"}), auto_approve=auto_approve
    )


def test_fatura_com_acao_propoe_get_invoice() -> None:
    # Given: pedido de segunda via
    # When: grafo roda
    out = _graph(auto_approve=True).invoke(
        {"ticket": "t1", "customer": "cli1", "message": "quero a segunda via"}
    )
    # Then: categoria fatura, citação do runbook e plano de leitura
    assert out["category"] == "fatura"
    assert "[fonte:fatura-2via]" in out["answer"]
    assert out["plan"].tool == "get_invoice"


def test_tecnico_sem_acao_nao_propoe_plano() -> None:
    # Given: LOS vermelha sem pedir chamado
    # When: grafo roda
    out = _graph(auto_approve=True).invoke(
        {"ticket": "t2", "customer": "cli1", "message": "luz los vermelha na ont"}
    )
    # Then: técnico, citado, sem plano
    assert out["category"] == "tecnico"
    assert "[fonte:" in out["answer"]
    assert out.get("plan") is None


def test_fora_do_corpus_abstem_sem_plano() -> None:
    # Given: pergunta sem overlap (ex.: horóscopo)
    # When: grafo roda
    out = _graph(auto_approve=True).invoke(
        {"ticket": "t3", "customer": "cli1", "message": "qual meu horoscopo de hoje"}
    )
    # Then: abstenção exata, sem citação inventada
    assert out["answer"] == ABSTAIN
    assert out.get("plan") is None
