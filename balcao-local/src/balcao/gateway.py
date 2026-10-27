"""Allowlisted tools behind a deny-by-default gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import NoReturn, Protocol

from balcao.models import ActionPlan

ALLOWED_TOOLS = ("get_invoice", "open_ticket", "schedule_visit")
READ_ONLY_TOOLS = ("get_invoice",)
GATEWAY_IDENTITY = "balcao"


@dataclass(frozen=True, slots=True)
class DeniedError(Exception):
    """Typed denial: which tool was refused and why."""

    tool: str
    reason: str

    def __str__(self) -> str:
        return f"denied tool={self.tool} reason={self.reason}"


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """One frozen audit row per gateway decision."""

    identity: str
    tool: str
    verdict: str


@dataclass(slots=True)
class Backend:
    """In-memory test-double backend; production uses PostgresLedger.

    Mutation is the documented purpose: it records side effects so tests
    can assert exactly-once execution.
    """

    invoices: dict[str, str] = field(default_factory=dict)
    ledger: list[str] = field(default_factory=list)

    def get_invoice(self, customer: str) -> str:
        """Return the invoice status line for a customer."""
        return self.invoices.get(customer, "sem fatura em aberto")

    def open_ticket(self, customer: str, motivo: str) -> str:
        """Open a ticket and record it; returns the ticket code."""
        code = f"CH-{len(self.ledger) + 1:04d}"
        self.ledger.append(f"{code}:{customer}:{motivo}")
        return code

    def schedule_visit(self, customer: str, janela: str) -> str:
        """Schedule a visit and record it; returns the confirmation."""
        code = f"AG-{len(self.ledger) + 1:04d}"
        self.ledger.append(f"{code}:{customer}:{janela}")
        return code


class Ledger(Protocol):
    """Structural contract any real or test-double backend must satisfy."""

    def get_invoice(self, customer: str) -> str: ...
    def open_ticket(self, customer: str, motivo: str) -> str: ...
    def schedule_visit(self, customer: str, janela: str) -> str: ...


@dataclass(frozen=True, slots=True)
class ToolGateway:
    """Executes validated plans; denies unknown tools and missing approval."""

    backend: Ledger
    audit: list[AuditRecord] = field(default_factory=list)

    def call(self, identity: str, plan: ActionPlan, customer: str) -> str:
        """Execute or record a denial and raise."""
        if plan.tool not in ALLOWED_TOOLS:
            self._deny(identity, plan.tool, "denied:unknown-tool")
        if identity != GATEWAY_IDENTITY:
            self._deny(identity, plan.tool, "denied:identity")
        match plan.tool:
            case "get_invoice":
                result = self.backend.get_invoice(customer)
            case "open_ticket":
                result = self.backend.open_ticket(
                    customer, plan.args.get("motivo", "")
                )
            case "schedule_visit":
                result = self.backend.schedule_visit(
                    customer, plan.args.get("janela", "")
                )
            case _:
                self._deny(identity, plan.tool, "denied:unknown-tool")
        self.audit.append(AuditRecord(identity, plan.tool, "allowed"))
        return result

    def refuse(self, plan: ActionPlan) -> str:
        """Record a denied approval and return the refusal message."""
        self.audit.append(AuditRecord(GATEWAY_IDENTITY, plan.tool, "denied:approval"))
        return "ação negada pelo responsável"

    def _deny(self, identity: str, tool: str, verdict: str) -> NoReturn:
        self.audit.append(AuditRecord(identity, tool, verdict))
        raise DeniedError(tool, verdict.removeprefix("denied:"))
