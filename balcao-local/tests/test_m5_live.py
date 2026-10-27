"""M5: triagem e plano via Gemma real; SKIP se o servidor estiver fora."""

import sys
from pathlib import Path

import httpx
import pytest
from openai import OpenAIError

sys.path.insert(0, "src")

from balcao.chains import build_llm, planner_chain, triage_chain
from balcao.gateway import Backend
from balcao.graph import build_graph
from balcao.kb import Retriever, load_kb

LiveError = (httpx.HTTPError, httpx.TimeoutException, OpenAIError)


def _skip(exc: Exception) -> pytest.skip:
    return pytest.skip(f"llama-server ausente: {exc}")


def test_live_triage_fatura() -> None:
    # Given: cadeia de triagem real
    chain = triage_chain()
    # When: pedido de segunda via
    try:
        out = chain.invoke({"message": "quero a segunda via da minha fatura"})
    except LiveError as exc:
        raise _skip(exc)
    # Then: categoria fatura com ação
    assert out.category == "fatura"
    assert out.needs_action is True


def test_live_triage_tecnico() -> None:
    # Given: cadeia de triagem real
    chain = triage_chain()
    # When: LOS vermelha sem pedir chamado
    try:
        out = chain.invoke({"message": "luz los vermelha acesa na ont"})
    except LiveError as exc:
        raise _skip(exc)
    # Then: técnico, sem ação
    assert out.category == "tecnico"
    assert out.needs_action is False


def test_live_planner_abre_chamado() -> None:
    # Given: cadeia de plano real
    chain = planner_chain()
    # When: pedido de chamado
    try:
        plan = chain.invoke({"message": "abram um chamado, internet caiu tudo"})
    except LiveError as exc:
        raise _skip(exc)
    # Then: ferramenta allowlisted com motivo
    assert plan.tool == "open_ticket"
    assert plan.args.get("motivo") != ""


def test_live_grafo_com_cadeias_llm() -> None:
    # Given: grafo com classificador real injetado
    kb = Retriever.build(load_kb(Path("kb")))
    graph = build_graph(
        kb,
        Backend(),
        classifier=triage_chain(),
        auto_approve=True,
    )
    # When: pedido técnico roda de ponta a ponta
    try:
        out = graph.invoke(
            {"ticket": "t", "customer": "c", "message": "wifi fraco no quarto"}
        )
    except LiveError as exc:
        raise _skip(exc)
    # Then: triagem real classificou e respondeu com citação
    assert out["category"] == "tecnico"
    assert "[fonte:" in out["answer"]


def test_live_cliente_aponta_para_servidor_local() -> None:
    # Given: LLM padrão
    llm = build_llm()
    # Then: base local, nunca nuvem
    assert "127.0.0.1" in str(llm.openai_api_base)
