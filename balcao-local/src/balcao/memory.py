"""Persistence: SQLite checkpoints per ticket, store for customer profile."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.base import BaseStore
from langgraph.store.memory import InMemoryStore
from langgraph.store.postgres import PostgresStore


@contextmanager
def open_checkpointer(db_path: Path) -> Iterator[SqliteSaver]:
    """Yield a SQLite saver; the file persists across runs for time travel."""
    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        yield saver


def open_store() -> BaseStore:
    """Return the cross-thread profile store (BaseStore-typed accessor)."""
    return InMemoryStore()


def remember_customer(store: BaseStore, customer: str, name: str) -> None:
    """Persist the customer display name under the `perfil` namespace."""
    store.put(("perfil",), customer, {"name": name})


def recall_customer(store: BaseStore, customer: str) -> str | None:
    """Recall the display name, or None for a first-time customer."""
    item = store.get(("perfil",), customer)
    if item is None:
        return None
    value = item.value.get("name")
    return value if isinstance(value, str) else None


__all__ = [
    "open_checkpointer",
    "open_pg_saver",
    "open_pg_store",
    "open_store",
    "recall_customer",
    "remember_customer",
]


@contextmanager
def open_pg_saver(conn_string: str) -> Iterator[PostgresSaver]:
    """Yield a Postgres saver with tables created (production checkpoints)."""
    with PostgresSaver.from_conn_string(conn_string) as saver:
        saver.setup()
        yield saver


@contextmanager
def open_pg_store(conn_string: str) -> Iterator[PostgresStore]:
    """Yield a Postgres store with tables created (production profiles)."""
    with PostgresStore.from_conn_string(conn_string) as store:
        store.setup()
        yield store