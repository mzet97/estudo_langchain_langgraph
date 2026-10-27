"""P06: primeiro nó com LLM real — ChatOpenAI no llama-server local."""

from __future__ import annotations

from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from local_lab.settings import DEFAULT_SETTINGS


class P06State(TypedDict):
    question: str
    answer: str


def make_ask(llm: object) -> object:
    """Nó que pergunta ao LLM e guarda o conteúdo da resposta."""

    def ask(state: P06State) -> dict:
        response = llm.invoke(state["question"])
        content = response.content if isinstance(response.content, str) else ""
        if not content.strip():
            raise ValueError("empty answer from model")
        return {"answer": content}

    return ask


def build_llm() -> ChatOpenAI:
    """Cria o ChatOpenAI real contra o llama-server local."""
    settings = DEFAULT_SETTINGS
    return ChatOpenAI(
        model=settings.llama_model,
        base_url=settings.llama_base_url,
        api_key="local-not-needed",
        temperature=0,
        max_tokens=settings.llama_max_output_tokens,
        timeout=settings.llama_timeout_s,
    )


def build_graph(llm: object | None = None) -> object:
    """Monta START→ask→END; sem `llm`, usa o Gemma real."""
    chosen = llm if llm is not None else build_llm()
    builder: StateGraph = StateGraph(P06State)
    builder.add_node("ask", make_ask(chosen))
    builder.add_edge(START, "ask")
    builder.add_edge("ask", END)
    return builder.compile()
