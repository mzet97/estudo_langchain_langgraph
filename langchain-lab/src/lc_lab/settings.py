"""Project settings: single source of truth for the local endpoint."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Immutable local-endpoint settings (env-overridable)."""

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


DEFAULT_SETTINGS = Settings()
