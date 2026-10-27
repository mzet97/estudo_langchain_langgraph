"""Typed errors: transient failures retry, programming errors fail fast."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransientProviderError(Exception):
    """Slots-free: Exception subclasses with __slots__ break copy/pickle."""
    """Simulated flaky provider; retried by the graph RetryPolicy."""

    detail: str

    def __str__(self) -> str:
        return f"transient provider failure: {self.detail}"
