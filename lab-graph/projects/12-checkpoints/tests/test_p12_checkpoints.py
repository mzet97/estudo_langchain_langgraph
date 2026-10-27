"""P12 tests: retomada, isolamento e time travel com fork."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p12_checkpoints.graph import build_graph, thread_config


def test_same_thread_resumes_and_accumulates():
    # Given: thread nova
    graph = build_graph()
    # When: dois invokes na mesma thread
    first = graph.invoke({"count": 0}, thread_config("t1"))
    second = graph.invoke({"count": 0}, thread_config("t1"))
    # Then: checkpoint retomado e acumulado
    assert first["count"] == 1
    assert second["count"] == 2


def test_threads_are_isolated():
    # Given: duas threads intercaladas
    graph = build_graph()
    graph.invoke({"count": 0}, thread_config("t1"))
    other = graph.invoke({"count": 0}, thread_config("t2"))
    main = graph.invoke({"count": 0}, thread_config("t1"))
    # Then: contagens independentes
    assert other["count"] == 1
    assert main["count"] == 2


def test_fork_diverges_without_destroying_main_line():
    # Given: linha principal com 2 checkpoints
    graph = build_graph()
    graph.invoke({"count": 0}, thread_config("t1"))
    graph.invoke({"count": 0}, thread_config("t1"))
    history = list(graph.get_state_history(thread_config("t1")))
    older = next(s for s in history if s.values.get("count") == 1)
    checkpoint_id = older.config["configurable"]["checkpoint_id"]
    # When: fork do checkpoint antigo + avanço da linha principal
    branched = graph.invoke(
        {"count": 0}, thread_config("t1", checkpoint_id)
    )
    main = graph.invoke({"count": 0}, thread_config("t1"))
    # Then: ramo diverge e linha principal segue
    assert branched["count"] == 2
    assert main["count"] == 3
