"""Graph node factories: triage, retrieve, fetch, draft, propose, gate, act."""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.exceptions import OutputParserException
from langchain_core.prompt_values import PromptValue
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langgraph.types import Command, interrupt

from balcao.errors import TransientProviderError
from balcao.gateway import GATEWAY_IDENTITY, READ_ONLY_TOOLS, Ledger, ToolGateway
from balcao.kb import Retriever
from balcao.models import ABSTAIN, ActionPlan, Category, DocHit, TicketState, TriageOut

MAX_DRAFT_ATTEMPTS = 2

_CATEGORY_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.FATURA: (
        "fatura", "boleto", "pix", "pagamento", "atraso", "multa", "conta",
        "cobrança", "segunda via", "2 via", "2ª via",
    ),
    Category.TECNICO: (
        "sem internet", "conexão", "lenta", "lento", "wifi", "wi-fi", "los",
        "fibra", "roteador", "ont", "sinal", "caiu", "fora do ar", "travando",
    ),
    Category.AGENDAMENTO: (
        "visita", "agendar", "técnico em casa", "remarcar", "marcar",
    ),
}

_ACTION_KEYWORDS: tuple[str, ...] = (
    "chamado", "agendar", "agende", "visita", "segunda via", "2 via",
    "remarcar",
)


def keyword_triage(message: str) -> TriageOut:
    """Deterministic offline classifier; the LLM chain replaces it in M5."""
    lowered = message.lower()
    for category, words in _CATEGORY_KEYWORDS.items():
        if any(w in lowered for w in words):
            return TriageOut(
                category=category,
                needs_action=any(a in lowered for a in _ACTION_KEYWORDS),
            )
    return TriageOut(category=Category.DESCONHECIDO, needs_action=False)


def keyword_plan(message: str, category: Category) -> ActionPlan | None:
    """Deterministic offline planner; the LLM chain replaces it in M5."""
    lowered = message.lower()
    if "segunda via" in lowered or "2 via" in lowered:
        return ActionPlan(tool="get_invoice", args={})
    if "chamado" in lowered:
        return ActionPlan(tool="open_ticket", args={"motivo": message[:120]})
    if category is Category.AGENDAMENTO or "visita" in lowered:
        janela = "tarde" if "tarde" in lowered else "manha"
        return ActionPlan(tool="schedule_visit", args={"janela": janela})
    return None


def triage_prompt() -> ChatPromptTemplate:
    """Triage prompt; rendered before the (fake or real) classifier."""
    return ChatPromptTemplate.from_messages(
        [
            ("system", "Classifique o pedido do cliente da VelaNet."),
            ("human", "{message}"),
        ]
    )


def default_classifier() -> Runnable:
    """LCEL chain: prompt → keyword classifier (offline, deterministic)."""

    def _run(value: PromptValue) -> TriageOut:
        return keyword_triage(value.to_string())

    return triage_prompt() | RunnableLambda(_run)


def make_triage(classifier: Runnable | None = None) -> object:
    """Triage node; LLM chain in production, keywords only as fallback.

    When the model returns malformed JSON, the deterministic keyword
    classifier takes over so the request degrades instead of 500ing.
    """
    chain = classifier or default_classifier()

    def triage(state: TicketState) -> dict:
        try:
            out = chain.invoke({"message": state["message"]})
        except OutputParserException:
            out = keyword_triage(state["message"])
        if not isinstance(out, TriageOut):
            out = TriageOut.model_validate(out)
        return {"category": out.category.value, "needs_action": out.needs_action}

    return triage


def make_retrieve(retriever: Retriever) -> object:
    """Retrieve node: top-2 runbooks by overlap."""

    def retrieve(state: TicketState) -> dict:
        return {"sources": retriever.search(state["message"])}

    return retrieve


def make_fetch(backend: Ledger, failures: int = 0) -> object:
    """Status fetch; `failures` simulates a flaky provider for retry tests."""
    calls = {"n": 0}

    def fetch(state: TicketState) -> dict:
        calls["n"] += 1
        if calls["n"] <= failures:
            raise TransientProviderError("provider instavel (simulado)")
        customer = state.get("customer", "")
        return {"status": backend.get_invoice(customer)}

    return fetch


def default_render(sources: list[DocHit]) -> str:
    """Render the top hit with its citation."""
    top = sources[0]
    first_line = top.text.strip().splitlines()[0]
    return f"{first_line} [fonte:{top.doc_id}]"


def make_draft(render: Callable[[list[DocHit]], str] | None = None) -> object:
    """Draft node: cite the top source or abstain; counts attempts."""

    def draft(state: TicketState) -> dict:
        sources = state.get("sources", [])
        attempts = state.get("attempts", 0) + 1
        if not sources:
            return {"answer": ABSTAIN, "attempts": attempts}
        text = default_render(sources) if render is None else render(sources)
        return {"answer": text, "attempts": attempts}

    return draft


def make_propose(planner: Runnable | None = None) -> object:
    """Propose node: validated ActionPlan or None (pure, no effects)."""

    def propose(state: TicketState) -> dict:
        if not state.get("needs_action", False):
            return {"plan": None}
        if planner is None:
            plan = keyword_plan(
                state["message"], Category(state.get("category", "desconhecido"))
            )
        else:
            try:
                raw = planner.invoke(state["message"])
            except OutputParserException:
                raw = None
            if raw is None:
                plan = keyword_plan(
                    state["message"], Category(state.get("category", "desconhecido"))
                )
            else:
                plan = (
                    raw
                    if isinstance(raw, ActionPlan)
                    else ActionPlan.model_validate(raw)
                )
        return {"plan": plan}

    return propose


def _draft_ok(state: TicketState) -> str:
    if (
        state.get("sources")
        and "[fonte:" not in state.get("answer", "")
        and state.get("attempts", 0) < MAX_DRAFT_ATTEMPTS
    ):
        return "draft"
    return "end"


def make_gate(gateway: ToolGateway, auto_approve: bool = False) -> object:
    """Approval gate: reads run free, writes wait for a human resume.

    `auto_approve` exists for pre-HITL offline tests only; production and
    the M4 tests always go through `interrupt`.
    """

    def gate(state: TicketState) -> Command:
        plan = state.get("plan")
        if plan is None:
            return Command(goto="finalize")
        if plan.tool in READ_ONLY_TOOLS or auto_approve:
            return Command(goto="act", update={"approved": True})
        decision = interrupt(
            {"plan": plan.model_dump(), "answer": state.get("answer", "")}
        )
        approved = (
            bool(decision.get("approved", False))
            if isinstance(decision, dict)
            else False
        )
        return Command(goto="act", update={"approved": approved})

    return gate


def make_act(gateway: ToolGateway) -> object:
    """Act node: executes approved writes, refuses the rest (audited)."""

    def act(state: TicketState) -> dict:
        plan = state.get("plan")
        if plan is None:
            return {"result": "nada a executar", "done": True}
        if not state.get("approved", False):
            return {"result": gateway.refuse(plan), "done": True}
        result = gateway.call(GATEWAY_IDENTITY, plan, state.get("customer", ""))
        return {"result": result, "done": True}

    return act


def make_abstain() -> object:
    """Unknown-category path: abstain with no plan."""

    def abstain(state: TicketState) -> dict:
        return {"answer": ABSTAIN, "plan": None, "done": True}

    return abstain


def make_finalize() -> object:
    """Terminal node for answered tickets."""

    def finalize(state: TicketState) -> dict:
        return {"done": True}

    return finalize
