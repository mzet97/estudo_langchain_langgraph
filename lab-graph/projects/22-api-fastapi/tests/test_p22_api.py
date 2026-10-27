"""P22 tests: POST /run, GET /stream SSE e 422 na borda."""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p22_api.app import create_app


def make_client() -> TestClient:
    """TestClient contra o app real (sem rede externa)."""
    return TestClient(create_app())


def test_run_doubles_input():
    # Given: app de teste
    client = make_client()
    # When: POST /run válido
    response = client.post("/run", json={"n": 21})
    # Then: 200 com o dobro
    assert response.status_code == 200
    assert response.json() == {"doubled": 42}


def test_stream_emits_node_events_in_order():
    # Given: app de teste
    client = make_client()
    # When: GET /stream
    response = client.get("/stream", params={"n": 5})
    # Then: SSE com um evento por nó, em ordem
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    body = response.text
    assert "event: double" in body
    assert "event: finish" in body
    assert body.index("event: double") < body.index("event: finish")


def test_run_rejects_missing_field():
    # Given: app de teste
    client = make_client()
    # When: POST sem o campo obrigatório
    response = client.post("/run", json={})
    # Then: 422 da borda, sem tocar o grafo
    assert response.status_code == 422
