"""P07 tests: JSON válido, inválido e live com validado."""

import sys
from pathlib import Path

import httpx
import pytest
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
)
from pydantic import ValidationError

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))
sys.path.insert(0, str(HERE.parents[3] / "src"))

from p07_structured.graph import build_graph  # noqa: RUF100


def test_valid_json_produces_typed_rating():
    # Given: fake com JSON dentro do contrato
    fake = FakeListChatModel(
        responses=['{"title": "Duna", "score": 9, "tags": ["sci-fi"]}']
    )
    graph = build_graph(llm=fake)
    # When: invocação
    result = graph.invoke({"query": "Duna", "rating": None})
    # Then: modelo tipado exato
    assert result["rating"].title == "Duna"
    assert result["rating"].score == 9
    assert result["rating"].tags == ["sci-fi"]


def test_invalid_json_raises_validation_error():
    # Given: fake com JSON fora do contrato (score 99, sem tags)
    fake = FakeListChatModel(responses=['{"title": "X", "score": 99}'])
    graph = build_graph(llm=fake)
    # When/Then: falha explícita, nada parcial publicado
    with pytest.raises(ValidationError):
        graph.invoke({"query": "X", "rating": None})


def test_live_server_returns_validated_rating():
    # Given: servidor local
    try:
        httpx.get("http://127.0.0.1:8080/health", timeout=5).raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"llama-server ausente: {exc}")
    # When: extração real
    graph = build_graph()
    result = graph.invoke({"query": "O Pequeno Príncipe", "rating": None})
    # Then: contrato válido (score dentro de 0–10 garantido pelo tipo)
    assert result["rating"] is not None
    assert 0 <= result["rating"].score <= 10
