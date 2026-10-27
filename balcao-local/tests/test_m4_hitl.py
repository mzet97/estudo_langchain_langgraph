"""M4: interrupt antes de escrever; resume decide; replay não duplica."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from langgraph.types import Command

from balcao.gateway import Backend, ToolGateway
from balcao.graph import build_graph
from balcao.kb import Retriever, load_kb
from balcao.memory import open_checkpointer


def _setup(tmp_path: Path) -> tuple[object, Backend, ToolGateway]:
    kb = Retriever.build(load_kb(Path("kb")))
    backend = Backend()
    gateway = ToolGateway(backend=backend)
    saver = open_checkpointer(tmp_path / "m4.db")
    return saver, backend, gateway, kb


def test_escrita_pausa_e_resume_aprovado_executa_uma_vez(
    tmp_path: Path,
) -> None:
    # Given: pedido de chamado com SQLite
    saver_ctx, backend, gateway, kb = _setup(tmp_path)
    with saver_ctx as saver:
        graph = build_graph(kb, backend, checkpointer=saver, gateway=gateway)
        config = {"configurable": {"thread_id": "t1"}}
        # When: roda até o interrupt
        paused = graph.invoke(
            {"ticket": "t1", "customer": "c", "message": "abram um chamado, los"},
            config=config,
        )
        # Then: pausou com o plano e nada foi executado
        assert "__interrupt__" in paused
        assert backend.ledger == []
        # When: responsável aprova
        done = graph.invoke(Command(resume={"approved": True}), config=config)
        # Then: executou uma vez e finalizou
        assert done["result"].startswith("CH-")
        assert done["done"] is True
        assert len(backend.ledger) == 1
        # When: replay do thread concluído
        again = graph.invoke(None, config=config)
        # Then: sem re-execução
        assert again["result"].startswith("CH-")
        assert len(backend.ledger) == 1


def test_resume_negado_nao_executa_e_audita(tmp_path: Path) -> None:
    # Given: pedido de visita pausado
    saver_ctx, backend, gateway, kb = _setup(tmp_path)
    with saver_ctx as saver:
        graph = build_graph(kb, backend, checkpointer=saver, gateway=gateway)
        config = {"configurable": {"thread_id": "t2"}}
        paused = graph.invoke(
            {"ticket": "t2", "customer": "c", "message": "agendar visita de manha"},
            config=config,
        )
        assert "__interrupt__" in paused
        # When: responsável nega
        done = graph.invoke(Command(resume={"approved": False}), config=config)
        # Then: nada executado, recusa auditada
        assert done["result"] == "ação negada pelo responsável"
        assert backend.ledger == []
        assert gateway.audit[-1].verdict == "denied:approval"


def test_leitura_executa_sem_aprovacao(tmp_path: Path) -> None:
    # Given: pedido de segunda via (leitura)
    saver_ctx, backend, gateway, kb = _setup(tmp_path)
    backend.invoices["c"] = "vencida R$ 89,90"
    with saver_ctx as saver:
        graph = build_graph(kb, backend, checkpointer=saver, gateway=gateway)
        # When: roda
        out = graph.invoke(
            {"ticket": "t3", "customer": "c", "message": "quero a segunda via"},
            config={"configurable": {"thread_id": "t3"}},
        )
        # Then: sem interrupt, fatura entregue
        assert "__interrupt__" not in out
        assert out["result"] == "vencida R$ 89,90"
