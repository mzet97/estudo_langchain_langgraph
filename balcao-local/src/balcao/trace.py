"""Local tracer: records run names and timing, never message content."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from langchain_core.callbacks import BaseCallbackHandler


@dataclass
class SanitizedEvent:
    """One sanitized event: what ran and how long, not what was said."""

    kind: str
    name: str
    elapsed_ms: float = 0.0


@dataclass(eq=False)
class EventLog(BaseCallbackHandler):
    """Callback handler that proves observability without leaking secrets.

    Identity hash: langchain deduplicates handlers in a set, so eq-based
    hashing would break with unhashable instances.
    """

    events: list[SanitizedEvent] = field(default_factory=list)
    _starts: dict[str, float] = field(default_factory=dict)

    def on_chain_start(
        self, serialized: dict | None, inputs: dict, **kwargs: object
    ) -> None:
        name = str((serialized or {}).get("name", "?"))
        self._starts[name] = time.perf_counter()
        self.events.append(SanitizedEvent(kind="start", name=name))

    def on_chain_end(
        self, outputs: dict, **kwargs: object
    ) -> None:
        name = str(kwargs.get("run_name", "?"))
        started = self._starts.pop(name, None)
        elapsed = (
            (time.perf_counter() - started) * 1000.0 if started is not None else 0.0
        )
        self.events.append(SanitizedEvent(kind="end", name=name, elapsed_ms=elapsed))

    def names(self) -> list[str]:
        """Event names in order; used by tests, never shipped to clients."""
        return [e.name for e in self.events]
