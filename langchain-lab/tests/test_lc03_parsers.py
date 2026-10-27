"""LC03: output parsers turn raw text into typed values or fail loudly."""

import sys

import pytest
from langchain_core.exceptions import OutputParserException
from pydantic import BaseModel, ConfigDict, Field

sys.path.insert(0, "src")

from langchain_core.output_parsers import (
    CommaSeparatedListOutputParser,
    PydanticOutputParser,
    StrOutputParser,
)


class Rating(BaseModel):
    """Frozen rating contract for parser tests."""

    model_config = ConfigDict(frozen=True)

    title: str
    score: int = Field(ge=0, le=10)


def test_str_parser_returns_text_unchanged() -> None:
    # Given: raw model text
    # When: parsed as string
    # Then: identical text back
    assert StrOutputParser().parse("ola mundo") == "ola mundo"


def test_list_parser_splits_items() -> None:
    # Given: comma-separated text
    # When: parsed as list
    # Then: trimmed items
    assert CommaSeparatedListOutputParser().parse("a, b,c") == ["a", "b", "c"]


def test_pydantic_parser_accepts_valid_json() -> None:
    # Given: valid JSON for the contract
    raw = '{"title": "Duna", "score": 9}'
    # When: parsed
    # Then: typed frozen value
    assert PydanticOutputParser(pydantic_object=Rating).parse(raw) == Rating(
        title="Duna", score=9
    )


def test_pydantic_parser_rejects_out_of_range() -> None:
    # Given: JSON violating the score range
    raw = '{"title": "Duna", "score": 99}'
    # When/Then: OutputParserException wrapping the range violation
    with pytest.raises(OutputParserException):
        PydanticOutputParser(pydantic_object=Rating).parse(raw)
