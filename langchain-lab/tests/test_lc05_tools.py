"""LC05: tools validate args; gateway allows one, denies the rest."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, "src")

from langchain_core.tools import StructuredTool

from lc_lab.gateway import DeniedError, make_gateway


def _add(a: int, b: int) -> int:
    """Soma dois inteiros."""
    return a + b


def test_structured_tool_executes_valid_args() -> None:
    # Given: allowlisted add tool
    tool = StructuredTool.from_function(
        func=_add, name="add", description="Soma dois inteiros."
    )
    # When: invoked with valid args
    # Then: typed result
    assert tool.invoke({"a": 2, "b": 3}) == 5


def test_structured_tool_rejects_bad_args() -> None:
    # Given: add tool
    tool = StructuredTool.from_function(
        func=_add, name="add", description="Soma dois inteiros."
    )
    # When/Then: wrong-typed args raise ValidationError
    with pytest.raises(ValidationError):
        tool.invoke({"a": "x", "b": 2})


def test_gateway_allows_authorized_add() -> None:
    # Given: gateway with authorized reader
    gateway = make_gateway(Path("/tmp"))
    # When: reader calls add
    # Then: executes and audits allowed
    assert gateway.call("reader", "add", {"a": 7, "b": 8}) == "15"


def test_gateway_denies_unknown_tool() -> None:
    # Given: gateway
    gateway = make_gateway(Path("/tmp"))
    # When/Then: unknown tool raises typed denial
    with pytest.raises(DeniedError, match="unknown-tool"):
        gateway.call("reader", "format_disk", {})
    assert gateway.audit[-1].verdict == "denied:unknown-tool"


def test_gateway_denies_wrong_identity() -> None:
    # Given: gateway
    gateway = make_gateway(Path("/tmp"))
    # When/Then: intruder is denied
    with pytest.raises(DeniedError, match="not allowed"):
        gateway.call("intruder", "add", {"a": 1, "b": 2})
    assert gateway.audit[-1].verdict == "denied:identity"


def test_gateway_denies_path_escape(tmp_path: Path) -> None:
    # Given: sandbox gateway and a file inside it
    (tmp_path / "ok.txt").write_text("conteudo", encoding="utf-8")
    gateway = make_gateway(tmp_path)
    # When/Then: escape attempt is denied, legit read works
    with pytest.raises(DeniedError, match="path-escape"):
        gateway.call("reader", "read", {"path": "../fora.txt"})
    assert gateway.call("reader", "read", {"path": "ok.txt"}) == "conteudo"
