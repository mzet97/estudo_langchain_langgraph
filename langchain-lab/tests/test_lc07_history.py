"""LC07: in-memory history and document value objects."""

import sys

sys.path.insert(0, "src")

from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage


def test_history_appends_and_lists_messages() -> None:
    # Given: empty history
    history = InMemoryChatMessageHistory()
    # When: two messages added
    history.add_message(HumanMessage(content="Oi"))
    history.add_ai_message("Ola!")
    # Then: both stored in order
    assert [m.type for m in history.messages] == ["human", "ai"]


def test_history_clear_empties_it() -> None:
    # Given: history with one message
    history = InMemoryChatMessageHistory()
    history.add_user_message("Oi")
    # When: cleared
    history.clear()
    # Then: empty
    assert history.messages == []


def test_document_keeps_content_and_metadata() -> None:
    # Given: a document with namespaced metadata
    doc = Document(page_content="RAG local.", metadata={"ns": "lc07"})
    # When/Then: content and metadata preserved
    assert doc.page_content == "RAG local."
    assert doc.metadata["ns"] == "lc07"
