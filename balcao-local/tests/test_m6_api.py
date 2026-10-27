"""M6 API: E2E run → approve → done, e SSE; tracer não vaza conteúdo."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from fastapi.testclient import TestClient

from balcao.app import create_app
from balcao.gateway import Backend
from balcao.graph import build_graph
from balcao.kb import Retriever, load_kb
from balcao.trace import EventLog


def test_run_pausa_e_resume_executa(tmp_path: Path) -> None:
    # Given: app com lifespan ativo
    with TestClient(create_app(tmp_path / "api.db", use_llm=False)) as client:
        # When: pedido de chamado
        r1 = client.post(
            "/run",
            json={"ticket_id": "t1", "customer": "c", "message": "abram um chamado, los"},
        )
        # Then: 202 com plano, sem efeito ainda
        assert r1.status_code == 200
        assert r1.json()["status"] == "awaiting_approval"
        assert r1.json()["plan"]["tool"] == "open_ticket"
        # When: responsável aprova
        r2 = client.post("/resume", json={"ticket_id": "t1", "approved": True})
        # Then: chamado aberto
        assert r2.json()["status"] == "done"
        assert r2.json()["result"].startswith("CH-")


def test_run_sem_acao_responde_direto(tmp_path: Path) -> None:
    # Given: app com lifespan ativo
    with TestClient(create_app(tmp_path / "api.db", use_llm=False)) as client:
        # When: dúvida técnica simples
        r = client.post(
            "/run",
            json={"ticket_id": "t2", "customer": "c", "message": "wifi fraco no quarto"},
        )
        # Then: resposta citada, sem aprovação
        assert r.json()["status"] == "done"
        assert "[fonte:" in r.json()["answer"]


def test_stream_emite_eventos_sse(tmp_path: Path) -> None:
    # Given: app com lifespan ativo
    with TestClient(create_app(tmp_path / "api.db", use_llm=False)) as client:
        # When: GET /stream
        r = client.get(
            "/stream",
            params={"ticket_id": "t3", "customer": "c", "message": "quero a segunda via"},
        )
        # Then: linhas SSE com nomes de nós, sem travar
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        assert "data:" in r.text


def test_tracer_registra_sem_vazar(tmp_path: Path) -> None:
    # Given: grafo com EventLog e mensagem sensível
    log = EventLog()
    graph = build_graph(Retriever.build(load_kb(Path("kb"))), Backend())
    secret = "minha senha secreta 12345"
    # When: roda com o tracer anexado
    graph.invoke(
        {"ticket": "t", "customer": "c", "message": secret},
        config={"callbacks": [log]},
    )
    # Then: eventos observados, conteúdo jamais gravado
    assert log.names() != []
    assert "12345" not in str(log.events)
    assert secret not in str(log.events)
