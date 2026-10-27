"""P20: functional API — tasks compondo pipeline via entrypoint."""

from __future__ import annotations

from langgraph.func import entrypoint, task


@task
def double(n: int) -> int:
    """Dobra um inteiro (task pura, testável isolada)."""
    return n * 2


@task
def add(a: int, b: int) -> int:
    """Soma dois inteiros (task pura, testável isolada)."""
    return a + b


@entrypoint()
def pipeline(payload: dict) -> int:
    """Orquestra double→double→add como código direto, sem builder."""
    first = double(payload["n"]).result()
    second = double(payload["m"]).result()
    return add(first, second).result()
