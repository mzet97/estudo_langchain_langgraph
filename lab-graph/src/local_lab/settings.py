"""Project settings: single source of truth for local endpoints and models."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    llama_base_url: str = field(
        default_factory=lambda: os.getenv(
            "LLAMA_BASE_URL", "http://127.0.0.1:8080/v1"
        )
    )
    llama_model: str = field(
        default_factory=lambda: os.getenv("LLAMA_MODEL", "gemma-4-12b-it")
    )
    llama_timeout_s: float = field(
        default_factory=lambda: float(os.getenv("LLAMA_TIMEOUT_S", "60"))
    )
    llama_max_output_tokens: int = field(
        default_factory=lambda: int(os.getenv("LLAMA_MAX_OUTPUT_TOKENS", "512"))
    )
    gguf_path: str = field(
        default_factory=lambda: os.getenv(
            "GGUF_PATH",
            "/var/mnt/HD1TB/tese/models/gemma-4-12b-it-UD-Q4_K_XL.gguf",
        )
    )
    llama_server_bin: str = field(
        default_factory=lambda: os.getenv(
            "LLAMA_SERVER_BIN",
            "/var/mnt/HD1TB/tese/src/llama_cpp/build-rocm/bin/llama-server",
        )
    )
    offline_test_mode: bool = field(
        default_factory=lambda: os.getenv("OFFLINE_TEST_MODE", "1") == "1"
    )


DEFAULT_SETTINGS = Settings()
