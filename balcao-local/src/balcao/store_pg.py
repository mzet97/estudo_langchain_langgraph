"""Postgres-backed provider: invoices and the effects ledger."""

from __future__ import annotations

import psycopg


class PostgresLedger:
    """Real backend: every read/write hits Postgres (no in-memory state)."""

    def __init__(self, conn_string: str) -> None:
        self._conn_string = conn_string

    def get_invoice(self, customer: str) -> str:
        """Return the invoice status line, or the no-open-invoice default."""
        with psycopg.connect(self._conn_string) as conn:
            row = conn.execute(
                "SELECT status FROM invoices WHERE customer = %s", (customer,)
            ).fetchone()
        if row is None:
            return "sem fatura em aberto"
        return str(row[0])

    def open_ticket(self, customer: str, motivo: str) -> str:
        """Insert a ticket row; the code derives from the serial id."""
        with psycopg.connect(self._conn_string) as conn:
            pk = conn.execute(
                "INSERT INTO ledger (code, customer, kind, detail) "
                "VALUES ('pending', %s, 'ticket', %s) RETURNING id",
                (customer, motivo),
            ).fetchone()[0]
            code = f"CH-{pk:04d}"
            conn.execute("UPDATE ledger SET code = %s WHERE id = %s", (code, pk))
            conn.commit()
        return code

    def schedule_visit(self, customer: str, janela: str) -> str:
        """Insert a visit row; the code derives from the serial id."""
        with psycopg.connect(self._conn_string) as conn:
            pk = conn.execute(
                "INSERT INTO ledger (code, customer, kind, detail) "
                "VALUES ('pending', %s, 'visit', %s) RETURNING id",
                (customer, janela),
            ).fetchone()[0]
            code = f"AG-{pk:04d}"
            conn.execute("UPDATE ledger SET code = %s WHERE id = %s", (code, pk))
            conn.commit()
        return code

    def count(self) -> int:
        """Row count; used by the E2E exactly-once assertion."""
        with psycopg.connect(self._conn_string) as conn:
            row = conn.execute("SELECT COUNT(*) FROM ledger").fetchone()
        return int(row[0])
