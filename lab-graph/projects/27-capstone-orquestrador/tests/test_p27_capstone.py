"""P27 tests: aprova e aplica, rejeita sem aplicar, spec inválida."""

import sys
from pathlib import Path

import pytest
from langgraph.types import Command

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p27_capstone.graph import build_graph, thread_config


def fresh_state(spec: dict) -> dict:
    """Estado inicial para uma spec."""
    return {
        "spec": spec,
        "plan": [],
        "staged": {},
        "results": {},
        "approved": False,
        "report": "",
    }


def valid_spec() -> dict:
    """Spec com 2 steps independentes."""
    return {
        "steps": [
            {"id": "t1", "op": "double", "args": {"n": 21}},
            {"id": "t2", "op": "add", "args": {"a": 1, "b": 2}},
        ]
    }


def test_approved_run_applies_staged_results():
    # Given: spec válida executada até a pausa
    graph = build_graph()
    paused = graph.invoke(fresh_state(valid_spec()), thread_config("t1"))
    assert paused["staged"] == {"t1": 42, "t2": 3}
    assert paused["results"] == {}
    # When: humano aprova
    final = graph.invoke(Command(resume=True), thread_config("t1"))
    # Then: encenado promovido e relatório ok
    assert final["approved"] is True
    assert final["results"] == {"t1": 42, "t2": 3}
    assert "applied 2 steps" in final["report"]


def test_rejected_run_applies_nothing():
    # Given: pausa ativa
    graph = build_graph()
    graph.invoke(fresh_state(valid_spec()), thread_config("t1"))
    # When: humano rejeita
    final = graph.invoke(Command(resume=False), thread_config("t1"))
    # Then: nada aplicado, recusa registrada
    assert final["approved"] is False
    assert final["results"] == {}
    assert final["report"] == "rejected by human"


def test_unknown_op_fails_before_any_execution():
    # Given: spec com op fora da allowlist
    graph = build_graph()
    bad = {"steps": [{"id": "t1", "op": "format_disk", "args": {}}]}
    # When/Then: falha no analyze, sem worker executado
    with pytest.raises(ValueError, match="unknown op"):
        graph.invoke(fresh_state(bad), thread_config("t1"))
