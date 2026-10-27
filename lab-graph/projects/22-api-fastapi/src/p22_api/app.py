"""P22: FastAPI com POST /run e GET /stream (SSE) sobre o grafo."""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from p22_api.graph import build_graph
from pydantic import BaseModel, ConfigDict


class RunRequest(BaseModel):
    """Contrato de entrada da borda HTTP."""

    model_config = ConfigDict(frozen=True)

    n: int


class RunResponse(BaseModel):
    """Contrato de saída da borda HTTP."""

    model_config = ConfigDict(frozen=True)

    doubled: int


def event_stream(graph: object, n: int) -> object:
    """Gerador SSE: um evento data: por nó executado, em ordem."""

    def generate() -> object:
        for chunk in graph.stream({"n": n, "doubled": 0}):
            node = next(iter(chunk))
            yield f"event: {node}\ndata: {json.dumps(chunk[node])}\n\n"

    return generate


def create_app(run_graph: object | None = None) -> FastAPI:
    """Factory do app; grafo injetável para testes."""
    graph = run_graph if run_graph is not None else build_graph()
    app = FastAPI(title="lab-graph P22")

    @app.post("/run", response_model=RunResponse)
    def run(payload: RunRequest) -> dict:
        result = graph.invoke({"n": payload.n, "doubled": 0})
        return {"doubled": result["doubled"]}

    @app.get("/stream")
    def stream(n: int) -> StreamingResponse:
        return StreamingResponse(
            event_stream(graph, n)(),
            media_type="text/event-stream",
        )

    return app
