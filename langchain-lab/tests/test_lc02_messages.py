"""LC02: message types keep role and content through prompt values."""

import sys

sys.path.insert(0, "src")

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate


def test_human_message_keeps_type_and_content() -> None:
    # Given: a human message
    msg = HumanMessage(content="Qual e o horario?")
    # When: inspected
    # Then: type and content are preserved
    assert msg.type == "human"
    assert msg.content == "Qual e o horario?"


def test_prompt_value_preserves_role_order() -> None:
    # Given: a two-role template
    tpl = ChatPromptTemplate.from_messages(
        [("system", "Util."), ("human", "{q}")]
    )
    # When: formatted
    value = tpl.format_messages(q="Oi")
    # Then: roles arrive in order with rendered content
    assert [m.type for m in value] == ["system", "human"]
    assert isinstance(value[0], SystemMessage)
    assert isinstance(value[1], HumanMessage)


def test_ai_message_round_trips_content() -> None:
    # Given: an AI answer
    msg = AIMessage(content="Sao 10h.")
    # When: content read back
    # Then: unchanged
    assert msg.content == "Sao 10h."
