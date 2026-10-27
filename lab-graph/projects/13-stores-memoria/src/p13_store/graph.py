"""P13: Store — memória (namespace, key) compartilhada entre threads."""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore


class P13State(TypedDict):
    mode: Literal["store", "recall"]
    ns: str
    key: str
    value: str
    answer: str


def memorize(state: P13State, store: BaseStore) -> dict:
    """Grava (ns, key) -> value no Store e confirma."""
    namespace = (state["ns"],)
    store.put(namespace, state["key"], {"value": state["value"]})
    return {"answer": f"stored:{state['key']}"}


def recall(state: P13State, store: BaseStore) -> dict:
    """Lê (ns, key) do Store; chave ausente é erro explícito."""
    item = store.get((state["ns"],), state["key"])
    if item is None:
        raise ValueError(f"no memory for {(state['ns'], state['key'])}")
    return {"answer": item.value["value"]}


def route_mode(state: P13State) -> Literal["memorize", "recall"]:
    """Desvia pelo modo pedido (dado, nunca palpite)."""
    if state["mode"] == "store":
        return "memorize"
    return "recall"


def build_graph(store: object | None = None) -> object:
    """Monta START→{memorize|recall}→END com o Store compartilhado."""
    builder: StateGraph = StateGraph(P13State)
    builder.add_node("memorize", memorize)
    builder.add_node("recall", recall)
    builder.add_conditional_edges(
        START, route_mode, {"memorize": "memorize", "recall": "recall"}
    )
    builder.add_edge("memorize", END)
    builder.add_edge("recall", END)
    return builder.compile(store=store or InMemoryStore())
