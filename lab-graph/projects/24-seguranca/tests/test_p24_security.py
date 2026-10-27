"""P24 tests: allow, 3 negações e auditoria sem segredo."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from p24_security.gateway import Denied, make_gateway


def test_authorized_call_executes_and_audits_allowed(tmp_path: Path) -> None:
    # Given: arquivo dentro do sandbox e identidade autorizada
    target = tmp_path / "ok.txt"
    target.write_text("conteúdo", encoding="utf-8")
    gateway = make_gateway(tmp_path)
    # When: leitura legítima
    result = gateway.call("reader", "read_file", {"path": "ok.txt"})
    # Then: executa e audita allowed
    assert result == "conteúdo"
    assert gateway.audit[-1]["verdict"] == "allowed"


def test_unknown_tool_denied() -> None:
    # Given: gateway vazio de formatadores
    gateway = make_gateway(Path("/tmp"))
    # When/Then: tool fora da lista nega sem executar
    with pytest.raises(Denied, match="unknown tool"):
        gateway.call("reader", "format_disk", {})
    assert gateway.audit[-1]["verdict"] == "denied:unknown-tool"


def test_wrong_identity_denied(tmp_path: Path) -> None:
    # Given: identidade sem acesso
    gateway = make_gateway(tmp_path)
    # When/Then: negação por identidade
    with pytest.raises(Denied, match="not allowed"):
        gateway.call("intruder", "read_file", {"path": "ok.txt"})
    assert gateway.audit[-1]["verdict"] == "denied:identity"


def test_path_traversal_denied(tmp_path: Path) -> None:
    # Given: tentativa de fuga do sandbox
    gateway = make_gateway(tmp_path)
    # When/Then: caminho fora nega
    with pytest.raises(Denied, match="escapes sandbox"):
        gateway.call("reader", "read_file", {"path": "../fora.txt"})
    assert "escapes sandbox" in gateway.audit[-1]["verdict"]


def test_audit_never_stores_secret_values(tmp_path: Path) -> None:
    # Given: negação com arg sensível
    gateway = make_gateway(tmp_path)
    with pytest.raises(Denied):
        gateway.call("intruder", "read_file", {"path": "../x", "token": "SEGREDO"})
    # When/Then: nenhum valor de arg aparece na auditoria
    blob = str(gateway.audit)
    assert "SEGREDO" not in blob
    assert "../x" not in blob
    assert "token" in blob
