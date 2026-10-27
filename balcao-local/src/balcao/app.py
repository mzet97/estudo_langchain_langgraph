"""FastAPI surface: /run, /resume (HITL) and /stream (SSE).

Production (no db_path): Postgres checkpointer + store, PostgresLedger
gateway and real LLM chains. Tests pass db_path for SQLite + keywords.
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langgraph.types import Command
from pydantic import BaseModel, ConfigDict

from balcao.chains import planner_chain, triage_chain
from balcao.gateway import Backend, ToolGateway
from balcao.graph import build_graph
from balcao.kb import default_retriever
from balcao.memory import open_checkpointer, open_pg_saver, open_pg_store
from balcao.store_pg import PostgresLedger
from balcao.trace import EventLog


class RunIn(BaseModel):
    """Run request boundary (parse, don't validate downstream)."""

    model_config = ConfigDict(frozen=True)

    ticket_id: str
    customer: str
    message: str


class ResumeIn(BaseModel):
    """Human decision boundary."""

    model_config = ConfigDict(frozen=True)

    ticket_id: str
    approved: bool


def _config(ticket_id: str) -> dict:
    return {"configurable": {"thread_id": ticket_id}}


def create_app(db_path: Path | None = None, use_llm: bool = True) -> FastAPI:
    """Build the app. Without db_path, Postgres + real LLM (production)."""
    app = FastAPI(title="Balcao Local")
    app.state.db_path = db_path
    app.state.use_llm = use_llm
    app.state.retriever = default_retriever()
    if db_path is None:
        app.state.backend = PostgresLedger(os.environ["DATABASE_URL"])
    else:
        app.state.backend = Backend()
    app.state.gateway = ToolGateway(backend=app.state.backend)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        if application.state.db_path is None:
            url = os.environ["DATABASE_URL"]
            with open_pg_saver(url) as saver, open_pg_store(url) as store:
                application.state.saver = saver
                application.state.store = store
                yield
        else:
            with open_checkpointer(application.state.db_path) as saver:
                application.state.saver = saver
                application.state.store = None
                yield

    app.router.lifespan_context = lifespan

    def graph() -> object:
        chains: dict = {}
        if app.state.use_llm:
            chains = {
                "classifier": triage_chain(),
                "planner": planner_chain(),
            }
        return build_graph(
            app.state.retriever,
            app.state.backend,
            checkpointer=app.state.saver,
            gateway=app.state.gateway,
            **chains,
        )

    @app.post("/run")
    def run(body: RunIn) -> dict:
        log = EventLog()
        out = graph().invoke(
            {"ticket": body.ticket_id, "customer": body.customer, "message": body.message},
            config={**_config(body.ticket_id), "callbacks": [log]},
        )
        if "__interrupt__" in out:
            payload = out["__interrupt__"][0].value
            return {"status": "awaiting_approval", "plan": payload["plan"]}
        return {"status": "done", "answer": out.get("answer"), "result": out.get("result")}

    @app.post("/resume")
    def resume(body: ResumeIn) -> dict:
        out = graph().invoke(
            Command(resume={"approved": body.approved}),
            config=_config(body.ticket_id),
        )
        return {"status": "done", "answer": out.get("answer"), "result": out.get("result")}

    @app.get("/stream")
    def stream(ticket_id: str, customer: str, message: str) -> StreamingResponse:
        def gen() -> Iterator[str]:
            for chunk in graph().stream(
                {"ticket": ticket_id, "customer": customer, "message": message},
                config=_config(ticket_id),
                stream_mode="updates",
            ):
                yield f"data: {json.dumps(sorted(chunk.keys()))}\n\n"

        return StreamingResponse(gen(), media_type="text/event-stream")

    return app
