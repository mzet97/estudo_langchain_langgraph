"""P15 tests: ainvoke, fronteira sync, updates e aclose antecipado."""

import sys
from pathlib import Path

import anyio
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p15_streaming.graph import build_graph


def test_ainvoke_returns_full_state_and_sync_refuses():
    # Given: grafo de nós só-async
    graph = build_graph()
    # When: invoke async
    async_result = anyio.run(graph.ainvoke, {"log": []})
    # Then: estado final completo; sync levanta a fronteira do framework
    assert async_result == {"log": ["a", "b"]}
    with pytest.raises(TypeError, match="async API"):
        graph.invoke({"log": []})


def test_stream_updates_arrive_in_order():
    # Given: stream em modo updates
    graph = build_graph()

    async def collect() -> list:
        return [event async for event in graph.astream({"log": []})]

    # When: consome tudo
    events = anyio.run(collect)
    # Then: um evento por nó, em ordem, com o update aplicado
    assert [next(iter(e)) for e in events] == ["step_a", "step_b"]
    assert events[0]["step_a"] == {"log": ["a"]}
    assert events[1]["step_b"] == {"log": ["b"]}


def test_early_close_stops_delivery():
    # Given: stream aberto
    graph = build_graph()

    async def take_first_and_close() -> list:
        seen = []
        agen = graph.astream({"log": []})
        async for event in agen:
            seen.append(event)
            break
        await agen.aclose()
        return seen

    # When: consome 1 evento e fecha
    seen = anyio.run(take_first_and_close)
    # Then: só o primeiro foi entregue e fechar não levantou
    assert len(seen) == 1
    assert next(iter(seen[0])) == "step_a"
