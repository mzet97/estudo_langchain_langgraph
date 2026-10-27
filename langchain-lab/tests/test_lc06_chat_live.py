"""LC06: ChatOpenAI points at local llama-server; live tests skip if down."""

import sys

import httpx
import pytest
from openai import OpenAIError
from pydantic import BaseModel, ConfigDict

sys.path.insert(0, "src")

from langchain_openai import ChatOpenAI

from lc_lab.settings import DEFAULT_SETTINGS


def _build(
    model_kwargs: dict[str, object] | None = None, timeout_s: float | None = None
) -> ChatOpenAI:
    s = DEFAULT_SETTINGS
    return ChatOpenAI(
        model=s.llama_model,
        base_url=s.llama_base_url,
        api_key="local-not-needed",
        temperature=0,
        max_tokens=s.llama_max_output_tokens,
        timeout=timeout_s or s.llama_timeout_s,
        model_kwargs=model_kwargs or {},
    )


def _skip_if_down(exc: Exception) -> pytest.skip:
    return pytest.skip(f"llama-server ausente: {exc}")


LiveError = (httpx.HTTPError, httpx.TimeoutException, OpenAIError)


def test_client_points_to_local_server() -> None:
    # Given: default settings
    # When: client built (no network call)
    llm = _build()
    # Then: base URL is the local server, never a cloud host
    assert "127.0.0.1" in str(llm.openai_api_base)


def test_live_chat_answers() -> None:
    # Given: real local model
    llm = _build()
    # When: plain chat
    try:
        answer = llm.invoke("Responda apenas: OK").content
    except LiveError as exc:
        raise _skip_if_down(exc)
    # Then: non-empty string answer
    assert isinstance(answer, str) and answer.strip() != ""


def test_live_json_mode_parses_to_pydantic() -> None:
    # Given: json_mode client and a frozen contract
    class Mood(BaseModel):
        """Contrato de saida do teste live."""

        model_config = ConfigDict(frozen=True)

        ok: bool

    llm = _build(model_kwargs={"response_format": {"type": "json_object"}})
    # When: asked for JSON only
    try:
        raw = llm.invoke("Responda SOMENTE com o JSON {\"ok\": true}.").content
        assert isinstance(raw, str)
        parsed = Mood.model_validate_json(raw)
    except LiveError as exc:
        raise _skip_if_down(exc)
    # Then: validates against the contract
    assert parsed.ok is True


def test_live_streaming_yields_chunks() -> None:
    # Given: real local model
    llm = _build()
    # When: streamed
    try:
        chunks = list(llm.stream("Conte ate 3."))
    except LiveError as exc:
        raise _skip_if_down(exc)
    # Then: at least one chunk with text
    assert any(isinstance(c.content, str) and c.content for c in chunks)


def test_live_tool_calling_documents_absence() -> None:
    # Given: tool definition on the current server template
    from langchain_core.tools import StructuredTool

    def get_time() -> str:
        """Retorna a hora atual."""
        return "10:00"

    tool = StructuredTool.from_function(
        func=get_time, name="get_time", description="Retorna a hora atual."
    )
    llm = _build(timeout_s=240).bind_tools([tool])
    # When: invoked
    try:
        msg = llm.invoke("Que horas sao?")
    except LiveError as exc:
        raise _skip_if_down(exc)
    # Then: server sem tool-calling responde texto, sem tool_calls (P00 FAIL)
    assert not getattr(msg, "tool_calls", [])
