"""LC08: local callbacks observe fake-model events without secrets."""

import sys

sys.path.insert(0, "src")

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult


class Recorder(BaseCallbackHandler):
    """Test handler recording only event names."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def on_llm_start(self, *args: object, **kwargs: object) -> None:
        self.events.append("start")

    def on_llm_end(self, *args: object, **kwargs: object) -> None:
        self.events.append("end")


def test_handler_sees_start_and_end() -> None:
    # Given: fake model with a recording handler
    recorder = Recorder()
    model = GenericFakeChatModel(
        messages=iter([AIMessage(content="eco")]), callbacks=[recorder]
    )
    # When: invoked
    assert model.invoke("x").content == "eco"
    # Then: start and end observed, in order
    assert recorder.events == ["start", "end"]


def test_llm_result_carries_generations() -> None:
    # Given: an LLM result with one generation
    result = LLMResult(
        generations=[[ChatGeneration(message=AIMessage(content="a"))]]
    )
    # When: flattened
    # Then: single text
    assert result.generations[0][0].text == "a"
