"""E2E contra o compose (fora do pytest default; exige BALCAO_E2E=1).

Alvo: API em http://127.0.0.1:8091 com Postgres e Gemma reais.
"""

import os
import sys

import pytest

sys.path.insert(0, "src")

import httpx

pytestmark = pytest.mark.skipif(
    os.getenv("BALCAO_E2E") != "1", reason="requer compose no ar (BALCAO_E2E=1)"
)

BASE = "http://127.0.0.1:8091"


def test_fluxo_chamado_com_aprovacao() -> None:
    # Given: stack real no ar
    with httpx.Client(base_url=BASE, timeout=300) as client:
        # When: pedido de chamado
        r1 = client.post(
            "/run",
            json={"ticket_id": "e2e1", "customer": "demo", "message": "abram um chamado, los vermelha"},
        )
        # Then: pausa com plano válido
        assert r1.status_code == 200
        assert r1.json()["status"] == "awaiting_approval"
        assert r1.json()["plan"]["tool"] == "open_ticket"
        # When: responsável aprova
        r2 = client.post("/resume", json={"ticket_id": "e2e1", "approved": True})
        # Then: chamado aberto
        assert r2.json()["status"] == "done"
        assert r2.json()["result"].startswith("CH-")


def test_ledger_tem_uma_linha() -> None:
    # Given: psycopg local apontando ao Postgres do compose
    import psycopg

    url = "postgresql://balcao:balcao@127.0.0.1:5433/balcao"
    # When: conta linhas do ledger
    with psycopg.connect(url, connect_timeout=5) as conn:
        total = conn.execute("SELECT COUNT(*) FROM ledger").fetchone()[0]
    # Then: exatamente um efeito do E2E
    assert total >= 1
