"""M3: SQLite persiste por ticket; store lembra o perfil entre tickets."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from balcao.gateway import Backend
from balcao.graph import build_graph
from balcao.kb import Retriever, load_kb
from balcao.memory import (
    open_checkpointer,
    open_store,
    recall_customer,
    remember_customer,
)


def test_checkpoint_isola_tickets(tmp_path: Path) -> None:
    # Given: grafo com SQLite e dois tickets
    kb = Retriever.build(load_kb(Path("kb")))
    with open_checkpointer(tmp_path / "balcao.db") as saver:
        graph = build_graph(kb, Backend(), checkpointer=saver)
        # When: cada ticket roda no próprio thread_id
        out1 = graph.invoke(
            {"ticket": "t1", "customer": "c", "message": "quero a segunda via"},
            config={"configurable": {"thread_id": "t1"}},
        )
        out2 = graph.invoke(
            {"ticket": "t2", "customer": "c", "message": "luz los vermelha na ont"},
            config={"configurable": {"thread_id": "t2"}},
        )
        # Then: respostas distintas e histórico separado
        assert "[fonte:fatura-2via]" in out1["answer"]
        assert "[fonte:" in out2["answer"]
        hist1 = list(
            graph.get_state_history(config={"configurable": {"thread_id": "t1"}})
        )
        hist2 = list(
            graph.get_state_history(config={"configurable": {"thread_id": "t2"}})
        )
        assert len(hist1) > 1 and len(hist2) > 1
        assert hist1[0].values["ticket"] == "t1"
        assert hist2[0].values["ticket"] == "t2"


def test_store_recorda_perfil_entre_tickets() -> None:
    # Given: store vazio
    store = open_store()
    # When: perfil salvo e recuperado
    assert recall_customer(store, "cli1") is None
    remember_customer(store, "cli1", "Dona Maria")
    # Then: nome volta em outro ticket
    assert recall_customer(store, "cli1") == "Dona Maria"
    assert recall_customer(store, "outro") is None
