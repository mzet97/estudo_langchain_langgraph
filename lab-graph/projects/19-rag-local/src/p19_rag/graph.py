"""P19: RAG local — retrieve por overlap, resposta com citação ou abstenção."""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class Doc(TypedDict):
    id: str
    text: str


DOCS: list[Doc] = [
    {
        "id": "reducer",
        "text": "Reducers fundem escritas paralelas no estado; sem reducer vale o último escritor.",
    },
    {
        "id": "checkpoint",
        "text": "Checkpointers gravam snapshots por thread_id e permitem retomar e bifurcar.",
    },
    {
        "id": "retry",
        "text": "RetryPolicy repete o nó em falha transitória; erro de programação não é retentado.",
    },
    {
        "id": "send",
        "text": "Send cria tarefas em runtime pela aresta condicional; o reducer junta os resultados.",
    },
]


class P19State(TypedDict):
    query: str
    sources: list[str]
    answer: str
    grounded: bool


def tokenize(text: str) -> set[str]:
    """Normaliza em tokens minúsculos sem pontuação comum."""
    cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
    return {w for w in cleaned.split() if len(w) > 2}


def retrieve(query: str, docs: list[Doc] | None = None, k: int = 2) -> list[Doc]:
    """Recupera até k docs por overlap de tokens (só overlap ≥ 1)."""
    corpus = docs if docs is not None else DOCS
    scored = [
        (len(tokenize(query) & tokenize(doc["text"])), doc) for doc in corpus
    ]
    ranked = sorted(
        (doc for score, doc in scored if score >= 1),
        key=lambda d: len(tokenize(query) & tokenize(d["text"])),
        reverse=True,
    )
    return ranked[:k]


def make_answer(retriever: object) -> object:
    """Nó que responde só com fontes ou declara abstenção."""

    def answer(state: P19State) -> dict:
        found = retriever(state["query"])
        if not found:
            return {
                "sources": [],
                "answer": "Sem fonte local — abstenho-me de responder.",
                "grounded": False,
            }
        first = found[0]
        return {
            "sources": [doc["id"] for doc in found],
            "answer": f"{first['text']} [{first['id']}]",
            "grounded": True,
        }

    return answer


def build_graph(retriever: object | None = None) -> object:
    """Monta START→answer→END com o retriever dado (ou o local)."""
    chosen = retriever if retriever is not None else retrieve
    builder: StateGraph = StateGraph(P19State)
    builder.add_node("answer", make_answer(chosen))
    builder.add_edge(START, "answer")
    builder.add_edge("answer", END)
    return builder.compile()
