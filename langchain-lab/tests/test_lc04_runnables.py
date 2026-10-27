"""LC04: LCEL composition (pipe, parallel, lambda, fallback) over fakes."""

import sys

sys.path.insert(0, "src")

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda, RunnableParallel


def _fake_echo() -> GenericFakeChatModel:
    return GenericFakeChatModel(messages=iter([AIMessage(content="eco")]))


def test_pipe_chains_lambda_into_parser() -> None:
    # Given: lambda then a formatter
    chain = RunnableLambda(lambda x: x + 1) | RunnableLambda(lambda x: f"n={x}")
    # When: invoked
    # Then: stages compose left to right
    assert chain.invoke(41) == "n=42"


def test_parallel_fans_out_and_merges() -> None:
    # Given: two branches over the same input
    both = RunnableParallel(
        first=RunnableLambda(lambda x: x + 1),
        second=RunnableLambda(lambda x: x * 10),
    )
    # When: invoked
    # Then: dict with both results
    assert both.invoke(2) == {"first": 3, "second": 20}


def test_fallback_recovers_from_failing_branch() -> None:
    # Given: a branch that always raises, with a healthy fallback
    def boom(x: int) -> int:
        raise RuntimeError("proposital")

    chain = RunnableLambda(boom).with_fallbacks([RunnableLambda(lambda x: -1)])
    # When: invoked
    # Then: fallback value wins
    assert chain.invoke(5) == -1


def test_fake_model_flows_through_lcel() -> None:
    # Given: fake chat model piped into content extraction
    chain = _fake_echo() | RunnableLambda(lambda m: m.content)
    # When: invoked
    # Then: deterministic content, no network
    assert chain.invoke("qualquer") == "eco"
