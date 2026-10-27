"""P09 tests: histórico ordenado, 2 turnos e memória live."""

import sys
from pathlib import Path

import httpx
import pytest
from langchain_core.language_models.fake_chat_models import (
    FakeListChatModel,
)
from langchain_core.messages import HumanMessage

HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parents[1] / "src"))
sys.path.insert(0, str(HERE.parents[3] / "src"))

from p09_messages.graph import build_graph


def test_two_turns_keep_ordered_history():
    # Given: fake com 2 respostas e 1º turno já respondido
    fake = FakeListChatModel(responses=["olá!", "tudo bem."])
    graph = build_graph(llm=fake)
    first = graph.invoke({"messages": [HumanMessage(content="oi")]})
    # When: 2º turno carrega o histórico do 1º
    second = graph.invoke(
        {"messages": [*first["messages"], HumanMessage(content="e aí?")]}
    )
    # Then: 4 mensagens em ordem, sem perda
    texts = [
        m.content for m in second["messages"] if isinstance(m.content, str)
    ]
    assert texts == ["oi", "olá!", "e aí?", "tudo bem."]


def test_empty_reply_raises():
    # Given: modelo mudo
    fake = FakeListChatModel(responses=["  "])
    graph = build_graph(llm=fake)
    # When/Then: falha explícita
    with pytest.raises(ValueError, match="empty reply"):
        graph.invoke({"messages": [HumanMessage(content="oi")]})


def test_live_remembers_name():
    # Given: servidor local
    try:
        httpx.get("http://127.0.0.1:8080/health", timeout=5).raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"llama-server ausente: {exc}")
    # When: declara nome e depois pergunta
    graph = build_graph()
    first = graph.invoke({"messages": [HumanMessage(content="Meu nome é Ada.")]})
    second = graph.invoke(
        {
            "messages": [
                *first["messages"],
                HumanMessage(content="Qual é o meu nome? Responda só o nome."),
            ]
        }
    )
    # Then: contexto carregado entre turnos
    last = second["messages"][-1].content
    assert isinstance(last, str) and "Ada" in last
