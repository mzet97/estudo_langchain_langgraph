"""Probe llama-server capabilities (read-only, Etapa A do MASTER_PROMPT).

Checks, in order: version is out of scope here (see P00 server logs),
GET /v1/models, plain chat, schema-constrained JSON, tool-calling,
streaming. Prints a JSON capability report. Exit 0 even when the
server is down (records BLOCKED instead of failing silently).
"""

from __future__ import annotations

import argparse
import json
import sys

sys.path.insert(0, "src")

from local_lab.evidence import build_evidence, evidence_to_dict
from local_lab.settings import Settings


def probe(base_url: str, gguf_path: str) -> dict:
    import httpx

    report: dict = {
        "base_url": base_url,
        "models": [],
        "capabilities": {
            "chat": "NOT_RUN",
            "json_schema": "NOT_RUN",
            "tool_calling": "NOT_RUN",
            "streaming": "NOT_RUN",
        },
    }
    try:
        with httpx.Client(base_url=base_url, timeout=30) as client:
            resp = client.get("/models")
            resp.raise_for_status()
            ids = [m["id"] for m in resp.json().get("data", []) if "id" in m]
            report["models"] = ids
            model = ids[0] if len(ids) == 1 else "gemma-4-12b-it"

            try:
                r = client.post(
                    "/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Diga OK"}],
                        "max_tokens": 16,
                        "stream": False,
                    },
                )
                r.raise_for_status()
                report["capabilities"]["chat"] = "PASS"
            except (httpx.HTTPError, ValueError) as exc:
                report["capabilities"]["chat"] = f"FAIL: {exc}"

            try:
                r = client.post(
                    "/chat/completions",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": "Responda em JSON."}
                        ],
                        "max_tokens": 64,
                        "stream": False,
                        "response_format": {
                            "type": "json_object",
                            "schema": {
                                "type": "object",
                                "properties": {"ok": {"type": "boolean"}},
                                "required": ["ok"],
                            },
                        },
                    },
                )
                r.raise_for_status()
                report["capabilities"]["json_schema"] = "PASS"
            except (httpx.HTTPError, ValueError) as exc:
                report["capabilities"]["json_schema"] = f"FAIL: {exc}"

            try:
                with client.stream(
                    "POST",
                    "/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "Conte ate 3"}],
                        "max_tokens": 32,
                        "stream": True,
                    },
                ) as r:
                    r.raise_for_status()
                    chunks = sum(1 for _ in r.iter_text())
                report["capabilities"]["streaming"] = (
                    "PASS" if chunks > 0 else "FAIL: empty stream"
                )
            except (httpx.HTTPError, ValueError) as exc:
                report["capabilities"]["streaming"] = f"FAIL: {exc}"

            try:
                r = client.post(
                    "/chat/completions",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "user", "content": "Que horas são?"}
                        ],
                        "max_tokens": 64,
                        "stream": False,
                        "tool_choice": "auto",
                        "tools": [
                            {
                                "type": "function",
                                "function": {
                                    "name": "get_time",
                                    "description": "Retorna a hora atual.",
                                    "parameters": {
                                        "type": "object",
                                        "properties": {},
                                    },
                                },
                            }
                        ],
                    },
                )
                r.raise_for_status()
                msg = r.json()["choices"][0]["message"]
                report["capabilities"]["tool_calling"] = (
                    "PASS" if msg.get("tool_calls") else "FAIL: no tool_calls"
                )
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                report["capabilities"]["tool_calling"] = f"FAIL: {exc}"
    except (httpx.HTTPError, ValueError) as exc:
        report["server"] = f"BLOCKED: {exc}"

    ev = build_evidence(
        "P00",
        f"probe {base_url}",
        gguf_path,
        status="PASS" if report.get("models") else "BLOCKED",
    )
    report["evidence"] = evidence_to_dict(ev)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe llama-server capabilities")
    parser.add_argument("--base-url", default=Settings().llama_base_url)
    parser.add_argument("--gguf-path", default=Settings().gguf_path)
    args = parser.parse_args()
    print(json.dumps(probe(args.base_url, args.gguf_path), indent=2))


if __name__ == "__main__":
    main()
