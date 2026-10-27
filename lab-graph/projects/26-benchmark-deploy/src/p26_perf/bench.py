"""P26: benchmark honesto — percentis medidos, concorrência isolada, teto."""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass


@dataclass(frozen=True)
class OverBudget(Exception):
    """Deploy barrado: p50 medido acima do teto contratado."""

    reason: str

    def __str__(self) -> str:
        return f"over budget: {self.reason}"


def percentile(samples: list[float], pct: float) -> float:
    """Percentil por interpolação linear (amostras ordenadas)."""
    if not samples:
        return 0.0
    ordered = sorted(samples)
    if len(ordered) == 1:
        return ordered[0]
    rank = (pct / 100.0) * (len(ordered) - 1)
    low = int(rank)
    high = min(low + 1, len(ordered) - 1)
    frac = rank - low
    return ordered[low] * (1.0 - frac) + ordered[high] * frac


def benchmark(
    fn: Callable[[], object], repeats: int = 20, warmup: int = 3
) -> dict:
    """Mede warmup + N repetições; devolve n/min/p50/p95/max em ms."""
    for _ in range(warmup):
        fn()
    samples = []
    for _ in range(repeats):
        started = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - started) * 1000.0)
    return {
        "n": len(samples),
        "min_ms": min(samples),
        "p50_ms": percentile(samples, 50),
        "p95_ms": percentile(samples, 95),
        "max_ms": max(samples),
    }


def run_concurrent(
    invoke: Callable[[dict, dict], dict], payloads: list[dict]
) -> list[dict]:
    """Executa cada payload na sua thread_id; ordem de saída = entrada."""
    configs = [
        {"configurable": {"thread_id": f"bench-{i}"}}
        for i in range(len(payloads))
    ]

    def one(pair: tuple) -> dict:
        payload, config = pair
        return invoke(dict(payload), config)

    with ThreadPoolExecutor(max_workers=len(payloads) or 1) as pool:
        return list(pool.map(one, zip(payloads, configs, strict=True)))


def budget_check(p50_ms: float, ceiling_ms: float) -> float:
    """Barra deploy acima do teto; devolve o p50 se dentro."""
    if p50_ms > ceiling_ms:
        raise OverBudget(f"p50 {p50_ms:.2f}ms > {ceiling_ms:.2f}ms")
    return p50_ms


def deployment_report(p50_ms: float, ceiling_ms: float) -> dict:
    """Gate de deploy local: verde só com budget dentro do teto."""
    try:
        budget_check(p50_ms, ceiling_ms)
    except OverBudget as blocked:
        return {"deploy": False, "reason": str(blocked)}
    return {"deploy": True, "reason": f"p50 {p50_ms:.2f}ms <= teto"}
