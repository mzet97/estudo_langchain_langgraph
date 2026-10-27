"""M6 eval: golden de triagem (SC-05) e citação/abstenção."""

import json
import sys
from pathlib import Path

from langchain_core.exceptions import OutputParserException
from langchain_core.runnables import RunnableLambda

sys.path.insert(0, "src")

from balcao.gateway import Backend
from balcao.graph import build_graph
from balcao.kb import Retriever, load_kb
from balcao.nodes import make_triage

CASES = json.loads((Path(__file__).parent / "golden_triage.json").read_text())


def _graph() -> object:
    return build_graph(
        Retriever.build(load_kb(Path("kb"))), Backend(), auto_approve=True
    )


def test_golden_triagem_atinge_90_por_cento() -> None:
    # Given: 10 casos golden e o grafo offline
    graph = _graph()
    # When: cada mensagem é triada
    hits = 0
    for case in CASES:
        out = graph.invoke({"ticket": "g", "customer": "c", "message": case["message"]})
        if out["category"] == case["category"]:
            hits += 1
    # Then: acurácia ≥ 90% (SC-05)
    assert hits / len(CASES) >= 0.90


def test_triage_recupera_de_json_malformado() -> None:
    # Given: classificador que sempre quebra o parse (como o Gemma ao
    # inventar "chamado" fora do enum)
    def broken(value: object) -> object:
        raise OutputParserException("category fora do enum")

    node = make_triage(RunnableLambda(broken))
    # When: mensagem de fatura passa pelo nó
    out = node({"message": "quero a segunda via"})
    # Then: fallback determinístico classifica sem 500
    assert out["category"] == "fatura"
    assert out["needs_action"] is True


def test_golden_citacao_ou_abstencao_100_por_cento() -> None:
    # Given: mensagens com e sem fonte
    graph = _graph()
    covered = [
        "quero a segunda via",
        "como pago no pix",
        "luz los vermelha na ont",
        "agendar visita de manha",
    ]
    # When/Then: toda resposta coberta cita fonte
    for message in covered:
        out = graph.invoke({"ticket": "g", "customer": "c", "message": message})
        assert "[fonte:" in out["answer"], message
    # When/Then: sem fonte, abstenção exata
    out = graph.invoke(
        {"ticket": "g", "customer": "c", "message": "qual meu horoscopo de hoje"}
    )
    assert out["answer"] == "Não encontrei essa informação nos runbooks."
