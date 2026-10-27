"""M6 perf: p50 do caminho offline abaixo de 500 ms (SC-04)."""

import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, "src")

from balcao.gateway import Backend
from balcao.graph import build_graph
from balcao.kb import Retriever, load_kb


def test_p50_offline_abaixo_de_500ms() -> None:
    # Given: grafo offline aquecido
    graph = build_graph(
        Retriever.build(load_kb(Path("kb"))), Backend(), auto_approve=True
    )
    graph.invoke({"ticket": "w", "customer": "c", "message": "oi"})
    # When: 20 repetições medidas
    samples = []
    for i in range(20):
        start = time.perf_counter()
        graph.invoke({"ticket": f"b{i}", "customer": "c", "message": "wifi fraco"})
        samples.append((time.perf_counter() - start) * 1000.0)
    # Then: p50 abaixo do orçamento
    assert statistics.median(samples) < 500.0
