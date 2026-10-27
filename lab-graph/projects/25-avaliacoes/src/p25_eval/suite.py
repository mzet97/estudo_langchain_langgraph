"""P25: golden suite — dados julgam, limiar pré-registrado barra."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    """Um caso golden: id estável, entrada e esperado congelados."""

    id: str
    input: object
    expected: object


@dataclass(frozen=True)
class RegressionBlocked(Exception):
    """Gate barrado: taxa abaixo do limiar pré-registrado."""

    reason: str

    def __str__(self) -> str:
        return f"regression blocked: {self.reason}"


GOLDEN_DOUBLE: list[Case] = [
    Case(id="double-zero", input=0, expected=0),
    Case(id="double-pos", input=21, expected=42),
    Case(id="double-neg", input=-3, expected=-6),
]

GOLDEN_SHOUT: list[Case] = [
    Case(id="shout-word", input="olá", expected="OLÁ"),
    Case(id="shout-empty", input="", expected=""),
]


def target_double(n: int) -> int:
    """Função sob teste (correta): dobra."""
    return n * 2


def target_shout(text: str) -> str:
    """Função sob teste (correta): maiúsculas."""
    return text.upper()


def run_suite(
    cases: list[Case], fn: Callable[[object], object]
) -> list[dict]:
    """Roda cada caso e registra passou/falhou sem mascarar."""
    results = []
    for case in cases:
        try:
            got = fn(case.input)
            passed = got == case.expected
        except Exception as exc:  # noqa: BLE001 - falha é dado do relatório
            got = f"{type(exc).__name__}: {exc}"
            passed = False
        results.append(
            {
                "id": case.id,
                "passed": passed,
                "expected": case.expected,
                "got": got,
            }
        )
    return results


def pass_rate(results: list[dict]) -> float:
    """Taxa de acerto em [0,1]; suite vazia vale 0."""
    if not results:
        return 0.0
    return sum(1 for r in results if r["passed"]) / len(results)


def gate(results: list[dict], min_rate: float) -> float:
    """Barra regressão abaixo do limiar; devolve a taxa se passar."""
    rate = pass_rate(results)
    if rate < min_rate:
        failed = [r["id"] for r in results if not r["passed"]]
        raise RegressionBlocked(f"rate {rate:.2f} < {min_rate:.2f}: {failed}")
    return rate
