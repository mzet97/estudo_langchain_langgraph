"""M5: cadeias LLM reais contra o llama-server local (json_mode + Pydantic)."""

from __future__ import annotations

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from balcao.models import ActionPlan, TriageOut
from balcao.settings import DEFAULT_SETTINGS


def build_llm(timeout_s: float | None = None) -> ChatOpenAI:
    """ChatOpenAI real em json_mode; base_url sempre local."""
    settings = DEFAULT_SETTINGS
    return ChatOpenAI(
        model=settings.llama_model,
        base_url=settings.llama_base_url,
        api_key="local-not-needed",
        temperature=0,
        max_tokens=settings.llama_max_output_tokens,
        timeout=timeout_s or settings.llama_timeout_s,
        model_kwargs={"response_format": {"type": "json_object"}},
    )


def triage_chain(llm: ChatOpenAI | None = None) -> Runnable:
    """Prompt → LLM → TriageOut validado; injetável em build_graph."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Classifique o pedido do cliente da VelaNet. Responda SOMENTE "
                    "com JSON válido no formato "
                    "usando APENAS estes valores de category, sem inventar outros: "
                    '{{"category": "fatura|tecnico|agendamento|desconhecido", '
                    '"needs_action": true|false}}. needs_action=true quando o '
                    "cliente pede efeito: chamado, visita, segunda via."
                ),
            ),
            ("human", "{message}"),
        ]
    )
    return prompt | (llm or build_llm()) | PydanticOutputParser(pydantic_object=TriageOut)


def planner_chain(llm: ChatOpenAI | None = None) -> Runnable:
    """Mensagem → ActionPlan validado; só é chamada quando há ação."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "Escolha a ferramenta para o pedido. Responda SOMENTE com "
                    'JSON válido no formato {{"tool": "<nome>", "args": '
                    "{{...}}}}. Ferramentas: get_invoice (2ª via/fatura, args "
                    "{{}}), open_ticket (chamado; args {{\"motivo\"}}), "
                    "schedule_visit (visita; args {{\"janela\": manha|tarde}})."
                ),
            ),
            ("human", "{message}"),
        ]
    )
    return (
        prompt | (llm or build_llm(timeout_s=120)) | PydanticOutputParser(pydantic_object=ActionPlan)
    )
