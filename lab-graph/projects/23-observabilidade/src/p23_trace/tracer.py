"""P23: tracing local — eventos por nó, sanitize de segredos e métricas."""

from __future__ import annotations

import time
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class P23State(TypedDict):
    n: int
    doubled: int
    secret: str


def double(state: P23State) -> dict:
    """Dobra a entrada (nó observado)."""
    return {"doubled": state["n"] * 2}


def finish(state: P23State) -> dict:
    """Nó final; só marca presença no trace."""
    return {}


def build_graph() -> object:
    """Monta START→double→finish→END e retorna compilado."""
    builder: StateGraph = StateGraph(P23State)
    builder.add_node("double", double)
    builder.add_node("finish", finish)
    builder.add_edge(START, "double")
    builder.add_edge("double", "finish")
    builder.add_edge("finish", END)
    return builder.compile()


DENYLIST = ("secret", "api_key", "token")


def sanitize(payload: dict | None, denylist: tuple = DENYLIST) -> dict:
    """Copia sem as chaves negadas (original intacto; None vira {})."""
    if payload is None:
        return {}
    return {k: v for k, v in payload.items() if k not in denylist}


class Tracer:
    """Envolve o grafo: registra eventos sanitizados e agrega métricas."""

    def __init__(self, graph: object, denylist: tuple = DENYLIST) -> None:
        self.graph = graph
        self.denylist = denylist
        self.events: list[dict] = []
        self.calls: dict[str, int] = {}
        self.errors: dict[str, int] = {}

    def run(self, payload: dict) -> dict:
        """Executa consumindo updates; erro é registrado e relançado.

        Devolve a fusão dos updates observados. `latency_ms` é o tempo
        entre eventos (proxy observável, não instrumentação interna).
        """
        result: dict = {}
        previous = time.perf_counter()
        try:
            for chunk in self.graph.stream(payload):
                node = next(iter(chunk))
                now = time.perf_counter()
                latency_ms = (now - previous) * 1000.0
                previous = now
                logged = sanitize(chunk[node], self.denylist)
                self.events.append(
                    {
                        "node": node,
                        "keys": sorted(logged),
                        "latency_ms": latency_ms,
                    }
                )
                self.calls[node] = self.calls.get(node, 0) + 1
                if chunk[node] is not None:
                    result = {**result, **chunk[node]}
        except Exception as exc:
            self.errors[type(exc).__name__] = (
                self.errors.get(type(exc).__name__, 0) + 1
            )
            raise
        return result

    def summary(self) -> dict:
        """Agrega a execução: nós, chamadas, erros e tempo total."""
        total = sum(e["latency_ms"] for e in self.events)
        return {
            "nodes": [e["node"] for e in self.events],
            "calls": dict(self.calls),
            "total_ms": total,
            "errors": dict(self.errors),
        }
