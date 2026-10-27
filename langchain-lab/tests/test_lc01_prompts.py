"""LC01: prompt templates render offline and fail loudly on missing vars."""

import sys

import pytest

sys.path.insert(0, "src")

from langchain_core.prompts import ChatPromptTemplate


def test_render_fills_variables() -> None:
    # Given: template with one variable
    tpl = ChatPromptTemplate.from_messages(
        [("system", "Seja conciso."), ("human", "{question}")]
    )
    # When: formatted with the variable
    value = tpl.format_messages(question="Ola")
    # Then: human message carries the rendered text
    assert value[-1].content == "Ola"


def test_missing_variable_raises_key_error() -> None:
    # Given: template requiring a variable
    tpl = ChatPromptTemplate.from_messages([("human", "{question}")])
    # When/Then: formatting without it raises KeyError
    with pytest.raises(KeyError):
        tpl.format()


def test_partial_prefills_system_message() -> None:
    # Given: template partially filled
    tpl = ChatPromptTemplate.from_messages(
        [("system", "{tone}"), ("human", "{question}")]
    )
    # When: tone is prefilled and question given at format time
    value = tpl.partial(tone="Seja conciso.").format_messages(question="Oi")
    # Then: both messages are rendered
    assert value[0].content == "Seja conciso."
    assert value[1].content == "Oi"
