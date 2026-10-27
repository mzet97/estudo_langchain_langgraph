"""Boundary models: enums, triage output, action plans, KB hits."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TypedDict

from pydantic import BaseModel, ConfigDict


class Category(StrEnum):
    """Ticket categories the triage can produce."""

    FATURA = "fatura"
    TECNICO = "tecnico"
    AGENDAMENTO = "agendamento"
    DESCONHECIDO = "desconhecido"


class TriageOut(BaseModel):
    """Parsed triage contract (LLM or keyword classifier output)."""

    model_config = ConfigDict(frozen=True)

    category: Category
    needs_action: bool


class ActionPlan(BaseModel):
    """Validated action proposal; only these tools exist."""

    model_config = ConfigDict(frozen=True)

    tool: str
    args: dict[str, str]


@dataclass(frozen=True, slots=True)
class DocHit:
    """One KB hit with its overlap score."""

    doc_id: str
    text: str
    score: float


ABSTAIN = "Não encontrei essa informação nos runbooks."


class TicketState(TypedDict, total=False):
    """Graph state; every key optional so nodes stay independent."""

    ticket: str
    customer: str
    message: str
    category: str
    needs_action: bool
    sources: list[DocHit]
    status: str
    answer: str
    attempts: int
    plan: ActionPlan | None
    approved: bool
    result: str
    done: bool
