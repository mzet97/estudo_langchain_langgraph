"""P21 tests: resume sem refazer, replay igual, sem-checkpoint refaz."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p21_durable.graph import build_graph


def fresh_state() -> dict:
    """Estado inicial zerado."""
    return {"a": 0, "b": 0, "c": 0}


def thread_config(thread_id: str) -> dict:
    """Config de execução com a thread obrigatória."""
    return {"configurable": {"thread_id": thread_id}}


def test_resume_does_not_redo_completed_steps():
    # Given: crash no meio na 1ª tentativa
    runs: dict = {}
    graph = build_graph(crash_budget={"n": 1}, runs=runs)
    with pytest.raises(ConnectionError, match="crash simulado"):
        graph.invoke(fresh_state(), thread_config("t1"))
    assert runs.get("step1") == 1
    # When: resume sem input novo (None) na mesma thread
    result = graph.invoke(None, thread_config("t1"))
    # Then: completo sem refazer o step1
    assert (result["a"], result["b"], result["c"]) == (1, 2, 3)
    assert runs.get("step1") == 1
    assert runs.get("fragile") == 2


def test_clean_replay_matches_recovered_run():
    # Given: thread limpa sem crash
    clean = build_graph(crash_budget={}, runs={})
    recovered = build_graph(crash_budget={"n": 1}, runs={})
    # When: replay limpo vs crash + resume
    with pytest.raises(ConnectionError, match="crash simulado"):
        recovered.invoke(fresh_state(), thread_config("t9"))
    resumed = recovered.invoke(None, thread_config("t9"))
    direct = clean.invoke(fresh_state(), thread_config("t8"))
    # Then: estados finais iguais
    assert resumed == direct == {"a": 1, "b": 2, "c": 3}


def test_no_checkpointer_redoes_everything():
    # Given: sem durabilidade e 1 crash
    runs: dict = {}
    graph = build_graph(
        checkpointer=None, crash_budget={"n": 1}, runs=runs
    )
    with pytest.raises(ConnectionError, match="crash simulado"):
        graph.invoke(fresh_state(), thread_config("t1"))
    # When: "resume" sem checkpoint
    result = graph.invoke(fresh_state(), thread_config("t1"))
    # Then: refez do zero (step1 rodou de novo)
    assert (result["a"], result["b"], result["c"]) == (1, 2, 3)
    assert runs.get("step1") == 2
