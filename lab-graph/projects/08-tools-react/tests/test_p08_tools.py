"""P08 tests: execução allowlisted, negação, JSON inválido e live."""

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

from p08_tools.graph import build_graph


def fresh_state(request: str) -> dict:
    """Estado inicial vazio para um pedido."""
    return {
        "request": request,
        "plan_json": "",
        "outcome": "",
        "observation": "",
        "answer": "",
    }


def test_allowlisted_tool_executes():
    # Given: plano válido para ferramenta permitida
    fake = FakeListChatModel(
        responses=['{"tool": "add", "args": {"a": 2, "b": 3}}']
    )
    graph = build_graph(llm=fake, clock=lambda: "2026-01-01T00:00:00")
    # When: pipeline completo
    result = graph.invoke(fresh_state("some 2+3"))
    # Then: executado com o resultado certo
    assert result["outcome"] == "executed"
    assert "5" in result["observation"]
    assert "5" in result["answer"]


def test_unknown_tool_denied_without_execution():
    # Given: plano para ferramenta fora da allowlist
    fake = FakeListChatModel(responses=['{"tool": "format_disk", "args": {}}'])
    graph = build_graph(llm=fake, clock=lambda: "2026-01-01T00:00:00")
    # When: pipeline completo
    result = graph.invoke(fresh_state("apague tudo"))
    # Then: negado, nada executado, recusa cita a ferramenta
    assert result["outcome"] == "denied"
    assert "format_disk" in result["answer"]


def test_invalid_plan_json_raises():
    # Given: plano que não é JSON válido
    fake = FakeListChatModel(responses=["vou somar, confia"])
    graph = build_graph(llm=fake, clock=lambda: "2026-01-01T00:00:00")
    # When/Then: falha explícita antes de qualquer execução
    with pytest.raises(ValidationError):
        graph.invoke(fresh_state("some 1+1"))


def test_live_sum_via_add_tool():
    # Given: servidor local
    try:
        httpx.get("http://127.0.0.1:8080/health", timeout=5).raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"llama-server ausente: {exc}")
    # When: pedido de soma ao Gemma
    graph = build_graph()
    result = graph.invoke(fresh_state("Quanto é 2+3? Use a ferramenta add."))
    # Then: executado com o resultado correto
    assert result["outcome"] == "executed"
    assert "5" in result["observation"]
