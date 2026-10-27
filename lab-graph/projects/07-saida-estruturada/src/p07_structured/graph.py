"""P07: saída estruturada — json_mode + validação Pydantic (sem tools)."""

from __future__ import annotations

from typing import TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict, Field

from local_lab.settings import DEFAULT_SETTINGS


class BookRating(BaseModel):
    """Avaliação de livro extraída do modelo (contrato de saída)."""

    model_config = ConfigDict(frozen=True)

    title: str
    score: int = Field(ge=0, le=10)
    tags: list[str]


class P07State(TypedDict):
    query: str
    rating: BookRating | None


PROMPT_TEMPLATE = (
    "Avalie o livro a seguir. Responda SOMENTE com JSON válido "
    "contendo as chaves title (str), score (int 0-10) e tags (lista de str). "
    "Sem nenhum texto fora do JSON.\nLivro: "
)


def render_prompt(query: str) -> str:
    """Compõe o prompt por concatenação (sem str.format nas chaves JSON)."""
    return PROMPT_TEMPLATE + query


def make_extract(llm: object) -> object:
    """Nó que extrai BookRating validado ou falha com ValidationError."""

    def extract(state: P07State) -> dict:
        response = llm.invoke(render_prompt(state["query"]))
        content = response.content if isinstance(response.content, str) else ""
        rating = BookRating.model_validate_json(content)
        return {"rating": rating}

    return extract


def build_llm() -> ChatOpenAI:
    """ChatOpenAI real em json_mode (function-calling vetado pelo P00)."""
    settings = DEFAULT_SETTINGS
    return ChatOpenAI(
        model=settings.llama_model,
        base_url=settings.llama_base_url,
        api_key="local-not-needed",
        temperature=0,
        max_tokens=settings.llama_max_output_tokens,
        timeout=settings.llama_timeout_s,
        model_kwargs={"response_format": {"type": "json_object"}},
    )


def build_graph(llm: object | None = None) -> object:
    """Monta START→extract→END; sem `llm`, usa o Gemma real."""
    chosen = llm if llm is not None else build_llm()
    builder: StateGraph = StateGraph(P07State)
    builder.add_node("extract", make_extract(chosen))
    builder.add_edge(START, "extract")
    builder.add_edge("extract", END)
    return builder.compile()
