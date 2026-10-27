"""Offline unit tests: settings defaults and evidence fingerprint."""

import sys

sys.path.insert(0, "src")

from local_lab.evidence import build_evidence
from local_lab.settings import Settings


def test_settings_defaults_point_to_local_gemma():
    s = Settings()
    assert s.llama_base_url == "http://127.0.0.1:8080/v1"
    assert "UD-Q4_K_XL" in s.gguf_path
    assert s.llama_server_bin.endswith("llama-server")


def test_evidence_never_leaks_full_private_path():
    ev = build_evidence("P00", "probe", "/secret/path/model.gguf")
    assert "/secret/path" not in str(ev.gguf_path_hash)
    assert ev.project_id == "P00"
