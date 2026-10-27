"""P15: async, streaming por updates e cancelamento no consumidor."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

import anyio
import anyio.lowlevel
from langgraph.graph import END, START, StateGraph


class P15State(TypedDict):
    log: Annotated[list[str], operator.add]


async def step_a(state: P15State) -> dict:
    """Etapa A assíncrona: cede o loop e registra passagem."""
    await anyio.lowlevel.checkpoint()
    return {"log": ["a"]}


async def step_b(state: P15State) -> dict:
    """Etapa B assíncrona: cede o loop e registra passagem."""
    await anyio.lowlevel.checkpoint()
    return {"log": ["b"]}


def build_graph() -> object:
    """Monta START→step_a→step_b→END (nós async) e retorna compilado."""
    builder: StateGraph = StateGraph(P15State)
    builder.add_node("step_a", step_a)
    builder.add_node("step_b", step_b)
    builder.add_edge(START, "step_a")
    builder.add_edge("step_a", "step_b")
    builder.add_edge("step_b", END)
    return builder.compile()
