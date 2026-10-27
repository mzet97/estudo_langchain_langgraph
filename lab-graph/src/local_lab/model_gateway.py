"""Model gateway: thin OpenAI-compatible adapter with capability probing.

Follows ADR-001/ADR-003: resolve the real model via the API, expose one
Capability flag per feature, never silently downgrade on missing support.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from .settings import Settings


@dataclass(frozen=True)
class Capability:
    chat: bool = False
    json_schema: bool = False
    tool_calling: bool = False
    streaming: bool = False


@dataclass
class ModelGateway:
    settings: Settings
    model_id: str | None = None
    capability: Capability = field(default_factory=Capability)

    def _client(self) -> httpx.Client:
        return httpx.Client(
            base_url=self.settings.llama_base_url,
            timeout=self.settings.llama_timeout_s,
        )

    def discover_models(self) -> list[str]:
        """Return model IDs from GET /models (real server, no mock)."""
        with self._client() as client:
            resp = client.get("/models")
            resp.raise_for_status()
            data = resp.json()
        ids = [m["id"] for m in data.get("data", []) if "id" in m]
        if len(ids) == 1:
            self.model_id = ids[0]
        return ids

    def chat(self, messages: list[dict], **kwargs) -> str:
        """Plain chat completion; raises on transport or API error."""
        payload = {
            "model": self.model_id or self.settings.llama_model,
            "messages": messages,
            "max_tokens": kwargs.get(
                "max_tokens", self.settings.llama_max_output_tokens
            ),
            "stream": False,
        }
        with self._client() as client:
            resp = client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return data["choices"][0]["message"]["content"]
