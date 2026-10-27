"""P08: ReAct com fallback — plano JSON validado + dispatcher allowlisted."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Literal, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ConfigDict

from local_lab.settings import DEFAULT_SETTINGS


class ToolPlan(BaseModel):
    """Plano de ferramenta emitido pelo modelo (única via de ação)."""

    model_config = ConfigDict(frozen=True)

    tool: str
    args: dict = {}


class P08State(TypedDict):
    request: str
    plan_json: str
    outcome: str
    observation: str
    answer: str


def make_add() -> Callable[[dict], str]:
    """Soma a + b (ferramenta pura e determinística)."""

    def add(args: dict) -> str:
        return str(float(args["a"]) + float(args["b"]))

    return add


def make_get_time(clock: Callable[[], str]) -> Callable[[dict], str]:
    """Hora atual via relógio injetável (determinismo offline)."""

    def get_time(args: dict) -> str:
        return clock()

    return get_time


def default_clock() -> str:
    """Relógio real (produção)."""
    return datetime.now().isoformat(timespec="seconds")


PROMPT = (
    "Você controla ferramentas. Responda SOMENTE com JSON válido "
    'no formato {"tool": nome, "args": {...}}. '
    "Ferramentas disponíveis: add(a, b) soma dois números; "
    "get_time() retorna a hora atual. Sem texto fora do JSON.\n"
    "Pedido: "
)


def make_plan(llm: object) -> object:
    """Nó que pede ao modelo o plano JSON (texto, nunca ação)."""

    def plan(state: P08State) -> dict:
        response = llm.invoke(PROMPT + state["request"])
        content = response.content if isinstance(response.content, str) else ""
        if not content.strip():
            raise ValueError("empty plan from model")
        return {"plan_json": content}

    return plan


def make_dispatch(tools: dict) -> object:
    """Nó que valida o plano e executa SOMENTE se allowlisted."""

    def dispatch(state: P08State) -> dict:
        plan = ToolPlan.model_validate_json(state["plan_json"])
        if plan.tool not in tools:
            return {
                "outcome": "denied",
                "observation": f"tool '{plan.tool}' not allowlisted",
            }
        return {"outcome": "executed", "observation": tools[plan.tool](plan.args)}

    return dispatch


def respond(state: P08State) -> dict:
    """Formata a resposta final a partir da observação executada."""
    return {"answer": f"Resultado: {state['observation']}"}


def deny(state: P08State) -> dict:
    """Formata a recusa sem ter executado nada."""
    return {"answer": f"Recusado: {state['observation']}"}


def route_outcome(state: P08State) -> Literal["respond", "deny"]:
    """Desvia pelo resultado do dispatcher (dado, nunca palpite)."""
    if state["outcome"] == "executed":
        return "respond"
    return "deny"


def build_graph(
    llm: object | None = None, clock: Callable[[], str] | None = None
) -> object:
    """Monta plan→dispatch→{respond|deny}→END. Allowlist: add, get_time."""
    if llm is None:
        settings = DEFAULT_SETTINGS
        llm = ChatOpenAI(
            model=settings.llama_model,
            base_url=settings.llama_base_url,
            api_key="local-not-needed",
            temperature=0,
            max_tokens=128,
            timeout=settings.llama_timeout_s,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
    tools = {
        "add": make_add(),
        "get_time": make_get_time(clock or default_clock),
    }
    builder: StateGraph = StateGraph(P08State)
    builder.add_node("plan", make_plan(llm))
    builder.add_node("dispatch", make_dispatch(tools))
    builder.add_node("respond", respond)
    builder.add_node("deny", deny)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "dispatch")
    builder.add_conditional_edges(
        "dispatch", route_outcome, {"respond": "respond", "deny": "deny"}
    )
    builder.add_edge("respond", END)
    builder.add_edge("deny", END)
    return builder.compile()
