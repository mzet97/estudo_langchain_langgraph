"""P09: conversa multi-turno — MessagesState acumula via add_messages."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import AIMessage, AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from local_lab.settings import DEFAULT_SETTINGS


class P09State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def make_chat(llm: object) -> object:
    """Nó que responde no contexto do histórico e anexa a resposta."""

    def chat(state: P09State) -> dict:
        response = llm.invoke(state["messages"])
        content = response.content if isinstance(response.content, str) else ""
        if not content.strip():
            raise ValueError("empty reply from model")
        return {"messages": [AIMessage(content=content)]}

    return chat


def build_graph(llm: object | None = None) -> object:
    """Monta START→chat→END; sem `llm`, usa o Gemma real."""
    if llm is None:
        settings = DEFAULT_SETTINGS
        llm = ChatOpenAI(
            model=settings.llama_model,
            base_url=settings.llama_base_url,
            api_key="local-not-needed",
            temperature=0,
            max_tokens=128,
            timeout=settings.llama_timeout_s,
        )
    builder: StateGraph = StateGraph(P09State)
    builder.add_node("chat", make_chat(llm))
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    return builder.compile()
