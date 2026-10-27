"""P06 tests: offline com fake + live contra o servidor (SKIP se ausente)."""

import sys
from pathlib import Path

import httpx
import pytest
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
)

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))
sys.path.insert(0, str(HERE.parents[3] / "src"))

from p06_llm.graph import build_graph


def test_offline_fake_answer_is_deterministic():
    # Given: LLM programado com resposta fixa
    fake = FakeListChatModel(responses=["resposta fixa"])
    graph = build_graph(llm=fake)
    # When: invocação
    result = graph.invoke({"question": "qualquer", "answer": ""})
    # Then: exatamente a resposta programada
    assert result["answer"] == "resposta fixa"


def test_offline_empty_answer_fails_loudly():
    # Given: LLM que devolve vazio
    fake = FakeListChatModel(responses=["   "])
    graph = build_graph(llm=fake)
    # When/Then: falha explícita em vez de resposta vazia
    with pytest.raises(ValueError, match="empty answer"):
        graph.invoke({"question": "qualquer", "answer": ""})


def test_live_server_answers():
    # Given: servidor local (prova de vida antes de gastar inferência)
    try:
        httpx.get("http://127.0.0.1:8080/health", timeout=5).raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"llama-server ausente: {exc}")
    # When: pergunta real ao Gemma
    graph = build_graph()
    result = graph.invoke({"question": "Diga apenas OK", "answer": ""})
    # Then: resposta não vazia
    assert result["answer"].strip() != ""
